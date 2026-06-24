"""Command-line launcher for the OPCAL-MLT Streamlit application."""

from __future__ import annotations

import argparse
import importlib.resources as pkg_resources
import sys
from pathlib import Path

from opcal_mlt.version import get_app_version


def _is_frozen() -> bool:
    """Return True when running from a PyInstaller bundle."""

    return bool(getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None))


def _bundle_app_root() -> Path:
    """Return the directory that contains bundled app resources."""

    if _is_frozen():
        return Path(getattr(sys, "_MEIPASS")) / "opcal_mlt" / "app"
    return Path(__file__).resolve().parent


def _resource_path(*parts: str) -> Path:
    """Resolve an app resource path in source and frozen modes."""

    return _bundle_app_root().joinpath(*parts)


def _app_entrypoint() -> Path:
    """Return the physical Streamlit script path."""

    return _resource_path("main.py")


def _ensure_streamlit_config() -> None:
    """Ensure a Streamlit config.toml exists so the app theme is consistent.

    If ./.streamlit doesn't exist, fall back to ~/.streamlit.
    """
    try:
        cwd_cfg = Path(".streamlit") / "config.toml"
        home_cfg = Path.home() / ".streamlit" / "config.toml"
        target = cwd_cfg if cwd_cfg.parent.exists() else home_cfg
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            bundled_config = _resource_path("config", "streamlit_theme.toml")
            if bundled_config.exists():
                target.write_bytes(bundled_config.read_bytes())
                return
            with (
                pkg_resources.files("opcal_mlt.app.config")
                .joinpath("streamlit_theme.toml")
                .open("rb") as r,
                target.open("wb") as w,
            ):
                w.write(r.read())
    except Exception:
        # Non-fatal: continue without copying if something goes wrong
        pass


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="opcal-mlt",
        description="Launch the OPCAL-MLT local labeling application.",
    )
    parser.add_argument(
        "--version", action="store_true", help="Print the app version and exit."
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Print launcher diagnostics and exit.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Do not open a browser automatically.",
    )
    parser.add_argument(
        "--server.port",
        dest="server_port",
        type=int,
        default=None,
        help="Port for the local Streamlit server.",
    )
    return parser.parse_args(argv)


def _print_diagnostics() -> None:
    """Print a compact launch environment report."""

    try:
        import streamlit as st

        streamlit_version = st.__version__
    except Exception as exc:  # pragma: no cover - depends on local environment
        streamlit_version = f"unavailable ({type(exc).__name__}: {exc})"

    app_path = _app_entrypoint()
    config_path = _resource_path("config", "streamlit_theme.toml")
    lines = {
        "opcal_mlt_version": get_app_version(),
        "streamlit_version": streamlit_version,
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "frozen": str(_is_frozen()).lower(),
        "app_entrypoint": str(app_path),
        "app_entrypoint_exists": str(app_path.exists()).lower(),
        "theme_config": str(config_path),
        "theme_config_exists": str(config_path.exists()).lower(),
    }
    for key, value in lines.items():
        print(f"{key}: {value}")


def _streamlit_args(args: argparse.Namespace) -> list[str]:
    app_path = _app_entrypoint()
    if not app_path.exists():
        raise SystemExit(f"Streamlit entrypoint not found: {app_path}")

    st_args = [
        "streamlit",
        "run",
        str(app_path),
        f"--server.headless={'true' if args.headless else 'false'}",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
    ]
    if args.server_port is not None:
        st_args.append(f"--server.port={args.server_port}")
    return st_args


def main(argv: list[str] | None = None) -> None:
    """Launch the Streamlit application for OPCAL-MLT."""

    args = _parse_args(argv)
    if args.version:
        print(get_app_version())
        return
    if args.diagnostics:
        _print_diagnostics()
        return

    _ensure_streamlit_config()
    sys.argv = _streamlit_args(args)
    from streamlit.web.cli import main as st_main

    st_main()


if __name__ == "__main__":
    main()
