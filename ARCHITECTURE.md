<!-- last_verified: 2026-06-05 -->
# Architecture

## Components

- **apps/web/** — Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
  - Dashboard with podcast metrics (shows, episodes, listening minutes, storage) + generation-activity chart
  - **Studio** — create a show, add source docs, generate a 2-host episode
  - **Shows library** — scoped explorer over the `shows/` prefix with inline audio player, transcript view, downloads
  - File upload with drag-and-drop, progress tracking (also reused for show-scoped ingestion)
  - Whole-bucket file browser with preview, download, delete
  - Dark mode via `next-themes`
- **services/api/** — FastAPI backend (layered architecture)
  - REST API for shows, episodes, sources, dashboard aggregations, files, upload
  - B2 S3 integration via boto3 (the only data store — no database)
  - **Generation pipeline** — LLM script generation + multi-voice TTS, run as a background task
  - File metadata extraction (images, PDFs) + source-doc text extraction (PDF/text/markdown)
  - Health check endpoint with B2 connectivity verification
  - Structured JSON logging with request tracing; Prometheus-format metrics endpoint
- **packages/shared/** — TypeScript type definitions
  - Mirrors Pydantic models from the API (files, shows, episodes, stats)
  - Consumed by `apps/web/` as a workspace dependency

## Backend Layering

The API follows a strict layered architecture:

```
types/     Pydantic models — no logic, no imports from other layers
  |
config/    Settings (pydantic-settings) — depends only on types
  |
repo/      Data access — B2 (boto3) + external SDK adapters (OpenAI LLM/TTS)
  |
service/   Business logic — orchestration, calls repo, returns types
  |
runtime/   FastAPI routes — calls service, never repo directly
```

### Layering Rules

1. Dependencies flow downward only: `types` -> `config` -> `repo` -> `service` -> `runtime`
2. No backward imports (e.g., service must not import from runtime)
3. **External SDKs are contained in `repo/`** — `boto3` (B2), and the OpenAI SDK (`repo/llm_client.py`, `repo/tts_client.py`). No raw SDK calls outside `repo/`.
4. All boundary data uses Pydantic models (no raw dicts across layers)
5. Each file stays under 300 lines

### Directory Structure

```
services/api/
  main.py                  App entrypoint, middleware, router registration, startup validation
  app/
    types/                 Pydantic models (FileMetadata, Show, Episode, PodcastStats, …)
    config/                Settings loaded from environment (B2_*, OPENAI_*, hosts/voices)
    repo/                  B2 S3 client + OpenAI LLM/TTS adapters (data/external access)
    service/               Business logic (upload, files, metadata, text_extract, shows, generation, dashboard)
    runtime/               FastAPI route handlers (upload, files, shows, dashboard, health, metrics)
  tests/                   pytest tests (structural + integration + mocked-provider generation)
```

## Generation Pipeline

Episode generation is decoupled from upload. Source documents are uploaded
first and live in B2; generation runs later as a FastAPI **background task**:

```
POST /shows/{id}/episodes
  -> service.shows.new_episode    (writes episode.json, status=pending)
  -> BackgroundTask: service.generation.generate_episode
       1. status -> generating (persisted to B2)
       2. repo.b2_client.get_object_bytes  — fetch each source back from B2
       3. service.text_extract             — PDF/text/markdown -> plain text
       4. repo.llm_client.generate_script  — OpenAI, structured JSON (2-host dialogue)
       5. write transcript.json to B2
       6. repo.tts_client.synthesize_line  — OpenAI TTS, one MP3 per line, per-host voice
       7. concatenate segments -> episode.mp3, write to B2
       8. status -> ready (with audio_key, duration); on error -> failed (with message)
```

The UI polls `GET /shows/{id}/episodes/{ep_id}` via TanStack Query
`refetchInterval` while the status is `pending`/`generating`, then stops.
The blaze generating loader is shown during the `generating` phase.

### Episode Lifecycle

`pending -> generating -> ready | failed`. Status and any error are persisted
in the episode's B2 manifest at each phase, so a crash leaves a `failed` or
partial record rather than a silent gap. Single-process background generation
is sufficient for a dev sample; a real queue/worker is noted in
[RELIABILITY.md](docs/RELIABILITY.md) and the tech-debt tracker.

## B2 Key Layout

```
shows/{show_id}/show.json                              # show manifest (title, created, source list, episode index)
shows/{show_id}/sources/{filename}                     # uploaded source docs
shows/{show_id}/episodes/{episode_id}/episode.json     # episode manifest (status, voices, timing, error)
shows/{show_id}/episodes/{episode_id}/transcript.json  # structured 2-host script [{speaker, text}]
shows/{show_id}/episodes/{episode_id}/episode.mp3      # synthesized audio
uploads/{filename}                                     # generic /upload destination
```

## Boundary Invariants

- **No external SDK leakage**: `boto3` and the OpenAI SDK are imported only in `app/repo/`. All other layers go through the repo interface.
- **No raw dicts at boundaries**: All data crossing layer boundaries uses typed Pydantic models.
- **No mutable globals**: Configuration is read-only after init.
- **Validated inputs**: All HTTP inputs validated by FastAPI/Pydantic. Object keys and show/episode ids validated against allowlists before any B2 access.

## Deployment

- **Local dev** — `pnpm dev` runs both services via `concurrently` (Web `:3000`, API `:8000`)
- **Railway** — two services from the same repo (see `infra/railway/README.md`)

## Data Stores

- **Backblaze B2** — object storage (S3-compatible API). Files, show/episode manifests (JSON), transcripts, and audio all live in a single bucket. No application database — B2 is the sole data store.

## External Services

- **Backblaze B2 S3 API** — storage, retrieval, listing, deletion, presigned URLs, **`get_object`** (read source bytes back for generation)
- **OpenAI** — chat completions (script generation) and audio speech (TTS)

## Trust Boundaries

See [docs/SECURITY.md](docs/SECURITY.md) for full security documentation.

- **Frontend -> API** — CORS-restricted to configured origins
- **API -> B2** — authenticated via application keys, signature v4, region from `B2_REGION`
- **API -> OpenAI** — `OPENAI_API_KEY` (env-only, never logged); source docs are untrusted input fed to the LLM
- **Client -> B2** — presigned URLs for download (attachment) and inline audio playback

## Data Flows

- **Create show**: Browser -> `POST /shows` -> service writes `show.json` to B2
- **Add source**: Browser -> `POST /shows/{id}/sources` (multipart) -> shared upload validation (doc allowlist, `shows/{id}/sources/` prefix) -> repo writes to B2 -> manifest updated
- **Generate**: Browser -> `POST /shows/{id}/episodes` -> episode created, background task runs the pipeline -> UI polls status
- **Listen / download**: Browser -> `GET /shows/{id}/episodes/{ep_id}` -> presigned inline (audio) + attachment (transcript) URLs
- **Dashboard**: Browser -> `GET /dashboard/{stats,recent-episodes,activity}` -> service aggregates across show/episode manifests + bucket storage
- **Files / Upload**: unchanged from the kept starter surfaces

## Observability

- Structured JSON logging on all requests with `request_id`
- Request timing middleware; `/metrics` (Prometheus format); `/health` (B2 connectivity)

## Canonical Files

- Generation orchestration: `services/api/app/service/generation.py`
- LLM adapter: `services/api/app/repo/llm_client.py`
- TTS adapter: `services/api/app/repo/tts_client.py`
- Show/episode manifest CRUD: `services/api/app/service/shows.py`
- B2 data access (repo layer): `services/api/app/repo/b2_client.py`
- Shows routes: `services/api/app/runtime/shows.py`
- Pydantic models: `services/api/app/types/` (`shows.py`, `files.py`, `stats.py`, …)
- Config (pydantic-settings): `services/api/app/config/settings.py`
- Structural tests: `services/api/tests/test_structure.py`
- Frontend API client: `apps/web/src/lib/api-client.ts`
- Shared TypeScript types: `packages/shared/src/types.ts`

## Core Features

- [Show Creation](docs/features/show-creation.md)
- [Episode Generation](docs/features/episode-generation.md)
- [Shows Library](docs/features/shows-library.md)
- [Dashboard](docs/features/dashboard.md)
- [File Upload](docs/features/file-upload.md)
- [File Browser](docs/features/file-browser.md)
- [Metadata Extraction](docs/features/metadata-extraction.md)

## References

- [docs/SECURITY.md](docs/SECURITY.md) — security principles and implementation
- [docs/RELIABILITY.md](docs/RELIABILITY.md) — reliability expectations
- [AGENTS.md](AGENTS.md) — architectural invariants and agent instructions
