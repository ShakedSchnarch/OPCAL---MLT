"""
Preprocessing utilities for OPCAL‑Labeler.

This module provides lightweight, transparent signal‑processing helpers used by
the UI layer. The emphasis is on robustness and interpretability rather than
heavy filtering:
  • Savitzky–Golay smoothing (phase‑preserving) for denoising
  • Baseline estimation via rolling median or global percentile
  • Robust scale (SD) estimate via MAD (1.4826×MAD)
  • Threshold construction: baseline + k·SD, including dual‑SD (pre/post stimulus)

Usage: the UI calls :func:`pre_post_sd_rect_params` to draw two floating SD·k
rectangles (0→stim, stim→end) above the trace without binding them to baseline.
"""

from __future__ import annotations

from typing import Tuple
import numpy as np
from scipy.signal import savgol_filter

# --- Constants ---------------------------------------------------------------
MAD_TO_SD: float = 1.4826   # Scale MAD → Gaussian-equivalent SD
EPS_SD: float = 1e-9        # Tiny positive floor for SD to avoid zero-width bands
DEFAULT_ROLLING_WINDOW_S: float = 20.0  # Typical rolling-median window (seconds)


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


def baseline_rolling_median(x: np.ndarray, fs_hz: float, window_s: float = DEFAULT_ROLLING_WINDOW_S) -> np.ndarray:
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
    """Estimate a robust SD as ``MAD_TO_SD × median(|x - median(x)|)``.

    Falls back to unbiased standard deviation when MAD is degenerate and
    clamps to a tiny positive floor (``EPS_SD``) so that downstream
    thresholds are always responsive to *k*.
    """
    mad = np.median(np.abs(x - np.median(x)))
    sd = MAD_TO_SD * mad
    if not np.isfinite(sd) or sd == 0.0:
        sd = float(np.std(x, ddof=1)) if x.size > 1 else 0.0
    return float(max(sd, EPS_SD))


def pre_post_sd_rect_params(
    x: np.ndarray,
    fs_hz: float,
    stim_time_s: float,
    k: float = 3.0,
    ref: str = "median",
) -> Tuple[float, float, float, float, int]:
    """Compute parameters for two *floating* SD·k rectangles (pre/post stim).

    Visual-only helper that returns constant vertical spans for two rectangles
    that **do not** attach to the dynamic baseline. For each segment, pick a
    constant reference level (segment median by default) and compute a robust
    SD via :func:`robust_sd_from_mad` on residuals relative to that level.

    The returned spans are:
    - ``[y0_pre,  y1_pre]  = [ref_pre,  ref_pre  + SD_pre]``  (pre **does not** use *k*)
    - ``[y0_post, y1_post] = [ref_post, ref_post + k·SD_post]``  (post uses *k*)

    Parameters
    ----------
    x : np.ndarray
        1D signal of shape (T,).
    fs_hz : float
        Sampling rate in Hertz.
    stim_time_s : float
        Time (seconds) at which stimulation starts.
    k : float, default=3.0
        Multiplier applied **only to the post‑stimulus** robust SD (band height). The pre‑stimulus band uses k = 1.
    ref : {"median", "zero"}, default="median"
        How to choose the constant reference level per segment.

    Returns
    -------
    (y0_pre, y1_pre, y0_post, y1_post, stim_idx)
        Rectangle base/top values for the pre/post segments and the
        stimulus index used for splitting.
    """
    n = int(x.size)
    stim_idx = int(max(0, min(n - 1, round(float(stim_time_s) * float(fs_hz)))))

    # --- Pre segment ---
    pre = x[:stim_idx] if stim_idx > 0 else x
    if ref == "zero":
        ref_pre = 0.0
    else:
        ref_pre = float(np.median(pre))
    sd_pre = robust_sd_from_mad(pre - ref_pre)
    sd_pre = float(max(sd_pre, 1e-9))
    y0_pre = ref_pre
    y1_pre = ref_pre + sd_pre

    # --- Post segment ---
    post = x[stim_idx:] if stim_idx < n else np.empty((0,), dtype=float)
    if post.size == 0:
        # Fallback: use pre if post is empty/tiny
        ref_post = ref_pre
        sd_post = sd_pre
    else:
        if ref == "zero":
            ref_post = 0.0
        else:
            ref_post = float(np.median(post))
        sd_post = robust_sd_from_mad(post - ref_post)
        sd_post = float(max(sd_post, 1e-9))

    y0_post = ref_post
    y1_post = ref_post + float(k) * sd_post

    return float(y0_pre), float(y1_pre), float(y0_post), float(y1_post), int(stim_idx)
