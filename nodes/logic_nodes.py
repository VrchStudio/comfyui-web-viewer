import hashlib
from .node_utils import VrchNodeUtils

CATEGORY="vrch.ai/logic"

class VrchIntRemapNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required":{
            "input_value":("INT",{"default":None}),
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

    def remap_int(self, input_value, input_min, input_max, output_min, output_max, output_invert, output_default):
        if input_min > input_max:
            raise ValueError("[VrchIntRemapNode] input_min cannot be greater than input_max.")
        if output_min > output_max:
            raise ValueError("[VrchIntRemapNode] output_min cannot be greater than output_max.")
        try:
            remap_func = VrchNodeUtils.select_remap_func(output_invert)
            mapped = remap_func(float(input_value), float(input_min), float(input_max), float(output_min), float(output_max))
            mapped_int = int(mapped)
            # Clamp within output range
            mapped_int = max(min(mapped_int, output_max), output_min)
            return (mapped_int,)
        except Exception:
            return (output_default,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        m = hashlib.sha256()
        for k in ("input_value","input_min","input_max","output_min","output_max","output_invert"):
            m.update(str(kwargs.get(k)).encode("utf-8"))
        return m.hexdigest()


class VrchFloatRemapNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required":{
            "input_value":("FLOAT",{"default":None}),
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

    def remap_float(self, input_value, input_min, input_max, output_min, output_max, output_invert, output_default):
        if input_min > input_max:
            raise ValueError("[VrchFloatRemapNode] input_min cannot be greater than input_max.")
        if output_min > output_max:
            raise ValueError("[VrchFloatRemapNode] output_min cannot be greater than output_max.")
        try:
            remap_func = VrchNodeUtils.select_remap_func(output_invert)
            mapped = remap_func(input_value, input_min, input_max, output_min, output_max)
            # Clamp within output range
            mapped_clamped = max(min(mapped, output_max), output_min)
            return (mapped_clamped,)
        except Exception:
            return (output_default,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        m = hashlib.sha256()
        for k in ("input_value","input_min","input_max","output_min","output_max","output_invert"):
            m.update(str(kwargs.get(k)).encode("utf-8"))
        return m.hexdigest()