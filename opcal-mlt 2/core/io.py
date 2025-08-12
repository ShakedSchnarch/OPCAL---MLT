from __future__ import annotations
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, List

def load_traces(path: str | Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    path = Path(path)
    meta: Dict[str, Any] = {}
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        traces = df.values  # T x N
        cell_ids = list(df.columns.astype(str))
        meta["cell_ids"] = cell_ids
    elif path.suffix.lower() == ".npz":
        npz = np.load(path, allow_pickle=True)
        traces = npz["traces"]
        meta = {k: npz[k].item() if npz[k].dtype == object else npz[k].tolist() for k in npz.files if k != "traces"}
    else:
        raise ValueError(f"Unsupported format: {path.suffix}")
    return traces, meta

def save_jsonl(records: List[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
