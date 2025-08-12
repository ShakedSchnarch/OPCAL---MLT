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
    # Only consider samples above threshold
    above = x > thr
    # Use find_peaks with distance constraint
    distance = max(1, int(min_distance_s * fs_hz))
    peaks, _ = find_peaks(x, distance=distance, prominence=prominence)
    # filter by threshold mask
    return peaks[above[peaks]]
