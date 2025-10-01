import numpy as np

from opcal_mlt.app import state_store
from opcal_mlt.domain.enums import Stage


def test_save_and_load_snapshot_roundtrip(tmp_path):
    root = tmp_path / "session"
    root.mkdir()
    traces = np.arange(12).reshape(3, 4)
    state = {
        "annotator": "alice",
        "stage": Stage.WORKSPACE,
        "recording_id": "rec42",
        "current_cell": 7,
        "label_map": {1: {"label": "Oscillatory", "notes": "ok", "uncertain": False}},
        "history": [(1, None)],
        "cell_ids": ["cell_00001", "cell_00002"],
        "traces": traces,
    }

    state_store.save_snapshot(root, state)
    snapshot = state_store.load_snapshot(root)
    assert snapshot is not None
    assert snapshot.data["annotator"] == "alice"
    assert snapshot.data["stage"] == Stage.WORKSPACE
    assert snapshot.data["label_map"][1]["label"] == "Oscillatory"
    assert snapshot.data["history"] == [(1, None)]
    np.testing.assert_array_equal(snapshot.traces, traces)


def test_persist_state_for_token_writes_cache_and_session(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache"
    monkeypatch.setattr(state_store, "CACHE_ROOT", cache_root, raising=False)
    token = "token123"
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    state = {
        "session_dir": str(session_dir),
        "session_token": token,
        "annotator": "bob",
        "stage": Stage.INGEST,
        "traces": np.arange(6).reshape(2, 3),
    }

    state_store.persist_state_for_token(token, state)

    cache_snapshot = cache_root / token / state_store.SNAPSHOT_FILENAME
    session_snapshot = session_dir / state_store.SNAPSHOT_FILENAME
    assert cache_snapshot.exists()
    assert session_snapshot.exists()


def test_mark_and_consume_dirty_flag():
    backing = {}
    state_store.mark_dirty(backing)
    assert backing[state_store.DIRTY_FLAG] is True
    assert state_store.consume_dirty_flag(backing) is True
    assert state_store.consume_dirty_flag(backing) is False


def test_hydrate_state_applies_once(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache"
    monkeypatch.setattr(state_store, "CACHE_ROOT", cache_root, raising=False)
    token = "token123"

    persisted = {
        "annotator": "alice",
        "stage": Stage.WORKSPACE,
        "current_cell": 4,
    }
    state_store.persist_state_for_token(token, persisted)

    backing = {}
    first = state_store.hydrate_state(backing, token)
    assert first is True
    assert backing["annotator"] == "alice"
    assert backing["stage"] == Stage.WORKSPACE
    assert backing["current_cell"] == 4
    assert backing[state_store.HYDRATED_FLAG] is True

    backing["annotator"] = "bob"
    second = state_store.hydrate_state(backing, token)
    assert second is False
    assert backing["annotator"] == "bob"  # not overwritten


def test_hydrate_state_prefers_session_dir_snapshot(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache"
    monkeypatch.setattr(state_store, "CACHE_ROOT", cache_root, raising=False)
    token = "token456"
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    cache_root = state_store.resolve_cache_dir(token)
    state_store.save_snapshot(cache_root, {"annotator": "cache", "stage": Stage.START})
    state_store.save_snapshot(session_dir, {"annotator": "session", "stage": Stage.WORKSPACE})

    backing = {"session_dir": str(session_dir)}
    state_store.hydrate_state(backing, token)

    assert backing["annotator"] == "session"
    assert backing["stage"] == Stage.WORKSPACE
