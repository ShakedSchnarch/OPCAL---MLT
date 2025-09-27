"""
Domain Enumerations
===================

Enumerations describing high-level domain concepts for OPCAL-Labeler.
Used for workflow stages, baseline methods, and canonical label classes.
"""
from __future__ import annotations

from enum import Enum, auto


class Stage(Enum):
    """
    Sequential steps in the labeling workflow.

    Members:
        START: Initial stage.
        INGEST: Data ingestion stage.
        WORKSPACE: Workspace/labeling stage.
        EXPORT: Export results stage.
    """

    START = auto()
    INGEST = auto()
    WORKSPACE = auto()
    EXPORT = auto()


class BaselineMethod(Enum):
    """
    Supported baseline estimation strategies.

    Members:
        ROLLING_MEDIAN: Rolling median baseline.
        PERCENTILE_25: 25th percentile baseline.
    """

    ROLLING_MEDIAN = "rolling_median"
    PERCENTILE_25 = "percentile_25"

    @classmethod
    def from_str(cls, value: str) -> "BaselineMethod":
        """
        Convert a string to a BaselineMethod enum member.

        Args:
            value (str): String representation of the baseline method.

        Returns:
            BaselineMethod: Corresponding enum member.

        Raises:
            ValueError: If the method is unsupported.
        """
        normalized = (value or "").strip().lower()
        if normalized.startswith("rolling"):
            return cls.ROLLING_MEDIAN
        if "percentile" in normalized:
            return cls.PERCENTILE_25
        msg = f"Unsupported baseline method: {value!r}"
        raise ValueError(msg)


class LabelClass(Enum):
    """
    Canonical label classes exposed in the UI.

    Members:
        HIGH_FLAT: High-flat activity.
        HIGH_OSCILLATORY: High-oscillatory activity.
        OSCILLATORY: Oscillatory activity.
        LOW_ACTIVITY: Low activity.
        DRIFTING: Drifting activity.
    """

    HIGH_FLAT = "High-flat"
    HIGH_OSCILLATORY = "High-oscillatory"
    OSCILLATORY = "Oscillatory"
    LOW_ACTIVITY = "Low-activity"
    DRIFTING = "Drifting"

    @classmethod
    def default(cls) -> "LabelClass":
        """
        Return the default label class (OSCILLATORY).

        Returns:
            LabelClass: Default label class.
        """
        return cls.OSCILLATORY

    @classmethod
    def from_str(cls, label: str) -> "LabelClass":
        """
        Convert a string to a LabelClass enum member.

        Args:
            label (str): String representation of the label class.

        Returns:
            LabelClass: Corresponding enum member.

        Raises:
            ValueError: If the label class is unknown.
        """
        for member in cls:
            if member.value.lower() == (label or "").strip().lower():
                return member
        msg = f"Unknown label class: {label!r}"
        raise ValueError(msg)


__all__ = ["Stage", "BaselineMethod", "LabelClass"]
