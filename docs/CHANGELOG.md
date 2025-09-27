# Changelog

## [1.0.0] - 2025-08-20
### Added
- Initial stable release of OPCAL-MLT.
- Standardized structure and documentation across all modules.
- Updated README, USER_GUIDE, and API documentation to reflect new version.

### Changed
- Refactored Streamlit entry (`app/app.py`) and theming to support router-driven views.
- Replaced legacy `screens.py` with modular `app/views/*` files and reusable components.
- Improved handling of STD * k rectangles in preprocessing logic (only post-stimulus red rectangle scaled, green remains baseline).

### Fixed
- Sidebar toggle issues resolved without affecting previous design.
- Standard deviation scaling bug fixed in preprocessing.

---

## 0.4.0 - 2025-08-17
- Summary-first finish screen: **pie chart** of label distribution + labeled-cells table shown **before** export
- Clear Step 1 actions (New / Resume / Load by path); stepper-only navigation (no auto-advance)
- Robust resume/summary: hydrate from disk (`labels.csv`, `cell_map.csv`) when in-memory state is empty
- Safer Streamlit state handling (no post-widget mutation); removed checkbox default conflicts
- Step 4: replaced "Next" with **Start a new labeling session**; export block moved below summary
- Statistics moved to core helper: `opcal_mlt.core.features.summarize_labels`
- UI polish: consistent headings, Light theme defaults, improved footer with version
- Documentation: updated README and USER_GUIDE for v0.4.0
- Bug fixes: prevent Next → Finish without any saved labels; stabilize media cache warnings

## 0.3.0
- Added new labels: `Uncertain` and `Drifting`
- Implemented session resume capability
- Added progress bar for labeling workflow
- Enabled per-cell label and notes persistence
- Updated favicon and logos
- Revised API.md documentation
- Refactored code for improved documentation and industry-standard style

## 0.2.0
- Added core labeling UI components
- Switched default export format from JSONL to CSV
- Introduced initial STD shading feature

## 0.1.0 - Initial MVP skeleton
