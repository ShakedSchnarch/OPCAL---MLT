"""Typed wrapper around ``st.session_state`` to avoid stringly-typed access."""
from __future__ import annotations

from typing import Any, MutableMapping

from opcal_mlt.domain.enums import LabelClass, Stage
from opcal_mlt.domain.models import LabelMap


class StateAdapter:
    """Expose strongly-typed helpers over Streamlit session state."""

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

    # --- Convenience getters ---------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value


__all__ = ["StateAdapter"]
