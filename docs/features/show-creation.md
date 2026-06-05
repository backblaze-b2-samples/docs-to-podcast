<!-- last_verified: 2026-06-05 -->
# Feature: Show Creation & Source Ingestion

## Purpose
Let a user create a show and attach source documents that later become the input for episode generation.

## Used By
- UI: `/studio` (Step 1 + Step 2)
- API: `POST /shows`, `GET /shows`, `GET /shows/{id}`, `POST /shows/{id}/sources`

## Core Functions
- `apps/web/src/components/studio/create-show-card.tsx` — create / pick a show
- `apps/web/src/components/studio/source-ingest-card.tsx` — drag-drop source upload (reuses the kept dropzone)
- `services/api/app/runtime/shows.py` — show + source routes
- `services/api/app/service/shows.py` — `create_show`, `add_source`, manifest CRUD
- `services/api/app/service/upload.py` — `process_upload(key_prefix=…, allowed_types=DOC_TYPES)`

## Canonical Files
- Manifest CRUD: `services/api/app/service/shows.py`
- Shared upload pipeline: `services/api/app/service/upload.py`

## Inputs
- title: str (CreateShowRequest)
- file: multipart upload (PDF / text / markdown only)

## Outputs
- `Show` manifest written to `shows/{id}/show.json`
- Source object written to `shows/{id}/sources/{filename}`; `SourceRef` appended to the show manifest
- Side effect: B2 writes (no database)

## Flow
- User creates a show → `POST /shows` writes the manifest, returns the new show
- User drops sources → each file streams to `POST /shows/{id}/sources`
- The source upload reuses the generic validation pipeline with a `shows/{id}/sources/` prefix and a doc-only type allowlist (`DOC_TYPES`)
- Re-uploading the same filename replaces that source ref (dedupe by key)

## Edge Cases
- Non-doc file type → 415 rejection (only PDF / text / markdown allowed for sources)
- Upload to a missing show id → 404
- Invalid / traversal show id → 400 (ids validated against an allowlist before B2 access)
- Empty or oversized file → 400 / 413

## UX States
- Empty: "No sources yet — add at least one before generating"
- Loading: per-file progress bars
- Error: toast per failed file

## Verification
- Test files: `services/api/tests/test_shows.py`, `services/api/tests/test_upload_conflict.py`
- Required cases: create + get show, list summaries, source dedupe, missing-show 404, key validation
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm typecheck && pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: all pytest tests green

## Related Docs
- [Episode Generation](episode-generation.md)
- [App Workflows](../app-workflows.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
