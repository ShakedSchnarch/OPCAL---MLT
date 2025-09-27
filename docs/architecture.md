# OPCAL-Labeler — Proposed Architecture

```
src/opcal_mlt/
├── app/
│   ├── app.py              # Streamlit entry point (replaces app/main.py)
│   ├── routing.py          # Stage router
│   ├── state.py            # Streamlit session_state adapter
│   ├── theme.py            # Shared light/dark palettes
│   ├── views/              # Individual screens (start, ingest, workspace, export)
│   └── components/         # Reusable UI pieces (navigation, diagnostics, forms)
├── domain/
│   ├── enums.py            # Stage/label/baseline enumerations
│   ├── events.py           # Domain events (label saved, undo)
│   └── models.py           # Dataclasses for sessions, traces, labels, peaks
├── services/
│   ├── ingest.py           # Loading traces + assigning IDs
│   ├── labeling.py         # Persist labels/peaks, compute features
│   ├── sessions.py         # Session lifecycle (start/resume/hydration + listings)
│   └── export.py           # ZIP export helpers
└── core/
    └── ...                 # Signal processing + low-level I/O
```

## Layering Principles
- **Core**: numerics and file-format helpers. No Streamlit imports.
- **Domain**: plain data models and enums shared across the app.
- **Services**: side-effectful operations (filesystem, CSV writes) implemented once.
- **App**: Streamlit UI that interacts with services and domain models only.

## Testing Strategy
- `tests/unit/`
  - `test_domain_models.py` — validates dataclasses/enums.
  - `test_session_service.py` — start/resume/hydration flows using tmp paths.
  - `test_ingest_service.py` — CSV/NPZ loading + ID assignment.
- Future optional suites: service-level integration tests (session → export) and Streamlit smoke tests using `streamlit.testing`.

## Migration Checklist
1. Introduce domain + services layers (this branch).
2. Move session hydration/export logic from `app/screens.py` into services.
3. Split `screens.py` into dedicated `app/views/*` modules using the router.
4. Replace direct `st.session_state` access with `StateAdapter` in pages.
5. Delete legacy helpers once coverage confirms parity, update documentation.
