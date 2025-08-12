# User Guide

## Keyboard shortcuts
- `1` High‑flat
- `2` High‑oscillatory
- `3` Oscillatory
- `4` Low‑activity
- `5` Uncertain
- `6` Drifting
- `S` Save, `U` Undo, `←/→` previous/next cell
- `+/-` change SD threshold, `F` toggle smoothing

## Workflow
1. Load a traces file (CSV/NPZ/HDF5). Example provided under `data_examples/`.
2. Adjust baseline method and SD threshold (default 3).
3. Review peaks and assign a label.
4. Add an optional note or choose the appropriate label.
5. Save and proceed to the next cell.

Autosave occurs every 60 seconds in `labels/` under the data directory.
