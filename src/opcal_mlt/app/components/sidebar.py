"""Sidebar parameter controls for the labeling workspace."""
from __future__ import annotations

import numpy as np
import streamlit as st


def render_sidebar_params(state) -> None:
    """Render sidebar parameters and persist values in session state."""
    with st.sidebar:
        st.markdown("### Labeling parameters")
        state.fs_hz = st.number_input(
            "Sampling rate (Hz)",
            min_value=0.01,
            value=float(state.get("fs_hz", 1.08)),
            step=0.01,
            format="%.2f",
            help="Default is 1.08 Hz (≈0.93 s/sample)",
        )

        if "show_raw" not in state:
            state["show_raw"] = True
        if "show_smoothed" not in state:
            state["show_smoothed"] = True
        show_raw = st.checkbox(
            "Show raw signal",
            value=bool(state.get("show_raw", True)),
            help="Toggle the original unfiltered trace.",
        )
        show_smoothed = st.checkbox(
            "Show smoothed signal",
            value=bool(state.get("show_smoothed", True)),
            help="Toggle the Savitzky–Golay smoothed trace (when smoothing is enabled).",
        )
        state["show_raw"] = bool(show_raw)
        state["show_smoothed"] = bool(show_smoothed)

        state.smooth = st.checkbox(
            "Apply Savitzky–Golay smoothing",
            value=bool(state.get("smooth", True)),
            help=(
                "Phase-preserving smoothing that reduces noise without shifting peaks. "
                "Turn off to view the raw signal."
            ),
        )
        if state.smooth:
            win_default = int(state.get("window", 31))
            if win_default % 2 == 0:
                win_default += 1
            state.window = st.slider(
                "Smoothing window (samples)",
                5,
                101,
                win_default,
                step=2,
                help=(
                    "Length of the Savitzky–Golay window in samples (must be odd). "
                    "Larger windows produce stronger smoothing but can flatten short events. "
                    "Typical: 21–61."
                ),
            )
            state.poly = st.slider(
                "Polynomial order",
                1,
                5,
                int(state.get("poly", 3)),
                help=(
                    "Order of the fitted polynomial within each window. "
                    "Lower values = gentler smoothing; higher values = more flexible curve. "
                    "Must be less than the window size. Typical: 2–3."
                ),
            )

        state.baseline_method = st.selectbox(
            "Baseline method",
            ["rolling_median", "percentile (25)"],
            index=0 if str(state.get("baseline_method", "rolling_median")).startswith("rolling") else 1,
        )
        state.window_s = st.slider("Rolling median window (s)", 5, 60, int(state.get("window_s", 20)))
        state.k = st.slider("SD threshold k", 1.0, 6.0, float(state.get("k", 3.0)), step=0.5)
        state.stim_time_s = st.number_input(
            "Stimulus time (s)",
            min_value=0.0,
            value=float(state.get("stim_time_s", 50.0)),
            step=1.0,
            help="Time when stimulation starts; used for dual-SD thresholds.",
        )

        st.markdown("### ΔF/F scale")
        scale_options = ["auto", "dataset", "manual"]
        scale_labels = {
            "auto": "Adaptive (per cell)",
            "dataset": "Fix to dataset extremes",
            "manual": "Manual range",
        }
        current_scale = str(state.get("y_scale_mode", "auto"))
        current_scale = current_scale if current_scale in scale_options else "auto"
        scale_mode = st.radio(
            "Mode",
            scale_options,
            index=scale_options.index(current_scale),
            format_func=lambda opt: scale_labels.get(opt, opt),
            help=(
                "Control how the y-axis range is chosen. Adaptive follows each cell, "
                "while the fixed options keep a consistent scale across all cells."
            ),
        )
        state["y_scale_mode"] = scale_mode

        dataset_range = None
        traces = getattr(state, "traces", None)
        if isinstance(traces, np.ndarray) and traces.size:
            try:
                y_min = float(np.nanmin(traces))
                y_max = float(np.nanmax(traces))
                if np.isfinite(y_min) and np.isfinite(y_max):
                    dataset_range = (y_min, y_max)
            except Exception:
                dataset_range = None

        if dataset_range and dataset_range[0] < dataset_range[1]:
            state["_y_range_dataset"] = dataset_range
            st.caption(f"Dataset extremes: {dataset_range[0]:.3f} … {dataset_range[1]:.3f}")
        else:
            if "_y_range_dataset" in state:
                state.pop("_y_range_dataset", None)
            if scale_mode == "dataset":
                st.warning("Unable to compute dataset extremes for fixed scaling.")

        if scale_mode == "manual":
            default_min = float(state.get("y_manual_min", dataset_range[0] if dataset_range else -0.5))
            default_max = float(state.get("y_manual_max", dataset_range[1] if dataset_range else 0.5))
            state["y_manual_min"] = st.number_input(
                "Manual min",
                value=default_min,
                step=0.1,
                format="%.3f",
            )
            state["y_manual_max"] = st.number_input(
                "Manual max",
                value=default_max if default_max > default_min else default_min + 1.0,
                step=0.1,
                format="%.3f",
            )
            if float(state["y_manual_min"]) >= float(state["y_manual_max"]):
                st.error("Manual max must be greater than min.")


__all__ = ["render_sidebar_params"]
