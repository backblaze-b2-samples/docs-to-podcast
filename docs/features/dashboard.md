<!-- last_verified: 2026-06-05 -->
# Feature: Dashboard

## Purpose
Give an at-a-glance overview of podcast activity: how many shows and episodes exist, how much listening time has been generated, how much storage is used, and recent generation activity.

## Used By
- UI: `/` page (dashboard home)
- API: `GET /dashboard/stats`, `GET /dashboard/recent-episodes`, `GET /dashboard/activity`

## Core Functions
- `apps/web/src/components/dashboard/stats-cards.tsx` — 4 stat cards (shows, episodes, listening minutes, storage)
- `apps/web/src/components/dashboard/recent-episodes-table.tsx` — last 10 episodes
- `apps/web/src/components/dashboard/generation-chart.tsx` — bar chart of episodes generated per day
- `apps/web/src/lib/queries.ts` — `usePodcastStats()`, `useRecentEpisodes()`, `useGenerationActivity()`
- `services/api/app/runtime/dashboard.py` — dashboard route handlers
- `services/api/app/service/dashboard.py` — aggregation business logic
- `services/api/app/repo/b2_client.py` — `get_upload_stats()`, manifest reads

## Canonical Files
- Aggregation logic: `services/api/app/service/dashboard.py`
- Dashboard cards: `apps/web/src/components/dashboard/stats-cards.tsx`

## Inputs
- None (dashboard loads data automatically)

## Outputs
- `GET /dashboard/stats` → `PodcastStats` (total_shows, total_episodes, total_listening_minutes, total_size_bytes, total_size_human)
- `GET /dashboard/recent-episodes?limit=10` → `RecentEpisode[]` (sorted newest-first)
- `GET /dashboard/activity?days=7` → `DailyEpisodeCount[]` (server-side aggregation)

## Flow
- Page loads → three parallel API calls (stats, recent episodes, generation activity)
- Service iterates show manifests + their episode manifests in B2 to aggregate counts and durations
- Listening minutes = sum of `duration_seconds` across **ready** episodes ÷ 60
- Storage used reuses the bucket-wide `get_upload_stats()` total

## Edge Cases
- No shows/episodes → stats are zeros, chart and table show empty states
- API unavailable → inline `ErrorState` with retry (no misleading zeros)
- Episode without a duration (not yet ready) → contributes 0 listening minutes

## UX States
- Loading: skeletons for cards and table
- Empty: "No episodes yet" / "No activity yet"
- Loaded: populated cards, chart, table

## Verification
- Test files: `services/api/tests/test_dashboard.py`
- Required cases: stats with mixed-status episodes, recent-episode ordering, zero-filled activity
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm typecheck && pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: all pytest tests green, no ruff/eslint violations

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
