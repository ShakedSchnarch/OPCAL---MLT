"""
OPCAL‑Labeler — Streamlit app for manual labeling of calcium‑imaging traces.

This module orchestrates the UI flow and navigation between four screens:
  1) Start session (new / resume / load by path)
  2) Upload & indexing
  3) Labeling workspace
  4) Finish & export

Signal processing and data utilities live under `opcal_mlt.core` and `opcal_mlt.app.session_io`.
Outputs are CSV‑based (session.csv, labels.csv, peaks.csv, cell_map.csv).
"""
import streamlit as st
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from opcal_mlt.app.ui import inject_theme_css, render_stepper_and_tips
from opcal_mlt.app.screens import render_labeling_workspace, render_finish_export, render_start_session, render_upload_and_indexing
try:
    # New name (preferred)
    from opcal_mlt.core.schemas import PreprocessConfig
except ImportError:  # Backward-compatibility with older versions
    from opcal_mlt.core.schemas import PreprocessSettings as PreprocessConfig
from opcal_mlt.app.session_io import make_session_dir, write_session_header, write_cell_map, append_labels, append_peaks, now_utc_iso
s = st.session_state
# Hard guards (in addition to setdefault below)
if "label_map" not in s or not isinstance(s.get("label_map"), dict):
    s["label_map"] = {}
if "current_cell" not in s:
    s["current_cell"] = 0
# Ensure annotator/save_dir always present for navigation logic
s.setdefault("annotator", "")
s.setdefault("save_dir", "")
s.setdefault("stage", 1)               # 1=Start, 2=Upload, 3=Label, 4=Finish
s.setdefault("params_confirmed", False)
s.setdefault("export_done", False)
s.setdefault("recording_id", "")
s.setdefault("label_map", {})
s.setdefault("current_cell", 0)
s.setdefault("traces", None)
s.setdefault("cell_ids", None)
s.setdefault("session_dir", "")

s.setdefault("fs_hz", 1.08)
s.setdefault("smooth", True)
s.setdefault("window", 31)
s.setdefault("poly", 3)
s.setdefault("show_raw", True)
s.setdefault("show_smoothed", True)


# === App metadata & constants ===
APP_NAME = "OPCAL‑Labeler"
APP_VERSION = "0.4.0"
LABELS = [
    "High-flat",
    "High-oscillatory",
    "Oscillatory",
    "Low-activity",
    "Uncertain",
    "Drifting",
]

# === Theming (light / dark) ===
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
    """Append a UTC‑timestamped message to the active session's log file (if any)."""
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

# Header + theme injection

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

# === Top stepper (4 stages) ===
# Do not auto‑advance between screens; only guard illegal entry to Step 3.
cur = int(s.get("stage", 1))
if cur == 3 and (s.get("traces") is None or s.get("cell_ids") is None):
    # If user jumped to labeling without data, send back to Upload
    s.stage = 2
else:
    s.stage = cur

current_step = int(s.stage)
render_stepper_and_tips(current_step)

# === Create session folder (once traces + metadata exist) ===
if s.get("annotator") and s.get("save_dir") and (s.get("traces") is not None) and not s.get("session_dir"):
    base_dir = Path(s.save_dir)
    # Recording ID: prefer provided value; fall back to a time‑based identifier.
    rec_id = s.get("recording_id") or f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    s.session_dir = make_session_dir(base_dir, rec_id, s.annotator)
    write_session_header(
        s.session_dir,
        {
            "session_id": Path(s.session_dir).name,
            "recording_id": rec_id,
            "annotator_id": s.annotator,
            "fs_hz": float(s.get("fs_hz", 1.08)),
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

# === Stage router (render a single screen) ===
if s.stage == 1:
    render_start_session(s=s)
elif s.stage == 2:
    render_upload_and_indexing(s=s)
elif s.stage == 3:
    theme = THEMES[st.session_state.get("theme", "Light")]
    render_labeling_workspace(s=s, theme=theme, logger=_log)
elif s.stage == 4:
    render_finish_export(st.session_state)
else:
    st.info("Follow the steps above to begin.")


# === Bottom navigation (Back / Next) ===
st.markdown("---")
req_ready = {
    1: bool(s.get("annotator") and s.get("save_dir")),
    2: bool(s.get("traces") is not None and s.get("cell_ids") is not None),
    3: None,   # will set below
    4: False,
}

# Guard for Step 3 → 4: require at least one saved label (memory or labels.csv)
has_any_labels = bool(st.session_state.get("label_map"))
if not has_any_labels and s.get("session_dir"):
    # Try disk labels.csv
    labels_csv_path = Path(s.session_dir) / "labels.csv"
    if labels_csv_path.exists():
        try:
            import pandas as _pd
            df_lab = _pd.read_csv(labels_csv_path)
            if len(df_lab) > 0:
                has_any_labels = True
        except Exception:
            pass
req_ready[3] = has_any_labels
import streamlit as _st
c_back, c_sp, c_next = st.columns([1,8,1])
back_disabled = (int(s.stage) <= 1)
next_disabled = not req_ready.get(int(s.stage), False)
with c_back:
    if st.button("Back", key="nav_back", use_container_width=True, disabled=back_disabled):
        s.stage = max(1, int(s.stage) - 1)
        st.rerun()
with c_next:
    if int(s.stage) == 4:
        # At finish: Next starts a new session (reset state except annotator/save_dir)
        if st.button("Start a new session", key="nav_restart", use_container_width=True):
            # Keep annotator, save_dir; reset session-specific keys
            keep_keys = {"annotator", "save_dir"}
            for k in [
                "session_dir", "traces", "cell_ids", "recording_id", "label_map",
                "current_cell", "export_done", "params_confirmed", "_celebrated_finish"
            ]:
                if k in s:
                    del s[k]
            s.stage = 1
            st.rerun()
    else:
        if st.button("Next", key="nav_next", use_container_width=True, disabled=next_disabled):
            s.stage = min(4, int(s.stage) + 1)
            st.rerun()

# Hint (Step 3): explain why Next is disabled when no labels are saved
if int(s.stage) == 3 and not has_any_labels:
    st.caption("Save at least one label to proceed to Finish & export.")

# === Footer ===
st.markdown(f"<div class='small-muted'>OPCAL‑Labeler v{APP_VERSION} • Local labeling tool • MIT/BSD‑style license. No telemetry. Data stays local.</div>", unsafe_allow_html=True)
