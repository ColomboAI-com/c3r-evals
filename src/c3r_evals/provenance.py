"""Strict provenance and deterministic split controls."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from typing import Iterable, Literal

Split = Literal["train", "validation", "calibration", "test"]


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


@dataclass(frozen=True)
class GovernedRecord:
    record_id: str
    group_id: str
    content: str
    source_uri: str
    license_id: str
    consent_basis: str
    collected_at: str
    generator: str

    @property
    def content_sha256(self) -> str:
        return _digest(self.content)

    @property
    def normalized_sha256(self) -> str:
        return _digest(_normalized(self.content))

    def validate(self) -> None:
        for name, value in vars(self).items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not self.collected_at.endswith("Z"):
            raise ValueError("collected_at must be an explicit UTC timestamp ending in Z")


def assign_split(group_id: str, namespace: str = "decisionmix-v1") -> Split:
    """Assign whole groups so related examples cannot cross split boundaries."""
    bucket = int(_digest(f"{namespace}:{group_id}")[:8], 16) % 100
    if bucket < 70:
        return "train"
    if bucket < 80:
        return "validation"
    if bucket < 90:
        return "calibration"
    return "test"


def validate_corpus(records: Iterable[GovernedRecord]) -> dict[str, int]:
    seen_ids: set[str] = set()
    seen_content: dict[str, str] = {}
    group_splits: dict[str, Split] = {}
    counts = {name: 0 for name in ("train", "validation", "calibration", "test")}
    for record in records:
        record.validate()
        if record.record_id in seen_ids:
            raise ValueError(f"duplicate record_id: {record.record_id}")
        seen_ids.add(record.record_id)
        prior = seen_content.get(record.normalized_sha256)
        if prior is not None:
            raise ValueError(f"normalized-content collision: {prior}, {record.record_id}")
        seen_content[record.normalized_sha256] = record.record_id
        split = assign_split(record.group_id)
        if record.group_id in group_splits and group_splits[record.group_id] != split:
            raise AssertionError("group split is not deterministic")
        group_splits[record.group_id] = split
        counts[split] += 1
    return counts

