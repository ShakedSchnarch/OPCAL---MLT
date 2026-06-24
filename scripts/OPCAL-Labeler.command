#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
REBUILD="${1:-}"

find_python() {
  if command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  return 1
}

test_local_install() {
  [ -x ".venv/bin/python" ] || return 1
  ".venv/bin/python" -c "import opcal_mlt; from opcal_mlt.version import get_app_version; raise SystemExit(0 if get_app_version() == '1.2.0' else 1)" >/dev/null 2>&1
}

PYTHON_BIN="$(find_python || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "Python 3.12 is required. Install it from python.org, then reopen this launcher."
  read -r -p "Press Enter to close..."
  exit 1
fi

if [ "$REBUILD" = "--rebuild" ] && [ -d ".venv" ]; then
  echo "Removing local Python environment..."
  rm -rf ".venv"
fi

if [ ! -d ".venv" ]; then
  echo "Creating local Python environment..."
  "$PYTHON_BIN" -m venv .venv
fi

if ! test_local_install; then
  echo "Installing/updating OPCAL-MLT dependencies..."
  ".venv/bin/python" -m pip install --upgrade pip setuptools wheel
  ".venv/bin/python" -m pip install -e .
fi

if ! test_local_install; then
  echo
  echo "The local .venv exists but OPCAL-MLT still cannot be imported correctly."
  echo "Run this launcher again with --rebuild to recreate .venv from scratch:"
  echo "./scripts/OPCAL-Labeler.command --rebuild"
  read -r -p "Press Enter to close..."
  exit 1
fi

echo "Launching OPCAL-Labeler..."
".venv/bin/opcal-mlt"
