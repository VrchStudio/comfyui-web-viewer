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


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


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

    def test_state_source_metadata_is_preserved(self):
        parser = MidiStateParser(debug=False)
        parser(encode_definition_frame([{"key": "brightness", "number": 22}], definition_seq=1, seq=1))
        state = parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 32}],
                definition_seq=1,
                seq=2,
                sender_id="midi-sender-secondary",
                source_tier="secondary",
            )
        )
        self.assertEqual(state["sender_id"], "midi-sender-secondary")
        self.assertEqual(state["source_tier"], "secondary")
        self.assertEqual(state["value_source_tiers_by_index"][0], "secondary")

    def test_full_snapshots_only_merge_values_changed_by_that_sender(self):
        parser = MidiStateParser(debug=False)
        primary_controls = [
            {"control_index": 0, "key": "brightness", "number": 22},
            {"control_index": 1, "key": "seed", "number": 23},
        ]
        secondary_controls = [
            {"control_index": 5, "key": "brightness", "number": 22},
            {"control_index": 6, "key": "seed", "number": 23},
        ]
        parser(encode_definition_frame(primary_controls, sender_id="primary-midi", source_tier="primary"))
        parser(encode_definition_frame(secondary_controls, sender_id="secondary-midi", source_tier="secondary"))
        parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 90}, {"control_index": 1, "value": 10}],
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        parser(
            encode_state_frame(
                control_values=[{"control_index": 5, "value": 20}, {"control_index": 6, "value": 20}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )

        state = parser(
            encode_state_frame(
                control_values=[{"control_index": 5, "value": 30}, {"control_index": 6, "value": 20}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        self.assertEqual(state["values_by_index"][state["index_by_key"]["brightness"]], 30)

        state = parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 90}, {"control_index": 1, "value": 11}],
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        self.assertEqual(state["values_by_index"][state["index_by_key"]["brightness"]], 30)
        self.assertEqual(state["values_by_index"][state["index_by_key"]["seed"]], 11)
        self.assertEqual(state["value_source_tiers_by_index"][state["index_by_key"]["brightness"]], "secondary")
        self.assertEqual(state["value_source_tiers_by_index"][state["index_by_key"]["seed"]], "primary")

    def test_primary_activity_window_only_blocks_same_control_temporarily(self):
        clock = FakeClock()
        parser = MidiStateParser(debug=False, monotonic_clock=clock)
        controls = [
            {"key": "brightness", "number": 22},
            {"key": "seed", "number": 23},
        ]
        parser(encode_definition_frame(controls, sender_id="primary-midi", source_tier="primary"))
        parser(encode_definition_frame(controls, sender_id="secondary-midi", source_tier="secondary"))
        parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 90}, {"control_index": 1, "value": 10}],
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 20}, {"control_index": 1, "value": 20}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        state = parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 30}, {"control_index": 1, "value": 20}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        self.assertEqual(state["values_by_index"][0], 30)

        state = parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 100}, {"control_index": 1, "value": 10}],
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        self.assertEqual(state["values_by_index"][0], 100)
        state = parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 40}, {"control_index": 1, "value": 21}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        self.assertEqual(state["values_by_index"][0], 100)
        self.assertEqual(state["values_by_index"][1], 21)

        clock.advance(0.31)
        state = parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 41}, {"control_index": 1, "value": 21}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        self.assertEqual(state["values_by_index"][0], 41)
        self.assertEqual(state["value_source_tiers_by_index"][0], "secondary")

    def test_raw_cc_and_notes_use_the_same_activity_window(self):
        clock = FakeClock()
        parser = MidiStateParser(debug=False, monotonic_clock=clock)
        parser(encode_definition_frame([], definition_seq=1, seq=1))
        parser(
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": 22, "value": 90}],
                raw_notes=[{"midi_channel": 0, "number": 36, "velocity": 64, "status": "noteOn"}],
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        parser(
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": 22, "value": 20}],
                raw_notes=[{"midi_channel": 0, "number": 36, "velocity": 127, "status": "noteOn"}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        parser(
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": 22, "value": 30}],
                raw_notes=[{"midi_channel": 0, "number": 36, "velocity": 0, "status": "noteOff"}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        state = parser(
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": 22, "value": 100}],
                raw_notes=[{"midi_channel": 0, "number": 36, "velocity": 32, "status": "noteOn"}],
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        self.assertEqual(state["cc_values"]["1"][22], 100)
        self.assertEqual(state["notes"]["1"][36]["velocity"], 32)

        state = parser(
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": 22, "value": 40}],
                raw_notes=[{"midi_channel": 0, "number": 36, "velocity": 127, "status": "noteOn"}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        self.assertEqual(state["cc_values"]["any"][22], 100)
        self.assertEqual(state["notes"]["any"][36]["velocity"], 32)

        clock.advance(0.31)
        state = parser(
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": 22, "value": 41}],
                raw_notes=[{"midi_channel": 0, "number": 36, "velocity": 0, "status": "noteOff"}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        self.assertEqual(state["cc_values"]["1"][22], 41)
        self.assertEqual(state["notes"]["1"][36]["velocity"], 0)
        self.assertEqual(state["cc_source_tiers"]["1"][22], "secondary")
        self.assertEqual(state["note_source_tiers"]["1"][36], "secondary")

    def test_repeated_definition_does_not_turn_next_snapshot_into_changes(self):
        parser = MidiStateParser(debug=False)
        controls = [{"key": "brightness", "number": 22}]
        primary_definition = encode_definition_frame(
            controls,
            definition_seq=7,
            sender_id="primary-midi",
            source_tier="primary",
        )
        parser(primary_definition)
        parser(
            encode_definition_frame(
                controls,
                definition_seq=7,
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 90}],
                definition_seq=7,
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 20}],
                definition_seq=7,
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        state = parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 30}],
                definition_seq=7,
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        self.assertEqual(state["values_by_index"][0], 30)

        parser(primary_definition)
        state = parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 90}],
                definition_seq=7,
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        self.assertEqual(state["values_by_index"][0], 30)

    def test_secondary_promotion_applies_its_full_snapshot(self):
        parser = MidiStateParser(debug=False)
        controls = [{"key": "brightness", "number": 22}]
        parser(encode_definition_frame(controls, sender_id="primary-midi", source_tier="primary"))
        parser(encode_definition_frame(controls, sender_id="secondary-midi", source_tier="secondary"))
        parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 90}],
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 20}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        state = parser(
            encode_state_frame(
                control_values=[{"control_index": 0, "value": 20}],
                sender_id="secondary-midi",
                source_tier="primary",
            )
        )
        self.assertEqual(state["values_by_index"][0], 20)
        self.assertEqual(state["value_source_tiers_by_index"][0], "primary")

    def test_expired_sender_definition_is_removed_from_composite(self):
        clock = FakeClock()
        parser = MidiStateParser(debug=False, monotonic_clock=clock, source_expiry_seconds=6.0)
        parser(
            encode_definition_frame(
                [{"key": "brightness", "number": 22}],
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        self.assertIn("brightness", parser.empty_state()["index_by_key"])

        clock.advance(6.1)
        state = parser(
            encode_definition_frame(
                [{"key": "seed", "number": 23}],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )
        self.assertNotIn("brightness", state["index_by_key"])
        self.assertIn("seed", state["index_by_key"])

    def test_malformed_frames_do_not_raise(self):
        parser = MidiStateParser(debug=False)
        empty = parser.empty_state()
        self.assertEqual(parser(b"short"), empty)
        self.assertEqual(parser(b"BAD!" + b"\x01" * 20), empty)
        self.assertEqual(parser(MAGIC + b"\x02" + b"\x01" * 20), empty)
        self.assertEqual(parser(MAGIC + b"\x01\x63\x00\x00" + b"\x00" * 8), empty)
        malformed_definition = encode_definition_frame([{"key": "brightness", "number": 22}])[:20]
        self.assertEqual(parser(malformed_definition), empty)
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

    def test_two_sender_merge_speed_for_8_controls(self):
        parser = MidiStateParser(debug=False)
        controls = [{"key": f"button_{idx}", "number": idx} for idx in range(8)]
        parser(encode_definition_frame(controls, sender_id="primary-midi", source_tier="primary"))
        parser(encode_definition_frame(controls, sender_id="secondary-midi", source_tier="secondary"))
        parser(
            encode_state_frame(
                control_values=[{"control_index": idx, "value": idx} for idx in range(8)],
                sender_id="primary-midi",
                source_tier="primary",
            )
        )
        parser(
            encode_state_frame(
                control_values=[{"control_index": idx, "value": idx} for idx in range(8)],
                sender_id="secondary-midi",
                source_tier="secondary",
            )
        )

        started = time.perf_counter()
        for seq in range(100):
            state = parser(
                encode_state_frame(
                    control_values=[
                        {"control_index": idx, "value": (seq + idx + 1) % 128}
                        for idx in range(8)
                    ],
                    seq=seq + 2,
                    sender_id="secondary-midi",
                    source_tier="secondary",
                )
            )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        self.assertEqual(len(state["values_by_index"]), 8)
        self.assertLess(elapsed_ms, 100.0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
