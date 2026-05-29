"""MIDI control nodes for VRCH MIDI WebSocket state."""

from __future__ import annotations

import time
from typing import Any

from .node_utils import VrchNodeUtils


CATEGORY = "vrch.ai/control/midi"
LOOKUP_MODES = ["workflow_key", "cc_number"]
MIDI_CHANNELS = ["any"] + [str(i) for i in range(1, 17)]
INT_OUTPUT_MIN_LIMIT = -999999
INT_OUTPUT_MAX_LIMIT = 999999


def _empty_midi_state() -> dict[str, Any]:
    return {
        "_vrch_type": "midi_state_v1",
        "definition_ready": False,
        "definitions_by_index": {},
        "index_by_key": {},
        "index_by_cc": {},
        "values_by_index": {},
        "cc_values": {},
        "notes": {},
    }


def _normalize_midi_state(midi: Any) -> dict[str, Any]:
    if isinstance(midi, dict):
        return midi
    return _empty_midi_state()


def _get_indexed(mapping: Any, index: int, default=None):
    if not isinstance(mapping, dict):
        return default
    if index in mapping:
        return mapping[index]
    return mapping.get(str(index), default)


def _lookup_raw_value(
    midi: Any,
    lookup_mode: str,
    control_key: str = "",
    midi_channel: str = "any",
    cc_number: int = 0,
    debug: bool = False,
) -> tuple[float | None, str]:
    state = _normalize_midi_state(midi)
    mode = lookup_mode if lookup_mode in LOOKUP_MODES else "workflow_key"

    if mode == "workflow_key":
        key = str(control_key or "").strip()
        if not key:
            return None, "empty workflow_key"
        index = state.get("index_by_key", {}).get(key)
        if index is None:
            available = ", ".join(sorted(str(k) for k in state.get("index_by_key", {}).keys()))
            return None, f"workflow_key {key} not found; available keys: {available}"
        values = state.get("values_by_index", {})
        raw = _get_indexed(values, index)
        if raw is None:
            return None, f"workflow_key {key} matched control_index {index}, but no value is available"
        definition = _get_indexed(state.get("definitions_by_index", {}), index, {})
        source = f"Matched workflow_key {key} -> control_index {index}"
        if definition:
            source += f" -> {definition.get('type', 'control')} {definition.get('number', '')}"
        source += f" -> raw {raw}"
        return float(raw), source

    channel = str(midi_channel or "any")
    if channel not in MIDI_CHANNELS:
        channel = "any"
    try:
        number = int(cc_number)
    except Exception:
        number = 0
    number = max(0, min(127, number))
    cc_values = state.get("cc_values", {})
    channel_values = cc_values.get(channel, {})
    if number in channel_values:
        raw = channel_values[number]
        return float(raw), f"Matched cc_number {channel}/{number} -> raw {raw}"
    if str(number) in channel_values:
        raw = channel_values[str(number)]
        return float(raw), f"Matched cc_number {channel}/{number} -> raw {raw}"
    return None, f"cc_number {channel}/{number} not found"


def _validate_ranges(input_min, input_max, output_min, output_max, output_default, node_name: str):
    if output_min > output_max:
        raise ValueError(f"[{node_name}] Output min value cannot be greater than max value.")
    if input_min > input_max:
        raise ValueError(f"[{node_name}] Input min value cannot be greater than max value.")
    if output_default < output_min or output_default > output_max:
        raise ValueError(f"[{node_name}] Default value must be within the output range.")


def _round_up_to_multiple(value: int, multiple: int) -> int:
    try:
        multiple = int(multiple)
    except Exception:
        return value
    if multiple <= 1:
        return value
    return -(-int(value) // multiple) * multiple


class VrchIntMidiControlNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "midi": ("VRCH_MIDI",),
                "lookup_mode": (LOOKUP_MODES, {"default": "workflow_key"}),
                "control_key": ("STRING", {"default": "", "multiline": False}),
                "midi_channel": (MIDI_CHANNELS, {"default": "any"}),
                "cc_number": ("INT", {"default": 0, "min": 0, "max": 127}),
                "input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
                "input_max": ("FLOAT", {"default": 127.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
                "output_min": ("INT", {"default": 0, "min": INT_OUTPUT_MIN_LIMIT, "max": INT_OUTPUT_MAX_LIMIT}),
                "output_max": ("INT", {"default": 100, "min": INT_OUTPUT_MIN_LIMIT, "max": INT_OUTPUT_MAX_LIMIT}),
                "output_invert": ("BOOLEAN", {"default": False}),
                "output_default": ("INT", {"default": 0, "min": INT_OUTPUT_MIN_LIMIT, "max": INT_OUTPUT_MAX_LIMIT}),
                "output_round_to_step": ("INT", {"default": 0, "min": 0, "max": INT_OUTPUT_MAX_LIMIT}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("VALUE", "RAW_CC")
    FUNCTION = "load_int_midi"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_int_midi(
        self,
        midi,
        lookup_mode="workflow_key",
        control_key="",
        midi_channel="any",
        cc_number=0,
        input_min=0.0,
        input_max=127.0,
        output_min=0,
        output_max=100,
        output_invert=False,
        output_default=0,
        output_round_to_step=0,
        debug=False,
    ):
        start = time.perf_counter()
        _validate_ranges(input_min, input_max, output_min, output_max, output_default, "VrchIntMidiControlNode")
        raw, source = _lookup_raw_value(midi, lookup_mode, control_key, midi_channel, cc_number, debug=debug)
        if raw is None:
            if debug:
                print(f"[VrchIntMidiControlNode] {source}; using default value: {output_default}")
            return int(output_default), 0
        remap_func = VrchNodeUtils.select_remap_func(output_invert)
        mapped = remap_func(float(raw), float(input_min), float(input_max), float(output_min), float(output_max))
        mapped_int = int(mapped)
        mapped_int = _round_up_to_multiple(mapped_int, output_round_to_step)
        if debug:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            print(f"[VrchIntMidiControlNode] {source}; mapped={mapped_int}; elapsed={elapsed_ms:.3f} ms")
        return mapped_int, int(raw)


class VrchFloatMidiControlNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "midi": ("VRCH_MIDI",),
                "lookup_mode": (LOOKUP_MODES, {"default": "workflow_key"}),
                "control_key": ("STRING", {"default": "", "multiline": False}),
                "midi_channel": (MIDI_CHANNELS, {"default": "any"}),
                "cc_number": ("INT", {"default": 0, "min": 0, "max": 127}),
                "input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
                "input_max": ("FLOAT", {"default": 127.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
                "output_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
                "output_max": ("FLOAT", {"default": 100.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
                "output_invert": ("BOOLEAN", {"default": False}),
                "output_default": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("FLOAT", "INT")
    RETURN_NAMES = ("VALUE", "RAW_CC")
    FUNCTION = "load_float_midi"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_float_midi(
        self,
        midi,
        lookup_mode="workflow_key",
        control_key="",
        midi_channel="any",
        cc_number=0,
        input_min=0.0,
        input_max=127.0,
        output_min=0.0,
        output_max=100.0,
        output_invert=False,
        output_default=0.0,
        debug=False,
    ):
        start = time.perf_counter()
        _validate_ranges(input_min, input_max, output_min, output_max, output_default, "VrchFloatMidiControlNode")
        raw, source = _lookup_raw_value(midi, lookup_mode, control_key, midi_channel, cc_number, debug=debug)
        if raw is None:
            if debug:
                print(f"[VrchFloatMidiControlNode] {source}; using default value: {output_default}")
            return float(output_default), 0
        remap_func = VrchNodeUtils.select_remap_func(output_invert)
        mapped = remap_func(float(raw), float(input_min), float(input_max), float(output_min), float(output_max))
        if debug:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            print(f"[VrchFloatMidiControlNode] {source}; mapped={mapped}; elapsed={elapsed_ms:.3f} ms")
        return float(mapped), int(raw)
