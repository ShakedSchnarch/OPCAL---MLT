"""
Logging Service
===============

Provides lightweight file-based logging scoped to session folders.
Used for diagnostic and session-level event tracking.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


class Logger(Protocol):
    """
    Protocol for logging callable objects.

    Args:
        message (str): Log message to record.
    """
    def __call__(self, message: str) -> None:
        ...


class SessionLogger:
    """
    Logger that appends UTC timestamped lines to session.log in the session folder.

    Attributes:
        _session_dir (Path | None): Path to the session directory.
    """

    def __init__(self, session_dir: Path | None) -> None:
        """
        Initialize the session logger.

        Args:
            session_dir (Path | None): Path to the session directory.
        """
        self._session_dir = Path(session_dir) if session_dir else None

    def __call__(self, message: str) -> None:
        """
        Log a message to session.log with a UTC timestamp.

        Args:
            message (str): Log message to record.

        Notes:
            Silent failure is acceptable for diagnostic logging (no exception raised).
        """
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
