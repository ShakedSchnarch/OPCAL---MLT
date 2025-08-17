from pathlib import Path
import subprocess
import sys

def main():
    target = Path(__file__).with_name("app.py")
    cmd = [sys.executable, "-m", "streamlit", "run", str(target)]
    raise SystemExit(subprocess.call(cmd))
