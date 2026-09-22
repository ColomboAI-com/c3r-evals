"""Dependency-free binary calibration metrics."""

from __future__ import annotations

from math import log
from typing import Sequence


def calibration_report(
    probabilities: Sequence[float], labels: Sequence[int], bins: int = 10, threshold: float = 0.5
) -> dict[str, float]:
    if len(probabilities) != len(labels) or not probabilities:
        raise ValueError("probabilities and labels must have equal, non-zero length")
    if bins < 1:
        raise ValueError("bins must be positive")
    pairs = []
    for probability, label in zip(probabilities, labels, strict=True):
        if not 0 <= probability <= 1 or label not in (0, 1):
            raise ValueError("probabilities must be [0,1] and labels binary")
        pairs.append((float(probability), int(label)))
    epsilon = 1e-12
    accuracy = sum((p >= threshold) == bool(y) for p, y in pairs) / len(pairs)
    brier = sum((p - y) ** 2 for p, y in pairs) / len(pairs)
    nll = -sum(y * log(max(p, epsilon)) + (1 - y) * log(max(1 - p, epsilon)) for p, y in pairs) / len(pairs)
    errors: list[tuple[int, float]] = []
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        members = [(p, y) for p, y in pairs if low <= p < high or (index == bins - 1 and p == 1)]
        if members:
            confidence = sum(p for p, _ in members) / len(members)
            observed = sum(y for _, y in members) / len(members)
            errors.append((len(members), abs(confidence - observed)))
    ece = sum(size * error for size, error in errors) / len(pairs)
    return {"count": float(len(pairs)), "accuracy": accuracy, "brier": brier, "nll": nll,
            "ece": ece, "mce": max(error for _, error in errors)}

