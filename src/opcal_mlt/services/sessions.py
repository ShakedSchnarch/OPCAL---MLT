"""Session lifecycle services (create, resume, hydrate)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from opcal_mlt.app.session_io import make_session_dir, now_utc_iso, write_session_header
from opcal_mlt.domain.enums import LabelClass
from opcal_mlt.domain.models import LabelMap, LabelState, SessionConfig, SessionPaths, build_label_map


@dataclass(slots=True)
class SessionContext:
    config: SessionConfig
    paths: SessionPaths
    recording_id: str


class SessionService:
    """High-level orchestration around session folders and CSV artifacts."""

    def start(self, config: SessionConfig, recording_id: str) -> SessionContext:
        session_dir = make_session_dir(config.save_root, recording_id, config.annotator_id)
        paths = SessionPaths(base_dir=session_dir.parent, session_dir=session_dir)
        write_session_header(
            session_dir,
            {
                "session_id": session_dir.name,
                "recording_id": recording_id,
                "annotator_id": config.annotator_id,
                "fs_hz": "",
                "started_utc": now_utc_iso(),
                "app_version": "",
                "source_path": "",
                "source_sha256": "",
            },
        )
        return SessionContext(config=config, paths=paths, recording_id=recording_id)

    def hydrate_labels(self, session_dir: Path) -> LabelMap:
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
                    uncertain=bool(getattr(row, "uncertain", False))
                    if "uncertain" in df.columns and not pd.isna(getattr(row, "uncertain", None))
                    else False,
                )
            )
        return build_label_map(records)

    def hydrate_cell_ids(self, session_dir: Path) -> Optional[list[str]]:
        cell_map_csv = session_dir / "cell_map.csv"
        if not cell_map_csv.exists():
            return None
        df_map = pd.read_csv(cell_map_csv).sort_values("cell_index")
        return [str(x) for x in df_map["cell_id"].tolist()]


__all__ = ["SessionService", "SessionContext"]
