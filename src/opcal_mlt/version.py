"""Version helpers for OPCAL-MLT."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

FALLBACK_VERSION = "1.1.1"


def get_app_version() -> str:
    """Return the installed package version with a source-tree fallback."""

    try:
        return version("opcal-mlt")
    except PackageNotFoundError:
        return FALLBACK_VERSION


__all__ = ["FALLBACK_VERSION", "get_app_version"]
