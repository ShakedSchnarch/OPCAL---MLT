# OPCAL-MLT Distribution Playbook

This guide describes how to produce standalone builds of the Streamlit application
for macOS, Windows, and Linux with minimal impact on the main source tree.
All tooling lives under `tools/distribution` and writes artefacts into `dist/`.

## Recommended distribution paths

For non-technical annotators, ship native PyInstaller bundles as the primary
path. Source launchers are a fallback for developers or technical users only:

- **macOS:** build `OPCAL-MLT.app`, zip it as `OPCAL-MLT-<version>-macos.zip`,
  and sign/notarise it later if Gatekeeper becomes a blocker.
- **Windows:** build the onedir folder containing `OPCAL-MLT.exe`, zip it as
  `OPCAL-MLT-<version>-windows.zip`, and wrap it with Inno Setup/MSIX later if
  Start Menu shortcuts are needed.
- **Source ZIP fallback:** use `scripts/build-macos-zip.sh` only when users are
  comfortable letting the launcher create a local `.venv` and install Python
  dependencies on first run.

Build artefacts are platform-specific. Produce Windows builds on Windows and
macOS builds on macOS.

## 1. Prerequisites

- Python 3.12 (matches the runtime the app targets)
- An isolated virtual environment on the build host
- PyInstaller ≥ 6.3 (install via `pip install pyinstaller>=6.3`)
- Platform-specific packaging helpers (optional):
  - macOS: `create-dmg` for DMG wrapping, `codesign`/`notarytool` for signing
  - Windows: Inno Setup or MSIX Packaging Tool to generate installers
  - Linux: `zip` or `appimagetool` for AppImage bundles

> ℹ️ Build artefacts are not portable between operating systems. Run each build on
> the target platform (e.g. Windows binaries must be built from Windows).

## 2. Run from source on Windows

Use this path for internal QA before creating a standalone Windows installer.
Open **PowerShell** in the project root and run:

```powershell
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
python -m pip install -e .
opcal-mlt
```

If activation is blocked by the Windows execution policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

One-command local launch is also available. It performs an import/version sanity
check before launching and can rebuild `.venv` explicitly:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\OPCAL-Labeler.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\OPCAL-Labeler.ps1 --rebuild
```

For developer validation on Windows:

```powershell
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m pytest
```

## 3. Running the builder script

All platforms share the same entry point:

```bash
python tools/distribution/build.py --clean
```

The script auto-detects the host platform, prepares `build/pyinstaller/<platform>/`
for temporary files, and writes outputs to `dist/executables/<platform>/`.

Common flags:

- `--clean` – wipe previous build artefacts before assembling a new bundle
- `--name <NAME>` – customise the executable/bundle name (defaults to `OPCAL-MLT`)
- `--collect-all` – force PyInstaller to collect data files for additional
  dependencies. Use this if you notice missing assets or runtime import errors.
- `--icon <PATH>` – set a custom icon (`.icns` on macOS, `.ico` on Windows).
- `--no-zip` – leave only the raw PyInstaller output and skip the release ZIP.
- `--console` – build a QA executable that prints `--version`, `--diagnostics`,
  and crash traces to the terminal. Do not use this for the final end-user ZIP.

The script always builds `onedir` output and, by default, creates a versioned ZIP
next to the raw artefact. If PyInstaller is missing, the script exits with a
descriptive message.

## 3A. Building Windows From GitHub

The recommended way to produce the Windows ZIP is the `release-builds` GitHub
Actions workflow because it runs on a real Windows host.

1. Push the release branch or tag to GitHub.
2. Open the repository on GitHub.
3. Go to **Actions** → **release-builds**.
4. Click **Run workflow** and choose the branch.
5. Wait for the **Windows executable ZIP** job to finish.
6. Download the `OPCAL-MLT-windows` artifact.
7. Inside the artifact, use `OPCAL-MLT-<version>-windows.zip` as the file to
   send to Windows users.

The workflow first builds `OPCAL-MLT-QA.exe` with a visible console and smoke
tests `--version`, `--diagnostics`, and `http://localhost:8765`. Only after that
does it build the final windowed `OPCAL-MLT.exe` ZIP.

## 4. Platform-specific notes

### macOS

1. Activate the build virtualenv and install PyInstaller.
2. Run `python tools/distribution/build.py --clean --icon path/to/logo.icns`.
3. The result is `dist/executables/macos/OPCAL-MLT.app` plus
   `dist/executables/macos/OPCAL-MLT-<version>-macos.zip`.
4. Optional post-processing:
   - Sign: `codesign --deep --force --sign "Developer ID Application: ..." OPCAL-MLT.app`
   - Notarise (for distribution outside the team) via `xcrun notarytool`.
   - Wrap into a DMG: `create-dmg dist/executables/macos/OPCAL-MLT.dmg OPCAL-MLT.app`.

### Windows

1. Install PyInstaller in a virtualenv (`py -m pip install pyinstaller>=6.3`).
2. First build a console QA executable so diagnostics are visible in PowerShell:
   ```powershell
   py tools\distribution\build.py --clean --console --name OPCAL-MLT-QA
   .\dist\executables\windows\OPCAL-MLT-QA\OPCAL-MLT-QA.exe --version
   .\dist\executables\windows\OPCAL-MLT-QA\OPCAL-MLT-QA.exe --diagnostics
   .\dist\executables\windows\OPCAL-MLT-QA\OPCAL-MLT-QA.exe --headless --server.port 8765
   ```
3. In another PowerShell window, verify the server:
   ```powershell
   Invoke-WebRequest -UseBasicParsing http://localhost:8765 | Select-Object -ExpandProperty StatusCode
   ```
   Stop the QA server with `Ctrl+C`.
4. Provide a `.ico` icon if desired and build the final windowed release:
   ```powershell
   py tools/distribution/build.py --clean --icon path\to\logo.ico
   ```
5. PyInstaller writes an unpacked folder: `dist/executables/windows/OPCAL-MLT/`
   containing `OPCAL-MLT.exe`, plus
   `dist/executables/windows/OPCAL-MLT-<version>-windows.zip`.
6. Package options:
   - Compress the folder into a ZIP for quick sharing.
   - Use Inno Setup/MSIX to create an installer that adds Start Menu shortcuts.

### Linux

1. Install PyInstaller (`pip install pyinstaller>=6.3`).
2. Run the builder: `python tools/distribution/build.py --clean`.
3. The onedir bundle lives at `dist/executables/linux/OPCAL-MLT/`.
4. Suggested distribution formats:
   - Tarball: `tar -czf OPCAL-MLT-linux.tar.gz OPCAL-MLT`
   - AppImage (optional): wrap the output using `appimagetool`.

## 5. Verifying builds

After each build:

- Launch the binary/bundle and confirm Streamlit serves the UI.
- Trigger the full annotation flow with sample data to ensure filesystem writes work.
- Verify both export buttons:
  - full session ZIP contains session provenance files,
  - training ZIP contains only class-wise CSVs.
- Inspect `logs/` or console output for missing module warnings.

For automated smoke tests, call the generated executable with launcher flags:

```bash
./dist/executables/linux/OPCAL-MLT/OPCAL-MLT --version
./dist/executables/linux/OPCAL-MLT/OPCAL-MLT --diagnostics
./dist/executables/linux/OPCAL-MLT/OPCAL-MLT --headless --server.port 8502
```

Use the platform-appropriate path (e.g. `OPCAL-MLT.app/Contents/MacOS/OPCAL-MLT` on macOS).

## 6. Release checklist additions

Augment the existing release checklist in `README.md` with the following steps when
publishing binaries:

1. Build per-platform bundles using `tools/distribution/build.py` on the native host.
2. Smoke-test each build with representative datasets.
3. Keep the generated ZIP for internal distribution; optionally package as
   DMG/MSI and sign/notarise later.
4. Upload artefacts to the Git tag release alongside the changelog entry.
5. Document any platform-specific caveats in the release notes.

## 7. Keeping assets external

The build script copies runtime assets (`src/opcal_mlt/app/assets` and
`src/opcal_mlt/app/config`) directly into the bundle. Additional files can be
bundled without modifying the application code by passing extra `--add-data`
arguments:

```bash
python tools/distribution/build.py --add-data "extra/path:relative/target"
```

(Use `;` instead of `:` when running on Windows.) Extend the script or wrap it in
platform-specific shell/PowerShell scripts if you need to automate more steps
without touching the main codebase.

## 8. Next steps

- Automate builds via CI runners (GitHub Actions, Azure DevOps) on macOS, Windows,
  and Linux to generate artefacts for every tagged release.
- Integrate installer creation (DMG/EXE/AppImage) into the CI workflow after
  validating manual builds.
- Optionally add checksum generation and artifact signing for provenance.
