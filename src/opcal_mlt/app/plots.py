"""Plot builders for OPCAL‑Labeler.

This module centralizes Plotly figure creation so `screens.py` stays focused on
UI control flow. Functions here are side‑effect free: they build and return
figures without touching Streamlit state.
"""
from __future__ import annotations
from typing import Dict

import numpy as np
import plotly.graph_objects as go

from opcal_mlt.app.ui import apply_plotly_theme


def make_workspace_figure(
    data: Dict,
    theme: Dict,
    *,
    dff_fixed: float = 0.2,
    height: int = 480,
) -> go.Figure:
    """Build the main workspace figure.

    Parameters
    ----------
    data : dict
        Dictionary produced by the cell processing function, expected keys:
        - "t", "x", "x_s", "base", "thr", "peaks" (np.ndarray/arrays)
        - "smooth", "show_raw", "show_smoothed" (bool)
        - "stim_idx" (int)
        - rectangle params: "rect_y0_pre", "rect_y1_pre", "rect_y0_post", "rect_y1_post"
    theme : dict
        Palette with keys used for shading/lines.
    dff_fixed : float, default 0.2
        Horizontal ΔF/F reference line value.
    height : int, default 480
        Figure height in pixels.

    Notes
    -----
    This builder is defensive: shapes/peaks are skipped gracefully when inputs are missing.
    """
    fig = go.Figure()

    # Raw / smoothed traces
    if data.get("show_raw", True):
        fig.add_trace(go.Scatter(x=data["t"], y=data["x"], name="raw", line=dict(width=1)))
    if data.get("smooth", True) and data.get("show_smoothed", True):
        fig.add_trace(go.Scatter(x=data["t"], y=data["x_s"], name="smoothed", line=dict(width=2)))

    # Baseline (dashed)
    fig.add_trace(go.Scatter(x=data["t"], y=data["base"], name="baseline", line=dict(width=1, dash="dash")))

    # Fixed ΔF/F reference line
    fig.add_trace(
        go.Scatter(
            x=data["t"],
            y=[float(dff_fixed)] * len(data["t"]),
            name="ΔF/F = 0.2",
            line=dict(width=1, dash="dot"),
        )
    )

    # Floating SD·k rectangles (pre/post)
    si = int(data.get("stim_idx", 0))
    t = data["t"]

    # Guards for short traces and index clamping
    if t is None or len(t) == 0:
        apply_plotly_theme(fig, theme)
        return fig
    si = max(0, min(int(si), len(t) - 1))

    if all(k in data for k in ("rect_y0_pre", "rect_y1_pre", "rect_y0_post", "rect_y1_post")):
        y0_pre = float(data["rect_y0_pre"]); y1_pre = float(data["rect_y1_pre"]) 
        y0_post = float(data["rect_y0_post"]); y1_post = float(data["rect_y1_post"]) 
        if y1_pre > y0_pre and len(t) >= 2 and si >= 0:
            fig.add_shape(
                type="rect", xref="x", yref="y",
                x0=float(t[0]), x1=float(t[si]), y0=y0_pre, y1=y1_pre,
                line=dict(width=0), fillcolor=theme.get("shade_pre", "rgba(99,102,241,0.10)"),
                opacity=1.0, layer="below",
            )
        if y1_post > y0_post and len(t) >= 2 and si < len(t):
            fig.add_shape(
                type="rect", xref="x", yref="y",
                x0=float(t[si]), x1=float(t[-1]), y0=y0_post, y1=y1_post,
                line=dict(width=0), fillcolor=theme.get("shade_post", "rgba(16,185,129,0.10)"),
                opacity=1.0, layer="below",
            )

    # Peaks
    peaks = data.get("peaks")
    if peaks is not None:
        try:
            peaks = np.asarray(peaks, dtype=int)
            peaks = peaks[(peaks >= 0) & (peaks < len(t))]
        except Exception:
            peaks = np.array([], dtype=int)
    if peaks is not None and len(peaks) > 0:
        fig.add_trace(
            go.Scatter(
                x=t[peaks],
                y=data["x_s"][peaks],
                mode="markers",
                name="peaks",
            )
        )

    fig.update_layout(height=height, margin=dict(l=10, r=10, t=32, b=10))
    apply_plotly_theme(fig, theme)
    return fig


def make_status_figure(status: np.ndarray, theme: Dict, *, height: int = 90) -> go.Figure:
    """Build the mini status strip used under the cell selector."""
    colors = [theme.get("status_unlabeled"), theme.get("status_labeled")]
    fig = go.Figure(
        go.Bar(
            x=list(range(len(status))),
            y=status,
            marker_color=[colors[status[i]] for i in range(len(status))],
        )
    )
    fig.update_yaxes(visible=False)
    fig.update_xaxes(title_text="Cells", tickmode="auto", nticks=10)
    fig.update_layout(height=height, margin=dict(l=4, r=4, t=4, b=4))
    apply_plotly_theme(fig, theme)
    return fig