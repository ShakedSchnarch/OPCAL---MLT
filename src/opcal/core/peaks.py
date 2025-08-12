"""
Utilities for detecting peaks in calcium imaging traces.

This module provides functions for identifying peaks in 1D calcium imaging data,
such as those corresponding to putative neuronal activity events.
"""
from __future__ import annotations
import numpy as np
from scipy.signal import find_peaks

def detect_peaks(
    x: np.ndarray,
    thr: np.ndarray,
    fs_hz: float,
    min_distance_s: float = 1.0,
    prominence: float | None = None,
) -> np.ndarray:
    """
    Detect peaks in a 1D calcium imaging trace based on thresholding and minimum distance.

    Parameters
    ----------
    x : np.ndarray
        The calcium trace as a 1D NumPy array of shape (T,). Units are arbitrary (e.g., dF/F).
    thr : np.ndarray
        The threshold trace as a 1D NumPy array of shape (T,). Peaks are only considered if x > thr at that index.
    fs_hz : float
        Sampling frequency of the trace in Hz (samples per second).
    min_distance_s : float, optional
        Minimum time (in seconds) between detected peaks. Default is 1.0.
    prominence : float or None, optional
        Required prominence of peaks (see scipy.signal.find_peaks). If None, no prominence filtering is applied.

    What constitutes a peak:
        A peak is a local maximum in `x` that exceeds the corresponding value in `thr` and is separated from other peaks
        by at least `min_distance_s` seconds. Optionally, peaks must also have at least the specified `prominence`.

    How `min_distance_s` and `prominence` influence detection:
        - `min_distance_s` ensures that detected peaks are at least this many seconds apart (converted to samples).
        - `prominence` filters out peaks that are not sufficiently prominent relative to their surroundings.

    Returns
    -------
    np.ndarray
        Array of integer indices into `x` where peaks were detected.
    """
    # Create a boolean mask for samples above the threshold
    above: np.ndarray = x > thr
    # Convert minimum peak distance from seconds to samples
    distance: int = max(1, int(min_distance_s * fs_hz))
    # Detect all local maxima (potential peaks) with distance and prominence constraints
    peaks, _ = find_peaks(x, distance=distance, prominence=prominence)
    # Filter detected peaks to only those above the threshold at their location
    valid_peaks = peaks[above[peaks]]
    return valid_peaks
