<!-- last_verified: 2026-05-01 -->
# AGENTS.md

This is the authoritative control surface for all coding agents. Read this first.

## 1. Repository Map

```
apps/web/          Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
                   screens: Dashboard, Studio, Shows, Upload, Files, Settings
services/api/      FastAPI backend (layered: types/config/repo/service/runtime)
                   pipeline: shows -> sources -> generation (LLM + TTS) -> episode
packages/shared/   Shared TypeScript types (files, shows, episodes, stats)
docs/              System of record (features, workflows, security, reliability)
docs/exec-plans/   Execution plans and tech debt tracker
infra/railway/     Deployment config
```

## 2. Project Structure — What's App-Specific

This app is built on the Backblaze vibe-coding starter kit. The reusable B2 scaffolding is kept; the podcast pipeline and its two screens are what's specific to **Docs to Podcast**.

**App-specific (the Docs to Podcast pipeline)**
- **Studio.** `/studio` route + `apps/web/src/components/studio/` — create a show, add sources (reusing the kept dropzone), generate an episode.
- **Shows library.** `/shows` (+ `/shows/[id]`) + `apps/web/src/components/shows/` — the sample's asset explorer scoped to the `shows/` prefix: list shows, drill in, play audio inline, read the transcript, download artifacts.
- **Backend pipeline.** `service/shows.py` (manifest CRUD), `service/generation.py` (orchestration), `service/text_extract.py` (source text), `service/dashboard.py` (podcast metrics), `runtime/shows.py`, `runtime/dashboard.py`, `repo/llm_client.py` + `repo/tts_client.py` (OpenAI adapters), `types/shows.py`.
- **Dashboard.** `/` route + `apps/web/src/components/dashboard/` rewritten for podcast metrics (shows, episodes, listening minutes, storage, generation activity). New aggregations flow through `runtime -> service -> repo` and are exposed via TanStack Query hooks in `apps/web/src/lib/queries.ts` — no bare `useEffect + fetch`. Update `docs/features/dashboard.md` in the same PR (see §9).

**Kept from the starter (do not strip, rename, or replace)**
- **UI kit / design system.** `apps/web/src/components/ui/` (shadcn primitives), tokens in `apps/web/src/app/globals.css`, the `/design` page. Build new screens with these primitives; never edit generated `components/ui/` files. Restyle via tokens in `globals.css`.
- **Whole-bucket File Explorer.** `/files` route, `apps/web/src/app/files/`, `apps/web/src/components/files/`, and the Files sidebar entry. This is the explorer over *every* object; the Shows library is the *scoped* explorer over `shows/`. Both are kept.
- **Upload.** `/upload` route, `apps/web/src/app/upload/`, `apps/web/src/components/upload/`, and its sidebar entry. The Studio reuses the dropzone + progress components for show-scoped ingestion.
- The sidebar nav (Dashboard, Studio, Shows, Upload, Files, Settings, plus the Design System utility link).

## 3. Architectural Invariants

**Backend layering**: `types` -> `config` -> `repo` -> `service` -> `runtime`

- No backward imports across layers
- No `boto3` outside `repo/`
- **No external SDK outside `repo/`** — `boto3` (B2) and the OpenAI SDK (LLM in `repo/llm_client.py`, TTS in `repo/tts_client.py`) are wrapped in `repo/` adapters. Orchestration, prompt-building, and audio assembly are business logic in `service/`.
- No business logic in route handlers (`runtime/`)
- All external APIs wrapped in `repo/` adapters
- All request/response data validated at boundary (Pydantic models)
- No shared mutable state across layers

**Frontend**: shadcn/ui components in `src/components/ui/` are generated — never modify them.

**Data fetching**: every API call flows through TanStack Query hooks in `apps/web/src/lib/queries.ts`. No bare `useEffect + fetch` patterns. New endpoints touch three files: `runtime/<router>.py`, `lib/api-client.ts`, `lib/queries.ts`.

**Generation pipeline**: episode generation runs as a FastAPI `BackgroundTask` (`service/generation.py`): fetch sources from B2 -> extract text -> `repo/llm_client` (structured 2-host script) -> save transcript -> `repo/tts_client` per line (multi-voice MP3) -> assemble -> save audio -> update status. Status (`pending -> generating -> ready | failed`) is persisted in the episode's B2 manifest; the UI polls it with a TanStack Query `refetchInterval`. See [ARCHITECTURE.md](ARCHITECTURE.md#generation-pipeline).

## 4. Quality Expectations

- **DRY** — do not duplicate logic, types, or constants. Extract shared code only when used in 2+ places.
- Structured JSON logging only — no `print()` statements
- No raw SDK calls outside `repo/` layer
- Files stay under 300 lines
- Tests added or updated for every behavior change
- Docs updated in same PR as code changes
- Lint clean before merge
- Prefer boring, composable libraries over clever abstractions
- No implicit type assumptions — use typed models

## 5. Mechanical Enforcement

| Rule | Enforced by |
|------|-------------|
| No backward imports | `tests/test_structure.py::test_no_backward_imports` |
| No boto3 outside repo/ | `tests/test_structure.py::test_boto3_only_in_repo` |
| File size < 300 lines | `tests/test_structure.py::test_file_size_limits` |
| All layers exist | `tests/test_structure.py::test_all_layers_exist` |
| No bare print() | `ruff` rule T20 |
| Import ordering | `ruff` rule I001 |
| Frontend strict equality | `eslint` rule eqeqeq |
| No unused vars | `eslint` + `ruff` rules |

## 6. Commands

```bash
# Run
pnpm dev               # start both frontend and backend
pnpm dev:web           # frontend only
pnpm dev:api           # backend only

# Test & Lint
pnpm lint              # frontend lint (eslint)
pnpm build             # frontend type check + build
pnpm lint:api          # backend lint (ruff)
pnpm test:api          # backend tests (pytest; LLM/TTS mocked — no network, no keys)
pnpm check:structure   # structural boundary tests
pnpm test:e2e          # Playwright e2e tests
```

## 7. Agent Workflow

1. Read this file first.
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) before structural changes.
3. For non-trivial changes, create a plan in `docs/exec-plans/active/`.
4. Implement the smallest coherent change.
5. Run: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
6. Update docs in the same PR (see §9).
7. Move completed plans to `docs/exec-plans/completed/`.
8. Only change files relevant to the task. No drive-by improvements.

## 8. Frontend Conventions

See [docs/dev-workflows.md](docs/dev-workflows.md) for full details.

## 9. Doc Update Mapping

| Change Type | Update Location |
|-------------|-----------------|
| Feature logic, inputs, outputs, tests | `docs/features/<feature>.md` |
| User journeys | `docs/app-workflows.md` |
| System layout, deployments | `ARCHITECTURE.md` |
| Dev or testing process | `docs/dev-workflows.md` |
| Setup or scope changes | `README.md` |
| Security changes | `docs/SECURITY.md` |
| Reliability changes | `docs/RELIABILITY.md` |
| Active work plans | `docs/exec-plans/active/` |
| Known tech debt | `docs/exec-plans/tech-debt-tracker.md` |

If documentation and implementation conflict, update docs in the same PR. Documentation rot destroys agent reliability.

## 10. Doc Map

| Topic | Location |
|-------|----------|
| System layout, data flows, boundaries | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Feature docs | [docs/features/](docs/features/) |
| User journeys | [docs/app-workflows.md](docs/app-workflows.md) |
| Engineering workflows and testing | [docs/dev-workflows.md](docs/dev-workflows.md) |
| Security principles | [docs/SECURITY.md](docs/SECURITY.md) |
| Reliability expectations | [docs/RELIABILITY.md](docs/RELIABILITY.md) |
| Execution plans | [docs/exec-plans/](docs/exec-plans/) |
| Tech debt | [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md) |

## 11. When Unsure

- Prefer boring, stable libraries
- Prefer small PRs over large changes
- Add tests with every change
- Never bypass lint rules without explicit instruction
- Ask before making destructive or irreversible changes
