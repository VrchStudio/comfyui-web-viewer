import hashlib
import json
import requests
import srt
from datetime import timedelta
import traceback

CATEGORY="vrch.ai/control/gamepad"

class VrchGamepadLoaderNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "index": (["0", "1", "2", "3", "4", "5", "6", "7"], {"default": "0"}),
                "name": ("STRING", {"default": ""}),
                "debug": ("BOOLEAN", {"default": False}),
                "raw_data": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
            },
        }
        
    # Updated return types to use standard ComfyUI supported types
    RETURN_TYPES = (
        "FLOAT",  # LEFT_STICK
        "FLOAT",  # RIGHT_STICK
        "BOOL",   # BUTTONS_BOOLEAN
        "INT",    # BUTTONS_INT
        "FLOAT",  # BUTTONS_FLOAT
        "JSON",   # RAW_DATA
    )
    
    RETURN_NAMES = (
        "LEFT_STICK",
        "RIGHT_STICK",
        "BUTTONS_BOOLEAN",
        "BUTTONS_INT",
        "BUTTONS_FLOAT",
        "RAW_DATA",
    )
    
    CATEGORY = CATEGORY
    FUNCTION = "load_gamepad"

    def load_gamepad(self, 
                     index: str, 
                     name: str, 
                     raw_data: str, 
                     debug: bool=False):
        """
        Load gamepad data and return it as JSON.
        """
        try:
            # Parse raw_data as JSON
            gamepad_data = {
                "index": index,
                "name": name,
                "raw_data": raw_data,
            }
            
            # Initialize default values
            left_stick = [0.0, 0.0]   # Default left stick values [x, y]
            right_stick = [0.0, 0.0]  # Default right stick values [x, y]
            buttons_boolean = [False] * 16  # Default button boolean states
            buttons_int = [0] * 16    # Default button int states
            buttons_float = [0.0] * 16  # Default button float values
            
            # Try to parse the gamepad data from raw_data
            if raw_data:
                try:
                    parsed_data = json.loads(raw_data)
                    
                    # Extract axis data if available
                    if "axes" in parsed_data and isinstance(parsed_data["axes"], list):
                        axes = parsed_data["axes"]
                        if len(axes) > 0:
                            left_stick[0] = float(axes[0])  # Left X
                        if len(axes) > 1:
                            left_stick[1] = float(axes[1])  # Left Y
                        if len(axes) > 2:
                            right_stick[0] = float(axes[2])  # Right X
                        if len(axes) > 3:
                            right_stick[1] = float(axes[3])  # Right Y
                    
                    # Extract button data if available
                    if "buttons" in parsed_data and isinstance(parsed_data["buttons"], list):
                        for i, btn in enumerate(parsed_data["buttons"]):
                            if isinstance(btn, dict):
                                is_pressed = bool(btn.get("pressed", False))
                                value = float(btn.get("value", 0.0))
                            elif hasattr(btn, "pressed") and hasattr(btn, "value"):
                                is_pressed = bool(btn.pressed)
                                value = float(btn.value)
                            else:
                                continue
                                
                            buttons_boolean[i] = is_pressed
                            buttons_int[i] = 1 if is_pressed else 0
                            buttons_float[i] = value
                            
                except json.JSONDecodeError:
                    if debug:
                        print("[VrchGamepadLoaderNode] Failed to parse gamepad data as JSON")
                except Exception as e:
                    if debug:
                        print(f"[VrchGamepadLoaderNode] Error processing gamepad data: {str(e)}")

            if debug:
                print("[VrchGamepadLoaderNode] Gamepad data:", json.dumps(gamepad_data, indent=2, ensure_ascii=False))
                print(f"[VrchGamepadLoaderNode] LEFT_STICK: {left_stick}")
                print(f"[VrchGamepadLoaderNode] RIGHT_STICK: {right_stick}")
                print(f"[VrchGamepadLoaderNode] BUTTONS_BOOLEAN: {buttons_boolean}")
                print(f"[VrchGamepadLoaderNode] BUTTONS_INT: {buttons_int}")
                print(f"[VrchGamepadLoaderNode] BUTTONS_FLOAT: {buttons_float}")
                
            # Return the data in the new requested format, everything as JSON
            return (
                left_stick,         # ComfyUI converts Python lists to JSON automatically
                right_stick,
                buttons_boolean,
                buttons_int,
                buttons_float,
                gamepad_data
            )
            
        except Exception as e:
            print(f"[VrchGamepadLoaderNode] Error loading gamepad data: {str(e)}")
            # Return default values for all outputs
            return (
                [0.0, 0.0],     # LEFT_STICK
                [0.0, 0.0],     # RIGHT_STICK
                [False] * 16,   # BUTTONS_BOOLEAN
                [0] * 16,       # BUTTONS_INT
                [0.0] * 16,     # BUTTONS_FLOAT
                {}              # RAW_DATA
            )
        
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        raw_data = kwargs.get("raw_data", "")
        debug = kwargs.get("debug", False)
        if not raw_data:
            if debug:
                print("[VrchGamepadLoaderNode] No raw_data provided to IS_CHANGED.")
            return False
        
        m = hashlib.sha256()
        m.update(raw_data.encode("utf-8"))
        return m.hexdigest()
