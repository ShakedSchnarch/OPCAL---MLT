# User Guide — OPCAL‑MLT v1.0.0-rc1

This guide walks annotators and lab operators through the complete four-stage workflow: **Start → Upload → Workspace → Finish**. All data stays local and the app writes human-readable CSV files.

---

## Table of contents
- [Prerequisites](#prerequisites)
- [Launch the app](#launch-the-app)
- [Stage 1 — Start session](#stage-1--start-session)
- [Stage 2 — Upload & indexing](#stage-2--upload--indexing)
- [Stage 3 — Labeling workspace](#stage-3--labeling-workspace)
- [Stage 4 — Finish & export](#stage-4--finish--export)
- [Keyboard shortcuts](#keyboard-shortcuts)
- [Session outputs](#session-outputs)
- [Tips & troubleshooting](#tips--troubleshooting)

---

## Prerequisites

- Python 3.12 (as specified in `pyproject.toml`)
- Dependencies installed via `requirements-dev.txt` or `environment.yml`
- Project installed in editable mode (`pip install -e .`)
- Trace file in CSV (`T × N`) or NPZ format; optional metadata JSON/CSV with cell identifiers

---

## Launch the app

```bash
# Option A — venv
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-dev.txt
pip install -e .

# Option B — conda
conda env create -f environment.yml
conda activate opcal-mlt
pip install -e .

# Run Streamlit
opcal-mlt
# or
python -m opcal_mlt.app.main
```

The browser opens at `http://localhost:8501`. Keep the terminal visible in case the app emits log messages or errors.

---

## Stage 1 — Start session

> Goal: capture the annotator identity and storage location.

1. Choose **New session**, **Resume recent session**, or **Load session from path**.
2. For a new session:
   - Fill in **Annotator ID**.
   - Use the default save directory (`~/OPCAL_LABELS`) or specify a custom folder.
   - Click **Save settings**. The folder is created if it does not exist.
3. To resume a session:
   - Select it from the dropdown (shows recording ID, folder name, number of labels).
   - Click **Resume session** to hydrate state from disk.
4. To load from a specific path, provide a session directory containing `labels.csv` or `session.csv` and click **Load session**.

Once the preferences are saved, the footer **Next** button becomes active.

---

## Stage 2 — Upload & indexing

> Goal: load traces and confirm the cell identifier mapping.

1. Drag-and-drop a `.csv` or `.npz` file onto the uploader.
2. Verify the preview (table rows for CSV, key list for NPZ).
3. Choose a mapping strategy:
   - **Auto-generate IDs** — yields `cell_00000`, `cell_00001`, ...
   - **Use column headers** — CSV only; headers must match the column count.
   - **Use IDs from NPZ** — relies on a `cell_ids` array with matching length.
   - **Import external mapping CSV** — upload a helper file with `cell_index,cell_id` columns.
4. The app warns if duplicate IDs are detected so you can adjust the mapping.
5. After traces and IDs are ready, proceed to Stage 3.

---

## Stage 3 — Labeling workspace

> Goal: inspect each trace, fine-tune parameters, and save labels.

Layout overview:
- **Left column:** navigation controls (progress bar, previous/next buttons, jump to first unlabeled cell).
- **Middle column:** Plotly chart showing raw trace, smoothed trace, baseline, pre/post STD bands, and detected peaks.
- **Right column:** label selector, uncertainty toggle, notes input, and **Save label (CSV)** button.

Workflow tips:
1. Adjust sidebar parameters: smoothing (Savitzky–Golay), baseline method/window, STD multiplier `k`, and stimulus time.
2. Choose a label class (High-flat, High-oscillatory, Oscillatory, Low-activity, Drifting).
3. Tick **Mark as uncertain** if the annotation is doubtful.
4. Add free-text notes as needed.
5. Click **Save label (CSV)**. The app appends to `labels.csv` and `peaks.csv` (if peaks exist) and writes to `session.log`.
6. The workspace automatically advances to the next unlabeled cell; use ← / → or the navigation widgets to revisit previous cells.

---

## Stage 4 — Finish & export

> Goal: review outcomes and create an archive for sharing.

1. The app hydrates from disk (`labels.csv`, `cell_map.csv`) before rendering.
2. Review the label statistics: pie chart and detailed table (notes + uncertainty flag).
3. Click **Export session as ZIP** to produce `<session_dir>.zip` alongside the CSV files.
4. Use **Start a new session** to reset the state while preserving annotator/save-directory preferences.

---

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| `1` … `5` | Assign label classes (1 → High-flat, …, 5 → Drifting) |
| `S` | Save current label |
| `U` | Undo last label change |
| `←` / `→` | Navigate to previous / next cell |
| `+` / `−` | Increase / decrease STD multiplier `k` |
| `F` | Toggle smoothing |

Ensure the browser window is focused for shortcuts to work.

---

## Session outputs

| File | Purpose | Notes |
| --- | --- | --- |
| `session.csv` | Session metadata (IDs, timestamps, app version, sampling rate, source info) | One row per session start |
| `cell_map.csv` | Mapping from `cell_index` to stable `cell_id` | Rewritten when IDs change |
| `labels.csv` | Per-cell annotations with processing settings, derived features, uncertainty flag | Append-only |
| `peaks.csv` | Peak-level measurements (index, time, value) | Written only when peaks are present |
| `session.log` | Text audit trail of labeling actions | Optional but recommended |

See [docs/API.md](API.md) for detailed schemas.

---

## Tips & troubleshooting

- **Page refresh returns to Start:** ensure Stage 1 completed — the app only persists state after the session directory is created. Use **Resume** to hydrate an existing session.
- **Cannot proceed to Finish:** save at least one label so `labels.csv` exists.
- **Duplicate ID warning:** adjust the external mapping or switch to auto-generated IDs until all IDs are unique.
- **ZIP export fails:** confirm the session folder is writable and disk space is available.
- **Need more testing guidance:** consult [docs/testing.md](testing.md). For storage policies and backups see [docs/data/README.md](data/README.md).

For further assistance, share a browser screenshot and terminal logs with the development team.
