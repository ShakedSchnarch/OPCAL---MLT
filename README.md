# OPCAL Manual Labeling Tool (MLT) — v0.4.0

**OPCAL-Labeler** is a professional, cross-platform manual labeling tool designed for calcium imaging traces in neuroscience research. It’s a local Streamlit app focused on accurate, efficient annotation of calcium signals to support downstream analysis.

---

## 📦 Quick Start

```bash
# Requires Python 3.12+
pip install -e .

# Launch (CLI)
opcal-mlt

# Or explicitly via Streamlit
python -m streamlit run src/opcal_mlt/app/main.py --server.port=8501

# Optional: better auto-reload on macOS
xcode-select --install
pip install watchdog
```

---

## ✨ Features (v0.4.0)
- **Stepper-only navigation** with clear Step 1 actions (New / Resume / Load by path)
- **Light theme** polish; consistent headings and layout
- **Summary-first** finish screen with **pie chart** label distribution + labeled-cells table
- **Robust resume & summary**: hydrates `labels.csv` / `cell_map.csv` from disk when needed
- Safe Streamlit state handling (no post-widget mutation; fewer warnings)
- Load traces (`CSV`, `NPZ`, `HDF5`) and metadata
- Baseline & robust SD (MAD) calculation; dual-SD threshold visualization (green pre-stimulus / red post)
- Peak detection via `scipy.signal.find_peaks`
- One-click / shortcut labeling per cell with per-cell notes
- Progress bar and per-session provenance; export of `session.csv`, `labels.csv`, `peaks.csv`, `cell_map.csv`

For detailed usage, see [`USER_GUIDE.md`](USER_GUIDE.md).  
For data formats and API details, see [`API.md`](API.md).

---

## 🗂 File Structure
```
src/
└── opcal_mlt/
    ├── app/                  # Streamlit app (UI + launcher + session I/O)
    │   ├── main.py
    │   ├── screens.py
    │   ├── ui.py
    │   ├── session_io.py
    │   ├── launch.py
    │   └── assets/
    │       └── logo.png
    └── core/                 # Core processing & data helpers
        ├── __init__.py
        ├── features.py       # feature extraction + summaries
        ├── io.py
        ├── peaks.py
        ├── preprocess.py
        └── schemas.py

tests/
examples/
README.md
USER_GUIDE.md
API.md
```

---

## 📤 Session Outputs
Each session creates:
```
<save_dir>/<recording_id>/<YYYYmmdd_HHMMSS>_<annotator>/
├─ session.csv
├─ labels.csv
├─ peaks.csv
└─ cell_map.csv
```
**`labels.csv`** is the main output for downstream analysis, containing timestamps, annotator ID, and consistent cell indices for reproducibility.

---

## 🆕 What’s New in 0.4.0
- Summary-first finish screen with **pie chart** of label distribution
- Clear Step 1 actions and improved Light theme
- Disk hydration for resume/summary (`labels.csv`, `cell_map.csv`)
- Safer Streamlit state usage (no post-widget mutation)

---

## ⚙️ Requirements
- **Python**: 3.12+  
- **OS**: Windows, macOS, or Linux  
- **Disk Space**: Minimum 200MB free for typical projects  

---

## 🤝 Contributing
We welcome contributions!  
1. Fork the repository  
2. Create a new branch (`feature/your-feature`)  
3. Submit a pull request with a clear description

---

## 🚀 Release / Tagging (maintainers)
```bash
git add -A
git commit -m "release: OPCAL-Labeler 0.4.0 — summary-first UI, pie chart stats, safer state"
git tag -a v0.4.0 -m "OPCAL-Labeler 0.4.0"
git push && git push --tags
```

---

## 📜 License
This project is licensed under the [MIT License](LICENSE).

---