"""Governed evaluation primitives for C3R."""

from .metrics import calibration_report
from .provenance import GovernedRecord, assign_split, validate_corpus

__all__ = ["GovernedRecord", "assign_split", "calibration_report", "validate_corpus"]

