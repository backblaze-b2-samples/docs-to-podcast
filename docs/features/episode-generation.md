<!-- last_verified: 2026-06-05 -->
# Feature: Episode Generation

## Purpose
Turn a show's source documents into a finished 2-host audio episode: an LLM writes a two-speaker dialogue, TTS renders it to multi-voice audio, and the transcript + audio are archived in B2.

## Used By
- UI: `/studio` (Step 3), `/shows/{id}` (episode cards)
- API: `POST /shows/{id}/episodes` (start), `GET /shows/{id}/episodes/{ep_id}` (poll)
- Job: FastAPI `BackgroundTask` → `service.generation.generate_episode`

## Core Functions
- `services/api/app/service/generation.py` — orchestration
- `services/api/app/service/text_extract.py` — PDF/text/markdown → plain text
- `services/api/app/repo/llm_client.py` — OpenAI chat completions, structured JSON script
- `services/api/app/repo/tts_client.py` — OpenAI TTS, one MP3 per line, per-host voice
- `services/api/app/repo/b2_client.py` — `get_object_bytes` (read sources back), `put_json`, `upload_file`

## Canonical Files
- Orchestration: `services/api/app/service/generation.py`
- External adapters: `services/api/app/repo/{llm_client,tts_client}.py`

## Inputs
- show_id, optional episode title (GenerateEpisodeRequest)
- Source documents already attached to the show (read back from B2)

## Outputs
- `transcript.json` (`{lines: [{speaker, text}]}`) under the episode prefix
- `episode.mp3` under the episode prefix
- Updated `episode.json` manifest (status, line_count, duration_seconds, audio_key, transcript_key, error)
- Side effects: B2 writes; OpenAI API calls

## Flow
1. `POST /shows/{id}/episodes` creates the episode (`pending`) and schedules the background task
2. Task: status → `generating`
3. Fetch each source from B2 (`get_object_bytes`) → extract text
4. `generate_script` → structured two-host dialogue
5. Write `transcript.json`; record `line_count`
6. `synthesize_line` per line with the speaker's voice → concatenate segments → `episode.mp3`
7. status → `ready` (with `audio_key`, estimated `duration_seconds`); on error → `failed` (with message)
- The UI polls step 7 via TanStack Query `refetchInterval` and stops once terminal.

## Edge Cases
- No readable source text → episode fails cleanly without calling the LLM
- LLM error (rate limit, 5xx) → `failed`, transcript not written
- TTS error mid-render → `failed`, but the transcript already in B2 is preserved
- Unexpected error → caught by a catch-all so the episode never stays stuck `generating`
- Show has no sources → `POST /episodes` returns 400 before scheduling work

## UX States
- Generating: blaze generating loader (Studio + episode card)
- Ready: inline audio player, transcript disclosure, download buttons
- Failed: error banner with the manifest's `error` text

## Verification
- Test files: `services/api/tests/test_generation.py` (LLM + TTS **mocked** — no network, no keys)
- Required cases: happy path, no-sources fail, LLM-error fail, TTS-error fail, voice routing, duration estimate
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm typecheck && pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: all pytest tests green; `test_boto3_only_in_repo` still green (new SDKs live in `repo/`)

## Related Docs
- [Show Creation](show-creation.md)
- [Shows Library](shows-library.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md) (Generation Pipeline)
- [RELIABILITY.md](../RELIABILITY.md)
