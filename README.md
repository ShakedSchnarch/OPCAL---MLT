# OPCAL Manual Labeling Tool (MLT)

**OPCAL-Labeler** is a professional, cross-platform manual labeling tool designed for calcium imaging traces in neuroscience research. It enables accurate and efficient annotation of calcium signals, supporting advanced data analysis workflows.

The tool supports **six labeling classes**:  
`High-flat`, `High-oscillatory`, `Oscillatory`, `Low-activity`, `Uncertain`, and `Drifting` — with the ability to add per-cell notes for detailed annotation.

---

## 📦 Quick Start

```
# Requires Python 3.12+
pip install -e .
opcal-mlt
# or (explicit)
python -m streamlit run src/opcal_mlt/app/main.py
```

---

## ✨ Features (v0.3.0)
- Load traces (`CSV`, `NPZ`, `HDF5`) and metadata
- Baseline & robust SD (MAD) calculation
- Threshold visualization (default: 3 SD)
- Peak detection via `scipy.signal.find_peaks`
- One-click/shortcut labeling per cell, with per-cell notes persistence
- Session resume capability without data loss
- Progress bar indicating labeling completion
- Export labels and session data in CSV format
- Logo and favicon customization
- Dual STD shading (green pre-stimulus, red post-stimulus)
- Full provenance stored with each label

For detailed usage, see [`USER_GUIDE.md`](USER_GUIDE.md).  
For data formats and API details, see [`API.md`](API.md).

---

## 🗂 File Structure
```
src/
└── opcal_mlt/
    ├── app/                  # Streamlit app (UI + launcher + session I/O)
    │   ├── main.py
    │   ├── launch.py
    │   └── session_io.py
    │   └── assets/
    │       └── logo.png
    └── core/                 # Core processing logic (algorithms, schemas, I/O)
        ├── __init__.py
        ├── features.py
        ├── io.py
        ├── peaks.py
        ├── preprocess.py
        └── schemas.py

tests/
examples/
README.md
USER_GUIDE.md
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

## 📜 License
This project is licensed under the [MIT License](LICENSE).

---