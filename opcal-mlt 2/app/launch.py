
import sys
from pathlib import Path
from streamlit.web.cli import main as st_main

def main():
    app_path = str(Path(__file__).parent / "main.py")
    sys.argv = ["streamlit", "run", app_path, "--server.headless=true"]
    st_main()

if __name__ == "__main__":
    main()
