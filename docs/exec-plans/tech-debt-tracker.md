<!-- last_verified: 2026-06-05 -->
# Tech Debt Tracker

Known tech debt items. Agents update this when they discover or create tech debt.

| Description | Impact | Proposed Resolution | Priority | Status |
|---|---|---|---|---|
| Episode MP3 assembly is naive byte concatenation of per-line clips | Slight clicks/gaps between lines; not gapless or loudness-normalized | Assemble with `pydub` + ffmpeg (crossfade/normalize), or request a single multi-speaker render if the provider supports it | Medium | Open |
| In-process background generation, no durable queue | An API restart leaves an episode stuck `generating` with no worker to resume | Move generation to a real queue/worker (Redis/RQ, Celery, or managed) | Medium | Open |
| No streaming generation | User waits for the full episode; no incremental script/audio | Stream script tokens (SSE) and/or progressive audio once the UX warrants it | Low | Open |
| No automatic retry on transient LLM/TTS errors | User must re-generate manually after a rate-limit/5xx | Add bounded retry/backoff in `repo/llm_client.py` / `repo/tts_client.py` | Low | Open |
| Source docs are untrusted LLM input (prompt injection) | A crafted document could steer the script | Add content review / instruction stripping; see `docs/SECURITY.md` | Medium | Open |
| `humanizeBytes` duplicated in TypeScript | DRY violation | Extract to `lib/utils.ts` | Low | Open |
| `formatDate` duplicated in TypeScript | DRY violation | Extract to `lib/utils.ts` | Low | Open |
