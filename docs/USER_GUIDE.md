# User Guide — OPCAL‑Labeler v0.4.1

OPCAL‑Labeler is a local **Streamlit** app for efficient, accurate labeling of calcium‑imaging traces. It guides you through a 4‑step flow: **Start → Upload → Label → Finish**. All data stays on your machine; session outputs are plain CSV files.

---

## 1) Launch

```bash
# From the project root
pip install -e .

# Option A: CLI entry point
opcal-mlt

# Option B: Explicit Streamlit command
python -m streamlit run src/opcal_mlt/app/main.py --server.port=8501
```
> Tip (macOS): For faster code reloads, install Watchdog: `xcode-select --install && pip install watchdog`.

---

## 2) Workflow (Step‑by‑step)

### Step 1 — Start session
Pick **one** action to initialize your work:
- **New session**: set *Annotator ID* and *Save directory*.
  - You can use the default folder (`~/OPCAL_LABELS`) or uncheck the box to choose a custom path.
- **Resume recent session**: select a session folder discovered under your save directory.
- **Load session from path**: browse to an existing session folder.

Click **Start** to confirm. Then use **Next** (bottom‑right) to move to Upload.

### Step 2 — Upload & indexing
- Upload a traces file: **CSV** or **NPZ** (HDF5 if applicable).
- Preview the first rows/columns to verify structure.
- Choose how to assign **cell IDs**:
  1. **Keep headers** from the file.
  2. **Import mapping** from an external CSV (columns: `cell_index,cell_id`).
  3. **Auto‑generate** IDs with prefix/padding options.

After a successful load, click **Next** to enter the labeling workspace.

### Step 3 — Labeling workspace
- Adjust parameters in the **sidebar** (smoothing, baseline, robust SD, thresholds, etc.).
- Inspect the plots: raw/smoothed signals, baseline, and dual‑SD threshold shading (pre‑stimulus green, post‑stimulus red).
- Select a **label** for the current cell, optionally add **notes**, and **Save label (CSV)**.
- You can also check **Mark as uncertain** to flag the label as uncertain.
- Navigate between cells with **← / →** (or the progress panel). You can undo the last change with **U**.
- **Next** remains disabled until at least one label is saved.

### Step 4 — Finish & export
- See **Label statistics** first: a **pie chart** of class distribution and a table of labeled cells.
- Click **Export session as ZIP** to package `session.csv`, `labels.csv`, `peaks.csv`, and `cell_map.csv`.
- Use **Start a new labeling session** to return to Step 1 and begin a fresh session (your exported data remains intact).

---

## 3) Keyboard Shortcuts

| Key(s)    | Action                                      |
|-----------|---------------------------------------------|
| 1         | Label as High‑flat                          |
| 2         | Label as High‑oscillatory                   |
| 3         | Label as Oscillatory                        |
| 4         | Label as Low‑activity                       |
| 5         | Label as Drifting                           |
| S         | **Save label (CSV)** for the current cell   |
| U         | Undo last label change                      |
| ← / →     | Navigate to previous / next cell            |
| + / −     | Increase / decrease SD threshold            |
| F         | Toggle smoothing                            |

---

## 4) Session outputs (CSV)
All files are written under the active **session directory**:

- `session.csv` — session metadata (IDs, parameters, timestamps, app version).
- `labels.csv` — one row per labeled cell: `cell_index, label, notes, uncertain` (+ timestamps if configured).
- `peaks.csv` — detected peaks per cell (indices, times, amplitudes, per‑cell stats).
- `cell_map.csv` — mapping from sequential index → external `cell_id`.

> The **Finish** screen hydrates its summary from disk (`labels.csv`, `cell_map.csv`) so you can refresh the page without losing progress indicators.

---

## 5) Tips & good practices
- Use a meaningful **Annotator ID** (Step 1) for provenance.
- Prefer a dedicated **save directory** (default: `~/OPCAL_LABELS`).
- Save frequently while labeling (`S`) — Next to Finish is enabled once at least one label is saved.
- You can re‑open a session via **Resume** (Step 1) at any time.

---

## 6) Troubleshooting
- **"Next" is disabled in Step 3** — Save at least one label (`S` or the Save button).
- **No statistics in Step 4** — Ensure `labels.csv` exists in your session folder (save a label first). The summary prefers disk data; refresh the page if needed.
- **Default path checkbox warning** — If you ever see a yellow warning about widget defaults, refresh the page. The app avoids post‑widget state mutation to prevent this.
- **Media file missing** — If the console shows `MediaFileHandler: Missing file …png`, refresh the page; this is a temporary Streamlit cache artifact.

---

## 7) Labels (default set)
- **High‑flat**, **High‑oscillatory**, **Oscillatory**, **Low‑activity**, **Drifting**

You can adapt names in code if your taxonomy differs. Any label can be flagged as uncertain via the checkbox.
