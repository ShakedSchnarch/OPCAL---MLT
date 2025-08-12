#!/usr/bin/env bash
# OPCAL-Labeler launcher (macOS)
# Creates/uses a local virtual environment in .opcal-venv,
# installs the project in editable mode, and starts the Streamlit app.
# Requirements: Python 3.10+ available on PATH.

set -Eeuo pipefail
trap 'echo "[ERROR] Launcher failed. See logs above." >&2' ERR

# Work from the script's directory (supports double-click from Finder)
cd "$(dirname "$0")"

# Resolve Python binary (allow override via env var)
PYTHON_BIN=${PYTHON_BIN:-python3}
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] Python 3.10+ not found on PATH. Please install Python and retry." >&2
  exit 1
fi

# Verify Python version >= 3.10
PY_VER=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
MAJOR=${PY_VER%%.*}
MINOR=${PY_VER##*.}
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
  echo "[ERROR] Python 3.10+ required (found $PY_VER)." >&2
  exit 1
fi

# Create/activate virtual environment
VENV=".opcal-venv"
if [ ! -d "$VENV" ]; then
  echo "[INFO] Creating virtual environment in $VENV ..."
  "$PYTHON_BIN" -m venv "$VENV"
fi
# shellcheck source=/dev/null
source "$VENV/bin/activate"

# Install/upgrade project locally
python -m pip install --upgrade pip >/dev/null
python -m pip install -e .

# Launch the app
exec python -m streamlit run app/main.py