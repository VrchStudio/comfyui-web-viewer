import io
import time
import struct
import numpy as np
from PIL import Image
import asyncio
import websockets
import threading

# Category for organizational purposes
CATEGORY = "vrch.ai/viewer/websocket"

# Global websocket server instance
_global_server = None

def get_global_server(host="0.0.0.0", port=8189, debug=False):
    global _global_server
    if _global_server is None:
        _global_server = SimpleWebSocketServer(host, port, debug)
    return _global_server

class SimpleWebSocketServer:
    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.clients = []  # List of websocket connections
        self.loop = asyncio.new_event_loop()
        self.server = None
        # Start the server in a separate thread
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        # Set the event loop for this thread
        asyncio.set_event_loop(self.loop)
        # Schedule the server coroutine
        self.loop.create_task(self._start_server())
        if self.debug:
            print(f"[DEBUG] WebSocket server task scheduled on {self.host}:{self.port}")
        self.loop.run_forever()

    async def _start_server(self):
        try:
            # Start the websocket server; handler now accepts path as optional
            self.server = await websockets.serve(self._handler, self.host, self.port)
            if self.debug:
                print(f"[DEBUG] WebSocket server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"[DEBUG] Failed to start WebSocket server: {e}")

    async def _handler(self, websocket, path=None):
        # If path is not provided, set it to empty string
        if path is None:
            path = ""
        if self.debug:
            print(f"[DEBUG] New connection from {websocket.remote_address} on path: '{path}'")
        self.clients.append(websocket)
        try:
            async for _ in websocket:
                pass
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Exception in connection: {e}")
        finally:
            if websocket in self.clients:
                self.clients.remove(websocket)
            if self.debug:
                print(f"[DEBUG] Connection closed from {websocket.remote_address}")

    def send_to_all(self, data):
        if self.debug:
            print(f"[DEBUG] Sending {len(data)} bytes to {len(self.clients)} client(s)")
        for ws in list(self.clients):
            asyncio.run_coroutine_threadsafe(ws.send(data), self.loop)

    def stop(self):
        if self.debug:
            print("[DEBUG] Stopping WebSocket server")
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()

class VrchImageWebSocketWebViewerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "format": (["PNG", "JPEG"], {"default": "PNG"}),
                "host": ("STRING", {"default": "0.0.0.0", "multiline": False}),
                "port": ("INT", {"default": 8189, "min": 1, "max": 65535}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_images"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    # Process and send images via the global websocket server
    def send_images(self, images, format, host, port, debug):
        results = []
        server = get_global_server(host, port, debug)
        for tensor in images:
            # Convert tensor to a NumPy array and scale to [0,255]
            arr = 255.0 * tensor.cpu().numpy()
            # Create PIL image and get binary data
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            buf = io.BytesIO()
            img.save(buf, format=format)
            binary_data = buf.getvalue()
            # Prepend header: two 32-bit big-endian integers (values 1 and 2)
            header = struct.pack(">II", 1, 2)
            data = header + binary_data
            server.send_to_all(data)
            results.append({
                "source": "websocket",
                "content-type": f"image/{format.lower()}",
                "type": "output",
            })
        if debug:
            print(f"[DEBUG] Sent {len(images)} images via global server on {host}:{port}")
        return {"ui": {"images": results}}

    @classmethod
    def IS_CHANGED(cls, images, format, host, port, debug):
        return time.time()
