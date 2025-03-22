import io
import time
import struct
import numpy as np
import asyncio
import websockets
import threading
import torch
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
        # Ensure path starts with "/"
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
            print(f"[SimpleWebSocketServer] Server task scheduled on {self.host}:{self.port} with path {self.path}")
        self.loop.run_forever()

    async def _start_server(self):
        try:
            self.server = await websockets.serve(self._handler, self.host, self.port)
            if self.debug:
                print(f"[SimpleWebSocketServer] Server started on {self.host}:{self.port} with path {self.path}")
        except Exception as e:
            print(f"[SimpleWebSocketServer] Failed to start server: {e}")

    async def _handler(self, websocket, path=None):
        # Get resource path from websocket.request
        resource_path = websocket.request.path if hasattr(websocket, "request") and websocket.request else ""
        # remove query parameters from resource path
        resource_path = resource_path.split("?")[0]
        # Check that resource path matches fixed_path
        if resource_path != self.path:
            if self.debug:
                print(f"[SimpleWebSocketServer] Reject connection: got '{resource_path}', expected '{self.path}'")
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
                print(f"[SimpleWebSocketServer] Reject connection: invalid channel '{channel_str}'")
            await websocket.close()
            return
        if self.debug:
            print(f"[SimpleWebSocketServer] New connection from {websocket.remote_address} on path '{resource_path}' with channel {channel}")
        self.clients[channel].append(websocket)
        try:
            async for _ in websocket:
                pass
        except Exception as e:
            if self.debug:
                print(f"[SimpleWebSocketServer] Exception on channel {channel}: {e}")
        finally:
            if websocket in self.clients[channel]:
                self.clients[channel].remove(websocket)
            if self.debug:
                print(f"[SimpleWebSocketServer] Connection closed from {websocket.remote_address} on channel {channel}")

    def send_to_channel(self, channel, data):
        if self.debug:
            print(f"[SimpleWebSocketServer] Sending {len(data)} bytes to channel {channel} with {len(self.clients[channel])} client(s)")
        for ws in list(self.clients[channel]):
            asyncio.run_coroutine_threadsafe(ws.send(data), self.loop)

    def stop(self):
        if self.debug:
            print("[SimpleWebSocketServer] Stopping server")
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()

class VrchImageWebSocketWebViewerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "format": (["PNG", "JPEG"], {"default": "JPEG"}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url":("BOOLEAN", {"default": False}),
                "debug": ("BOOLEAN", {"default": False}),
                "extra_params":("STRING", {"multiline": True, "dynamicPrompts": False}),
                "url": ("STRING", {"default": "", "multiline": True}),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGES",)
    FUNCTION = "send_images"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def send_images(self, 
                    images, 
                    channel, 
                    server, 
                    format, 
                    window_width,
                    window_height,
                    show_url,
                    debug,
                    extra_params,
                    url):
        results = []
        host, port = server.split(":")
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
            print(f"[VrchImageWebSocketWebViewerNode] Sent {len(images)} images to channel {ch} via global server on {host}:{port} with path '/image'")
        return (images,)

# Dictionary to keep track of WebSocket client instances
_websocket_clients = {}

class WebSocketClient:
    def __init__(self, host, port, path, channel, data_handler=None, debug=False):
        self.host = host
        self.port = int(port)
        self.path = path if path.startswith("/") else "/" + path
        self.channel = int(channel)
        self.debug = debug
        self.received_data = None
        self.data_handler = data_handler
        self.lock = threading.Lock()
        self.running = True
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self._connect_and_listen())
        self.loop.run_forever()
    
    async def _connect_and_listen(self):
        while self.running:
            try:
                uri = f"ws://{self.host}:{self.port}{self.path}?channel={self.channel}"
                if self.debug:
                    print(f"[WebSocketClient] Connecting to {uri}")
                
                async with websockets.connect(uri) as websocket:
                    if self.debug:
                        print(f"[WebSocketClient] Connected to {uri}")
                    
                    async for message in websocket:
                        try:
                            if not self.running:
                                break
                            
                            # Process the message using the data handler if provided,
                            # otherwise store the raw message
                            processed_data = None
                            if self.data_handler:
                                processed_data = self.data_handler(message)
                            else:
                                processed_data = message
                            
                            # Store the processed data
                            with self.lock:
                                self.received_data = processed_data
                            
                            if self.debug:
                                print(f"[WebSocketClient] Received data on {self.path} channel {self.channel}")
                        
                        except Exception as e:
                            if self.debug:
                                print(f"[WebSocketClient] Error processing message: {e}")
            
            except Exception as e:
                if self.debug:
                    print(f"[WebSocketClient] Connection error: {e}")
            
            # Wait before reconnecting
            await asyncio.sleep(5)
    
    def get_latest_data(self):
        with self.lock:
            return self.received_data
    
    def stop(self):
        self.running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=1)

def image_data_handler(message):
    """Default handler for processing image messages"""
    if len(message) < 8:  # At least 8 bytes for the header
        return None
        
    # Unpack header (2 uint32 values)
    header = struct.unpack(">II", message[:8])
    image_data = message[8:]
    
    # Convert image data to tensor
    image = Image.open(io.BytesIO(image_data))
    image_np = np.array(image).astype(np.float32) / 255.0
    image_tensor = torch.from_numpy(image_np)[None,]
    
    return image_tensor

def get_websocket_client(host, port, path, channel, data_handler=None, debug=False):
    key = f"{host}:{port}:{path}:{channel}"
    if key not in _websocket_clients:
        _websocket_clients[key] = WebSocketClient(host, port, path, channel, data_handler, debug)
    else:
        # Update debug setting if client already exists
        _websocket_clients[key].debug = debug
    return _websocket_clients[key]

class VrchImageWebSocketChannelLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    FUNCTION = "receive_image"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY
    
    def receive_image(self, channel, server, debug):
        host, port = server.split(":")
        client = get_websocket_client(host, port, "image", channel, data_handler=image_data_handler, debug=debug)
        
        image = client.get_latest_data()
        if image is not None:
            return (image,)
        else:
            # Return a small black image as placeholder
            placeholder = torch.zeros((1, 512, 512, 3), dtype=torch.float32)
            return (placeholder,)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always trigger evaluation to check for new images
        return float("NaN")