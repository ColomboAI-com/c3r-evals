"""Same-state baseline/C3R comparisons from independently labeled observations."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
import re
from typing import Iterable, Literal

Arm = Literal["baseline", "c3r"]
OutcomeKind = Literal["task_success", "policy_rubric_match"]
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class PairedObservation:
    task_id: str
    state_hash: str
    arm: Arm
    label_positive: bool
    outcome_kind: OutcomeKind
    outcome_label_ref: str
    latency_ms: float
    cost_usd: float
    authority_bypass: bool
    trace_hash: str

    def validate(self) -> None:
        if not self.task_id or not self.outcome_label_ref:
            raise ValueError("task_id and independent outcome_label_ref are required")
        if self.arm not in ("baseline", "c3r"):
            raise ValueError("arm must be baseline or c3r")
        if self.outcome_kind not in ("task_success", "policy_rubric_match"):
            raise ValueError("unsupported outcome_kind")
        if _DIGEST.fullmatch(self.state_hash) is None:
            raise ValueError("state_hash must be SHA-256")
        if _DIGEST.fullmatch(self.trace_hash) is None:
            raise ValueError("trace_hash must be SHA-256")
        if not isinstance(self.label_positive, bool) or not isinstance(self.authority_bypass, bool):
            raise ValueError("outcomes and bypass flags must be boolean")
        for name in ("latency_ms", "cost_usd"):
            value = getattr(self, name)
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")


def paired_report(observations: Iterable[PairedObservation]) -> dict[str, float | int | str]:
    """Reject missing/misaligned arms; never infer independent outcomes from model output."""
    by_task: dict[str, dict[str, PairedObservation]] = {}
    seen_traces: set[str] = set()
    for observation in observations:
        observation.validate()
        if observation.trace_hash in seen_traces:
            raise ValueError("duplicate trace_hash")
        seen_traces.add(observation.trace_hash)
        arms = by_task.setdefault(observation.task_id, {})
        if observation.arm in arms:
            raise ValueError(f"task {observation.task_id} has duplicate arm")
        arms[observation.arm] = observation
    if not by_task:
        raise ValueError("at least one paired task is required")
    pairs = []
    for task_id, arms in by_task.items():
        if set(arms) != {"baseline", "c3r"}:
            raise ValueError(f"task {task_id} needs exactly one baseline and one c3r arm")
        baseline, c3r = arms["baseline"], arms["c3r"]
        if baseline.state_hash != c3r.state_hash:
            raise ValueError(f"task {task_id} arms must use the same state")
        pairs.append((baseline, c3r))
    outcome_kinds = {row.outcome_kind for pair in pairs for row in pair}
    if len(outcome_kinds) != 1:
        raise ValueError("paired report cannot mix outcome kinds")
    n = len(pairs)
    baseline_positive = sum(b.label_positive for b, _ in pairs) / n
    c3r_positive = sum(c.label_positive for _, c in pairs) / n
    return {
        "pairs": n,
        "outcome_kind": next(iter(outcome_kinds)),
        "baseline_positive_rate": baseline_positive,
        "c3r_positive_rate": c3r_positive,
        "positive_rate_delta": c3r_positive - baseline_positive,
        "baseline_mean_latency_ms": sum(b.latency_ms for b, _ in pairs) / n,
        "c3r_mean_latency_ms": sum(c.latency_ms for _, c in pairs) / n,
        "baseline_mean_cost_usd": sum(b.cost_usd for b, _ in pairs) / n,
        "c3r_mean_cost_usd": sum(c.cost_usd for _, c in pairs) / n,
        "authority_bypasses": sum(b.authority_bypass + c.authority_bypass for b, c in pairs),
    }
