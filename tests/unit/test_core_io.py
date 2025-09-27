import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from opcal_mlt.core.io import load_traces, save_jsonl


def test_load_traces_csv(tmp_path):
    df = pd.DataFrame({"cell_a": [1.0, 2.0], "cell_b": [3.0, 4.0]})
    csv_path = tmp_path / "traces.csv"
    df.to_csv(csv_path, index=False)

    traces, meta = load_traces(csv_path)

    assert traces.shape == (2, 2)
    assert meta["cell_ids"] == ["cell_a", "cell_b"]


def test_load_traces_csv_empty_raises(tmp_path):
    csv_path = tmp_path / "empty.csv"
    pd.DataFrame(columns=["a", "b"]).to_csv(csv_path, index=False)
    with pytest.raises(ValueError):
        load_traces(csv_path)


def test_load_traces_npz(tmp_path):
    traces = np.arange(6, dtype=float).reshape(3, 2)
    npz_path = tmp_path / "bundle.npz"
    np.savez(
        npz_path,
        traces=traces,
        recording_id="rec42",
        fs_hz=np.array(5.0),
        cell_ids=np.array(["c0", "c1"]),
    )

    loaded, meta = load_traces(npz_path)

    assert np.array_equal(loaded, traces)
    assert meta["recording_id"] == "rec42"
    assert meta["cell_ids"] == ["c0", "c1"]
    assert meta["fs_hz"] == 5.0


def test_load_traces_rejects_unknown_suffix(tmp_path):
    data_path = tmp_path / "data.txt"
    data_path.write_text("irrelevant", encoding="utf-8")
    with pytest.raises(ValueError):
        load_traces(data_path)


def test_save_jsonl_roundtrip(tmp_path):
    records = [{"a": 1, "text": "hello"}, {"a": 2, "b": 3}]
    out_path = tmp_path / "labels" / "records.jsonl"
    save_jsonl(records, out_path)

    data = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    assert data == records


def test_save_jsonl_validates_input(tmp_path):
    out_path = tmp_path / "invalid.jsonl"
    with pytest.raises(ValueError):
        save_jsonl({"a": 1}, out_path)
