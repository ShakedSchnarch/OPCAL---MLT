# OPCAL-MLT Build Log

## 2026-06-24 - v1.2.0 macOS local verification

Host:
- macOS 26.5.1 arm64
- Python 3.12.11
- Clean venv: `/private/tmp/opcal_mlt_clean_venv_120`
- PyInstaller 6.21.0

Commands verified:
- `python -m pip install -e ".[dev]"`
- `opcal-mlt --version` -> `1.2.0`
- `opcal-mlt --diagnostics` -> found source `main.py` and theme config
- `python -m pip check` -> no broken requirements
- `python -m pytest` -> 45 passed
- `python -m ruff check src tests tools` -> passed
- `python -m black --target-version py312 --check` on changed Python files -> passed
- `python tools/distribution/build.py` -> built macOS app and ZIP

macOS artifact:
- `dist/executables/macos/OPCAL-MLT.app`
- `dist/executables/macos/OPCAL-MLT-1.2.0-macos.zip` (246 MB)

Packaged app smoke:
- `OPCAL-MLT --version` -> `1.2.0`
- `OPCAL-MLT --diagnostics` -> frozen mode true, Streamlit 1.58.0, bundled `main.py` present, bundled theme config present
- `OPCAL-MLT --headless --server.port 8765` -> Uvicorn started on localhost
- `curl -I http://localhost:8765` -> `HTTP/1.1 200 OK`

Notes:
- The first macOS bundle attempt exposed missing Streamlit metadata; the builder now copies metadata for `opcal-mlt` and `streamlit`.
- A later macOS bundle attempt exposed an empty `Contents/Resources/base_library.zip`; the builder now repairs that file from PyInstaller's build output if needed and clears extended attributes before zipping.
- Windows QA should first use `python tools\distribution\build.py --clean --console --name OPCAL-MLT-QA` so `--version`, `--diagnostics`, and runtime exceptions are visible in PowerShell. The final user ZIP should be built without `--console`.
- Native Windows build and smoke must still be run on a Windows host.
