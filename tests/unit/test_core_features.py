import numpy as np
import pandas as pd
import pytest

from opcal_mlt.core.features import basic_features, summarize_labels


def test_basic_features_computes_expected_stats():
    x = np.array([0.0, 1.0, 2.0, 3.0])
    thr = np.array([1.5])  # broadcast path
    peaks = np.array([2, 3])

    feats = basic_features(x=x, thr=thr, fs_hz=2.0, peaks_idx=peaks)

    assert feats["mean"] == pytest.approx(np.mean(x))
    assert feats["std"] == pytest.approx(np.std(x))
    rms_expected = np.sqrt(np.mean(np.square(x)))
    assert feats["rms"] == pytest.approx(rms_expected)
    assert feats["frac_above_thr"] == pytest.approx(0.5)
    duration_min = x.size / 2.0 / 60.0
    assert feats["peaks_per_min"] == pytest.approx(peaks.size / duration_min)


def test_basic_features_handles_zero_length_or_invalid_fs():
    empty = np.array([], dtype=float)
    feats = basic_features(x=empty, thr=empty, fs_hz=30.0, peaks_idx=np.array([], dtype=int))
    assert all(value == 0.0 for value in feats.values())

    feats_bad_fs = basic_features(x=np.array([1.0]), thr=np.array([1.0]), fs_hz=0.0, peaks_idx=np.array([], dtype=int))
    assert all(value == 0.0 for value in feats_bad_fs.values())


def test_summarize_labels_generates_tables_with_optional_cell_ids():
    label_map = {
        0: {"label": "Oscillatory", "notes": "ok", "uncertain": True},
        2: {"label": "Low-activity", "notes": ""},
    }
    cell_ids = ["c0", "c1", "c2"]

    labels_df, stats_df = summarize_labels(label_map, cell_ids=cell_ids, total_cells=4)

    assert list(labels_df["cell_index"]) == [0, 2]
    assert list(labels_df["cell_id"]) == ["c0", "c2"]
    assert list(labels_df["label"]) == ["Oscillatory", "Low-activity"]
    assert bool(labels_df.loc[0, "uncertain"])

    stats = stats_df.set_index("label")
    assert stats.loc["Oscillatory", "count"] == 1
    # Percentages use provided total_cells
    assert stats.loc["Oscillatory", "percent"] == pytest.approx(25.0)
    assert stats.loc["Low-activity", "percent"] == pytest.approx(25.0)


def test_summarize_labels_handles_missing_data_gracefully():
    labels_df, stats_df = summarize_labels({}, cell_ids=None, total_cells=None)
    assert labels_df.empty
    assert stats_df.empty

    partial = {1: {"label": "Oscillatory"}}
    labels_df, _ = summarize_labels(partial, cell_ids=["only"], total_cells=None)
    # Index out of range should map to None
    assert pd.isna(labels_df.loc[0, "cell_id"])
