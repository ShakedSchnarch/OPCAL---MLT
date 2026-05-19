# Changelog

All notable changes follow the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

## [1.1.0] - 2026-05-10
### Added
- Class-wise training CSV export from the Finish screen.
- Separate uncertain-label CSV export that excludes uncertain ROIs from class-specific files.
- Source filename and SHA-256 session metadata for newly uploaded source files.
- Windows PowerShell source launcher (`scripts/OPCAL-Labeler.ps1`) and explicit Windows install/run commands.

### Changed
- App and package version now come from `opcal_mlt.__version__`.
- `pytest` can run from the repository root without requiring an editable install first.
- README, Quickstart, User Guide, Distribution Playbook, and Testing Playbook now describe the training export and platform-specific setup paths.

### Fixed
- macOS source ZIP launcher referenced by `scripts/build-macos-zip.sh` now exists and installs/launches the local app.
- Session hydration treats string boolean values such as `"False"` as false instead of truthy text.

## [1.0.0-rc1] - 2025-08-21
### Added
- Router-driven Streamlit architecture with dedicated views for each stage of the workflow.
- Session logging (`session.log`) alongside the CSV exports for auditing.
- Text summaries for historical PDFs (`docs/dev/summary_notes.md`) and a testing playbook (`docs/testing.md`).

### Changed
- Updated STD shading policy: the pre-stimulus band remains fixed at 1·σ, the post-stimulus band scales with the user-selected `k`.
- Workspace navigation now highlights unlabeled cells and hydrates form controls with the last saved values.
- The export screen hydrates from disk before rendering statistics.

### Fixed
- Prevented stage desynchronisation on browser refresh by mirroring query parameters.
- Added explicit duplicate-cell-ID warnings during ingestion instead of failing silently.

### Documentation
- Restored the logo in `README.md` and added navigation links to all project docs.
- Updated installation instructions with `requirements-dev.txt` / `environment.yml` and linked to [docs/data/README.md](docs/data/README.md) and [docs/testing.md](docs/testing.md).
- Expanded the Quickstart, user guide, and API contract.

## [0.4.0] - 2025-08-17
### Added
- Summary-first finish screen with pie chart and labeled-cell table.
- Session resume flow and disk hydration for statistics.
- Core helper `opcal_mlt.core.features.summarize_labels` for label summaries.

### Changed
- Streamlined stepper navigation (Start → Upload → Label → Finish) with explicit actions only.
- Improved Streamlit state handling to avoid default-widget warnings.
- UI polish: consistent headings, light theme defaults, footer with version string.

### Fixed
- Prevented navigation to Finish without an initial label.
- Stabilised Streamlit media cache warnings.

## [0.3.0] - 2025-07-10
- Added labels `Uncertain` and `Drifting` (later replaced by the uncertainty flag).
- Introduced session resume capability and labeling progress bar.
- Persisted per-cell notes, refreshed favicon and logos.
- Revised API.md documentation and refactored code for clarity.

## [0.2.0] - 2025-05-02
- Added core labeling UI components.
- Switched exports from JSONL to CSV (`labels.csv`, `cell_map.csv`).
- Introduced the first STD shading visualisation.

## [0.1.0] - 2025-03-15
- Initial MVP skeleton with basic Streamlit interface and CSV ingest.
