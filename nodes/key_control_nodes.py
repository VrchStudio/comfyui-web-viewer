# key_control_nodes.py

import hashlib

# Define the category for organizational purposes
CATEGORY = "vrch.io/control"


class VrchIntKeyControlNode:
    """
    VrchIntKeyControlNode allows users to control an integer output value (0-100)
    using keyboard shortcuts. Users can adjust the step size and choose different
    shortcut key combinations.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "step_size": ("INT", {"default": 1, "min": 1, "max": 10}),
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
                "current_value": ("INT", {"default": 50, "min": 0, "max": 100}),
            }
        }

    RETURN_TYPES = ("INT",)
    FUNCTION = "get_current_value"
    CATEGORY = CATEGORY

    def get_current_value(self, step_size=1, shortcut_key1="F1", shortcut_key2="Down/Up", current_value=50):
        """
        Returns the current integer value from the UI widget.

        Args:
            step_size (int): The amount to increment/decrement.
            shortcut_key1 (str): The selected first shortcut key (F1-F12).
            shortcut_key2 (str): The selected second shortcut key combination (Down/Up or Left/Right).
            current_value (int): The current value from the UI widget.

        Returns:
            tuple: A tuple containing the current integer value.
        """
        return (current_value,)

    @classmethod
    def IS_CHANGED(cls, step_size, shortcut_key1, shortcut_key2, current_value):
        """
        Determines if the node's state has changed based on inputs.

        Args:
            step_size (int): The current step size.
            shortcut_key1 (str): The current first shortcut key.
            shortcut_key2 (str): The current second shortcut key combination.
            current_value (int): The current value.

        Returns:
            str: A hash representing the current state.
        """
        m = hashlib.sha256()
        m.update(str(step_size).encode())
        m.update(shortcut_key1.encode())
        m.update(shortcut_key2.encode())
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