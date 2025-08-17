
"""
Preprocessing utilities for OPCAL‑Labeler.

This module provides lightweight, transparent signal‑processing helpers used by
the UI layer. The emphasis is on robustness and interpretability rather than
heavy filtering:
  • Savitzky–Golay smoothing (phase‑preserving) for denoising
  • Baseline estimation via rolling median or global percentile
  • Robust scale (SD) estimate via MAD (1.4826×MAD)
  • Threshold construction: baseline + k·SD, including dual‑SD (pre/post stimulus)
"""

from __future__ import annotations

from typing import Tuple
import numpy as np
from scipy.signal import savgol_filter


def smooth_signal(x: np.ndarray, window: int = 31, polyorder: int = 3) -> np.ndarray:
    """Return a Savitzky–Golay smoothed copy of a 1D signal.

    Parameters
    ----------
    x : np.ndarray
        1D input signal of shape (T,).
    window : int, default=31
        Window length (samples). Will be coerced to an odd integer ≥ 5.
    polyorder : int, default=3
        Polynomial order for the filter (1–5 typical).

    Notes
    -----
    If the signal is shorter than the effective window, the original signal is
    returned unchanged to avoid edge artifacts.
    """

    # Ensure an odd window ≥ 5, clamp polyorder to a sensible range
    window = max(5, int(window) | 1)  # bitwise OR with 1 -> odd
    polyorder = max(1, min(int(polyorder), 5))

    if x.size < window:
        return x.copy()

    return savgol_filter(x, window_length=window, polyorder=polyorder, mode="interp")


def baseline_rolling_median(x: np.ndarray, fs_hz: float, window_s: float = 20.0) -> np.ndarray:
    """Estimate a slowly varying baseline using a rolling median window.

    Parameters
    ----------
    x : np.ndarray
        1D signal of shape (T,).
    fs_hz : float
        Sampling rate in Hertz.
    window_s : float, default=20.0
        Median window size in seconds (typ. 10–30 s).

    Returns
    -------
    np.ndarray
        Baseline array of shape (T,) aligned to ``x``.
    """

    # Convert seconds to samples and make the window odd (≥ 1)
    w = int(max(1, round(window_s * fs_hz)))
    if w % 2 == 0:
        w += 1

    pad = w // 2
    # Edge‑padding to avoid shrinking at the boundaries
    xp = np.pad(x, (pad, pad), mode="edge")
    med = np.empty_like(x, dtype=float)

    # Simple rolling median (O(T·w)); for T up to order ~1e5 this is fine
    for i in range(x.size):
        med[i] = np.median(xp[i : i + w])

    return med


def baseline_percentile(x: np.ndarray, q: float = 25.0) -> np.ndarray:
    """Return a flat baseline at a global percentile of the signal.

    Parameters
    ----------
    x : np.ndarray
        1D signal of shape (T,).
    q : float, default=25.0
        Percentile in [0, 100]. Typically 20–30 captures the quiescent level.
    """

    b = np.percentile(x, q)
    return np.full_like(x, fill_value=float(b), dtype=float)


def robust_sd_from_mad(x: np.ndarray) -> float:
    """Robust standard‑deviation estimate as 1.4826×MAD.

    ``MAD = median(|x − median(x)|)``. The factor 1.4826 scales MAD to the
    Gaussian SD for large samples.
    """

    mad = np.median(np.abs(x - np.median(x)))
    return float(1.4826 * mad)


def threshold_from_baseline(
    x: np.ndarray,
    baseline: np.ndarray | float,
    k: float = 3.0,
    sd: float | None = None,
) -> np.ndarray:
    """Construct a per‑sample threshold: ``baseline + k·SD``.

    If ``sd`` is not provided, it is estimated robustly from ``x − baseline``.
    ``baseline`` may be a scalar or an array broadcastable to ``x``.
    """

    base = np.full_like(x, float(baseline)) if np.isscalar(baseline) else np.asarray(baseline, float)
    if sd is None:
        sd = robust_sd_from_mad(x - base)
    return base + float(k) * float(sd)


def dual_sd_thresholds(
    x: np.ndarray,
    base: np.ndarray,
    fs_hz: float,
    stim_time_s: float,
    k: float = 3.0,
) -> Tuple[np.ndarray, np.ndarray, float, float, int]:
    """Compute separate thresholds for pre‑ and post‑stimulus segments.

    Parameters
    ----------
    x : np.ndarray
        1D signal (T,).
    base : np.ndarray
        Baseline (T,) aligned with ``x``.
    fs_hz : float
        Sampling rate in Hertz.
    stim_time_s : float
        Time (seconds) at which stimulation starts.
    k : float, default=3.0
        Threshold multiplier, i.e., ``thr = baseline + k·SD``.

    Returns
    -------
    (thr_pre, thr_post, sd_pre, sd_post, stim_idx)
        ``thr_pre`` and ``thr_post`` are threshold arrays for the respective
        segments; ``sd_pre``/``sd_post`` are the robust SDs used; ``stim_idx`` is
        the sample index where the split occurs (clipped to [0, T−1]).
    """

    n = int(x.size)
    # Convert seconds → sample index and clip to valid range
    stim_idx = int(max(0, min(n - 1, round(float(stim_time_s) * float(fs_hz)))))

    # Compute robust SDs on each segment; fall back sensibly if segments are tiny
    if stim_idx > 3:
        sd_pre = robust_sd_from_mad(x[:stim_idx] - base[:stim_idx])
    else:
        sd_pre = robust_sd_from_mad(x - base)

    if stim_idx < n - 3:
        sd_post = robust_sd_from_mad(x[stim_idx:] - base[stim_idx:])
    else:
        sd_post = sd_pre

    thr_pre = base[:stim_idx] + float(k) * sd_pre
    thr_post = base[stim_idx:] + float(k) * sd_post

    return thr_pre, thr_post, float(sd_pre), float(sd_post), stim_idx
