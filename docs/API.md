# Data Formats & I/O Contracts (OPCAL‑Labeler v1.0.0)

This document defines the on‑disk formats used by **OPCAL‑Labeler** for input traces and session outputs. It is the source of truth for interoperability with downstream analysis and for reproducing annotations.

---

## 1) Inputs

### 1.1 Traces
- **CSV** — shape **T × N** (rows=time samples, columns=cells). Column headers are treated as cell IDs when available.
- **NPZ** — must contain `traces` (2D array **T × N`). Optional keys:
  - `recording_id` (string)
  - `cell_ids` (list/array of length **N**)
- **HDF5** *(optional, if enabled in your build)* — dataset `traces` with shape **T × N** and optional attributes/ancillary datasets `recording_id`, `cell_ids`.

### 1.2 Metadata (optional JSON)
Used only if provided externally; typical fields:
```json
{
  "recording_id": "rec_001",
  "fs_hz": 10.0,
  "cell_ids": ["cell_00000", "cell_00001", "..."]
}
```
Sampling rate (`fs_hz`) can also be set from the user interface.

### 1.3 Cell ID assignment
If cell IDs are missing or you choose to override them, Step 2 offers three mutually exclusive modes:
1) **Keep headers** from the uploaded file.
2) **Import mapping** from an external CSV with columns:
   - `cell_index` (int, 0‑based)
   - `cell_id` (str)
3) **Auto‑generate** IDs with prefix/padding/start settings.

When starting a new session for an existing recording, the app may **reuse** the latest `cell_map.csv` for that recording ID to preserve continuity across sessions.

---

## 2) Outputs — Session Directory Layout (CSV)

Each labeling session writes a self‑contained folder:
```
<save_dir>/<recording_id>/<YYYYmmdd_HHMMSS>_<annotator>/
├─ session.csv      # One header row with session metadata
├─ cell_map.csv     # Mapping: cell index → cell ID (full list)
├─ labels.csv       # One row per labeled cell
└─ peaks.csv        # One row per detected peak (optional)
```

### 2.1 `session.csv`
One row describing the session header. Columns:

| Column          | Type   | Description                                            |
|-----------------|--------|--------------------------------------------------------|
| `session_id`    | str    | Folder name `<YYYYmmdd_HHMMSS>_<annotator>`           |
| `recording_id`  | str    | Identifier of the recording                            |
| `annotator_id`  | str    | User‑provided annotator ID                             |
| `fs_hz`         | float  | Sampling rate (Hz) used in the session                 |
| `started_utc`   | str    | ISO‑8601 UTC timestamp when the session started        |
| `app_version`   | str    | App version (e.g., `1.0.0`)                            |
| `source_path`   | str    | Original filename uploaded (if any)                    |
| `source_sha256` | str    | Optional checksum of the source file                   |

### 2.2 `cell_map.csv`
Full mapping for reproducibility (written at session start):

| Column       | Type | Description                                   |
|--------------|------|-----------------------------------------------|
| `cell_index` | int  | 0‑based column index in the traces matrix     |
| `cell_id`    | str  | Stable cell ID used throughout the session    |

### 2.3 `labels.csv`
One row per **saved** label. Columns:

| Column                   | Type   | Description                                                                                       |
|--------------------------|--------|---------------------------------------------------------------------------------------------------|
| `session_id`             | str    | Session folder name                                                                               |
| `recording_id`           | str    | Recording identifier                                                                              |
| `annotator_id`           | str    | Annotator ID                                                                                      |
| `saved_utc`              | str    | ISO‑8601 UTC timestamp of the save                                                                |
| `cell_index`             | int    | 0‑based index of the cell                                                                         |
| `cell_id`                | str    | Cell ID (from `cell_map.csv`)                                                                     |
| `label`                  | str    | One of: `High-flat`, `High-oscillatory`, `Oscillatory`, `Low-activity`, `Drifting`  |
| `uncertain`              | bool   | True if the label is flagged as uncertain (via checkbox)                                        |
| `notes`                  | str    | Free‑text notes (may be empty)                                                                    |
| `filter_type`            | str    | `savgol` or `none`                                                                                |
| `filter_window`          | int    | Savitzky–Golay window (samples), if used                                                          |
| `filter_polyorder`       | int    | Savitzky–Golay polynomial order, if used                                                          |
| `baseline_method`        | str    | `rolling_median` or `percentile`                                                                  |
| `baseline_window_s_or_q` | float  | Window (seconds) for rolling median or percentile `q` (e.g., 25.0)                                |
| `sd_method`              | str    | Scale estimate name (currently `MAD`)                                                             |
| `threshold_k`            | float  | Multiplier *k* used for `baseline + k·SD`                                                         |
| `mean`                   | float  | Mean of the (possibly smoothed) trace                                                             |
| `std`                    | float  | Standard deviation of the trace                                                                   |
| `rms`                    | float  | Root‑mean‑square of the trace                                                                     |
| `frac_above_thr`         | float  | Fraction of samples above threshold                                                               |
| `peaks_per_min`          | float  | Number of peaks per minute                                                                        |
| `version`                | str    | App version written into the row                                                                  |

#### Example (`labels.csv`)

```csv
session_id,recording_id,annotator_id,saved_utc,cell_index,cell_id,label,uncertain,notes,filter_type,filter_window,filter_polyorder,baseline_method,baseline_window_s_or_q,sd_method,threshold_k,mean,std,rms,frac_above_thr,peaks_per_min,version
20250812_073000_ada,rec_001,ada,2025-08-12T07:31:10+00:00,57,cell_00057,High-oscillatory,False,"bursts at start",savgol,31,3,rolling_median,20.0,MAD,3.0,0.18,0.07,0.06,0.42,7.3,1.0.0
```

### 2.4 `peaks.csv` (optional but recommended)
One row per detected peak (only for labeled cells):

| Column         | Type  | Description                                  |
|----------------|-------|----------------------------------------------|
| `session_id`   | str   | Session folder name                          |
| `recording_id` | str   | Recording identifier                         |
| `cell_index`   | int   | 0‑based index of the cell                    |
| `peak_idx`     | int   | Sample index of the peak                     |
| `peak_time_s`  | float | Time of the peak in seconds                  |
| `peak_value`   | float | Value of the (smoothed) trace at the peak    |

### 2.5 Summary hydration (Step 4)
The **Finish** screen prefers to read labels and IDs from disk. If the in‑memory state is empty (e.g., after a browser refresh), it hydrates from `labels.csv` and `cell_map.csv` when present. Percentages in the summary are computed against the total number of cells when known (from `traces` or `cell_map.csv`), otherwise against the number of labeled cells.

---

## 3) Controlled Vocabulary — Labels

The allowed label values are fixed for consistency:

- High‑flat
- High‑oscillatory
- Oscillatory
- Low‑activity
- Drifting

Labels can be flagged as uncertain via the `uncertain` boolean column in `labels.csv`.

---

## 4) Programmatic helpers (core)

The app exposes a UI‑agnostic summary helper in core:

```python
from opcal_mlt.core.features import summarize_labels
labels_df, stats_df = summarize_labels(label_map, cell_ids, total_cells=None)
```
- `labels_df`: one row per labeled cell (`cell_index`, `cell_id`, `label`, `uncertain`, `notes`).
- `stats_df`: per‑class counts and percentages (0–100, 1 decimal place).

---

## 5) Legacy JSONL Output (Deprecated)

Earlier prototypes supported a JSONL output (one JSON object per cell). The current app uses **CSV** exclusively. For archival purposes, a legacy JSONL example is provided below; new tooling should rely on the CSV files detailed above.

```json
{
  "recording_id": "rec_001",
  "cell_id": "cell_057",
  "fs_hz": 10.0,
  "label": "High-oscillatory",
  "notes": "bursts at start",
  "preprocess": {
    "filter": {"type": "savgol", "window": 31, "polyorder": 3},
    "baseline": {"method": "rolling_median", "window_s": 20},
    "sd_method": "MAD",
    "threshold_k": 3.0
  },
  "features": {"mean": 0.18, "frac_above_thr": 0.42, "peaks_per_min": 7.3, "rms": 0.06},
  "peaks": [123, 201, 255, 480],
  "version": "0.4.0",
  "timestamp_utc": "2025-08-12T07:30:00Z"
}
```

---

## 6) Format changes in 0.4.0

- `labels.csv` example now reflects `version=0.4.0`.
- Added an explicit **hydration** note for Step 4 (reading `labels.csv`/`cell_map.csv`).
- Clarified the three ID‑assignment modes in Step 2.
- Documented optional HDF5 support where applicable.
- Introduced the core helper `features.summarize_labels` for programmatic summaries.

## 6) Format changes in 0.4.1

- Added a new boolean `uncertain` column to `labels.csv` to flag labels as uncertain via a checkbox.
- Removed the `Uncertain` label category from the controlled vocabulary; uncertainty is now indicated separately via the `uncertain` column.

## 7) Format changes in 1.0.0

- **No schema changes** to on‑disk CSVs (`session.csv`, `cell_map.csv`, `labels.csv`, `peaks.csv`).
- Clarified the visual policy for STD rectangles in the UI (pre‑stimulus band uses **k = 1**, post‑stimulus band uses **k**). This is a **visual aid only** and does not change any saved values.
- Router/dispatch refactors in the app do not affect I/O formats.
- Examples updated to show `app_version = 1.0.0`.