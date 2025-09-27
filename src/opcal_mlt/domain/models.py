"""Typed domain models to decouple UI code from raw dictionaries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

import numpy as np

from opcal_mlt.domain.enums import BaselineMethod, LabelClass, Stage

LabelNotes = str
LabelMap = Dict[int, "LabelState"]


@dataclass(slots=True)
class SessionConfig:
    """User-specified configuration for a labeling session."""

    annotator_id: str
    save_root: Path
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.annotator_id:
            raise ValueError("annotator_id must be a non-empty string")
        self.save_root = Path(self.save_root).expanduser()


@dataclass(slots=True)
class SessionPaths:
    """Resolved filesystem locations tied to a session."""

    base_dir: Path
    session_dir: Path

    def ensure(self) -> Path:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        return self.session_dir


@dataclass(slots=True)
class TraceSet:
    """Bundle traces, identifiers and sampling rate as a cohesive unit."""

    traces: np.ndarray
    cell_ids: List[str]
    fs_hz: float

    def __post_init__(self) -> None:
        if self.traces.ndim != 2:
            raise ValueError("traces must be a 2D array (T x N)")
        if len(self.cell_ids) != self.traces.shape[1]:
            raise ValueError("cell_ids length must match number of columns in traces")
        if self.fs_hz <= 0:
            raise ValueError("fs_hz must be positive")


@dataclass(slots=True, kw_only=True)
class LabelState:
    """In-memory representation of a labeled cell."""

    cell_index: int
    label: LabelClass
    notes: LabelNotes = ""
    uncertain: bool = False


@dataclass(slots=True, kw_only=True)
class LabelRecord(LabelState):
    """Serialized representation with session metadata and features."""

    session_id: str
    recording_id: str
    annotator_id: str
    saved_utc: datetime
    feature_mean: float
    feature_std: float
    feature_rms: float
    frac_above_thr: float
    peaks_per_min: float
    filter_type: str
    filter_window: int
    filter_polyorder: int
    baseline_method: BaselineMethod
    baseline_window_s_or_q: float
    threshold_k: float


@dataclass(slots=True, kw_only=True)
class PeakRecord:
    """Single detected peak tied to a saved label."""

    session_id: str
    recording_id: str
    cell_index: int
    peak_idx: int
    peak_time_s: float
    peak_value: float


@dataclass(slots=True)
class WorkspaceSnapshot:
    """Summary of the workspace after saving a label."""

    label_map: LabelMap = field(default_factory=dict)
    history: List[LabelState] = field(default_factory=list)
    stage: Stage = Stage.WORKSPACE


@dataclass(slots=True, kw_only=True)
class SessionSummary:
    """Lightweight descriptor used when listing resumable sessions."""

    session_dir: Path
    recording_id: str
    labels_count: int
    last_modified: datetime


@dataclass(slots=True, kw_only=True)
class LoadedSession:
    """Full session payload returned when hydrating from disk."""

    session_dir: Path
    label_map: LabelMap
    cell_ids: Optional[List[str]]
    metadata: Mapping[str, Any]


def build_label_map(records: Iterable[LabelState]) -> LabelMap:
    """Create a lookup map from an iterable of label states."""

    result: LabelMap = {}
    for item in records:
        result[int(item.cell_index)] = item
    return result


__all__ = [
    "SessionConfig",
    "SessionPaths",
    "TraceSet",
    "LabelState",
    "LabelRecord",
    "PeakRecord",
    "WorkspaceSnapshot",
    "SessionSummary",
    "LoadedSession",
    "LabelMap",
    "build_label_map",
]
