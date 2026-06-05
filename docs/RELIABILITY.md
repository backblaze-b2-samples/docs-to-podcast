<!-- last_verified: 2026-06-05 -->
# Reliability

Reliability expectations and practices for this project.

## Health Checks

- `GET /health` verifies B2 connectivity and returns `healthy` or `degraded`
- Health endpoint is always available, even when B2 is down

## Error Handling

- HTTP handlers return structured error responses with appropriate status codes
- External service failures (B2) are caught and surfaced as 500/503 responses
- No unhandled exceptions leak stack traces to clients

## Logging

- Structured JSON logging via Python stdlib
- Every request gets a `request_id` for tracing
- Log levels: ERROR for failures, WARNING for degraded state, INFO for requests

## Observability

- Request timing middleware logs duration for every request
- `/metrics` endpoint exposes basic Prometheus-format counters
- Upload success/failure counts tracked

## Episode Generation

- Generation runs as a FastAPI **background task**, decoupled from the request
  that kicks it off. Status (`pending -> generating -> ready | failed`) is
  persisted to the episode's B2 manifest at each phase.
- **Failure handling**: any LLM/TTS/extraction error marks the episode
  `failed` with a human-readable `error` in the manifest. A catch-all guards
  against ever leaving an episode stuck in `generating`. The UI surfaces the
  error and lets the user generate a new episode.
- **Partial artifacts**: the transcript is written before audio synthesis, so
  a TTS failure still leaves a readable transcript in B2 alongside the failed
  episode record. Source docs and the show manifest are unaffected.
- **No automatic retries** in v1 — the user re-generates manually. A
  retry/backoff policy and a real queue/worker are noted below and in the
  tech-debt tracker.
- **Durability caveat**: generation is single-process and in-memory. If the
  API process is killed mid-generation, the episode is left in `generating`
  with no worker to resume it; re-generate to recover. A durable queue
  (e.g. Redis/RQ, Celery, or a managed queue) is the production path.

## Graceful Degradation

- File / show listing returns empty (not error) when B2 has no matching objects
- Metadata extraction failures don't block upload (return partial metadata)
- A missing source during generation is skipped with a warning; an all-empty
  source set fails the episode cleanly rather than calling the LLM with nothing
- Frontend shows skeleton states while loading, error states on failure, and
  the blaze generating loader while an episode is in flight

## Deployment

- Railway health checks on `/health`
- Zero-downtime deploys via rolling updates
- Environment-specific configuration via env vars (no config files in prod)
