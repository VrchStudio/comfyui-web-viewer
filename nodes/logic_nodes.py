import hashlib
import json
import time
import numpy as np
import torch
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image
from .node_utils import VrchNodeUtils
from .osc_control_nodes import AlwaysEqualProxy

CATEGORY="vrch.ai/logic"

class VrchIntRemapNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "input": ("INT",     {"default": None, "forceInput": True}),
            },
            "required": {
                "input_min":     ("INT",     {"default": 0,    "min": -999999, "max": 999999}),
                "input_max":     ("INT",     {"default": 1,    "min": -999999, "max": 999999}),
                "output_min":    ("INT",     {"default": 0,    "min": -999999, "max": 999999}),
                "output_max":    ("INT",     {"default": 100,  "min": -999999, "max": 999999}),
                "output_invert": ("BOOLEAN", {"default": False}),
                "output_default":("INT",     {"default": 0}),
            },
        }

    RETURN_TYPES=("INT",)
    RETURN_NAMES=("OUTPUT",)
    FUNCTION="remap_int"
    CATEGORY=CATEGORY

    def remap_int(self, input=None, input_min=0, input_max=1, output_min=0, output_max=100, output_invert=False, output_default=0):
        if input_min > input_max:
            raise ValueError("[VrchIntRemapNode] input_min cannot be greater than input_max.")
        if output_min > output_max:
            raise ValueError("[VrchIntRemapNode] output_min cannot be greater than output_max.")
        try:
            remap_func = VrchNodeUtils.select_remap_func(output_invert)
            mapped = remap_func(float(input), float(input_min), float(input_max), float(output_min), float(output_max))
            mapped_int = int(mapped)
            # Clamp within output range
            mapped_int = max(min(mapped_int, output_max), output_min)
            return (mapped_int,)
        except Exception:
            return (output_default,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        m = hashlib.sha256()
        for k in ("input","input_min","input_max","output_min","output_max","output_invert"):
            m.update(str(kwargs.get(k)).encode("utf-8"))
        return m.hexdigest()


class VrchFloatRemapNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "input": ("FLOAT",   {"default": None,   "forceInput": True}),
            },
            "required": {
                "input_min":     ("FLOAT",   {"default": 0.0,    "min": -999999.0, "max": 999999.0, "step": 0.01}),
                "input_max":     ("FLOAT",   {"default": 1.0,    "min": -999999.0, "max": 999999.0, "step": 0.01}),
                "output_min":    ("FLOAT",   {"default": 0.0,    "min": -999999.0, "max": 999999.0, "step": 0.01}),
                "output_max":    ("FLOAT",   {"default": 100.0,  "min": -999999.0, "max": 999999.0, "step": 0.01}),
                "output_invert": ("BOOLEAN", {"default": False}),
                "output_default":("FLOAT",   {"default": 0.0}),
            },
        }

    RETURN_TYPES=("FLOAT",)
    RETURN_NAMES=("OUTPUT",)
    FUNCTION="remap_float"
    CATEGORY=CATEGORY

    def remap_float(self, input=None, input_min=0.0, input_max=1.0, output_min=0.0, output_max=100.0, output_invert=False, output_default=0.0):
        if input_min > input_max:
            raise ValueError("[VrchFloatRemapNode] input_min cannot be greater than input_max.")
        if output_min > output_max:
            raise ValueError("[VrchFloatRemapNode] output_min cannot be greater than output_max.")
        try:
            remap_func = VrchNodeUtils.select_remap_func(output_invert)
            mapped = remap_func(input, input_min, input_max, output_min, output_max)
            # Clamp within output range
            mapped_clamped = max(min(mapped, output_max), output_min)
            return (mapped_clamped,)
        except Exception:
            return (output_default,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        m = hashlib.sha256()
        for k in ("input","input_min","input_max","output_min","output_max","output_invert"):
            m.update(str(kwargs.get(k)).encode("utf-8"))
        return m.hexdigest()


class VrchTriggerToggleNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "trigger": ("BOOLEAN", {"default": None, "forceInput": True}),
            },
            "required": {
                "initial_state": ("BOOLEAN", {"default": False}), 
                "debug":         ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "JSON",)
    RETURN_NAMES = ("OUTPUT", "JSON",)
    FUNCTION = "switch"
    CATEGORY = CATEGORY

    def __init__(self):
        self.last_initial_state = None
        self.state = False
        self.last_trigger = False

    def switch(self, trigger=None, initial_state=False, debug=False):
        
        # If initial_state input changed, reset current state
        if self.last_initial_state is None or initial_state != self.last_initial_state:
            self.state = initial_state
            self.last_initial_state = initial_state
            self.last_trigger = False
            
        # Edge‐detect the trigger: toggle only on rising edge
        current_trigger = bool(trigger)
        if current_trigger and not self.last_trigger:
           self.state = not self.state
        self.last_trigger = current_trigger
            
        if debug:
            print(f"[VrchTriggerToggleNode] Trigger: {trigger}, Initial State: {initial_state}, Current State: {self.state}")
        
        # Prepare JSON data
        raw_data = {
            "trigger": trigger,
            "initial_state": initial_state,
            "current_state": self.state,
        }
        json_data = json.dumps(raw_data, indent=2, ensure_ascii=False)
        
        result = {
            "ui": {
                "current_state": [self.state],
            },
            "result": (self.state, json_data,)
        }
        return result

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

class VrchTriggerToggleX4Node:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "trigger1": ("BOOLEAN", {"default": None, "forceInput": True}),
                "trigger2": ("BOOLEAN", {"default": None, "forceInput": True}),
                "trigger3": ("BOOLEAN", {"default": None, "forceInput": True}),
                "trigger4": ("BOOLEAN", {"default": None, "forceInput": True}),
            },
            "required": {
                "initial_state1": ("BOOLEAN", {"default": False}),
                "initial_state2": ("BOOLEAN", {"default": False}),
                "initial_state3": ("BOOLEAN", {"default": False}),
                "initial_state4": ("BOOLEAN", {"default": False}),
                "debug":          ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "BOOLEAN", "BOOLEAN", "BOOLEAN", "JSON")
    RETURN_NAMES = ("OUTPUT1", "OUTPUT2", "OUTPUT3", "OUTPUT4", "JSON")
    FUNCTION = "switch"
    CATEGORY = CATEGORY

    def __init__(self):
        self.last_initial_states = [None] * 4
        self.states               = [False] * 4
        self.last_triggers        = [False] * 4

    def switch(self,
               trigger1=None, trigger2=None, trigger3=None, trigger4=None,
               initial_state1=False, initial_state2=False, initial_state3=False, initial_state4=False,
               debug=False):
        triggers = [trigger1, trigger2, trigger3, trigger4]
        initials = [initial_state1, initial_state2, initial_state3, initial_state4]

        # reset on initial_state change and clear trigger latch
        for i in range(4):
            if self.last_initial_states[i] is None or initials[i] != self.last_initial_states[i]:
                self.states[i]               = initials[i]
                self.last_initial_states[i]  = initials[i]
                self.last_triggers[i]        = False

        # edge‑detect each trigger
        current_triggers = [bool(t) for t in triggers]
        for i in range(4):
            if current_triggers[i] and not self.last_triggers[i]:
                self.states[i] = not self.states[i]
            self.last_triggers[i] = current_triggers[i]

        # prepare JSON payload
        raw_data = {
            f"trigger{i+1}": {
                "trigger":       triggers[i],
                "initial_state": initials[i],
                "current_state": self.states[i],
            } for i in range(4)
        }
        json_data = json.dumps(raw_data, indent=2, ensure_ascii=False)

        if debug:
            print(f"[VrchTriggerToggleX4Node] {json_data}")

        result = {
            "ui": {
                "current_state": [*self.states],
            },
            "result": (*self.states, json_data,)
        }
        return result

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")


class VrchTriggerToggleX8Node:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "trigger1": ("BOOLEAN", {"default": None, "forceInput": True}),
                "trigger2": ("BOOLEAN", {"default": None, "forceInput": True}),
                "trigger3": ("BOOLEAN", {"default": None, "forceInput": True}),
                "trigger4": ("BOOLEAN", {"default": None, "forceInput": True}),
                "trigger5": ("BOOLEAN", {"default": None, "forceInput": True}),
                "trigger6": ("BOOLEAN", {"default": None, "forceInput": True}),
                "trigger7": ("BOOLEAN", {"default": None, "forceInput": True}),
                "trigger8": ("BOOLEAN", {"default": None, "forceInput": True}),
            },
            "required": {
                "initial_state1": ("BOOLEAN", {"default": False}),
                "initial_state2": ("BOOLEAN", {"default": False}),
                "initial_state3": ("BOOLEAN", {"default": False}),
                "initial_state4": ("BOOLEAN", {"default": False}),
                "initial_state5": ("BOOLEAN", {"default": False}),
                "initial_state6": ("BOOLEAN", {"default": False}),
                "initial_state7": ("BOOLEAN", {"default": False}),
                "initial_state8": ("BOOLEAN", {"default": False}),
                "debug":          ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("BOOLEAN",)*8 + ("JSON",)
    RETURN_NAMES = tuple(f"OUTPUT{i}" for i in range(1,9)) + ("JSON",)
    FUNCTION = "switch"
    CATEGORY = CATEGORY

    def __init__(self):
        self.last_initial_states = [None] * 8
        self.states               = [False] * 8
        self.last_triggers        = [False] * 8

    def switch(self,
               trigger1=None, trigger2=None, trigger3=None, trigger4=None,
               trigger5=None, trigger6=None, trigger7=None, trigger8=None,
               initial_state1=False, initial_state2=False, initial_state3=False, initial_state4=False,
               initial_state5=False, initial_state6=False, initial_state7=False, initial_state8=False,
               debug=False):
        triggers = [trigger1, trigger2, trigger3, trigger4,
                    trigger5, trigger6, trigger7, trigger8]
        initials = [initial_state1, initial_state2, initial_state3, initial_state4,
                    initial_state5, initial_state6, initial_state7, initial_state8]

        # reset on initial_state change and clear trigger latch
        for i in range(8):
            if self.last_initial_states[i] is None or initials[i] != self.last_initial_states[i]:
                self.states[i]               = initials[i]
                self.last_initial_states[i]  = initials[i]
                self.last_triggers[i]        = False

        # edge‑detect each trigger
        current_triggers = [bool(t) for t in triggers]
        for i in range(8):
            if current_triggers[i] and not self.last_triggers[i]:
                self.states[i] = not self.states[i]
            self.last_triggers[i] = current_triggers[i]

        # prepare JSON payload
        raw_data = {
            f"trigger{i+1}": {
                "trigger":       triggers[i],
                "initial_state": initials[i],
                "current_state": self.states[i],
            } for i in range(8)
        }
        json_data = json.dumps(raw_data, indent=2, ensure_ascii=False)

        if debug:
            print(f"[VrchTriggerToggleX8Node] {json_data}")

        result = {
            "ui": {
                "current_state": [*self.states],
            },
            "result": (*self.states, json_data,)
        }
        return result

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")


class VrchDelayNode:
    def __init__(self):
        self.any_output = None  # To store the delayed output
        self.delay_period = 0   # Delay in milliseconds
        self.debug = False      # Debug flag

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "any_input": (AlwaysEqualProxy("*"), {}),
                "delay_ms": ("INT", {"default": 0, "min": 0, "max": 10000, "step": 1}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = (AlwaysEqualProxy("*"),)
    RETURN_NAMES = ("ANY_OUTPUT",)
    FUNCTION = "delay"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def delay(self, any_input, delay_ms, debug):
        self.debug = debug
        self.delay_period = delay_ms
        
        # Process the any_input with the specified delay
        if any_input is not None:
            if self.debug:
                print(f"[VrchDelayNode] Delaying input for {self.delay_period} ms")
            
            try:
                # Sleep for the specified delay period
                time.sleep(self.delay_period / 1000.0)  # Convert ms to seconds
                
                # Set the output after delay
                self.any_output = any_input
                
                if self.debug:
                    print(f"[VrchDelayNode] Output set after delay: {self.any_output}")
            except Exception as e:
                if self.debug:
                    print(f"[VrchDelayNode] Error during delay: {e}")
        
        return (self.any_output,)

class VrchQRCodeNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
                "size": ("INT", {"default": 256, "min": 64, "max": 1024, "step": 32}),
                "error_correction": (["L", "M", "Q", "H"], {"default": "M"}),
                "border": ("INT", {"default": 2, "min": 0, "max": 20}),
                "debug": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("QR_CODE",)
    FUNCTION = "generate_qr_code"
    CATEGORY = CATEGORY

    def generate_qr_code(self, text, size, error_correction="M", border=4, debug=False):
        if debug:
            print(f"[VrchQRCodeNode] Input text: {text}")
            print(f"[VrchQRCodeNode] Size: {size}")
            print(f"[VrchQRCodeNode] Error correction: {error_correction}")
            print(f"[VrchQRCodeNode] Border: {border}")

        try:
            
            if debug:
                print("[VrchQRCodeNode] Generating QR code using Python qrcode library")
            
            # Map error correction levels
            error_correction_map = {
                "L": 1,  # qrcode.constants.ERROR_CORRECT_L
                "M": 0,  # qrcode.constants.ERROR_CORRECT_M
                "Q": 3,  # qrcode.constants.ERROR_CORRECT_Q
                "H": 2,  # qrcode.constants.ERROR_CORRECT_H
            }
            
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,  # Let it auto-determine the version
                error_correction=error_correction_map[error_correction],
                box_size=10,  # Will be resized later
                border=border,
            )
            
            # Add data and optimize
            qr.add_data(text)
            qr.make(fit=True)
            
            # Create image
            pil_image = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)
            
            # Convert to RGB if needed
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            
            # Resize to requested size
            pil_image = pil_image.resize((size, size), Image.Resampling.LANCZOS)
                
            # Convert PIL image to ComfyUI IMAGE format (tensor)
            image_array = np.array(pil_image).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_array)[None,]  # Add batch dimension
            
            if debug:
                print(f"[VrchQRCodeNode] Output tensor shape: {image_tensor.shape}")
            
            return (image_tensor,)
            
        except Exception as e:
            if debug:
                print(f"[VrchQRCodeNode] Error: {e}")
            
            # Return a white square as fallback
            white_image = np.ones((size, size, 3), dtype=np.float32)
            white_tensor = torch.from_numpy(white_image)[None,]
            return (white_tensor,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        m = hashlib.sha256()
        for k in ("text", "size", "error_correction", "border"):
            m.update(str(kwargs.get(k, "")).encode("utf-8"))
        return m.hexdigest()