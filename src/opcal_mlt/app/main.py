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
from opcal_mlt.app.ui import inject_theme_css, render_stepper_and_tips
from opcal_mlt.app.screens import render_labeling_workspace, render_finish_export, render_start_session, render_upload_and_indexing, render_params
try:
    # New name (preferred)
    from opcal_mlt.core.schemas import PreprocessConfig
except ImportError:  # Backward-compatibility with older versions
    from opcal_mlt.core.schemas import PreprocessSettings as PreprocessConfig
from opcal_mlt.app.session_io import make_session_dir, write_session_header, write_cell_map, append_labels, append_peaks, now_utc_iso
s = st.session_state
s.setdefault("stage", 1)               # 1=Start, 2=Upload, 3=Params, 4=Label, 5=Finish
s.setdefault("params_confirmed", False)
s.setdefault("export_done", False)
s.setdefault("recording_id", "")


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
    initial_sidebar_state="collapsed",
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
# Infer stage conservatively based on existing flags, but never downgrade the user's explicit navigation.
# We only advance the stage if prerequisites for the *next* stage are already satisfied.
cur = int(s.get("stage", 1))
# If we haven't uploaded yet, max is 1 (Start) or 2 (Upload)
if cur <= 1:
    s.stage = 1
elif cur == 2 and s.get("traces") is None:
    s.stage = 2
elif cur <= 3 and not s.get("params_confirmed"):
    s.stage = 3
elif cur <= 4 and not s.get("export_done"):
    # Reaching stage 4 (labeling) requires a session_dir, but we allow the user to *arrive* at step 4 UI only
    # after upload + params are confirmed; the session folder will be created automatically once traces exist.
    s.stage = 4 if (s.get("traces") is not None and s.get("params_confirmed")) else 3
else:
    s.stage = 5

labels_steps = ["Start new session", "Upload & indexing", "Labeling parameters", "Label files", "Finish & export"]
current_step = int(s.stage)
render_stepper_and_tips(current_step)

# Navigation controls
req_ready = {
    1: bool(s.get("annotator") and s.get("save_dir")),  # after Start/Update in step 1
    2: bool(s.get("traces") is not None),               # after upload in step 2
    3: bool(s.get("params_confirmed")),                 # after confirm in step 3
    4: True,
    5: False,
}
nav_left, nav_right = st.columns([1,1])
if nav_left.button("Back", key="btn_stage_back", disabled=(current_step <= 1)):
    s.stage = max(1, current_step - 1)
    st.rerun()
if nav_right.button("Next", key="btn_stage_next", disabled=not req_ready.get(current_step, False)):
    s.stage = min(5, current_step + 1)
    st.rerun()


# --- Create session folder once traces & user meta exist (no sidebar flow) ---
if s.get("annotator") and s.get("save_dir") and (s.get("traces") is not None) and not s.get("session_dir"):
    base_dir = Path(s.save_dir)
    rec_id = s.get("recording_id") or f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    s.session_dir = make_session_dir(base_dir, rec_id, s.annotator)
    write_session_header(
        s.session_dir,
        {
            "session_id": Path(s.session_dir).name,
            "recording_id": rec_id,
            "annotator_id": s.annotator,
            "fs_hz": float(s.get("fs_hz", 10.0)),
            "started_utc": now_utc_iso(),
            "app_version": APP_VERSION,
            "source_path": "",
            "source_sha256": "",
        },
    )
    if s.get("cell_ids"):
        write_cell_map(
            s.session_dir, [{"cell_index": i, "cell_id": s.cell_ids[i]} for i in range(len(s.cell_ids))]
        )
    _log(f"session_start annotator={s.annotator} recording_id={rec_id}")

# --- Stage router: show only the current stage screen ---
from opcal_mlt.app.screens import render_start_session, render_upload_and_indexing, render_params
if s.stage == 1:
    render_start_session(s=s)
elif s.stage == 2:
    render_upload_and_indexing(s=s)
elif s.stage == 3:
    render_params(s=s)
elif s.stage >= 4 and s.get("traces") is not None and s.get("session_dir"):
    params = {
        "fs_hz": float(s.get("fs_hz", 10.0)),
        "smooth": bool(s.get("smooth", True)),
        "window": int(s.get("window", 31)),
        "poly": int(s.get("poly", 3)),
        "baseline_method": str(s.get("baseline_method", "rolling_median")),
        "window_s": int(s.get("window_s", 20)),
        "k": float(s.get("k", 3.0)),
        "stim_time_s": float(s.get("stim_time_s", 5.0)),
    }
    theme = THEMES[st.session_state.get("theme", "Light")]
    render_labeling_workspace(s=s, params=params, theme=theme, logger=_log)
    render_finish_export(st.session_state)
else:
    st.info("Follow the steps above to begin.")

# --- Footer & legal note ---
st.markdown("---")
st.markdown("<div class='small-muted'>OPCAL‑Labeler • Local labeling tool • MIT/BSD‑style license. No telemetry. Data stays local.</div>", unsafe_allow_html=True)
