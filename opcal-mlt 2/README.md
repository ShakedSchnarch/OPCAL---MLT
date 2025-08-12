# OPCAL Manual Labeling Tool (MLT)

A fast internal tool for manual labeling of calcium imaging traces into 6 classes:
**High‑flat, High‑oscillatory, Oscillatory, Low‑activity, Uncertain, Drifting**.

## Quick start
```bash
# (optional) conda create -n opcal-mlt python=3.11 -y && conda activate opcal-mlt
pip install -e .
# Or with poetry:
# poetry install
streamlit run app/main.py
```

## Features in MVP
- Load traces (CSV/NPZ/HDF5) and metadata
- Baseline & robust SD (MAD) calculation
- Threshold visualization (default 3 SD)
- Peak detection with `scipy.signal.find_peaks`
- One‑click/shortcut labeling per cell, autosave JSONL
- Full provenance stored with each label

See `USER_GUIDE.md` for usage and `API.md` for data formats.


## Installation (cross‑platform)
Prerequisite: Python 3.10+ installed.
Recommended (isolated) install with pipx:
```bash
python -m pip install --user pipx
pipx ensurepath
pipx install .
opcal-mlt
```

Alternatively:
```bash
pip install -e .
opcal-mlt
```

## Session outputs (CSV)
Each session creates:
```
<save_dir>/<recording_id>/<YYYYmmdd_HHMMSS>_<annotator>/
├─ session.csv
├─ labels.csv
├─ peaks.csv
└─ cell_map.csv
```
Dual SD shading is displayed (green pre‑stimulus, red post‑stimulus).
