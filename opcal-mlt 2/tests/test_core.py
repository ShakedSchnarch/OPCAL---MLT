import numpy as np
from core import preprocess as pp
from core import peaks as pk

def test_threshold_nonempty():
    x = np.zeros(1000)
    x[200] = 5.0
    base = pp.baseline_percentile(x, q=25)
    thr = pp.threshold_from_baseline(x, base, k=3.0)
    assert thr.shape == x.shape

def test_peak_detection_simple():
    fs = 10.0
    x = np.zeros(300)
    x[50] = 3.0
    x[150] = 3.0
    base = pp.baseline_percentile(x, q=25)
    thr = pp.threshold_from_baseline(x, base, k=1.0)  # easy
    peaks = pk.detect_peaks(x, thr, fs_hz=fs, min_distance_s=5.0)
    assert len(peaks) == 2
