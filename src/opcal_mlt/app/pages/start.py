"""Streamlit page: Step 1 — start or resume a session."""
from __future__ import annotations

import streamlit as st

from opcal_mlt.app.state import StateAdapter
from opcal_mlt.domain.enums import Stage
from opcal_mlt.services.sessions import SessionService


def render(*, state: StateAdapter, session_service: SessionService) -> None:
    st.markdown("<div class='step-header'>Step 1 — Start session</div>", unsafe_allow_html=True)
    st.info("Placeholder page. Implementation will move from screens.py.")
    if st.button("Go to Upload"):
        state.set_stage(Stage.INGEST)
