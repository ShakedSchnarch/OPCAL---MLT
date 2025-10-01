"""
Session State Adapter
====================

Typed wrapper around ``st.session_state`` to avoid stringly-typed access.
Provides strongly-typed helpers for managing Streamlit session state in OPCAL-Labeler.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, MutableMapping, Optional

import numpy as np

from opcal_mlt.domain.enums import LabelClass, Stage
from opcal_mlt.domain.models import LabelMap
from opcal_mlt.app.state_store import mark_dirty


class StateAdapter:
    """
    Expose strongly-typed helpers over Streamlit session state.

    Methods:
        get_stage: Retrieve the current workflow stage.
        set_stage: Set the workflow stage.
        get_label_map: Retrieve the current label map.
        update_label_map: Update the label map for a cell.
        set_label_map_from_states: Set the label map from label states.
        ... (additional session and workspace management methods)
    """

    def __init__(self, backing: MutableMapping[str, Any]) -> None:
        self._state = backing

    # --- Stage management -------------------------------------------------
    def get_stage(self) -> Stage:
        value = self._state.get("stage", Stage.START.value if isinstance(Stage.START.value, int) else 1)
        if isinstance(value, Stage):
            return value
        if isinstance(value, int):
            mapping = {
                1: Stage.START,
                2: Stage.INGEST,
                3: Stage.WORKSPACE,
                4: Stage.EXPORT,
            }
            return mapping.get(value, Stage.START)
        if isinstance(value, str):
            lookup = {
                "start": Stage.START,
                "ingest": Stage.INGEST,
                "workspace": Stage.WORKSPACE,
                "export": Stage.EXPORT,
            }
            return lookup.get(value.lower(), Stage.START)
        return Stage.START

    def set_stage(self, stage: Stage) -> None:
        if self._state.get("stage") != stage:
            self._state["stage"] = stage
            mark_dirty(self._state)
        else:
            self._state["stage"] = stage

    # --- Label map -------------------------------------------------------
    def get_label_map(self) -> LabelMap:
        value = self._state.get("label_map")
        return value if isinstance(value, dict) else {}

    def update_label_map(self, cell_index: int, label: LabelClass, notes: str, uncertain: bool) -> None:
        label_map = self.get_label_map().copy()
        label_map[int(cell_index)] = {
            "label": label.value,
            "notes": notes,
            "uncertain": uncertain,
        }
        self._state["label_map"] = label_map
        mark_dirty(self._state)

    def set_label_map_from_states(self, label_map: LabelMap) -> None:
        self._state["label_map"] = {
            int(cell_index): {
                "label": state.label.value,
                "notes": state.notes,
                "uncertain": state.uncertain,
            }
            for cell_index, state in label_map.items()
        }
        mark_dirty(self._state)

    # --- Session metadata ------------------------------------------------
    def get_annotator(self) -> str:
        return str(self._state.get("annotator", ""))

    def set_annotator(self, annotator: str) -> None:
        if self._state.get("annotator") != annotator:
            mark_dirty(self._state)
        self._state["annotator"] = annotator

    def get_save_dir(self) -> str:
        return str(self._state.get("save_dir", ""))

    def set_save_dir(self, path: str | Path) -> None:
        value = str(path)
        if self._state.get("save_dir") != value:
            mark_dirty(self._state)
        self._state["save_dir"] = value

    def get_session_dir(self) -> str:
        return str(self._state.get("session_dir", ""))

    def set_session_dir(self, path: Optional[str | Path]) -> None:
        if path is None:
            if "session_dir" in self._state:
                self._state.pop("session_dir", None)
                mark_dirty(self._state)
        else:
            value = str(path)
            if self._state.get("session_dir") != value:
                mark_dirty(self._state)
            self._state["session_dir"] = value

    def set_cell_ids(self, cell_ids: list[str]) -> None:
        current = self._state.get("cell_ids")
        new_value = list(cell_ids)
        if current != new_value:
            mark_dirty(self._state)
        self._state["cell_ids"] = new_value

    def get_cell_ids(self) -> list[str] | None:
        return self._state.get("cell_ids")

    # --- Convenience getters ---------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        current = self._state.get(key)
        changed = False
        if current is value:
            changed = False
        elif isinstance(current, np.ndarray) or isinstance(value, np.ndarray):
            if not isinstance(current, np.ndarray) or not isinstance(value, np.ndarray):
                changed = True
            elif current.shape != value.shape or current.dtype != value.dtype:
                changed = True
            else:
                changed = bool(np.any(current != value))
        else:
            changed = current != value
        self._state[key] = value
        if changed:
            mark_dirty(self._state)


__all__ = ["StateAdapter"]
