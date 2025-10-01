"""Navigation and progress helpers."""
from __future__ import annotations

from typing import Dict

import numpy as np
import streamlit as st

from opcal_mlt.app.plots import make_status_figure
from opcal_mlt.app.state_store import mark_dirty


def render_navigation_and_progress(container, state, total_cells: int, theme: Dict) -> None:
    """Render cell selector, progress indicator, and mini status bar.

    Args:
        container: Streamlit column/container receiving the controls.
        state: Streamlit session state proxy used by the workspace.
        total_cells: Total number of cells in the dataset.
        theme: Theme palette used to style plots and highlights.

    Returns:
        None: Streamlit renders UI elements directly.
    """
    with container:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Cells")
        current_idx = int(getattr(state, "current_cell", 0))
        idx = st.number_input("Cell index", 0, total_cells - 1, current_idx, step=1, key="cell_index")
        if int(idx) != current_idx:
            state.current_cell = int(idx)
            mark_dirty(st.session_state)
        else:
            state.current_cell = int(idx)

        if state.get("prev_cell") != state.current_cell:
            mapping = state.label_map.get(int(state.current_cell)) if isinstance(state.get("label_map"), dict) else None
            st.session_state["workspace_label_value"] = mapping["label"] if mapping else "Oscillatory"
            st.session_state["workspace_notes_value"] = mapping["notes"] if mapping else ""
            st.session_state["workspace_uncertain_value"] = bool(mapping.get("uncertain", False)) if mapping else False
            state.prev_cell = state.current_cell
            mark_dirty(st.session_state)

        progress = int((len(state.label_map) / max(1, total_cells)) * 100)
        st.markdown(
            f'<div class="progress-track"><div class="progress-fill" style="width:{progress}%;"></div></div>',
            unsafe_allow_html=True,
        )

        status = np.zeros(total_cells, dtype=int)
        for cell_index in state.label_map.keys():
            if 0 <= int(cell_index) < total_cells:
                status[int(cell_index)] = 1
        fig_status = make_status_figure(status, theme, height=90)
        st.plotly_chart(fig_status, use_container_width=True)

        st.write(f"Progress: {len(state.label_map)} / {total_cells} labeled")
        st.markdown('</div>', unsafe_allow_html=True)


__all__ = ["render_navigation_and_progress"]
