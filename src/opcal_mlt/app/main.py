"""
OPCAL‑Labeler — a local Streamlit app for manual labeling of calcium imaging traces.
Features:
  • Dual-SD threshold visualization (pre/post stimulus)
  • Per-cell labeling with progress tracking and session resume
  • CSV-based session outputs (session.csv, labels.csv, peaks.csv, cell_map.csv)
This file focuses on UI orchestration; signal processing lives in `core/`.
"""
import streamlit as st
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from opcal_mlt.core import preprocess as pp
from opcal_mlt.core import peaks as pk
from opcal_mlt.core import features as ft
from opcal_mlt.app.ui import inject_theme_css, render_stepper_and_tips
try:
    # New name (preferred)
    from opcal_mlt.core.schemas import PreprocessConfig
except ImportError:  # Backward-compatibility with older versions
    from opcal_mlt.core.schemas import PreprocessSettings as PreprocessConfig
from opcal_mlt.core.io import save_jsonl
from opcal_mlt.app.session_io import make_session_dir, write_session_header, write_cell_map, append_labels, append_peaks, now_utc_iso
s = st.session_state
s.setdefault("stage", 1)               # 1=Start, 2=Upload, 3=Params, 4=Label, 5=Finish
s.setdefault("params_confirmed", False)
s.setdefault("export_done", False)


# --- App metadata & constants ---
APP_NAME = "OPCAL‑Labeler"
APP_VERSION = "0.3.1"
LABELS = [
    "High-flat",
    "High-oscillatory",
    "Oscillatory",
    "Low-activity",
    "Uncertain",
    "Drifting",
]

# ---- Theming (light/dark) ----
THEMES = {
    "Light": {
        "bg": "#f7f9fb",
        "panel": "#ffffff",
        "border": "#e6edf3",
        "text": "#111827",
        "muted": "#6b7280",
        "accent": "#2563eb",
        "ok": "#2ca02c",
        "warn": "#d97706",
        "err": "#dc2626",
        "shade_pre": "rgba(0,160,0,0.14)",
        "shade_post": "rgba(200,0,0,0.14)",
        "status_unlabeled": "#d1d5db",
        "status_labeled": "#2ca02c",
        "plotly_tpl": "plotly_white",
    },
    "Dark": {
        "bg": "#0f172a",
        "panel": "#0b1220",
        "border": "#1f2a44",
        "text": "#e5e7eb",
        "muted": "#9ca3af",
        "accent": "#60a5fa",
        "ok": "#34d399",
        "warn": "#f59e0b",
        "err": "#f87171",
        "shade_pre": "rgba(16,185,129,0.16)",
        "shade_post": "rgba(239,68,68,0.16)",
        "status_unlabeled": "#334155",
        "status_labeled": "#34d399",
        "plotly_tpl": "plotly_dark",
    },
}

def _log(msg: str):
    """Append a timestamped message to the current session's log file (if a session is active)."""
    try:
        s = st.session_state
        if s.get("session_dir"):
            p = Path(s.session_dir) / "session.log"
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8") as f:
                ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
                f.write(f"{ts} | {msg}\n")
    except Exception:
        pass

# Resolve page icon (favicon): prefer assets/favicon.png; otherwise derive from logo.png (if PIL is available)
assets_dir = Path(__file__).parent / "assets"
_favicon_path = assets_dir / "favicon.png"
_logo_for_icon = assets_dir / "logo.png"
_page_icon_obj = None
try:
    from PIL import Image as _Image  # optional dependency
    if (not _favicon_path.exists()) and _logo_for_icon.exists():
        _page_icon_obj = _Image.open(_logo_for_icon).convert("RGBA")
        _page_icon_obj = _page_icon_obj.resize((64, 64))
except Exception:
    _page_icon_obj = None


st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
    page_icon=(
        _page_icon_obj
        if _page_icon_obj is not None
        else (str(_favicon_path) if _favicon_path.exists() else None)
    ),
)

# Professional header and theming

st.markdown(
    f"""
    <div class="app-title">
      <div class="app-title-main">{APP_NAME}</div>
      <div class="app-title-sub">Manual labeling tool • v{APP_VERSION}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

inject_theme_css(THEMES[st.session_state.get("theme", "Light")])

# --- Top stepper (5 stages) ---
# Infer stage if user already performed actions (guards against refresh)
if not s.get("session_dir"):
    s.stage = 1
elif s.get("traces") is None:
    s.stage = max(s.stage, 2)
elif not s.get("params_confirmed"):
    s.stage = max(s.stage, 3)
elif not s.get("export_done"):
    s.stage = max(s.stage, 4)
else:
    s.stage = 5

labels_steps = ["Start new session", "Upload & indexing", "Labeling parameters", "Label files", "Finish & export"]
current_step = int(s.stage)
render_stepper_and_tips(current_step)

# Navigation controls
req_ready = {
    1: bool(s.get("session_dir")),
    2: bool(s.get("traces") is not None),
    3: bool(s.get("params_confirmed")),
    4: True,
    5: False,
}
nav_left, nav_right = st.columns([1,1])
if nav_left.button("Back", disabled=(current_step <= 1)):
    s.stage = max(1, current_step - 1)
    st.rerun()
if nav_right.button("Next", disabled=not req_ready.get(current_step, False)):
    s.stage = min(5, current_step + 1)
    st.rerun()

# --- Sidebar: session controls, loading, and configuration ---
with st.sidebar:
    st.header("Step 1 — Start new session")
    st.caption("Set annotator, default save folder. Click Start / Update Session to create a session folder.")
    start_session = st.button("Start / Update Session")
    if start_session:
        s.annotator = annotator.strip() or "anon"
        s.save_dir = save_dir.strip() or str(Path.home() / "OPCAL_LABELS")
    s = st.session_state
    st.session_state["theme"] = "Light"
    annotator = st.text_input("Annotator ID", value=st.session_state.get("annotator", ""))
    save_dir = st.text_input("Save directory", value=st.session_state.get("save_dir", str(Path.home() / "OPCAL_LABELS")))
    # Resume last session (auto-detect the newest labels.csv under save_dir)
    if st.button("Resume last session"):
        base = Path(save_dir.strip() or str(Path.home() / "OPCAL_LABELS"))
        candidates = []
        if base.exists():
            for rec_dir in base.iterdir():
                if rec_dir.is_dir():
                    for sess in rec_dir.iterdir():
                        if (sess / "labels.csv").exists():
                            try:
                                mtime = (sess / "labels.csv").stat().st_mtime
                                candidates.append((mtime, sess))
                            except Exception:
                                pass
        if candidates:
            candidates.sort(reverse=True)
            p = candidates[0][1]
            s.session_dir = str(p)
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
            if cell_map_csv.exists() and not s.cell_ids:
                try:
                    df_map = pd.read_csv(cell_map_csv)
                    df_map = df_map.sort_values("cell_index")
                    s.cell_ids = [str(x) for x in df_map["cell_id"].tolist()]
                except Exception as e:
                    st.warning(f"Could not read cell_map.csv: {e}")
            st.success(f"Resumed last session: {p} ({loaded} labeled cells)")
            # Try to show session header
            sess_hdr = p / "session.csv"
            if sess_hdr.exists():
                try:
                    df_hdr = pd.read_csv(sess_hdr)
                    if len(df_hdr) > 0:
                        st.caption("Current session header:")
                        st.dataframe(df_hdr.head(1), use_container_width=True)
                except Exception:
                    pass
        else:
            st.warning("No previous sessions found under the selected Save directory.")
    st.markdown(":blue[Load previous session]")
    load_session_dir = st.text_input("Existing session dir (optional)", value="", help="Path to an existing session folder containing labels.csv")
    if st.button("Load session"):
        p = Path(load_session_dir.strip())
        if p.exists() and p.is_dir():
            s.session_dir = str(p)
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
            if cell_map_csv.exists() and not s.cell_ids:
                try:
                    df_map = pd.read_csv(cell_map_csv)
                    # ensure correct ordering by index
                    df_map = df_map.sort_values("cell_index")
                    s.cell_ids = [str(x) for x in df_map["cell_id"].tolist()]
                except Exception as e:
                    st.warning(f"Could not read cell_map.csv: {e}")
            st.success(f"Loaded session from {p} ({loaded} labeled cells)")
            # Show session header if exists
            sess_hdr = p / "session.csv"
            if sess_hdr.exists():
                try:
                    df_hdr = pd.read_csv(sess_hdr)
                    if len(df_hdr) > 0:
                        st.caption("Loaded session header:")
                        st.dataframe(df_hdr.head(1), use_container_width=True)
                except Exception:
                    pass
        else:
            st.warning("Enter a valid existing session directory path.")
    st.markdown('---')
    st.header("Cell IDs")
    # Persist config in session
    s.setdefault("cell_ids_mode", "file")
    s.setdefault("cell_id_prefix", "cell_")
    s.setdefault("cell_id_pad", 5)
    s.setdefault("cell_id_start", 0)

    mode_label = {"file": "From file (columns / embedded)", "auto": "Auto-generate"}
    cell_id_mode = st.radio(
        "Cell ID source",
        [mode_label["file"], mode_label["auto"]],
        index=0 if s.get("cell_ids_mode") == "file" else 1,
        help="Use cell IDs from the uploaded file (CSV columns or NPZ 'cell_ids'), or generate IDs."
    )
    s.cell_ids_mode = "file" if cell_id_mode == mode_label["file"] else "auto"

    col_ids1, col_ids2, col_ids3 = st.columns(3)
    s.cell_id_prefix = col_ids1.text_input("Auto ID prefix", value=s.get("cell_id_prefix", "cell_"))
    s.cell_id_pad = col_ids2.number_input("Zero pad", min_value=1, max_value=8, value=int(s.get("cell_id_pad", 5)), step=1)
    s.cell_id_start = col_ids3.number_input("Start index", min_value=0, max_value=1000000, value=int(s.get("cell_id_start", 0)), step=1)
    # Add checkbox for preferring existing cell_map
    prefer_existing = st.checkbox(
        "Use existing cell_map if found",
        value=True,
        help="When starting a new session for the same recording_id, reuse the latest cell_map.csv found under the Save directory."
    )

    st.markdown('---')
    st.header("Signal settings")
    fs_hz = st.number_input("Sampling rate (Hz)", min_value=0.1, value=10.0, step=0.1)
    smooth = st.checkbox("Apply Savitzky–Golay smoothing", value=True)
    window = st.slider("Smooth window", 5, 101, 31, step=2)
    poly = st.slider("Smooth polyorder", 1, 5, 3)
    baseline_method = st.selectbox("Baseline method", ["rolling_median", "percentile (25)"])
    window_s = st.slider("Rolling median window (s)", 5, 60, 20)
    k = st.slider("SD threshold k", 1.0, 6.0, 3.0, step=0.5)
    stim_time_s = st.number_input("Stimulus time (s)", min_value=0.0, value=5.0, help="Time when stimulation starts; used for dual-SD shading")
    st.markdown('---')
    if st.button("Confirm labeling parameters"):
        s.params_confirmed = True
        s.stage = max(s.stage, 4)
        st.success("Parameters confirmed for this session.")

    # --- About & Help expander ---
    with st.expander("About & Help"):
        st.markdown("**OPCAL‑Labeler** is a local tool for manual labeling of calcium imaging traces. Data never leaves your machine.")
        st.markdown("**Labels:** High‑flat · High‑oscillatory · Oscillatory · Low‑activity · Uncertain · Drifting")
        st.markdown("**Thresholds:** Dual SD envelopes – pre‑stimulus (green) and post‑stimulus (red). Adjust *k* and stimulus time in the sidebar.")
        img = Path(__file__).parent / "assets" / "sd_threshold.png"
        if img.exists():
            st.image(str(img), caption="Standard deviation thresholds (illustration)")
        st.markdown(f"<span class='small-muted'>Version {APP_VERSION}. For citation, include the tool name and version.</span>", unsafe_allow_html=True)


#
# --- Data loading (CSV / NPZ) ---
st.subheader("Step 2 — Upload & indexing")
st.caption("Supported formats: CSV (rows=time, columns=cells) and NPZ (keys: traces, optional: cell_ids, recording_id).")
uploaded = st.file_uploader(
    "Upload data file (CSV / NPZ)",
    type=["csv", "npz"],
    accept_multiple_files=False,
    help="CSV: rows=time, columns=cells. NPZ: required key 'traces' (T×N), optional 'cell_ids', 'recording_id'. You can also drag & drop a file here."
)
if not uploaded:
    st.info("Drag & drop a CSV/NPZ file here. After upload, set options in the left sidebar and press **Start / Update Session**.")
else:
    st.caption(f"Selected file: **{uploaded.name}**")

s = st.session_state
s.setdefault("labels", [])
s.setdefault("current_cell", 0)
s.setdefault("traces", None)
s.setdefault("cell_ids", [])
s.setdefault("recording_id", "rec_001")
s.setdefault("session_dir", None)
s.setdefault("annotator", annotator)
s.setdefault("save_dir", save_dir)
s.setdefault("label_map", {})
s.setdefault("prev_cell", None)

if uploaded:
    suffix = Path(uploaded.name).suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(uploaded)
        s.traces = df.values
        Ncols = s.traces.shape[1]
        if s.get("cell_ids_mode") == "file" and all(str(c).lower() != "unnamed: 0" for c in df.columns):
            s.cell_ids = list(df.columns.astype(str))
        else:
            pad = int(s.get("cell_id_pad", 5))
            start = int(s.get("cell_id_start", 0))
            prefix = str(s.get("cell_id_prefix", "cell_"))
            s.cell_ids = [f"{prefix}{i+start:0{pad}d}" for i in range(Ncols)]
    else:
        npz = np.load(uploaded, allow_pickle=True)
        s.traces = npz["traces"]
        Ncols = s.traces.shape[1]
        if s.get("cell_ids_mode") == "file" and "cell_ids" in npz:
            try:
                arr = npz["cell_ids"]
                s.cell_ids = [str(x) for x in (arr.tolist() if hasattr(arr, "tolist") else list(arr))]
            except Exception:
                pad = int(s.get("cell_id_pad", 5))
                start = int(s.get("cell_id_start", 0))
                prefix = str(s.get("cell_id_prefix", "cell_"))
                s.cell_ids = [f"{prefix}{i+start:0{pad}d}" for i in range(Ncols)]
        else:
            pad = int(s.get("cell_id_pad", 5))
            start = int(s.get("cell_id_start", 0))
            prefix = str(s.get("cell_id_prefix", "cell_"))
            s.cell_ids = [f"{prefix}{i+start:0{pad}d}" for i in range(Ncols)]
        if "recording_id" in npz:
            s.recording_id = str(npz["recording_id"]) 
    s.current_cell = 0
    s.stage = max(s.stage, 3)
    # Warn on duplicate IDs
    if len(set(s.cell_ids)) != len(s.cell_ids):
        st.warning("Duplicate cell IDs detected. Consider switching to Auto-generate or adjusting prefix/padding/start.")
    st.success(f"Loaded traces: shape {s.traces.shape}")

if start_session and s.traces is not None:
    s.annotator = annotator.strip() or "anon"
    s.save_dir = save_dir.strip() or str(Path.home() / "OPCAL_LABELS")
    base_dir = Path(s.save_dir)
    s.session_dir = make_session_dir(base_dir, s.recording_id, s.annotator)
    write_session_header(
        s.session_dir,
        {
            "session_id": Path(s.session_dir).name,
            "recording_id": s.recording_id,
            "annotator_id": s.annotator,
            "fs_hz": fs_hz,
            "started_utc": now_utc_iso(),
            "app_version": APP_VERSION,
            "source_path": uploaded.name if uploaded else "",
            "source_sha256": "",
        },
    )
    Ncols = s.traces.shape[1]
    s.current_cell = 0  # reset navigation at session start
    s.stage = max(s.stage, 3)
    imported_map = False
    # Try to reuse a previous cell_map for this recording_id
    try:
        if prefer_existing:
            rec_dir = Path(s.save_dir) / s.recording_id
            if rec_dir.exists():
                candidates = []
                for sess_dir in rec_dir.iterdir():
                    if (sess_dir / "cell_map.csv").exists():
                        try:
                            mtime = (sess_dir / "cell_map.csv").stat().st_mtime
                            candidates.append((mtime, sess_dir))
                        except Exception:
                            pass
                if candidates:
                    candidates.sort(reverse=True)
                    last_map_dir = candidates[0][1]
                    import pandas as _pd
                    df_map = _pd.read_csv(last_map_dir / "cell_map.csv")
                    df_map = df_map.sort_values("cell_index")
                    ids_from_map = [str(x) for x in df_map["cell_id"].tolist()]
                    if len(ids_from_map) == Ncols:
                        s.cell_ids = ids_from_map
                        imported_map = True
                        st.info(f"Reused cell_map from: {last_map_dir}")
                    else:
                        st.warning("Existing cell_map length does not match current data; generating IDs.")
    except Exception as e:
        st.warning(f"Could not reuse previous cell_map: {e}")

    # Fallbacks if we still have no IDs
    if not s.cell_ids or len(s.cell_ids) != Ncols:
        if s.get("cell_ids_mode") == "file":
            # If mode=file but no valid IDs available, generate
            pad = int(s.get("cell_id_pad", 5))
            start = int(s.get("cell_id_start", 0))
            prefix = str(s.get("cell_id_prefix", "cell_"))
            s.cell_ids = [f"{prefix}{i+start:0{pad}d}" for i in range(Ncols)]
        else:
            pad = int(s.get("cell_id_pad", 5))
            start = int(s.get("cell_id_start", 0))
            prefix = str(s.get("cell_id_prefix", "cell_"))
            s.cell_ids = [f"{prefix}{i+start:0{pad}d}" for i in range(Ncols)]

    write_cell_map(
        s.session_dir, [{"cell_index": i, "cell_id": s.cell_ids[i]} for i in range(len(s.cell_ids))]
    )
    st.success(f"Session folder: {s.session_dir}")
    _log(f"session_start annotator={s.annotator} recording_id={s.recording_id}")
    # Preview the newly created session header
    try:
        import pandas as _pd
        _hdr = _pd.read_csv(Path(s.session_dir) / "session.csv")
        if len(_hdr) > 0:
            st.caption("New session header:")
            st.dataframe(_hdr.head(1), use_container_width=True)
    except Exception:
        pass

# If user started a session before uploading data, create a session folder shell (no traces yet)
if start_session and s.traces is None:
    s.annotator = annotator.strip() or s.get("annotator", "anon")
    s.save_dir = save_dir.strip() or s.get("save_dir", str(Path.home() / "OPCAL_LABELS"))
    base_dir = Path(s.save_dir)
    rec_id = s.get("recording_id", f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    s.session_dir = make_session_dir(base_dir, rec_id, s.annotator)
    write_session_header(
        s.session_dir,
        {
            "session_id": Path(s.session_dir).name,
            "recording_id": rec_id,
            "annotator_id": s.annotator,
            "fs_hz": 0.0,
            "started_utc": now_utc_iso(),
            "app_version": APP_VERSION,
            "source_path": "",
            "source_sha256": "",
        },
    )
    st.success(f"Session folder: {s.session_dir}")
    _log(f"session_start annotator={s.annotator} recording_id={rec_id}")
    s.stage = max(s.stage, 2)

# --- Main workspace: navigation, visualization, labeling ---
if s.stage >= 4 and s.traces is not None and s.get("session_dir"):
    T, N = s.traces.shape
    left, mid, right = st.columns([1,2,1], gap="large")
    with left:
        st.subheader("Cells")
        if s.get("session_dir"):
            st.caption(f"Session: {s.session_dir}")
        idx = st.number_input("Cell index", 0, N-1, s.current_cell, step=1)
        s.current_cell = idx
        # Update widget defaults when switching cells
        if s.get("prev_cell") != s.current_cell:
            existing = s.label_map.get(int(s.current_cell))
            st.session_state["label_value"] = existing["label"] if existing else "Oscillatory"
            st.session_state["notes_value"] = existing["notes"] if existing else ""
            s.prev_cell = s.current_cell

        # Progress bar
        progress = int((len(s.label_map) / max(1, N)) * 100)
        st.progress(progress/100)
        # Status strip of labeled/unlabeled cells
        import plotly.graph_objects as go
        status = np.zeros(N, dtype=int)
        for ci in s.label_map.keys():
            if 0 <= int(ci) < N:
                status[int(ci)] = 1
        fig_status = go.Figure(go.Bar(x=list(range(N)), y=status, marker_color=[THEMES[st.session_state.get("theme","Light")]["status_unlabeled"] if v==0 else THEMES[st.session_state.get("theme","Light")]["status_labeled"] for v in status]))
        fig_status.update_yaxes(visible=False)
        fig_status.update_xaxes(title_text="Cells", tickmode="auto", nticks=10)
        fig_status.update_layout(height=120, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig_status, use_container_width=True)
        # Jump helpers
        colJ1, colJ2 = st.columns(2)
        if colJ1.button("Next unlabeled"):
            unlabeled = [i for i in range(N) if i not in s.label_map]
            if unlabeled:
                s.current_cell = int(unlabeled[0])
                st.rerun()
        if colJ2.button("Prev unlabeled"):
            unlabeled = [i for i in range(N) if i not in s.label_map]
            if unlabeled:
                prevs = [u for u in unlabeled if u < s.current_cell]
                s.current_cell = int(prevs[-1]) if prevs else s.current_cell
                st.rerun()

        st.write(f"Progress: {len(s.label_map)} / {N} labeled")
        colA, colB = st.columns(2)
        if colA.button("Prev"):
            s.current_cell = max(0, s.current_cell - 1)
            st.rerun()
        if colB.button("Next"):
            s.current_cell = min(N-1, s.current_cell + 1)
            st.rerun()

    x = s.traces[:, s.current_cell].astype(float)
    x_s = pp.smooth_signal(x, window=window, polyorder=poly) if smooth else x
    base = pp.baseline_rolling_median(x_s, fs_hz, window_s=window_s) if baseline_method.startswith("rolling") else pp.baseline_percentile(x_s, q=25.0)

    thr_pre, thr_post, sd_pre, sd_post, stim_idx = pp.dual_sd_thresholds(x_s, base, fs_hz, stim_time_s, k=k)
    thr = np.concatenate([thr_pre, thr_post])
    peaks = pk.detect_peaks(x_s, thr, fs_hz, min_distance_s=1.0)

    with mid:
        st.subheader(f"Cell {s.cell_ids[s.current_cell]}")
        import plotly.graph_objects as go
        t = np.arange(x.size)/fs_hz
        fig = go.Figure()
        plot_tpl = THEMES[st.session_state.get("theme","Light")]["plotly_tpl"]
        fig.add_trace(go.Scatter(x=t, y=x, name="raw", line=dict(width=1)))
        if smooth:
            fig.add_trace(go.Scatter(x=t, y=x_s, name="smoothed", line=dict(width=2)))
        fig.add_trace(go.Scatter(x=t, y=base, name="baseline", line=dict(width=1, dash="dash")))
        # Shading envelopes
        if stim_idx > 1:
            fig.add_shape(type="rect",
                          x0=t[0], x1=t[stim_idx-1], y0=base[:stim_idx].min(), y1=(thr_pre).max(),
                          fillcolor=THEMES[st.session_state.get("theme","Light")]["shade_pre"], line=dict(width=0), layer="below")
        fig.add_shape(type="rect",
                      x0=t[stim_idx], x1=t[-1], y0=base[stim_idx:].min(), y1=(thr_post).max(),
                      fillcolor=THEMES[st.session_state.get("theme","Light")]["shade_post"], line=dict(width=0), layer="below")
        fig.add_trace(go.Scatter(x=t[:stim_idx], y=thr_pre, name=f"thr pre ({k}·SD)", line=dict(width=1)))
        fig.add_trace(go.Scatter(x=t[stim_idx:], y=thr_post, name=f"thr post ({k}·SD)", line=dict(width=1)))
        fig.add_trace(go.Scatter(x=t[peaks], y=x_s[peaks], mode="markers", name="peaks"))
        fig.update_layout(height=520, hovermode="x unified", template=plot_tpl, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Label")
        s.setdefault("history", [])  # stack of (cell_index, prev_dict)
        if st.button("Undo last save"):
            if s.history:
                ci, prev = s.history.pop()
                if prev is None:
                    # Clear mapping if previously empty
                    s.label_map.pop(ci, None)
                    st.session_state["label_value"] = "Oscillatory"
                    st.session_state["notes_value"] = ""
                else:
                    s.label_map[ci] = prev
                    st.session_state["label_value"] = prev.get("label", "Oscillatory")
                    st.session_state["notes_value"] = prev.get("notes", "")
                _log(f"undo cell_index={ci}")
                st.success("Undid last save for current/previous cell.")
        label = st.radio("Class", LABELS, key="label_value")
        notes = st.text_area("Notes", placeholder="Optional free text", key="notes_value")
        if st.button("Save label (CSV)"):
            # push previous state for undo
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
                _log(f"save cell_index={int(s.current_cell)} label={label}")
                s.label_map[int(s.current_cell)] = {"label": label, "notes": notes}
                st.success(f"Saved → {Path(s.session_dir) / 'labels.csv'}")
                # Auto-advance to next unlabeled cell (optional)
                next_unlab = [i for i in range(N) if i not in s.label_map and i > s.current_cell]
                if next_unlab:
                    s.current_cell = int(next_unlab[0])
                    st.rerun()
            else:
                st.warning("Start a session (Annotator & Save dir) to save CSVs.")

    st.markdown('---')
    st.subheader("Step 5 — Finish & export")
    export_col1, export_col2 = st.columns([1,2])
    with export_col1:
        do_export = st.button("Export session as ZIP")
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
else:
    if s.stage == 1:
        st.info("Step 1 — Start a new session in the left sidebar.")
    elif s.stage == 2:
        st.info("Step 2 — Upload a CSV/NPZ file and choose indexing in the sidebar.")
    elif s.stage == 3:
        st.info("Step 3 — Adjust labeling parameters in the left sidebar and click “Confirm labeling parameters”.")
    elif s.stage == 5:
        st.success("Step 5 — Session finished. You can export a ZIP archive or start a new session.")
    else:
        st.info("Follow the steps above to begin.")

# --- Footer & legal note ---
st.markdown("---")
st.markdown("<div class='small-muted'>OPCAL‑Labeler • Local labeling tool • MIT/BSD‑style license. No telemetry. Data stays local.</div>", unsafe_allow_html=True)
