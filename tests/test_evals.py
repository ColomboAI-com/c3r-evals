import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from c3r_evals import GovernedRecord, assign_split, calibration_report, validate_corpus


def record(record_id: str, group: str, content: str) -> GovernedRecord:
    return GovernedRecord(record_id, group, content, "https://example.test/source", "CC-BY-4.0",
                          "documented-public-license", "2026-09-22T00:00:00Z", "fixture-v1")


class GovernanceTests(unittest.TestCase):
    def test_split_is_stable_and_group_aware(self):
        self.assertEqual(assign_split("group-a"), assign_split("group-a"))

    def test_normalized_duplicates_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "collision"):
            validate_corpus([record("a", "g1", "Hello   World"), record("b", "g2", " hello world ")])

    def test_provenance_is_required(self):
        with self.assertRaisesRegex(ValueError, "license_id"):
            record("a", "g1", "x").__class__("a", "g1", "x", "uri", "", "consent", "2026-09-22T00:00:00Z", "gen").validate()


class MetricTests(unittest.TestCase):
    def test_perfect_predictions(self):
        report = calibration_report([0.0, 1.0], [0, 1])
        self.assertEqual(report["accuracy"], 1.0)
        self.assertEqual(report["brier"], 0.0)
        self.assertEqual(report["ece"], 0.0)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            calibration_report([1.2], [1])


if __name__ == "__main__":
    unittest.main()
