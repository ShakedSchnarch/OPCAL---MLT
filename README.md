# OPCAL‑MLT — Manual Labeling Tool

A lightweight Streamlit application for manual labeling of calcium imaging traces (ΔF/F) with baseline and stimulus‑aligned utilities.
![alt text](image.png)
> **Version:** **v1.0.0**
---

## Table of contents

- [OPCAL‑MLT — Manual Labeling Tool](#opcalmlt--manual-labeling-tool)
  - [Table of contents](#table-of-contents)
  - [Overview](#overview)
  - [Key features](#key-features)
  - [Installation](#installation)
  - [Quick start](#quick-start)
  - [Data inputs \& assumptions](#data-inputs--assumptions)
  - [Workflow](#workflow)
  - [STD rectangles: pre vs post](#std-rectangles-pre-vs-post)
  - [Project structure](#project-structure)
  - [Development](#development)
    - [Code style \& docs](#code-style--docs)
  - [Releases \& versioning](#releases--versioning)
  - [Troubleshooting](#troubleshooting)
  - [FAQ](#faq)
  - [License](#license)
    - [Changelog (pointer)](#changelog-pointer)

---

## Overview

OPCAL‑MLT is a manual labeling tool for trace data where the user defines event labels around a known stimulus time. The app emphasizes clear visualization of baseline vs. ΔF/F, consistent STD bands, and simple export of labels.

The codebase is split into `app/` (UI) and `core/` (signal utilities), striving for clear boundaries: UI renders; core computes.

## Key features

* Streamlined 4‑step flow (start → upload & index → label → finish & export).
* Baseline + ΔF/F visualization with robust statistics.
* **STD rectangles policy:** pre‑stimulus band (green) uses **k = 1**; post‑stimulus band (red) uses **k**.
* Keyboard navigation for fast annotation (if enabled in screens).
* Export labels to CSV within a session directory.

## Installation

Using an editable install during development:

```bash
# From repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

Run the app:

```bash
opcal-mlt
# or
python -m opcal_mlt.app.main
```

Default URL: `http://localhost:8501`

## Quick start

1. **Start session** — choose/create a working session.
2. **Upload & indexing** — load traces (`.npy`/`.csv`) and IDs; the app validates shapes and types.
3. **Label files** — browse cells, adjust stimulus parameters, add labels.
4. **Finish & export** — write labels to disk (`labels.csv` in the session folder).

## Data inputs & assumptions

* **Traces**: 2D array `[n_cells, n_samples]` (`float32` recommended).
* **Cell IDs**: 1D array/list of length `n_cells` (string/int).
* **Time**: either provided or inferred by sampling rate.
* **Stimulus time (seconds)**: used to split pre/post segments.

## Workflow

* Baseline is computed using a consistent method (rolling median or percentile) on the pre segment unless otherwise specified.
* ΔF/F is shown relative to baseline.
* A constant threshold can be derived as `baseline + k·STD_pre`; bands are drawn to guide the eye (see policy below).

## STD rectangles: pre vs post

To improve interpretability and match review policy:

* **Pre (green)**: band height = `baseline + 1·STD_pre` (i.e., **k = 1**).
* **Post (red)**: band height = `baseline + k·STD_post` (i.e., user‑controlled **k**).

> Note: Threshold logic may continue to use `baseline + k·STD_pre` for detection consistency; the rectangles are a visual aid and should not double‑apply `k`.

## Project structure

```
src/opcal_mlt/
  app/
    app.py           # Primary Streamlit runner (routing + layout + services)
    main.py          # Compatibility shim → simply imports and runs app.run()
    state.py         # Typed adapter around st.session_state
    routing.py       # Stage → page dispatcher
    theme.py         # Shared light/dark palettes + CSS injection helpers
    components/      # UI widgets (diagnostics, navigation, sidebar)
    views/           # start.py, ingest.py, workspace.py, export.py (Streamlit views routed internally)
    session_io.py    # CSV helpers (session header, labels.csv, etc.)
    plots.py         # Plotly figure builders (no Streamlit imports)
    workspace_logic.py # Deterministic processing for the labeling view
  core/
    preprocess.py    # Signal utilities (smoothing, baseline, robust SD)
    peaks.py         # Peak detection helpers
    features.py      # Feature extraction + label summaries
    io.py            # Trace loading helpers
  domain/            # Dataclasses + enums (SessionConfig, TraceSet, LabelClass, ...)
  services/          # Session/Ingest/Labeling/Export facades used by the UI layer
```

## Development

* Use `release/vX.Y` branches for release prep.
* Page functions follow the convention `render(*, state, …)` and are wired via `app.routing.Router`.
* Keep plotting code inside `app/plots.py`; Streamlit pages should stay lightweight and call into services/domain layers for side-effects.
* Avoid circular imports by keeping `theme.py`/`ui.py` free of page-level imports.

### Code style & docs

* Short docstrings (English) for public helpers.
* Remove unused imports; prefer explicit, minimal dependencies in UI files.
* Preserve existing visual design unless a change is explicitly approved.

## Releases & versioning

* Prepare a release branch: `git checkout -b release/v1.0`.
* Update `APP_VERSION` in `app/app.py` when finalizing.
* Add a `CHANGELOG.md` entry summarizing user-visible changes (see below).

**v1.0 highlights (planned):**

* Streamlit app refactored into modular pages + services under `app/`.
* Typed domain layer (`domain/models.py`) and service facades power all I/O.
* Simplified test tree (`tests/unit`) with coverage for the new services.

## Troubleshooting

Common runtime errors seen during refactors and their meaning:

* `KeyError: No route registered for stage: Stage.WORKSPACE`

  * **Cause:** a new Stage enum value was introduced without registering it.
  * **Fix:** call `router.register(...)` for the new stage inside `app/app.py`.

* `FileNotFoundError: Session directory not found` when reaching the Workspace page

  * **Cause:** start/ingest steps were skipped, so `session_dir` was never created.
  * **Fix:** complete Start + Upload steps, or set `annotator`, `save_dir`, `traces`, and `cell_ids` before jumping ahead.

* `ValueError: traces must be a 2D array (T x N)`

  * **Cause:** uploaded data has the wrong shape; the ingest service enforces 2D arrays.
  * **Fix:** reshape / re-save the trace file so each column represents a cell.

* `IndentationError` / `SyntaxError: unmatched ')'`

  * **Cause:** manual merges left a stray parenthesis/indent.
  * **Fix:** reformat the region and re‑run; prefer small, reviewable patches.

## FAQ

**Q:** Do I need a theme to run the app?
**A:** No. The app runs with defaults. If `get_theme` exists, it’s used; otherwise the UI sticks to existing palette.

**Q:** Why is pre band not multiplied by `k`?
**A:** This was a deliberate decision to keep pre‑stimulus variability as a 1·STD reference and emphasize the effect size after the stimulus.

## License

MIT (or project‑specific license — update here if different).

---

### Changelog (pointer)

See `CHANGELOG.md` for detailed entries. For this release, include:

* UI: no visual changes unless specified.
* Plots: pre/post STD rectangle policy update.
* Main: safer dispatch and optional theme usage.
* Screens: signature guarding and stimulus index bounds.
