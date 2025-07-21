import asyncio
import socket
import threading
import urllib.parse
import websockets

# Track servers by host:port (not by path)
_port_servers = {}
_server_lock = threading.RLock()


def _port_is_in_use(host, port):
    """Check if a port is already in use"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception:
        return False


async def _is_valid_websocket_server(host, port, timeout=5):
    """Check if there's a valid WebSocket server at the given address"""
    # Try multiple approaches to validate WebSocket server
    
    # Method 1: Try connecting to root path
    try:
        uri = f"ws://{host}:{port}/"
        websocket = await asyncio.wait_for(websockets.connect(uri), timeout=timeout)
        try:
            # If we can connect successfully, it's likely a WebSocket server
            pass
        finally:
            await websocket.close()
        return True
    except Exception:
        pass
    
    # Method 2: Try common WebSocket paths
    common_paths = ["/ws", "/websocket", "/socket", "/api/ws"]
    for path in common_paths:
        try:
            uri = f"ws://{host}:{port}{path}"
            websocket = await asyncio.wait_for(websockets.connect(uri), timeout=timeout)
            try:
                pass
            finally:
                await websocket.close()
            return True
        except Exception:
            continue
    
    # Method 3: Try connecting without any specific protocol requirements
    try:
        uri = f"ws://{host}:{port}/"
        # Use a more permissive connection attempt
        websocket = await asyncio.wait_for(
            websockets.connect(
                uri, 
                # Allow any subprotocol
                subprotocols=[],
                # More permissive headers
                extra_headers={}
            ), 
            timeout=timeout
        )
        try:
            pass
        finally:
            await websocket.close()
        return True
    except websockets.exceptions.InvalidStatusCode:
        # If we get InvalidStatusCode, it might still be a WebSocket server
        # but with different requirements
        return True
    except Exception:
        pass
    
    return False


class WebSocketClientProxy:
    """Client proxy that connects to an existing WebSocket server"""
    
    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.paths = set()
        self.clients = {}  # path -> channel -> [websocket connections]
        self._connections = {}  # uri -> websocket connection
        self._is_running = True
        
    def register_path(self, path):
        """Register a path for this proxy"""
        if path not in self.paths:
            self.paths.add(path)
            self.clients[path] = {i: [] for i in range(1, 9)}
            if self.debug:
                print(f"[WebSocketClientProxy] Registered path {path} for {self.host}:{self.port}")
    
    def send_to_channel(self, path, channel, data):
        """Send data to a channel via WebSocket client connection"""
        if path not in self.paths:
            if self.debug:
                print(f"[WebSocketClientProxy] Path '{path}' not registered")
            return
            
        # Create connection key
        uri = f"ws://{self.host}:{self.port}{path}?channel={channel}"
        
        # Send data asynchronously in a thread to avoid event loop conflicts
        def send_in_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._send_async(uri, data))
                finally:
                    loop.close()
            except Exception as e:
                if self.debug:
                    print(f"[WebSocketClientProxy] Failed to send data: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=send_in_thread, daemon=True)
        thread.start()
    
    async def _send_async(self, uri, data):
        """Send data asynchronously"""
        try:
            # Use asyncio.wait_for for timeout instead of timeout parameter
            websocket = await asyncio.wait_for(
                websockets.connect(uri), 
                timeout=5.0
            )
            try:
                # Send the data as a message
                await websocket.send(data)
                if self.debug:
                    print(f"[WebSocketClientProxy] Sent data to {uri}")
                
                # Keep connection open briefly to ensure message is processed
                await asyncio.sleep(0.1)
            finally:
                await websocket.close()
        except Exception as e:
            if self.debug:
                print(f"[WebSocketClientProxy] Connection failed to {uri}: {e}")
    
    def is_running(self):
        """Check if the proxy is operational"""
        return self._is_running
    
    def start(self):
        """Proxy is always ready"""
        return True
    
    def stop(self):
        """Stop the proxy"""
        self._is_running = False
        if self.debug:
            print("[WebSocketClientProxy] Proxy stopped")


class SimpleWebSocketServer:
    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        
        # Track paths and their clients
        self.paths = set()
        self.clients = {}  # path -> channel -> [websockets]
        
        self.loop = asyncio.new_event_loop()
        self.server = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self._is_running = False

    def register_path(self, path):
        """Register a new path for this server to handle"""
        with _server_lock:  # Use the global lock for consistency
            if path not in self.paths:
                self.paths.add(path)
                # Initialize channels (1-8) for this path
                self.clients[path] = {i: [] for i in range(1, 9)}
                if self.debug:
                    print(f"[SimpleWebSocketServer] Registered path {path} on {self.host}:{self.port}")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self._start_server())
        if self.debug:
            print(f"[SimpleWebSocketServer] Server task scheduled on {self.host}:{self.port}")
        self.loop.run_forever()
        self._is_running = False
        if self.debug:
            print(f"[SimpleWebSocketServer] Server loop stopped on {self.host}:{self.port}")

    async def _start_server(self):
        try:
            # Create a wrapper handler that is compatible with different websockets library versions
            async def handler_wrapper(websocket, path=None):
                await self._handler(websocket, path)
            
            self.server = await websockets.serve(handler_wrapper, self.host, self.port)
            print(f"Server listening on {self.host}:{self.port}")
            
            self._is_running = True
            if self.debug:
                print(f"[SimpleWebSocketServer] Server started on {self.host}:{self.port}")
        except Exception as e:
            self._is_running = False
            print(f"[SimpleWebSocketServer] Failed to start server: {e}")

    async def _handler(self, websocket, path=None):
        # Get resource path - try multiple ways to get the correct path
        resource_path = ""
        
        if hasattr(websocket, "request") and websocket.request:
            resource_path = websocket.request.path
        elif hasattr(websocket, "path") and websocket.path:
            resource_path = websocket.path
        elif path is not None:
            resource_path = path
        else:
            resource_path = "/"
            
        # Remove query parameters from resource path
        resource_path = resource_path.split("?")[0]
        
        if self.debug:
            print(f"[SimpleWebSocketServer] Processing connection with path: '{resource_path}', registered paths: {list(self.paths)}")
        
        # Check if this path is registered with this server
        if resource_path not in self.paths:
            if self.debug:
                print(f"[SimpleWebSocketServer] Reject connection: path '{resource_path}' not registered")
            await websocket.close()
            return
        
        # Parse channel parameter from the original path (including query string)
        full_path = ""
        if hasattr(websocket, "request") and websocket.request:
            full_path = websocket.request.path
        elif hasattr(websocket, "path") and websocket.path:
            full_path = websocket.path
        elif path is not None:
            full_path = path
        else:
            full_path = "/"
            
        parsed = urllib.parse.urlparse(full_path)
        params = urllib.parse.parse_qs(parsed.query)
        channel_str = params.get("channel", [None])[0]
        
        try:
            channel = int(channel_str)
            if channel < 1 or channel > 8:
                raise ValueError
        except:
            if self.debug:
                print(f"[SimpleWebSocketServer] Reject connection: invalid channel '{channel_str}'")
            await websocket.close()
            return
            
        if self.debug:
            print(f"[SimpleWebSocketServer] New connection from {websocket.remote_address} on path '{resource_path}' with channel {channel}")
            
        # Add client to the specific path and channel
        self.clients[resource_path][channel].append(websocket)
        print(f"Connection open on {resource_path} channel {channel}")
        
        try:
            # Keep connection alive by waiting for it to close
            # Also handle any incoming messages
            async def message_handler():
                async for message in websocket:
                    if self.debug:
                        # Smart message logging - avoid printing binary data
                        if isinstance(message, bytes):
                            print(f"[SimpleWebSocketServer] Received binary message on {resource_path} channel {channel}: {len(message)} bytes")
                        elif isinstance(message, str):
                            if len(message) > 256:
                                print(f"[SimpleWebSocketServer] Received text message on {resource_path} channel {channel}: {len(message)} chars (truncated: {message[:200]}...)")
                            else:
                                print(f"[SimpleWebSocketServer] Received text message on {resource_path} channel {channel}: {message}")
                        else:
                            print(f"[SimpleWebSocketServer] Received message on {resource_path} channel {channel}: {type(message).__name__} ({len(str(message))} chars)")
                    # Broadcast message to all other clients in the same channel
                    for client_ws in list(self.clients[resource_path][channel]):
                        if client_ws != websocket:  # Don't send back to sender
                            try:
                                await client_ws.send(message)
                            except Exception as e:
                                if self.debug:
                                    print(f"[SimpleWebSocketServer] Failed to forward message to client: {e}")
                                # Remove failed client
                                if client_ws in self.clients[resource_path][channel]:
                                    self.clients[resource_path][channel].remove(client_ws)
            
            # Run message handler in background and wait for connection to close
            message_task = asyncio.create_task(message_handler())
            try:
                await websocket.wait_closed()
            except:
                pass
            finally:
                if not message_task.done():
                    message_task.cancel()
        except websockets.exceptions.ConnectionClosed:
            # Normal connection close
            pass
        except Exception as e:
            if self.debug:
                print(f"[SimpleWebSocketServer] Exception on {resource_path} channel {channel}: {e}")
        finally:
            if websocket in self.clients[resource_path][channel]:
                self.clients[resource_path][channel].remove(websocket)
            if self.debug:
                print(f"[SimpleWebSocketServer] Connection closed from {websocket.remote_address} on {resource_path} channel {channel}")

    def send_to_channel(self, path, channel, data):
        """Send data to all clients on a specific path and channel"""
        if path not in self.paths or channel not in self.clients[path]:
            if self.debug:
                print(f"[SimpleWebSocketServer] Cannot send: path '{path}' not registered or channel {channel} not found")
            return
            
        clients = self.clients[path][channel]
        if self.debug:
            client_count = len(clients)
            print(f"[SimpleWebSocketServer] Sending {len(str(data))} bytes to {path} channel {channel} with {client_count} client(s)")
            
        # Send to all clients, removing any that fail
        failed_clients = []
        for ws in list(clients):
            try:
                future = asyncio.run_coroutine_threadsafe(ws.send(data), self.loop)
                # Wait briefly for the send to complete
                future.result(timeout=1.0)
            except Exception as e:
                if self.debug:
                    print(f"[SimpleWebSocketServer] Failed to send to client: {e}")
                failed_clients.append(ws)
        
        # Remove failed clients
        for ws in failed_clients:
            if ws in clients:
                clients.remove(ws)

    def start(self):
        """Public method to start the server if it's not already running."""
        if self.debug:
            print(f"[SimpleWebSocketServer] Starting server on {self.host}:{self.port}")
        if not self._is_running:
            self.loop.call_soon_threadsafe(
                lambda: asyncio.ensure_future(self._start_server(), loop=self.loop)
            )
        return self._is_running
            
    def stop(self):
        """Stop the server and close all connections."""
        if self.debug:
            print("[SimpleWebSocketServer] Stopping server")
        
        self._is_running = False
        
        if self.server:
            self.server.close()
        
        # Stop the event loop more safely
        if self.loop and self.loop.is_running():
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except RuntimeError:
                # Loop might already be closed
                pass
        
        # Don't wait for thread with blocking join since it's a daemon thread
        # Just mark as not running and let the daemon thread clean up naturally
        if self.debug:
            print("[SimpleWebSocketServer] Server stopped")

    def is_running(self):
        """Check if the server is running."""
        return self._is_running and self.server is not None


def get_global_server(host, port, path="", debug=False) -> SimpleWebSocketServer:
    """Get or create a WebSocket server for the specified host:port.
    Each host:port combination has exactly one server that handles all paths.
    If port is already in use by another process, creates a client proxy instead.
    
    Args:
        host (str): The host address for the server
        port (int): The port number for the server
        path (str): The path for this handler to use (for routing)
        debug (bool): Whether to enable debug logging
        
    Returns:
        SimpleWebSocketServer or WebSocketClientProxy: The server instance or proxy
    """
    if not path:
        path = "/"
        
    # Normalize path for consistency
    path = path if path.startswith("/") else "/" + path
    
    # Use server address as the key - paths are handled by the same server
    server_key = f"{host}:{port}"
    
    with _server_lock:
        if server_key not in _port_servers:
            # Check if port is already in use
            if _port_is_in_use(host, port):
                if debug:
                    print(f"[get_global_server] Port {host}:{port} is in use, checking if it's a valid WebSocket server")
                
                # Check if it's a valid WebSocket server
                def check_websocket_server():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            is_valid = loop.run_until_complete(_is_valid_websocket_server(host, port, timeout=8))
                            return is_valid
                        finally:
                            loop.close()
                    except Exception as e:
                        if debug:
                            print(f"[get_global_server] WebSocket validation error: {e}")
                        return False
                
                is_valid = check_websocket_server()
                
                if is_valid:
                    if debug:
                        print(f"[get_global_server] Found valid WebSocket server at {host}:{port}, creating client proxy")
                    # Create client proxy instead of server
                    _port_servers[server_key] = WebSocketClientProxy(host, port, debug)
                else:
                    if debug:
                        print(f"[get_global_server] Port {host}:{port} validation failed, but assuming it might be a valid WebSocket server")
                    # Instead of raising an exception, create a client proxy anyway
                    # This is more permissive for existing WebSocket servers that don't support our validation
                    _port_servers[server_key] = WebSocketClientProxy(host, port, debug)
            else:
                # Port is free, create a new server for this host:port
                _port_servers[server_key] = SimpleWebSocketServer(host, port, debug)
        
        # Get the existing server/proxy and update debug setting
        server = _port_servers[server_key]
        server.debug = debug
        
        # Register this path with the server/proxy
        server.register_path(path)
        
        return server
