# Data Formats

## Input
- **Traces**: CSV (rows=time, columns=cells), or NPZ/HDF5 with `traces` 2D array (T x N)
- **Metadata** (JSON):
```json
{
  "recording_id": "rec_001",
  "fs_hz": 10.0,
  "cell_ids": ["cell_001", "cell_002", "..."]
}
```

## Output (JSONL)
One record per cell:
```json
{
  "recording_id": "rec_001",
  "cell_id": "cell_057",
  "fs_hz": 10.0,
  "label": "High-oscillatory",
  "is_uncertain": false,
  "notes": "bursts at start",
  "preprocess": {
    "filter": {"type":"savgol","window":31,"polyorder":3},
    "baseline": {"method":"rolling_median","window_s":20},
    "sd_method": "MAD",
    "threshold_k": 3.0
  },
  "features": {"mean": 0.18, "frac_above_thr": 0.42, "peaks_per_min": 7.3, "rms": 0.06},
  "peaks": [123, 201, 255, 480],
  "version": "mlt-0.1.0",
  "timestamp_utc": "2025-08-12T07:30:00Z"
}
```
