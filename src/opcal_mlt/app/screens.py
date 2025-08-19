"""
Screens for the OPCAL Labeler Streamlit app.

This module implements the UI for the four high-level steps:
1) Start new session / resume / load by path
2) Upload & indexing
3) Labeling workspace (parameters + plotting + labeling)
4) Finish & export (summary + ZIP export)

Conventions:
- We use `s` as an alias for `st.session_state` throughout the file.
- All functions are *pure-UI*; they read/write to `s` and do not return data.
- State keys that are shared across screens are documented in each function
  docstring under "Session state keys".
- Keep user-facing text in English for clarity and consistency.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

from opcal_mlt.core import preprocess as pp
from opcal_mlt.core import peaks as pk
from opcal_mlt.core import features as ft
from opcal_mlt.app.session_io import append_labels, append_peaks


def render_finish_export(session_state) -> None:
    """
    Step 4 — Finish & export.

    Shows a summary of labeled cells (pie chart + per‑cell table) and an option
    to export the current session as a ZIP archive. If `labels.csv` exists on
    disk, the function hydrates the summary from it and falls back to the
    in‑memory `s.label_map` otherwise.

    Session state keys (read/write):
    - s.session_dir: str path to the active session folder (required for export)
    - s.label_map: Dict[int, {label:str, notes:str}] used when labels.csv missing
    - s.cell_ids: List[str] for table display (optional)
    - s.traces: np.ndarray (T×N), used to infer total cell count for context
    - s._celebrated_finish: bool guard to trigger balloons only once per session
    - s.export_done: bool set to True after a successful export
    """
    s = session_state
    st.markdown('---')
    st.header("Step 4 — Finish & export")

    # Celebrate arrival to the final step once per session
    if not s.get("_celebrated_finish", False):
        st.success("Great job! Labeling complete. You can now export this session as a ZIP archive.")
        try:
            st.balloons()
        except Exception:
            pass
        s._celebrated_finish = True

    # ---------- Hydrate from disk when possible ----------
    labels_df_disk = None
    try:
        if s.get("session_dir"):
            import pandas as _pd
            sess = Path(s.session_dir)
            labels_csv_path = sess / "labels.csv"
            if labels_csv_path.exists():
                try:
                    labels_df_disk = _pd.read_csv(labels_csv_path)
                except Exception:
                    labels_df_disk = None
            # Fill cell_ids if missing (for nicer tables)
            if not s.get("cell_ids"):
                map_csv = sess / "cell_map.csv"
                if map_csv.exists():
                    try:
                        df_map = _pd.read_csv(map_csv).sort_values("cell_index")
                        s.cell_ids = [str(x) for x in df_map["cell_id"].tolist()]
                    except Exception:
                        pass
    except Exception:
        pass

    # Diagnostics: help users verify where the app is reading data from.
    if s.get("session_dir"):
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

    # Summary (first): compute label stats, then visualize as a pie chart.
    st.markdown("---")
    st.subheader("Label statistics")

    try:
        import pandas as _pd

        # Infer total cell count for nicer context (optional)
        total_cells = None
        if s.get("traces") is not None:
            total_cells = int(getattr(s.traces, "shape", [0, 0])[1])
        elif s.get("session_dir"):
            sess = Path(s.session_dir)
            map_csv = sess / "cell_map.csv"
            if map_csv.exists():
                try:
                    df_map = _pd.read_csv(map_csv)
                    total_cells = int(len(df_map))
                except Exception:
                    pass
            if total_cells is None:
                lab_csv = sess / "labels.csv"
                if lab_csv.exists():
                    try:
                        _tmp = _pd.read_csv(lab_csv)
                        if "cell_index" in _tmp.columns and len(_tmp) > 0:
                            total_cells = int(_tmp["cell_index"].max()) + 1
                    except Exception:
                        pass

        # Build summary using helper (prefer disk, fallback to memory)
        if labels_df_disk is not None and len(labels_df_disk) > 0:
            has_unc = "uncertain" in labels_df_disk.columns
            disk_map = {
                int(r.cell_index): {
                    "label": str(r.label),
                    "notes": ("" if "notes" not in labels_df_disk.columns or _pd.isna(getattr(r, "notes", None)) else str(getattr(r, "notes", ""))),
                    "uncertain": bool(getattr(r, "uncertain")) if (has_unc and not _pd.isna(getattr(r, "uncertain", None))) else False,
                }
                for r in labels_df_disk.itertuples(index=False)
            }
            if not s.get("label_map"):
                s.label_map = disk_map
            labels_df, stats_df = ft.summarize_labels(disk_map, s.get("cell_ids"), total_cells=total_cells)
        else:
            labels_df, stats_df = ft.summarize_labels(
                s.get("label_map", {}),
                s.get("cell_ids"),
                total_cells=total_cells,
            )
    except Exception:
        import pandas as _pd
        labels_df = _pd.DataFrame(columns=["cell_index", "cell_id", "label", "notes", "uncertain"])
        stats_df  = _pd.DataFrame(columns=["label", "count", "percent"])

    if labels_df is not None and len(labels_df) > 0:
        st.caption(f"Found {len(labels_df)} labeled cells" + (f" / {total_cells} total" if total_cells else ""))

        # Pie chart instead of table
        try:
            import plotly.express as px
            fig = px.pie(
                stats_df,
                names="label",
                values="count",
                hole=0.45,
                title="Class distribution",
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

        # Detailed per-cell table (kept, under the pie)
        df_display = labels_df.copy()
        if "uncertain" in df_display.columns:
            # Present a user-friendly column with checkmarks
            df_display["Uncertain?"] = df_display["uncertain"].map(lambda v: "✓" if bool(v) else "✗")
            # Move the friendly column next to 'label' and optionally hide the raw boolean
            cols = list(df_display.columns)
            # Ensure a consistent column order: cell_index, cell_id, label, Uncertain?, notes, (uncertain hidden)
            desired_order = [c for c in ["cell_index", "cell_id", "label", "Uncertain?", "notes"] if c in cols]
            # Append any remaining columns (excluding the raw 'uncertain' if we already added Uncertain?)
            remaining = [c for c in cols if c not in desired_order and c != "uncertain"]
            df_display = df_display[desired_order + remaining]
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No labels saved yet in this session.")

    # ---------- Export (after summary) ----------
    st.markdown("---")
    st.subheader("Export")
    export_col1, export_col2 = st.columns([1, 2])
    with export_col1:
        st.markdown('<div class="btn-action btn-lg">', unsafe_allow_html=True)
        do_export = st.button("Export session as ZIP", key="btn_export_zip")
        st.markdown('</div>', unsafe_allow_html=True)
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
    Step 3 — Main labeling workspace.

    Responsibilities:
    - Expose processing parameters (sidebar) and apply them to the selected cell.
    - Plot raw/smoothed signals, baseline and dual‑SD thresholds.
    - Navigate between cells and manage labeling, including undo support.

    Parameters
    ----------
    s : streamlit.runtime.state.SafeSessionState
        The shared session state object (`st.session_state`).
    theme : dict
        A small palette used for plot shading/markers.
    logger : Callable[[str], None]
        Callback used for lightweight audit logs.

    Session state keys (read/write)
    -------------------------------
    - traces: np.ndarray (T×N) of signals (required)
    - cell_ids: List[str] mapping index→id (required)
    - current_cell / prev_cell: int navigation helpers
    - label_map: Dict[int, {label, notes, uncertain}] accumulated labels
    - history: List[Tuple[cell_index, previous_label_or_None]] for undo
    - fs_hz, smooth, window, poly, baseline_method, window_s, k, stim_time_s: parameters
    """
    # Robust sidebar floating toggle buttons and collapse logic
    components.html(
        """
        <style>
          /* Floating buttons */
          #openSidebarBtn, #collapseSidebarBtn {
            position: fixed; z-index: 2147483647; width: 36px; height: 36px; border-radius: 18px;
            border: 1px solid #ccc; background: #fff; color: #111; box-shadow: 0 2px 6px rgba(0,0,0,.12);
            display: none; align-items: center; justify-content: center; cursor: pointer; user-select: none;
            text-align: center; line-height: 36px;
          }
          #openSidebarBtn:hover, #collapseSidebarBtn:hover { box-shadow: 0 4px 10px rgba(0,0,0,.18); }
          /* Positions (collapse btn will be adjusted dynamically) */
          #openSidebarBtn { top: 110px; left: 14px; }
          #collapseSidebarBtn { top: 110px; left: 334px; }
        </style>
        <script>
        (function() {
          const doc = window.parent.document;
          const body = doc.body;
          const sidebarSel = '[data-testid="stSidebar"]';
          const getSB = () => doc.querySelector(sidebarSel);

          // Create buttons immediately (even before sidebar exists)
          let openBtn = doc.getElementById('openSidebarBtn');
          if (!openBtn) {
            openBtn = doc.createElement('div');
            openBtn.id = 'openSidebarBtn';
            openBtn.title = 'Show sidebar';
            openBtn.innerHTML = '\\u00AB\\u00AB'; // ««
            doc.body.appendChild(openBtn);
          }
          let collapseBtn = doc.getElementById('collapseSidebarBtn');
          if (!collapseBtn) {
            collapseBtn = doc.createElement('div');
            collapseBtn.id = 'collapseSidebarBtn';
            collapseBtn.title = 'Hide sidebar';
            collapseBtn.innerHTML = '\\u00BB\\u00BB'; // »»
            doc.body.appendChild(collapseBtn);
          }

          const ensureOpen = () => body.classList.remove('sb-collapsed');
          const ensureCollapsed = () => body.classList.add('sb-collapsed');

          // Detect transform/visibility that indicates offscreen even if class isn't set
          function isSidebarOffscreen() {
            const sb = getSB();
            if (!sb) return false;
            const style = sb.getAttribute('style') || '';
            if (style.includes('translateX(-') || style.includes('transform: matrix')) return true;
            const cs = window.getComputedStyle(sb);
            const rect = sb.getBoundingClientRect();
            return (cs.transform && cs.transform !== 'none') || rect.right <= 0 || cs.opacity === '0';
          }
          function isCollapsed() {
            return body.classList.contains('sb-collapsed') || isSidebarOffscreen();
          }

          function forceOpen() {
            ensureOpen();
            const sb = getSB();
            if (sb) {
              try { sb.style.removeProperty('transform'); } catch(e) {}
              try { sb.style.removeProperty('opacity'); } catch(e) {}
              try { sb.style.removeProperty('pointer-events'); } catch(e) {}
            }
          }
          function forceCollapse() {
            ensureCollapsed();
            const sb = getSB();
            if (sb) {
              sb.style.transform = 'translateX(-110%)';
              sb.style.opacity = '0';
              sb.style.pointerEvents = 'none';
            }
          }

          // Default intent: open once sidebar is mounted
          let triedDefaultOpen = false;
          function tryDefaultOpen() {
            const sb = getSB();
            if (sb && !triedDefaultOpen) {
              triedDefaultOpen = true;
              // Delay a tick to let Streamlit finish layout before forcing open
              setTimeout(() => { forceOpen(); tick(); }, 50);
            }
          }

          // Button handlers
          openBtn.onclick = () => { forceOpen(); tick(); };
          collapseBtn.onclick = () => { forceCollapse(); tick(); };

          // Observer: when sidebar exists, sync with Streamlit's own toggles
          let mo = null;
          function ensureObserver() {
            const sb = getSB();
            if (sb && !mo) {
              mo = new MutationObserver(() => {
                // Keep body class aligned with actual visual state
                const off = isSidebarOffscreen();
                if (off) ensureCollapsed(); else ensureOpen();
                positionCollapseBtn();
                tick();
              });
              mo.observe(sb, { attributes: true, attributeFilter: ['style', 'class'] });
            }
          }

          function positionCollapseBtn() {
            const el = getSB();
            if (!el) return;
            const r = el.getBoundingClientRect();
            const cb = doc.getElementById('collapseSidebarBtn');
            cb.style.left = Math.max(14, r.right + 14) + 'px';
          }

          function tick() {
            tryDefaultOpen();
            ensureObserver();
            positionCollapseBtn();

            // Show open button whenever the sidebar is collapsed OR offscreen for any reason
            if (isCollapsed()) {
              openBtn.style.display = 'flex';
              collapseBtn.style.display = 'none';
            } else {
              openBtn.style.display = 'none';
              collapseBtn.style.display = 'flex';
            }
            openBtn.style.pointerEvents = 'auto';
            collapseBtn.style.pointerEvents = 'auto';
          }

          tick();
          // Keep syncing on resizes or layout shifts
          const poll = setInterval(tick, 500);
          window.addEventListener('resize', tick);
        })();
        </script>
        """,
        height=0,
    )
    # Safety: initialize state keys used below
    if "label_map" not in s or not isinstance(s.label_map, dict):
        s.label_map = {}
    if "current_cell" not in s:
        s.current_cell = 0
    if s.get("traces") is None or s.get("cell_ids") is None:
        st.warning("No data loaded yet. Go back to Step 2 (Upload & indexing).")
        return
    # Estimate duration using current (or default) fs to derive stable defaults
    _fs_guess = float(s.get("fs_hz", 1.08))
    _T = int(getattr(s.traces, "shape", [0, 0])[0])
    _dur_s = (_T / _fs_guess) if _fs_guess > 0 else 0.0
    # Default stimulus time ensures at least ~30 samples (or 10 s) before the split,
    # but not more than ~40% of the recording to avoid a tiny post segment.
    _stim_default = float(
        s.get(
            "stim_time_s",
            min(max(30.0 / max(_fs_guess, 1e-9), 10.0), max(1.0, 0.4 * _dur_s)),
        )
    )
    # Sidebar: processing/labeling parameters
    with st.sidebar:
        st.markdown("### Labeling parameters")
        s.fs_hz = st.number_input(
            "Sampling rate (Hz)",
            min_value=0.01,
            value=float(s.get("fs_hz", 1.08)),
            step=0.01,
            format="%.2f",
            help="Default is 1.08 Hz (≈0.93 s/sample)"
        )
        # Plot visibility preferences (persist across reruns)
        s.show_raw = st.checkbox(
            "Show raw signal",
            value=bool(s.get("show_raw", True)),
            help="Toggle the original unfiltered trace.",
        )
        s.show_smoothed = st.checkbox(
            "Show smoothed signal",
            value=bool(s.get("show_smoothed", True)),
            help="Toggle the Savitzky–Golay smoothed trace (when smoothing is enabled).",
        )
        # --- Preprocessing – Smoothing (moved back to Step 3) ---
        s.smooth = st.checkbox(
            "Apply Savitzky–Golay smoothing",
            value=bool(s.get("smooth", True)),
            help=(
                "Phase-preserving smoothing that reduces noise without shifting peaks. "
                "Turn off to view the raw signal."
            ),
        )
        if not s.smooth:
            s.show_smoothed = False
        if s.smooth:
            # Window slider uses odd values only (step=2), default coerced to odd
            _win_default = int(s.get("window", 31))
            if _win_default % 2 == 0:
                _win_default += 1
            s.window = st.slider(
                "Smoothing window (samples)",
                5, 101, _win_default, step=2,
                help=(
                    "Length of the Savitzky–Golay window in samples (must be odd). "
                    "Larger windows produce stronger smoothing but can flatten short events. "
                    "Typical: 21–61."
                ),
            )
            s.poly = st.slider(
                "Polynomial order",
                1, 5, int(s.get("poly", 3)),
                help=(
                    "Order of the fitted polynomial within each window. "
                    "Lower values = gentler smoothing; higher values = more flexible curve. "
                    "Must be less than the window size. Typical: 2–3."
                ),
            )
        s.baseline_method = st.selectbox("Baseline method", ["rolling_median", "percentile (25)"], index=0 if str(s.get("baseline_method","rolling_median")).startswith("rolling") else 1)
        s.window_s = st.slider("Rolling median window (s)", 5, 60, int(s.get("window_s", 20)))
        s.k = st.slider("SD threshold k", 1.0, 6.0, float(s.get("k", 3.0)), step=0.5)
        s.stim_time_s = st.number_input(
            "Stimulus time (s)",
            min_value=0.0,
            value=float(_stim_default),
            step=1.0,
            help=(
                "Time when stimulation starts; used for dual-SD thresholds. "
                "Default adapts to ensure ≥~30 samples (or 10 s) before the split."
            ),
        )
    # Use latest state for processing
    fs_hz      = float(s.get("fs_hz", 1.08))
    smooth     = bool(s.get("smooth", True))
    window     = int(s.get("window", 31))
    poly       = int(s.get("poly", 3))
    baseline_method = str(s.get("baseline_method", "rolling_median"))
    window_s   = int(s.get("window_s", 20))
    k          = float(s.get("k", 3.0))
    stim_time_s= float(s.get("stim_time_s", 5.0))

    T, N = s.traces.shape
    left, mid, right = st.columns([3, 8, 3], gap="small")

    # -------- Left: navigation & progress --------
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Cells")
        if s.get("session_dir"):
            st.caption(f"Session: {s.session_dir}")
        idx = st.number_input("Cell index", 0, N-1, s.current_cell, step=1)
        s.current_cell = idx

        # When the user navigates, reflect any existing label in the radio/textarea.
        if s.get("prev_cell") != s.current_cell:
            existing = s.label_map.get(int(s.current_cell))
            st.session_state["label_value"] = existing["label"] if existing else "Oscillatory"
            st.session_state["notes_value"] = existing["notes"] if existing else ""
            st.session_state["uncertain_value"] = bool(existing.get("uncertain", False)) if existing else False
            s.prev_cell = s.current_cell

        # Progress bar + strip
        progress = int((len(s.label_map) / max(1, N)) * 100)
        st.markdown(f'<div class="progress-track"><div class="progress-fill" style="width:{progress}%;"></div></div>', unsafe_allow_html=True)
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
        fig_status.update_layout(height=90, margin=dict(l=4,r=4,t=4,b=4))
        st.plotly_chart(fig_status, use_container_width=True)

        st.write(f"Progress: {len(s.label_map)} / {N} labeled")
        st.markdown('</div>', unsafe_allow_html=True)

    # Middle: processing & plot
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
        if bool(s.get("show_raw", True)):
            fig.add_trace(go.Scatter(x=t, y=x, name="raw", line=dict(width=1)))
        if smooth and bool(s.get("show_smoothed", True)):
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
        fig.update_layout(height=480, margin=dict(l=10, r=10, t=32, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # Right: labeling
    with right:
        st.subheader("Label")
        label = st.radio("Class", ["High-flat","High-oscillatory","Oscillatory","Low-activity","Drifting"], key="label_value")
        uncertain = st.checkbox("Mark as uncertain", key="uncertain_value", help="Flag this label as uncertain")
        notes = st.text_area("Notes", placeholder="Optional free text", key="notes_value")

        st.markdown('<div class="btn-action btn-lg">', unsafe_allow_html=True)
        if st.button("Save label (CSV)", key="btn_save_label"):
            s.history.append((int(s.current_cell), s.label_map.get(int(s.current_cell))))
            label = st.session_state.get("label_value", "Oscillatory")
            notes = st.session_state.get("notes_value", "")
            uncertain = bool(st.session_state.get("uncertain_value", False))
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
                "uncertain": uncertain,
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
                s.label_map[int(s.current_cell)] = {"label": label, "notes": notes, "uncertain": uncertain}
                st.success(f"Saved → {Path(s.session_dir) / 'labels.csv'}")
                next_unlab = [i for i in range(N) if i not in s.label_map and i > s.current_cell]
                if next_unlab:
                    s.current_cell = int(next_unlab[0])
                    st.rerun()
            else:
                st.warning("Start a session (Annotator & Save dir) to save CSVs.")
        st.markdown('</div>', unsafe_allow_html=True)

from opcal_mlt.app.session_io import make_session_dir, write_session_header, write_cell_map, now_utc_iso

def render_start_session(*, s):
    """
    Step 1 — Start new session / resume / load by path.

    Provides three mutually exclusive actions. The function only updates
    `s.annotator`, `s.save_dir` and/or `s.session_dir` and leaves file creation
    to later steps. The UI is designed so that users always move forward via the
    stepper (Back/Next are outside this function).

    Session state keys (read/write):
    - annotator: str (ID of the person labeling)
    - save_dir: str (root directory where session folders reside)
    - session_dir: str (path to a specific session — set by resume/load)
    - label_map, cell_ids: hydrated on resume/load when CSVs are found
    """
    st.markdown('<div class="step-header">Step 1 — Start session</div>', unsafe_allow_html=True)
    st.caption("Pick one action to initialize or restore your working session.")
    import pathlib as _pl  # Use local alias to avoid any accidental shadowing of Path inside this function

    # Unified chooser for clarity — hide Resume when no valid session exists
    # Remove any local 'from pathlib import Path' (if present) in this function
    def _has_resumable_session(base_root: _pl.Path) -> bool:
        """Return True if a valid session folder exists under base_root.
        A folder is considered valid if it contains either labels.csv or session.csv.
        """
        try:
            if not base_root.exists():
                return False
            for rec_dir in base_root.iterdir():
                if rec_dir.is_dir():
                    for sess in rec_dir.iterdir():
                        if sess.is_dir() and ((sess / "labels.csv").exists() or (sess / "session.csv").exists()):
                            return True
            return False
        except Exception:
            return False

    # Determine the save root to scan
    _default_root = _pl.Path.home() / "OPCAL_LABELS"
    _base_root = _pl.Path(str(s.get("save_dir", str(_default_root))).strip()).expanduser()
    _has_resume = _has_resumable_session(_base_root)
    s["_resume_available"] = _has_resume

    # Build radio choices dynamically
    _choices = ["New session"]
    if _has_resume:
        _choices.append("Resume recent session")
    _choices.append("Load session from path")

    choice = st.radio(
        "Action",
        tuple(_choices),
        horizontal=True,
        key="start_choice",
    )

    if not _has_resume:
        st.caption("No previous session was found in the save folder. Start a new session or load from a path.")

    # --- New session ---
    if choice == "New session":
        st.markdown("### New session")
        st.caption("Set your annotator ID and where sessions are saved. This does not create files yet; they are created when data is uploaded.")
        default_root = (s.get("save_dir") or str(_pl.Path.home() / "OPCAL_LABELS"))

        # Initialize backing keys before rendering widgets to avoid Streamlit key mutation errors.
        if "use_default_savedir" not in st.session_state:
            st.session_state["use_default_savedir"] = True
        if "start_savedir" not in st.session_state:
            st.session_state["start_savedir"] = default_root

        annotator_val = st.text_input(
            "Annotator ID",
            value=s.get("annotator", ""),
            key="start_annotator",
            placeholder="Enter annotator ID",
        ).strip()

        # Default-location toggle (placed above the path input)
        use_default = st.checkbox(
            "Use default (~/OPCAL_LABELS)",
            key="use_default_savedir",
            help="When checked, the default folder will be used for the session. Uncheck to choose a custom folder path.")

        # Show a *disabled* field when using default, otherwise a normal editable input.
        if use_default:
            effective_root = default_root
            # Use a separate view-only key to avoid mutating the real input key after creation
            st.text_input(
                "Save directory",
                value=default_root,
                key="start_savedir_view",
                disabled=True,
                help="Folder where session subfolders will be created.")
        else:
            effective_root = st.text_input(
                "Save directory",
                value=st.session_state.get("start_savedir", default_root),
                key="start_savedir",
                disabled=False,
                help="Folder where session subfolders will be created.")

        # Determine prospective root without side effects for validation
        chosen_root_preview = default_root if use_default else st.session_state.get("start_savedir", default_root)
        # Use whichever is populated: the immediate input return or session state (Streamlit keeps widget state under the key)
        annotator_current = (st.session_state.get("start_annotator") or annotator_val or "").strip()
        valid_annot = len(annotator_current) > 0
        valid_root = len(str(chosen_root_preview).strip()) > 0
        start_disabled = not (valid_annot and valid_root)

        if st.button("Start", type="primary", key="btn_start_new_session", use_container_width=True, disabled=start_disabled):
            # Determine the effective root without mutating widget keys post-creation
            chosen_root = default_root if use_default else st.session_state.get("start_savedir", default_root)
            root = _pl.Path(chosen_root).expanduser()
            try:
                root.mkdir(parents=True, exist_ok=True)
                s.annotator = (annotator_val or "anon")
                s.save_dir = str(root)
                st.success("Settings saved — you can proceed to Upload.")
            except Exception as e:
                st.error(f"Could not create or use the selected directory: {e}")

    # --- Resume recent session ---
    elif choice == "Resume recent session":
        st.markdown("### Resume recent session")
        st.caption("We look under your Save directory for the most recent session folders that contain labels.csv.")
        base_root = st.text_input("Save directory", value=s.get("save_dir", str(_pl.Path.home() / "OPCAL_LABELS")), key="resume_savedir")
        # Heuristic: scan <save_dir>/<recording>/<session> and pick those with labels.csv (latest first).
        recent = []
        base = _pl.Path(base_root.strip())
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
            # Enable only if we actually found candidates
            start_resume_disabled = (len(recent) == 0)
            if st.button("Start", type="primary", key="btn_start_resume", use_container_width=True, disabled=start_resume_disabled):
                try:
                    p = recent[options.index(sel)][1]
                    s.session_dir = str(p)
                    # Ensure annotator/save_dir present so Next can enable
                    s.annotator = (s.get("annotator") or "anon")
                    # Prefer the typed base_root; otherwise keep existing save_dir or fall back to default under HOME
                    default_root = str(_pl.Path.home() / "OPCAL_LABELS")
                    base_root_clean = base_root.strip()
                    s.save_dir = base_root_clean or s.get("save_dir") or default_root
                    # Load existing state (labels + optional cell_map)
                    labels_csv = p / "labels.csv"
                    cell_map_csv = p / "cell_map.csv"
                    loaded = 0
                    if labels_csv.exists():
                        try:
                            df_lab = pd.read_csv(labels_csv)
                            has_unc = "uncertain" in df_lab.columns
                            s.label_map = {
                                int(r.cell_index): {
                                    "label": str(r.label),
                                    "notes": ("" if pd.isna(getattr(r, "notes", None)) else str(getattr(r, "notes", ""))),
                                    "uncertain": bool(getattr(r, "uncertain")) if (has_unc and not pd.isna(getattr(r, "uncertain", None))) else False,
                                }
                                for r in df_lab.itertuples(index=False)
                            }
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
    elif choice == "Load session from path":

        # Text field to choose a session folder
        session_dir = st.text_input(
            "Session folder",
            value=str(s.get("session_dir", "")),
            help="Pick a folder that contains 'labels.csv' or 'session.csv' to load an existing session.",
        )

        # Pre-validate to control the button state
        _typed_path = str(session_dir or "").strip()
        _pre_valid = False
        def _is_valid_session_dir(p: _pl.Path) -> bool:
            try:
                return p.is_dir() and (
                    (p / "labels.csv").exists() or (p / "session.csv").exists()
                )
            except Exception:
                return False
        if _typed_path:
            try:
                _pre_valid = _is_valid_session_dir(_pl.Path(_typed_path).expanduser())
            except Exception:
                _pre_valid = False

        load_btn = st.button("Load session", disabled=(not _pre_valid))

        # Small helper to validate a session directory

        if load_btn:
            p = _pl.Path(session_dir).expanduser()

            # Validate before attempting to load
            if not _is_valid_session_dir(p):
                st.error("Selected folder does not contain 'labels.csv' or 'session.csv'. Please choose a valid session directory.")
                st.stop()

            # Persist and try to hydrate state from disk
            try:
                s.session_dir = str(p)
                # Derive save_dir as the grand‑parent (…/save_dir/<recording>/<session>) when possible
                try:
                    s.save_dir = str(p.parent.parent)
                except Exception:
                    # Fall back to HOME/OPCAL_LABELS if unexpected layout
                    s.save_dir = str(_pl.Path.home() / "OPCAL_LABELS")
                # Ensure annotator present so navigation can proceed
                s.annotator = (s.get("annotator") or "anon")

                # Load labels and optional cell map (best‑effort)
                loaded = 0
                try:
                    df_lab = pd.read_csv(p / "labels.csv")
                    has_unc = "uncertain" in df_lab.columns
                    s.label_map = {
                        int(r.cell_index): {
                            "label": str(r.label),
                            "notes": ("" if pd.isna(getattr(r, "notes", None)) else str(getattr(r, "notes", ""))),
                            "uncertain": bool(getattr(r, "uncertain")) if (has_unc and not pd.isna(getattr(r, "uncertain", None))) else False,
                        }
                        for r in df_lab.itertuples(index=False)
                    }
                    loaded = len(s.label_map)
                except Exception:
                    # No labels or failed to read; keep empty map
                    s.label_map = s.get("label_map", {}) or {}
                try:
                    if not s.get("cell_ids"):
                        df_map = pd.read_csv(p / "cell_map.csv").sort_values("cell_index")
                        s.cell_ids = [str(x) for x in df_map["cell_id"].tolist()]
                except Exception:
                    pass

                st.success(f"Session loaded successfully from: {p}\n\nLoaded {loaded} labeled cells.")
            except Exception as e:
                st.error(f"Failed to load session: {e}")
            s["session_dir"] = str(p)
            st.success("Folder looks valid. Loading session…")
            # The existing code that actually reads files and restores state continues here

def render_upload_and_indexing(*, s):
    """
    Step 2 — Upload & indexing.

    Accepts CSV or NPZ input, previews the data and lets the user decide how
    to assign cell IDs (keep headers / import mapping / auto‑generate). This
    function does not write to disk—only prepares `s.traces`, `s.cell_ids` and
    `s.recording_id` for the downstream labeling workspace.

    Session state keys (read/write):
    - traces: np.ndarray (T×N)
    - cell_ids: List[str]
    - recording_id: str
    - cell_id_prefix, cell_id_pad, cell_id_start: auto‑ID options
    - current_cell: int (reset to 0 after successful load)
    """

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
        # Preferred default: Auto-generate IDs (top option)
        mode = st.radio(
            "Choose how to assign cell IDs",
            ("Auto-generate IDs", "Use column headers from CSV", "Import external mapping CSV"),
            index=0,
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
    """
    (Deprecated) Step 3 — Labeling parameters.

    Kept for internal use or future toggles. The interactive labeling screen now
    exposes these parameters in the sidebar of the workspace itself.
    """
    st.header("Step 3 — Labeling parameters")
    s.fs_hz = st.number_input(
        "Sampling rate (Hz)",
        min_value=0.01,
        value=float(s.get("fs_hz", 1.08)),
        step=0.01,
        format="%.2f",
        help="Default is 1.08 Hz (≈0.93 s/sample)"
    )
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