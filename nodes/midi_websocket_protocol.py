"""VRCH MIDI WebSocket binary protocol helpers."""

from __future__ import annotations

import struct
import time
from dataclasses import dataclass, field
from typing import Any, Callable


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
SOURCE_TIER_PRIORITY = {
    "secondary": 1,
    "primary": 2,
}
PRIMARY_ACTIVITY_WINDOW_SECONDS = 0.3
SOURCE_EXPIRY_SECONDS = 6.0
LEGACY_SOURCE_KEY = "__legacy__"


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


def normalize_source_tier(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "secondary":
        return "secondary"
    return "primary"


def source_tier_priority(value: Any) -> int:
    return SOURCE_TIER_PRIORITY.get(normalize_source_tier(value), SOURCE_TIER_PRIORITY["primary"])


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


def _read_optional_string(data: bytes, offset: int) -> tuple[str, int]:
    if offset >= len(data):
        return "", offset
    try:
        return _read_string(data, offset)
    except MidiProtocolError:
        return "", len(data)


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
    sender_id: str = "",
    owner_id: str = "",
    preset_id: str = "",
    preset_name: str = "",
    device_name: str = "",
    source_tier: str = "primary",
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
    payload += _pack_string(sender_id)
    payload += _pack_string(owner_id)
    payload += _pack_string(preset_id)
    payload += _pack_string(preset_name)
    payload += _pack_string(device_name)
    payload += _pack_string(normalize_source_tier(source_tier))
    return _pack_header(FRAME_DEFINITION, seq, timestamp_ms_low, device_index) + payload


def encode_state_frame(
    raw_cc: list[dict[str, Any]] | None = None,
    raw_notes: list[dict[str, Any]] | None = None,
    control_values: list[dict[str, Any]] | None = None,
    definition_seq: int = 1,
    seq: int = 1,
    timestamp_ms_low: int | None = None,
    device_index: int = 0,
    sender_id: str = "",
    source_tier: str = "primary",
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
    payload += _pack_string(sender_id)
    payload += _pack_string(normalize_source_tier(source_tier))
    return _pack_header(FRAME_STATE, seq, timestamp_ms_low, device_index) + payload


@dataclass
class MidiFrameHeader:
    frame_type: int
    flags: int
    device_index: int
    seq: int
    timestamp_ms_low: int


@dataclass
class MidiSourceState:
    source_key: str
    sender_id: str
    source_tier: str = "primary"
    state_tier: str | None = None
    owner_id: str = ""
    preset_id: str = ""
    preset_name: str = ""
    device_name: str = ""
    definition_ready: bool = False
    definition_seq: int | None = None
    definitions_by_index: dict[int, dict[str, Any]] = field(default_factory=dict)
    raw_cc_values: dict[tuple[str, int], int] = field(default_factory=dict)
    raw_note_values: dict[tuple[str, int], dict[str, Any]] = field(default_factory=dict)
    control_values: dict[int, int] = field(default_factory=dict)
    state_initialized: bool = False
    last_seen: float = 0.0


class MidiStateStore:
    def __init__(
        self,
        debug: bool = False,
        monotonic_clock: Callable[[], float] | None = None,
        primary_activity_window_seconds: float = PRIMARY_ACTIVITY_WINDOW_SECONDS,
        source_expiry_seconds: float = SOURCE_EXPIRY_SECONDS,
    ):
        self.debug = debug
        self._monotonic_clock = monotonic_clock or time.monotonic
        self.primary_activity_window_seconds = max(0.0, float(primary_activity_window_seconds))
        self.source_expiry_seconds = max(0.0, float(source_expiry_seconds))
        self.reset()

    def reset(self):
        self.definition_ready = False
        self.definition_seq = None
        self.definitions_by_index: dict[int, dict[str, Any]] = {}
        self.index_by_key: dict[str, int] = {}
        self.index_by_cc: dict[str, int] = {}
        self.values_by_index: dict[int, int] = {}
        self.value_source_tiers_by_index: dict[int, str] = {}
        self.cc_values: dict[str, dict[int, int]] = {}
        self.cc_source_tiers: dict[str, dict[int, str]] = {}
        self.notes: dict[str, dict[int, dict[str, Any]]] = {}
        self.note_source_tiers: dict[str, dict[int, str]] = {}
        self.sender_id = ""
        self.source_tier = "primary"
        self.seq = None
        self.timestamp_ms_low = None
        self.received_at = None
        self.packet_age_ms = None
        self._sources: dict[str, MidiSourceState] = {}
        self._composite_index_by_identity: dict[tuple[Any, ...], int] = {}
        self._values_by_identity: dict[tuple[Any, ...], int] = {}
        self._value_source_tiers_by_identity: dict[tuple[Any, ...], str] = {}
        self._primary_active_until: dict[tuple[Any, ...], float] = {}

    def snapshot(self) -> dict[str, Any]:
        return {
            "_vrch_type": "midi_state_v1",
            "definition_ready": bool(self.definition_ready),
            "definition_seq": self.definition_seq,
            "definitions_by_index": dict(self.definitions_by_index),
            "index_by_key": dict(self.index_by_key),
            "index_by_cc": dict(self.index_by_cc),
            "values_by_index": dict(self.values_by_index),
            "value_source_tiers_by_index": dict(self.value_source_tiers_by_index),
            "cc_values": {ch: dict(values) for ch, values in self.cc_values.items()},
            "cc_source_tiers": {ch: dict(values) for ch, values in self.cc_source_tiers.items()},
            "notes": {ch: {num: dict(value) for num, value in notes.items()} for ch, notes in self.notes.items()},
            "note_source_tiers": {ch: dict(values) for ch, values in self.note_source_tiers.items()},
            "sender_id": self.sender_id,
            "source_tier": self.source_tier,
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

    @staticmethod
    def _source_key(sender_id: str) -> str:
        return str(sender_id or "").strip() or LEGACY_SOURCE_KEY

    @staticmethod
    def _definition_identity(
        definition_source_key: str,
        control_index: int,
        definition: dict[str, Any],
    ) -> tuple[Any, ...]:
        clean_key = str(definition.get("key") or "").strip()
        if clean_key:
            return ("key", clean_key)
        return ("source", definition_source_key, int(control_index))

    def _get_source(self, sender_id: str, source_tier: str, now: float) -> MidiSourceState:
        source_key = self._source_key(sender_id)
        source = self._sources.get(source_key)
        if source is None:
            source = MidiSourceState(source_key=source_key, sender_id=str(sender_id or ""))
            self._sources[source_key] = source
        source.sender_id = str(sender_id or "")
        source.source_tier = normalize_source_tier(source_tier)
        source.last_seen = now
        return source

    def _prune_expired_sources(self, now: float):
        if self.source_expiry_seconds <= 0:
            return
        expired = [
            source_key
            for source_key, source in self._sources.items()
            if now - source.last_seen > self.source_expiry_seconds
        ]
        if not expired:
            return
        for source_key in expired:
            del self._sources[source_key]
        self._rebuild_composite_definition()

    def _rebuild_composite_definition(self):
        definition_sources = [source for source in self._sources.values() if source.definition_ready]
        definition_sources.sort(
            key=lambda source: (
                1 if source.source_key == LEGACY_SOURCE_KEY else 0,
                -source_tier_priority(source.source_tier),
                source.source_key,
            )
        )

        definitions_by_index: dict[int, dict[str, Any]] = {}
        index_by_key: dict[str, int] = {}
        index_by_cc: dict[str, int] = {}
        composite_index_by_identity: dict[tuple[Any, ...], int] = {}
        used_composite_indexes: set[int] = set()
        next_composite_index = 0

        for source in definition_sources:
            for local_index in sorted(source.definitions_by_index):
                definition = source.definitions_by_index[local_index]
                identity = self._definition_identity(source.source_key, local_index, definition)
                if identity in composite_index_by_identity:
                    if self.debug and identity[0] == "key":
                        print(f"[MidiStateParser] duplicate workflow key ignored: {identity[1]}")
                    continue

                # Preserve sender-local indexes when they do not collide, especially for the primary source.
                preferred_index = int(local_index)
                if preferred_index not in used_composite_indexes:
                    composite_index = preferred_index
                else:
                    while next_composite_index in used_composite_indexes:
                        next_composite_index += 1
                    composite_index = next_composite_index
                used_composite_indexes.add(composite_index)
                composite_index_by_identity[identity] = composite_index
                definitions_by_index[composite_index] = dict(definition)

                clean_key = str(definition.get("key") or "").strip()
                if clean_key:
                    index_by_key[clean_key] = composite_index

                channel_key = str(definition.get("midi_channel") or "any")
                number = clamp_u8(definition.get("number", 0))
                channel_cc_key = cc_lookup_key(channel_key, number)
                any_cc_key = cc_lookup_key("any", number)
                if channel_cc_key not in index_by_cc:
                    index_by_cc[channel_cc_key] = composite_index
                if channel_key != "any" and any_cc_key not in index_by_cc:
                    index_by_cc[any_cc_key] = composite_index

        valid_identities = set(composite_index_by_identity)
        self._values_by_identity = {
            identity: value
            for identity, value in self._values_by_identity.items()
            if identity in valid_identities
        }
        self._value_source_tiers_by_identity = {
            identity: tier
            for identity, tier in self._value_source_tiers_by_identity.items()
            if identity in valid_identities
        }
        self._primary_active_until = {
            target: deadline
            for target, deadline in self._primary_active_until.items()
            if target[0] != "control" or target[1] in valid_identities
        }
        self.definition_ready = bool(definition_sources)
        self.definitions_by_index = definitions_by_index
        self.index_by_key = index_by_key
        self.index_by_cc = index_by_cc
        self._composite_index_by_identity = composite_index_by_identity
        self._sync_values_by_index()

    def _sync_values_by_index(self):
        self.values_by_index = {}
        self.value_source_tiers_by_index = {}
        for identity, composite_index in self._composite_index_by_identity.items():
            if identity in self._values_by_identity:
                self.values_by_index[composite_index] = self._values_by_identity[identity]
            if identity in self._value_source_tiers_by_identity:
                self.value_source_tiers_by_index[composite_index] = self._value_source_tiers_by_identity[identity]

    def _definition_source_for_state(
        self,
        source: MidiSourceState,
        frame_definition_seq: int,
    ) -> MidiSourceState | None:
        if source.definition_ready and source.definition_seq == frame_definition_seq:
            return source
        legacy_source = self._sources.get(LEGACY_SOURCE_KEY)
        if (
            source.source_key != LEGACY_SOURCE_KEY
            and legacy_source is not None
            and legacy_source.definition_ready
            and legacy_source.definition_seq == frame_definition_seq
        ):
            return legacy_source
        return None

    def _can_apply_target(self, target: tuple[Any, ...], source_tier: str, now: float) -> bool:
        if source_tier == "primary":
            return True
        deadline = self._primary_active_until.get(target, 0.0)
        if deadline <= now:
            self._primary_active_until.pop(target, None)
            return True
        return False

    def _record_primary_activity(self, target: tuple[Any, ...], source_tier: str, now: float, active: bool):
        if source_tier == "primary" and active:
            self._primary_active_until[target] = now + self.primary_activity_window_seconds

    def _merge_cc_value(
        self,
        channel_key: str,
        cc_number: int,
        value: int,
        source_tier: str,
        now: float,
        primary_active: bool,
    ):
        for output_channel in dict.fromkeys((channel_key, "any")):
            target = ("cc", output_channel, cc_number)
            if not self._can_apply_target(target, source_tier, now):
                continue
            self.cc_values.setdefault(output_channel, {})[cc_number] = value
            self.cc_source_tiers.setdefault(output_channel, {})[cc_number] = source_tier
            self._record_primary_activity(target, source_tier, now, primary_active)

    def _merge_note_value(
        self,
        channel_key: str,
        note_number: int,
        note_value: dict[str, Any],
        source_tier: str,
        now: float,
        primary_active: bool,
    ):
        for output_channel in dict.fromkeys((channel_key, "any")):
            target = ("note", output_channel, note_number)
            if not self._can_apply_target(target, source_tier, now):
                continue
            self.notes.setdefault(output_channel, {})[note_number] = dict(note_value)
            self.note_source_tiers.setdefault(output_channel, {})[note_number] = source_tier
            self._record_primary_activity(target, source_tier, now, primary_active)

    def _merge_control_value(
        self,
        identity: tuple[Any, ...],
        value: int,
        source_tier: str,
        now: float,
        primary_active: bool,
    ):
        if identity not in self._composite_index_by_identity:
            return
        target = ("control", identity)
        if not self._can_apply_target(target, source_tier, now):
            return
        self._values_by_identity[identity] = value
        self._value_source_tiers_by_identity[identity] = source_tier
        self._record_primary_activity(target, source_tier, now, primary_active)

    def _has_other_initialized_primary(self, source_key: str) -> bool:
        return any(
            other_key != source_key
            and source.state_initialized
            and source.state_tier == "primary"
            for other_key, source in self._sources.items()
        )

    @staticmethod
    def _changed_items(current: dict[Any, Any], previous: dict[Any, Any], apply_full: bool, initialized: bool):
        if apply_full:
            return list(current.items())
        if not initialized:
            return []
        return [(key, value) for key, value in current.items() if previous.get(key) != value]

    def apply_definition(self, header: MidiFrameHeader, data: bytes, offset: int):
        definition_seq, offset = _read_u32(data, offset)
        control_count, offset = _read_u8(data, offset)
        definitions_by_index: dict[int, dict[str, Any]] = {}

        for _ in range(control_count):
            if offset + 6 > len(data):
                raise MidiProtocolError("truncated definition record")
            control_index, control_type, midi_channel, number, default_value, flags = struct.unpack_from(">BBBBBB", data, offset)
            offset += 6
            key, offset = _read_string(data, offset)
            control_id, offset = _read_string(data, offset)
            label, offset = _read_string(data, offset)
            definitions_by_index[control_index] = {
                "key": key,
                "id": control_id,
                "label": label,
                "type": CONTROL_TYPES.get(control_type, "unknown"),
                "control_type": control_type,
                "midi_channel": channel_to_key(midi_channel),
                "number": number,
                "default_value": default_value,
                "flags": flags,
            }

        sender_id, offset = _read_optional_string(data, offset)
        owner_id, offset = _read_optional_string(data, offset)
        preset_id, offset = _read_optional_string(data, offset)
        preset_name, offset = _read_optional_string(data, offset)
        device_name, offset = _read_optional_string(data, offset)
        raw_source_tier, offset = _read_optional_string(data, offset)
        source_tier = normalize_source_tier(raw_source_tier)

        now = self._monotonic_clock()
        self._prune_expired_sources(now)
        source = self._get_source(sender_id, source_tier, now)
        definition_changed = (
            not source.definition_ready
            or source.definition_seq != definition_seq
            or source.definitions_by_index != definitions_by_index
        )
        source.owner_id = owner_id
        source.preset_id = preset_id
        source.preset_name = preset_name
        source.device_name = device_name
        source.definition_ready = True
        source.definition_seq = definition_seq
        source.definitions_by_index = definitions_by_index
        if definition_changed:
            source.state_initialized = False

        self.sender_id = sender_id
        self.source_tier = source_tier
        self.definition_seq = definition_seq
        self._rebuild_composite_definition()
        self._set_packet_meta(header)
        return self.snapshot()

    def apply_state(self, header: MidiFrameHeader, data: bytes, offset: int):
        frame_definition_seq, offset = _read_u32(data, offset)
        raw_cc_count, offset = _read_u8(data, offset)
        raw_cc_records = []
        for _ in range(raw_cc_count):
            if offset + 3 > len(data):
                raise MidiProtocolError("truncated raw cc record")
            midi_channel, cc_number, value = struct.unpack_from(">BBB", data, offset)
            offset += 3
            raw_cc_records.append((midi_channel, cc_number, value))

        raw_note_count, offset = _read_u8(data, offset)
        raw_note_records = []
        for _ in range(raw_note_count):
            if offset + 4 > len(data):
                raise MidiProtocolError("truncated raw note record")
            midi_channel, note_number, velocity, flags = struct.unpack_from(">BBBB", data, offset)
            offset += 4
            raw_note_records.append(
                (
                    midi_channel,
                    note_number,
                    {
                        "velocity": velocity,
                        "is_on": bool(flags & 1) and velocity > 0,
                        "is_off": bool(flags & 2) or not (bool(flags & 1) and velocity > 0),
                        "flags": flags,
                    },
                )
            )

        control_value_count, offset = _read_u8(data, offset)
        control_values = []
        for _ in range(control_value_count):
            if offset + 3 > len(data):
                raise MidiProtocolError("truncated control value record")
            control_index, value, flags = struct.unpack_from(">BBB", data, offset)
            offset += 3
            control_values.append((control_index, value, flags))

        sender_id, offset = _read_optional_string(data, offset)
        raw_source_tier, offset = _read_optional_string(data, offset)
        source_tier = normalize_source_tier(raw_source_tier)
        now = self._monotonic_clock()
        self._prune_expired_sources(now)
        source = self._get_source(sender_id, source_tier, now)

        incoming_cc = {
            (channel_to_key(midi_channel), cc_number): value
            for midi_channel, cc_number, value in raw_cc_records
        }
        incoming_notes = {
            (channel_to_key(midi_channel), note_number): note_value
            for midi_channel, note_number, note_value in raw_note_records
        }
        incoming_controls = {
            control_index: value
            for control_index, value, _flags in control_values
        }

        # VMID v1 frames are full snapshots; only changes against this sender's prior snapshot are merge candidates.
        was_initialized = source.state_initialized
        previous_state_tier = source.state_tier
        promoted_to_primary = previous_state_tier == "secondary" and source_tier == "primary"
        apply_full = promoted_to_primary or (
            not was_initialized
            and (source_tier == "primary" or not self._has_other_initialized_primary(source.source_key))
        )
        primary_active = source_tier == "primary" and (promoted_to_primary or not apply_full)

        for (channel_key, cc_number), value in self._changed_items(
            incoming_cc,
            source.raw_cc_values,
            apply_full,
            was_initialized,
        ):
            self._merge_cc_value(channel_key, cc_number, value, source_tier, now, primary_active)

        for (channel_key, note_number), note_value in self._changed_items(
            incoming_notes,
            source.raw_note_values,
            apply_full,
            was_initialized,
        ):
            self._merge_note_value(channel_key, note_number, note_value, source_tier, now, primary_active)

        definition_source = self._definition_source_for_state(source, frame_definition_seq)
        if definition_source is not None:
            for control_index, value in self._changed_items(
                incoming_controls,
                source.control_values,
                apply_full,
                was_initialized,
            ):
                definition = definition_source.definitions_by_index.get(control_index)
                if definition is None:
                    continue
                identity = self._definition_identity(definition_source.source_key, control_index, definition)
                self._merge_control_value(identity, value, source_tier, now, primary_active)
        elif incoming_controls and self.debug:
            print(
                "[MidiStateParser] state definition_seq mismatch; "
                f"frame={frame_definition_seq}, sender={sender_id or LEGACY_SOURCE_KEY}"
            )

        source.raw_cc_values = incoming_cc
        source.raw_note_values = incoming_notes
        source.control_values = incoming_controls
        source.state_initialized = True
        source.state_tier = source_tier
        source.last_seen = now
        self.sender_id = sender_id
        self.source_tier = source_tier
        self._sync_values_by_index()
        self._set_packet_meta(header)
        return self.snapshot()


class MidiStateParser:
    def __init__(
        self,
        debug: bool = False,
        monotonic_clock: Callable[[], float] | None = None,
        primary_activity_window_seconds: float = PRIMARY_ACTIVITY_WINDOW_SECONDS,
        source_expiry_seconds: float = SOURCE_EXPIRY_SECONDS,
    ):
        self.debug = debug
        self.store = MidiStateStore(
            debug=debug,
            monotonic_clock=monotonic_clock,
            primary_activity_window_seconds=primary_activity_window_seconds,
            source_expiry_seconds=source_expiry_seconds,
        )

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
