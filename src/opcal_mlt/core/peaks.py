"""
Peak Detection Utilities
=======================

Functions for detecting peaks in calcium imaging traces, used to identify putative neuronal activity events.
All detection is based on thresholding, minimum distance, and optional prominence filtering.
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

    Args:
        x (np.ndarray): The calcium trace as a 1D NumPy array of shape (T,).
        thr (np.ndarray): The threshold trace as a 1D NumPy array of shape (T,).
        fs_hz (float): Sampling frequency of the trace in Hz (samples per second).
        min_distance_s (float, optional): Minimum time (in seconds) between detected peaks. Default is 1.0.
        prominence (float | None, optional): Required prominence of peaks (see scipy.signal.find_peaks). If None, no prominence filtering is applied.

    Returns:
        np.ndarray: Array of integer indices into `x` where peaks were detected.
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
