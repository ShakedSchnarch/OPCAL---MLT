

"""Workspace data/processing helpers for the labeling screen.

This module keeps *logic* separate from Streamlit UI code in `screens.py`.
Functions here read/write Streamlit's `session_state` (`s`) only as needed and
return plain Python/numpy objects for plotting and saving.
"""
from __future__ import annotations

import numpy as np
import streamlit as st

from opcal_mlt.core import preprocess as pp
from opcal_mlt.core import peaks as pk


__all__ = [
    "ensure_workspace_state",
    "process_trace_for_cell",
]


# Helper to compute stimulus index, clamped to array bounds
def _stim_index(n: int, fs_hz: float, stim_time_s: float) -> int:
    """Return clamped stimulus index for an array of length n."""
    if n <= 0:
        return 0
    try:
        si = int(round(float(stim_time_s) * float(fs_hz)))
    except Exception:
        si = 0
    return max(0, min(int(si), n - 1))


def ensure_workspace_state(s) -> bool:
    """Ensure mandatory keys exist for the labeling workspace.

    Returns
    -------
    bool
        True when required data (traces & cell_ids) exist. If missing, renders a
        warning and returns False.
    """
    if "label_map" not in s or not isinstance(s.label_map, dict):
        s.label_map = {}
    if "current_cell" not in s:
        s.current_cell = 0
    if "history" not in s or not isinstance(s.get("history"), list):
        s["history"] = []

    if s.get("traces") is None or s.get("cell_ids") is None:
        st.warning("No data loaded yet. Go back to Step 2 (Upload & indexing).")
        return False

    return True


def process_trace_for_cell(s):
    """Compute processed signals and thresholds for the currently selected cell.
    
    Returns a *canonical* data pack that the plotting layer expects, keeping
    UI code simple and consistent.
    Parameters
    ----------
    s : streamlit.runtime.state.SafeSessionState
        Shared session state (`st.session_state`). Must include `traces` and
        `current_cell`.

    Returns
    -------
    dict
        Keys include: ``x, x_s, base, thr, peaks, t, stim_idx, fs_hz, k, smooth,
        show_raw, show_smoothed, sd_const, rect_y0_pre, rect_y1_pre, rect_y0_post,
        rect_y1_post``.
    """
    fs_hz = float(s.get("fs_hz", 1.08))
    smooth = bool(s.get("smooth", True))
    window = int(s.get("window", 31))
    poly = int(s.get("poly", 3))
    baseline_method = str(s.get("baseline_method", "rolling_median"))
    window_s = int(s.get("window_s", 20))
    k = float(s.get("k", 3.0))
    stim_time_s = float(s.get("stim_time_s", 5.0))

    x = s.traces[:, s.current_cell].astype(float)
    x_s = pp.smooth_signal(x, window=window, polyorder=poly) if smooth else x

    # Baseline for display (user choice)
    if baseline_method.startswith("rolling"):
        base_display = pp.baseline_rolling_median(x_s, fs_hz, window_s=window_s)
    else:
        base_display = pp.baseline_percentile(x_s, q=25.0)

    # Pre-stim index in samples
    stim_idx = _stim_index(int(x_s.size), fs_hz, stim_time_s)

    # Robust SD from pre-stim residuals relative to the display baseline
    if stim_idx > 0:
        sd_const = pp.robust_sd_from_mad(x_s[:stim_idx] - base_display[:stim_idx])
    else:
        sd_const = pp.robust_sd_from_mad(x_s - base_display)

    # Threshold vector used for peak detection and features
    base = base_display
    thr = base_display + float(k) * float(sd_const)

    peaks = pk.detect_peaks(x_s, thr, fs_hz, min_distance_s=1.0)
    t = np.arange(x.size) / fs_hz

    # Parameters for floating SD·k rectangles (pre/post), independent of baseline UI
    y0_pre, y1_pre, y0_post, y1_post, _stim_idx_rect = pp.pre_post_sd_rect_params(
        x_s, fs_hz, stim_time_s, k=k, ref="median"
    )

    return {
        "x": x,
        "x_s": x_s,
        "base": base,
        "thr": thr,
        "peaks": peaks,
        "t": t,
        "stim_idx": int(stim_idx),
        "fs_hz": fs_hz,
        "k": k,
        "smooth": smooth,
        "show_raw": bool(s.get("show_raw", True)),
        "show_smoothed": bool(s.get("show_smoothed", True)),
        "sd_const": float(sd_const),
        "rect_y0_pre": float(y0_pre),
        "rect_y1_pre": float(y1_pre),
        "rect_y0_post": float(y0_post),
        "rect_y1_post": float(y1_post),
    }