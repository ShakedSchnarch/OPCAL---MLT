#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN=${PYTHON_BIN:-python3}
command -v "$PYTHON_BIN" >/dev/null 2>&1 || { echo "[ERROR] Python 3.10+ not found"; exit 1; }
VENV=".opcal-venv"
[ -d "$VENV" ] || "$PYTHON_BIN" -m venv "$VENV"
# shellcheck source=/dev/null
source "$VENV/bin/activate"
python -m pip install --upgrade pip >/dev/null
python -m pip install -e .
exec python -m streamlit run src/opcal/app/main.py