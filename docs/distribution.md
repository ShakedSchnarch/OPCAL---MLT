# OPCAL-MLT Distribution Playbook

This guide describes how to produce standalone builds of the Streamlit application
for macOS, Windows, and Linux with minimal impact on the main source tree.
All tooling lives under `tools/distribution` and writes artefacts into `dist/`.

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

## 2. Running the builder script

All platforms share the same entry point:

```bash
python tools/distribution/build.py
```

The script auto-detects the host platform, prepares `build/pyinstaller/<platform>/`
for temporary files, and writes outputs to `dist/executables/<platform>/`.

Common flags:

- `--clean` – wipe previous build artefacts before assembling a new bundle
- `--name <NAME>` – customise the executable/bundle name (defaults to `OPCAL-MLT`)
- `--collect-all` – force PyInstaller to collect data files for additional
  dependencies. Use this if you notice missing assets or runtime import errors.
- `--icon <PATH>` – set a custom icon (`.icns` on macOS, `.ico` on Windows).

If PyInstaller is missing, the script exits with a descriptive message.

## 3. Platform-specific notes

### macOS

1. Activate the build virtualenv and install PyInstaller.
2. Run `python tools/distribution/build.py --clean --icon path/to/logo.icns`.
3. The result is `dist/executables/macos/OPCAL-MLT.app`.
4. Optional post-processing:
   - Sign: `codesign --deep --force --sign "Developer ID Application: ..." OPCAL-MLT.app`
   - Notarise (for distribution outside the team) via `xcrun notarytool`.
   - Wrap into a DMG: `create-dmg dist/executables/macos/OPCAL-MLT.dmg OPCAL-MLT.app`.

### Windows

1. Install PyInstaller in a virtualenv (`py -m pip install pyinstaller>=6.3`).
2. Provide a `.ico` icon if desired and run:
   ```powershell
   py tools/distribution/build.py --clean --icon path\to\logo.ico
   ```
3. PyInstaller writes an unpacked folder: `dist/executables/windows/OPCAL-MLT/` containing `OPCAL-MLT.exe`.
4. Package options:
   - Compress the folder into a ZIP for quick sharing.
   - Use Inno Setup/MSIX to create an installer that adds Start Menu shortcuts.

### Linux

1. Install PyInstaller (`pip install pyinstaller>=6.3`).
2. Run the builder: `python tools/distribution/build.py --clean`.
3. The onedir bundle lives at `dist/executables/linux/OPCAL-MLT/`.
4. Suggested distribution formats:
   - Tarball: `tar -czf OPCAL-MLT-linux.tar.gz OPCAL-MLT`
   - AppImage (optional): wrap the output using `appimagetool`.

## 4. Verifying builds

After each build:

- Launch the binary/bundle and confirm Streamlit serves the UI.
- Trigger the full annotation flow with sample data to ensure filesystem writes work.
- Inspect `logs/` or console output for missing module warnings.

For automated smoke tests, call the generated executable with Streamlit's headless flag:

```bash
./dist/executables/linux/OPCAL-MLT/OPCAL-MLT --server.headless true --help
```

Use the platform-appropriate path (e.g. `OPCAL-MLT.app/Contents/MacOS/OPCAL-MLT` on macOS).

## 5. Release checklist additions

Augment the existing release checklist in `README.md` with the following steps when
publishing binaries:

1. Build per-platform bundles using `tools/distribution/build.py` on the native host.
2. Smoke-test each build with representative datasets.
3. Package (ZIP/DMG/MSI) and, if required, sign/notarise the deliverables.
4. Upload artefacts to the Git tag release alongside the changelog entry.
5. Document any platform-specific caveats in the release notes.

## 6. Keeping assets external

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

## 7. Next steps

- Automate builds via CI runners (GitHub Actions, Azure DevOps) on macOS, Windows,
  and Linux to generate artefacts for every tagged release.
- Integrate installer creation (DMG/EXE/AppImage) into the CI workflow after
  validating manual builds.
- Optionally add checksum generation and artifact signing for provenance.
