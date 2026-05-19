"""
Application Launcher
===================

Entry point for running the OPCAL-MLT Streamlit application locally.
Programmatically invokes the Streamlit CLI to run `main.py` in headless mode.
"""
from __future__ import annotations
import importlib.resources as pkg_resources
import sys
from pathlib import Path

from streamlit.web.cli import main as st_main

def _ensure_streamlit_config() -> None:
    """
    Ensure a Streamlit config.toml exists so the app theme is consistent.

    If ./.streamlit doesn't exist, fall back to ~/.streamlit.
    """
    try:
        cwd_cfg = Path(".streamlit") / "config.toml"
        home_cfg = Path.home() / ".streamlit" / "config.toml"
        target = cwd_cfg if cwd_cfg.parent.exists() else home_cfg
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with pkg_resources.files("opcal_mlt.app.config").joinpath("streamlit_theme.toml").open("rb") as r, target.open("wb") as w:
                w.write(r.read())
    except Exception:
        # Non-fatal: continue without copying if something goes wrong
        pass

def main() -> None:
    """
    Launch the Streamlit application for OPCAL-MLT.

    Constructs the absolute path to the main application file,
    overrides `sys.argv` to mimic running `streamlit run main.py` from the CLI,
    and calls the Streamlit CLI main function in headless mode.
    """
    _ensure_streamlit_config()
    # Determine absolute path to the Streamlit app entry file
    app_path = str(Path(__file__).parent / "main.py")

    # Override sys.argv to mimic a CLI call for a local end-user launch.
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.headless=true",
        "--server.fileWatcherType=none",
    ]

    # Invoke Streamlit's CLI main function
    st_main()

if __name__ == "__main__":
    main()
