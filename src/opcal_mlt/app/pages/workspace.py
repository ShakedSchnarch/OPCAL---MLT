"""Streamlit page: Step 3 — labeling workspace."""
from __future__ import annotations

import streamlit as st

from opcal_mlt.app.state import StateAdapter
from opcal_mlt.domain.enums import Stage
from opcal_mlt.services.labeling import LabelingService


def render(*, state: StateAdapter, labeling_service: LabelingService) -> None:
    st.markdown("<div class='step-header'>Step 3 — Labeling workspace</div>", unsafe_allow_html=True)
    st.info("Placeholder page. Implementation will move from screens.py.")
    if st.button("Go to Export"):
        state.set_stage(Stage.EXPORT)
