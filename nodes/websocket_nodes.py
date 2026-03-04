import hashlib
import io
import json
import time
import struct
import base64
import numpy as np
import asyncio
import websockets
import threading
import torch
import urllib.parse
import ffmpeg
import torchaudio
from PIL import Image
from .node_utils import VrchNodeUtils
from .utils.websocket_server import get_global_server

# Category for organizational purposes
CATEGORY = "vrch.ai/viewer/websocket"
# The default server IP address
DEFAULT_SERVER_IP = VrchNodeUtils.get_default_ip_address(fallback_ip="0.0.0.0")
# The default server Port
DEFAULT_SERVER_PORT = 8001
JSON_STATE_MAX_KEYS = 128
JSON_STATE_CLEAR_KEY = "__clear__"

class VrchWebSocketServerNode:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Server host selection: show resolved default IP value, not string literal
                "server": (["127.0.0.1", "0.0.0.0", f"{DEFAULT_SERVER_IP}"], {"default": f"{DEFAULT_SERVER_IP}"}),
                # Port selection with default
                "port": ("INT", {"default": int(DEFAULT_SERVER_PORT), "min": 1, "max": 65535}),
                "external_server_only": ("BOOLEAN", {"default": False}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("SERVER",)
    FUNCTION = "start_server"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def start_server(self, server, port, external_server_only, debug):
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
        server_mode = "external_only" if external_server_only else "auto"
        ws_server = get_global_server(host, port, debug=debug, mode=server_mode)
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
        batch_size = len(images)
        batch_id = getattr(self, "_last_batch_id", 0)
        batch_id = (batch_id + 1) % 65536
        self._last_batch_id = batch_id

        for index, tensor in enumerate(images):
            arr = 255.0 * tensor.cpu().numpy()
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            buf = io.BytesIO()
            img.save(buf, format=format)
            binary_data = buf.getvalue()
            meta = (batch_id << 16) | ((index & 0xFF) << 8) | (batch_size & 0xFF)
            header = struct.pack(">II", 1, meta)
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
        batch_size = len(images)
        batch_id = getattr(self, "_last_batch_id", 0)
        batch_id = (batch_id + 1) % 65536
        self._last_batch_id = batch_id

        for index, tensor in enumerate(images):
            arr = 255.0 * tensor.cpu().numpy()
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            buf = io.BytesIO()
            img.save(buf, format=format)
            binary_data = buf.getvalue()
            meta = (batch_id << 16) | ((index & 0xFF) << 8) | (batch_size & 0xFF)
            header = struct.pack(">II", 1, meta)
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
                "incremental_update": ("BOOLEAN", {"default": False}),
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
                      incremental_update,
                      debug,
                      image_filters_json=None):
        if not hasattr(self, "_last_full_settings"):
            self._last_full_settings = {}

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
        full_settings = settings["settings"]
        key = (host, port, ch)

        if incremental_update:
            prev = self._last_full_settings.get(key, {})
            diff = {}

            for param_key, param_value in full_settings.items():
                if param_key == "filters" and isinstance(param_value, dict):
                    prev_filters = prev.get("filters", {}) if isinstance(prev, dict) else {}
                    filter_diff = {
                        f_key: f_val
                        for f_key, f_val in param_value.items()
                        if prev_filters.get(f_key) != f_val
                    }
                    if filter_diff:
                        diff.setdefault("filters", {}).update(filter_diff)
                else:
                    if prev.get(param_key) != param_value:
                        diff[param_key] = param_value

            if diff:
                payload = {"settings": diff}
                payload_json = json.dumps(payload)
                server.send_to_channel("/image", ch, payload_json)
                if debug:
                    print(f"[VrchImageWebSocketSettingsNode] Incremental update -> channel {ch}: {payload_json}")
                self._last_full_settings[key] = full_settings
                return (payload,)
            else:
                if debug:
                    print("[VrchImageWebSocketSettingsNode] Incremental update skipped (no changes detected)")
                return (None,)

        settings_json = json.dumps(settings)
        server.send_to_channel("/image", ch, settings_json)
        if debug:
            print(f"[VrchImageWebSocketSettingsNode] Sending settings to channel {ch} via global server on {host}:{port} with path '/image': {settings_json}")

        self._last_full_settings[key] = full_settings
        return (settings,)

class VrchImageWebSocketFilterSettingsNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Reordered & streamlined (grayscale removed)
                # New order requested:
                # opacity, brightness, contrast, saturate, hueRotate, invert, sepia, blur
                "opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "brightness": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "contrast": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "saturate": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "hue_rotate": ("INT", {"default": 0, "min": 0, "max": 360}),
                "invert": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "sepia": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "blur": ("INT", {"default": 0, "min": 0, "max": 50}),
                "incremental_update": ("BOOLEAN", {"default": False}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("JSON",)
    RETURN_NAMES = ("IMAGE_FILTERS_JSON",)
    FUNCTION = "build_filters_json"
    OUTPUT_NODE = False
    CATEGORY = CATEGORY

    def build_filters_json(self,
                           opacity,
                           brightness,
                           contrast,
                           saturate,
                           hue_rotate,
                           invert,
                           sepia,
                           blur,
                           incremental_update,
                           debug,
                           **legacy):
        """Build the filters JSON.

        Note: grayscale has been removed. Any legacy workflows providing a
        grayscale positional/keyword argument will be ignored gracefully via **legacy.
        """
        if not hasattr(self, "_last_filters"):
            self._last_filters = None

        # Produce object matching previous spec {"filters": {...}} for backward compatibility
        filters_full = {
            "opacity": float(opacity),
            "brightness": float(brightness),
            "contrast": float(contrast),
            "saturate": float(saturate),
            "hueRotate": int(hue_rotate),
            "invert": float(invert),
            "sepia": float(sepia),
            "blur": int(blur),
        }

        if incremental_update and isinstance(self._last_filters, dict):
            diff = {
                key: value
                for key, value in filters_full.items()
                if self._last_filters.get(key) != value
            }
            if diff:
                payload = {"filters": diff}
                if debug:
                    print(f"[VrchImageWebSocketFilterSettingsNode] Incremental filters diff: {payload}")
                self._last_filters = filters_full
                return (payload,)
            if debug:
                print("[VrchImageWebSocketFilterSettingsNode] Incremental update skipped (no filter changes)")
            return (None,)

        payload = {"filters": filters_full}
        if debug:
            print(f"[VrchImageWebSocketFilterSettingsNode] Full filters payload: {payload}")
        self._last_filters = filters_full
        return (payload,)

# Dictionary to keep track of WebSocket client instances
_websocket_clients = {}
_websocket_clients_lock = threading.RLock()

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
        self._ws = None
        self._listen_task = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self._listen_task = self.loop.create_task(self._connect_and_listen())
        self.loop.run_forever()
        pending = [task for task in asyncio.all_tasks(self.loop) if not task.done()]
        for task in pending:
            task.cancel()
        if pending:
            self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()
    
    async def _connect_and_listen(self):
        reconnect_delay = 1.0
        while self.running:
            try:
                uri = f"ws://{self.host}:{self.port}{self.path}?channel={self.channel}"
                if self.debug:
                    print(f"[WebSocketClient] Connecting to {uri}")
                
                async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as websocket:
                    self._ws = websocket
                    reconnect_delay = 1.0
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
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                if self.debug:
                    print(f"[WebSocketClient] Connection error: {e}")
            finally:
                self._ws = None
            
            # Backoff reconnect to avoid tight loops.
            if self.running:
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 5.0)
    
    def get_latest_data(self):
        with self.lock:
            return self.received_data
    
    async def _shutdown_async(self):
        ws = self._ws
        if ws is not None:
            try:
                await ws.close()
            except Exception:
                pass
        self._ws = None
        if self._listen_task is not None and not self._listen_task.done():
            self._listen_task.cancel()
            await asyncio.gather(self._listen_task, return_exceptions=True)

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.loop and self.loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(self._shutdown_async(), self.loop)
                future.result(timeout=2.0)
            except Exception:
                pass
        if self.loop and self.loop.is_running():
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except RuntimeError:
                pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)

def get_websocket_client(host, port, path, channel, data_handler=None, debug=False):
    key = f"{host}:{port}:{path}:{channel}"
    with _websocket_clients_lock:
        client = _websocket_clients.get(key)
        # Replace dead/stopped clients instead of reusing stale instances.
        if client is not None:
            thread_alive = bool(getattr(client, "thread", None) and client.thread.is_alive())
            if not client.running or not thread_alive:
                try:
                    client.stop()
                except Exception:
                    pass
                _websocket_clients.pop(key, None)
                client = None

        if client is None:
            client = WebSocketClient(host, port, path, channel, data_handler, debug)
            _websocket_clients[key] = client
        else:
            # Update debug setting if client already exists.
            client.debug = debug
            if hasattr(client.data_handler, "debug"):
                client.data_handler.debug = debug
        return client


def stop_all_websocket_clients():
    with _websocket_clients_lock:
        clients = list(_websocket_clients.values())
        _websocket_clients.clear()

    for client in clients:
        try:
            client.stop()
        except Exception:
            pass
        
def image_data_handler(message):
    """Default handler for processing image messages"""
    if not isinstance(message, (bytes, bytearray)):
        # Non-binary payload (e.g. JSON settings) is ignored by the image handler
        return None

    if len(message) < 8:  # At least 8 bytes for the header
        return None

    # Unpack header (2 uint32 values)
    first, second = struct.unpack(">II", message[:8])
    image_data = message[8:]

    batch_id = (second >> 16) & 0xFFFF
    frame_index = (second >> 8) & 0xFF
    frame_total = second & 0xFF
    
    # Convert image data to tensor
    image = Image.open(io.BytesIO(image_data))
    image_np = np.array(image).astype(np.float32) / 255.0
    image_tensor = torch.from_numpy(image_np)[None,]
    image_tensor._metadata = {
        "batch_id": batch_id,
        "frame_index": frame_index,
        "frame_total": frame_total,
        "raw_type": first,
    }
    return image_tensor

class JsonStateMerger:
    def __init__(self, max_keys=JSON_STATE_MAX_KEYS, clear_key=JSON_STATE_CLEAR_KEY, debug=False):
        self.state = {}
        self.max_keys = max_keys
        self.clear_key = clear_key
        self.debug = debug

    def __call__(self, message):
        try:
            payload = json.loads(message)
        except (json.JSONDecodeError, TypeError):
            if self.debug:
                print("[JsonStateMerger] Invalid JSON payload; ignoring")
            return dict(self.state) if self.state else None

        if not isinstance(payload, dict):
            if self.debug:
                print("[JsonStateMerger] Non-dict JSON payload ignored")
            return dict(self.state) if self.state else None

        if payload.get(self.clear_key):
            if self.debug:
                print(f"[JsonStateMerger] Clear key '{self.clear_key}' received; resetting state")
            self.state = {}

        for key, value in payload.items():
            if key == self.clear_key:
                continue
            if self.max_keys and self.max_keys > 0 and key not in self.state and len(self.state) >= self.max_keys:
                if self.debug:
                    print(f"[JsonStateMerger] Max keys {self.max_keys} reached; skipping new key '{key}'")
                continue
            self.state[key] = value

        return dict(self.state)

def make_json_state_handler(debug=False):
    return JsonStateMerger(max_keys=JSON_STATE_MAX_KEYS, clear_key=JSON_STATE_CLEAR_KEY, debug=debug)

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
            if "shape" in latent_data:
                latent["shape"] = latent_data["shape"]
            if "channels" in latent_data:
                latent["channels"] = latent_data["channels"]
            else:
                latent["channels"] = int(samples_tensor.shape[1]) if samples_tensor.ndim >= 2 else None
            return latent
        return None
    except (json.JSONDecodeError, KeyError, ValueError):
        # If parsing fails, return None
        return None

def audio_data_handler(message):
    """Default handler for processing audio messages"""
    try:
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        payload = json.loads(message)
        if isinstance(payload, dict) and payload.get("base64_data"):
            return payload
        return None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

class VrchLiveConsoleControlNode:
    PANE_CONFIG = [
        ("display_image_viewer", "viewer", True),
        ("display_image_viewer_aux", "viewerAux", False),
        ("display_image_settings", "settings", True),
        ("display_prompt_sender", "prompt", True),
        ("display_srt_player", "srt", False),
        ("display_sketch_sender", "sketch", False),
        ("display_image_sender", "image", True),
        ("display_audio_recorder", "audioRecorder", False),
        ("display_audio_player", "audioPlayer", False),
        ("display_midi_sender", "midi", False),
        ("display_gamepad_sender", "gamepad", False),
    ]

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "8"}),
            "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
        }
        for input_name, _target, default_visible in cls.PANE_CONFIG:
            required[input_name] = ("BOOLEAN", {"default": bool(default_visible)})
        required["only_send_changed"] = ("BOOLEAN", {"default": True})
        required["debug"] = ("BOOLEAN", {"default": False})
        return {"required": required}

    RETURN_TYPES = ("JSON",)
    RETURN_NAMES = ("JSON",)
    FUNCTION = "send_control"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def send_control(
        self,
        channel,
        server,
        display_image_viewer,
        display_image_viewer_aux,
        display_image_settings,
        display_prompt_sender,
        display_srt_player,
        display_sketch_sender,
        display_image_sender,
        display_audio_recorder,
        display_audio_player,
        display_midi_sender,
        display_gamepad_sender,
        only_send_changed,
        debug,
    ):
        host, port = server.split(":")
        ws_server = get_global_server(host, port, path="/json", debug=debug)
        ch = int(channel)

        pane_input_values = {
            "display_image_viewer": bool(display_image_viewer),
            "display_image_viewer_aux": bool(display_image_viewer_aux),
            "display_image_settings": bool(display_image_settings),
            "display_prompt_sender": bool(display_prompt_sender),
            "display_srt_player": bool(display_srt_player),
            "display_sketch_sender": bool(display_sketch_sender),
            "display_image_sender": bool(display_image_sender),
            "display_audio_recorder": bool(display_audio_recorder),
            "display_audio_player": bool(display_audio_player),
            "display_midi_sender": bool(display_midi_sender),
            "display_gamepad_sender": bool(display_gamepad_sender),
        }
        pane_state = {}
        for input_name, target_key, _default_visible in self.PANE_CONFIG:
            pane_state[target_key] = pane_input_values[input_name]

        cache_key = f"{host}:{port}|{ch}"
        if not hasattr(self, "_last_state_by_target"):
            self._last_state_by_target = {}
        previous = self._last_state_by_target.get(cache_key) or {}

        ops = []
        for pane_id, visible in pane_state.items():
            if only_send_changed and pane_id in previous and previous[pane_id] == visible:
                continue
            if only_send_changed and pane_id not in previous:
                # First run for this target still sends explicit state to avoid ambiguity.
                pass
            ops.append({
                "op": "pane.set_visibility",
                "target": pane_id,
                "args": {"visible": visible},
            })

        payload = {
            "live_console_control": {
                "version": "1.0",
                "request_id": f"lc-{int(time.time() * 1000)}",
                "timestamp_ms": int(time.time() * 1000),
                "ops": ops,
                "meta": {
                    "source": "VrchLiveConsoleControlNode",
                },
            }
        }

        if ops:
            ws_server.send_to_channel("/json", ch, json.dumps(payload))
            self._last_state_by_target[cache_key] = dict(pane_state)
            if debug:
                print(f"[VrchLiveConsoleControlNode] Sent {len(ops)} ops to channel {ch} via {host}:{port}")
        else:
            if debug:
                print(f"[VrchLiveConsoleControlNode] No changed pane states; skipped send for channel {ch}")

        return (payload,)

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
                "shape": list(samples_tensor.shape),
                "channels": int(samples_tensor.shape[1]) if samples_tensor.ndim >= 2 else None,
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
        client = get_websocket_client(host, port, "/json", channel, data_handler=make_json_state_handler(debug=debug), debug=debug)
        
        # Get JSON data from WebSocket client
        json_data = client.get_latest_data()
        fallback_reason = None
        
        # If we received data from WebSocket, process it
        if json_data is not None:
            if debug:
                print(f"[VrchJsonWebSocketChannelLoaderNode] Received JSON data on channel {channel}")
                print(f"[VrchJsonWebSocketChannelLoaderNode] JSON content: {str(json_data)[:200]}{'...' if len(str(json_data)) > 200 else ''}")
            return (json_data,)
        else:
            fallback_reason = "No JSON data received"

        # If we didn't receive data, use the default JSON string (if provided)
        if default_json_string:
            if debug:
                reason = fallback_reason or "No JSON data received"
                print(f"[VrchJsonWebSocketChannelLoaderNode] {reason}; using default JSON string")
            
            try:
                # Try to parse the default JSON string
                default_data = json.loads(default_json_string)
                return (default_data,)
            except json.JSONDecodeError as e:
                raise ValueError(f"[VrchJsonWebSocketChannelLoaderNode] Invalid default JSON format: {str(e)}")
        
        # If no default provided, return empty object
        if debug:
            reason = fallback_reason or "No JSON data received"
            print(f"[VrchJsonWebSocketChannelLoaderNode] {reason} and no default provided, returning empty object")
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
                "latent_format": (["SD1/SDXL", "SD3/FLUX"], {"default": "SD1/SDXL"}),
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
    
    def receive_latent(self, channel=1, server="", latent_format="SD1/SDXL", debug=False, default_latent=None):
        def _get_latent_channels(latent):
            if isinstance(latent, dict):
                samples = latent.get("samples")
                if isinstance(samples, torch.Tensor) and samples.ndim >= 2:
                    return int(samples.shape[1])
            return None

        def _make_empty_latent(channels, reference_latent=None, shape_hint=None, dtype_hint=None, device_hint=None):
            samples = None
            if isinstance(reference_latent, dict):
                samples = reference_latent.get("samples")
            if isinstance(samples, torch.Tensor) and samples.ndim >= 4:
                shape = list(samples.shape)
                shape[1] = channels
                return {"samples": torch.zeros(shape, dtype=samples.dtype, device=samples.device)}
            if isinstance(shape_hint, (list, tuple)) and len(shape_hint) >= 4:
                shape = list(shape_hint)
                shape[1] = channels
                dtype = dtype_hint if dtype_hint is not None else torch.float32
                device = device_hint if device_hint is not None else "cpu"
                return {"samples": torch.zeros(shape, dtype=dtype, device=device)}
            return {"samples": torch.zeros((1, channels, 64, 64), dtype=torch.float32)}
        
        def _target_channels():
            return 16 if latent_format == "SD3/FLUX" else 4

        host, port = server.split(":")
        client = get_websocket_client(host, port, "/latent", channel, data_handler=latent_data_handler, debug=debug)
        cache = getattr(self, "_last_latent_info", None)
        if cache is None:
            cache = {}
            self._last_latent_info = cache
        cache_key = (server, str(channel))
        
        def _update_cache(latent):
            if isinstance(latent, dict):
                samples = latent.get("samples")
                if isinstance(samples, torch.Tensor) and samples.ndim >= 4:
                    cache[cache_key] = {
                        "shape": tuple(samples.shape),
                        "dtype": samples.dtype,
                        "device": samples.device,
                    }
        
        # Get latent data from WebSocket client
        latent_data = client.get_latest_data()
        
        # If we received data from WebSocket, return it
        if latent_data is not None:
            if debug:
                print(f"[VrchLatentWebSocketChannelLoaderNode] Received latent data on channel {channel}")
                if "samples" in latent_data:
                    print(f"[VrchLatentWebSocketChannelLoaderNode] Latent shape: {latent_data['samples'].shape}")
            received_channels = _get_latent_channels(latent_data)
            if received_channels is None:
                if debug:
                    print("[VrchLatentWebSocketChannelLoaderNode] Invalid latent format; using fallback")
            else:
                target_channels = _target_channels()
                if received_channels == target_channels:
                    _update_cache(latent_data)
                    return (latent_data,)
                if debug:
                    print(f"[VrchLatentWebSocketChannelLoaderNode] Channel mismatch: expected {target_channels}, received {received_channels}")
                if default_latent is not None:
                    default_channels = _get_latent_channels(default_latent)
                    if default_channels == target_channels:
                        _update_cache(default_latent)
                        return (default_latent,)
                    if debug and default_channels is not None:
                        print(f"[VrchLatentWebSocketChannelLoaderNode] Default latent channels {default_channels} mismatch; creating empty latent")
                return (_make_empty_latent(target_channels, latent_data, shape_hint=getattr(latent_data.get("samples", None), "shape", None)),)
        
        # If we didn't receive data, use the default latent (if provided)
        if default_latent is not None:
            if debug:
                print(f"[VrchLatentWebSocketChannelLoaderNode] No latent data received, using default latent")
            target_channels = _target_channels()
            default_channels = _get_latent_channels(default_latent)
            if default_channels == target_channels:
                _update_cache(default_latent)
                return (default_latent,)
            if debug and default_channels is not None:
                print(f"[VrchLatentWebSocketChannelLoaderNode] Default latent channels {default_channels} mismatch; creating empty latent")
            return (_make_empty_latent(target_channels, default_latent),)
        
        # If no default provided, create empty latent
        if debug:
            print(f"[VrchLatentWebSocketChannelLoaderNode] No latent data received and no default provided, creating empty latent")
        
        # Create a minimal empty latent with cached shape (or fallback)
        info = cache.get(cache_key)
        shape_hint = info["shape"] if info else None
        dtype_hint = info["dtype"] if info else None
        device_hint = info["device"] if info else None
        channels = _target_channels()
        empty_latent = _make_empty_latent(channels, shape_hint=shape_hint, dtype_hint=dtype_hint, device_hint=device_hint)
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
            if debug and hasattr(image, "_metadata"):
                meta = getattr(image, "_metadata", {})
                print(
                    "[VrchImageWebSocketChannelLoaderNode] Received frame",
                    meta.get("frame_index"),
                    "of",
                    meta.get("frame_total"),
                    "(batch",
                    meta.get("batch_id"),
                    ")",
                )
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

class VrchAudioWebSocketChannelLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}", "multiline": False}),
                "debug": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "default_audio": ("AUDIO",),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    FUNCTION = "receive_audio"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def receive_audio(self, channel=1, server="", debug=False, default_audio=None):
        host, port = server.split(":")
        client = get_websocket_client(host, port, "/audio", channel, data_handler=audio_data_handler, debug=debug)
        payload = client.get_latest_data()

        if isinstance(payload, dict) and payload.get("base64_data"):
            audio = self._decode_base64_audio(payload["base64_data"], debug=debug)
            if audio is not None:
                return (audio,)

        if default_audio is not None:
            return (default_audio,)

        return (self._silent_audio(),)

    @staticmethod
    def _silent_audio(duration_sec: float = 0.5, sample_rate: int = 44100):
        num_samples = max(int(sample_rate * duration_sec), 1)
        waveform = torch.zeros(2, num_samples)
        return {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}

    @staticmethod
    def _decode_base64_audio(base64_data, debug=False):
        if not base64_data or not isinstance(base64_data, str) or not base64_data.strip():
            if debug:
                print("[VrchAudioWebSocketChannelLoaderNode] Empty base64 payload")
            return None

        try:
            audio_bytes = base64.b64decode(base64_data)
        except Exception as err:
            if debug:
                print(f"[VrchAudioWebSocketChannelLoaderNode] Base64 decode failed: {err}")
            return None

        if not audio_bytes:
            if debug:
                print("[VrchAudioWebSocketChannelLoaderNode] Decoded payload empty")
            return None

        input_buffer = io.BytesIO(audio_bytes)
        try:
            process = (
                ffmpeg
                .input('pipe:0', format='webm')
                .output('pipe:1', format='wav')
                .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
            )
            output, _ = process.communicate(input=input_buffer.read())
            if not output:
                if debug:
                    print("[VrchAudioWebSocketChannelLoaderNode] ffmpeg produced no output")
                return None
            wav_buffer = io.BytesIO(output)
            waveform, sample_rate = torchaudio.load(wav_buffer)
        except Exception as err:
            if debug:
                print(f"[VrchAudioWebSocketChannelLoaderNode] Audio decode failed: {err}")
            return None

        try:
            if waveform.dim() == 1:
                waveform = waveform.unsqueeze(0)
            if waveform.shape[0] == 1:
                waveform = waveform.repeat(2, 1)
            audio = {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}
            return audio
        except Exception as err:
            if debug:
                print(f"[VrchAudioWebSocketChannelLoaderNode] Waveform reshape failed: {err}")
            return None

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")
