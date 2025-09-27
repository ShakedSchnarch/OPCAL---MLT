"""Diagnostic helpers for displaying session status."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


def render_session_diagnostics(state) -> None:
    """Display session directory and labels.csv status (best effort)."""
    try:
        session_dir = state.get("session_dir") if hasattr(state, "get") else getattr(state, "session_dir", "")
        if not session_dir:
            return
        diag = f"Session dir: `{session_dir}`  \n"
        labels_path = Path(session_dir) / "labels.csv"
        if labels_path.exists():
            try:
                df = pd.read_csv(labels_path)
                diag += f"<b>labels.csv</b>: exists, {len(df)} rows"
            except Exception:
                diag += "<b>labels.csv</b>: exists, <span style='color:red;'>could not read</span>"
        else:
            diag += "<b>labels.csv</b>: <span style='color:orange;'>not found</span>"
        st.caption(diag, unsafe_allow_html=True)
    except Exception:
        return


__all__ = ["render_session_diagnostics"]
