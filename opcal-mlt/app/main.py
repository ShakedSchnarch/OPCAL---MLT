import streamlit as st
import numpy as np
import pandas as pd
import json
from pathlib import Path
from core import preprocess as pp
from core import peaks as pk
from core import features as ft
from core.schemas import LabelRecord, PreprocessConfig
from core.io import save_jsonl

st.set_page_config(page_title="OPCAL MLT", layout="wide")

st.title("OPCAL Manual Labeling Tool (MVP)")

left, mid, right = st.columns([1,2,1], gap="large")

# Sidebar for global settings
with st.sidebar:
    st.header("Settings")
    fs_hz = st.number_input("Sampling rate (Hz)", min_value=0.1, value=10.0, step=0.1)
    smooth = st.checkbox("Apply Savitzky–Golay smoothing", value=True)
    window = st.slider("Smooth window", 5, 101, 31, step=2)
    poly = st.slider("Smooth polyorder", 1, 5, 3)
    baseline_method = st.selectbox("Baseline method", ["rolling_median", "percentile (25)"])
    window_s = st.slider("Rolling median window (s)", 5, 60, 20)
    k = st.slider("SD threshold k", 1.0, 6.0, 3.0, step=0.5)
    min_dist = st.slider("Min distance between peaks (s)", 0.5, 5.0, 1.0, step=0.5)
    autosave = st.checkbox("Autosave", value=True)

uploaded = st.file_uploader("Upload traces CSV (rows=time, cols=cells) or NPZ", type=["csv", "npz"])

state = st.session_state
if "labels" not in state:
    state.labels = []
if "current_cell" not in state:
    state.current_cell = 0
if "traces" not in state:
    state.traces = None
    state.cell_ids = []
    state.recording_id = "rec_001"

if uploaded:
    suffix = Path(uploaded.name).suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(uploaded)
        state.traces = df.values  # T x N
        state.cell_ids = list(df.columns.astype(str))
    elif suffix == ".npz":
        npz = np.load(uploaded)
        state.traces = npz["traces"]
        state.cell_ids = [f"cell_{i:03d}" for i in range(state.traces.shape[1])]
        if "recording_id" in npz:
            state.recording_id = str(npz["recording_id"])
    st.success(f"Loaded traces: shape {state.traces.shape}")

if state.traces is not None:
    T, N = state.traces.shape
    with left:
        st.subheader("Cells")
        idx = st.number_input("Cell index", 0, N-1, state.current_cell, step=1)
        state.current_cell = idx
        st.write(f"Progress: {len(state.labels)} / {N} labeled")
        if st.button("Prev"): state.current_cell = max(0, state.current_cell - 1)
        if st.button("Next"): state.current_cell = min(N-1, state.current_cell + 1)

    x = state.traces[:, state.current_cell].astype(float)

    # Preprocess
    x_s = pp.smooth_signal(x, window=window, polyorder=poly) if smooth else x
    if baseline_method.startswith("rolling"):
        base = pp.baseline_rolling_median(x_s, fs_hz, window_s=window_s)
    else:
        base = pp.baseline_percentile(x_s, q=25.0)
    thr = pp.threshold_from_baseline(x_s, base, k=k)
    peaks = pk.detect_peaks(x_s, thr, fs_hz, min_distance_s=min_dist)

    # Plot
    with mid:
        st.subheader(f"Cell {state.cell_ids[state.current_cell]}")
        import plotly.graph_objects as go
        t = np.arange(x.size)/fs_hz
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t, y=x, name="raw", line=dict(width=1)))
        if smooth:
            fig.add_trace(go.Scatter(x=t, y=x_s, name="smoothed", line=dict(width=2)))
        fig.add_trace(go.Scatter(x=t, y=base, name="baseline", line=dict(width=1, dash="dash")))
        fig.add_trace(go.Scatter(x=t, y=thr, name="threshold", fill=None, line=dict(width=1)))
        fig.add_trace(go.Scatter(x=t[peaks], y=x_s[peaks], mode="markers", name="peaks"))
        fig.update_layout(height=500, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Label")
        label = st.radio("Class", ["High-flat", "High-oscillatory", "Oscillatory", "Low-activity"], index=2)
        uncertain = st.checkbox("Uncertain", value=False)
        notes = st.text_area("Notes", placeholder="Optional free text")
        if st.button("Save label (S)"):
            rec = LabelRecord(
                recording_id=state.recording_id,
                cell_id=str(state.cell_ids[state.current_cell]),
                fs_hz=fs_hz,
                label=label, is_uncertain=uncertain, notes=notes,
                preprocess=PreprocessConfig(
                    filter={"type":"savgol","window":int(window),"polyorder":int(poly)} if smooth else {"type":"none"},
                    baseline={"method":"rolling_median","window_s":float(window_s)} if baseline_method.startswith("rolling") else {"method":"percentile","q":25.0},
                    sd_method="MAD",
                    threshold_k=float(k),
                ),
                features=ft.basic_features(x_s, thr, fs_hz, peaks),
                peaks=[int(p) for p in peaks],
            ).model_dump()
            state.labels = [r for r in state.labels if r["cell_id"] != rec["cell_id"]]
            state.labels.append(rec)
            st.success("Saved.")

        if st.button("Export JSONL"):
            out = Path("labels.jsonl")
            save_jsonl(state.labels, out)
            st.success(f"Exported {len(state.labels)} labels to {out.resolve()}")

else:
    st.info("Upload traces to begin.")
