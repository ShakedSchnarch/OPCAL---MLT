import zipfile
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from opcal_mlt.app.session_io import append_labels
from opcal_mlt.services.export import ExportService


def _label_row(session_dir, *, cell_index, label, uncertain=False):
    return {
        "session_id": session_dir.name,
        "recording_id": "rec",
        "annotator_id": "ann",
        "saved_utc": datetime.now(timezone.utc).isoformat(),
        "cell_index": cell_index,
        "cell_id": f"cell_{cell_index:03d}",
        "label": label,
        "uncertain": uncertain,
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
        "version": "test",
    }


def test_export_training_csv_bundle_splits_classes_and_uncertain(tmp_path):
    session_dir = tmp_path / "rec" / "session"
    session_dir.mkdir(parents=True)
    traces = np.arange(20, dtype=float).reshape(5, 4)

    append_labels(session_dir, _label_row(session_dir, cell_index=0, label="Low-activity"))
    append_labels(session_dir, _label_row(session_dir, cell_index=1, label="High-flat", uncertain=True))
    append_labels(session_dir, _label_row(session_dir, cell_index=2, label="Oscillatory"))
    append_labels(session_dir, _label_row(session_dir, cell_index=2, label="High-oscillatory"))

    result = ExportService().export_training_csv_bundle(
        session_dir=session_dir,
        traces=traces,
        source_name="Signals Analysis_new (1).csv",
    )

    names = {path.name for path in result.csv_paths}
    assert names == {
        "data for training_Signals_Analysis_new_1_low_activity.csv",
        "data for training_Signals_Analysis_new_1_high_oscillatory.csv",
        "data for training_Signals_Analysis_new_1_uncertain.csv",
    }

    low = pd.read_csv(result.output_dir / "data for training_Signals_Analysis_new_1_low_activity.csv", header=None)
    high_osc = pd.read_csv(result.output_dir / "data for training_Signals_Analysis_new_1_high_oscillatory.csv", header=None)
    uncertain = pd.read_csv(result.output_dir / "data for training_Signals_Analysis_new_1_uncertain.csv", header=None)

    np.testing.assert_array_equal(low.to_numpy(), traces[:, [0]])
    np.testing.assert_array_equal(high_osc.to_numpy(), traces[:, [2]])
    np.testing.assert_array_equal(uncertain.to_numpy(), traces[:, [1]])

    with zipfile.ZipFile(result.archive_path) as archive:
        assert set(archive.namelist()) == names


def test_export_training_csv_bundle_rejects_mismatched_label_indices(tmp_path):
    session_dir = tmp_path / "rec" / "session"
    session_dir.mkdir(parents=True)
    append_labels(session_dir, _label_row(session_dir, cell_index=3, label="Low-activity"))

    with pytest.raises(ValueError, match="cell_index=3"):
        ExportService().export_training_csv_bundle(
            session_dir=session_dir,
            traces=np.zeros((5, 2)),
            source_name="source.csv",
        )
