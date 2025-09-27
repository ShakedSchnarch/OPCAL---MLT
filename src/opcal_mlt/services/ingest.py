"""Data ingestion helpers bridging raw file I/O and domain models."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from opcal_mlt.core.io import load_traces
from opcal_mlt.domain.models import TraceSet


class IngestService:
    """Facade around loading traces and generating cell identifiers."""

    def load_trace_set(self, source, *, default_fs: float | None = None) -> tuple[TraceSet, dict]:
        temp_path: Path | None = None
        try:
            if hasattr(source, "read"):
                data = source.read()
                if hasattr(source, "seek"):
                    source.seek(0)
                suffix = Path(getattr(source, "name", "uploaded")).suffix or ""
                from tempfile import NamedTemporaryFile

                with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(data)
                    temp_path = Path(tmp.name)
                traces, meta = load_traces(temp_path)
            else:
                traces, meta = load_traces(source)
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()
        cell_ids = meta.get("cell_ids") or self._auto_cell_ids(traces.shape[1])
        fs_hz = float(meta.get("fs_hz", default_fs or 1.0))
        return TraceSet(traces=traces, cell_ids=cell_ids, fs_hz=fs_hz), meta

    def _auto_cell_ids(self, count: int, *, prefix: str = "cell_", pad: int = 5, start: int = 0) -> List[str]:
        return [f"{prefix}{start + idx:0{pad}d}" for idx in range(count)]

    def apply_external_ids(self, trace_set: TraceSet, mapping: Iterable[str]) -> TraceSet:
        ids = list(mapping)
        if len(ids) != trace_set.traces.shape[1]:
            msg = "Mapping length does not match number of traces"
            raise ValueError(msg)
        return TraceSet(traces=trace_set.traces, cell_ids=ids, fs_hz=trace_set.fs_hz)

    def auto_cell_ids(self, count: int, *, prefix: str = "cell_", pad: int = 5, start: int = 0) -> List[str]:
        return self._auto_cell_ids(count, prefix=prefix, pad=pad, start=start)


__all__ = ["IngestService"]
