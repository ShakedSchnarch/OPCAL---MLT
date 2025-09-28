# OPCAL‑MLT · Manual Labeling Tool

<p align="center">
  <img src="src/opcal_mlt/app/assets/logo.png" alt="OPCAL-MLT logo" width="140" />
</p>

> Lightweight Streamlit workspace for labeling calcium imaging (ΔF/F) traces with baseline-aware visualization and reproducible exports.

---

## Quick links

- [User guide](docs/USER_GUIDE.md) — full walkthrough for annotators
- [Quickstart](docs/quickstart.md) — five-minute setup + first labels
- [Data & API contracts](docs/API.md) — CSV schemas, metadata fields, helpers
- [Architecture](docs/architecture.md) — layer-by-layer tour for contributors
- [Testing playbook](docs/testing.md) — unit/integration/UI procedures
- [Data guide](docs/data/README.md) — storage layout & backup policy
- [Research notes](docs/dev/summary_notes.md) — text summaries of PDF specs
- [Changelog](docs/CHANGELOG.md) — release history and upgrade notes

---

## At a glance

| Capability | Details |
| --- | --- |
| Guided flow | Four stages (Start → Upload & indexing → Workspace → Finish & export) with persistent session state |
| Visual policy | Pre-stimulus STD band fixed to 1·σ, post-stimulus band scales with `k`; thresholds stay consistent with detection logic |
| Outputs | Deterministic CSV bundle (`session.csv`, `cell_map.csv`, `labels.csv`, `peaks.csv`) plus optional ZIP export |
| Services | Typed domain + service layer for ingesting traces, saving labels, and exporting sessions |
| Versioning | App UI reports `1.0.0-rc1`; package metadata currently `0.4.0` while the team finalises the stable release |

---

## System overview

```
src/opcal_mlt/
  app/           # Streamlit UI, routing, state adapter, theming, custom components
  core/          # Signal processing helpers (preprocess, peaks, feature summaries)
  domain/        # Enums and dataclasses used throughout the app
  services/      # File-system aware facades (sessions, ingest, labeling, export)
```

Key concepts:
- **StateAdapter** wraps `st.session_state` to keep the UI typed and testable.
- **Router** binds workflow stages (`Stage.START → Stage.EXPORT`) to page render functions.
- **SessionService** owns session directory creation, hydration, and listings.
- **LabelingService** persists labels/peaks and computes summary features, all routed through `session_io` helpers to guarantee CSV schemas.

---

## Prerequisites

- Python **3.12** (match the version declared in `pyproject.toml`)
- Install dependencies via `requirements.txt` **or** the Conda `environment.yml`
- Node/JS is **not** required; Streamlit bundles its own frontend
- (Optional) `watchdog` package speeds up Streamlit autoreload on macOS/Linux

---

## Local setup

```bash
# Option A — venv + pip
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-dev.txt

# Option B — Conda environment
conda env create -f environment.yml
conda activate opcal-mlt

# Editable install for contributors
pip install -e .

# Launch the app (two equivalent options)
opcal-mlt
# or
python -m opcal_mlt.app.main
```

Default Streamlit address: `http://localhost:8501`

> **Tip:** running `opcal-mlt` copies `.streamlit/config.toml` from `src/opcal_mlt/app/config/streamlit_theme.toml` automatically (handled by `launch.py`).

---

## Data lifecycle

| Stage | What happens | Files touched |
| --- | --- | --- |
| Start | Create or resume a session; ensure `session_dir` exists | `session.csv` header, `cell_map.csv` (if IDs available) |
| Upload & indexing | Load traces (`.csv`/`.npz`), choose cell IDs (auto, headers, external map) | Populates in-memory trace set, optionally reuses prior `cell_map.csv` |
| Workspace | Visualise baseline vs ΔF/F, save labels with notes & uncertainty flag, compute peaks/features | Append rows to `labels.csv` and `peaks.csv` |
| Finish & export | Aggregate statistics, optionally ZIP the session folder | `labels.csv`, `cell_map.csv`, `session.csv`, `peaks.csv`, exported archive |
| Archive & backup | Copy session folders into `data/labeled_sessions/` and zip nightly | `data/` tree (see [Data guide](docs/data/README.md)) |

### CSV schemas (summary)
- `session.csv`: one row per app launch, including timestamps, annotator, app version, fs.
- `cell_map.csv`: stable mapping from `cell_index` → `cell_id`.
- `labels.csv`: per-cell annotations with processing metadata and derived features.
- `peaks.csv`: per-peak measurements linked to `labels.csv` rows.

Full field descriptions live in [docs/API.md](docs/API.md).

---

## Working on the codebase

### Tests & static checks

```bash
# Unit tests
pytest

# Linting (Ruff) & formatting (Black)
ruff check src tests
black --check src tests
```

Core unit suites live in `tests/unit/` and focus on domain/services correctness. Extend them when introducing new service behaviour or data formats. See [docs/testing.md](docs/testing.md) for full policy.

### Documentation standard

- Docstrings follow the Google style described in `docs/dev/documentation_style.md`.
- Keep module summaries concise and emphasise intent and domain context rather than restating types.
- Inline comments should explain *why* a choice was made or note domain caveats; remove redundant legacy notes when touching code.

### Streamlit development workflow
- Run `opcal-mlt` in one terminal with `--server.runOnSave=true` (Streamlit menu) for live reload.
- Keep business logic outside Streamlit pages: implement in `services/` or `core/`, then call from `views/`.
- Avoid writing to disk directly from views; always go through the relevant service so CSV schemas remain consistent.

### Release checklist (manual)
1. Align version strings (`pyproject.toml`, `app/app.py::APP_VERSION`, docs).
2. Update [docs/CHANGELOG.md](docs/CHANGELOG.md) with dated entries.
3. Smoke-test the 4-step flow on representative data (CSV and NPZ).
4. Bundle a release ZIP via `scripts/build-macos-zip.sh` (if distributing binaries).
5. Tag the release in Git and attach the docs/demos requested by the team.

---

## Troubleshooting

| Symptom | Likely cause | Suggested fix |
| --- | --- | --- |
| `KeyError: No route registered for stage` | New workflow stage added without router registration | Update `app/app.py` to register the stage with the `Router` |
| Session resets after page refresh | Session directory not initialised; state not hydrated | Complete Step 1 (annotator + save dir) or call `SessionService.hydrate_labels` |
| `ValueError: traces must be a 2D array (T x N)` | Uploaded trace file shape mismatch | Reshape input so columns represent cells |
| Duplicate cell ID warning | External mapping or headers contain repeats | Adjust mapping or regenerate IDs using the auto-ID helper |

If you hit an unexpected bug, enable `streamlit run ... --logger.level=debug` and consult the terminal logs alongside `session.log` written next to `labels.csv`.

---

For roadmap items, open tasks, and post-release actions see `docs/todo.md`.
