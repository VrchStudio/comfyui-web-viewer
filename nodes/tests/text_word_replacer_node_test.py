#!/usr/bin/env python3
"""Tests for VrchTextWordReplacerNode."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from nodes.text_nodes import VrchTextWordReplacerNode  # noqa: E402


class TestTextWordReplacerNode(unittest.TestCase):
    def setUp(self):
        self.node = VrchTextWordReplacerNode()

    def replace(self, text, rules, match_mode="whole_word", case_sensitive=False):
        return self.node.replace_text(
            text=text,
            rules=rules,
            match_mode=match_mode,
            case_sensitive=case_sensitive,
            debug=False,
        )

    def test_basic_replacement_and_report(self):
        output, report = self.replace(
            "happy and sad",
            "happy => joyful\nsad => melancholic",
        )

        self.assertEqual(output, "joyful and melancholic")
        self.assertEqual(report["rules_count"], 2)
        self.assertEqual(report["replaced_count"], 2)
        self.assertEqual(report["matched"], {"happy": 1, "sad": 1})

    def test_whole_word_does_not_replace_inside_words(self):
        output, report = self.replace("sad sadness unsad", "sad => blue")

        self.assertEqual(output, "blue sadness unsad")
        self.assertEqual(report["replaced_count"], 1)

    def test_literal_mode_replaces_inside_words(self):
        output, report = self.replace("sad sadness", "sad => blue", match_mode="literal")

        self.assertEqual(output, "blue blueness")
        self.assertEqual(report["replaced_count"], 2)

    def test_case_insensitive_matching(self):
        output, report = self.replace("Happy happy HAPPY", "happy => joyful")

        self.assertEqual(output, "joyful joyful joyful")
        self.assertEqual(report["matched"], {"happy": 3})

    def test_case_sensitive_matching(self):
        output, report = self.replace("Happy happy", "happy => joyful", case_sensitive=True)

        self.assertEqual(output, "Happy joyful")
        self.assertEqual(report["replaced_count"], 1)

    def test_longer_source_matches_before_shorter_source(self):
        output, report = self.replace(
            "cat girl and cat",
            "cat => dog\ncat girl => neko girl",
        )

        self.assertEqual(output, "neko girl and dog")
        self.assertEqual(report["matched"], {"cat girl": 1, "cat": 1})

    def test_replacements_do_not_cascade(self):
        output, report = self.replace(
            "happy sad",
            "happy => sad\nsad => dark",
        )

        self.assertEqual(output, "sad dark")
        self.assertEqual(report["matched"], {"happy": 1, "sad": 1})

    def test_empty_target_deletes_text(self):
        output, report = self.replace("bad mood", "bad =>")

        self.assertEqual(output, " mood")
        self.assertEqual(report["replaced_count"], 1)

    def test_comments_empty_lines_and_invalid_rules_are_ignored(self):
        output, report = self.replace(
            "happy and sad",
            """
            # comment
            invalid line
            happy => joyful

            => ignored
            sad => calm
            """,
        )

        self.assertEqual(output, "joyful and calm")
        self.assertEqual(report["rules_count"], 2)
        self.assertEqual(report["ignored_rules_count"], 2)

    def test_empty_rules_return_original_text(self):
        output, report = self.replace("keep this", "")

        self.assertEqual(output, "keep this")
        self.assertEqual(report["rules_count"], 0)
        self.assertEqual(report["replaced_count"], 0)


if __name__ == "__main__":
    unittest.main()
