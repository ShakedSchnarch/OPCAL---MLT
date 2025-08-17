from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from opcal_mlt.core import preprocess as pp
from opcal_mlt.core import peaks as pk
from opcal_mlt.core import features as ft
from opcal_mlt.app.session_io import append_labels, append_peaks

def render_finish_export(session_state) -> None:
    """Step 4: Export the current session folder as a ZIP."""
    s = session_state
    st.markdown('---')
    st.subheader("Step 4 — Finish & export")
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
            st.success(f"Exported: {zip_path}")
        except Exception as e:
            st.error(f"Export failed: {e}")

def render_labeling_workspace(*, s, theme: dict, logger) -> None:
    """
    Step 3: Main labeling workspace (navigation, plots, labeling & save).
    """
    # Safety: initialize state keys used below
    if "label_map" not in s or not isinstance(s.label_map, dict):
        s.label_map = {}
    if "current_cell" not in s:
        s.current_cell = 0
    if s.get("traces") is None or s.get("cell_ids") is None:
        st.warning("No data loaded yet. Go back to Step 2 (Upload & indexing).")
        return
    # --- Sidebar parameters (visible and editable during labeling) ---
    with st.sidebar:
        st.markdown("### Labeling parameters")
        s.fs_hz = st.number_input("Sampling rate (Hz)", min_value=0.1, value=float(s.get("fs_hz", 10.0)), step=0.1)
        s.smooth = st.checkbox("Apply Savitzky–Golay smoothing", value=bool(s.get("smooth", True)))
        s.window = st.slider("Smooth window", 5, 101, int(s.get("window", 31)), step=2)
        s.poly = st.slider("Smooth polyorder", 1, 5, int(s.get("poly", 3)))
        s.baseline_method = st.selectbox("Baseline method", ["rolling_median", "percentile (25)"], index=0 if str(s.get("baseline_method","rolling_median")).startswith("rolling") else 1)
        s.window_s = st.slider("Rolling median window (s)", 5, 60, int(s.get("window_s", 20)))
        s.k = st.slider("SD threshold k", 1.0, 6.0, float(s.get("k", 3.0)), step=0.5)
        s.stim_time_s = st.number_input("Stimulus time (s)", min_value=0.0, value=float(s.get("stim_time_s", 5.0)), help="Time when stimulation starts; used for dual-SD shading")
    # Use latest state for processing
    fs_hz      = float(s.get("fs_hz", 10.0))
    smooth     = bool(s.get("smooth", True))
    window     = int(s.get("window", 31))
    poly       = int(s.get("poly", 3))
    baseline_method = str(s.get("baseline_method", "rolling_median"))
    window_s   = int(s.get("window_s", 20))
    k          = float(s.get("k", 3.0))
    stim_time_s= float(s.get("stim_time_s", 5.0))

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
        st.markdown(f"### Cell <code>{s.cell_ids[s.current_cell]}</code>", unsafe_allow_html=True)
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
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
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

from opcal_mlt.app.session_io import make_session_dir, write_session_header, write_cell_map, now_utc_iso

def render_start_session(*, s):
    st.header("Step 1 — Start new session")
    st.caption("Choose what you want to do and complete the minimal details. You can move to the next step once Annotator + Save directory are set.")

    # Unified chooser for clarity
    choice = st.radio(
        "Action",
        ("Start / Update settings", "Resume recent session", "Load session from path"),
        horizontal=True,
        key="start_choice",
    )

    # --- Start / Update settings ---
    if choice == "Start / Update settings":
        st.subheader("Start / Update settings")
        st.caption("Set your annotator ID and where sessions are saved. This does not create files yet; they are created when data is uploaded.")
        annotator = st.text_input("Annotator ID", value=s.get("annotator", ""), key="start_annotator")
        save_dir = st.text_input("Save directory", value=s.get("save_dir", str(Path.home() / "OPCAL_LABELS")), key="start_savedir")
        if st.button("Save settings", key="btn_save_start_settings"):
            s.annotator = annotator.strip() or "anon"
            s.save_dir = save_dir.strip() or str(Path.home() / "OPCAL_LABELS")
            st.success("Settings saved — you can proceed to Upload when ready.")
        st.markdown('<div class="hint">Tip: You only need these once per working session. You can change them later.</div>', unsafe_allow_html=True)

    # --- Resume recent session ---
    elif choice == "Resume recent session":
        st.subheader("Resume recent session")
        st.caption("We look under your Save directory for the most recent session folders that contain labels.csv.")
        base_root = st.text_input("Save directory", value=s.get("save_dir", str(Path.home() / "OPCAL_LABELS")), key="resume_savedir")
        recent = []
        base = Path(base_root.strip())
        if base.exists():
            for rec_dir in base.iterdir():
                if rec_dir.is_dir():
                    for sess in rec_dir.iterdir():
                        lab = sess / "labels.csv"
                        if lab.exists():
                            try:
                                mtime = lab.stat().st_mtime
                                recent.append((mtime, sess))
                            except Exception:
                                pass
        recent = sorted(recent, key=lambda x: x[0], reverse=True)[:10]
        if recent:
            options = [f"{p.parent.name} / {p.name}" for _, p in recent]
            sel = st.selectbox("Pick a session", options, index=0, key="resume_pick")
            if st.button("Resume", key="btn_resume_pick"):
                try:
                    p = recent[options.index(sel)][1]
                    s.session_dir = str(p)
                    # Ensure annotator/save_dir present so Next can enable
                    s.annotator = s.get("annotator", "anon")
                    s.save_dir = base_root.strip() or s.get("save_dir", str(Path.home() / "OPCAL_LABELS"))
                    # Load existing state (labels + optional cell_map)
                    labels_csv = p / "labels.csv"
                    cell_map_csv = p / "cell_map.csv"
                    loaded = 0
                    if labels_csv.exists():
                        try:
                            df_lab = pd.read_csv(labels_csv)
                            s.label_map = {int(r.cell_index): {"label": str(r.label), "notes": str(r.notes) if not pd.isna(r.notes) else ""} for r in df_lab.itertuples(index=False)}
                            loaded = len(s.label_map)
                        except Exception as e:
                            st.error(f"Failed to read labels.csv: {e}")
                    if cell_map_csv.exists() and not s.get("cell_ids"):
                        try:
                            df_map = pd.read_csv(cell_map_csv).sort_values("cell_index")
                            s.cell_ids = [str(x) for x in df_map["cell_id"].tolist()]
                        except Exception as e:
                            st.warning(f"Could not read cell_map.csv: {e}")
                    st.success(f"Resumed: {p} (loaded {loaded} labeled cells)")
                except Exception as e:
                    st.error(f"Could not resume: {e}")
        else:
            st.info("No previous sessions found under the selected Save directory.")
        st.markdown('<div class="hint">Tip: Change the Save directory above if your sessions are stored elsewhere.</div>', unsafe_allow_html=True)

    # --- Load session by path ---
    else:
        st.subheader("Load session from path")
        st.caption("Paste a full path to an existing session folder (the folder that contains labels.csv).")
        load_path = st.text_input("Existing session folder path", value=s.get("load_session_dir", ""), key="load_path")
        if st.button("Load session", key="btn_load_session_path"):
            p = Path(load_path.strip())
            if p.exists() and p.is_dir():
                s.session_dir = str(p)
                s.annotator = s.get("annotator", "anon")
                s.save_dir = s.get("save_dir", str(Path.home() / "OPCAL_LABELS"))
                labels_csv = p / "labels.csv"
                cell_map_csv = p / "cell_map.csv"
                loaded = 0
                if labels_csv.exists():
                    try:
                        df_lab = pd.read_csv(labels_csv)
                        s.label_map = {int(r.cell_index): {"label": str(r.label), "notes": str(r.notes) if not pd.isna(r.notes) else ""} for r in df_lab.itertuples(index=False)}
                        loaded = len(s.label_map)
                    except Exception as e:
                        st.error(f"Failed to read labels.csv: {e}")
                if cell_map_csv.exists() and not s.get("cell_ids"):
                    try:
                        df_map = pd.read_csv(cell_map_csv).sort_values("cell_index")
                        s.cell_ids = [str(x) for x in df_map["cell_id"].tolist()]
                    except Exception as e:
                        st.warning(f"Could not read cell_map.csv: {e}")
                st.success(f"Loaded session from: {p} (loaded {loaded} labeled cells)")
            else:
                st.warning("Please enter a valid existing session folder path.")
        st.markdown('<div class="hint">Tip: This is useful when someone shared a session folder with you.</div>', unsafe_allow_html=True)

def render_upload_and_indexing(*, s):
    st.header("Step 2 — Upload & indexing")
    st.caption("Upload a CSV (rows=time, columns=cells) or NPZ (key 'traces', optional 'cell_ids','recording_id'). After upload, choose how to map cell IDs.")

    # --- Upload ---
    uploaded = st.file_uploader(
        "Upload data file (CSV / NPZ)",
        type=["csv", "npz"],
        accept_multiple_files=False,
        key="uploader_step2",
        help="CSV: rows=time, columns=cells. NPZ: required key 'traces' (T×N), optional 'cell_ids', 'recording_id'."
    )

    if not uploaded:
        st.info("Drag & drop a CSV/NPZ file to begin.")
        return

    st.success(f"Selected file: **{uploaded.name}**")
    suffix = Path(uploaded.name).suffix.lower()

    # Reset per-upload state to avoid stale values
    for k in ["traces","cell_ids","recording_id","cell_map_preview_done"]:
        s.pop(k, None)

    # --- Parse file & quick preview ---
    if suffix == ".csv":
        df = pd.read_csv(uploaded)
        s.traces = df.values
        N = s.traces.shape[1]
        # Prepare a small preview of headers and first rows
        st.subheader("Preview")
        st.write(df.head(5))
        # Heuristic: numeric/clean headers?
        col_headers = list(df.columns.astype(str))
        has_useful_headers = all(h.lower() != "unnamed: 0" for h in col_headers)
        default_recording = Path(uploaded.name).stem
        s.recording_id = s.get("recording_id", default_recording)

        # --- Choose mapping mode ---
        st.subheader("Cell ID mapping")
        mode = st.radio(
            "Choose how to assign cell IDs",
            ("Use column headers from CSV", "Import external mapping CSV", "Auto-generate IDs"),
            index=(0 if has_useful_headers else 2),
            key="idx_mode_csv",
            help="You can keep the CSV column names, import a mapping file with columns 'cell_index,cell_id', or generate IDs."
        )

        if mode == "Use column headers from CSV":
            s.cell_ids = col_headers
            st.info("Using column headers as cell IDs.")
        elif mode == "Import external mapping CSV":
            map_file = st.file_uploader(
                "Upload mapping CSV (columns: cell_index, cell_id)", type=["csv"], key="map_csv_uploader"
            )
            if map_file is not None:
                try:
                    df_map = pd.read_csv(map_file)
                    if not {"cell_index","cell_id"}.issubset(set(df_map.columns)):
                        st.error("Mapping CSV must contain columns: 'cell_index' and 'cell_id'.")
                    else:
                        df_map = df_map.sort_values("cell_index")
                        ids = [str(x) for x in df_map["cell_id"].tolist()]
                        if len(ids) != N:
                            st.error(f"Mapping length ({len(ids)}) doesn't match number of columns ({N}).")
                        else:
                            s.cell_ids = ids
                            st.success("Applied external mapping.")
                except Exception as e:
                    st.error(f"Failed to read mapping CSV: {e}")
        else:  # Auto-generate
            colA, colB, colC = st.columns(3)
            prefix = colA.text_input("Auto ID prefix", value=str(s.get("cell_id_prefix","cell_")), key="auto_prefix")
            pad    = colB.number_input("Zero pad", 1, 8, int(s.get("cell_id_pad",5)), step=1, key="auto_pad")
            start  = colC.number_input("Start index", 0, 1_000_000, int(s.get("cell_id_start",0)), step=1, key="auto_start")
            s.cell_id_prefix, s.cell_id_pad, s.cell_id_start = prefix, pad, start
            s.cell_ids = [f"{prefix}{i+start:0{pad}d}" for i in range(N)]
            st.info("Auto-generated IDs applied.")

    else:  # NPZ
        npz = np.load(uploaded, allow_pickle=True)
        s.traces = npz["traces"]
        N = s.traces.shape[1]
        st.subheader("Preview")
        st.write({"npz_keys": list(npz.files)})
        s.recording_id = str(npz["recording_id"]) if "recording_id" in npz else s.get("recording_id", Path(uploaded.name).stem)

        # Present options depending on whether cell_ids exists in NPZ
        has_ids = "cell_ids" in npz
        mode_options = ["Use IDs from NPZ" if has_ids else "Auto-generate IDs", "Import external mapping CSV", "Auto-generate IDs"]
        if not has_ids:
            mode_options = ["Auto-generate IDs", "Import external mapping CSV"]
        mode = st.radio(
            "Choose how to assign cell IDs",
            tuple(mode_options),
            index=0,
            key="idx_mode_npz",
        )

        if mode == "Use IDs from NPZ" and has_ids:
            try:
                arr = npz["cell_ids"]
                s.cell_ids = [str(x) for x in (arr.tolist() if hasattr(arr, "tolist") else list(arr))]
                if len(s.cell_ids) != N:
                    st.warning("Length of 'cell_ids' doesn't match 'traces' columns; switching to auto‑generate.")
                    mode = "Auto-generate IDs"
            except Exception as e:
                st.warning(f"Failed to read NPZ cell_ids ({e}); switching to auto‑generate.")
                mode = "Auto-generate IDs"

        if mode == "Import external mapping CSV":
            map_file = st.file_uploader(
                "Upload mapping CSV (columns: cell_index, cell_id)", type=["csv"], key="map_npz_uploader"
            )
            if map_file is not None:
                try:
                    df_map = pd.read_csv(map_file)
                    if not {"cell_index","cell_id"}.issubset(set(df_map.columns)):
                        st.error("Mapping CSV must contain columns: 'cell_index' and 'cell_id'.")
                    else:
                        df_map = df_map.sort_values("cell_index")
                        ids = [str(x) for x in df_map["cell_id"].tolist()]
                        if len(ids) != N:
                            st.error(f"Mapping length ({len(ids)}) doesn't match number of columns ({N}).")
                        else:
                            s.cell_ids = ids
                            st.success("Applied external mapping.")
                except Exception as e:
                    st.error(f"Failed to read mapping CSV: {e}")

        if (mode == "Auto-generate IDs") or ("cell_ids" not in s):
            prefix = st.text_input("Auto ID prefix", value=str(s.get("cell_id_prefix","cell_")), key="auto_prefix_npz")
            pad    = st.number_input("Zero pad", 1, 8, int(s.get("cell_id_pad",5)), step=1, key="auto_pad_npz")
            start  = st.number_input("Start index", 0, 1_000_000, int(s.get("cell_id_start",0)), step=1, key="auto_start_npz")
            s.cell_id_prefix, s.cell_id_pad, s.cell_id_start = prefix, pad, start
            s.cell_ids = [f"{prefix}{i+start:0{pad}d}" for i in range(N)]
            st.info("Auto-generated IDs applied.")

    # --- Finalize upload ---
    if s.get("traces") is not None and s.get("cell_ids") is not None:
        if len(set(s.cell_ids)) != len(s.cell_ids):
            st.warning("Duplicate cell IDs detected. Consider a different mapping.")
        s.current_cell = 0
        st.success(f"Loaded traces: shape {s.traces.shape}. Mapping ready.")

def render_params(*, s):
    st.header("Step 3 — Labeling parameters")
    s.fs_hz = st.number_input("Sampling rate (Hz)", min_value=0.1, value=float(s.get("fs_hz", 10.0)), step=0.1)
    s.smooth = st.checkbox("Apply Savitzky–Golay smoothing", value=bool(s.get("smooth", True)))
    s.window = st.slider("Smooth window", 5, 101, int(s.get("window", 31)), step=2)
    s.poly = st.slider("Smooth polyorder", 1, 5, int(s.get("poly", 3)))
    s.baseline_method = st.selectbox("Baseline method", ["rolling_median", "percentile (25)"], index=0 if str(s.get("baseline_method","rolling_median")).startswith("rolling") else 1)
    s.window_s = st.slider("Rolling median window (s)", 5, 60, int(s.get("window_s", 20)))
    s.k = st.slider("SD threshold k", 1.0, 6.0, float(s.get("k", 3.0)), step=0.5)
    s.stim_time_s = st.number_input("Stimulus time (s)", min_value=0.0, value=float(s.get("stim_time_s", 5.0)), help="Time when stimulation starts; used for dual-SD shading")
    if st.button("Confirm labeling parameters", key="btn_stage3_confirm"):
        s.params_confirmed = True
        st.success("Parameters confirmed. Proceed to labeling.")