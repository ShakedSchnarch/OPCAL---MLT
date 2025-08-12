# OPCAL Manual Labeling Tool (MLT)

**OPCAL-Labeler** is a professional, cross-platform manual labeling tool designed for calcium imaging traces in neuroscience research. It enables accurate and efficient annotation of calcium signals, supporting advanced data analysis workflows.

The tool supports **six labeling classes**:  
`High-flat`, `High-oscillatory`, `Oscillatory`, `Low-activity`, `Uncertain`, and `Drifting` — with the ability to add per-cell notes for detailed annotation.

---

## 📦 Quick Start

### 1. From Source (Development Mode)
```bash
# Requires Python 3.10+
# (Optional) Create a virtual environment:
conda create -n opcal-mlt python=3.10 -y && conda activate opcal-mlt

# Install in editable mode
pip install -e .

# (Recommended for development)
poetry install

# Run the application
streamlit run app/main.py
```

### 2. From Prebuilt Distribution (ZIP)
Prebuilt ZIP archives are available for **Windows**, **macOS**, and **Linux**.  
Each contains a launcher script in the root directory for easy startup without opening a terminal.

- **Windows** → Double-click `OPCAL-Labeler.bat`  
- **macOS** → Double-click `OPCAL-Labeler.command` *(may require granting execution permission: `chmod +x OPCAL-Labeler.command`)*  
- **Linux** → Double-click or run `./OPCAL-Labeler.sh`

No additional installation steps are needed if Python 3.10+ is installed and available in the system PATH.

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
.
├── app/                  # Streamlit app entry point
├── core/                 # Core processing logic
├── examples/             # Example datasets
├── scripts/              # Launcher scripts (.bat, .sh, .command, .ps1)
├── tests/                # Unit tests
├── README.md
└── USER_GUIDE.md
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
- **Python**: 3.10+  
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