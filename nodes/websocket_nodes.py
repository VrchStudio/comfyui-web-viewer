import io
import time
import struct
import numpy as np
from PIL import Image
import asyncio
import websockets
import threading
import urllib.parse

# Fixed endpoint path for communication
FIXED_PATH = "/channel"

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
        self.fixed_path = FIXED_PATH
        # Dictionary: client_id -> list of websocket connections
        self.clients = {}
        self.loop = asyncio.new_event_loop()
        self.server = None
        # Start the server in a separate thread
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        # Set the event loop for this thread
        asyncio.set_event_loop(self.loop)

        # Define asynchronous function to start the server
        async def start_server():
            self.server = await websockets.serve(self._handler, self.host, self.port)
            if self.debug:
                print(f"[DEBUG] WebSocket server started on {self.host}:{self.port}{self.fixed_path}")

        # Schedule the server start task in the event loop
        self.loop.create_task(start_server())
        # Run the event loop indefinitely
        self.loop.run_forever()

    async def _handler(self, websocket, path):
        # Parse the URL to get the path and query parameters
        parsed = urllib.parse.urlparse(path)
        resource_path = parsed.path  # e.g., "/channel"
        # Reject connection if the path does not match the fixed path
        if resource_path != self.fixed_path:
            if self.debug:
                print(f"[DEBUG] Reject connection: got '{resource_path}', expected '{self.fixed_path}'")
            await websocket.close()
            return
        # Parse query parameters from the URL
        params = urllib.parse.parse_qs(parsed.query)
        client_id = params.get("client_id", ["default"])[0]
        if self.debug:
            print(f"[DEBUG] Accepted connection from client_id: {client_id} on {resource_path}")
        # Store the websocket connection in the clients dictionary
        if client_id not in self.clients:
            self.clients[client_id] = []
        self.clients[client_id].append(websocket)
        try:
            async for _ in websocket:
                # Keep the connection alive
                pass
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Exception for client {client_id}: {e}")
        finally:
            # Remove the websocket connection from the dictionary
            if client_id in self.clients and websocket in self.clients[client_id]:
                self.clients[client_id].remove(websocket)
                if self.debug:
                    print(f"[DEBUG] Client {client_id} disconnected")

    def send_to_client(self, client_id, data):
        if self.debug:
            print(f"[DEBUG] Sending {len(data)} bytes to client_id: {client_id}")
        if client_id in self.clients:
            for ws in list(self.clients[client_id]):
                asyncio.run_coroutine_threadsafe(ws.send(data), self.loop)

    def stop(self):
        if self.debug:
            print("[DEBUG] Stopping WebSocket server")
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()

# ComfyUI Node: Sends images over the websocket server
class VrchImageWebSocketWebViewerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "format": (["PNG", "JPEG"], {"default": "PNG"}),
                "client_id": ("STRING", {"default": "default", "multiline": False}),
                "host": ("STRING", {"default": "0.0.0.0", "multiline": False}),
                "port": ("INT", {"default": 8189, "min": 1, "max": 65535}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }
    RETURN_TYPES = ()
    FUNCTION = "send_images"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def send_images(self, images, format, client_id, host, port, debug):
        results = []
        # Get or create the global websocket server instance
        server = get_global_server(host, port, debug)
        for tensor in images:
            # Convert tensor to numpy array and scale values to [0, 255]
            arr = 255.0 * tensor.cpu().numpy()
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            buf = io.BytesIO()
            img.save(buf, format=format)
            binary_data = buf.getvalue()
            # Build header: two 32-bit big-endian integers (values 1 and 2)
            header = struct.pack(">II", 1, 2)
            data = header + binary_data
            server.send_to_client(client_id, data)
            results.append({
                "source": "websocket",
                "content-type": f"image/{format.lower()}",
                "type": "output",
            })
        if debug:
            print(f"[DEBUG] Sent {len(images)} images to client '{client_id}' via global server")
        return {"ui": {"images": results}}

    @classmethod
    def IS_CHANGED(cls, images, format, client_id, host, port, debug):
        return time.time()