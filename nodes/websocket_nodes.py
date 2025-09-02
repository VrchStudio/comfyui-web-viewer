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
from .utils.websocket_server import get_global_server

# Category for organizational purposes
CATEGORY = "vrch.ai/viewer/websocket"
# The default server IP address
DEFAULT_SERVER_IP = VrchNodeUtils.get_default_ip_address(fallback_ip="0.0.0.0")
# The default server Port
DEFAULT_SERVER_PORT = 8001

class VrchWebSocketServerNode:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Server host selection: show resolved default IP value, not string literal
                "server": (["127.0.0.1", "0.0.0.0", f"{DEFAULT_SERVER_IP}"], {"default": f"{DEFAULT_SERVER_IP}"}),
                # Port selection with default
                "port": ("INT", {"default": int(DEFAULT_SERVER_PORT), "min": 1, "max": 65535}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("SERVER",)
    FUNCTION = "start_server"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def start_server(self, server, port, debug):
        # Compose full server string
        try:
            port = int(port)
        except Exception:
            port = int(DEFAULT_SERVER_PORT)
        server_str = f"{server}:{port}"
        # Detect change in server address or first initialization
        server_changed = server_str != getattr(self, '_last_server', None)
        host = server
        # Get or create the global server
        ws_server = get_global_server(host, port, debug=debug)
        # Register default paths on first init or server change
        if server_changed or not getattr(self, '_initialized', False):
            for p in ["/image", "/json", "/latent", "/audio", "/video", "/text"]:
                ws_server.register_path(p)
            self._initialized = True
            self._last_server = server_str
            if debug:
                print(f"[VrchWebSocketServerNode] Registered default paths on {host}:{port}")
        
        is_running = ws_server.is_running()
        if debug:
            print(f"[VrchWebSocketServerNode] Server on {host}:{port} status check. Running: {is_running}")
        return {
            "ui": {
                "server_status": [is_running],
                "debug_status": [debug],
                "server_full": [server_str],
            },
            "result": (server_str,)
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
                "number_of_images": ("INT", {"default": 1, "min": 1, "max": 99}),
                "image_display_duration":("INT", {"default": 1000, "min": 1, "max": 10000}),
                "fade_anim_duration": ("INT", {"default": 200, "min": 1, "max": 10000}),
                "blend_mode": (["none", "normal", "multiply", "screen", "overlay", "darken", "lighten", 
                                "color-dodge", "color-burn", "hard-light", "soft-light", "difference", 
                                "exclusion", "hue", "saturation", "color", "luminosity"], {"default": "none"}),
                "loop_playback": ("BOOLEAN", {"default": True}),
                "update_on_end": ("BOOLEAN", {"default": False}),
                "background_colour_hex": ("STRING", {"default": "#222222", "multiline": False}),
                "server_messages": ("STRING", {"default": "", "multiline": False}),
                "save_settings": ("BOOLEAN", {"default": False}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url":("BOOLEAN", {"default": False}),
                "dev_mode": ("BOOLEAN", {"default": False}),
                "debug": ("BOOLEAN", {"default": False}),
                "extra_params":("STRING", {"multiline": True, "dynamicPrompts": False}),
                "url": ("STRING", {"default": "", "multiline": True}),
            }
        }
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("IMAGES", "URL")
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
                    blend_mode,
                    loop_playback,
                    update_on_end,
                    background_colour_hex,
                    server_messages,
                    save_settings,
                    window_width,
                    window_height,
                    show_url,
                    dev_mode,
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
                    "mixBlendMode": blend_mode,
                    "enableLoop": loop_playback,
                    "enableUpdateOnEnd": update_on_end,
                    "bgColourPicker": background_colour_hex,
                    "serverMessages": server_messages,
                }
            }
            settings_json = json.dumps(settings)
            server.send_to_channel("/image", ch, settings_json)
            if debug:
                print(f"[VrchImageWebSocketWebViewerNode] Sending settings to channel {ch} via global server on {host}:{port} with path '/image': {settings_json}")
            
        if debug:
            print(f"[VrchImageWebSocketWebViewerNode] Sent {len(images)} images to channel {ch} via global server on {host}:{port} with path '/image'")
        return (images, url)


class VrchImageWebSocketSimpleWebViewerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "format": (["PNG", "JPEG"], {"default": "JPEG"}),
                "number_of_images": ("INT", {"default": 1, "min": 1, "max": 99}),
                "image_display_duration":("INT", {"default": 1000, "min": 1, "max": 10000}),
                "fade_anim_duration": ("INT", {"default": 200, "min": 1, "max": 10000}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url":("BOOLEAN", {"default": False}),
                "dev_mode": ("BOOLEAN", {"default": False}),
                "debug": ("BOOLEAN", {"default": False}),
                "extra_params":("STRING", {"multiline": True, "dynamicPrompts": False}),
                "url": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("IMAGES", "URL")
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
                    window_width,
                    window_height,
                    show_url,
                    dev_mode,
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
            
        if debug:
            print(f"[VrchImageWebSocketSimpleWebViewerNode] Sent {len(images)} images to channel {ch} via global server on {host}:{port} with path '/image'")
        return (images, url)


class VrchImageWebSocketSettingsNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "send_settings": ("BOOLEAN", {"default": True}),
                "number_of_images": ("INT", {"default": 1, "min": 1, "max": 99}),
                "image_display_duration":("INT", {"default": 1000, "min": 1, "max": 10000}),
                "fade_anim_duration": ("INT", {"default": 200, "min": 1, "max": 10000}),
                "blend_mode": (["none", "normal", "multiply", "screen", "overlay", "darken", "lighten", 
                                "color-dodge", "color-burn", "hard-light", "soft-light", "difference", 
                                "exclusion", "hue", "saturation", "color", "luminosity"], {"default": "none"}),
                "loop_playback": ("BOOLEAN", {"default": True}),
                "update_on_end": ("BOOLEAN", {"default": False}),
                "background_colour_hex": ("STRING", {"default": "#222222", "multiline": False}),
                "server_messages": ("STRING", {"default": "", "multiline": False}),
                "debug": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "image_filters_json": ("JSON",),
            }
        }

    RETURN_TYPES = ("JSON",)
    RETURN_NAMES = ("IMAGE_SETTINGS_JSON",)
    FUNCTION = "send_settings"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def send_settings(self,
                      channel,
                      server,
                      send_settings,
                      number_of_images,
                      image_display_duration,
                      fade_anim_duration,
                      blend_mode,
                      loop_playback,
                      update_on_end,
                      background_colour_hex,
                      server_messages,
                      debug,
                      image_filters_json=None):
        # Check if settings should be sent
        if not send_settings:
            if debug:
                print(f"[VrchImageWebSocketSettingsNode] Settings sending is disabled, skipping")
            return ()
            
        host, port = server.split(":")
        server = get_global_server(host, port, path="/image", debug=debug) # Ensure path is set correctly for viewer
        ch = int(channel)
        
        # Send server settings
        settings = {
            "settings": {
                "numberOfImages": number_of_images,
                "imageDisplayDuration": image_display_duration,
                "fadeAnimDuration": fade_anim_duration,
                "mixBlendMode": blend_mode,
                "enableLoop": loop_playback,
                "enableUpdateOnEnd": update_on_end,
                "bgColourPicker": background_colour_hex,
                "serverMessages": server_messages,
            }
        }

        # Merge filters if provided (supports either {"filters": {...}} or direct mapping {...})
        if image_filters_json is not None:
            try:
                if isinstance(image_filters_json, dict):
                    if "filters" in image_filters_json and isinstance(image_filters_json["filters"], dict):
                        settings["settings"]["filters"] = image_filters_json["filters"]
                    else:
                        settings["settings"]["filters"] = image_filters_json
                else:
                    if debug:
                        print("[VrchImageWebSocketSettingsNode] image_filters_json provided but not a dict; ignoring")
            except Exception as e:
                if debug:
                    print(f"[VrchImageWebSocketSettingsNode] Failed to merge image_filters_json: {e}")
        settings_json = json.dumps(settings)
        server.send_to_channel("/image", ch, settings_json)
        if debug:
            print(f"[VrchImageWebSocketSettingsNode] Sending settings to channel {ch} via global server on {host}:{port} with path '/image': {settings_json}")
        # Return the Python dict (already merged) so downstream nodes can reuse/augment
        return (settings,)

class VrchImageWebSocketFilterSettingsNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Pure parameter node (no channel/server). Ranges mirror applyRemoteFilters().
                "blur": ("INT", {"default": 0, "min": 0, "max": 50}),
                "brightness": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "contrast": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "grayscale": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "hue_rotate": ("INT", {"default": 0, "min": 0, "max": 360}),
                "invert": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "saturate": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "sepia": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("JSON",)
    RETURN_NAMES = ("IMAGE_FILTERS_JSON",)
    FUNCTION = "build_filters_json"
    OUTPUT_NODE = False
    CATEGORY = CATEGORY

    def build_filters_json(self,
                           blur,
                           brightness,
                           contrast,
                           grayscale,
                           hue_rotate,
                           invert,
                           saturate,
                           sepia):
        # Produce object matching previous spec {"filters": {...}} for backward compatibility
        payload = {
            "filters": {
                "blur": int(blur),
                "brightness": float(brightness),
                "contrast": float(contrast),
                "grayscale": float(grayscale),
                "hueRotate": int(hue_rotate),
                "invert": float(invert),
                "saturate": float(saturate),
                "sepia": float(sepia),
            }
        }
        return (payload,)

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

def latent_data_handler(message):
    """Default handler for processing latent messages"""
    try:
        # Parse the JSON string to get latent data
        latent_data = json.loads(message)
        
        # Convert back to tensor format expected by ComfyUI
        if "samples" in latent_data:
            samples_list = latent_data["samples"]
            # Convert list back to numpy array then to tensor
            samples_np = np.array(samples_list, dtype=np.float32)
            samples_tensor = torch.from_numpy(samples_np)
            
            latent = {"samples": samples_tensor}
            return latent
        return None
    except (json.JSONDecodeError, KeyError, ValueError):
        # If parsing fails, return None
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

class VrchLatentWebSocketSenderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent": ("LATENT",),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("LATENT",)
    FUNCTION = "send_latent"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY
    
    def send_latent(self, latent, channel, server, debug):
        host, port = server.split(":")
        server = get_global_server(host, port, path="/latent", debug=debug)
        ch = int(channel)
        
        # Validate the latent data
        if not latent or "samples" not in latent:
            raise ValueError("[VrchLatentWebSocketSenderNode] Invalid latent data provided")
            
        try:
            # Convert latent tensor to JSON-serializable format
            samples_tensor = latent["samples"]
            samples_list = samples_tensor.cpu().numpy().tolist()
            
            latent_data = {
                "samples": samples_list,
                "shape": list(samples_tensor.shape)
            }
            latent_json = json.dumps(latent_data)
            
            # Send the latent data to WebSocket clients
            server.send_to_channel("/latent", ch, latent_json)
            
            if debug:
                print(f"[VrchLatentWebSocketSenderNode] Sent latent to channel {ch} via server on {host}:{port} with path '/latent'")
                print(f"[VrchLatentWebSocketSenderNode] Latent shape: {latent_data['shape']}")
            
            return (latent,)
            
        except Exception as e:
            raise ValueError(f"[VrchLatentWebSocketSenderNode] Error processing latent data: {str(e)}")

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

class VrchLatentWebSocketChannelLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "debug": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                 "default_latent": ("LATENT",),
            }
        }
    
    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("LATENT",)
    FUNCTION = "receive_latent"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY
    
    def receive_latent(self, channel=1, server="", debug=False, default_latent=None):
        host, port = server.split(":")
        client = get_websocket_client(host, port, "/latent", channel, data_handler=latent_data_handler, debug=debug)
        
        # Get latent data from WebSocket client
        latent_data = client.get_latest_data()
        
        # If we received data from WebSocket, return it
        if latent_data is not None:
            if debug:
                print(f"[VrchLatentWebSocketChannelLoaderNode] Received latent data on channel {channel}")
                if "samples" in latent_data:
                    print(f"[VrchLatentWebSocketChannelLoaderNode] Latent shape: {latent_data['samples'].shape}")
            return (latent_data,)
        
        # If we didn't receive data, use the default latent (if provided)
        if default_latent is not None:
            if debug:
                print(f"[VrchLatentWebSocketChannelLoaderNode] No latent data received, using default latent")
            return (default_latent,)
        
        # If no default provided, create empty latent
        if debug:
            print(f"[VrchLatentWebSocketChannelLoaderNode] No latent data received and no default provided, creating empty latent")
        
        # Create a minimal empty latent with proper shape
        empty_latent = {"samples": torch.zeros((1, 4, 64, 64), dtype=torch.float32)}
        return (empty_latent,)
    
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
