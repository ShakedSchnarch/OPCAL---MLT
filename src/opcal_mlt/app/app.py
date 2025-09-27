"""Future Streamlit entry point orchestrating routing and services."""
from __future__ import annotations

import streamlit as st

from opcal_mlt.app.routing import Router
from opcal_mlt.app.state import StateAdapter
from opcal_mlt.domain.enums import Stage
from opcal_mlt.services.export import ExportService
from opcal_mlt.services.ingest import IngestService
from opcal_mlt.services.labeling import LabelingService
from opcal_mlt.services.sessions import SessionService

from opcal_mlt.app.pages import export as page_export
from opcal_mlt.app.pages import ingest as page_ingest
from opcal_mlt.app.pages import start as page_start
from opcal_mlt.app.pages import workspace as page_workspace


def run() -> None:
    """Entry point resembling Streamlit's ``main.py``."""
    state = StateAdapter(st.session_state)
    router = Router()
    services = {
        "sessions": SessionService(),
        "ingest": IngestService(),
        "labeling": LabelingService(),
        "export": ExportService(),
    }
    router.register(Stage.START, lambda: page_start.render(state=state, session_service=services["sessions"]))
    router.register(Stage.INGEST, lambda: page_ingest.render(state=state, ingest_service=services["ingest"]))
    router.register(Stage.WORKSPACE, lambda: page_workspace.render(state=state, labeling_service=services["labeling"]))
    router.register(
        Stage.EXPORT,
        lambda: page_export.render(
            state=state,
            session_service=services["sessions"],
            export_service=services["export"],
        ),
    )
    router.dispatch(state.get_stage())


if __name__ == "__main__":
    run()
