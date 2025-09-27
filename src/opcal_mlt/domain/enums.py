"""Enumerations describing high-level domain concepts for OPCAL-Labeler."""
from __future__ import annotations

from enum import Enum, auto


class Stage(Enum):
    """Sequential steps in the labeling workflow."""

    START = auto()
    INGEST = auto()
    WORKSPACE = auto()
    EXPORT = auto()


class BaselineMethod(Enum):
    """Supported baseline estimation strategies."""

    ROLLING_MEDIAN = "rolling_median"
    PERCENTILE_25 = "percentile_25"

    @classmethod
    def from_str(cls, value: str) -> "BaselineMethod":
        normalized = (value or "").strip().lower()
        if normalized.startswith("rolling"):
            return cls.ROLLING_MEDIAN
        if "percentile" in normalized:
            return cls.PERCENTILE_25
        msg = f"Unsupported baseline method: {value!r}"
        raise ValueError(msg)


class LabelClass(Enum):
    """Canonical label classes exposed in the UI."""

    HIGH_FLAT = "High-flat"
    HIGH_OSCILLATORY = "High-oscillatory"
    OSCILLATORY = "Oscillatory"
    LOW_ACTIVITY = "Low-activity"
    DRIFTING = "Drifting"

    @classmethod
    def default(cls) -> "LabelClass":
        return cls.OSCILLATORY

    @classmethod
    def from_str(cls, label: str) -> "LabelClass":
        for member in cls:
            if member.value.lower() == (label or "").strip().lower():
                return member
        msg = f"Unknown label class: {label!r}"
        raise ValueError(msg)


__all__ = ["Stage", "BaselineMethod", "LabelClass"]
