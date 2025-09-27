"""Export utilities (ZIP bundles, manifest helpers)."""
from __future__ import annotations

import shutil
from pathlib import Path


class ExportService:
    """Create archives for sharing or backup."""

    def export_session(self, session_dir: Path) -> Path:
        session_dir = Path(session_dir)
        if not session_dir.exists():
            raise FileNotFoundError(f"Session directory not found: {session_dir}")
        zip_base = session_dir.parent / session_dir.name
        archive_path = shutil.make_archive(str(zip_base), "zip", root_dir=session_dir)
        return Path(archive_path)


__all__ = ["ExportService"]
