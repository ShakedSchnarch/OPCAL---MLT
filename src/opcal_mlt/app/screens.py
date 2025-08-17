from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from opcal_mlt.core import preprocess as pp
from opcal_mlt.core import peaks as pk
from opcal_mlt.core import features as ft
from opcal_mlt.app.session_io import append_labels, append_peaks

def render_finish_export(session_state) -> None:
    """Step 5: Export the current session folder as a ZIP."""
    s = session_state
    st.markdown('---')
    st.subheader("Step 5 — Finish & export")
    export_col1, export_col2 = st.columns([1, 2])
    with export_col1:
        do_export = st.button("Export session as ZIP", key="btn_export_zip")
    with export_col2:
        st.caption("Creates a ZIP archive of the current session folder (labels.csv, peaks.csv, session.csv, cell_map.csv).")

    if do_export and s.get("session_dir"):
        try:
            import shutil
            sess_path = Path(s.session_dir)
            zip_base = sess_path.parent / f"{sess_path.name}"
            zip_path = shutil.make_archive(str(zip_base), "zip", root_dir=sess_path)
            s.export_done = True
            s.stage = 5
            st.success(f"Exported: {zip_path}")
        except Exception as e:
            st.error(f"Export failed: {e}")

def render_labeling_workspace(*, s, params: dict, theme: dict, logger) -> None:
    """
    Step 4: Main labeling workspace (navigation, plots, labeling & save).
    `params` must contain: fs_hz, smooth, window, poly, baseline_method, window_s, k, stim_time_s
    """
    fs_hz      = float(params["fs_hz"])
    smooth     = bool(params["smooth"])
    window     = int(params["window"])
    poly       = int(params["poly"])
    baseline_method = str(params["baseline_method"])
    window_s   = int(params["window_s"])
    k          = float(params["k"])
    stim_time_s= float(params["stim_time_s"])

    T, N = s.traces.shape
    left, mid, right = st.columns([1, 2, 1], gap="large")

    # -------- Left: navigation & progress --------
    with left:
        st.subheader("Cells")
        if s.get("session_dir"):
            st.caption(f"Session: {s.session_dir}")
        idx = st.number_input("Cell index", 0, N-1, s.current_cell, step=1)
        s.current_cell = idx

        # When switching cells, sync defaults from saved state
        if s.get("prev_cell") != s.current_cell:
            existing = s.label_map.get(int(s.current_cell))
            st.session_state["label_value"] = existing["label"] if existing else "Oscillatory"
            st.session_state["notes_value"] = existing["notes"] if existing else ""
            s.prev_cell = s.current_cell

        # Progress bar + strip
        progress = int((len(s.label_map) / max(1, N)) * 100)
        st.progress(progress/100)
        status = np.zeros(N, dtype=int)
        for ci in s.label_map.keys():
            if 0 <= int(ci) < N:
                status[int(ci)] = 1
        fig_status = go.Figure(go.Bar(
            x=list(range(N)), y=status,
            marker_color=[theme["status_unlabeled"] if v==0 else theme["status_labeled"] for v in status]
        ))
        fig_status.update_yaxes(visible=False)
        fig_status.update_xaxes(title_text="Cells", tickmode="auto", nticks=10)
        fig_status.update_layout(height=120, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig_status, use_container_width=True)

        colJ1, colJ2 = st.columns(2)
        if colJ1.button("Next unlabeled", key="btn_next_unlabeled"):
            unlabeled = [i for i in range(N) if i not in s.label_map]
            if unlabeled:
                s.current_cell = int(unlabeled[0])
                st.rerun()
        if colJ2.button("Prev unlabeled", key="btn_prev_unlabeled"):
            unlabeled = [i for i in range(N) if i not in s.label_map]
            if unlabeled:
                prevs = [u for u in unlabeled if u < s.current_cell]
                s.current_cell = int(prevs[-1]) if prevs else s.current_cell
                st.rerun()

        st.write(f"Progress: {len(s.label_map)} / {N} labeled")
        colA, colB = st.columns(2)
        if colA.button("Prev", key="btn_prev_cell"):
            s.current_cell = max(0, s.current_cell - 1)
            st.rerun()
        if colB.button("Next", key="btn_next_cell"):
            s.current_cell = min(N-1, s.current_cell + 1)
            st.rerun()

    # -------- Middle: processing & plot --------
    x = s.traces[:, s.current_cell].astype(float)
    x_s = pp.smooth_signal(x, window=window, polyorder=poly) if smooth else x
    base = pp.baseline_rolling_median(x_s, fs_hz, window_s=window_s) if baseline_method.startswith("rolling") else pp.baseline_percentile(x_s, q=25.0)
    thr_pre, thr_post, sd_pre, sd_post, stim_idx = pp.dual_sd_thresholds(x_s, base, fs_hz, stim_time_s, k=k)
    thr = np.concatenate([thr_pre, thr_post])
    peaks = pk.detect_peaks(x_s, thr, fs_hz, min_distance_s=1.0)

    with mid:
        st.subheader(f"Cell {s.cell_ids[s.current_cell]}")
        t = np.arange(x.size)/fs_hz
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t, y=x,   name="raw",      line=dict(width=1)))
        if smooth:
            fig.add_trace(go.Scatter(x=t, y=x_s, name="smoothed", line=dict(width=2)))
        fig.add_trace(go.Scatter(x=t, y=base, name="baseline", line=dict(width=1, dash="dash")))
        if stim_idx > 1:
            fig.add_shape(type="rect",
                          x0=t[0], x1=t[stim_idx-1], y0=base[:stim_idx].min(), y1=(thr_pre).max(),
                          fillcolor=theme["shade_pre"], line=dict(width=0), layer="below")
        fig.add_shape(type="rect",
                      x0=t[stim_idx], x1=t[-1], y0=base[stim_idx:].min(), y1=(thr_post).max(),
                      fillcolor=theme["shade_post"], line=dict(width=0), layer="below")
        fig.add_trace(go.Scatter(x=t[:stim_idx],  y=thr_pre,  name=f"thr pre ({k}·SD)",  line=dict(width=1)))
        fig.add_trace(go.Scatter(x=t[stim_idx:], y=thr_post, name=f"thr post ({k}·SD)", line=dict(width=1)))
        fig.add_trace(go.Scatter(x=t[peaks], y=x_s[peaks], mode="markers", name="peaks"))
        st.plotly_chart(fig, use_container_width=True)

    # -------- Right: labeling --------
    with right:
        st.subheader("Label")
        s.setdefault("history", [])
        if st.button("Undo last save", key="btn_undo_save"):
            if s.history:
                ci, prev = s.history.pop()
                if prev is None:
                    s.label_map.pop(ci, None)
                    st.session_state["label_value"] = "Oscillatory"
                    st.session_state["notes_value"] = ""
                else:
                    s.label_map[ci] = prev
                    st.session_state["label_value"] = prev.get("label", "Oscillatory")
                    st.session_state["notes_value"] = prev.get("notes", "")
                logger(f"undo cell_index={ci}")
                st.success("Undid last save for current/previous cell.")

        label = st.radio("Class", ["High-flat","High-oscillatory","Oscillatory","Low-activity","Uncertain","Drifting"], key="label_value")
        notes = st.text_area("Notes", placeholder="Optional free text", key="notes_value")

        if st.button("Save label (CSV)", key="btn_save_label"):
            s.history.append((int(s.current_cell), s.label_map.get(int(s.current_cell))))
            label = st.session_state.get("label_value", "Oscillatory")
            notes = st.session_state.get("notes_value", "")
            feats = ft.basic_features(x_s, thr, fs_hz, peaks)
            saved_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            lab_row = {
                "session_id": Path(s.session_dir).name if s.session_dir else "nosession",
                "recording_id": s.recording_id,
                "annotator_id": s.annotator if s.session_dir else "",
                "saved_utc": saved_utc,
                "cell_index": int(s.current_cell),
                "cell_id": str(s.cell_ids[s.current_cell]),
                "label": label,
                "notes": notes,
                "filter_type": "savgol" if smooth else "none",
                "filter_window": int(window) if smooth else 0,
                "filter_polyorder": int(poly) if smooth else 0,
                "baseline_method": "rolling_median" if baseline_method.startswith("rolling") else "percentile",
                "baseline_window_s_or_q": float(window_s) if baseline_method.startswith("rolling") else 25.0,
                "sd_method": "MAD",
                "threshold_k": float(k),
                "mean": float(feats["mean"]),
                "std": float(feats["std"]),
                "rms": float(feats["rms"]),
                "frac_above_thr": float(feats["frac_above_thr"]),
                "peaks_per_min": float(feats["peaks_per_min"]),
                "version": "mlt-0.2.0",
            }
            if s.session_dir:
                append_labels(Path(s.session_dir), lab_row)
                peak_rows = [{
                    "session_id": Path(s.session_dir).name,
                    "recording_id": s.recording_id,
                    "cell_index": int(s.current_cell),
                    "peak_idx": int(p),
                    "peak_time_s": float(p)/fs_hz,
                    "peak_value": float(x_s[p]),
                } for p in peaks]
                append_peaks(Path(s.session_dir), peak_rows)
                logger(f"save cell_index={int(s.current_cell)} label={label}")
                s.label_map[int(s.current_cell)] = {"label": label, "notes": notes}
                st.success(f"Saved → {Path(s.session_dir) / 'labels.csv'}")
                next_unlab = [i for i in range(N) if i not in s.label_map and i > s.current_cell]
                if next_unlab:
                    s.current_cell = int(next_unlab[0])
                    st.rerun()
            else:
                st.warning("Start a session (Annotator & Save dir) to save CSVs.")