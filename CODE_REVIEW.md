# Code Review: Docs to Podcast

**Reviewer:** Claude | **Date:** 2026-06-05

---

## Overall Impression

`docs-to-podcast` is a focused Backblaze B2 sample built on the vibe-coding starter kit. It keeps the reusable, well-architected scaffolding — strict backend layering, mechanical enforcement via structural tests, shared types, structured logging — and adds the podcast pipeline: show creation, LLM script generation, multi-voice TTS, and a per-episode B2 archive. This review covers the engineering quality of the finished sample.

## Quality Gates (passing)

- **Backend layering** enforced by `services/api/tests/test_structure.py`: no backward imports, all external SDKs (`boto3`, `openai`) confined to `repo/`, every `app/*.py` under 300 lines, all layers present.
- **`pnpm test:api`** — backend tests pass; the LLM and TTS adapters are mocked, so the suite runs with no network and no API keys.
- **`pnpm lint:api`** (ruff) and **`pnpm lint`** / **`pnpm build`** (eslint + `tsc` + `next build`) are clean.
- **Secrets** — only placeholders in `.env.example`; real credentials live in the gitignored `.env`.

## What's Done Well

- **Strict layered architecture** (`types -> config -> repo -> service -> runtime`) with mechanical enforcement via tests — rare and valuable.
- **External APIs wrapped in `repo/` adapters** — `boto3` for B2, and OpenAI for both the LLM (`repo/llm_client.py`) and TTS (`repo/tts_client.py`). Orchestration, prompt-building, and audio assembly stay in `service/`.
- **B2 is the sole data store** — shows and episodes are JSON manifests in the bucket, and each per-episode bundle (sources + transcript + audio) lives together under `shows/{id}/episodes/{ep}/`.
- **AGENTS.md as a single source of truth**, **Pydantic at all boundaries**, **shared TypeScript types** mirroring the backend models, **structured JSON logging**, **presigned URLs + filename sanitization + path-traversal protection**, and **file-size limits enforced by test**.
- **Resilient generation** — runs as a FastAPI `BackgroundTask`; status (`pending -> generating -> ready | failed`) is persisted to the episode's B2 manifest at each phase, so a crash leaves a `failed`/partial record rather than a silent gap, and the UI polls status via a TanStack Query `refetchInterval`.

## Known Limitations (tracked)

See [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md). The notable ones:

- **Audio assembly** concatenates per-line MP3 segments (zero system deps) rather than gapless/normalized assembly via `pydub` + ffmpeg.
- **In-process generation** — the background task runs inside the API process; a production deployment would move it to a durable queue/worker so generation survives restarts and scales horizontally.
- **No streaming generation** — episodes render fully before playback; live/streaming generation is a future enhancement.
- **Source documents are untrusted input** to the LLM; see [docs/SECURITY.md](docs/SECURITY.md) for the prompt-injection note.

## Running a Fresh Review

After changes, run `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`, and update the feature docs in the same change (AGENTS.md §9).
