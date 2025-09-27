"""Domain events used for audit logging and undo history."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from opcal_mlt.domain.enums import LabelClass


@dataclass(slots=True)
class LabelSaved:
    cell_index: int
    label: LabelClass
    saved_at: datetime
    uncertain: bool = False


@dataclass(slots=True)
class UndoPerformed:
    cell_index: int
    restored_label: LabelClass | None
    undone_at: datetime


__all__ = ["LabelSaved", "UndoPerformed"]
