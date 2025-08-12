# OPCAL Manual Labeling Tool (MLT)

OPCAL-Labeler is a professional, cross-platform manual labeling tool designed for calcium imaging traces in neuroscience research. It facilitates accurate and efficient annotation of calcium signals to support advanced data analysis.

The tool supports 6 classes for labeling: High-flat, High-oscillatory, Oscillatory, Low-activity, Uncertain, and Drifting, with the ability to add per-cell notes for detailed annotation.

## Quick start
```bash
# Requires Python 3.10+
# (optional) conda create -n opcal-mlt python=3.10 -y && conda activate opcal-mlt
pip install -e .
# For development, Poetry is recommended:
# poetry install
streamlit run app/main.py
```

## Current Features (v0.3.0)
- Load traces (CSV/NPZ/HDF5) and metadata
- Baseline & robust SD (MAD) calculation
- Threshold visualization (default 3 SD)
- Peak detection with `scipy.signal.find_peaks`
- One-click/shortcut labeling per cell, with per-cell label and notes persistence
- Session resume capability to continue labeling without loss
- Progress bar indicating labeling completion status
- Export labels and session data in CSV format (default)
- Logo and favicon customization
- Dual STD shading displayed (green pre-stimulus, red post-stimulus)
- Full provenance stored with each label

See `USER_GUIDE.md` for usage and `API.md` for data formats.

## Installation (cross-platform)
Prerequisite: Python 3.10+ installed and available on your system PATH. Dependencies are installed automatically.

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
The `labels.csv` file is the main output for downstream analysis and includes timestamps, annotator ID, and consistent cell indices for reproducibility. Dual STD shading is displayed (green pre-stimulus, red post-stimulus).

## Documentation
- [User Guide](USER_GUIDE.md) — Detailed usage instructions  
- [API Reference](API.md) — Data formats and API details  
- [Changelog](CHANGELOG.md) — Version history and updates  

## License
This project is licensed under the MIT License.
