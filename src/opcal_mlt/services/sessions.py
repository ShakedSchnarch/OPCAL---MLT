"""
Session Service
===============

Provides high-level orchestration for session lifecycle management, including creation, resumption, hydration, and metadata handling.
Handles session folders, CSV artifacts, and summary operations for electrophysiological labeling workflows.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

from opcal_mlt.app.session_io import make_session_dir, now_utc_iso, write_session_header
from opcal_mlt.domain.enums import LabelClass
from opcal_mlt.domain.models import (
    LabelMap,
    LabelState,
    LoadedSession,
    SessionConfig,
    SessionPaths,
    SessionSummary,
    build_label_map,
)


@dataclass(slots=True)
class SessionContext:
    """
    Context object for a session, containing configuration, paths, and recording ID.

    Attributes:
        config (SessionConfig): Session configuration.
        paths (SessionPaths): Paths relevant to the session.
        recording_id (str): Identifier for the recording.
    """
    config: SessionConfig
    paths: SessionPaths
    recording_id: str


class SessionService:
    """
    Service for managing session lifecycle, folders, and CSV artifacts.

    Methods:
        start: Create a new session and initialize metadata.
        hydrate_labels: Load label map from session CSV.
        hydrate_cell_ids: Load cell IDs from session CSV.
        list_resumable_sessions: List resumable sessions in a save root.
        load_session: Load a session and its metadata.
    """

    def start(
        self,
        config: SessionConfig,
        recording_id: str,
        *,
        metadata: Optional[dict] = None,
    ) -> SessionContext:
        """
        Create a new session and initialize its metadata and folder structure.

        Args:
            config (SessionConfig): Session configuration.
            recording_id (str): Identifier for the recording.
            metadata (Optional[dict]): Optional metadata for session header.

        Returns:
            SessionContext: Context object for the created session.
        """
        session_dir = make_session_dir(config.save_root, recording_id, config.annotator_id)
        paths = SessionPaths(base_dir=session_dir.parent, session_dir=session_dir)
        header = metadata.copy() if metadata else {}
        header.setdefault("session_id", session_dir.name)
        header.setdefault("recording_id", recording_id)
        header.setdefault("annotator_id", config.annotator_id)
        header.setdefault("fs_hz", "")
        header.setdefault("started_utc", now_utc_iso())
        header.setdefault("app_version", "")
        header.setdefault("source_path", "")
        header.setdefault("source_sha256", "")
        write_session_header(session_dir, header)
        return SessionContext(config=config, paths=paths, recording_id=recording_id)

    def hydrate_labels(self, session_dir: Path) -> LabelMap:
        """
        Load label map from the session's labels.csv file.

        Args:
            session_dir (Path): Path to the session directory.

        Returns:
            LabelMap: Dictionary mapping cell indices to label states.
        """
        labels_csv = session_dir / "labels.csv"
        if not labels_csv.exists():
            return {}
        df = pd.read_csv(labels_csv)
        records = []
        for row in df.itertuples(index=False):
            label = getattr(row, "label", "")
            records.append(
                LabelState(
                    cell_index=int(getattr(row, "cell_index")),
                    label=LabelClass.from_str(str(label)),
                    notes="" if pd.isna(getattr(row, "notes", "")) else str(getattr(row, "notes", "")),
                    uncertain=_coerce_bool(getattr(row, "uncertain", False)) if "uncertain" in df.columns else False,
                )
            )
        return build_label_map(records)

    def hydrate_cell_ids(self, session_dir: Path) -> Optional[list[str]]:
        """
        Load cell IDs from the session's cell_map.csv file.

        Args:
            session_dir (Path): Path to the session directory.

        Returns:
            Optional[list[str]]: List of cell IDs, or None if not found.
        """
        cell_map_csv = session_dir / "cell_map.csv"
        if not cell_map_csv.exists():
            return None
        df_map = pd.read_csv(cell_map_csv).sort_values("cell_index")
        return [str(x) for x in df_map["cell_id"].tolist()]

    def list_resumable_sessions(self, save_root: Path, limit: int = 5) -> List[SessionSummary]:
        """
        List resumable sessions in the given save root directory.

        Args:
            save_root (Path): Path to the root directory containing session folders.
            limit (int): Maximum number of sessions to return.

        Returns:
            List[SessionSummary]: List of session summaries sorted by last modified.
        """
        save_root = Path(save_root).expanduser()
        if not save_root.exists():
            return []
        candidates: List[SessionSummary] = []
        for recording_dir in save_root.iterdir():
            if not recording_dir.is_dir():
                continue
            for session_dir in recording_dir.iterdir():
                if not session_dir.is_dir():
                    continue
                summary = self._summarize_session(session_dir)
                if summary:
                    candidates.append(summary)
        candidates.sort(key=lambda item: item.last_modified, reverse=True)
        return candidates[:limit]

    def load_session(self, session_dir: Path) -> LoadedSession:
        """
        Load a session and its metadata from the given directory.

        Args:
            session_dir (Path): Path to the session directory.

        Returns:
            LoadedSession: Loaded session object with label map, cell IDs, and metadata.

        Raises:
            FileNotFoundError: If the session directory does not exist.
        """
        session_dir = Path(session_dir)
        if not session_dir.exists():
            raise FileNotFoundError(f"Session directory not found: {session_dir}")
        label_map = self.hydrate_labels(session_dir)
        cell_ids = self.hydrate_cell_ids(session_dir)
        metadata = self._read_session_metadata(session_dir)
        return LoadedSession(session_dir=session_dir, label_map=label_map, cell_ids=cell_ids, metadata=metadata)

    # ------------------------------------------------------------------
    def _summarize_session(self, session_dir: Path) -> Optional[SessionSummary]:
        """
        Summarize a session by counting labels and determining last modification time.

        Args:
            session_dir (Path): Path to the session directory.

        Returns:
            Optional[SessionSummary]: Summary object or None if not found.
        """
        labels_csv = session_dir / "labels.csv"
        session_csv = session_dir / "session.csv"
        if not labels_csv.exists() and not session_csv.exists():
            return None
        labels_count = 0
        last_modified_ts: float = 0.0
        if labels_csv.exists():
            labels_count = self._safe_count_rows(labels_csv)
            last_modified_ts = labels_csv.stat().st_mtime
        elif session_csv.exists():
            last_modified_ts = session_csv.stat().st_mtime
        recording_id = session_dir.parent.name
        return SessionSummary(
            session_dir=session_dir,
            recording_id=recording_id,
            labels_count=labels_count,
            last_modified=datetime.fromtimestamp(last_modified_ts),
        )

    def _safe_count_rows(self, path: Path) -> int:
        """
        Safely count the number of rows in a CSV file.

        Args:
            path (Path): Path to the CSV file.

        Returns:
            int: Number of rows, or 0 if an error occurs.
        """
        try:
            df = pd.read_csv(path)
            return int(len(df))
        except Exception:
            return 0

    def _read_session_metadata(self, session_dir: Path) -> dict:
        """
        Read session metadata from the session.csv file.

        Args:
            session_dir (Path): Path to the session directory.

        Returns:
            dict: Dictionary of session metadata, or empty dict if not found or error.
        """
        session_csv = session_dir / "session.csv"
        if not session_csv.exists():
            return {}
        try:
            df = pd.read_csv(session_csv)
            if df.empty:
                return {}
            row = df.iloc[-1].to_dict()
            return {k: ("" if pd.isna(v) else v) for k, v in row.items()}
        except Exception:
            return {}


def _coerce_bool(value: object) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", ""}:
        return False
    return bool(value)


__all__ = ["SessionService", "SessionContext"]
