# OPCAL Manual Labeling Tool (MLT)

A fast internal tool for manual labeling of calcium imaging traces into 4 classes:
**High‑flat, High‑oscillatory, Oscillatory, Low‑activity**.

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
