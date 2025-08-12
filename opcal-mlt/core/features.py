from __future__ import annotations
import numpy as np

def basic_features(x: np.ndarray, thr: np.ndarray, fs_hz: float, peaks_idx: np.ndarray) -> dict:
    dur_min = x.size / fs_hz / 60.0
    peaks_per_min = float(peaks_idx.size) / max(1e-9, dur_min)
    frac_above = float((x > thr).mean())
    rms = float(np.sqrt(np.mean(np.square(x))))
    return {
        "mean": float(np.mean(x)),
        "std": float(np.std(x)),
        "rms": rms,
        "frac_above_thr": frac_above,
        "peaks_per_min": peaks_per_min,
    }
