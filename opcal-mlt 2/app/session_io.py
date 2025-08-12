
from __future__ import annotations
import csv, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def make_session_dir(base_dir: Path, recording_id: str, annotator: str) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    sess = base_dir / recording_id / f"{ts}_{annotator}"
    sess.mkdir(parents=True, exist_ok=True)
    return sess

def write_session_header(session_dir: Path, header: Dict[str, Any]) -> None:
    path = session_dir / "session.csv"
    need_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(header.keys()))
        if need_header:
            w.writeheader()
        w.writerow(header)

def write_cell_map(session_dir: Path, cell_map: List[Dict[str, Any]]) -> None:
    path = session_dir / "cell_map.csv"
    need_header = not path.exists()
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cell_index","cell_id"])
        if need_header:
            w.writeheader()
        for row in cell_map:
            w.writerow(row)

def append_labels(session_dir: Path, row: Dict[str, Any]) -> None:
    path = session_dir / "labels.csv"
    need_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if need_header:
            w.writeheader()
        w.writerow(row)

def append_peaks(session_dir: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    path = session_dir / "peaks.csv"
    need_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if need_header:
            w.writeheader()
        for r in rows:
            w.writerow(r)
