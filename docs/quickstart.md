# Quickstart — Label Your First Recording in 5 Minutes

> Designed for annotators who just received the tool and want to validate that everything works end-to-end.

---

## 1. Install the app

```bash
# Choose one option from the project root

# (A) venv + pip
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-dev.txt
pip install -e .

# (B) conda environment
conda env create -f environment.yml
conda activate opcal-mlt
pip install -e .
```

> When an official PyPI package is available you will be able to run `pip install opcal-mlt` inside a clean environment.

---

## 2. Launch Streamlit

```bash
opcal-mlt
# or
python -m opcal_mlt.app.main
```

The browser opens at `http://localhost:8501`. Keep the terminal visible for logs.

---

## 3. Create a session

1. In **Step 1 — Start session**, set:
   - `Annotator ID` → any meaningful identifier for provenance (e.g. `alice-lab`).
   - `Save directory` → accept the default (`~/OPCAL_LABELS`) or choose another location. The folder is created automatically.
2. Click **Save settings**.

---

## 4. Upload traces

1. Move to **Step 2 — Upload & indexing**.
2. Drag a `.csv` (shape `T × N`) or `.npz` file into the uploader.
3. Choose how to assign cell IDs:
   - `Auto-generate IDs` (default, produces `cell_00000`, ...).
   - `Use column headers` (CSV only).
   - `Import external mapping CSV` (columns `cell_index`, `cell_id`).
4. Wait for the success message showing the trace shape.

---

## 5. Label a few cells

1. Proceed to **Step 3 — Labeling workspace**.
2. Inspect the ΔF/F plot. Adjust smoothing, baseline window, and threshold `k` from the sidebar if needed.
3. Pick a label class, optionally add notes or mark as uncertain.
4. Click **Save label (CSV)**. The app writes to the session directory immediately.
5. Use ← / → to move between cells.

---

## 6. Review & export

1. After saving at least one label, go to **Step 4 — Finish & export**.
2. Review the statistics table and pie chart for sanity checks.
3. Click **Export session as ZIP** to create `<session>.zip` next to your CSVs.

---

## 7. Where to look next

- Need the full walkthrough? Read [docs/USER_GUIDE.md](USER_GUIDE.md).
- Integrating with analysis pipelines? See [docs/API.md](API.md).
- Extending the app? Start with [README.md](../README.md) and [docs/architecture.md](architecture.md).
