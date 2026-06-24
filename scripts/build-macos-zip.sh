#!/usr/bin/env bash
set -euo pipefail

VERSION="$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"
NAME="OPCAL-MLT-${VERSION}-source-macOS"
OUT="dist/$NAME"

echo "→ Preparing $OUT"
rm -rf "$OUT" && mkdir -p "$OUT"

echo "→ Copying project files"
rsync -a \
  --exclude ".git" \
  --exclude ".github" \
  --exclude "dist" \
  --exclude "__pycache__" \
  --exclude ".pytest_cache" \
  --exclude "*.pyc" \
  README.md pyproject.toml \
  requirements.txt requirements-dev.txt environment.yml \
  docs/USER_GUIDE.md \
  src/ "$OUT/"

# Copy macOS launcher into bundle
mkdir -p "$OUT/scripts"
rsync -a scripts/OPCAL-Labeler.command "$OUT/scripts/"

echo "→ Ensuring launcher is executable"
chmod +x "$OUT/scripts/OPCAL-Labeler.command" || true

echo "→ Zipping"
( cd dist && rm -f "$NAME.zip" && zip -r "$NAME.zip" "$NAME" )

echo "✅ DONE: dist/$NAME.zip"
