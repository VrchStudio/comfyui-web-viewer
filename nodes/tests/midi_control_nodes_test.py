#!/usr/bin/env python3
"""Tests for VRCH MIDI control nodes."""

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from nodes.midi_control_nodes import VrchFloatMidiControlNode, VrchIntMidiControlNode  # noqa: E402


def midi_state():
    return {
        "_vrch_type": "midi_state_v1",
        "definition_ready": True,
        "definitions_by_index": {
            0: {"key": "brightness", "id": "knob-1", "label": "Brightness", "type": "cc", "number": 22},
            1: {"key": "seed", "id": "fader-1", "label": "Seed", "type": "cc", "number": 7},
        },
        "index_by_key": {"brightness": 0, "seed": 1},
        "index_by_cc": {"1:22": 0, "1:7": 1},
        "values_by_index": {0: 96, 1: 42},
        "cc_values": {"1": {22: 11, 7: 42}, "any": {22: 11, 7: 42}},
        "notes": {},
    }


class TestMidiControlNodes(unittest.TestCase):
    def test_int_workflow_key_lookup(self):
        node = VrchIntMidiControlNode()
        value, raw = node.load_int_midi(
            midi_state(), "workflow_key", "brightness", "any", 0, 0, 127, 0, 127, False, 0, False
        )
        self.assertEqual(value, 96)
        self.assertEqual(raw, 96.0)

    def test_float_cc_number_lookup(self):
        node = VrchFloatMidiControlNode()
        value, raw = node.load_float_midi(
            midi_state(), "cc_number", "ignored", "1", 22, 0, 127, 0.0, 1.0, False, 0.0, False
        )
        self.assertAlmostEqual(value, 11 / 127)
        self.assertEqual(raw, 11.0)

    def test_no_fallback_from_missing_key_to_valid_cc(self):
        node = VrchIntMidiControlNode()
        value, raw = node.load_int_midi(
            midi_state(), "workflow_key", "missing", "1", 22, 0, 127, 0, 127, False, 5, False
        )
        self.assertEqual(value, 5)
        self.assertEqual(raw, 0.0)

    def test_conflict_resolves_by_lookup_mode_only(self):
        node = VrchIntMidiControlNode()
        key_value, _ = node.load_int_midi(
            midi_state(), "workflow_key", "brightness", "1", 7, 0, 127, 0, 127, False, 0, False
        )
        cc_value, _ = node.load_int_midi(
            midi_state(), "cc_number", "brightness", "1", 7, 0, 127, 0, 127, False, 0, False
        )
        self.assertEqual(key_value, 96)
        self.assertEqual(cc_value, 42)

    def test_display_label_is_not_lookup_key(self):
        node = VrchIntMidiControlNode()
        value, raw = node.load_int_midi(
            midi_state(), "workflow_key", "Brightness", "any", 0, 0, 127, 0, 127, False, 9, False
        )
        self.assertEqual(value, 9)
        self.assertEqual(raw, 0.0)

    def test_json_roundtrip_state_still_resolves_indexes(self):
        state = json.loads(json.dumps(midi_state()))
        int_node = VrchIntMidiControlNode()
        key_value, key_raw = int_node.load_int_midi(
            state, "workflow_key", "brightness", "any", 0, 0, 127, 0, 127, False, 0, False
        )
        cc_value, cc_raw = int_node.load_int_midi(
            state, "cc_number", "", "1", 22, 0, 127, 0, 127, False, 0, False
        )
        self.assertEqual(key_value, 96)
        self.assertEqual(key_raw, 96.0)
        self.assertEqual(cc_value, 11)
        self.assertEqual(cc_raw, 11.0)

    def test_reverse_mapping(self):
        node = VrchIntMidiControlNode()
        value, raw = node.load_int_midi(
            midi_state(), "workflow_key", "brightness", "any", 0, 0, 127, 0, 127, True, 0, False
        )
        self.assertEqual(value, 31)
        self.assertEqual(raw, 96.0)

    def test_range_validation(self):
        node = VrchFloatMidiControlNode()
        with self.assertRaises(ValueError):
            node.load_float_midi(midi_state(), "workflow_key", "brightness", "any", 0, 10, 0, 0, 1, False, 0, False)
        with self.assertRaises(ValueError):
            node.load_float_midi(midi_state(), "workflow_key", "brightness", "any", 0, 0, 127, 10, 1, False, 0, False)
        with self.assertRaises(ValueError):
            node.load_float_midi(midi_state(), "workflow_key", "brightness", "any", 0, 0, 127, 0, 1, False, 2, False)


if __name__ == "__main__":
    unittest.main(verbosity=1)
