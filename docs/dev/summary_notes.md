# Development Document Summaries

> Text summaries of the binary documents stored in `docs/dev/` so contributors can reference them without opening large PDFs or spreadsheets.

## 1. Signal Processing Hub (134c57a2-2920-4dc4-8359-40e58ff0f7af_Signal_Processing_Hub.pdf)
- Describes the signal-processing assumptions for OPCAL, including filtering, normalization, and ΔF/F calculation.
- Provides a block diagram of the data flow from acquisition to feature extraction.
- Recommends validation checks: sampling rate verification, standard deviation sanity checks, Savitzky–Golay + MAD parameter sweeps.
- Action items:
  - Cross-check the diagram with `opcal_mlt/core/preprocess.py`.
  - Ensure the workspace plot reflects baseline and standard deviation consistently.

## 2. Pilot feedback notes (OPCal labeler notes.xlsx - הערות 2.pdf)
- Aggregates feedback from early testers regarding performance on large files, session persistence after refresh, and the UX of cell ID selection.
- Action items:
  - Document session hydration behaviour (`app/app.py`, `SessionService.hydrate_labels`).
  - Improve duplicate cell ID warnings during ingestion (implemented in the current build).
  - Track any remaining items in `docs/todo.md` or the issue tracker.

## 3. Build Manual Labeling Tool (ad3fc387-8352-4c0f-b656-ea84bf5d5f18_Build_Manual_Labeling_Tool.pdf)
- High-level product requirements: four explicit stages, immediate CSV persistence, optional ZIP export.
- UX specification for a single Plotly chart combining raw/smoothed traces, baseline, and threshold overlays.
- Stresses clear visual feedback (pre/post STD bands) and keyboard navigation.
- Action items:
  - Confirm the README and user guide cover all required behaviours (done).
  - Keep the architecture overview aligned with these requirements (done).

## 4. Refactor plan (e8d04ce7-71b3-4920-8417-656a020fc6d8_OPCal_Labeler_refactor.pdf)
- Documents the layered refactor (app/core/domain/services) and dependency boundaries.
- Recommends introducing `StateAdapter`, `Router`, and service facades to avoid circular imports.
- Action items:
  - Maintain unit tests for the major services (`tests/unit/test_session_service.py`, etc.).
  - Keep `docs/architecture.md` synchronized with the actual module layout (current version matches).

---

If new binary documents are added, summarize them here and link any follow-up tasks in `docs/todo.md`.
