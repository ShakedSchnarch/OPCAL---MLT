"""Export helpers for session archives and training-ready CSV bundles."""
from __future__ import annotations

import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from opcal_mlt.domain.enums import LabelClass


_CLASS_FILE_SLUGS: dict[LabelClass, str] = {
    LabelClass.LOW_ACTIVITY: "low_activity",
    LabelClass.HIGH_FLAT: "high_flat",
    LabelClass.HIGH_OSCILLATORY: "high_oscillatory",
    LabelClass.OSCILLATORY: "oscillatory",
    LabelClass.DRIFTING: "drifting",
}


@dataclass(slots=True)
class TrainingCsvExportResult:
    """Result returned after creating a class-wise training CSV export."""

    output_dir: Path
    archive_path: Path
    csv_paths: list[Path]
    counts_by_file: dict[str, int]


class ExportService:
    """Service for exporting session data."""

    def export_session(self, session_dir: Path) -> Path:
        """Create a ZIP archive of the given session directory.

        Args:
            session_dir: Path to the session directory to archive.

        Returns:
            Path to the created ZIP archive.

        Raises:
            FileNotFoundError: If the session directory does not exist.
        """
        session_dir = Path(session_dir)
        if not session_dir.exists():
            raise FileNotFoundError(f"Session directory not found: {session_dir}")
        zip_base = session_dir.parent / session_dir.name
        archive_path = shutil.make_archive(str(zip_base), "zip", root_dir=session_dir)
        return Path(archive_path)

    def export_training_csv_bundle(
        self,
        *,
        session_dir: Path,
        traces: np.ndarray,
        source_name: str | None = None,
    ) -> TrainingCsvExportResult:
        """Export labeled traces as class-wise, headerless CSV files.

        Confident labels are written into per-class files. Labels marked as
        uncertain are written into a separate ``uncertain`` CSV and excluded
        from the class files. When a cell was saved multiple times, only the
        latest row in ``labels.csv`` is used.

        Args:
            session_dir: Session directory containing ``labels.csv``.
            traces: Trace matrix shaped ``timepoints x ROIs``.
            source_name: Original upload name, used in generated filenames.

        Returns:
            Paths and ROI counts for the generated CSV files and ZIP archive.

        Raises:
            FileNotFoundError: If ``session_dir`` or ``labels.csv`` is missing.
            ValueError: If traces or labels cannot be matched safely.
        """
        session_dir = Path(session_dir)
        if not session_dir.exists():
            raise FileNotFoundError(f"Session directory not found: {session_dir}")

        trace_matrix = np.asarray(traces)
        if trace_matrix.ndim != 2:
            raise ValueError("traces must be a 2D array shaped timepoints x ROIs")

        labels_df = self._load_latest_labels(session_dir)
        source_slug = _safe_filename_stem(source_name or _source_name_from_session(session_dir))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = session_dir / f"training_csv_export_{source_slug}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        class_indices: dict[LabelClass, list[int]] = {label: [] for label in _CLASS_FILE_SLUGS}
        uncertain_indices: list[int] = []

        for row in labels_df.itertuples(index=False):
            cell_index = int(getattr(row, "cell_index"))
            if cell_index < 0 or cell_index >= trace_matrix.shape[1]:
                raise ValueError(
                    f"Label for cell_index={cell_index} cannot be matched to traces with {trace_matrix.shape[1]} ROIs"
                )

            label_text = str(getattr(row, "label", ""))
            uncertain = _coerce_bool(getattr(row, "uncertain", False))
            label_class = _label_class_or_none(label_text)

            if uncertain or label_text.strip().lower() == "uncertain":
                uncertain_indices.append(cell_index)
                continue
            if label_class is None:
                raise ValueError(f"Unknown label class in labels.csv: {label_text!r}")
            class_indices[label_class].append(cell_index)

        csv_paths: list[Path] = []
        counts_by_file: dict[str, int] = {}
        file_prefix = f"data for training_{source_slug}"

        for label_class, indices in class_indices.items():
            if not indices:
                continue
            slug = _CLASS_FILE_SLUGS[label_class]
            path = output_dir / f"{file_prefix}_{slug}.csv"
            _write_trace_columns(path, trace_matrix, indices)
            csv_paths.append(path)
            counts_by_file[path.name] = len(indices)

        if uncertain_indices:
            path = output_dir / f"{file_prefix}_uncertain.csv"
            _write_trace_columns(path, trace_matrix, uncertain_indices)
            csv_paths.append(path)
            counts_by_file[path.name] = len(uncertain_indices)

        if not csv_paths:
            raise ValueError("No labeled ROIs were available for training CSV export")

        archive_path = output_dir.with_suffix(".zip")
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in csv_paths:
                archive.write(path, arcname=path.name)

        return TrainingCsvExportResult(
            output_dir=output_dir,
            archive_path=archive_path,
            csv_paths=csv_paths,
            counts_by_file=counts_by_file,
        )

    def _load_latest_labels(self, session_dir: Path) -> pd.DataFrame:
        labels_csv = session_dir / "labels.csv"
        if not labels_csv.exists():
            raise FileNotFoundError(f"labels.csv not found: {labels_csv}")

        df = pd.read_csv(labels_csv)
        required = {"cell_index", "label"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"labels.csv is missing required columns: {', '.join(sorted(missing))}")
        if df.empty:
            raise ValueError("labels.csv does not contain any label rows")

        df = df.dropna(subset=["cell_index"]).copy()
        df["cell_index"] = df["cell_index"].astype(int)
        if "uncertain" not in df.columns:
            df["uncertain"] = False
        return df.drop_duplicates(subset=["cell_index"], keep="last").sort_values("cell_index")


def _write_trace_columns(path: Path, traces: np.ndarray, indices: Iterable[int]) -> None:
    matrix = traces[:, list(indices)]
    pd.DataFrame(matrix).to_csv(path, index=False, header=False)


def _label_class_or_none(label: str) -> LabelClass | None:
    try:
        return LabelClass.from_str(label)
    except ValueError:
        return None


def _coerce_bool(value: object) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, np.integer)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", ""}:
        return False
    return bool(value)


def _safe_filename_stem(name: str) -> str:
    stem = Path(str(name)).stem or str(name)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    return stem or "recording"


def _source_name_from_session(session_dir: Path) -> str:
    recording_dir = session_dir.parent.name if session_dir.parent != session_dir else "recording"
    return recording_dir or "recording"


__all__ = ["ExportService", "TrainingCsvExportResult"]
