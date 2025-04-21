import hashlib
import json
from .node_utils import VrchNodeUtils

CATEGORY="vrch.ai/logic"

class VrchIntRemapNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required":{
            "input":("INT",{"default":None, "forceInput": True}),
            "input_min":("INT",{"default":0,"min":-999999,"max":999999}),
            "input_max":("INT",{"default":1,"min":-999999,"max":999999}),
            "output_min":("INT",{"default":0,"min":-999999,"max":999999}),
            "output_max":("INT",{"default":100,"min":-999999,"max":999999}),
            "output_invert":("BOOLEAN",{"default":False}),
            "output_default":("INT",{"default":0}),
        }}

    RETURN_TYPES=("INT",)
    RETURN_NAMES=("OUTPUT",)
    FUNCTION="remap_int"
    CATEGORY=CATEGORY

    def remap_int(self, input, input_min, input_max, output_min, output_max, output_invert, output_default):
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
        return {"required":{
            "input":("FLOAT",{"default":None, "forceInput": True}),
            "input_min":("FLOAT",{"default":0.0,"min":-999999.0,"max":999999.0,"step":0.01}),
            "input_max":("FLOAT",{"default":1.0,"min":-999999.0,"max":999999.0,"step":0.01}),
            "output_min":("FLOAT",{"default":0.0,"min":-999999.0,"max":999999.0,"step":0.01}),
            "output_max":("FLOAT",{"default":100.0,"min":-999999.0,"max":999999.0,"step":0.01}),
            "output_invert":("BOOLEAN",{"default":False}),
            "output_default":("FLOAT",{"default":0.0}),
        }}

    RETURN_TYPES=("FLOAT",)
    RETURN_NAMES=("OUTPUT",)
    FUNCTION="remap_float"
    CATEGORY=CATEGORY

    def remap_float(self, input, input_min, input_max, output_min, output_max, output_invert, output_default):
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
        return {"required":{
            "trigger": ("BOOLEAN", {"default": None, "forceInput": True}),
            "initial_state": ("BOOLEAN", {"default": False}), 
            "debug": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = ("BOOLEAN", "JSON",)
    RETURN_NAMES = ("OUTPUT", "JSON",)
    OUTPUT_NODE = True
    FUNCTION = "switch"
    CATEGORY = CATEGORY

    def __init__(self):
        self.last_initial_state = None
        self.state = False

    def switch(self, trigger, initial_state, debug):
        
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
            
        return (self.state, json_data,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

# Insert new 4-channel trigger toggle node
class VrchTriggerToggleX4Node:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required":{
            "trigger1": ("BOOLEAN", {"default": None, "forceInput": True}),
            "trigger2": ("BOOLEAN", {"default": None, "forceInput": True}),
            "trigger3": ("BOOLEAN", {"default": None, "forceInput": True}),
            "trigger4": ("BOOLEAN", {"default": None, "forceInput": True}),
            # default outputs before any toggle
            "initial_state1": ("BOOLEAN", {"default": False}),
            "initial_state2": ("BOOLEAN", {"default": False}),
            "initial_state3": ("BOOLEAN", {"default": False}),
            "initial_state4": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = ("BOOLEAN","BOOLEAN","BOOLEAN","BOOLEAN")
    RETURN_NAMES = ("OUTPUT1","OUTPUT2","OUTPUT3","OUTPUT4")
    FUNCTION = "switch"
    CATEGORY = CATEGORY

    def __init__(self):
        self.last_initial_states = [None, None, None, None]
        self.state1 = False
        self.state2 = False
        self.state3 = False
        self.state4 = False

    def switch(self, trigger1, trigger2, trigger3, trigger4,
               initial_state1, initial_state2, initial_state3, initial_state4):
        # Reset any channel whose initial_state input has changed
        for idx, init_state in enumerate((initial_state1, initial_state2, initial_state3, initial_state4)):
            if self.last_initial_states[idx] is None or init_state != self.last_initial_states[idx]:
                setattr(self, f'state{idx+1}', init_state)
                self.last_initial_states[idx] = init_state
        # Toggle each state on True input
        if trigger1:
            self.state1 = not self.state1
        if trigger2:
            self.state2 = not self.state2
        if trigger3:
            self.state3 = not self.state3
        if trigger4:
            self.state4 = not self.state4
        return (self.state1, self.state2, self.state3, self.state4)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")