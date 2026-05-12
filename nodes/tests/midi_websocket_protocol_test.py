#!/usr/bin/env python3
"""Tests for VRCH MIDI WebSocket binary protocol."""

import json
import sys
import time
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from nodes.midi_websocket_protocol import (  # noqa: E402
    MAGIC,
    MidiStateParser,
    encode_definition_frame,
    encode_state_frame,
)


class TestMidiWebSocketProtocol(unittest.TestCase):
    def test_definition_and_state_roundtrip(self):
        parser = MidiStateParser(debug=False)
        definition = encode_definition_frame(
            [
                {"key": "brightness", "id": "knob-1", "label": "Brightness", "type": "cc", "midi_channel": 0, "number": 22},
                {"key": "seed", "id": "fader-1", "label": "Seed", "type": "cc", "midi_channel": 0, "number": 7},
            ],
            definition_seq=4,
            seq=10,
        )
        state = parser(definition)
        self.assertTrue(state["definition_ready"])
        self.assertEqual(state["definition_seq"], 4)
        self.assertEqual(state["index_by_key"], {"brightness": 0, "seed": 1})
        self.assertEqual(state["index_by_cc"]["1:22"], 0)
        json.dumps(state)
        self.assertEqual(state["definitions_by_index"][0]["label"], "Brightness")
        self.assertNotIn("Brightness", state["index_by_key"])
        self.assertNotIn("knob-1", state["index_by_key"])

        state = parser(
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": 22, "value": 96}],
                control_values=[{"control_index": 0, "value": 96}],
                definition_seq=4,
                seq=11,
            )
        )
        self.assertEqual(state["values_by_index"][0], 96)
        self.assertEqual(state["cc_values"]["1"][22], 96)
        self.assertEqual(state["cc_values"]["any"][22], 96)

    def test_note_state_is_preserved(self):
        parser = MidiStateParser(debug=False)
        parser(encode_definition_frame([], definition_seq=1, seq=1))
        state = parser(
            encode_state_frame(
                raw_notes=[{"midi_channel": 0, "number": 36, "velocity": 127, "status": "noteOn"}],
                definition_seq=1,
                seq=2,
            )
        )
        note = state["notes"]["1"][36]
        self.assertEqual(note["velocity"], 127)
        self.assertTrue(note["is_on"])
        self.assertFalse(note["is_off"])
        state = parser(
            encode_state_frame(
                raw_notes=[{"midi_channel": 0, "number": 36, "velocity": 0, "status": "noteOff"}],
                definition_seq=1,
                seq=3,
            )
        )
        note = state["notes"]["1"][36]
        self.assertEqual(note["velocity"], 0)
        self.assertFalse(note["is_on"])
        self.assertTrue(note["is_off"])

    def test_malformed_frames_do_not_raise(self):
        parser = MidiStateParser(debug=False)
        empty = parser.empty_state()
        self.assertEqual(parser(b"short"), empty)
        self.assertEqual(parser(b"BAD!" + b"\x01" * 20), empty)
        self.assertEqual(parser(MAGIC + b"\x02" + b"\x01" * 20), empty)
        self.assertEqual(parser(MAGIC + b"\x01\x63\x00\x00" + b"\x00" * 8), empty)
        self.assertEqual(parser(encode_definition_frame([{"key": "brightness", "number": 22}])[:-1]), empty)
        self.assertEqual(parser("text frame"), empty)

    def test_state_definition_mismatch_keeps_raw_but_not_key_values(self):
        parser = MidiStateParser(debug=False)
        parser(encode_definition_frame([{"key": "brightness", "number": 22}], definition_seq=1, seq=1))
        state = parser(
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": 22, "value": 64}],
                control_values=[{"control_index": 0, "value": 64}],
                definition_seq=99,
                seq=2,
            )
        )
        self.assertEqual(state["cc_values"]["1"][22], 64)
        self.assertNotIn(0, state["values_by_index"])

    def test_duplicate_workflow_key_keeps_first_mapping(self):
        parser = MidiStateParser(debug=False)
        state = parser(
            encode_definition_frame(
                [
                    {"control_index": 0, "key": "brightness", "number": 22},
                    {"control_index": 1, "key": "brightness", "number": 23},
                ],
                definition_seq=1,
                seq=1,
            )
        )
        self.assertEqual(state["index_by_key"]["brightness"], 0)

    def test_parser_lookup_speed_for_8_controls(self):
        parser = MidiStateParser(debug=False)
        controls = [{"key": f"button_{idx}", "number": idx} for idx in range(8)]
        parser(encode_definition_frame(controls, definition_seq=1, seq=1))
        started = time.perf_counter()
        state = parser(
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": idx, "value": idx + 1} for idx in range(8)],
                control_values=[{"control_index": idx, "value": idx + 1} for idx in range(8)],
                definition_seq=1,
                seq=2,
            )
        )
        values = [state["values_by_index"][idx] for idx in range(8)]
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self.assertEqual(values, list(range(1, 9)))
        self.assertLess(elapsed_ms, 15.0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
