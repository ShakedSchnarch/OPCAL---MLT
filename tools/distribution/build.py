#!/usr/bin/env python3
"""Utility for producing standalone OPCAL-MLT binaries via PyInstaller.

The script keeps build artefacts under ``dist/executables`` and avoids
modifying the core source tree beyond transient build folders.

Usage examples
--------------

Build for the current platform (auto-detected):
    python tools/distribution/build.py

Build for Windows from a Windows host, with a custom icon and output location:
    python tools/distribution/build.py --platform windows --icon path/to/icon.ico \
        --output C:/releases/opcal-mlt

The script expects PyInstaller (>=6.3) to be installed in the active environment
and surfaces actionable errors when prerequisites are missing.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import sys
from pathlib import Path
from textwrap import dedent

try:
    import PyInstaller.__main__ as PYINSTALLER  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - defer error handling to runtime
    PYINSTALLER = None

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIST_DIR = REPO_ROOT / "dist" / "executables"
DEFAULT_BUILD_DIR = REPO_ROOT / "build" / "pyinstaller"
ENTRYPOINT = REPO_ROOT / "src" / "opcal_mlt" / "app" / "launch.py"
ASSETS_DIR = REPO_ROOT / "src" / "opcal_mlt" / "app" / "assets"
CONFIG_DIR = REPO_ROOT / "src" / "opcal_mlt" / "app" / "config"

SUPPORTED_PLATFORMS = {"macos": "darwin", "windows": "win32", "linux": "linux"}


def _detect_platform() -> str:
    current = sys.platform
    for name, token in SUPPORTED_PLATFORMS.items():
        if current.startswith(token):
            return name
    raise SystemExit(f"Unsupported build host platform: {current}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build distributable binaries for OPCAL-MLT via PyInstaller",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--platform",
        choices=sorted(SUPPORTED_PLATFORMS.keys()),
        default=None,
        help="Target platform; defaults to the current host platform",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Directory to place the final PyInstaller dist folder",
    )
    parser.add_argument(
        "--work",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help="Working directory for PyInstaller build artefacts",
    )
    parser.add_argument(
        "--icon",
        type=Path,
        default=None,
        help="Optional icon file (.ico on Windows, .icns on macOS)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing build/dist directories before running",
    )
    parser.add_argument(
        "--name",
        default="OPCAL-MLT",
        help="Base name for the generated executable or bundle",
    )
    parser.add_argument(
        "--collect-all",
        action="store_true",
        help="Collect data/submodules for all first-party dependencies (slower, safer)",
    )
    parser.add_argument(
        "--add-data",
        action="append",
        default=[],
        metavar="SRC{sep}DEST",
        help=(
            "Extra PyInstaller --add-data mappings. Use ':' on POSIX and ';' on Windows. "
            "Repeat the flag for multiple entries."
        ).replace("{sep}", os.pathsep),
    )
    return parser.parse_args()


def _resolve_dist_base(target: Path | None, platform_key: str) -> Path:
    base = target or (DEFAULT_DIST_DIR / platform_key)
    base.mkdir(parents=True, exist_ok=True)
    return base


def _cleanup(paths: list[Path]) -> None:
    for path in paths:
        if path.exists():
            shutil.rmtree(path)


def _build(platform_key: str, args: argparse.Namespace) -> None:
    if PYINSTALLER is None:
        raise SystemExit(
            dedent(
                """
                PyInstaller is required but not installed.
                Install it in your build environment, e.g. `pip install pyinstaller>=6.3`.
                """
            ).strip()
        )

    dist_base = _resolve_dist_base(args.output, platform_key)
    work_dir = args.work / platform_key
    spec_dir = work_dir / "spec"

    work_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)

    if args.clean:
        _cleanup([dist_base, work_dir])
        dist_base.mkdir(parents=True, exist_ok=True)
        work_dir.mkdir(parents=True, exist_ok=True)
        spec_dir.mkdir(parents=True, exist_ok=True)

    if not ENTRYPOINT.exists():
        raise SystemExit(f"Entrypoint not found: {ENTRYPOINT}")

    datas = [
        f"{ASSETS_DIR}{os.pathsep}opcal_mlt/app/assets",
        f"{CONFIG_DIR}{os.pathsep}opcal_mlt/app/config",
    ]

    pyinstaller_args: list[str] = [
        str(ENTRYPOINT),
        "--name",
        args.name,
        "--noconfirm",
        "--clean",
        "--windowed",
        "--distpath",
        str(dist_base),
        "--workpath",
        str(work_dir / "build"),
        "--specpath",
        str(spec_dir),
    ]

    for data_arg in datas:
        pyinstaller_args.extend(["--add-data", data_arg])

    for extra_data in args.add_data:
        pyinstaller_args.extend(["--add-data", extra_data])

    hidden_imports = [
        "streamlit.web.cli",
        "streamlit.web.bootstrap",
        "streamlit.web.server.server",
        "streamlit.runtime.caching",
    ]
    for hidden in hidden_imports:
        pyinstaller_args.extend(["--hidden-import", hidden])

    if args.collect_all:
        collect_targets = [
            "streamlit",
            "altair",
            "pydeck",
            "plotly",
            "matplotlib",
        ]
        for target in collect_targets:
            pyinstaller_args.extend(["--collect-all", target])
    else:
        pyinstaller_args.extend(["--collect-data", "streamlit"])
        pyinstaller_args.extend(["--collect-submodules", "streamlit"])

    if args.icon:
        icon_path = args.icon.resolve()
        if not icon_path.exists():
            raise SystemExit(f"Icon file not found: {icon_path}")
        if platform_key == "windows" and icon_path.suffix.lower() != ".ico":
            raise SystemExit("Windows builds require a .ico icon file")
        if platform_key == "macos" and icon_path.suffix.lower() != ".icns":
            raise SystemExit("macOS builds require an .icns icon file")
        pyinstaller_args.extend(["--icon", str(icon_path)])

    if platform_key != "windows":
        # Hide the terminal window on POSIX by default
        pyinstaller_args.append("--noconsole")

    print("→ Running PyInstaller with arguments:\n  " + "\n  ".join(pyinstaller_args))
    PYINSTALLER.run(pyinstaller_args)

    if platform_key == "windows":
        artefact_dir = dist_base / args.name
    elif platform_key == "macos":
        artefact_dir = dist_base / f"{args.name}.app"
    else:
        artefact_dir = dist_base / args.name

    if not artefact_dir.exists():
        print(
            "⚠️  PyInstaller finished without creating the expected artefact. "
            "Check the logs above for errors.",
            file=sys.stderr,
        )
    else:
        print(f"✅ Build complete: {artefact_dir}")


def main() -> None:
    args = _parse_args()
    host_platform = _detect_platform()
    target_platform = args.platform or host_platform

    if target_platform != host_platform:
        raise SystemExit(
            "Cross-compiling is not supported. Run this script on the target platform."
        )

    print(f"Building OPCAL-MLT for {target_platform} (host: {platform.system().lower()})")
    _build(target_platform, args)


if __name__ == "__main__":
    main()
