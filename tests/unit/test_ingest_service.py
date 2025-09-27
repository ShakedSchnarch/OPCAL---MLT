import io

import numpy as np
import pandas as pd
import pytest

from opcal_mlt.domain.models import TraceSet
from opcal_mlt.services.ingest import IngestService


def test_load_trace_set_from_csv_path(tmp_path):
    df = pd.DataFrame({"cell_a": [1.0, 2.0], "cell_b": [3.0, 4.0]})
    csv_path = tmp_path / "traces.csv"
    df.to_csv(csv_path, index=False)

    service = IngestService()
    trace_set, meta = service.load_trace_set(csv_path)

    assert trace_set.traces.shape == (2, 2)
    assert trace_set.cell_ids == ["cell_a", "cell_b"]
    assert meta["cell_ids"] == ["cell_a", "cell_b"]


def test_load_trace_set_from_file_like_csv():
    df = pd.DataFrame({"cell_a": [1.0, 2.0], "cell_b": [3.0, 4.0]})
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    buffer.name = "inline.csv"

    service = IngestService()
    trace_set, _ = service.load_trace_set(buffer)

    assert trace_set.traces.shape == (2, 2)
    assert trace_set.cell_ids == ["cell_a", "cell_b"]


def test_load_trace_set_from_npz(tmp_path):
    traces = np.random.rand(5, 2)
    npz_path = tmp_path / "bundle.npz"
    np.savez(npz_path, traces=traces, cell_ids=np.array(["id0", "id1"]), recording_id="recA", fs_hz=2.5)

    service = IngestService()
    trace_set, meta = service.load_trace_set(npz_path)

    assert trace_set.traces.shape == (5, 2)
    assert trace_set.cell_ids == ["id0", "id1"]
    assert pytest.approx(trace_set.fs_hz) == 2.5
    assert meta["recording_id"] == "recA"


def test_apply_external_ids_valid():
    service = IngestService()
    original = TraceSet(traces=np.zeros((5, 3)), cell_ids=["a", "b", "c"], fs_hz=1.0)
    updated = service.apply_external_ids(original, ["x", "y", "z"])
    assert updated.cell_ids == ["x", "y", "z"]


def test_apply_external_ids_length_mismatch():
    service = IngestService()
    original = TraceSet(traces=np.zeros((5, 3)), cell_ids=["a", "b", "c"], fs_hz=1.0)
    with pytest.raises(ValueError):
        service.apply_external_ids(original, ["x"])  # wrong length


def test_auto_cell_ids_format():
    service = IngestService()
    ids = service.auto_cell_ids(3, prefix="cell_", pad=2, start=10)
    assert ids == ["cell_10", "cell_11", "cell_12"]
