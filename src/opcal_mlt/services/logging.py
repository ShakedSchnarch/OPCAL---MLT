"""Lightweight file-based logging scoped to session folders."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


class Logger(Protocol):
    def __call__(self, message: str) -> None:  # pragma: no cover - protocol signature
        ...


class SessionLogger:
    """Append UTC timestamped lines to ``session.log`` if the folder exists."""

    def __init__(self, session_dir: Path | None) -> None:
        self._session_dir = Path(session_dir) if session_dir else None

    def __call__(self, message: str) -> None:
        if not self._session_dir:
            return
        try:
            path = self._session_dir / "session.log"
            path.parent.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            with path.open("a", encoding="utf-8") as fh:
                fh.write(f"{ts} | {message}\n")
        except Exception:
            # Silent failure is acceptable for diagnostic logging.
            return


__all__ = ["Logger", "SessionLogger"]
