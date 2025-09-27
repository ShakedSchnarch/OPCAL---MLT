"""Label persistence and feature calculation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from opcal_mlt.app.session_io import append_labels, append_peaks
from opcal_mlt.core.features import basic_features
from opcal_mlt.domain.enums import BaselineMethod, LabelClass
from opcal_mlt.domain.models import LabelRecord, LabelState, PeakRecord, TraceSet


@dataclass(slots=True)
class LabelSaveResult:
    label_state: LabelState
    peaks: Sequence[int]


class LabelingService:
    """Encapsulate the workflow of saving a label and derived peaks."""

    def save_label(
        self,
        *,
        session_dir: Path,
        trace_set: TraceSet,
        cell_index: int,
        smoothed_trace: np.ndarray,
        threshold: np.ndarray,
        peaks: Sequence[int],
        label: LabelClass,
        notes: str,
        uncertain: bool,
        recording_id: str,
        annotator_id: str,
        metadata: dict,
    ) -> LabelSaveResult:
        saved_utc = datetime.now(timezone.utc)
        feats = basic_features(smoothed_trace, threshold, trace_set.fs_hz, np.asarray(peaks, dtype=int))
        record = LabelRecord(
            cell_index=cell_index,
            label=label,
            notes=notes,
            uncertain=uncertain,
            session_id=session_dir.name,
            recording_id=recording_id,
            annotator_id=annotator_id,
            saved_utc=saved_utc,
            feature_mean=feats["mean"],
            feature_std=feats["std"],
            feature_rms=feats["rms"],
            frac_above_thr=feats["frac_above_thr"],
            peaks_per_min=feats["peaks_per_min"],
            filter_type=str(metadata.get("filter_type", "none")),
            filter_window=int(metadata.get("filter_window", 0)),
            filter_polyorder=int(metadata.get("filter_polyorder", 0)),
            baseline_method=metadata.get("baseline_method", BaselineMethod.ROLLING_MEDIAN),
            baseline_window_s_or_q=float(metadata.get("baseline_window_s_or_q", 0.0)),
            threshold_k=float(metadata.get("threshold_k", 3.0)),
        )
        append_labels(
            session_dir,
            {
                "session_id": record.session_id,
                "recording_id": record.recording_id,
                "annotator_id": record.annotator_id,
                "saved_utc": record.saved_utc.isoformat(),
                "cell_index": record.cell_index,
                "cell_id": trace_set.cell_ids[cell_index],
                "label": record.label.value,
                "uncertain": record.uncertain,
                "notes": record.notes,
                "filter_type": record.filter_type,
                "filter_window": record.filter_window,
                "filter_polyorder": record.filter_polyorder,
                "baseline_method": record.baseline_method.value,
                "baseline_window_s_or_q": record.baseline_window_s_or_q,
                "sd_method": metadata.get("sd_method", "MAD"),
                "threshold_k": record.threshold_k,
                "mean": record.feature_mean,
                "std": record.feature_std,
                "rms": record.feature_rms,
                "frac_above_thr": record.frac_above_thr,
                "peaks_per_min": record.peaks_per_min,
                "version": metadata.get("version", "mlt-0.2.0"),
            },
        )
        peak_rows = [
            {
                "session_id": record.session_id,
                "recording_id": record.recording_id,
                "cell_index": cell_index,
                "peak_idx": int(idx),
                "peak_time_s": float(idx) / trace_set.fs_hz,
                "peak_value": float(smoothed_trace[idx]),
            }
            for idx in peaks
        ]
        append_peaks(session_dir, peak_rows)
        state = LabelState(cell_index=cell_index, label=label, notes=notes, uncertain=uncertain)
        return LabelSaveResult(label_state=state, peaks=peaks)


__all__ = ["LabelingService", "LabelSaveResult"]
