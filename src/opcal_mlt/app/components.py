"""Reusable UI components for OPCAL‑Labeler screens.

These helpers are *pure UI*: they read/write to Streamlit's session_state
(`s`) and do not return data except where noted. Keeping them here allows the
high‑level screen functions in `screens.py` to stay concise and readable.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict

import numpy as np
import streamlit as st
from opcal_mlt.app.plots import make_status_figure


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
def render_session_diagnostics(s) -> None:
  """Render a small diagnostic caption about the active session directory and
  presence/readability of `labels.csv`. Best‑effort and never raises.
  """
  try:
    if not s.get("session_dir"):
      return
    import pandas as _pd
    diag = f"Session dir: `{s.session_dir}`  \n"
    p = Path(s.session_dir) / "labels.csv"
    if p.exists():
      try:
        _df = _pd.read_csv(p)
        diag += f"<b>labels.csv</b>: exists, {len(_df)} rows"
      except Exception:
        diag += "<b>labels.csv</b>: exists, <span style='color:red;'>could not read</span>"
    else:
      diag += "<b>labels.csv</b>: <span style='color:orange;'>not found</span>"
    st.caption(diag, unsafe_allow_html=True)
  except Exception:
    # Swallow any diagnostics issues silently
    pass


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
def render_sidebar_params(s) -> None:
  """Render sidebar parameters and persist values in session state."""
  with st.sidebar:
    st.markdown("### Labeling parameters")
    s.fs_hz = st.number_input(
      "Sampling rate (Hz)",
      min_value=0.01,
      value=float(s.get("fs_hz", 1.08)),
      step=0.01,
      format="%.2f",
      help="Default is 1.08 Hz (≈0.93 s/sample)",
    )
    # Manage visibility toggles explicitly in `s` to avoid Streamlit key mutation pitfalls
    if "show_raw" not in s:
      s["show_raw"] = True
    if "show_smoothed" not in s:
      s["show_smoothed"] = True
    _show_raw = st.checkbox(
      "Show raw signal",
      value=bool(s.get("show_raw", True)),
      help="Toggle the original unfiltered trace.",
    )
    _show_smoothed = st.checkbox(
      "Show smoothed signal",
      value=bool(s.get("show_smoothed", True)),
      help="Toggle the Savitzky–Golay smoothed trace (when smoothing is enabled).",
    )
    # Persist back to session state if changed
    if bool(s.get("show_raw", True)) != bool(_show_raw):
      s["show_raw"] = bool(_show_raw)
    if bool(s.get("show_smoothed", True)) != bool(_show_smoothed):
      s["show_smoothed"] = bool(_show_smoothed)
    s.smooth = st.checkbox(
      "Apply Savitzky–Golay smoothing",
      value=bool(s.get("smooth", True)),
      help=(
        "Phase-preserving smoothing that reduces noise without shifting peaks. "
        "Turn off to view the raw signal."
      ),
    )
    if s.smooth:
      _win_default = int(s.get("window", 31))
      if _win_default % 2 == 0:
        _win_default += 1
      s.window = st.slider(
        "Smoothing window (samples)",
        5,
        101,
        _win_default,
        step=2,
        help=(
          "Length of the Savitzky–Golay window in samples (must be odd). "
          "Larger windows produce stronger smoothing but can flatten short events. "
          "Typical: 21–61."
        ),
      )
      s.poly = st.slider(
        "Polynomial order",
        1,
        5,
        int(s.get("poly", 3)),
        help=(
          "Order of the fitted polynomial within each window. "
          "Lower values = gentler smoothing; higher values = more flexible curve. "
          "Must be less than the window size. Typical: 2–3."
        ),
      )
    s.baseline_method = st.selectbox(
      "Baseline method",
      ["rolling_median", "percentile (25)"],
      index=0 if str(s.get("baseline_method", "rolling_median")).startswith("rolling") else 1,
    )
    s.window_s = st.slider("Rolling median window (s)", 5, 60, int(s.get("window_s", 20)))
    s.k = st.slider("SD threshold k", 1.0, 6.0, float(s.get("k", 3.0)), step=0.5)
    s.stim_time_s = st.number_input(
      "Stimulus time (s)",
      min_value=0.0,
      value=float(s.get("stim_time_s", 50.0)),
      step=1.0,
      help=("Time when stimulation starts; used for dual-SD thresholds."),
    )

    st.markdown("### ΔF/F scale")
    scale_options = ["auto", "dataset", "manual"]
    _scale_labels = {
      "auto": "Adaptive (per cell)",
      "dataset": "Fix to dataset extremes",
      "manual": "Manual range",
    }
    current_scale = str(s.get("y_scale_mode", "auto"))
    current_scale = current_scale if current_scale in scale_options else "auto"
    scale_mode = st.radio(
      "Mode",
      scale_options,
      index=scale_options.index(current_scale),
      format_func=lambda opt: _scale_labels.get(opt, opt),
      help=(
        "Control how the y-axis range is chosen. Adaptive follows each cell, "
        "while the fixed options keep a consistent scale across all cells."
      ),
    )
    s["y_scale_mode"] = scale_mode

    dataset_range = None
    traces = getattr(s, "traces", None)
    if isinstance(traces, np.ndarray) and traces.size:
      try:
        y_min = float(np.nanmin(traces))
        y_max = float(np.nanmax(traces))
        if np.isfinite(y_min) and np.isfinite(y_max):
          dataset_range = (y_min, y_max)
      except Exception:
        dataset_range = None

    if dataset_range and dataset_range[0] < dataset_range[1]:
      s["_y_range_dataset"] = dataset_range
      st.caption(f"Dataset extremes: {dataset_range[0]:.3f} … {dataset_range[1]:.3f}")
    else:
      if "_y_range_dataset" in s:
        s.pop("_y_range_dataset", None)
      if scale_mode == "dataset":
        st.warning("Unable to compute dataset extremes for fixed scaling.")

    if scale_mode == "manual":
      default_min = float(s.get("y_manual_min", dataset_range[0] if dataset_range else -0.5))
      default_max = float(s.get("y_manual_max", dataset_range[1] if dataset_range else 0.5))
      s["y_manual_min"] = st.number_input(
        "Manual min",
        value=default_min,
        step=0.1,
        format="%.3f",
      )
      s["y_manual_max"] = st.number_input(
        "Manual max",
        value=default_max if default_max > default_min else default_min + 1.0,
        step=0.1,
        format="%.3f",
      )
      if float(s["y_manual_min"]) >= float(s["y_manual_max"]):
        st.error("Manual max must be greater than min.")


# ---------------------------------------------------------------------------
# Navigation + progress strip
# ---------------------------------------------------------------------------
def render_navigation_and_progress(col, s, N: int, theme: Dict) -> None:
  """Left column: session info, cell selector, and progress strip."""
  with col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Cells")
    if s.get("session_dir"):
      st.caption(f"Session: {s.session_dir}")
    idx = st.number_input("Cell index", 0, N - 1, int(s.current_cell), step=1, key="cell_index")
    s.current_cell = int(idx)

    # When navigating, pre-fill widgets with any existing label for this cell
    if s.get("prev_cell") != s.current_cell:
      existing = s.label_map.get(int(s.current_cell))
      st.session_state["label_value"] = existing["label"] if existing else "Oscillatory"
      st.session_state["notes_value"] = existing["notes"] if existing else ""
      st.session_state["uncertain_value"] = bool(existing.get("uncertain", False)) if existing else False
      s.prev_cell = s.current_cell

    # Progress bar + mini status strip
    progress = int((len(s.label_map) / max(1, N)) * 100)
    st.markdown(
      f'<div class="progress-track"><div class="progress-fill" style="width:{progress}%;"></div></div>',
      unsafe_allow_html=True,
    )
    status = np.zeros(N, dtype=int)
    for ci in s.label_map.keys():
      if 0 <= int(ci) < N:
        status[int(ci)] = 1
    fig_status = make_status_figure(status, theme, height=90)
    st.plotly_chart(fig_status, use_container_width=True)

    st.write(f"Progress: {len(s.label_map)} / {N} labeled")
    st.markdown('</div>', unsafe_allow_html=True)
