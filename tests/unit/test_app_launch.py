from __future__ import annotations

from pathlib import Path

from opcal_mlt.app import launch


def test_parse_server_port_and_headless() -> None:
    args = launch._parse_args(["--headless", "--server.port", "8502"])

    assert args.headless is True
    assert args.server_port == 8502


def test_streamlit_args_use_entrypoint_and_browser_defaults(monkeypatch) -> None:
    fake_main = Path(__file__)
    args = launch._parse_args([])
    monkeypatch.setattr(launch, "_app_entrypoint", lambda: fake_main)

    result = launch._streamlit_args(args)

    assert result[:3] == ["streamlit", "run", str(fake_main)]
    assert "--server.headless=false" in result
    assert "--server.fileWatcherType=none" in result
    assert "--browser.gatherUsageStats=false" in result
    assert "--global.developmentMode=false" in result


def test_streamlit_args_accept_port(monkeypatch) -> None:
    fake_main = Path(__file__)
    args = launch._parse_args(["--server.port", "8503"])
    monkeypatch.setattr(launch, "_app_entrypoint", lambda: fake_main)

    result = launch._streamlit_args(args)

    assert "--server.port=8503" in result


def test_ensure_standard_streams_restores_missing_streams(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "launcher.log"
    original_handles = list(launch._STDIO_HANDLES)
    monkeypatch.setattr(launch, "_launcher_log_path", lambda: log_path)
    monkeypatch.setattr(launch.sys, "stdout", None)
    monkeypatch.setattr(launch.sys, "stderr", None)

    try:
        launch._ensure_standard_streams()

        assert launch.sys.stdout is not None
        assert launch.sys.stderr is not None
        assert log_path.exists()
    finally:
        for handle in launch._STDIO_HANDLES[len(original_handles) :]:
            handle.close()
        launch._STDIO_HANDLES[:] = original_handles
