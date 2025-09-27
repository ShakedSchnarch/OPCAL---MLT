from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from opcal_mlt.app.session_io import append_labels, write_cell_map
from opcal_mlt.domain.models import SessionConfig
from opcal_mlt.services.sessions import SessionService


@pytest.fixture
def session_service():
    return SessionService()


@pytest.fixture
def session_config(tmp_path):
    return SessionConfig(annotator_id="ann", save_root=tmp_path, created_at=datetime.now(timezone.utc))


def test_start_creates_session_dir(session_service, session_config):
    ctx = session_service.start(session_config, recording_id="rec1")
    assert ctx.paths.session_dir.exists()
    # session.csv should exist with at least one row
    session_csv = ctx.paths.session_dir / "session.csv"
    assert session_csv.exists()
    df = pd.read_csv(session_csv)
    assert not df.empty


def test_hydrate_labels_empty_when_missing(session_service, session_config):
    ctx = session_service.start(session_config, recording_id="rec2")
    assert session_service.hydrate_labels(ctx.paths.session_dir) == {}


def test_hydrate_labels_returns_map(session_service, session_config):
    ctx = session_service.start(session_config, recording_id="rec3")
    append_labels(
        ctx.paths.session_dir,
        {
            "session_id": ctx.paths.session_dir.name,
            "recording_id": "rec3",
            "annotator_id": "ann",
            "saved_utc": datetime.now(timezone.utc).isoformat(),
            "cell_index": 0,
            "cell_id": "cell_000",
            "label": "Oscillatory",
            "uncertain": False,
            "notes": "",
            "filter_type": "none",
            "filter_window": 0,
            "filter_polyorder": 0,
            "baseline_method": "rolling_median",
            "baseline_window_s_or_q": 20.0,
            "sd_method": "MAD",
            "threshold_k": 3.0,
            "mean": 0.0,
            "std": 0.0,
            "rms": 0.0,
            "frac_above_thr": 0.0,
            "peaks_per_min": 0.0,
            "version": "mlt-test",
        },
    )
    label_map = session_service.hydrate_labels(ctx.paths.session_dir)
    assert 0 in label_map
    assert label_map[0].label.value == "Oscillatory"


def test_list_resumable_sessions_orders_by_mtime(session_service, session_config, tmp_path):
    ctx1 = session_service.start(session_config, recording_id="recA")
    append_labels(
        ctx1.paths.session_dir,
        {
            "session_id": ctx1.paths.session_dir.name,
            "recording_id": "recA",
            "annotator_id": "ann",
            "saved_utc": datetime.now(timezone.utc).isoformat(),
            "cell_index": 0,
            "cell_id": "cell_000",
            "label": "Oscillatory",
            "uncertain": False,
            "notes": "",
            "filter_type": "none",
            "filter_window": 0,
            "filter_polyorder": 0,
            "baseline_method": "rolling_median",
            "baseline_window_s_or_q": 20.0,
            "sd_method": "MAD",
            "threshold_k": 3.0,
            "mean": 0.0,
            "std": 0.0,
            "rms": 0.0,
            "frac_above_thr": 0.0,
            "peaks_per_min": 0.0,
            "version": "mlt-test",
        },
    )
    ctx2 = session_service.start(session_config, recording_id="recB")
    append_labels(
        ctx2.paths.session_dir,
        {
            "session_id": ctx2.paths.session_dir.name,
            "recording_id": "recB",
            "annotator_id": "ann",
            "saved_utc": datetime.now(timezone.utc).isoformat(),
            "cell_index": 0,
            "cell_id": "cell_000",
            "label": "Oscillatory",
            "uncertain": False,
            "notes": "",
            "filter_type": "none",
            "filter_window": 0,
            "filter_polyorder": 0,
            "baseline_method": "rolling_median",
            "baseline_window_s_or_q": 20.0,
            "sd_method": "MAD",
            "threshold_k": 3.0,
            "mean": 0.0,
            "std": 0.0,
            "rms": 0.0,
            "frac_above_thr": 0.0,
            "peaks_per_min": 0.0,
            "version": "mlt-test",
        },
    )
    summaries = session_service.list_resumable_sessions(session_config.save_root)
    assert summaries
    assert summaries[0].session_dir in {ctx1.paths.session_dir, ctx2.paths.session_dir}


def test_load_session_returns_metadata(session_service, session_config):
    ctx = session_service.start(session_config, recording_id="recMeta")
    write_cell_map(
        ctx.paths.session_dir,
        [
            {"cell_index": 0, "cell_id": "cell_000"},
            {"cell_index": 1, "cell_id": "cell_001"},
        ],
    )
    loaded = session_service.load_session(ctx.paths.session_dir)
    assert loaded.metadata.get("session_id") == ctx.paths.session_dir.name
    assert loaded.cell_ids == ["cell_000", "cell_001"]
