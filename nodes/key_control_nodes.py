# key_control_nodes.py

import hashlib

# Define the category for organizational purposes
CATEGORY = "vrch.ai/control/keyboard"


class VrchIntKeyControlNode:
    """
    VrchIntKeyControlNode allows users to control an integer output value within
    a customizable range using keyboard shortcuts. Users can adjust the step size,
    choose different shortcut key combinations, and define minimum and maximum values.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "min_value": ("INT", {"default": 0, "min": -9999, "max": 9999}),
                "max_value": ("INT", {"default": 100, "min": -9999, "max": 9999}),
                "step_size": ("INT", {"default": 1, "min": 1, "max": 1000}),
                "shortcut_key1": (
                    [
                        "F1",
                        "F2",
                        "F3",
                        "F4",
                        "F5",
                        "F6",
                        "F7",
                        "F8",
                        "F9",
                        "F10",
                        "F11",
                        "F12",
                    ],
                    {"default": "F2"},  # Updated default from "F1" to "F2"
                ),
                "shortcut_key2": (
                    [
                        "Down/Up",
                        "Left/Right",
                    ],
                    {"default": "Down/Up"},
                ),
                "current_value": ("INT", {"default": 50, "min": -9999, "max": 9999}),
            }
        }

    RETURN_TYPES = ("INT",)
    FUNCTION = "get_current_value"
    CATEGORY = CATEGORY

    def get_current_value(self, step_size=1, shortcut_key1="F2", shortcut_key2="Down/Up", min_value=0, max_value=100, current_value=50):
        """
        Returns the current integer value from the UI widget.

        Args:
            step_size (int): The amount to increment/decrement.
            shortcut_key1 (str): The selected first shortcut key (F1-F12).
            shortcut_key2 (str): The selected second shortcut key combination (Down/Up or Left/Right).
            min_value (int): The minimum allowable value.
            max_value (int): The maximum allowable value.
            current_value (int): The current value from the UI widget.

        Returns:
            tuple: A tuple containing the current integer value.
        """
        # Ensure current_value is within min and max bounds
        current_value = max(min(current_value, max_value), min_value)
        return (current_value,)

    @classmethod
    def IS_CHANGED(cls, step_size, shortcut_key1, shortcut_key2, min_value, max_value, current_value):
        """
        Determines if the node's state has changed based on inputs.

        Args:
            step_size (int): The current step size.
            shortcut_key1 (str): The current first shortcut key.
            shortcut_key2 (str): The current second shortcut key combination.
            min_value (int): The current minimum value.
            max_value (int): The current maximum value.
            current_value (int): The current value.

        Returns:
            str: A hash representing the current state.
        """
        m = hashlib.sha256()
        m.update(str(step_size).encode())
        m.update(shortcut_key1.encode())
        m.update(shortcut_key2.encode())
        m.update(str(min_value).encode())
        m.update(str(max_value).encode())
        m.update(str(current_value).encode())
        return m.hexdigest()


class VrchFloatKeyControlNode:
    """
    VrchFloatKeyControlNode allows users to control a floating-point output value (0.0-1.0)
    using keyboard shortcuts. Users can adjust the step size and choose different
    shortcut key combinations.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "step_size": ("FLOAT", {"default": 0.01, "min": 0.01, "max": 0.10, "step": 0.01}),
                "shortcut_key1": (
                    [
                        "F1",
                        "F2",
                        "F3",
                        "F4",
                        "F5",
                        "F6",
                        "F7",
                        "F8",
                        "F9",
                        "F10",
                        "F11",
                        "F12",
                    ],
                    {"default": "F2"},
                ),
                "shortcut_key2": (
                    [
                        "Down/Up",
                        "Left/Right",
                    ],
                    {"default": "Down/Up"},
                ),
                "current_value": ("FLOAT", {"default": 0.50, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("FLOAT",)
    FUNCTION = "get_current_value"
    CATEGORY = CATEGORY

    def get_current_value(self, step_size=0.01, shortcut_key1="F1", shortcut_key2="Down/Up", current_value=0.50):
        """
        Returns the current floating-point value from the UI widget.

        Args:
            step_size (float): The amount to increment/decrement.
            shortcut_key1 (str): The selected first shortcut key (F1-F12).
            shortcut_key2 (str): The selected second shortcut key combination (Down/Up or Left/Right).
            current_value (float): The current value from the UI widget.

        Returns:
            tuple: A tuple containing the current floating-point value.
        """
        return (current_value,)

    @classmethod
    def IS_CHANGED(cls, step_size, shortcut_key1, shortcut_key2, current_value):
        """
        Determines if the node's state has changed based on inputs.

        Args:
            step_size (float): The current step size.
            shortcut_key1 (str): The current first shortcut key.
            shortcut_key2 (str): The current second shortcut key combination.
            current_value (float): The current value.

        Returns:
            str: A hash representing the current state.
        """
        m = hashlib.sha256()
        m.update(str(step_size).encode())
        m.update(shortcut_key1.encode())
        m.update(shortcut_key2.encode())
        m.update(str(current_value).encode())
        return m.hexdigest()
    
    
class VrchBooleanKeyControlNode:
    """
    VrchBooleanKeyControlNode allows users to toggle a boolean output value (True/False)
    using a keyboard shortcut. Users can choose a shortcut key from F1-F12.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "shortcut_key": (
                    [
                        "F1",
                        "F2",
                        "F3",
                        "F4",
                        "F5",
                        "F6",
                        "F7",
                        "F8",
                        "F9",
                        "F10",
                        "F11",
                        "F12",
                    ],
                    {"default": "F2"},
                ),
                "current_value": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("BOOLEAN",)
    FUNCTION = "get_current_value"
    CATEGORY = CATEGORY

    def get_current_value(self, shortcut_key="F1", current_value=False):
        """
        Returns the current boolean value from the UI widget.

        Args:
            shortcut_key (str): The selected shortcut key (F1-F12).
            current_value (bool): The current boolean value from the UI widget.

        Returns:
            tuple: A tuple containing the current boolean value.
        """
        return (current_value,)

    @classmethod
    def IS_CHANGED(cls, shortcut_key, current_value):
        """
        Determines if the node's state has changed based on inputs.

        Args:
            shortcut_key (str): The current shortcut key.
            current_value (bool): The current boolean value.

        Returns:
            str: A hash representing the current state.
        """
        m = hashlib.sha256()
        m.update(shortcut_key.encode())
        m.update(str(current_value).encode())
        return m.hexdigest()


class VrchTextKeyControlNode:
    """
    VrchTextKeyControlNode allows users to select one of eight text inputs
    using a keyboard shortcut. Users can choose a shortcut key (F1-F12),
    define the current selection (1-8), and optionally skip empty text options
    when cycling through selections.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text1": ("STRING", {"default": "", "multiline": True}),
                "text2": ("STRING", {"default": "", "multiline": True}),
                "text3": ("STRING", {"default": "", "multiline": True}),
                "text4": ("STRING", {"default": "", "multiline": True}),
                "text5": ("STRING", {"default": "", "multiline": True}),
                "text6": ("STRING", {"default": "", "multiline": True}),
                "text7": ("STRING", {"default": "", "multiline": True}),
                "text8": ("STRING", {"default": "", "multiline": True}),
                "skip_empty_option": ("BOOLEAN", {"default": True}),
                "shortcut_key": (
                    [
                        "F1",
                        "F2",
                        "F3",
                        "F4",
                        "F5",
                        "F6",
                        "F7",
                        "F8",
                        "F9",
                        "F10",
                        "F11",
                        "F12",
                    ],
                    {"default": "F2"},
                ),
                "current_value": (
                    ["1", "2", "3", "4", "5", "6", "7", "8"],
                    {"default": "1"},
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_current_value"
    CATEGORY = CATEGORY

    def get_current_value(self, text1="", text2="", text3="", text4="", text5="", text6="", text7="", text8="", skip_empty_option=True, shortcut_key="F2", current_value="1"):
        """
        Returns the currently selected text based on current_value.
        If skip_empty_option is True, it skips any empty texts.

        Args:
            text1 (str): First text input.
            text2 (str): Second text input.
            text3 (str): Third text input.
            text4 (str): Fourth text input.
            text5 (str): Fifth text input.
            text6 (str): Sixth text input.
            text7 (str): Seventh text input.
            text8 (str): Eighth text input.
            skip_empty_option (bool): Whether to skip empty texts when cycling.
            shortcut_key (str): The selected shortcut key (F1-F12).
            current_value (str): The current selected value ("1" to "8").

        Returns:
            tuple: A tuple containing the selected text.
        """
        texts = {
            "1": text1,
            "2": text2,
            "3": text3,
            "4": text4,
            "5": text5,
            "6": text6,
            "7": text7,
            "8": text8,
        }

        if skip_empty_option:
            # Filter out empty texts and sort keys
            valid_keys = sorted([k for k, v in texts.items() if v.strip() != ""], key=lambda x: int(x))
            selected_key = str(current_value)
            if selected_key not in valid_keys:
                selected_key = valid_keys[0] if valid_keys else "1"
        else:
            selected_key = current_value

        return (texts.get(selected_key, ""),)

    @classmethod
    def IS_CHANGED(cls, text1, text2, text3, text4, text5, text6, text7, text8, skip_empty_option, shortcut_key, current_value):
        """
        Determines if the node's state has changed based on inputs.

        Args:
            text1 (str): First text input.
            text2 (str): Second text input.
            text3 (str): Third text input.
            text4 (str): Fourth text input.
            text5 (str): Fifth text input.
            text6 (str): Sixth text input.
            text7 (str): Seventh text input.
            text8 (str): Eighth text input.
            skip_empty_option (bool): Whether to skip empty texts.
            shortcut_key (str): The selected shortcut key.
            current_value (str): The current selected value.

        Returns:
            str: A hash representing the current state.
        """
        m = hashlib.sha256()
        m.update(text1.encode())
        m.update(text2.encode())
        m.update(text3.encode())
        m.update(text4.encode())
        m.update(text5.encode())
        m.update(text6.encode())
        m.update(text7.encode())
        m.update(text8.encode())
        m.update(str(skip_empty_option).encode())
        m.update(shortcut_key.encode())
        m.update(current_value.encode())
        return m.hexdigest()
    