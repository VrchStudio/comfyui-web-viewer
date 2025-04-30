import hashlib
import io
import json
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

def get_global_server(host=DEFAULT_SERVER_IP, port=DEFAULT_SERVER_PORT, path="", debug=False) -> SimpleWebSocketServer:
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

class VrchWebSocketServerNode:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("SERVER",)
    FUNCTION = "start_server"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def start_server(self, server, debug):
        host, port_str = server.split(":")
        port = int(port_str)
            
        # Note: The global server is shared. Starting this node essentially ensures
        # the server is running with the latest debug setting, but doesn't create
        # multiple independent servers on the same host/port.
        ws_server = get_global_server(host, port, debug=debug)
                
        # Check if the server is running
        is_running = ws_server.is_running()
        
        if debug:
            print(f"[VrchWebSocketServerNode] Server on {host}:{port} status check. Running: {is_running}")

        return {
            "ui": {
                "server_status": [is_running], # Pass status to UI
                "debug_status": [debug]        # Pass debug state to UI
            },
            "result": (server,)  # Return the server string
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")  # Always trigger evaluation to check server status


class VrchImageWebSocketWebViewerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "format": (["PNG", "JPEG"], {"default": "JPEG"}),
                "number_of_images": ("INT", {"default": 4, "min": 1, "max": 99}),
                "image_display_duration":("INT", {"default": 1000, "min": 1, "max": 10000}),
                "fade_anim_duration": ("INT", {"default": 200, "min": 1, "max": 10000}),
                "server_messages": ("STRING", {"default": "", "multiline": False}),
                "save_settings": ("BOOLEAN", {"default": False}),
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
                    number_of_images,
                    image_display_duration,
                    fade_anim_duration,
                    server_messages,
                    save_settings,
                    window_width,
                    window_height,
                    show_url,
                    debug,
                    extra_params,
                    url):
        results = []
        host, port = server.split(":")
        server = get_global_server(host, port, path="/image", debug=debug) # Ensure path is set correctly for viewer
        ch = int(channel)
        for tensor in images:
            arr = 255.0 * tensor.cpu().numpy()
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            buf = io.BytesIO()
            img.save(buf, format=format)
            binary_data = buf.getvalue()
            header = struct.pack(">II", 1, 2)
            data = header + binary_data
            server.send_to_channel("/image", ch, data)
            
        # Send server settings
        if save_settings:
            settings = {
                "settings": {
                    "numberOfImages": number_of_images,
                    "imageDisplayDuration": image_display_duration,
                    "fadeAnimDuration": fade_anim_duration,
                    "serverMessages": server_messages,
                }
            }
            settings_json = json.dumps(settings)
            server.send_to_channel("/image", ch, settings_json)
            if debug:
                print(f"[VrchImageWebSocketWebViewerNode] Sending settings to channel {ch} via global server on {host}:{port} with path '/image': {settings_json}")
            
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
        
def get_websocket_client(host, port, path, channel, data_handler=None, debug=False):
    key = f"{host}:{port}:{path}:{channel}"
    if key not in _websocket_clients:
        _websocket_clients[key] = WebSocketClient(host, port, path, channel, data_handler, debug)
    else:
        # Update debug setting if client already exists
        _websocket_clients[key].debug = debug
    return _websocket_clients[key]

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

def json_data_handler(message):
    """Default handler for processing JSON messages"""
    try:
        # Try to parse the message as JSON
        json_data = json.loads(message)
        return json_data
    except json.JSONDecodeError:
        # If it's not valid JSON, return None
        return None

class VrchJsonWebSocketSenderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "debug": ("BOOLEAN", {"default": False}),
                "json_string": ("STRING", {"default": "{}", "multiline": True}),
            }
        }
    
    RETURN_TYPES = ("JSON",)
    RETURN_NAMES = ("JSON",)
    FUNCTION = "send_json"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY
    
    def send_json(self, json_string, channel, server, debug):
        host, port = server.split(":")
        server = get_global_server(host, port, path="/json", debug=debug)
        ch = int(channel)
        
        # Validate the JSON string
        if not json_string or not json_string.strip():
            raise ValueError("[VrchJsonWebSocketSenderNode] Empty JSON string provided")
            
        try:
            # Try to parse the input as JSON
            json_data = json.loads(json_string)
            
            # Send the JSON data to WebSocket clients
            server.send_to_channel("/json", ch, json_string)
            
            if debug:
                print(f"[VrchJsonWebSocketSenderNode] Sent JSON to channel {ch} via server on {host}:{port} with path '/json'")
                print(f"[VrchJsonWebSocketSenderNode] JSON content: {json_string[:200]}{'...' if len(json_string) > 200 else ''}")
            
            return (json_data,)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"[VrchJsonWebSocketSenderNode] Invalid JSON format: {str(e)}")

class VrchJsonWebSocketChannelLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "debug": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                 "default_json_string": ("STRING", {"default": "{}", "multiline": True}),
            }
        }
    
    RETURN_TYPES = ("JSON",)
    RETURN_NAMES = ("JSON",)
    FUNCTION = "receive_json"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY
    
    def receive_json(self, channel=1, server="", debug=False, default_json_string=None):
        host, port = server.split(":")
        client = get_websocket_client(host, port, "/json", channel, data_handler=json_data_handler, debug=debug)
        
        # Get JSON data from WebSocket client
        json_data = client.get_latest_data()
        
        # If we received data from WebSocket, return it
        if json_data is not None:
            if debug:
                print(f"[VrchJsonWebSocketChannelLoaderNode] Received JSON data on channel {channel}")
                print(f"[VrchJsonWebSocketChannelLoaderNode] JSON content: {str(json_data)[:200]}{'...' if len(str(json_data)) > 200 else ''}")
            return (json_data,)
        
        # If we didn't receive data, use the default JSON string (if provided)
        if default_json_string:
            if debug:
                print(f"[VrchJsonWebSocketChannelLoaderNode] No JSON data received, using default JSON string")
            
            try:
                # Try to parse the default JSON string
                default_data = json.loads(default_json_string)
                return (default_data,)
            except json.JSONDecodeError as e:
                raise ValueError(f"[VrchJsonWebSocketChannelLoaderNode] Invalid default JSON format: {str(e)}")
        
        # If no default provided, return empty object
        if debug:
            print(f"[VrchJsonWebSocketChannelLoaderNode] No JSON data received and no default provided, returning empty object")
        return ({},)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always trigger evaluation to check for new data
        return float("NaN")

class VrchImageWebSocketChannelLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "placeholder": (["black", "white", "grey", "image"], {"default": "black"}),
                "debug": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "default_image": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("IMAGE","BOOLEAN")
    RETURN_NAMES = ("IMAGE","IS_DEFAULT_IMAGE")
    FUNCTION = "receive_image"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY
    
    def receive_image(self, channel, server, placeholder, debug, default_image=None):
        if placeholder == "image" and default_image is not None:
             # use tensor data_ptr to detect new image instance
             cur_id = default_image.data_ptr() if hasattr(default_image, 'data_ptr') else id(default_image)
             last_id = getattr(self, '_last_default_image_id', None)
             if cur_id != last_id:
                # update stored id and return new default_image immediately
                self._last_default_image_id = cur_id
                if debug:
                    print(f"[VrchImageWebSocketChannelLoaderNode] Detected new default_image, passing it downstream once")
                return (default_image, True)
            
        host, port = server.split(":")
        # Ensure path is set correctly for loader
        client = get_websocket_client(host, port, "/image", channel, data_handler=image_data_handler, debug=debug) 
        
        image = client.get_latest_data()
        if image is not None:
            return (image, False)
        
        # No image data, select placeholder
        if placeholder == "image":
            if default_image is None:
                raise ValueError("[VrchImageWebSocketChannelLoaderNode] Placeholder 'image' selected but no default_image provided")
            placeholder_img = default_image
            return (placeholder_img, True)  # Using default_image as placeholder, so IS_DEFAULT_IMAGE should be True
        elif placeholder == "white":
            placeholder_img = torch.ones((1, 512, 512, 3), dtype=torch.float32)
        elif placeholder == "grey":
            placeholder_img = torch.ones((1, 512, 512, 3), dtype=torch.float32) * 0.5
        else:  # default to black
            placeholder_img = torch.zeros((1, 512, 512, 3), dtype=torch.float32)
        
        if debug:
            print(f"[VrchImageWebSocketChannelLoaderNode] No image data received, using {placeholder} placeholder")
        return (placeholder_img, False)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always trigger evaluation to check for new images
        return float("NaN")