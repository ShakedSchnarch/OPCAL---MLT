"""
I/O helpers for loading calcium traces and saving JSONL records.

This module provides functions to load calcium imaging traces from CSV or NPZ files,
returning both the trace data and associated metadata, as well as to save lists of
Python dictionaries as JSON Lines (JSONL) files. Basic validation and clear error
messages are provided for unsupported formats or missing data.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, List

def load_traces(path: str | Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load calcium traces and associated metadata from a CSV or NPZ file.

    Parameters
    ----------
    path : str or Path
        Path to the traces file. Supported formats: .csv (columns as cells), .npz (must contain 'traces').

    Returns
    -------
    traces : np.ndarray
        2D array of shape (T, N) with calcium traces, where T is time and N is number of cells.
    meta : dict
        Dictionary containing metadata. For CSV, includes "cell_ids" (list of column names).
        For NPZ, includes all keys except "traces".

    Raises
    ------
    ValueError
        If the file format is unsupported or required data is missing.
    """
    path = Path(path)
    meta: Dict[str, Any] = {}
    if path.suffix.lower() == ".csv":
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")
        df = pd.read_csv(path)
        if df.empty:
            raise ValueError(f"CSV file is empty: {path}")
        traces = df.values  # T x N
        cell_ids = list(df.columns.astype(str))
        meta["cell_ids"] = cell_ids
    elif path.suffix.lower() == ".npz":
        if not path.exists():
            raise FileNotFoundError(f"NPZ file not found: {path}")
        npz = np.load(path, allow_pickle=True)
        if "traces" not in npz:
            raise ValueError(f"NPZ file must contain a 'traces' array: {path}")
        traces = npz["traces"]
        # Gather metadata, converting objects to native Python types where possible
        meta = {
            k: npz[k].item() if npz[k].dtype == object else npz[k].tolist()
            for k in npz.files if k != "traces"
        }
    else:
        raise ValueError(f"Unsupported file format: '{path.suffix}'. Supported formats: .csv, .npz")
    return traces, meta

def save_jsonl(records: List[dict], path: str | Path) -> None:
    """
    Save a list of dictionaries as a JSON Lines (JSONL) file.

    Parameters
    ----------
    records : List[dict]
        List of Python dictionaries to serialize, one per line.
    path : str or Path
        Output file path. Parent directories are created if needed.

    Raises
    ------
    ValueError
        If `records` is not a list of dictionaries.
    """
    path = Path(path)
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        raise ValueError("records must be a list of dictionaries.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            # Minimal quoting for compact JSONL output
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
