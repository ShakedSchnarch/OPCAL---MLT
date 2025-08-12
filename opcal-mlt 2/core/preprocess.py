
from __future__ import annotations
import numpy as np
from scipy.signal import savgol_filter

def smooth_signal(x: np.ndarray, window: int = 31, polyorder: int = 3) -> np.ndarray:
    window = max(5, window | 1)  # make odd, >=5
    polyorder = max(1, min(polyorder, 5))
    if x.size < window:
        return x.copy()
    return savgol_filter(x, window_length=window, polyorder=polyorder, mode="interp")

def baseline_rolling_median(x: np.ndarray, fs_hz: float, window_s: float = 20.0) -> np.ndarray:
    w = int(max(1, window_s * fs_hz))
    w = w + (w % 2 == 0)  # odd
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
    mad = np.median(np.abs(x - np.median(x)))
    return 1.4826 * mad

def threshold_from_baseline(x: np.ndarray, baseline: np.ndarray | float, k: float = 3.0, sd: float | None = None) -> np.ndarray:
    base = np.full_like(x, float(baseline)) if np.isscalar(baseline) else baseline.astype(float)
    if sd is None:
        sd = robust_sd_from_mad(x - base)
    return base + k * sd

def dual_sd_thresholds(x: np.ndarray, base: np.ndarray, fs_hz: float, stim_time_s: float, k: float = 3.0):
    """Return (thr_pre, thr_post, sd_pre, sd_post, stim_idx)."""
    n = x.size
    stim_idx = int(max(0, min(n-1, round(stim_time_s * fs_hz))))
    sd_pre = robust_sd_from_mad(x[:stim_idx] - base[:stim_idx]) if stim_idx > 3 else robust_sd_from_mad(x - base)
    sd_post = robust_sd_from_mad(x[stim_idx:] - base[stim_idx:]) if stim_idx < n-3 else sd_pre
    thr_pre = base[:stim_idx] + k * sd_pre
    thr_post = base[stim_idx:] + k * sd_post
    return thr_pre, thr_post, float(sd_pre), float(sd_post), stim_idx
