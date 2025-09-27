"""Diagnostic helpers for displaying session status."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


def render_session_diagnostics(state) -> None:
    """Intentionally muted; diagnostics available only in debug builds."""
    return


__all__ = ["render_session_diagnostics"]
