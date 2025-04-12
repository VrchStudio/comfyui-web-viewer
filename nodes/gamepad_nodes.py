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
                "refresh_interval": ("INT", {"default": 100, "min": 10, "max": 10000}),
                "debug": ("BOOLEAN", {"default": False}),
                "raw_data": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
            },
        }
        
    RETURN_TYPES = (
        "JSON",   # RAW_DATA
        "FLOAT",  # LEFT_STICK
        "FLOAT",  # RIGHT_STICK
        "BOOL",   # BUTTONS_BOOLEAN
        "INT",    # BUTTONS_INT
        "FLOAT",  # BUTTONS_FLOAT
    )
    
    RETURN_NAMES = (
        "RAW_DATA",
        "LEFT_STICK",
        "RIGHT_STICK",
        "BOOLEAN_BUTTONS",
        "INT_BUTTONS",
        "FLOAT_BUTTONS",
    )
    
    CATEGORY = CATEGORY
    FUNCTION = "load_gamepad"

    def load_gamepad(self, 
                     index: str, 
                     name: str, 
                     refresh_interval: int=100,
                     debug: bool=False,
                     raw_data: str=""):
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
            
            # Initialize with empty arrays - will be sized based on actual gamepad data
            buttons_boolean = []
            buttons_int = []
            buttons_float = []
            
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
                        button_count = len(parsed_data["buttons"])
                        
                        # Initialize arrays with the correct size based on actual gamepad data
                        buttons_boolean = [False] * button_count
                        buttons_int = [0] * button_count
                        buttons_float = [0.0] * button_count
                        
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
                    else:
                        # If no buttons data found, initialize with default empty arrays
                        buttons_boolean = []
                        buttons_int = []
                        buttons_float = []
                            
                except json.JSONDecodeError:
                    if debug:
                        print("[VrchGamepadLoaderNode] Failed to parse gamepad data as JSON")
                except Exception as e:
                    if debug:
                        print(f"[VrchGamepadLoaderNode] Error processing gamepad data: {str(e)}")

            # Ensure we have at least empty arrays even if no data was processed
            if not buttons_boolean:
                buttons_boolean = []
            if not buttons_int:
                buttons_int = []
            if not buttons_float:
                buttons_float = []

            if debug:
                print(f"[VrchGamepadLoaderNode] Gamepad data:", json.dumps(gamepad_data, indent=2, ensure_ascii=False))
                print(f"[VrchGamepadLoaderNode] LEFT_STICK: {left_stick}")
                print(f"[VrchGamepadLoaderNode] RIGHT_STICK: {right_stick}")
                print(f"[VrchGamepadLoaderNode] BUTTONS_BOOLEAN: {buttons_boolean}")
                print(f"[VrchGamepadLoaderNode] BUTTONS_INT: {buttons_int}")
                print(f"[VrchGamepadLoaderNode] BUTTONS_FLOAT: {buttons_float}")
                print(f"[VrchGamepadLoaderNode] Number of buttons: {len(buttons_boolean)}")
                
            return (
                gamepad_data,
                left_stick,
                right_stick,
                buttons_boolean,
                buttons_int,
                buttons_float,
            )
            
        except Exception as e:
            print(f"[VrchGamepadLoaderNode] Error loading gamepad data: {str(e)}")
            # Return default values for all outputs
            return (
                {}              # RAW_DATA
                [0.0, 0.0],     # LEFT_STICK
                [0.0, 0.0],     # RIGHT_STICK
                [],             # BUTTONS_BOOLEAN (empty array instead of fixed size)
                [],             # BUTTONS_INT (empty array instead of fixed size)
                [],             # BUTTONS_FLOAT (empty array instead of fixed size)
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
