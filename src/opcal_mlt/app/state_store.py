"""State persistence helpers for Streamlit session state.

This module knows how to serialize a subset of ``st.session_state`` to disk so
that browser navigation (back/forward/refresh) keeps the OPCAL MLT workflow in
sync. The intent is to keep blobs (numpy arrays) separate from light-weight
metadata to avoid corrupting large files on frequent writes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from opcal_mlt.domain.enums import Stage

SNAPSHOT_VERSION = 1
SNAPSHOT_FILENAME = "session_state.json"
TRACES_FILENAME = "session_traces.npz"
CACHE_ROOT = Path.home() / ".opcal_mlt" / "state_cache"

_SIMPLE_KEYS: tuple[str, ...] = (
    "annotator",
    "save_dir",
    "stage",
    "params_confirmed",
    "export_done",
    "recording_id",
    "session_dir",
    "current_cell",
    "fs_hz",
    "smooth",
    "window",
    "poly",
    "show_raw",
    "show_smoothed",
    "stim_time_s",
    "baseline_method",
    "window_s",
    "k",
    "theme",
    "y_scale_mode",
    "y_manual_min",
    "y_manual_max",
    "_y_range_dataset",
    "workspace_label_value",
    "workspace_notes_value",
    "workspace_uncertain_value",
    "prev_cell",
)
_COLLECTION_KEYS: tuple[str, ...] = ("cell_ids", "history")


@dataclass(slots=True)
class Snapshot:
    """Container returned by :func:`load_snapshot`."""

    data: dict[str, Any]
    traces: np.ndarray | None


def _stage_to_payload(value: Stage | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, Stage):
        return value.name
    if isinstance(value, str) and value:
        return value
    return None


def _stage_from_payload(value: str | None) -> Stage | None:
    if not value:
        return None
    try:
        return Stage[value]
    except KeyError:
        return None


def _serialize_history(history: Iterable[Any] | None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not history:
        return result
    for item in history:
        if not isinstance(item, (tuple, list)) or not item:
            continue
        cell_index = int(item[0])
        previous = item[1] if len(item) > 1 else None
        result.append({"cell_index": cell_index, "previous": previous})
    return result


def _deserialize_history(payload: Iterable[Mapping[str, Any]] | None) -> list[tuple[int, Any]]:
    if not payload:
        return []
    restored: list[tuple[int, Any]] = []
    for row in payload:
        if "cell_index" not in row:
            continue
        restored.append((int(row["cell_index"]), row.get("previous")))
    return restored


def _serialize_label_map(label_map: Mapping[Any, Any] | None) -> dict[str, Any]:
    if not label_map:
        return {}
    return {str(int(k)): v for k, v in label_map.items()}


def _deserialize_label_map(payload: Mapping[str, Any] | None) -> dict[int, Any]:
    if not payload:
        return {}
    restored: dict[int, Any] = {}
    for key, value in payload.items():
        try:
            restored[int(key)] = value
        except (TypeError, ValueError):
            continue
    return restored


def resolve_cache_dir(token: str) -> Path:
    """Return the cache directory associated with ``token``."""

    root = CACHE_ROOT / token
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_snapshot(root: Path, state: Mapping[str, Any]) -> None:
    """Persist the relevant subset of ``state`` under ``root``."""

    root.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"version": SNAPSHOT_VERSION, "values": {}}

    for key in _SIMPLE_KEYS:
        if key not in state:
            continue
        value = state.get(key)
        if key == "stage":
            payload["values"][key] = _stage_to_payload(value)
            continue
        if isinstance(value, Path):
            payload["values"][key] = str(value)
            continue
        if isinstance(value, tuple):
            payload["values"][key] = list(value)
            continue
        payload["values"][key] = value

    if "label_map" in state:
        payload["label_map"] = _serialize_label_map(state.get("label_map"))

    if "history" in state:
        payload["history"] = _serialize_history(state.get("history"))

    if "cell_ids" in state:
        cell_ids = state.get("cell_ids")
        if isinstance(cell_ids, (list, tuple)):
            payload["cell_ids"] = [str(x) for x in cell_ids]
        elif isinstance(cell_ids, Sequence) and not isinstance(cell_ids, str):
            payload["cell_ids"] = [str(x) for x in list(cell_ids)]
        else:
            payload["cell_ids"] = None

    snapshot_path = root / SNAPSHOT_FILENAME
    snapshot_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2))

    traces = state.get("traces")
    if isinstance(traces, np.ndarray):
        np.savez_compressed(root / TRACES_FILENAME, traces=traces)


def load_snapshot(root: Path) -> Snapshot | None:
    """Load snapshot data from ``root`` if it exists."""

    snapshot_path = root / SNAPSHOT_FILENAME
    if not snapshot_path.exists():
        return None
    try:
        payload = json.loads(snapshot_path.read_text())
    except json.JSONDecodeError:
        return None

    version = payload.get("version")
    if version != SNAPSHOT_VERSION:
        return None

    values: dict[str, Any] = {}
    raw_values: Mapping[str, Any] = payload.get("values", {})
    for key in _SIMPLE_KEYS:
        if key not in raw_values:
            continue
        value = raw_values[key]
        if key == "stage":
            stage = _stage_from_payload(value)
            if stage is not None:
                values[key] = stage
            continue
        if key == "_y_range_dataset" and isinstance(value, list) and len(value) == 2:
            values[key] = tuple(value)
            continue
        values[key] = value

    values["label_map"] = _deserialize_label_map(payload.get("label_map"))
    values["history"] = _deserialize_history(payload.get("history"))

    cell_ids = payload.get("cell_ids")
    if isinstance(cell_ids, list):
        values["cell_ids"] = [str(x) for x in cell_ids]

    traces_path = root / TRACES_FILENAME
    traces_array: np.ndarray | None = None
    if traces_path.exists():
        try:
            with np.load(traces_path, allow_pickle=False) as npz:
                traces_array = npz.get("traces")
        except Exception:
            traces_array = None

    return Snapshot(data=values, traces=traces_array)


def clear_snapshot(root: Path) -> None:
    """Remove persisted snapshot files under ``root``."""

    if not root.exists():
        return
    for candidate in (root / SNAPSHOT_FILENAME, root / TRACES_FILENAME):
        if candidate.exists():
            candidate.unlink(missing_ok=True)
