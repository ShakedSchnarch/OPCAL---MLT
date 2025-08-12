from __future__ import annotations
import numpy as np
from scipy.signal import savgol_filter
from typing import Literal, Tuple

def smooth_signal(x: np.ndarray, window: int = 31, polyorder: int = 3) -> np.ndarray:
    window = max(5, window | 1)  # make odd, >=5
    polyorder = max(1, min(polyorder, 5))
    if x.size < window:
        return x.copy()
    return savgol_filter(x, window_length=window, polyorder=polyorder, mode="interp")

def baseline_rolling_median(x: np.ndarray, fs_hz: float, window_s: float = 20.0) -> np.ndarray:
    w = int(max(1, window_s * fs_hz))
    w = w + (w % 2 == 0)  # odd
    # pad and rolling median
    pad = w // 2
    xp = np.pad(x, (pad, pad), mode="edge")
    med = np.empty_like(x, dtype=float)
    for i in range(x.size):
        med[i] = np.median(xp[i:i+w])
    return med

def baseline_percentile(x: np.ndarray, q: float = 25.0) -> np.ndarray:
    b = np.percentile(x, q)
    return np.full_like(x, fill_value=b, dtype=float)

def robust_sd_from_mad(x: np.ndarray) -> float:
    # robust SD estimate
    mad = np.median(np.abs(x - np.median(x)))
    return 1.4826 * mad

def threshold_from_baseline(
    x: np.ndarray,
    baseline: np.ndarray | float,
    k: float = 3.0,
    sd: float | None = None,
) -> np.ndarray:
    if np.isscalar(baseline):
        base = np.full_like(x, float(baseline))
    else:
        base = baseline.astype(float)
    if sd is None:
        sd = robust_sd_from_mad(x - base)
    thr = base + k * sd
    return thr
