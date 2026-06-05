<!-- last_verified: 2026-06-05 -->
# Security

Security principles and implementation for Docs to Podcast.

## Trust Boundaries

- **Frontend -> API**: CORS-restricted to configured origins, scoped to `GET/POST/DELETE/OPTIONS`
- **API -> B2**: Authenticated via `B2_APPLICATION_KEY_ID` + `B2_APPLICATION_KEY`, signature v4, region from `B2_REGION`
- **API -> OpenAI**: `OPENAI_API_KEY`, env-only, never logged. Used for both script generation (LLM) and audio synthesis (TTS).
- **Client -> B2**: Presigned URLs — `Content-Disposition: attachment` for downloads/transcripts (10-min expiry); inline URLs for the audio player (1-hour expiry, no attachment so the `<audio>` element can stream)

## Upload Validation

- Filename sanitization: path traversal, null bytes, unsafe chars stripped
- MIME/extension consistency check against allowlist
- Chunked streaming with size enforcement (100MB default)
- Content-type allowlist (images, PDFs, text, archives, audio/video)
- Empty file rejection

## File / Show Key Validation

- Empty keys rejected; path traversal patterns rejected (`../`, `%2e%2e`, backslashes, null bytes)
- Show and episode ids are server-minted hex tokens validated against a strict
  allowlist (`service/shows.py`) before any B2 access — a client-supplied
  `show_id` can never escape the `shows/` prefix.
- The bucket is the only access boundary — add prefix scoping in
  `services/api/app/service/files.py::validate_key` if your deployment
  shares a bucket with other workloads

## Untrusted Source Documents (Prompt Injection)

Uploaded source docs are **untrusted input** and are fed directly to the LLM
to write the script. A malicious document could attempt prompt injection
("ignore previous instructions…"). Mitigations in this sample:

- The system prompt instructs the model to produce only a two-host dialogue
  and not to invent unsupported facts; structured JSON output constrains the
  response shape.
- Generated audio/transcripts are treated as data, not executed.
- For production, add content review and consider sandboxing the prompt /
  stripping instruction-like text from sources. Tracked in the tech-debt tracker.

## Download Safety

- Presigned URLs force `Content-Disposition: attachment`
- Prevents inline rendering of user-uploaded content (XSS mitigation)

## Secrets Management

- All secrets (B2 keys, `OPENAI_API_KEY`) loaded via environment variables (pydantic-settings)
- `OPENAI_API_KEY` is never logged and never returned by any endpoint — the
  `/config` route exposes only non-secret defaults (host names, voices, model ids)
- Never committed to source control
- `.env.example` documents required variables with placeholder values only

## Agent Security Rules

- Never commit `.env`, credentials, or API keys
- Never weaken validation without explicit instruction
- Never bypass CORS, auth, or input sanitization
- Always validate at system boundaries
