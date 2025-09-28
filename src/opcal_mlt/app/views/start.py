"""
Step 1 — Start, Resume, or Load a Session
=========================================

This module implements the first step of the labeling workflow in the OPCAL MLT tool.
Users can initialize a new labeling session, resume a recent session, or load a session from disk.

Functions:
    render: Main entry point for the Streamlit page.
    _render_new_session: UI for starting a new session.
    _render_resume: UI for resuming a recent session.
    _render_load_from_path: UI for loading a session from a specified path.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import streamlit as st

from opcal_mlt.app.state import StateAdapter
from opcal_mlt.services.sessions import SessionService

_DEFAULT_SAVE_ROOT = Path.home() / "OPCAL_LABELS"

# ==== Main Page Renderer ====
def render(*, state: StateAdapter, session_service: SessionService) -> None:
    """Render the Stage 1 Streamlit page for starting, resuming, or loading a session.

    Args:
        state: Application state adapter.
        session_service: Service responsible for session management.

    Returns:
        None: Streamlit renders output directly.
    """
    st.markdown("<div class='step-header'>Step 1 — Start session</div>", unsafe_allow_html=True)
    st.caption("Initialize a new labeling run, resume a recent session, or load one from disk.")

    save_root = state.get_save_dir().strip() or str(_DEFAULT_SAVE_ROOT)
    resumable = session_service.list_resumable_sessions(Path(save_root), limit=10)

    options: List[str] = ["New session"]
    if resumable:
        options.append("Resume recent session")
    options.append("Load session from path")

    choice = st.radio("Action", options, horizontal=True, key="start_action")

    if choice == "New session":
        _render_new_session(state)
    elif choice == "Resume recent session":
        _render_resume(state, session_service, save_root)
    else:
        _render_load_from_path(state, session_service)

# ==== Session Creation ====
def _render_new_session(state: StateAdapter) -> None:
    """Render UI elements for starting a new labeling session.

    Args:
        state: Application state adapter.

    Returns:
        None: Streamlit renders output directly.
    """
    st.markdown("### New session")
    default_root = state.get_save_dir().strip() or str(_DEFAULT_SAVE_ROOT)

    annotator_val = st.text_input(
        "Annotator ID",
        value=state.get_annotator(),
        key="start_annotator",
        placeholder="Enter annotator ID",
    ).strip()

    use_default = st.checkbox(
        "Use default save directory (~/OPCAL_LABELS)",
        value=(not state.get_save_dir()),
        key="start_use_default_save",
    )

    if use_default:
        st.text_input(
            "Save directory",
            value=str(_DEFAULT_SAVE_ROOT),
            disabled=True,
            key="start_savedir_view",
            help="Sessions will be stored under ~/OPCAL_LABELS/<recording>/<session>.",
        )
        chosen_root = Path(_DEFAULT_SAVE_ROOT)
    else:
        chosen_root_str = st.text_input(
            "Save directory",
            value=state.get_save_dir() or default_root,
            key="start_savedir_input",
            help="Folder where session subdirectories will be created.",
        )
        chosen_root = Path(chosen_root_str).expanduser()

    start_disabled = not (annotator_val and str(chosen_root).strip())

    if st.button("Save settings", type="primary", use_container_width=True, disabled=start_disabled, key="start_save_settings"):
        try:
            chosen_root.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            st.error(f"Could not create or access {chosen_root}: {exc}")
            return
        state.set_annotator(annotator_val)
        state.set_save_dir(chosen_root)
        st.success("Preferences saved. Continue to Upload when ready.")


def _render_resume(
    state: StateAdapter,
    session_service: SessionService,
    save_root: str,
) -> None:
    """Render controls for resuming a recently saved session.

    Args:
        state: Application state adapter.
        session_service: Session service used for discovery and hydration.
        save_root: Root directory to inspect for session folders.
    """
    st.markdown("### Resume recent session")
    st.caption("Pick an existing session folder from your save directory.")

    save_root_input = st.text_input(
        "Save directory",
        value=save_root,
        key="resume_savedir",
    ).strip()

    try:
        candidates = session_service.list_resumable_sessions(Path(save_root_input), limit=10)
    except Exception:
        candidates = []

    if not candidates:
        st.info("No sessions with labels.csv found under the selected directory.")
        return

    labels = [f"{item.recording_id} / {item.session_dir.name} ({item.labels_count} labels)" for item in candidates]
    selection = st.selectbox("Pick a session", labels, index=0, key="resume_pick")
    idx = labels.index(selection) if selection in labels else 0

    if st.button("Resume session", type="primary", use_container_width=True, key="resume_apply"):
        summary = candidates[idx]
        try:
            loaded = session_service.load_session(summary.session_dir)
        except Exception as exc:
            st.error(f"Could not load session: {exc}")
            return
        state.set_session_dir(loaded.session_dir)
        state.set_save_dir(Path(save_root_input or summary.session_dir.parent.parent))
        annotator = str(loaded.metadata.get("annotator_id", "")).strip() or state.get_annotator() or "anon"
        state.set_annotator(annotator)
        state.set_label_map_from_states(loaded.label_map)
        if loaded.cell_ids and not state.get_cell_ids():
            state.set_cell_ids(loaded.cell_ids)
        if "recording_id" in loaded.metadata:
            state.set("recording_id", loaded.metadata["recording_id"])
        st.success(f"Resumed session {summary.session_dir} (loaded {len(loaded.label_map)} labels).")


def _render_load_from_path(state: StateAdapter, session_service: SessionService) -> None:
    """Render controls for loading a session from an explicit path.

    Args:
        state: Application state adapter.
        session_service: Session service used to validate and hydrate sessions.
    """
    st.markdown("### Load session from path")
    st.caption("Provide a session directory that already contains labels.csv or session.csv.")

    typed_path = st.text_input(
        "Session folder",
        value=state.get_session_dir(),
        key="load_session_dir",
    ).strip()

    is_valid = _looks_like_session_dir(typed_path)
    if st.button("Load session", type="primary", use_container_width=True, disabled=not is_valid, key="load_session_btn"):
        target = Path(typed_path).expanduser()
        try:
            loaded = session_service.load_session(target)
        except Exception as exc:
            st.error(f"Failed to load session: {exc}")
            return
        state.set_session_dir(loaded.session_dir)
        state.set_label_map_from_states(loaded.label_map)
        if loaded.cell_ids:
            state.set_cell_ids(loaded.cell_ids)
        base_root = loaded.session_dir.parent.parent if loaded.session_dir.parent.parent.exists() else _DEFAULT_SAVE_ROOT
        state.set_save_dir(base_root)
        annotator = str(loaded.metadata.get("annotator_id", "")).strip() or state.get_annotator() or "anon"
        state.set_annotator(annotator)
        if "recording_id" in loaded.metadata:
            state.set("recording_id", loaded.metadata["recording_id"])
        st.success(f"Loaded session from {loaded.session_dir}.")


def _looks_like_session_dir(path_str: str) -> bool:
    """Return True when the given path resembles a session directory.

    Args:
        path_str: Candidate path string provided by the user.

    Returns:
        bool: ``True`` when the directory exists and contains expected CSV artifacts.
    """
    if not path_str:
        return False
    try:
        path = Path(path_str).expanduser()
        return path.is_dir() and ((path / "labels.csv").exists() or (path / "session.csv").exists())
    except Exception:
        return False
