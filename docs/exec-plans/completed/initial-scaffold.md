# Scaffold plan: `docs-to-podcast`

> Source of truth for this delta: the fresh clone of `vibe-coding-starter-kit` at
> `.claude/scratch/vcsk-eeb21554-c465-4749-9538-ab33a8cd7727/` (HEAD `8fc490f`, 163 files).
> Parent standards: `sampleapps/../CLAUDE.md` (S3-only default, custom user agent, `B2_*` env names).

---

## 1. Purpose

`docs-to-podcast` is a NotebookLM-style "audio overview" generator built on the starter kit. A user
creates a **show**, uploads source documents (PDFs, articles, notes), and the app generates a
conversational **2-host podcast episode** discussing the material: an LLM writes a two-speaker
dialogue script, a multi-voice TTS provider renders it to audio, and the **source docs +
transcript + episode audio** are all archived together in Backblaze B2 under a per-show / per-episode
prefix. It targets the highest-volume current AI-search intents ("NotebookLM alternative", "AI
podcast generator", "audio overview") and is a natural B2 demo: each episode is a self-contained
bundle of related objects, exactly the shape object storage is good at. Audience: developers
evaluating B2 for AI artifact storage, and vibe-coders who want a recognizable end-to-end AI app
wired to durable storage out of the box.

**Resolved open questions (from the concept brief):**
- **2-host, configurable.** Default to two named hosts with distinct voices; host names + voices are
  env-configurable. Single-host is a future toggle, not v1.
- **Full-episode render, not streaming.** Generation runs as a FastAPI `BackgroundTask`; the episode
  carries a status (`pending → generating → ready | failed`) persisted in its B2 manifest, and the UI
  polls episode status (TanStack Query `refetchInterval`) showing the starter's `generating-loader`.
  Streaming/SSE generation is noted as a future enhancement (tech-debt tracker).

---

## 2. Architecture delta from `vibe-coding-starter-kit`

The starter kit is the ceiling — we **keep** the full scaffold, **adapt** the dashboard, **add** the
podcast pipeline + two new screens, and **trim** only starter-specific history/screenshots. The
backend keeps its strict `types → config → repo → service → runtime` layering and all structural
tests; every new external API (Claude, TTS) is wrapped in a `repo/` adapter, consistent with the
existing `boto3`-only-in-`repo/` invariant.

### KEEP (as-is, do not strip/rename)
- **UI kit / design system** — `apps/web/src/components/ui/`, design tokens in `globals.css`, the
  `/design` reference page. Build new screens with these primitives only.
- **Upload** — `/upload` route + `components/upload/` (dropzone, progress). Retained per AGENTS.md §2
  as the generic bucket-upload surface; the Studio reuses these components for show-scoped ingestion.
- **Files explorer (full-bucket browse)** — `/files`, `app/files/`, `components/files/`, and the Files
  sidebar entry. **Non-negotiable keep** (parent skill rule). This is the whole-bucket explorer.
- **Backend layering + structural tests** — `services/api/app/{types,config,repo,service,runtime}`,
  `tests/test_structure.py` (layering, boto3-containment, 300-line limit, all-layers-exist), JSON
  logging, `/health`, `/metrics`, request-id middleware, CORS/startup validation in `main.py`.
- **Data layer discipline** — TanStack Query hooks in `lib/queries.ts` + `lib/api-client.ts`; no bare
  `useEffect + fetch`. New endpoints touch exactly `runtime/*.py` + `api-client.ts` + `queries.ts`.
- **Metadata extraction** — `service/metadata.py` (checksums, PDF info, image dims). The shared
  `FileMetadataDetail` type already carries audio fields (`duration_seconds`, `codec`, `bitrate`) — we
  reuse those for generated episodes.
- **Dev ergonomics** — `pnpm dev`, `scripts/{dev.sh,doctor.mjs,pick-port.mjs}`, Railway infra docs,
  pre-commit config, e2e harness.

### ADD (new for `docs-to-podcast`)
- **Studio** — `/studio` route + `components/studio/`. The headline workflow: create a show → upload
  source docs (reusing the kept dropzone) → choose host names/voices → **Generate episode** →
  progress via the kept `generating-loader`.
- **Shows / Library** — `/shows` route + `components/shows/`. **The sample-specific asset explorer
  scoped to the sample's own folder** (`shows/` prefix) required by the parent skill alongside the
  full-bucket Files explorer. Lists shows; drill into a show to see its sources + episodes with an
  inline HTML5 audio player, transcript view, and per-asset download.
- **Sidebar nav** gains **Studio** and **Shows** entries (between Dashboard and Upload); branding
  changes from "OSS Starter Kit" to "Docs to Podcast".
- **Backend pipeline (all new, layering-compliant):**
  - `repo/llm_client.py` — Anthropic Messages API wrapper (script generation).
  - `repo/tts_client.py` — TTS provider wrapper (per-line, multi-voice synthesis).
  - `repo/b2_client.py` — **extend** with `get_object` (read source bytes back) + small JSON
    object get/put helpers for show/episode manifests. `boto3` stays only here.
  - `service/shows.py` — show & episode manifest CRUD on B2 (create/list/get show, add source,
    list/get episodes). B2 is the sole data store — no DB.
  - `service/text_extract.py` — extract plain text from source docs (PDF via PyPDF2, `.txt`/`.md`
    direct) to feed the LLM.
  - `service/generation.py` — orchestrates: fetch sources → extract text → `llm_client` →
    structured 2-host script → save transcript JSON → `tts_client` per line → assemble MP3 → save
    audio → update episode status. (Split into a `service/script.py` helper if it nears 300 lines.)
  - `runtime/shows.py` — routes: `POST /shows`, `GET /shows`, `GET /shows/{id}`,
    `POST /shows/{id}/sources` (multipart), `POST /shows/{id}/episodes` (kicks off generation via
    `BackgroundTasks`), `GET /shows/{id}/episodes/{ep_id}` (status + result for polling).
  - `types/shows.py` — `Show`, `Episode`, `EpisodeStatus`, `ScriptLine`, `GenerateEpisodeRequest`,
    `ShowSummary` (Pydantic, mirrored into `packages/shared`).
- **Shared types** — `Show`, `Episode`, `ScriptLine`, `EpisodeStatus`, request/response models added
  to `packages/shared/src/types.ts`.
- **DRY refactor** — generalize `service/upload.py::process_upload` to accept a `key_prefix` (default
  `uploads/`) so show-scoped source upload reuses the same validation rather than duplicating it;
  restrict source uploads to a doc-only type allowlist (pdf, txt, md).
- **Tests** — generation tests with **mocked** `llm_client`/`tts_client` (no real API calls, no
  network, no keys in CI); show/episode key-validation tests; updated dashboard stats tests. Keep all
  structural tests green (new SDKs live in `repo/`, so `test_boto3_only_in_repo` is unaffected).
- **Exec plan** — this plan is moved to `docs/exec-plans/completed/initial-scaffold.md` at finalize.

### ADAPT (rewrite for the use case)
- **Dashboard** (`/` + `components/dashboard/`) — replace generic upload stats with podcast metrics:
  total shows, total episodes, total listening minutes, storage used; recent episodes table;
  generation-activity chart. New aggregations flow through `runtime → service → repo` and TanStack
  Query hooks (no bare fetch). `docs/features/dashboard.md` updated in the same change.
- **Settings** (`/settings`) — keep; surface read-only defaults for host names + voices and the
  configured providers/models (no secrets rendered). Light touch.
- **App metadata / titles** — `layout.tsx` title, FastAPI `title=`, sidebar label, README hero.

### TRIM (remove from starter)
- `docs/exec-plans/completed/2026-02-*.md` and `2026-02-14-*` — starter-kit history, irrelevant here.
- `docs/images/b2-starterkit-dashboard1.png`, `b2-starterkit-fileview2.png` — starter screenshots that
  don't match this UI. Remove and replace the README "What it looks like" block with a short
  placeholder note (screenshots to be captured later via the `sample-screenshotter` skill).
  **No new binary assets are created during scaffolding** (per skill rule — ask before creating any).

> The bucket explorer (`/files`) is **kept** and a **scoped asset explorer** (`/shows`) is **added** —
> both requirements of the parent skill are satisfied. Nothing about removing the bucket explorer.

---

## 3. B2 surface (S3-compatible only — no b2-native)

All access is through the S3-compatible API via `boto3`, contained in `repo/b2_client.py`, with the
custom user agent set on the single shared client. Operations exercised:

| S3 operation | Used for | Status |
|---|---|---|
| `head_bucket` | `/health` connectivity check | kept |
| `put_object` | upload sources, write transcript JSON, write episode MP3, write manifests | kept |
| `list_objects_v2` (+ pagination) | Files explorer, Shows listing (prefix/delimiter on `shows/`), dashboard stats | kept |
| `head_object` | file metadata | kept |
| `delete_object` | delete files / shows | kept |
| `generate_presigned_url` | download + inline audio playback (episode MP3) | kept |
| **`get_object`** | **read source-doc bytes back from B2 so the generator can extract text** | **NEW** |

`get_object` is the only new S3 call. Justification: generation is decoupled from upload (background
task), and B2 is the system of record for sources — the generator fetches them from B2 rather than
holding bytes in memory. Still fully S3-compatible. **No b2-native API anywhere.**

**B2 key layout (per-episode bundle — the "naturally B2-shaped" demo):**
```
shows/{show_id}/show.json                              # show manifest (title, created, source keys, episode index)
shows/{show_id}/sources/{filename}                     # uploaded source docs
shows/{show_id}/episodes/{episode_id}/episode.json     # episode manifest (status, voices, timing, error)
shows/{show_id}/episodes/{episode_id}/transcript.json  # structured 2-host script [{speaker, text}]
shows/{show_id}/episodes/{episode_id}/episode.mp3      # synthesized audio
uploads/{filename}                                     # generic /upload destination (kept, unchanged)
```
Show/episode metadata are JSON objects in B2 (no database), consistent with the starter's "B2 is the
sole data store" stance. Single-process background generation + B2-persisted status is fine for a dev
sample; a real queue/worker is noted as future work in the reliability/tech-debt docs.

---

## 4. Key features (seed README + `docs/features/*.md`)

1. **Show creation & source ingestion** — create a show, drag-drop PDFs/articles/notes; stored under `shows/{id}/sources/`.
2. **AI 2-host script generation** — Claude turns the sources into a structured two-speaker dialogue (Host A / Host B), saved as `transcript.json`.
3. **Multi-voice audio synthesis** — each line rendered with the speaker's assigned voice; assembled into one `episode.mp3`.
4. **Shows library + player** — scoped explorer of `shows/`: browse shows, listen inline, read the transcript, download any artifact.
5. **Podcast dashboard** — shows, episodes, total listening minutes, storage, recent-episode + generation-activity views.
6. **Whole-bucket Files explorer** — the kept starter browser over every object (sources, transcripts, audio, generic uploads).

---

## 5. Doc transforms

| Starter doc | Action |
|---|---|
| `README.md` | **Rewrite** — new hero/feature list/tech stack (add OpenAI for LLM + TTS); Quick Start adds `B2_*` (renamed + `B2_REGION`) and a single `OPENAI_API_KEY`; drop "Use this template" framing (this is a finished sample); replace screenshots with placeholder note. Keep B2 links/UTM with renamed content tag. |
| `AGENTS.md` | **Adapt** — repo map + layering kept; §2 becomes "Project structure / what's app-specific"; add invariant note that LLM/TTS clients live in `repo/`; document the generation pipeline + new commands. |
| `ARCHITECTURE.md` | **Adapt** — add generation-pipeline component, `repo/llm_client.py` + `repo/tts_client.py` adapters, the `shows/` key layout, episode lifecycle, background-task + status-polling data flow, the new `get_object` use. |
| `docs/features/dashboard.md` | **Rewrite** for podcast metrics. |
| `docs/features/file-upload.md`, `file-browser.md`, `metadata-extraction.md` | **Keep**, light edits (upload note for show-scoped ingestion; metadata extended with source text + audio fields). |
| `docs/features/show-creation.md`, `episode-generation.md`, `shows-library.md` | **ADD** new feature docs from `_template.md`. |
| `docs/app-workflows.md` | **Rewrite** — journeys: create show → upload → generate → listen/download. |
| `docs/dev-workflows.md` | **Adapt** — LLM/TTS env, testing generation with mocked providers, `vibe-coding-starter-kit` → `docs-to-podcast` references. |
| `docs/SECURITY.md` | **Adapt** — LLM/TTS API keys (env-only, never logged), prompt-injection note (source docs are untrusted input), presigned URLs for audio. |
| `docs/RELIABILITY.md` | **Adapt** — generation failure handling, partial/failed episodes, retries, single-process background-task durability caveat. |
| `docs/design-system.md`, `CODE_REVIEW.md` | **Keep**, rename references only. |
| `docs/exec-plans/tech-debt-tracker.md` | **Reset/adapt** — add: simple MP3 concat vs. gapless assembly; in-process generation vs. queue; no streaming generation yet. |
| `docs/exec-plans/completed/2026-02-*` | **Delete** (starter history). |
| `CLAUDE.md` | **Keep** (`@AGENTS.md` pointer). |

---

## 6. Rename table (every identifier)

| From | To | Where (counts from grep) |
|---|---|---|
| `vibe-coding-starter-kit` (kebab) | `docs-to-podcast` | 23 hits: `package.json` (name), `packages/shared/package.json`, `apps/web/package.json`, `next.config.ts` `transpilePackages`, `dev:web`/`build`/`test:e2e` filter scripts, `README.md`, `docs/dev-workflows.md`, `docs/SECURITY.md`, and TS imports |
| `@vibe-coding-starter-kit/web` | `@docs-to-podcast/web` | `apps/web/package.json`, root `package.json` filter scripts |
| `@vibe-coding-starter-kit/shared` | `@docs-to-podcast/shared` | `packages/shared/package.json`, `next.config.ts`, all `import … from "@vibe-coding-starter-kit/shared"` (api-client, queries, file-tree, file-browser, file-metadata-panel, file-preview, command-palette, upload-progress) |
| `Vibe Coding Starter Kit` / `Vibe Coding OSS Starter Kit` (Title) | `Docs to Podcast` | `README.md` h1, `CODE_REVIEW.md` h1 |
| `OSS Starter Kit` | `Docs to Podcast` | `apps/web/src/app/layout.tsx` (`metadata.title`), `components/layout/app-sidebar.tsx` (header span), `services/api/main.py` (`FastAPI(title=…)`), `CODE_REVIEW.md` |
| `OSS Starter Kit API` | `Docs to Podcast API` | `services/api/main.py` |
| `b2ai-oss-start` | `b2ai-docs-to-podcast` | **user_agent_extra** in `repo/b2_client.py` (Standard #2) **and** `utm_content` tags in `README.md` (×3), `app-sidebar.tsx` footer link, `scripts/doctor.mjs`. ⚠️ If the board sub-issue for this sample specifies a different `user_agent_extra`, use that value instead — confirm at build time. |
| `b2-starterkit-dashboard1.png`, `b2-starterkit-fileview2.png` | *(removed)* | `docs/images/` + README refs deleted (no new binaries created during scaffold) |
| App description "File management dashboard…" | "Turn documents into a 2-host AI podcast, archived on Backblaze B2" | `layout.tsx` metadata description, FastAPI `description=` |

**Image tags / workflow slugs:** none present — no `.github/workflows/`, no `Dockerfile`, no
docker-compose in the starter tree. Nothing to rename there.

---

## 7. Env vars (`.env.example`) — **brings sample into Standard #3 compliance**

The starter deviates from parent Standard #3: it uses `B2_KEY_ID` and has **no** `B2_REGION`. The new
sample **must** rename to the standard names and add region (passed as `region_name` to the boto3
client). New vars for the LLM/TTS providers are added.

```
# Backblaze B2 (required) — Standard #3 names
B2_APPLICATION_KEY_ID=your_key_id        # renamed from B2_KEY_ID
B2_APPLICATION_KEY=your_application_key
B2_BUCKET_NAME=your-bucket-name
B2_ENDPOINT=your_b2_endpoint
B2_REGION=us-west-004                     # NEW — required by Standard #3, passed to boto3
# B2_PUBLIC_URL=                          # optional, kept

# OpenAI — powers BOTH script generation and TTS (single key) — required
OPENAI_API_KEY=your_openai_api_key
LLM_MODEL=gpt-4o-mini                      # cheap default; env-configurable
TTS_MODEL=gpt-4o-mini-tts                  # OpenAI multi-voice TTS; env-configurable
TTS_VOICE_HOST_A=alloy
TTS_VOICE_HOST_B=verse
HOST_A_NAME=Alex
HOST_B_NAME=Sam
```
`settings.py` renames `b2_key_id → b2_application_key_id`, adds `b2_region`, and adds the
OpenAI/LLM/TTS settings; `main.py` startup validation + `doctor.mjs` preflight + placeholder set
updated to match. The `deny-b2-secrets.sh` hook still applies — only placeholders go in `.env.example`.
The builder should verify the exact cheap OpenAI model + TTS voice ids against current OpenAI docs and
adjust the defaults if `gpt-4o-mini` / `gpt-4o-mini-tts` / those voice names have moved.

---

## 8. LLM / TTS implementation notes (for the builder)

> **Provider decision (user-approved, overrides the repo's default-to-Claude guidance):** this sample
> uses **OpenAI for BOTH the LLM script generation and the TTS** — one `openai` dependency, one
> `OPENAI_API_KEY`. This is a deliberate, recorded choice by the user; **do NOT "correct" it to
> Claude/Anthropic.** (The `claude-api` skill is therefore not the reference for this sample's LLM
> code — use the official OpenAI SDK.)

- **LLM (`repo/llm_client.py`)** — official `openai` Python SDK. Default model `gpt-4o-mini`
  (env `LLM_MODEL`), a cheap, widely-available model. Produce the 2-host script with **structured
  JSON output** via `response_format={"type": "json_schema", "json_schema": {…}}` returning
  `{ "lines": [ {"speaker": "A"|"B", "text": "…"} ] }`. Set a generous `max_tokens`/`max_completion_tokens`
  for full transcripts. Use the SDK's typed exceptions, never string-match errors. Verify the current
  cheap model id + structured-output param shape against OpenAI docs and adjust if they've moved.
- **TTS (`repo/tts_client.py`)** — **OpenAI TTS** (default `gpt-4o-mini-tts`, env `TTS_MODEL`):
  multiple named voices, MP3 output, same `OPENAI_API_KEY`. One call per script line with the
  speaker's assigned voice → MP3 bytes. v1 assembles the episode by **concatenating per-line MP3
  segments** (zero system deps); gapless/normalized assembly via `pydub`+ffmpeg is a noted optional
  upgrade (tech-debt). Keep the adapter provider-agnostic so ElevenLabs/others swap in cleanly.
- **Layering** — both adapters live in `repo/` (matches AGENTS.md "all external APIs wrapped in repo/
  adapters"). Orchestration/prompt-building/audio-assembly is business logic in `service/`. No raw
  SDK calls outside `repo/`. Files stay < 300 lines.
- **`requirements.txt`** — add `openai>=…`; do **not** add `anthropic`. PyPDF2 (already present) covers
  source-doc text extraction.
- **Note for the reviewer:** B2 standards (#1 S3-only, #2 custom user agent, #3 `B2_*` names + region)
  still apply in full. The LLM provider choice is out of scope for those standards — OpenAI is correct
  here per the user's decision.

---

## 9. Out-of-scope for the scaffold / things I will STOP and ask before doing
- Pushing to any remote (publishing is the separate `publish-sample-repo` skill).
- Creating binary assets — screenshots, logos (README uses a placeholder note instead).
- Touching any sibling sample in `../`.
- Using a different `user_agent_extra` than `b2ai-docs-to-podcast` (will confirm against the board
  sub-issue if one exists).
