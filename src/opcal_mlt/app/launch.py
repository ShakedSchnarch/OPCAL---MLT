"""
Launch script for the OPCAL-MLT Streamlit application.

This script serves as the entry point for running the Manual Labeling Tool locally.
It programmatically invokes the Streamlit CLI to run `main.py` in headless mode.
"""

import sys
from pathlib import Path
from streamlit.web.cli import main as st_main

def main() -> None:
    """
    Launch the Streamlit application for OPCAL-MLT.

    This function constructs the absolute path to the main application file,
    overrides `sys.argv` to mimic running `streamlit run main.py` from the CLI,
    and calls the Streamlit CLI main function in headless mode.
    """
    # Determine absolute path to the Streamlit app entry file
    app_path = str(Path(__file__).parent / "main.py")

    # Override sys.argv to mimic a CLI call: `streamlit run app_path --server.headless=true`
    sys.argv = ["streamlit", "run", app_path, "--server.headless=true"]

    # Invoke Streamlit's CLI main function
    st_main()

if __name__ == "__main__":
    main()
