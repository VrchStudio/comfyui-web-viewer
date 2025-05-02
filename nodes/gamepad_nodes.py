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
                "refresh_interval": ("INT", {"default": 50, "min": 10, "max": 10000}),
                "debug": ("BOOLEAN", {"default": False}),
                "raw_data": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
            },
        }
        
    RETURN_TYPES = (
        "JSON",      # RAW_DATA
        "FLOAT",     # LEFT_STICK
        "FLOAT",     # RIGHT_STICK
        "BOOLEAN",   # BUTTONS_BOOLEAN
        "INT",       # BUTTONS_INT
        "FLOAT",     # BUTTONS_FLOAT
    )
    
    RETURN_NAMES = (
        "RAW_DATA",
        "LEFT_STICK",
        "RIGHT_STICK",
        "BOOLEAN_BUTTONS",
        "INT_BUTTONS",
        "FLOAT_BUTTONS",
    )
    
    OUTPUT_NODE = True
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
    
    
class VrchXboxControllerNode:  
    """  
    A specialized node for mapping Xbox controller inputs from raw gamepad data.  
    This node takes raw gamepad data from VrchGamepadLoaderNode and maps it to  
    standard Xbox controller buttons and controls for easier use in workflows.  
    """  
      
    @classmethod  
    def INPUT_TYPES(s):  
        """  
        Define the input parameters for the node.  
          
        Returns:  
            dict: Dictionary containing input parameter specifications  
        """  
        return {  
            "required": {  
                "raw_data": ("JSON", {"default": {}}),  # Raw gamepad data from VrchGamepadLoaderNode  
                "debug": ("BOOLEAN", {"default": False}),  # Enable debug output  
            },  
        }  
      
    # Define the types of outputs this node will provide  
    RETURN_TYPES = (  
        "JSON",       # FULL_MAPPING - Complete mapping as JSON  
        "FLOAT",      # LEFT_STICK - Array with [x, y] values  
        "FLOAT",      # RIGHT_STICK - Array with [x, y] values  
        "FLOAT",      # LEFT_TRIGGER - Value from 0.0 to 1.0  
        "FLOAT",      # RIGHT_TRIGGER - Value from 0.0 to 1.0  
        "BOOLEAN",    # A_BUTTON - Bottom face button  
        "BOOLEAN",    # B_BUTTON - Right face button  
        "BOOLEAN",    # X_BUTTON - Left face button  
        "BOOLEAN",    # Y_BUTTON - Top face button  
        "BOOLEAN",    # LB_BUTTON - Left bumper  
        "BOOLEAN",    # RB_BUTTON - Right bumper  
        "BOOLEAN",    # VIEW_BUTTON - Left center button (formerly Back)  
        "BOOLEAN",    # MENU_BUTTON - Right center button (formerly Start)  
        "BOOLEAN",    # LEFT_STICK_PRESS - Left stick click  
        "BOOLEAN",    # RIGHT_STICK_PRESS - Right stick click  
        "BOOLEAN",    # DPAD_UP - D-pad up direction  
        "BOOLEAN",    # DPAD_DOWN - D-pad down direction  
        "BOOLEAN",    # DPAD_LEFT - D-pad left direction  
        "BOOLEAN",    # DPAD_RIGHT - D-pad right direction  
        "BOOLEAN",    # XBOX_BUTTON - Xbox logo button  
    )  
      
    # Names for the outputs, matching the types above  
    RETURN_NAMES = (  
        "FULL_MAPPING",
        "LEFT_STICK",  
        "RIGHT_STICK",  
        "LEFT_TRIGGER",  
        "RIGHT_TRIGGER",  
        "A_BUTTON",  
        "B_BUTTON",  
        "X_BUTTON",   
        "Y_BUTTON",  
        "LB_BUTTON",  
        "RB_BUTTON",  
        "VIEW_BUTTON",  
        "MENU_BUTTON",  
        "LEFT_STICK_PRESS",  
        "RIGHT_STICK_PRESS",  
        "DPAD_UP",  
        "DPAD_DOWN",  
        "DPAD_LEFT",  
        "DPAD_RIGHT",  
        "XBOX_BUTTON",  
    )  
      
    CATEGORY = CATEGORY 
    FUNCTION = "process_xbox_controller"  
  
    def process_xbox_controller(self, raw_data, debug=False):  
        """  
        Process raw gamepad data and map it to Xbox controller inputs.  
          
        Args:  
            raw_data (dict): Raw gamepad data from VrchGamepadLoaderNode  
            debug (bool): Whether to print debug information  
              
        Returns:  
            tuple: All mapped Xbox controller inputs as specified in RETURN_TYPES  
        """  
        # Initialize default values for all outputs  
        left_stick = [0.0, 0.0]    # [x, y] values for left analog stick  
        right_stick = [0.0, 0.0]   # [x, y] values for right analog stick  
        left_trigger = 0.0         # Value for left trigger (LT)  
        right_trigger = 0.0        # Value for right trigger (RT)  
        buttonsBoolean = [0]*17  # Array for boolean button states (0 or 1)
        buttonsFloat = [0]*17    # Array for float button values (0.0 to 1.0)
          
        # Initialize button states (all False by default)  
        a_button = False           # A button (bottom face button)  
        b_button = False           # B button (right face button)  
        x_button = False           # X button (left face button)  
        y_button = False           # Y button (top face button)  
        lb_button = False          # Left bumper (LB)  
        rb_button = False          # Right bumper (RB)  
        view_button = False        # View button (formerly Back)  
        menu_button = False        # Menu button (formerly Start)  
        left_stick_press = False   # Left stick press (L3)  
        right_stick_press = False  # Right stick press (R3)  
        dpad_up = False            # D-pad up  
        dpad_down = False          # D-pad down  
        dpad_left = False          # D-pad left  
        dpad_right = False         # D-pad right  
        xbox_button = False        # Xbox logo button  
          
        # Create a complete mapping object for the JSON output  
        full_mapping = {  
            "left_stick": left_stick,  
            "right_stick": right_stick,  
            "left_trigger": left_trigger,  
            "right_trigger": right_trigger,  
            "a_button": a_button,  
            "b_button": b_button,  
            "x_button": x_button,  
            "y_button": y_button,  
            "lb_button": lb_button,  
            "rb_button": rb_button,  
            "view_button": view_button,  
            "menu_button": menu_button,  
            "left_stick_press": left_stick_press,  
            "right_stick_press": right_stick_press,  
            "dpad_up": dpad_up,  
            "dpad_down": dpad_down,  
            "dpad_left": dpad_left,  
            "dpad_right": dpad_right,  
            "xbox_button": xbox_button,  
        }  
          
        # If no data is provided, return default values  
        if not raw_data:  
            if debug:  
                print("[VrchXboxControllerNode] No raw data provided.")  
            returned_data = {
                "ui": {
                    "buttonsBoolean": buttonsBoolean,
                    "buttonsFloat": buttonsFloat,
                    "leftStick": left_stick,
                    "rightStick": right_stick,
                },
                "result":(
                    full_mapping,
                    left_stick, right_stick, left_trigger, right_trigger,  
                    a_button, b_button, x_button, y_button,  
                    lb_button, rb_button, view_button, menu_button,  
                    left_stick_press, right_stick_press,  
                    dpad_up, dpad_down, dpad_left, dpad_right,  
                    xbox_button,
                ),
            }
            return returned_data
          
        # Parse and process the raw_data  
        try:  
            # Extract data from raw_data  
            if "raw_data" in raw_data and raw_data["raw_data"]:  
                # Handle cases where raw_data might be a JSON string  
                if isinstance(raw_data["raw_data"], str):  
                    try:  
                        parsed_data = json.loads(raw_data["raw_data"])  
                    except json.JSONDecodeError:  
                        # If JSON parsing fails, use raw_data as is  
                        parsed_data = raw_data  
                else:  
                    # If raw_data is already a dict, use it directly  
                    parsed_data = raw_data  
                  
                # Process axes data (analog sticks)  
                if "axes" in parsed_data and isinstance(parsed_data["axes"], list):  
                    axes = parsed_data["axes"]  
                    # Map axes to stick positions  
                    if len(axes) > 0:  
                        left_stick[0] = float(axes[0])  # Left stick X-axis  
                    if len(axes) > 1:  
                        left_stick[1] = float(axes[1])  # Left stick Y-axis  
                    if len(axes) > 2:  
                        right_stick[0] = float(axes[2])  # Right stick X-axis  
                    if len(axes) > 3:  
                        right_stick[1] = float(axes[3])  # Right stick Y-axis  
                  
                # Process buttons data  
                if "buttons" in parsed_data and isinstance(parsed_data["buttons"], list): 
                    # Extract button data from parsed_data 
                    buttons = parsed_data["buttons"]
                    
                    # Map buttons to boolean and float arrays
                    for i, btn in enumerate(buttons):
                        if i < len(buttonsBoolean):
                            buttonsBoolean[i] = self._get_button_state(buttons, i)
                        if i < len(buttonsFloat):
                            buttonsFloat[i] = self._get_button_value(buttons, i) 
                      
                    # Map buttons to Xbox controller layout  
                    # Standard Xbox controller button mapping  
                    if len(buttons) > 0:  
                        a_button = self._get_button_state(buttons, 0)  # A button  
                    if len(buttons) > 1:  
                        b_button = self._get_button_state(buttons, 1)  # B button  
                    if len(buttons) > 2:  
                        x_button = self._get_button_state(buttons, 2)  # X button  
                    if len(buttons) > 3:  
                        y_button = self._get_button_state(buttons, 3)  # Y button  
                    if len(buttons) > 4:  
                        lb_button = self._get_button_state(buttons, 4)  # Left bumper  
                    if len(buttons) > 5:  
                        rb_button = self._get_button_state(buttons, 5)  # Right bumper  
                    if len(buttons) > 6:  
                        left_trigger = self._get_button_value(buttons, 6)  # Left trigger  
                    if len(buttons) > 7:  
                        right_trigger = self._get_button_value(buttons, 7)  # Right trigger  
                    if len(buttons) > 8:  
                        view_button = self._get_button_state(buttons, 8)  # View button  
                    if len(buttons) > 9:  
                        menu_button = self._get_button_state(buttons, 9)  # Menu button  
                    if len(buttons) > 10:  
                        left_stick_press = self._get_button_state(buttons, 10)  # Left stick press  
                    if len(buttons) > 11:  
                        right_stick_press = self._get_button_state(buttons, 11)  # Right stick press  
                    if len(buttons) > 12:  
                        dpad_up = self._get_button_state(buttons, 12)  # D-pad up  
                    if len(buttons) > 13:  
                        dpad_down = self._get_button_state(buttons, 13)  # D-pad down  
                    if len(buttons) > 14:  
                        dpad_left = self._get_button_state(buttons, 14)  # D-pad left  
                    if len(buttons) > 15:  
                        dpad_right = self._get_button_state(buttons, 15)  # D-pad right  
                    if len(buttons) > 16:  
                        xbox_button = self._get_button_state(buttons, 16)  # Xbox button  
              
            # Update the full mapping object with current values  
            full_mapping = {  
                "left_stick": left_stick,  
                "right_stick": right_stick,  
                "left_trigger": left_trigger,  
                "right_trigger": right_trigger,  
                "a_button": a_button,  
                "b_button": b_button,  
                "x_button": x_button,  
                "y_button": y_button,  
                "lb_button": lb_button,  
                "rb_button": rb_button,  
                "view_button": view_button,  
                "menu_button": menu_button,  
                "left_stick_press": left_stick_press,  
                "right_stick_press": right_stick_press,  
                "dpad_up": dpad_up,  
                "dpad_down": dpad_down,  
                "dpad_left": dpad_left,  
                "dpad_right": dpad_right,  
                "xbox_button": xbox_button,  
            }  
              
            # Print debug information if enabled  
            if debug:  
                print(f"[VrchXboxControllerNode] Xbox controller mapping: {full_mapping}")  
                
            returned_data = {
                "ui": {
                    "buttonsBoolean": buttonsBoolean,
                    "buttonsFloat": buttonsFloat,
                    "leftStick": left_stick,
                    "rightStick": right_stick,
                },
                "result":(
                    full_mapping,
                    left_stick, right_stick, left_trigger, right_trigger,  
                    a_button, b_button, x_button, y_button,  
                    lb_button, rb_button, view_button, menu_button,  
                    left_stick_press, right_stick_press,  
                    dpad_up, dpad_down, dpad_left, dpad_right,  
                    xbox_button,
                ),
            }
              
            # Return all mapped values  
            return returned_data
              
        except Exception as e:  
            # Handle any errors during processing  
            if debug:  
                print(f"[VrchXboxControllerNode] Error processing Xbox controller data: {str(e)}")  
                
            returned_data = {
                "ui": {
                    "buttonsBoolean": buttonsBoolean,
                    "buttonsFloat": buttonsFloat,
                    "leftStick": left_stick,
                    "rightStick": right_stick,
                },
                "result":(
                    full_mapping,
                    left_stick, right_stick, left_trigger, right_trigger,  
                    a_button, b_button, x_button, y_button,  
                    lb_button, rb_button, view_button, menu_button,  
                    left_stick_press, right_stick_press,  
                    dpad_up, dpad_down, dpad_left, dpad_right,  
                    xbox_button,
                ),
            }
              
            # Return default values in case of error  
            return returned_data
      
    def _get_button_state(self, buttons, index):  
        """  
        Get the pressed state of a button at the specified index.  
          
        Args:  
            buttons (list): List of button objects  
            index (int): Index of the button to check  
              
        Returns:  
            bool: True if the button is pressed, False otherwise  
        """  
        try:  
            btn = buttons[index]  
            if isinstance(btn, dict):  
                return bool(btn.get("pressed", False))  
            elif hasattr(btn, "pressed"):  
                return bool(btn.pressed)  
            return False  
        except (IndexError, TypeError):  
            return False  
              
    def _get_button_value(self, buttons, index):  
        """  
        Get the analog value of a button at the specified index.  
        Used for triggers which can have values between 0.0 and 1.0.  
          
        Args:  
            buttons (list): List of button objects  
            index (int): Index of the button to check  
              
        Returns:  
            float: Value of the button (0.0 to 1.0)  
        """  
        try:  
            btn = buttons[index]  
            if isinstance(btn, dict):  
                return float(btn.get("value", 0.0))  
            elif hasattr(btn, "value"):  
                return float(btn.value)  
            return 0.0  
        except (IndexError, TypeError):  
            return 0.0

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        raw_data = kwargs.get("raw_data", "")
        debug = kwargs.get("debug", False)
        if not raw_data:
            if debug:
                print("[VrchXboxControllerNode] No raw_data provided to IS_CHANGED.")
            return False
        
        m = hashlib.sha256()
        m.update(raw_data.encode("utf-8"))
        return m.hexdigest()
