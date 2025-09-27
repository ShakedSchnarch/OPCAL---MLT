import numpy as np
import pytest

from opcal_mlt.domain.enums import BaselineMethod, LabelClass, Stage
from opcal_mlt.domain.models import TraceSet


def test_stage_mapping_values():
    assert Stage.START.name == "START"
    assert Stage.WORKSPACE != Stage.EXPORT


def test_label_class_from_str_exact_match():
    assert LabelClass.from_str("Oscillatory") is LabelClass.OSCILLATORY


def test_baseline_method_from_str_handles_variants():
    assert BaselineMethod.from_str("rolling median") is BaselineMethod.ROLLING_MEDIAN
    assert BaselineMethod.from_str("percentile") is BaselineMethod.PERCENTILE_25


def test_trace_set_validation():
    traces = np.zeros((10, 2))
    with pytest.raises(ValueError):
        TraceSet(traces=traces.reshape(20), cell_ids=["a", "b"], fs_hz=1.0)
    with pytest.raises(ValueError):
        TraceSet(traces=traces, cell_ids=["a"], fs_hz=1.0)
    with pytest.raises(ValueError):
        TraceSet(traces=traces, cell_ids=["a", "b"], fs_hz=0)
    trace_set = TraceSet(traces=traces, cell_ids=["a", "b"], fs_hz=2.5)
    assert trace_set.fs_hz == 2.5
