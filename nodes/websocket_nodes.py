import io
import time
import struct
import numpy as np
import asyncio
import websockets
import threading
import urllib.parse
from PIL import Image
from .node_utils import VrchNodeUtils

# Category for organizational purposes
CATEGORY = "vrch.ai/viewer/websocket"
# The default server IP address
DEFAULT_SERVER_IP = VrchNodeUtils.get_default_ip_address(fallback_ip="0.0.0.0")
# The default server Port
DEFAULT_SERVER_PORT = 8001
# Global websocket server instance
_global_server = None

def get_global_server(host=DEFAULT_SERVER_IP, port=DEFAULT_SERVER_PORT, path="", debug=False):
    global _global_server
    if _global_server is None:
        _global_server = SimpleWebSocketServer(host, port, path, debug)
    else:
        _global_server.debug = debug
    return _global_server

class SimpleWebSocketServer:
    def __init__(self, host, port, path, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        # Ensure fixed_path starts with "/"
        self.path = path if path.startswith("/") else "/" + path
        # Use channels 1 to 8
        self.clients = {i: [] for i in range(1, 9)}
        self.loop = asyncio.new_event_loop()
        self.server = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self._start_server())
        if self.debug:
            print(f"[DEBUG] Server task scheduled on {self.host}:{self.port} with path {self.path}")
        self.loop.run_forever()

    async def _start_server(self):
        try:
            self.server = await websockets.serve(self._handler, self.host, self.port)
            if self.debug:
                print(f"[DEBUG] Server started on {self.host}:{self.port} with path {self.fixed_path}")
        except Exception as e:
            print(f"[DEBUG] Failed to start server: {e}")

    async def _handler(self, websocket, path=None):
        # Get resource path from websocket.request
        resource_path = websocket.request.path if hasattr(websocket, "request") and websocket.request else ""
        # remove query parameters from resource path
        resource_path = resource_path.split("?")[0]
        # Check that resource path matches fixed_path
        if resource_path != self.path:
            if self.debug:
                print(f"[DEBUG] Reject connection: got '{resource_path}', expected '{self.fixed_path}'")
            await websocket.close()
            return
        # Parse query parameter "channel"
        parsed = urllib.parse.urlparse(websocket.request.path)
        params = urllib.parse.parse_qs(parsed.query)
        channel_str = params.get("channel", [None])[0]
        try:
            channel = int(channel_str)
            if channel < 1 or channel > 8:
                raise ValueError
        except:
            if self.debug:
                print(f"[DEBUG] Reject connection: invalid channel '{channel_str}'")
            await websocket.close()
            return
        if self.debug:
            print(f"[DEBUG] New connection from {websocket.remote_address} on path '{resource_path}' with channel {channel}")
        self.clients[channel].append(websocket)
        try:
            async for _ in websocket:
                pass
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Exception on channel {channel}: {e}")
        finally:
            if websocket in self.clients[channel]:
                self.clients[channel].remove(websocket)
            if self.debug:
                print(f"[DEBUG] Connection closed from {websocket.remote_address} on channel {channel}")

    def send_to_channel(self, channel, data):
        if self.debug:
            print(f"[DEBUG] Sending {len(data)} bytes to channel {channel} with {len(self.clients[channel])} client(s)")
        for ws in list(self.clients[channel]):
            asyncio.run_coroutine_threadsafe(ws.send(data), self.loop)

    def stop(self):
        if self.debug:
            print("[DEBUG] Stopping server")
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()

class VrchImageWebSocketWebViewerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "host": ("STRING", {"default": DEFAULT_SERVER_IP, "multiline": False}),
                "port": ("INT", {"default": DEFAULT_SERVER_PORT, "min": 1, "max": 65535}),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "format": (["PNG", "JPEG"], {"default": "PNG"}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }
    RETURN_TYPES = ()
    FUNCTION = "send_images"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def send_images(self, images, format, host, port, channel, debug):
        results = []
        server = get_global_server(host, port, path="image", debug=debug)
        ch = int(channel)
        for tensor in images:
            arr = 255.0 * tensor.cpu().numpy()
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            buf = io.BytesIO()
            img.save(buf, format=format)
            binary_data = buf.getvalue()
            header = struct.pack(">II", 1, 2)
            data = header + binary_data
            server.send_to_channel(ch, data)
        if debug:
            print(f"[DEBUG] Sent {len(images)} images to channel {ch} via global server on {host}:{port} with path '/image'")
        return {}
