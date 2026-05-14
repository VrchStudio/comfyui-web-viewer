"""VRCH MIDI WebSocket binary protocol helpers."""

from __future__ import annotations

import struct
import time
from dataclasses import dataclass
from typing import Any


MAGIC = b"VMID"
VERSION = 1
FRAME_DEFINITION = 1
FRAME_STATE = 2
HEADER_SIZE = 16

CHANNEL_ANY = 255

CONTROL_TYPES = {
    1: "cc",
    2: "note",
    3: "toggle",
    4: "xy_x",
    5: "xy_y",
}
CONTROL_TYPE_IDS = {value: key for key, value in CONTROL_TYPES.items()}


class MidiProtocolError(ValueError):
    """Raised by test encoders when protocol input is invalid."""


def clamp_u8(value: Any, default: int = 0) -> int:
    try:
        number = int(value)
    except Exception:
        number = default
    return max(0, min(255, number))


def normalize_midi_channel(value: Any) -> int:
    if value in (None, "", "any", "unknown"):
        return CHANNEL_ANY
    try:
        number = int(value)
    except Exception:
        return CHANNEL_ANY
    if number == CHANNEL_ANY:
        return CHANNEL_ANY
    if 1 <= number <= 16:
        return number - 1
    if 0 <= number <= 15:
        return number
    return CHANNEL_ANY


def channel_to_key(value: int) -> str:
    if value == CHANNEL_ANY:
        return "any"
    if 0 <= value <= 15:
        return str(value + 1)
    return "any"


def cc_lookup_key(channel_key: str, number: int) -> str:
    return f"{channel_key}:{int(number)}"


def _read_u8(data: bytes, offset: int) -> tuple[int, int]:
    if offset + 1 > len(data):
        raise MidiProtocolError("truncated uint8")
    return data[offset], offset + 1


def _read_u32(data: bytes, offset: int) -> tuple[int, int]:
    if offset + 4 > len(data):
        raise MidiProtocolError("truncated uint32")
    return struct.unpack_from(">I", data, offset)[0], offset + 4


def _read_string(data: bytes, offset: int) -> tuple[str, int]:
    if offset + 2 > len(data):
        raise MidiProtocolError("truncated string length")
    length = struct.unpack_from(">H", data, offset)[0]
    offset += 2
    if offset + length > len(data):
        raise MidiProtocolError("truncated string data")
    raw = data[offset:offset + length]
    return raw.decode("utf-8"), offset + length


def _pack_string(value: Any) -> bytes:
    raw = str(value or "").encode("utf-8")
    if len(raw) > 65535:
        raise MidiProtocolError("string is too long")
    return struct.pack(">H", len(raw)) + raw


def _pack_header(frame_type: int, seq: int = 0, timestamp_ms_low: int | None = None, device_index: int = 0) -> bytes:
    if timestamp_ms_low is None:
        timestamp_ms_low = int(time.time() * 1000) & 0xFFFFFFFF
    return struct.pack(
        ">4sBBBBII",
        MAGIC,
        VERSION,
        clamp_u8(frame_type),
        0,
        clamp_u8(device_index),
        int(seq) & 0xFFFFFFFF,
        int(timestamp_ms_low) & 0xFFFFFFFF,
    )


def encode_definition_frame(
    controls: list[dict[str, Any]],
    definition_seq: int = 1,
    seq: int = 1,
    timestamp_ms_low: int | None = None,
    device_index: int = 0,
) -> bytes:
    """Build a definition frame. This is primarily used by tests."""

    if len(controls) > 255:
        raise MidiProtocolError("too many control definitions")
    payload = struct.pack(">IB", int(definition_seq) & 0xFFFFFFFF, len(controls))
    for index, control in enumerate(controls):
        control_index = clamp_u8(control.get("control_index", index))
        raw_type = control.get("control_type", control.get("type", "cc"))
        if isinstance(raw_type, str):
            control_type = CONTROL_TYPE_IDS.get(raw_type, 1)
        else:
            control_type = clamp_u8(raw_type, 1)
        payload += struct.pack(
            ">BBBBBB",
            control_index,
            control_type,
            normalize_midi_channel(control.get("midi_channel", CHANNEL_ANY)),
            clamp_u8(control.get("number", 0)),
            clamp_u8(control.get("default_value", 0)),
            clamp_u8(control.get("flags", 0)),
        )
        payload += _pack_string(control.get("key", control.get("workflow_key", "")))
        payload += _pack_string(control.get("id", ""))
        payload += _pack_string(control.get("label", ""))
    return _pack_header(FRAME_DEFINITION, seq, timestamp_ms_low, device_index) + payload


def encode_state_frame(
    raw_cc: list[dict[str, Any]] | None = None,
    raw_notes: list[dict[str, Any]] | None = None,
    control_values: list[dict[str, Any]] | None = None,
    definition_seq: int = 1,
    seq: int = 1,
    timestamp_ms_low: int | None = None,
    device_index: int = 0,
) -> bytes:
    """Build a state frame. This is primarily used by tests."""

    raw_cc = raw_cc or []
    raw_notes = raw_notes or []
    control_values = control_values or []
    if len(raw_cc) > 255 or len(raw_notes) > 255 or len(control_values) > 255:
        raise MidiProtocolError("too many state records")
    payload = struct.pack(">IB", int(definition_seq) & 0xFFFFFFFF, len(raw_cc))
    for item in raw_cc:
        payload += struct.pack(
            ">BBB",
            normalize_midi_channel(item.get("midi_channel", CHANNEL_ANY)),
            clamp_u8(item.get("cc_number", item.get("number", 0))),
            clamp_u8(item.get("value", 0)),
        )
    payload += struct.pack(">B", len(raw_notes))
    for item in raw_notes:
        status = str(item.get("status", "")).lower()
        flags = clamp_u8(item.get("flags", 0))
        if not flags:
            if item.get("is_on") is True or status == "noteon":
                flags |= 1
            if item.get("is_off") is True or status == "noteoff":
                flags |= 2
        payload += struct.pack(
            ">BBBB",
            normalize_midi_channel(item.get("midi_channel", CHANNEL_ANY)),
            clamp_u8(item.get("note_number", item.get("number", 0))),
            clamp_u8(item.get("velocity", item.get("value", 0))),
            flags,
        )
    payload += struct.pack(">B", len(control_values))
    for item in control_values:
        payload += struct.pack(
            ">BBB",
            clamp_u8(item.get("control_index", item.get("index", 0))),
            clamp_u8(item.get("value", 0)),
            clamp_u8(item.get("flags", 0)),
        )
    return _pack_header(FRAME_STATE, seq, timestamp_ms_low, device_index) + payload


@dataclass
class MidiFrameHeader:
    frame_type: int
    flags: int
    device_index: int
    seq: int
    timestamp_ms_low: int


class MidiStateStore:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.reset()

    def reset(self):
        self.definition_ready = False
        self.definition_seq = None
        self.definitions_by_index: dict[int, dict[str, Any]] = {}
        self.index_by_key: dict[str, int] = {}
        self.index_by_cc: dict[str, int] = {}
        self.values_by_index: dict[int, int] = {}
        self.cc_values: dict[str, dict[int, int]] = {}
        self.notes: dict[str, dict[int, dict[str, Any]]] = {}
        self.seq = None
        self.timestamp_ms_low = None
        self.received_at = None
        self.packet_age_ms = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "_vrch_type": "midi_state_v1",
            "definition_ready": bool(self.definition_ready),
            "definition_seq": self.definition_seq,
            "definitions_by_index": dict(self.definitions_by_index),
            "index_by_key": dict(self.index_by_key),
            "index_by_cc": dict(self.index_by_cc),
            "values_by_index": dict(self.values_by_index),
            "cc_values": {ch: dict(values) for ch, values in self.cc_values.items()},
            "notes": {ch: {num: dict(value) for num, value in notes.items()} for ch, notes in self.notes.items()},
            "seq": self.seq,
            "timestamp_ms_low": self.timestamp_ms_low,
            "received_at": self.received_at,
            "packet_age_ms": self.packet_age_ms,
        }

    def _set_packet_meta(self, header: MidiFrameHeader):
        now = time.time()
        self.seq = header.seq
        self.timestamp_ms_low = header.timestamp_ms_low
        self.received_at = now
        now_ms_low = int(now * 1000) & 0xFFFFFFFF
        self.packet_age_ms = float((now_ms_low - header.timestamp_ms_low) & 0xFFFFFFFF)

    def apply_definition(self, header: MidiFrameHeader, data: bytes, offset: int):
        definition_seq, offset = _read_u32(data, offset)
        control_count, offset = _read_u8(data, offset)
        definitions_by_index: dict[int, dict[str, Any]] = {}
        index_by_key: dict[str, int] = {}
        index_by_cc: dict[str, int] = {}

        for _ in range(control_count):
            if offset + 6 > len(data):
                raise MidiProtocolError("truncated definition record")
            control_index, control_type, midi_channel, number, default_value, flags = struct.unpack_from(">BBBBBB", data, offset)
            offset += 6
            key, offset = _read_string(data, offset)
            control_id, offset = _read_string(data, offset)
            label, offset = _read_string(data, offset)

            channel_key = channel_to_key(midi_channel)
            definition = {
                "key": key,
                "id": control_id,
                "label": label,
                "type": CONTROL_TYPES.get(control_type, "unknown"),
                "control_type": control_type,
                "midi_channel": channel_key,
                "number": number,
                "default_value": default_value,
                "flags": flags,
            }
            definitions_by_index[control_index] = definition

            clean_key = str(key or "").strip()
            if clean_key:
                if clean_key not in index_by_key:
                    index_by_key[clean_key] = control_index
                elif self.debug:
                    print(f"[MidiStateParser] duplicate workflow key ignored: {clean_key}")

            channel_cc_key = cc_lookup_key(channel_key, number)
            any_cc_key = cc_lookup_key("any", number)
            if channel_cc_key not in index_by_cc:
                index_by_cc[channel_cc_key] = control_index
            if channel_key != "any" and any_cc_key not in index_by_cc:
                index_by_cc[any_cc_key] = control_index

        self.definition_seq = definition_seq
        self.definition_ready = True
        self.definitions_by_index = definitions_by_index
        self.index_by_key = index_by_key
        self.index_by_cc = index_by_cc
        self.values_by_index = {idx: value for idx, value in self.values_by_index.items() if idx in definitions_by_index}
        self._set_packet_meta(header)
        return self.snapshot()

    def apply_state(self, header: MidiFrameHeader, data: bytes, offset: int):
        frame_definition_seq, offset = _read_u32(data, offset)
        raw_cc_count, offset = _read_u8(data, offset)
        for _ in range(raw_cc_count):
            if offset + 3 > len(data):
                raise MidiProtocolError("truncated raw cc record")
            midi_channel, cc_number, value = struct.unpack_from(">BBB", data, offset)
            offset += 3
            channel_key = channel_to_key(midi_channel)
            self.cc_values.setdefault(channel_key, {})[cc_number] = value
            self.cc_values.setdefault("any", {})[cc_number] = value

        raw_note_count, offset = _read_u8(data, offset)
        for _ in range(raw_note_count):
            if offset + 4 > len(data):
                raise MidiProtocolError("truncated raw note record")
            midi_channel, note_number, velocity, flags = struct.unpack_from(">BBBB", data, offset)
            offset += 4
            channel_key = channel_to_key(midi_channel)
            note_value = {
                "velocity": velocity,
                "is_on": bool(flags & 1) and velocity > 0,
                "is_off": bool(flags & 2) or not (bool(flags & 1) and velocity > 0),
                "flags": flags,
            }
            self.notes.setdefault(channel_key, {})[note_number] = note_value
            self.notes.setdefault("any", {})[note_number] = dict(note_value)

        control_value_count, offset = _read_u8(data, offset)
        control_values = []
        for _ in range(control_value_count):
            if offset + 3 > len(data):
                raise MidiProtocolError("truncated control value record")
            control_index, value, flags = struct.unpack_from(">BBB", data, offset)
            offset += 3
            control_values.append((control_index, value, flags))

        if self.definition_ready and frame_definition_seq == self.definition_seq:
            for control_index, value, _flags in control_values:
                if control_index in self.definitions_by_index:
                    self.values_by_index[control_index] = value
        elif self.debug:
            print(
                "[MidiStateParser] state definition_seq mismatch; "
                f"frame={frame_definition_seq}, current={self.definition_seq}"
            )

        self._set_packet_meta(header)
        return self.snapshot()


class MidiStateParser:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.store = MidiStateStore(debug=debug)

    def __call__(self, message: bytes | bytearray | memoryview | str):
        return self.parse(message)

    def empty_state(self) -> dict[str, Any]:
        return self.store.snapshot()

    def parse(self, message: bytes | bytearray | memoryview | str):
        start = time.perf_counter()
        try:
            if isinstance(message, str):
                if self.debug:
                    print("[MidiStateParser] ignoring text frame on /midi")
                return self.store.snapshot()
            data = bytes(message)
            if len(data) < HEADER_SIZE:
                if self.debug:
                    print("[MidiStateParser] ignoring short frame")
                return self.store.snapshot()
            magic, version, frame_type, flags, device_index, seq, timestamp_ms_low = struct.unpack_from(">4sBBBBII", data, 0)
            if magic != MAGIC or version != VERSION:
                if self.debug:
                    print("[MidiStateParser] ignoring frame with bad magic/version")
                return self.store.snapshot()
            header = MidiFrameHeader(frame_type, flags, device_index, seq, timestamp_ms_low)
            if frame_type == FRAME_DEFINITION:
                snapshot = self.store.apply_definition(header, data, HEADER_SIZE)
            elif frame_type == FRAME_STATE:
                snapshot = self.store.apply_state(header, data, HEADER_SIZE)
            else:
                if self.debug:
                    print(f"[MidiStateParser] ignoring unknown frame type: {frame_type}")
                return self.store.snapshot()
            if self.debug:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                print(f"[MidiStateParser] parsed frame_type={frame_type} seq={seq} in {elapsed_ms:.3f} ms")
            return snapshot
        except Exception as exc:
            if self.debug:
                print(f"[MidiStateParser] parse error: {exc}")
            return self.store.snapshot()
