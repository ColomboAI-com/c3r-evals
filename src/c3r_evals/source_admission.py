"""Fail-closed source admission for evidence claims, not a legal-rights determination."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

EvidenceKind = Literal["synthetic", "controlled", "field"]
Use = Literal["training", "calibration", "benchmark", "publication"]
Claim = Literal["synthetic", "controlled", "empirical", "production"]

_IMMUTABLE_REVISION = re.compile(r"^[0-9a-f]{40,64}$")


@dataclass(frozen=True)
class SourcePolicy:
    source_id: str
    revision: str
    file_sha256: str
    license_id: str
    evidence_kind: EvidenceKind
    partition: str
    rights_basis: str
    consent_basis: str
    retention_rule: str
    publication_scope: str

    def validate(self) -> None:
        for name, value in vars(self).items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if _IMMUTABLE_REVISION.fullmatch(self.revision) is None:
            raise ValueError("revision must be an immutable hexadecimal digest")
        if re.fullmatch(r"[0-9a-f]{64}", self.file_sha256) is None:
            raise ValueError("file_sha256 must be a SHA-256 digest")
        if self.evidence_kind not in ("synthetic", "controlled", "field"):
            raise ValueError("unsupported evidence_kind")
        if self.partition not in ("train", "validation", "calibration", "test", "benchmark_test", "unsplit"):
            raise ValueError("unsupported partition")
        if self.publication_scope not in ("none", "aggregate", "redacted", "attributed-derived", "raw"):
            raise ValueError("unsupported publication_scope")


@dataclass(frozen=True)
class AdmissionDecision:
    source_id: str
    revision: str
    use: Use
    claim: Claim
    evidence_kind: EvidenceKind


def admit_source(source: SourcePolicy, *, use: Use, claim: Claim) -> AdmissionDecision:
    """Check source/partition compatibility before any ingestion or release.

    A passing decision is necessary, never sufficient: it does not verify the
    submitted rights statement, independent outcome labels, or a production canary.
    """
    source.validate()
    if use not in ("training", "calibration", "benchmark", "publication"):
        raise ValueError("unsupported use")
    if claim not in ("synthetic", "controlled", "empirical", "production"):
        raise ValueError("unsupported claim")
    if source.partition in ("test", "benchmark_test") and use in ("training", "calibration"):
        raise ValueError("sealed test partition cannot be used for training or calibration")
    if source.evidence_kind == "synthetic" and (use == "calibration" or claim != "synthetic"):
        raise ValueError("synthetic source cannot support C3R calibration or empirical claims")
    if source.evidence_kind == "controlled" and claim in ("empirical", "production"):
        raise ValueError("controlled runs are not field evidence")
    if claim == "production":
        raise ValueError("source admission alone cannot establish production qualification")
    if use == "publication" and source.publication_scope == "none":
        raise ValueError("source has no publication scope")
    return AdmissionDecision(source.source_id, source.revision, use, claim, source.evidence_kind)
