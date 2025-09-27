"""Streamlit page: Step 2 — upload and index traces."""
from __future__ import annotations

import streamlit as st

from opcal_mlt.app.state import StateAdapter
from opcal_mlt.domain.enums import Stage
from opcal_mlt.services.ingest import IngestService


def render(*, state: StateAdapter, ingest_service: IngestService) -> None:
    st.markdown("<div class='step-header'>Step 2 — Upload & indexing</div>", unsafe_allow_html=True)
    st.info("Placeholder page. Implementation will move from screens.py.")
    if st.button("Go to Workspace"):
        state.set_stage(Stage.WORKSPACE)
