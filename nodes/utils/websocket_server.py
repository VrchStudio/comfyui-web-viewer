import asyncio
import threading
import urllib.parse
import websockets

# Track servers by host:port (not by path)
_port_servers = {}
_server_lock = threading.RLock()


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
            # Simple single-server approach
            self.server = await websockets.serve(self._handler, self.host, self.port)
            print(f"Server listening on {self.host}:{self.port}")
            
            self._is_running = True
            if self.debug:
                print(f"[SimpleWebSocketServer] Server started on {self.host}:{self.port}")
        except Exception as e:
            self._is_running = False
            print(f"[SimpleWebSocketServer] Failed to start server: {e}")

    async def _handler(self, websocket, path=None):
        # Get resource path from websocket.request
        resource_path = websocket.request.path if hasattr(websocket, "request") and websocket.request else ""
        # Remove query parameters from resource path
        resource_path = resource_path.split("?")[0]
        
        # Check if this path is registered with this server
        if resource_path not in self.paths:
            if self.debug:
                print(f"[SimpleWebSocketServer] Reject connection: path '{resource_path}' not registered")
            await websocket.close()
            return
        
        # Parse channel parameter
        parsed = urllib.parse.urlparse(websocket.request.path)
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
            async for _ in websocket:
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
            return
            
        if self.debug:
            client_count = len(self.clients[path][channel])
            print(f"[SimpleWebSocketServer] Sending {len(data)} bytes to {path} channel {channel} with {client_count} client(s)")
            
        for ws in list(self.clients[path][channel]):
            asyncio.run_coroutine_threadsafe(ws.send(data), self.loop)

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
        if self.server:
             self.server.close()
             self.loop.call_soon_threadsafe(asyncio.ensure_future, self.server.wait_closed())
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread.is_alive():
            self.thread.join(timeout=1)
        self._is_running = False

    def is_running(self):
        """Check if the server is running."""
        return self.server is not None and self._is_running


def get_global_server(host, port, path="", debug=False) -> SimpleWebSocketServer:
    """Get or create a WebSocket server for the specified host:port.
    Each host:port combination has exactly one server that handles all paths.
    
    Args:
        host (str): The host address for the server
        port (int): The port number for the server
        path (str): The path for this handler to use (for routing)
        debug (bool): Whether to enable debug logging
        
    Returns:
        SimpleWebSocketServer: The server instance
    """
    if not path:
        path = "/"
        
    # Normalize path for consistency
    path = path if path.startswith("/") else "/" + path
    
    # Use server address as the key - paths are handled by the same server
    server_key = f"{host}:{port}"
    
    with _server_lock:
        if server_key not in _port_servers:
            # Create a new server for this host:port
            _port_servers[server_key] = SimpleWebSocketServer(host, port, debug)
        
        # Get the existing server and update debug setting
        server = _port_servers[server_key]
        server.debug = debug
        
        # Register this path with the server
        server.register_path(path)
        
        return server
