"""
Feature Extraction Utilities
===========================

Feature extraction and labeling summary utilities for OPCAL‑Labeler.
Includes descriptive statistics and aggregation functions for calcium traces and label maps.
All features are designed to be fast, interpretable, and robust for research workflows.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


def basic_features(
    x: np.ndarray,
    thr: np.ndarray,
    fs_hz: float,
    peaks_idx: np.ndarray,
) -> Dict[str, float]:
    """
    Compute a concise set of features for a single calcium trace.

    Args:
        x (np.ndarray): 1D array (T,) of the (optionally smoothed) calcium trace.
        thr (np.ndarray): 1D array (T,) of the per-sample threshold; same length as ``x``.
        fs_hz (float): Sampling rate in Hertz.
        peaks_idx (np.ndarray): 1D integer array of peak sample indices (as from ``scipy.signal.find_peaks``).

    Returns:
        Dict[str, float]: Dictionary of computed features:
            - mean: Arithmetic mean of ``x`` (NaN-safe)
            - std: Standard deviation of ``x`` (NaN-safe)
            - rms: Root-mean-square of ``x`` (NaN-safe)
            - frac_above_thr: Fraction of samples with ``x > thr``
            - peaks_per_min: Number of peaks normalized per minute

    Notes:
        All statistics are NaN-safe and robust to empty input.
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

    dur_min = T / fs_hz / 60.0  # Duration in minutes
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


def summarize_labels(
    label_map: Dict[int, Dict[str, Any]],
    cell_ids: List[str] | None = None,
    total_cells: int | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create a per-cell labels table and per-class statistics.

    Args:
        label_map (dict): Mapping: cell_index -> {"label": str, "notes": str, ...}
        cell_ids (list[str] | None): Optional cell id list (same order as traces columns). If provided, it's included in the returned table.
        total_cells (int | None): If given, percentages are computed against this number. Otherwise the denominator is the number of labeled cells.

    Returns:
        Tuple[DataFrame, DataFrame]:
            labels_df: One row per labeled cell: cell_index, cell_id (optional), label, notes, uncertain (if present).
            stats_df: Per-class count and percentage (0–100, rounded to 1 decimal place).

    Notes:
        The "uncertain" column may be included if present in the label_map.
        Handles empty input gracefully.
    """
    # Empty case
    if not label_map:
        labels_df = pd.DataFrame(columns=["cell_index", "cell_id", "label", "notes", "uncertain"])  # empty
        stats_df = pd.DataFrame(columns=["label", "count", "percent"])
        return labels_df, stats_df

    # Build per-cell table
    rows = []
    for ci, meta in label_map.items():
        ci_int = int(ci)
        # Defensive check for cell_ids length and index validity
        cell_id_val = (cell_ids[ci_int] if (cell_ids is not None and 0 <= ci_int < len(cell_ids)) else None)
        rows.append({
            "cell_index": ci_int,
            "cell_id": cell_id_val,
            "label": str(meta.get("label", "")),
            "notes": str(meta.get("notes", "")),
            "uncertain": bool(meta.get("uncertain", False)),
        })
    labels_df = pd.DataFrame(rows).sort_values("cell_index").reset_index(drop=True)

    # Aggregate per-class
    counts = labels_df["label"].value_counts(dropna=False).rename_axis("label").reset_index(name="count")
    denom = int(total_cells) if (total_cells is not None and total_cells > 0) else max(1, len(labels_df))
    counts["percent"] = (counts["count"] / denom * 100.0).round(1)
    stats_df = counts

    return labels_df, stats_df
