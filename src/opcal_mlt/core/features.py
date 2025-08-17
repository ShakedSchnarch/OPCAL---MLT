
from __future__ import annotations

"""
Feature extraction utilities for OPCAL‑Labeler.

This module intentionally keeps a small, transparent set of descriptive
statistics that are fast to compute and easy to interpret by annotators.
"""

from typing import Dict
import numpy as np


def basic_features(
    x: np.ndarray,
    thr: np.ndarray,
    fs_hz: float,
    peaks_idx: np.ndarray,
) -> Dict[str, float]:
    """Compute a concise set of features for a single calcium trace.

    Parameters
    ----------
    x : np.ndarray
        1D array (T,) of the (optionally smoothed) calcium trace.
    thr : np.ndarray
        1D array (T,) of the per‑sample threshold; same length as ``x``.
    fs_hz : float
        Sampling rate in Hertz.
    peaks_idx : np.ndarray
        1D integer array of peak sample indices (as from ``scipy.signal.find_peaks``).

    Returns
    -------
    Dict[str, float]
        A dictionary with:
        - ``mean`` – arithmetic mean of ``x`` (NaN‑safe)
        - ``std`` – standard deviation of ``x`` (NaN‑safe)
        - ``rms`` – root‑mean‑square of ``x`` (NaN‑safe)
        - ``frac_above_thr`` – fraction of samples with ``x > thr``
        - ``peaks_per_min`` – number of peaks normalized per minute
    """

    T = int(x.size)
    if T == 0 or fs_hz <= 0:
        # Guard against invalid inputs to avoid divisions by zero.
        return {
            "mean": 0.0,
            "std": 0.0,
            "rms": 0.0,
            "frac_above_thr": 0.0,
            "peaks_per_min": 0.0,
        }

    # Ensure threshold shape is broadcastable to the trace shape.
    if thr.shape != x.shape:
        thr = np.broadcast_to(thr, x.shape)

    dur_min = T / fs_hz / 60.0
    peaks_per_min = float(np.size(peaks_idx)) / max(1e-9, dur_min)

    # NaN‑safe statistics (ignore NaNs if present)
    mean = float(np.nanmean(x))
    std = float(np.nanstd(x))
    rms = float(np.sqrt(np.nanmean(np.square(x))))

    # Fraction of samples strictly above the threshold
    frac_above = float(np.mean(x > thr))

    return {
        "mean": mean,
        "std": std,
        "rms": rms,
        "frac_above_thr": frac_above,
        "peaks_per_min": peaks_per_min,
    }
