
"""
Session I/O utilities for OPCAL‑Labeler.

This module provides thin, testable helpers for creating a session folder and
writing CSV artifacts in a consistent and robust way:
  • session.csv   – one header row describing the session metadata
  • cell_map.csv  – mapping between (cell_index → cell_id) for reproducibility
  • labels.csv    – one row per labeled cell
  • peaks.csv     – one row per detected peak (optional)

Notes
-----
- We intentionally avoid pandas here to keep runtime dependencies light and
  explicit. The CSVs remain easy to read with pandas when needed.
- All writers ensure the parent directory exists and write headers if the file
  does not exist yet. For appenders, the header field order is derived from the
  first row written; keep your dict keys stable to maintain column order.
"""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# --- CSV defaults (consistent newlines & minimal quoting) ---
_CSV_DIALECT_KW = dict(quoting=csv.QUOTE_MINIMAL, lineterminator="\n")


def now_utc_iso() -> str:
    """Return current UTC time in ISO‑8601 without microseconds.

    Example: "2025-08-12T07:30:00+00:00"
    """

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    """Compute SHA‑256 hex digest of a file.

    Parameters
    ----------
    path : Path
        Path to the file to hash.
    """

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_session_dir(base_dir: Path, recording_id: str, annotator: str) -> Path:
    """Create and return a new session directory.

    Layout: ``<base_dir>/<recording_id>/<YYYYmmdd_HHMMSS>_<annotator>/``
    The directory is created if missing.
    """

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    sess = base_dir / recording_id / f"{ts}_{annotator}"
    sess.mkdir(parents=True, exist_ok=True)
    return sess


def write_session_header(session_dir: Path, header: Dict[str, Any]) -> None:
    """Append a session header row to ``session.csv``.

    If the file does not exist, a header line is written first. The order of
    columns follows the order of ``header`` keys (keep them stable upstream).
    """

    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / "session.csv"
    need_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(header.keys()), **_CSV_DIALECT_KW)
        if need_header:
            w.writeheader()
        w.writerow(header)


def write_cell_map(session_dir: Path, cell_map: List[Dict[str, Any]]) -> None:
    """Write (overwrite) ``cell_map.csv`` with rows of ``{"cell_index","cell_id"}``.

    This is written with a fixed schema to guarantee predictable column order.
    """

    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / "cell_map.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cell_index", "cell_id"], **_CSV_DIALECT_KW)
        w.writeheader()
        for row in cell_map:
            # Defensive cast to the expected schema
            w.writerow({"cell_index": row.get("cell_index"), "cell_id": row.get("cell_id")})


def append_labels(session_dir: Path, row: Dict[str, Any]) -> None:
    """Append a labeled‑cell row to ``labels.csv``.

    If the file does not exist, a header line is emitted first. The column order
    follows the incoming row's keys; call sites should keep key order stable.
    """

    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / "labels.csv"
    need_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()), **_CSV_DIALECT_KW)
        if need_header:
            w.writeheader()
        w.writerow(row)


def append_peaks(session_dir: Path, rows: List[Dict[str, Any]]) -> None:
    """Append multiple peak rows to ``peaks.csv`` (no‑op on empty list)."""

    if not rows:
        return
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / "peaks.csv"
    need_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), **_CSV_DIALECT_KW)
        if need_header:
            w.writeheader()
        for r in rows:
            w.writerow(r)
