# OPCAL-Labeler — Proposed Architecture

```
src/opcal_mlt/
├── app/
│   ├── app.py              # Streamlit entry point (replaces app/main.py)
│   ├── routing.py          # Stage router
│   ├── state.py            # Streamlit session_state adapter
│   ├── pages/              # Individual screens (start, ingest, workspace, export)
│   └── components/         # Reusable UI pieces (navigation, diagnostics, forms)
├── domain/
│   ├── enums.py            # Stage/label/baseline enumerations
│   ├── events.py           # Domain events (label saved, undo)
│   └── models.py           # Dataclasses for sessions, traces, labels, peaks
├── services/
│   ├── ingest.py           # Loading traces + assigning IDs
│   ├── labeling.py         # Persist labels/peaks, compute features
│   ├── sessions.py         # Session lifecycle (start/resume/hydration)
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
  - `test_domain_*` — validate dataclasses/enums behave as expected.
  - `test_services_*` — cover session, ingest, labeling, export services using tmp paths.
  - `test_app_state.py` — exercise the StateAdapter conversions.
- `tests/integration/`
  - `test_flow_labeling.py` — end-to-end flow across services (start → ingest → label → export).
  - `test_export_zip.py` — ensure archive contains expected files.
- Future optional UI smoke tests via `streamlit.testing` once pages are fully migrated.

## Migration Checklist
1. Introduce domain + services layers (this branch).
2. Move session hydration/export logic from `app/screens.py` into services.
3. Split `screens.py` into dedicated `app/pages/*` modules using the router.
4. Replace direct `st.session_state` access with `StateAdapter` in pages.
5. Delete legacy helpers once coverage confirms parity, update documentation.
