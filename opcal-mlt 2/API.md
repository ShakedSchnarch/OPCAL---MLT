# Data Formats & I/O Contracts (OPCAL‑Labeler v0.3.0)

This document defines the on-disk formats used by **OPCAL‑Labeler** for input traces and session outputs. It serves as the source of truth for interoperability with analysis pipelines and for reproducing annotations.

---

## 1) Inputs

### 1.1 Traces
- **CSV** — shape **T × N** (rows=time samples, columns=cells). Column headers are treated as cell IDs when available.
- **NPZ** — must contain `traces` (2D array **T × N**). Optional keys:
  - `recording_id` (string)
  - `cell_ids` (list/array of length **N**)

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

### Note on Cell ID Generation and Reuse
If cell IDs are missing or you choose to override them, the app can **auto-generate** IDs via the sidebar (prefix/padding/start). When starting a new session, the app can also **reuse** the latest `cell_map.csv` for the same recording ID to preserve continuity across sessions.

---

## 2) Outputs — Session Directory Layout (CSV)

Each labeling session writes a self-contained folder:
```
<save_dir>/<recording_id>/<YYYYmmdd_HHMMSS>_<annotator>/
├─ session.csv      # One header row with session metadata
├─ cell_map.csv     # Mapping: cell index → cell ID (full list)
├─ labels.csv       # One row per labeled cell
└─ peaks.csv        # One row per detected peak (optional)
```

### 2.1 `session.csv`
One row describing the session header. Columns:

| Column          | Type   | Description                                           |
|-----------------|--------|-------------------------------------------------------|
| `session_id`    | str    | Folder name `<YYYYmmdd_HHMMSS>_<annotator>`           |
| `recording_id`  | str    | Identifier of the recording                            |
| `annotator_id`  | str    | User-provided annotator ID                             |
| `fs_hz`         | float  | Sampling rate (Hz) used in the session                |
| `started_utc`   | str    | ISO-8601 UTC timestamp when the session started       |
| `app_version`   | str    | App version (e.g., `0.3.0`)                           |
| `source_path`   | str    | Original filename uploaded (if any)                   |
| `source_sha256` | str    | Optional checksum of the source file                   |

### 2.2 `cell_map.csv`
Full mapping for reproducibility (always written at session start):

| Column       | Type | Description                                  |
|--------------|------|----------------------------------------------|
| `cell_index` | int  | 0-based column index in the traces matrix    |
| `cell_id`    | str  | Stable cell ID used throughout the session   |

### 2.3 `labels.csv`
One row per labeled cell. Columns:

| Column                   | Type   | Description                                                                                 |
|--------------------------|--------|---------------------------------------------------------------------------------------------|
| `session_id`             | str    | Session folder name                                                                         |
| `recording_id`           | str    | Recording identifier                                                                        |
| `annotator_id`           | str    | Annotator ID                                                                               |
| `saved_utc`              | str    | ISO-8601 UTC timestamp of the save                                                        |
| `cell_index`             | int    | 0-based index of the cell                                                                  |
| `cell_id`                | str    | Cell ID (from `cell_map.csv`)                                                              |
| `label`                  | str    | One of: `High-flat`, `High-oscillatory`, `Oscillatory`, `Low-activity`, `Uncertain`, `Drifting` |
| `notes`                  | str    | Free-text notes (may be empty)                                                             |
| `filter_type`            | str    | `savgol` or `none`                                                                         |
| `filter_window`          | int    | Savitzky–Golay window (samples), if used                                                 |
| `filter_polyorder`       | int    | Savitzky–Golay polynomial order, if used                                                 |
| `baseline_method`        | str    | `rolling_median` or `percentile`                                                          |
| `baseline_window_s_or_q` | float  | Window (seconds) for rolling median or percentile `q` (e.g., 25.0)                        |
| `sd_method`              | str    | Scale estimate name (currently `MAD`)                                                    |
| `threshold_k`            | float  | Multiplier *k* used for `baseline + k·SD`                                                |
| `mean`                   | float  | Mean of the (possibly smoothed) trace                                                    |
| `std`                    | float  | Standard deviation of the trace                                                          |
| `rms`                    | float  | Root-mean-square of the trace                                                            |
| `frac_above_thr`         | float  | Fraction of samples above threshold                                                      |
| `peaks_per_min`          | float  | Number of peaks per minute                                                                |
| `version`                | str    | App version written into the row                                                         |

#### Example (`labels.csv`)

```csv
session_id,recording_id,annotator_id,saved_utc,cell_index,cell_id,label,notes,filter_type,filter_window,filter_polyorder,baseline_method,baseline_window_s_or_q,sd_method,threshold_k,mean,std,rms,frac_above_thr,peaks_per_min,version
20250812_073000_ada,rec_001,ada,2025-08-12T07:31:10+00:00,57,cell_00057,High-oscillatory,"bursts at start",savgol,31,3,rolling_median,20.0,MAD,3.0,0.18,0.07,0.06,0.42,7.3,0.3.0
```

### 2.4 `peaks.csv` (optional but recommended)
One row per detected peak (only for labeled cells):

| Column         | Type  | Description                                 |
|----------------|-------|---------------------------------------------|
| `session_id`   | str   | Session folder name                         |
| `recording_id` | str   | Recording identifier                        |
| `cell_index`   | int   | 0-based index of the cell                   |
| `peak_idx`     | int   | Sample index of the peak                     |
| `peak_time_s`  | float | Time of the peak in seconds                   |
| `peak_value`   | float | Value of the (smoothed) trace at the peak  |

---

## 3) Controlled Vocabulary — Labels

The allowed label values are fixed for consistency:

- High-flat
- High-oscillatory
- Oscillatory
- Low-activity
- Uncertain
- Drifting

---

## 4) Legacy JSONL Output (Deprecated)

Earlier prototypes supported a JSONL output (one JSON object per cell). The current app uses **CSV** exclusively. For archival purposes, a legacy JSONL example is provided below, but new tooling should rely on the CSV files detailed above.

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
  "version": "0.3.0",
  "timestamp_utc": "2025-08-12T07:30:00Z"
}
```

---

## 5) Changelog

- Switched from JSONL to CSV as the primary output format for session data.
- Added new label categories: `Uncertain` and `Drifting`.
- Introduced the ability to reuse `cell_map.csv` from previous sessions for the same recording ID to maintain cell ID continuity.
- Standardized terminology to use "cell ID" and "recording ID" consistently.
- Clarified and aligned descriptions across all sections for clarity and professionalism.