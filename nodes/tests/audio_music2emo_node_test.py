#!/usr/bin/env python3
"""Tests for VrchAudioMusic2EmotionNode mood text formatting."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from nodes.audio_music2emo_node import VrchAudioMusic2EmotionNode  # noqa: E402


class TestAudioMusic2EmotionNode(unittest.TestCase):
    def test_weighted_and_name_only_moods_use_same_threshold_and_order(self):
        moods_output, moods_name_only = VrchAudioMusic2EmotionNode._format_moods_outputs(
            predicted_moods=[],
            mood_probs={
                "calm": 0.25,
                "happy": 0.9,
                "upbeat": 0.75,
            },
            threshold=0.5,
        )

        self.assertEqual(moods_output, "happy: 0.9000\nupbeat: 0.7500")
        self.assertEqual(moods_name_only, "happy, upbeat")

    def test_name_only_is_empty_when_no_moods_pass_threshold(self):
        moods_output, moods_name_only = VrchAudioMusic2EmotionNode._format_moods_outputs(
            predicted_moods=[],
            mood_probs={"calm": 0.25},
            threshold=0.5,
        )

        self.assertEqual(moods_output, "No moods detected")
        self.assertEqual(moods_name_only, "")

    def test_fallback_predicted_moods_are_comma_separated(self):
        moods_output, moods_name_only = VrchAudioMusic2EmotionNode._format_moods_outputs(
            predicted_moods=["dreamy", "gentle", "warm"],
            mood_probs={},
            threshold=0.5,
        )

        self.assertEqual(moods_output, "dreamy, gentle, warm")
        self.assertEqual(moods_name_only, "dreamy, gentle, warm")


if __name__ == "__main__":
    unittest.main()
