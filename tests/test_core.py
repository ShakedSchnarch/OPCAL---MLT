"""Unit tests for core preprocessing and peak detection utilities."""

import numpy as np
from opcal_mlt.core import preprocess as pp
from opcal_mlt.core import peaks as pk
from opcal_mlt.core import features as ft

def test_threshold_nonempty():
    """Test that the threshold calculation returns an array of the correct shape for a simple signal."""
    # Create a signal with mostly zeros and a single high value spike
    signal = np.zeros(1000)
    signal[200] = 5.0

    # Compute baseline using the 25th percentile of the signal
    baseline = pp.baseline_percentile(signal, q=25)

    # Calculate threshold based on baseline with a multiplier k=3.0
    threshold = pp.threshold_from_baseline(signal, baseline, k=3.0)

    # Assert that the threshold array matches the shape of the input signal
    assert threshold.shape == signal.shape

def test_peak_detection_simple():
    """Test that two distinct peaks are detected in a sparse signal with sufficient minimum distance."""
    sampling_frequency = 10.0  # Hz

    # Create a signal with two spikes separated by more than min_distance_s
    signal = np.zeros(300)
    signal[50] = 3.0
    signal[150] = 3.0

    # Compute baseline using the 25th percentile of the signal
    baseline = pp.baseline_percentile(signal, q=25)

    # Calculate threshold based on baseline with a multiplier k=1.0 for easier detection
    threshold = pp.threshold_from_baseline(signal, baseline, k=1.0)

    # Detect peaks with a minimum distance of 5 seconds between them
    peaks = pk.detect_peaks(signal, threshold, fs_hz=sampling_frequency, min_distance_s=5.0)

    # Assert that exactly two peaks are detected
    assert len(peaks) == 2

def test_dual_sd_thresholds_shapes_and_index():
    """dual_sd_thresholds should split at the correct sample index and produce segments whose combined length equals T."""
    fs = 10.0  # Hz
    T = 100
    stim_time = 3.0  # seconds -> index 30
    x = np.zeros(T)
    x[60] = 5.0  # a spike post-stim
    base = pp.baseline_percentile(x, q=25)

    thr_pre, thr_post, sd_pre, sd_post, stim_idx = pp.dual_sd_thresholds(x, base, fs, stim_time, k=3.0)

    # Split index should match 3s * 10Hz = 30
    assert stim_idx == 30
    # Combined length equals T
    assert thr_pre.size + thr_post.size == T
    # SDs are non-negative
    assert sd_pre >= 0.0 and sd_post >= 0.0


def test_smooth_signal_short_input_returns_copy():
    """If the signal is shorter than the smoothing window, the function should return the input unchanged (copy)."""
    x = np.linspace(0, 1, 10)
    y = pp.smooth_signal(x, window=31, polyorder=3)  # window > len(x)
    assert np.allclose(x, y)


def test_peak_detection_respects_threshold_mask():
    """Peaks below the provided threshold should be filtered out even if find_peaks detects them structurally."""
    fs = 10.0
    x = np.zeros(200)
    x[50] = 0.5   # below threshold
    x[100] = 3.0  # above threshold
    # Provide an explicit threshold vector of ones
    thr = np.ones_like(x) * 1.0
    peaks = pk.detect_peaks(x, thr, fs_hz=fs, min_distance_s=0.1)
    # Only the peak at index 100 should survive the threshold filter
    assert np.array_equal(peaks, np.array([100]))


def test_baseline_rolling_median_constant_signal():
    """Rolling-median baseline of a constant signal should equal that constant (within numerical tolerance)."""
    fs = 10.0
    x = np.full(100, 2.0)
    base = pp.baseline_rolling_median(x, fs_hz=fs, window_s=5.0)
    assert np.allclose(base, 2.0)


def test_basic_features_output_schema_and_types():
    """basic_features should return all expected keys with float values and sensible ranges."""
    fs = 10.0
    T = 300
    x = 0.01 * np.random.standard_normal(T)
    x[120] = 2.0  # a clear event
    thr = np.zeros_like(x)
    peaks = np.array([120])
    feats = ft.basic_features(x, thr, fs, peaks)

    # Expected keys
    expected_keys = {"mean", "std", "rms", "frac_above_thr", "peaks_per_min"}
    assert set(feats.keys()) == expected_keys

    # Types and ranges
    assert all(isinstance(feats[k], float) for k in expected_keys)
    assert 0.0 <= feats["frac_above_thr"] <= 1.0
    assert feats["peaks_per_min"] >= 0.0
