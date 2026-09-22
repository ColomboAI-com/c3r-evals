import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from c3r_evals.paired import PairedObservation, paired_report


def observation(task: str, arm: str, *, success: bool, state: str = "a" * 64) -> PairedObservation:
    return PairedObservation(
        task_id=task,
        state_hash=state,
        arm=arm,
        label_positive=success,
        outcome_kind="policy_rubric_match",
        outcome_label_ref=f"verifier:{task}",
        latency_ms=10.0 if arm == "baseline" else 12.0,
        cost_usd=0.0 if arm == "baseline" else 0.01,
        authority_bypass=False,
        trace_hash=("b" if arm == "baseline" else "c") * 63 + task[-1],
    )


class PairedReportTests(unittest.TestCase):
    def test_same_state_paired_report(self):
        rows = [
            observation("task-1", "baseline", success=False),
            observation("task-1", "c3r", success=True),
            observation("task-2", "baseline", success=True),
            observation("task-2", "c3r", success=True),
        ]
        report = paired_report(rows)
        self.assertEqual(report["pairs"], 2)
        self.assertEqual(report["positive_rate_delta"], 0.5)
        self.assertEqual(report["outcome_kind"], "policy_rubric_match")
        self.assertEqual(report["authority_bypasses"], 0)

    def test_missing_arm_and_mismatched_state_fail(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            paired_report([observation("task-1", "baseline", success=False)])
        with self.assertRaisesRegex(ValueError, "same state"):
            paired_report([
                observation("task-1", "baseline", success=False),
                observation("task-1", "c3r", success=True, state="d" * 64),
            ])

    def test_duplicate_trace_or_invalid_measurement_fails(self):
        from dataclasses import replace

        first = observation("task-1", "baseline", success=False)
        second = observation("task-1", "c3r", success=True)
        with self.assertRaisesRegex(ValueError, "trace_hash"):
            paired_report([first, replace(second, trace_hash=first.trace_hash)])
        with self.assertRaisesRegex(ValueError, "latency_ms"):
            paired_report([first, replace(second, latency_ms=-1)])

    def test_mixed_outcome_kinds_fail(self):
        from dataclasses import replace

        first = observation("task-1", "baseline", success=False)
        second = replace(observation("task-1", "c3r", success=True), outcome_kind="task_success")
        with self.assertRaisesRegex(ValueError, "outcome kinds"):
            paired_report([first, second])


if __name__ == "__main__":
    unittest.main()
