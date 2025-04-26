import hashlib
import json
from .node_utils import VrchNodeUtils

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

    def switch(self, trigger=None, initial_state=False, debug=False):
        
        # If initial_state input changed, reset current state
        if self.last_initial_state is None or initial_state != self.last_initial_state:
            self.state = initial_state
            self.last_initial_state = initial_state
            
        # Toggle state only when trigger is True
        if trigger:
            self.state = not self.state
            
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
        self.states = [False] * 4

    def switch(self,
               trigger1=None, trigger2=None, trigger3=None, trigger4=None,
               initial_state1=False, initial_state2=False, initial_state3=False, initial_state4=False,
               debug=False):
        triggers = [trigger1, trigger2, trigger3, trigger4]
        initials = [initial_state1, initial_state2, initial_state3, initial_state4]

        # reset & toggle
        for i in range(4):
            if self.last_initial_states[i] is None or initials[i] != self.last_initial_states[i]:
                self.states[i] = initials[i]
                self.last_initial_states[i] = initials[i]
            if triggers[i]:
                self.states[i] = not self.states[i]

        # build grouped JSON data
        raw_data = {
            f"trigger{i+1}": {
                "trigger": triggers[i],
                "initial_state": initials[i],
                "current_state": self.states[i]
            }
            for i in range(4)
        }
        json_data = json.dumps(raw_data, indent=2, ensure_ascii=False)

        if debug:
            # print debug info in JSON format
            print(f"[VrchTriggerToggleX4Node] {json_data}")
            
        result = {
            "ui": {
                "current_state": [*self.states],
            },
            "result": (*self.states, json_data)
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
            "required":{
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

    RETURN_TYPES = ("BOOLEAN","BOOLEAN","BOOLEAN","BOOLEAN",
                    "BOOLEAN","BOOLEAN","BOOLEAN","BOOLEAN","JSON")
    RETURN_NAMES = ("OUTPUT1","OUTPUT2","OUTPUT3","OUTPUT4",
                    "OUTPUT5","OUTPUT6","OUTPUT7","OUTPUT8","JSON")
    FUNCTION = "switch"
    CATEGORY = CATEGORY

    def __init__(self):
        self.last_initial_states = [None] * 8
        self.states = [False] * 8

    def switch(self,
               trigger1 = None, trigger2 = None, trigger3 = None, trigger4 = None,
               trigger5 = None, trigger6 = None, trigger7 = None, trigger8 = None,
               initial_state1 = False, initial_state2 = False, initial_state3 = False, initial_state4 = False,
               initial_state5 = False, initial_state6 = False, initial_state7 = False, initial_state8 = False,
               debug = False):
        triggers = [trigger1, trigger2, trigger3, trigger4,
                    trigger5, trigger6, trigger7, trigger8]
        initials = [initial_state1, initial_state2, initial_state3, initial_state4,
                    initial_state5, initial_state6, initial_state7, initial_state8]

        # reset initial changes and toggle on trigger
        for i in range(8):
            if self.last_initial_states[i] is None or initials[i] != self.last_initial_states[i]:
                self.states[i] = initials[i]
                self.last_initial_states[i] = initials[i]
            if triggers[i]:
                self.states[i] = not self.states[i]

        # build grouped JSON data
        raw_data = {
            f"trigger{i+1}": {
                "trigger":       triggers[i],
                "initial_state": initials[i],
                "current_state": self.states[i]
            }
            for i in range(8)
        }
        json_data = json.dumps(raw_data, indent=2, ensure_ascii=False)

        if debug:
            # print debug info in JSON format
            print(f"[VrchTriggerToggleX8Node] {json_data}")

        result = {
            "ui": {
                "current_state": [*self.states],
            },
            "result": (*self.states, json_data)
        }
        return result

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")