#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3.12, then reopen this launcher."
  read -r -p "Press Enter to close..."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creating local Python environment..."
  python3 -m venv .venv
fi

source ".venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e .

echo "Launching OPCAL-Labeler..."
opcal-mlt
