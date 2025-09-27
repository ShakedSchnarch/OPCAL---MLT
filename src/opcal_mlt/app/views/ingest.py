"""
Step 2 — Upload Traces and Assign Cell IDs
==========================================

This module implements the second step of the labeling workflow in the OPCAL MLT tool.
Users upload CSV/NPZ files, preview traces, and map cell IDs for further analysis.

Functions:
    render: Main entry point for the Streamlit page.
    _render_csv_flow: UI for CSV file upload and mapping.
    _render_npz_flow: UI for NPZ file upload and mapping.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import streamlit as st

from opcal_mlt.app.state import StateAdapter
from opcal_mlt.domain.models import TraceSet
from opcal_mlt.services.ingest import IngestService

def render(*, state: StateAdapter, ingest_service: IngestService) -> None:

# ==== Main Page Renderer ====
def render(*, state: StateAdapter, ingest_service: IngestService) -> None:
    """Render the Step 2 Streamlit page for uploading traces and assigning cell IDs.

    Args:
        state (StateAdapter): The application state adapter.
        ingest_service (IngestService): Service for ingesting trace data.
    """
    st.markdown("<div class='step-header'>Step 2 — Upload & indexing</div>", unsafe_allow_html=True)
    st.caption("Upload a CSV/NPZ file, preview it, and decide how to map cell IDs.")

    uploaded = st.file_uploader(
        "Upload data file (CSV / NPZ)",
        type=["csv", "npz"],
        accept_multiple_files=False,
        key="uploader_step2",
    )

    if not uploaded:
        st.info("Drag & drop a CSV/NPZ file to begin.")
        return

    suffix = Path(uploaded.name).suffix.lower()
    raw_bytes = uploaded.getvalue()
    buffer_for_service = io.BytesIO(raw_bytes)
    buffer_for_service.name = uploaded.name

    try:
        trace_set, meta = ingest_service.load_trace_set(buffer_for_service)
    except Exception as exc:
        st.error(f"Failed to load traces: {exc}")
        return

    state.set("traces", trace_set.traces)
    state.set_cell_ids(trace_set.cell_ids)

    if suffix == ".csv":
        _render_csv_flow(state, ingest_service, trace_set, meta, raw_bytes, uploaded.name)
    elif suffix == ".npz":
        _render_npz_flow(state, ingest_service, trace_set, meta, raw_bytes, uploaded.name)
    else:
        st.error(f"Unsupported file type: {suffix}")
        return

    if state.get("traces") is not None and state.get_cell_ids() is not None:
        cell_ids = state.get_cell_ids() or []
        if len(set(cell_ids)) != len(cell_ids):
            st.warning("Duplicate cell IDs detected. Consider adjusting your mapping.")
        state.set("current_cell", 0)
        st.success(f"Loaded traces: shape {trace_set.traces.shape}. Mapping ready.")


def _render_csv_flow(
    state: StateAdapter,
    ingest_service: IngestService,
    trace_set: TraceSet,
    meta: dict,
    raw_bytes: bytes,
    filename: str,
) -> None:
    df_preview = pd.read_csv(io.BytesIO(raw_bytes))
    st.success(f"Selected file: **{filename}**")
    st.subheader("Preview")
    st.dataframe(df_preview.head(5))

    default_recording = Path(filename).stem
    state.set("recording_id", state.get("recording_id", default_recording))

    st.subheader("Cell ID mapping")
    options = ("Auto-generate IDs", "Use column headers", "Import external mapping CSV")
    mode = st.radio("Choose mapping strategy", options, index=0, key="csv_mapping_mode")

    if mode == "Use column headers":
        state.set_cell_ids([str(col) for col in df_preview.columns.astype(str)])
        st.info("Using CSV column headers as cell IDs.")
    elif mode == "Import external mapping CSV":
        _apply_external_mapping(state, ingest_service, trace_set, key="csv_mapping_upload")
    else:
        _apply_auto_ids(state, ingest_service, trace_set, key_prefix="csv")


def _render_npz_flow(
    state: StateAdapter,
    ingest_service: IngestService,
    trace_set: TraceSet,
    meta: dict,
    raw_bytes: bytes,
    filename: str,
) -> None:
    npz = np.load(io.BytesIO(raw_bytes), allow_pickle=True)
    st.success(f"Selected file: **{filename}**")
    st.subheader("Preview")
    st.write({"npz_keys": list(npz.files)})

    recording_id = meta.get("recording_id") or Path(filename).stem
    state.set("recording_id", recording_id)

    has_ids = "cell_ids" in npz
    mode_options = []
    if has_ids:
        mode_options.append("Use IDs from NPZ")
    mode_options.extend(["Import external mapping CSV", "Auto-generate IDs"])

    default_index = mode_options.index("Auto-generate IDs") if "Auto-generate IDs" in mode_options else 0

    mode = st.radio("Choose mapping strategy", tuple(mode_options), index=default_index, key="npz_mapping_mode")

    if mode == "Use IDs from NPZ" and has_ids:
        try:
            ids = npz["cell_ids"]
            cell_ids = [str(x) for x in (ids.tolist() if hasattr(ids, "tolist") else list(ids))]
            if len(cell_ids) != trace_set.traces.shape[1]:
                st.warning("Length of 'cell_ids' doesn't match number of columns; switching to auto-generate.")
                _apply_auto_ids(state, ingest_service, trace_set, key_prefix="npz")
            else:
                state.set_cell_ids(cell_ids)
                st.info("Using cell IDs embedded in NPZ.")
        except Exception as exc:
            st.warning(f"Failed to read NPZ cell_ids ({exc}); switching to auto-generate.")
            _apply_auto_ids(state, ingest_service, trace_set, key_prefix="npz")
    elif mode == "Import external mapping CSV":
        _apply_external_mapping(state, ingest_service, trace_set, key="npz_mapping_upload")
    else:
        _apply_auto_ids(state, ingest_service, trace_set, key_prefix="npz")


def _apply_external_mapping(state: StateAdapter, ingest_service: IngestService, trace_set: TraceSet, *, key: str) -> None:
    map_file = st.file_uploader("Upload mapping CSV (columns: cell_index, cell_id)", type=["csv"], key=key)
    if map_file is None:
        return
    try:
        df_map = pd.read_csv(map_file)
    except Exception as exc:
        st.error(f"Failed to read mapping CSV: {exc}")
        return
    if not {"cell_index", "cell_id"}.issubset(df_map.columns):
        st.error("Mapping CSV must contain columns 'cell_index' and 'cell_id'.")
        return
    df_map = df_map.sort_values("cell_index")
    ids = [str(x) for x in df_map["cell_id"].tolist()]
    try:
        applied = ingest_service.apply_external_ids(trace_set, ids)
    except ValueError as exc:
        st.error(str(exc))
        return
    state.set_cell_ids(applied.cell_ids)
    st.success("Applied external mapping.")


def _apply_auto_ids(state: StateAdapter, ingest_service: IngestService, trace_set: TraceSet, *, key_prefix: str) -> None:
    colA, colB, colC = st.columns(3)
    prefix = colA.text_input(
        "Auto ID prefix",
        value=str(state.get("cell_id_prefix", "cell_")),
        key=f"{key_prefix}_auto_prefix",
    )
    pad = colB.number_input(
        "Zero pad",
        min_value=1,
        max_value=8,
        value=int(state.get("cell_id_pad", 5)),
        step=1,
        key=f"{key_prefix}_auto_pad",
    )
    start = colC.number_input(
        "Start index",
        min_value=0,
        max_value=1_000_000,
        value=int(state.get("cell_id_start", 0)),
        step=1,
        key=f"{key_prefix}_auto_start",
    )
    ids = ingest_service.auto_cell_ids(trace_set.traces.shape[1], prefix=prefix, pad=int(pad), start=int(start))
    state.set_cell_ids(ids)
    state.set("cell_id_prefix", prefix)
    state.set("cell_id_pad", int(pad))
    state.set("cell_id_start", int(start))
    st.info("Auto-generated IDs applied.")
