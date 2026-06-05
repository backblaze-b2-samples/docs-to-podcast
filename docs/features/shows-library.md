<!-- last_verified: 2026-06-05 -->
# Feature: Shows Library

## Purpose
Provide a sample-scoped asset explorer over the `shows/` prefix in B2: browse shows, drill into one, listen to episodes inline, read transcripts, and download artifacts. (Complements the kept whole-bucket Files explorer.)

## Used By
- UI: `/shows`, `/shows/{id}`
- API: `GET /shows`, `GET /shows/{id}`, `GET /shows/{id}/episodes/{ep_id}`

## Core Functions
- `apps/web/src/components/shows/shows-list.tsx` — show cards
- `apps/web/src/components/shows/show-detail.tsx` — sources + episode list
- `apps/web/src/components/shows/episode-card.tsx` — player, transcript, downloads, status polling
- `apps/web/src/components/shows/episode-status-badge.tsx` — shared status badge + duration formatter
- `services/api/app/runtime/shows.py` — list/get routes
- `services/api/app/repo/b2_client.py` — `list_prefixes` (delimiter on `shows/`), `get_inline_presigned_url`, `get_presigned_url`

## Canonical Files
- Episode card: `apps/web/src/components/shows/episode-card.tsx`
- Scoped listing: `services/api/app/service/shows.py::list_shows`

## Inputs
- show_id (path), episode_id (path)

## Outputs
- `ShowSummary[]` for the library grid
- `ShowDetail` (show + episode manifests) for the detail page
- `EpisodeDetail` (episode + presigned audio/transcript URLs + inline transcript lines)

## Flow
- `/shows` lists shows via `list_prefixes("shows/")` + each `show.json`
- `/shows/{id}` loads the show manifest and its episodes
- Each episode card polls `GET /shows/{id}/episodes/{ep_id}`; when `ready` it renders an HTML5 `<audio>` element (inline presigned URL), a transcript disclosure, and Audio / Transcript download links
- Audio uses an inline presigned URL (no attachment) so the browser can stream; downloads force attachment

## Edge Cases
- No shows → empty state pointing to Studio
- Show not found → 404 surfaced as an empty/error state
- Episode still generating → generating loader instead of the player
- Episode failed → error banner

## UX States
- Loading: skeleton cards
- Empty: "No shows yet" / "No episodes yet"
- Error: inline `ErrorState` with retry

## Verification
- Test files: `services/api/tests/test_shows.py`
- Required cases: list summaries, get show detail, audio URL is null until ready
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm typecheck && pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: all pytest tests green

## Related Docs
- [Episode Generation](episode-generation.md)
- [File Browser](file-browser.md) (the whole-bucket explorer)
- [App Workflows](../app-workflows.md)
