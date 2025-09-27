"""Streamlit page: Step 4 — finish & export."""
from __future__ import annotations

import streamlit as st

from opcal_mlt.app.state import StateAdapter
from opcal_mlt.domain.enums import Stage
from opcal_mlt.services.export import ExportService


def render(*, state: StateAdapter, export_service: ExportService) -> None:
    st.markdown("<div class='step-header'>Step 4 — Finish & export</div>", unsafe_allow_html=True)
    st.info("Placeholder page. Implementation will move from screens.py.")
    if st.button("Back to start"):
        state.set_stage(Stage.START)
