import asyncio
import socket
import struct
import threading
import urllib.parse
from concurrent.futures import TimeoutError as FutureTimeoutError

import websockets

# Track servers by host:port (not by path)
_port_servers = {}
_server_lock = threading.RLock()
_REALTIME_PATHS = {"/image", "/video"}


def _port_is_in_use(host, port):
    """Check if a port is already in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            return sock.connect_ex((host, port)) == 0
    except Exception:
        return False


async def _is_valid_websocket_server(host, port, timeout=5):
    """Check if there's a valid WebSocket server at the given address."""
    try:
        uri = f"ws://{host}:{port}/"
        websocket = await asyncio.wait_for(websockets.connect(uri), timeout=timeout)
        try:
            pass
        finally:
            await websocket.close()
        return True
    except Exception:
        pass

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

    try:
        uri = f"ws://{host}:{port}/"
        websocket = await asyncio.wait_for(
            websockets.connect(uri, subprotocols=[], extra_headers={}),
            timeout=timeout,
        )
        try:
            pass
        finally:
            await websocket.close()
        return True
    except websockets.exceptions.InvalidStatusCode:
        return True
    except Exception:
        pass

    return False


class WebSocketClientProxy:
    """Client proxy that connects to an existing WebSocket server."""

    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = int(port)
        self.debug = debug
        self.paths = set()
        self.clients = {}  # path -> channel -> [websocket connections] (compat only)

        self._is_running = True
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)

        self._connections = {}  # uri -> websocket connection
        self._endpoint_queues = {}  # uri -> asyncio.Queue
        self._endpoint_workers = {}  # uri -> asyncio.Task
        self._endpoint_realtime = {}  # uri -> bool

        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

        pending = [task for task in asyncio.all_tasks(self._loop) if not task.done()]
        for task in pending:
            task.cancel()
        if pending:
            self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

        self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        self._loop.close()

    def register_path(self, path):
        """Register a path for this proxy."""
        if path not in self.paths:
            self.paths.add(path)
            self.clients[path] = {i: [] for i in range(1, 9)}
            if self.debug:
                print(f"[WebSocketClientProxy] Registered path {path} for {self.host}:{self.port}")

    def _is_realtime_path(self, path):
        clean_path = str(path).split("?", 1)[0]
        return clean_path in _REALTIME_PATHS

    def _is_realtime_payload(self, path, data):
        clean_path = str(path).split("?", 1)[0]
        if clean_path not in _REALTIME_PATHS:
            return False

        # /image may include multi-frame batches; dropping intra-batch frames
        # can make viewers unable to render a complete image set.
        if clean_path == "/image":
            if isinstance(data, str):
                return False
            if isinstance(data, (bytes, bytearray)) and len(data) >= 8:
                try:
                    _, meta = struct.unpack(">II", data[:8])
                    frame_total = meta & 0xFF
                    return frame_total <= 1
                except Exception:
                    return True
        return True

    def _ensure_endpoint_worker(self, uri, realtime=False):
        queue = self._endpoint_queues.get(uri)
        if queue is None:
            queue = asyncio.Queue(maxsize=1 if realtime else 0)
            self._endpoint_queues[uri] = queue
            self._endpoint_realtime[uri] = bool(realtime)
            self._endpoint_workers[uri] = self._loop.create_task(self._endpoint_worker(uri, queue))
        return queue

    async def _endpoint_worker(self, uri, queue):
        websocket = None
        reconnect_backoff = 0.5

        while self._is_running:
            try:
                data = await queue.get()
            except asyncio.CancelledError:
                break

            if data is None and not self._is_running:
                break

            try:
                if self._endpoint_realtime.get(uri, False):
                    while True:
                        try:
                            newer_data = queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                        data = newer_data

                if websocket is None or websocket.closed:
                    websocket = await asyncio.wait_for(
                        websockets.connect(uri, ping_interval=20, ping_timeout=20),
                        timeout=5.0,
                    )
                    self._connections[uri] = websocket
                    reconnect_backoff = 0.5
                    if self.debug:
                        print(f"[WebSocketClientProxy] Connected: {uri}")

                await websocket.send(data)
            except Exception as e:
                if self.debug:
                    print(f"[WebSocketClientProxy] Send failed for {uri}: {e}")

                if websocket is not None:
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                websocket = None
                self._connections.pop(uri, None)

                # Keep behavior resilient for temporary disconnects.
                await asyncio.sleep(reconnect_backoff)
                reconnect_backoff = min(reconnect_backoff * 2, 5.0)

        if websocket is not None:
            try:
                await websocket.close()
            except Exception:
                pass
        self._connections.pop(uri, None)

    def _enqueue_message(self, uri, data, realtime=False):
        if not self._is_running:
            return
        queue = self._ensure_endpoint_worker(uri, realtime=realtime)
        if realtime:
            try:
                queue.put_nowait(data)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(data)
                except asyncio.QueueFull:
                    pass
            return
        queue.put_nowait(data)

    def send_to_channel(self, path, channel, data):
        """Send data to a channel via persistent WebSocket client connection."""
        if not self._is_running:
            return

        if path not in self.paths:
            if self.debug:
                print(f"[WebSocketClientProxy] Path '{path}' not registered")
            return

        try:
            channel_int = int(channel)
            if channel_int < 1 or channel_int > 8:
                return
        except Exception:
            return

        uri = f"ws://{self.host}:{self.port}{path}?channel={channel_int}"
        realtime = self._is_realtime_payload(path, data)

        try:
            self._loop.call_soon_threadsafe(self._enqueue_message, uri, data, realtime)
        except RuntimeError:
            if self.debug:
                print("[WebSocketClientProxy] Loop is closed; dropping message")

    async def _shutdown_async(self):
        workers = [task for task in self._endpoint_workers.values() if task and not task.done()]
        for task in workers:
            task.cancel()
        if workers:
            await asyncio.gather(*workers, return_exceptions=True)

        for ws in list(self._connections.values()):
            try:
                await ws.close()
            except Exception:
                pass

        self._connections.clear()
        self._endpoint_workers.clear()
        self._endpoint_queues.clear()
        self._endpoint_realtime.clear()

    def is_running(self):
        """Check if the proxy is operational."""
        return self._is_running

    def start(self):
        """Proxy is always ready."""
        return True

    def stop(self):
        """Stop the proxy."""
        if not self._is_running:
            return

        self._is_running = False

        if self._loop and self._loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(self._shutdown_async(), self._loop)
                future.result(timeout=5.0)
            except Exception as e:
                if self.debug:
                    print(f"[WebSocketClientProxy] Shutdown warning: {e}")

            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except RuntimeError:
                pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        if self.debug:
            print("[WebSocketClientProxy] Proxy stopped")


class SimpleWebSocketServer:
    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = int(port)
        self.debug = debug

        self.paths = set()
        self.clients = {}  # path -> channel -> [websockets]

        self._is_running = False
        self._connection_tasks = set()
        self._realtime_pending = {}
        self._realtime_send_tasks = {}

        self.loop = asyncio.new_event_loop()
        self.server = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def register_path(self, path):
        """Register a new path for this server to handle."""
        with _server_lock:
            if path not in self.paths:
                self.paths.add(path)
                self.clients[path] = {i: [] for i in range(1, 9)}
                if self.debug:
                    print(f"[SimpleWebSocketServer] Registered path {path} on {self.host}:{self.port}")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self._start_server())

        if self.debug:
            print(f"[SimpleWebSocketServer] Server task scheduled on {self.host}:{self.port}")

        self.loop.run_forever()

        pending = [task for task in asyncio.all_tasks(self.loop) if not task.done()]
        for task in pending:
            task.cancel()
        if pending:
            self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()

        self._is_running = False
        if self.debug:
            print(f"[SimpleWebSocketServer] Server loop stopped on {self.host}:{self.port}")

    async def _start_server(self):
        try:
            async def handler_wrapper(websocket, path=None):
                await self._handler(websocket, path)

            self.server = await websockets.serve(
                handler_wrapper,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=20,
            )
            print(f"Server listening on {self.host}:{self.port}")

            self._is_running = True
            if self.debug:
                print(f"[SimpleWebSocketServer] Server started on {self.host}:{self.port}")
        except Exception as e:
            self._is_running = False
            print(f"[SimpleWebSocketServer] Failed to start server: {e}")

    def _extract_request_path(self, websocket, path=None):
        if hasattr(websocket, "request") and websocket.request:
            return websocket.request.path
        if hasattr(websocket, "path") and websocket.path:
            return websocket.path
        if path is not None:
            return path
        return "/"

    def _is_realtime_path(self, path):
        clean_path = str(path).split("?", 1)[0]
        return clean_path in _REALTIME_PATHS

    def _is_realtime_payload(self, path, data):
        clean_path = str(path).split("?", 1)[0]
        if clean_path not in _REALTIME_PATHS:
            return False

        if clean_path == "/image":
            if isinstance(data, str):
                return False
            if isinstance(data, (bytes, bytearray)) and len(data) >= 8:
                try:
                    _, meta = struct.unpack(">II", data[:8])
                    frame_total = meta & 0xFF
                    return frame_total <= 1
                except Exception:
                    return True
        return True

    async def _broadcast_to_clients(self, target_clients, data, send_timeout=2.0):
        if not target_clients:
            return []

        send_tasks = [
            asyncio.create_task(asyncio.wait_for(client.send(data), timeout=send_timeout))
            for client in target_clients
        ]
        results = await asyncio.gather(*send_tasks, return_exceptions=True)

        failed_clients = []
        for client, result in zip(target_clients, results):
            if isinstance(result, Exception):
                failed_clients.append(client)

        return failed_clients

    async def _broadcast_channel(self, path, channel, data, exclude=None):
        channel_map = self.clients.get(path)
        if not channel_map:
            return

        channel_clients = channel_map.get(channel)
        if channel_clients is None:
            return

        snapshot = list(channel_clients)
        if exclude is not None:
            snapshot = [client for client in snapshot if client != exclude]

        if self._is_realtime_payload(path, data):
            self._broadcast_channel_realtime(path, channel, snapshot, data)
            return

        failed_clients = await self._broadcast_to_clients(snapshot, data, send_timeout=2.0)

        for failed in failed_clients:
            if failed in channel_clients:
                channel_clients.remove(failed)

    def _broadcast_channel_realtime(self, path, channel, clients, data):
        for client in clients:
            if getattr(client, "closed", False):
                channel_clients = self.clients.get(path, {}).get(channel, [])
                if client in channel_clients:
                    channel_clients.remove(client)
                continue

            task_key = (path, channel, client)
            previous_task = self._realtime_send_tasks.get(task_key)
            if previous_task is not None:
                if previous_task.done():
                    self._realtime_send_tasks.pop(task_key, None)
                else:
                    # Client is still busy sending previous frame: drop this frame for this client.
                    continue

            send_task = asyncio.create_task(client.send(data))
            self._realtime_send_tasks[task_key] = send_task
            send_task.add_done_callback(
                lambda t, p=path, ch=channel, c=client: self._on_realtime_send_done(p, ch, c, t)
            )

    def _on_realtime_send_done(self, path, channel, client, task):
        task_key = (path, channel, client)
        self._realtime_send_tasks.pop(task_key, None)

        if task.cancelled():
            return

        exc = task.exception()
        if exc is None:
            return

        if self.debug:
            print(f"[SimpleWebSocketServer] Realtime send error on {path} channel {channel}: {exc}")

        channel_clients = self.clients.get(path, {}).get(channel, [])
        if client in channel_clients:
            channel_clients.remove(client)

    async def _handler(self, websocket, path=None):
        task = asyncio.current_task()
        if task is not None:
            self._connection_tasks.add(task)

        resource_path = self._extract_request_path(websocket, path=path).split("?")[0]

        if self.debug:
            print(f"[SimpleWebSocketServer] Processing connection with path: '{resource_path}', registered paths: {list(self.paths)}")

        if resource_path not in self.paths:
            if self.debug:
                print(f"[SimpleWebSocketServer] Reject connection: path '{resource_path}' not registered")
            await websocket.close()
            if task is not None and task in self._connection_tasks:
                self._connection_tasks.remove(task)
            return

        full_path = self._extract_request_path(websocket, path=path)
        parsed = urllib.parse.urlparse(full_path)
        params = urllib.parse.parse_qs(parsed.query)
        channel_str = params.get("channel", [None])[0]

        try:
            channel = int(channel_str)
            if channel < 1 or channel > 8:
                raise ValueError
        except Exception:
            if self.debug:
                print(f"[SimpleWebSocketServer] Reject connection: invalid channel '{channel_str}'")
            await websocket.close()
            if task is not None and task in self._connection_tasks:
                self._connection_tasks.remove(task)
            return

        if self.debug:
            print(f"[SimpleWebSocketServer] New connection from {websocket.remote_address} on path '{resource_path}' with channel {channel}")

        self.clients[resource_path][channel].append(websocket)
        print(f"Connection open on {resource_path} channel {channel}")

        message_task = None
        try:
            async def message_handler():
                async for message in websocket:
                    if self.debug:
                        if isinstance(message, bytes):
                            print(f"[SimpleWebSocketServer] Received binary message on {resource_path} channel {channel}: {len(message)} bytes")
                        elif isinstance(message, str):
                            if len(message) > 256:
                                print(
                                    f"[SimpleWebSocketServer] Received text message on {resource_path} channel {channel}: "
                                    f"{len(message)} chars (truncated: {message[:200]}...)"
                                )
                            else:
                                print(f"[SimpleWebSocketServer] Received text message on {resource_path} channel {channel}: {message}")
                        else:
                            print(
                                f"[SimpleWebSocketServer] Received message on {resource_path} channel {channel}: "
                                f"{type(message).__name__} ({len(str(message))} chars)"
                            )

                    await self._broadcast_channel(resource_path, channel, message, exclude=websocket)

            message_task = asyncio.create_task(message_handler())

            try:
                await websocket.wait_closed()
            except Exception:
                pass
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            if self.debug:
                print(f"[SimpleWebSocketServer] Exception on {resource_path} channel {channel}: {e}")
        finally:
            if message_task is not None and not message_task.done():
                message_task.cancel()
                await asyncio.gather(message_task, return_exceptions=True)

            channel_clients = self.clients.get(resource_path, {}).get(channel, [])
            if websocket in channel_clients:
                channel_clients.remove(websocket)

            if task is not None and task in self._connection_tasks:
                self._connection_tasks.remove(task)

            if self.debug:
                print(f"[SimpleWebSocketServer] Connection closed from {websocket.remote_address} on {resource_path} channel {channel}")

    async def _send_to_channel_async(self, path, channel, data):
        channel_map = self.clients.get(path)
        if not channel_map or channel not in channel_map:
            if self.debug:
                print(f"[SimpleWebSocketServer] Cannot send: path '{path}' not registered or channel {channel} not found")
            return

        clients = channel_map[channel]
        if self.debug:
            print(f"[SimpleWebSocketServer] Sending {len(str(data))} bytes to {path} channel {channel} with {len(clients)} client(s)")

        await self._broadcast_channel(path, channel, data, exclude=None)

    def _queue_realtime_send(self, path, channel, data):
        if not self._is_running:
            return

        key = (path, channel)
        state = self._realtime_pending.get(key)
        if state is None:
            state = {"latest": None, "sending": False}
            self._realtime_pending[key] = state

        state["latest"] = data
        if not state["sending"]:
            state["sending"] = True
            self.loop.create_task(self._flush_realtime_send(path, channel))

    async def _flush_realtime_send(self, path, channel):
        key = (path, channel)
        while self._is_running:
            state = self._realtime_pending.get(key)
            if not state:
                return

            payload = state.get("latest")
            state["latest"] = None
            if payload is None:
                state["sending"] = False
                return

            try:
                await self._send_to_channel_async(path, channel, payload)
            except Exception as e:
                if self.debug:
                    print(f"[SimpleWebSocketServer] Realtime send failed on {path} channel {channel}: {e}")

            state = self._realtime_pending.get(key)
            if not state:
                return
            if state.get("latest") is None:
                state["sending"] = False
                return

    def send_to_channel(self, path, channel, data):
        """Send data to all clients on a specific path and channel."""
        if not getattr(self, "_is_running", False):
            return
        loop = getattr(self, "loop", None)
        if not loop or not loop.is_running():
            return

        try:
            channel_int = int(channel)
        except Exception:
            return

        if self._is_realtime_payload(path, data):
            try:
                loop.call_soon_threadsafe(self._queue_realtime_send, path, channel_int, data)
            except RuntimeError:
                if self.debug:
                    print(f"[SimpleWebSocketServer] Realtime schedule failed for {path} channel {channel_int}")
            return

        future = None
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._send_to_channel_async(path, channel_int, data),
                loop,
            )
            future.result(timeout=2.0)
        except FutureTimeoutError:
            if future is not None:
                future.cancel()
            if self.debug:
                print(f"[SimpleWebSocketServer] Timed out while sending to {path} channel {channel_int}")
        except Exception as e:
            if self.debug:
                print(f"[SimpleWebSocketServer] Failed to schedule send: {e}")

    async def _shutdown_async(self):
        if self.server is not None:
            self.server.close()
            try:
                await self.server.wait_closed()
            except Exception:
                pass
            self.server = None

        all_clients = []
        for channel_map in self.clients.values():
            for client_list in channel_map.values():
                all_clients.extend(list(client_list))

        close_tasks = [asyncio.create_task(client.close()) for client in set(all_clients)]
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

        current_task = asyncio.current_task()
        tracked_tasks = [task for task in list(self._connection_tasks) if task is not current_task and not task.done()]
        for task in tracked_tasks:
            task.cancel()
        if tracked_tasks:
            await asyncio.gather(*tracked_tasks, return_exceptions=True)

        for path in self.clients:
            for channel in self.clients[path]:
                self.clients[path][channel].clear()
        self._realtime_pending.clear()

        pending_tasks = [task for task in self._realtime_send_tasks.values() if task and not task.done()]
        for task in pending_tasks:
            task.cancel()
        if pending_tasks:
            await asyncio.gather(*pending_tasks, return_exceptions=True)
        self._realtime_send_tasks.clear()

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

        if self.loop and self.loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(self._shutdown_async(), self.loop)
                future.result(timeout=6.0)
            except Exception as e:
                if self.debug:
                    print(f"[SimpleWebSocketServer] Shutdown warning: {e}")

            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except RuntimeError:
                pass

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        if self.debug:
            print("[SimpleWebSocketServer] Server stopped")

    def is_running(self):
        """Check if the server is running."""
        return self._is_running and self.server is not None


def get_global_server(host, port, path="", debug=False):
    """Get or create a WebSocket server for the specified host:port.

    Each host:port combination has exactly one server that handles all paths.
    If port is already in use by another process, creates a client proxy instead.
    """
    if not path:
        path = "/"

    path = path if path.startswith("/") else "/" + path

    server_key = f"{host}:{port}"

    with _server_lock:
        if server_key not in _port_servers:
            if _port_is_in_use(host, port):
                if debug:
                    print(f"[get_global_server] Port {host}:{port} is in use, checking if it's a valid WebSocket server")

                def check_websocket_server_in_thread():
                    result = {"ok": False}

                    def runner():
                        try:
                            result["ok"] = asyncio.run(_is_valid_websocket_server(host, port, timeout=8))
                        except Exception as e:
                            if debug:
                                print(f"[get_global_server] WebSocket validation error: {e}")
                            result["ok"] = False

                    thread = threading.Thread(target=runner, daemon=True)
                    thread.start()
                    thread.join(timeout=10)
                    if thread.is_alive():
                        if debug:
                            print("[get_global_server] WebSocket validation timed out")
                        return False
                    return result["ok"]

                is_valid = check_websocket_server_in_thread()

                if is_valid:
                    if debug:
                        print(f"[get_global_server] Found valid WebSocket server at {host}:{port}, creating client proxy")
                    _port_servers[server_key] = WebSocketClientProxy(host, port, debug)
                else:
                    if debug:
                        print(f"[get_global_server] Port {host}:{port} validation failed, using client proxy anyway")
                    _port_servers[server_key] = WebSocketClientProxy(host, port, debug)
            else:
                _port_servers[server_key] = SimpleWebSocketServer(host, port, debug)

        server = _port_servers[server_key]
        server.debug = debug
        server.register_path(path)

        return server
