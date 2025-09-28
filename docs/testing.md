# Testing Playbook — OPCAL‑MLT

This document captures the testing policy for the project so release deliverables can be verified consistently.

## Test taxonomy
- **Unit tests** — live under `tests/unit/`; cover core signal utilities, domain models, and service logic (ingest, sessions, labeling).
- **Lightweight integration tests** — service-level tests using temporary directories to validate CSV creation and ZIP exports.
- **UI / Streamlit tests** — plan to leverage `streamlit.testing` or mocks to exercise the Start→Upload→Workspace→Finish flow (suite pending).
- **Manual smoke tests** — run representative CSV and NPZ datasets through the full flow, verifying state persistence after browser refresh.

## Local execution
```bash
# Assuming an activated venv/conda environment
pytest                     # run the full unit suite
pytest tests/unit/test_session_service.py  # target a single module

# Linting & formatting
ruff check src tests
black --check src tests
```

## Coverage expectations
- `core/preprocess`, `core/peaks`, `core/features` — numerical correctness and edge cases.
- `services/sessions` — directory creation, session header writing, hydration flows.
- `services/ingest` — CSV/NPZ loading, external ID application, error handling.
- `services/labeling` — feature calculation, CSV append behaviour, peak serialization.
- `app/session_io` — end-to-end CSV writes with mocked filesystem interactions (pending work).

## Planned additions
1. **Session merge tests** — once `scripts/merge_sessions_to_dataset.py` is implemented, create integrity checks for label consolidation.
2. **Automated UI smoke** — add a minimal Streamlit Testing API scenario to guard the multi-step flow.
3. **Label QA pipeline** — script that produces statistical reports on annotations (ties into the roadmap in `docs/todo.md`).

## Reporting
- Persist critical test runs (e.g. `pytest -vv`) under `docs/dev/build-log.md` when preparing releases.
- Include a brief summary of test results in release notes or supporting documentation.

For environment setup see `requirements-dev.txt`/`environment.yml`. Backup policies live in `docs/data/README.md`.
