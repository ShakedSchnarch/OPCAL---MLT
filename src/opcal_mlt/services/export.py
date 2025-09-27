"""
Export Service
==============

Provides utilities for exporting session data, including creating ZIP archives for sharing or backup.
"""
from __future__ import annotations

import shutil
from pathlib import Path


class ExportService:
    """
    Service for exporting session data as ZIP archives.

    Methods:
        export_session: Creates a ZIP archive of a session directory for sharing or backup.
    """

    def export_session(self, session_dir: Path) -> Path:
        """
        Create a ZIP archive of the given session directory.

        Args:
            session_dir (Path): Path to the session directory to archive.

        Returns:
            Path: Path to the created ZIP archive.

        Raises:
            FileNotFoundError: If the session directory does not exist.
        """
        session_dir = Path(session_dir)
        if not session_dir.exists():
            raise FileNotFoundError(f"Session directory not found: {session_dir}")
        zip_base = session_dir.parent / session_dir.name
        archive_path = shutil.make_archive(str(zip_base), "zip", root_dir=session_dir)
        return Path(archive_path)


__all__ = ["ExportService"]
