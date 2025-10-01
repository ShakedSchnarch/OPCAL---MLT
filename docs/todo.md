# Task List — OPCAL-MLT

- [x] STD rectangles: pre vs post
- [x] Visualization:
  - [x] Y-axis value
  - [x] Fix scale
- [x] Peak detection parameters
- [x] Code refactor
- [x] Update documentation and files
- [x] Tester
- [x] Sliding bar
- [x] Documentation standardization
- [ ]  Implement one-click launch (if applicable)
- [ ] Refresh option

## Critical
- [x] Extract clear text from `docs/dev/OPCal labeler notes.xlsx - הערות 2.pdf` (OCR or source request), document each note in a dedicated file/issue, and classify it (code/UX/docs). *Summaries captured in `docs/dev/summary_notes.md`.*
- [ ] Apply the documented notes: update code (`src/`), configuration (`scripts/`), and docs (`docs/`) as needed; track closure for each item.
- [ ] Investigate the `pytest` signal 11 crash when running from the repo root: reproduce in a clean virtual environment, identify the failing module (e.g. `tests/test_processing.py`), and patch code or dependencies.
- [ ] After the fix, run `pytest -vv` and archive the successful output under `docs/dev/`.
- [ ] Align version numbers across `pyproject.toml`, `src/opcal_mlt/app/main.py`, `README.md`, and `docs/CHANGELOG.md`; document the rationale in the changelog.
- [ ] Update `main.py` so `APP_VERSION` is sourced from a single location (e.g. `src/opcal_mlt/__init__.py`).
- [ ] Fix the macOS build pipeline: add the missing `scripts/OPCAL-Labeler.command` or remove the reference from `scripts/build-macos-zip.sh:12`, run the build script, and verify `dist/OPCAL-Labeler-macOS.zip` is runnable.
- [ ] Document the build log (commands + output) in `docs/dev/build-log.md` for publication transparency.
- [x] Produce dependency lock files (`requirements.txt` and `environment.yml`) for reproducible environments.
- [x] Update installation instructions in `README.md` and `docs/USER_GUIDE.md` to reference the new environment files.

## Near term
- [ ] Create `docs/methods/opcal_labeler_methodology.md` describing the statistical model, signal processing stages, and the tool’s contribution to the research pipeline.
- [x] Summarize the content of `docs/dev/*.pdf` into Markdown (`docs/dev/summary_notes.md`) and link to it from the README.
- [ ] Review the summarized documents and break out additional actionable tasks (append to this list or the issue tracker).
- [ ] Develop `scripts/merge_sessions_to_dataset.py` to gather all session folders (e.g. under `Labeled signals*/`) and merge `labels.csv`/`cell_map.csv` into a training dataset matching `docs/API.md`.
- [ ] Add a unit test (e.g. `tests/test_io.py`) verifying the new merge script preserves integrity (cell numbering, `session_id`, etc.).
- [ ] Expand tests for `opcal_mlt/app/session_io.py`, mocking the filesystem to cover directory creation, writes, and reloads.
- [ ] Add Streamlit UI tests (via `streamlit.testing` or mocks) to confirm the four-step flow remains intact after code changes.
- [x] Create `docs/testing.md` describing unit/integration/manual test protocols.
- [ ] Improve data management: move `Labeled signals 810 frames_160225 - NEW - Oscillatory` into `data/raw/`, document the structure in `data/README.md`, and draft a basic backup policy. *(Documentation in place; data move still pending.)*
- [ ] Add a simple backup script (e.g. `scripts/backup_sessions.py`) that exports a daily ZIP of raw and labeled data.

## Long term
- [ ] Build a QA pipeline: script label statistics (distribution, outliers, inter-annotator consistency) and publish a report (`docs/reports/qa_report.md`).
- [ ] Prototype semi-automatic labeling suggestions: implement `src/opcal_mlt/core/suggestions.py` and expose approve/reject options in the UI.
- [ ] Measure the impact of suggestion tooling on labeling time/consistency and add plots + analysis under `docs/reports/`.
- [ ] Produce a bilingual API guide (`docs/API_he.md`) with Python and R examples for downstream analysis.
- [ ] Create a project Dockerfile, run tests inside the container, and prepare CI to publish tagged images per release.
- [ ] Configure GitHub Actions (or alternative CI) to run linting, tests, package builds (pip + macOS zip), and publish signed release artifacts.
- [ ] Document the CI/CD workflow in `docs/devops.md` and add a flow diagram to `docs/assets/`.

## Additional notes from user feedback
- [x] Preserve workflow state across browser refreshes and avoid regressions that return users to earlier stages (snapshot persistence + URL tokens).
