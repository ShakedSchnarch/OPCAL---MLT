"""
Domain Events
=============

Domain events used for audit logging and undo history in OPCAL-Labeler.
Defines event structures for label saving and undo operations.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from opcal_mlt.domain.enums import LabelClass


@dataclass(slots=True)
class LabelSaved:
    """
    Event representing a saved label action.

    Attributes:
        cell_index (int): Index of the labeled cell.
        label (LabelClass): Label assigned to the cell.
        saved_at (datetime): Timestamp of save event.
        uncertain (bool): Whether the label was marked as uncertain.
    """
    cell_index: int
    label: LabelClass
    saved_at: datetime
    uncertain: bool = False


@dataclass(slots=True)
class UndoPerformed:
    """
    Event representing an undo action in the labeling workflow.

    Attributes:
        cell_index (int): Index of the cell affected by undo.
        restored_label (LabelClass | None): Label restored by undo, if any.
        undone_at (datetime): Timestamp of undo event.
    """
    cell_index: int
    restored_label: LabelClass | None
    undone_at: datetime


__all__ = ["LabelSaved", "UndoPerformed"]
