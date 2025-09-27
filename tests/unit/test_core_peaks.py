import numpy as np

from opcal_mlt.core.peaks import detect_peaks


def test_detect_peaks_filters_below_threshold():
    x = np.array([0.0, 2.0, 1.0, 3.0, 0.0, 2.0, 0.0])
    thr = np.ones_like(x)

    peaks = detect_peaks(x, thr=thr, fs_hz=2.0, min_distance_s=0.4)

    assert np.array_equal(peaks, np.array([1, 3, 5]))

    high_thr = np.full_like(x, 2.5)
    filtered = detect_peaks(x, thr=high_thr, fs_hz=2.0, min_distance_s=0.4)
    assert np.array_equal(filtered, np.array([3]))


def test_detect_peaks_respects_min_distance():
    x = np.array([0.0, 5.0, 0.0, 4.0, 0.0])
    thr = np.zeros_like(x)

    close_peaks = detect_peaks(x, thr=thr, fs_hz=10.0, min_distance_s=0.01)
    assert np.array_equal(close_peaks, np.array([1, 3]))

    separated = detect_peaks(x, thr=thr, fs_hz=10.0, min_distance_s=0.31)
    assert np.array_equal(separated, np.array([1]))


def test_detect_peaks_with_prominence():
    x = np.array([0.0, 1.0, 0.1, 3.0, 0.2, 1.1, 0.0])
    thr = np.zeros_like(x)
    peaks = detect_peaks(x, thr=thr, fs_hz=5.0, min_distance_s=0.1, prominence=1.5)
    assert np.array_equal(peaks, np.array([3]))
