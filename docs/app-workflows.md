<!-- last_verified: 2026-06-05 -->
# App Workflows

User journeys inside Docs to Podcast.

## Create a Show and Generate an Episode (the headline flow)

- User navigates to `/studio`
- **Step 1 — choose a show**: types a title and clicks **Create** (or picks an existing show from the dropdown). The show manifest is written to `shows/{id}/show.json` in B2.
- **Step 2 — add sources**: drags or selects PDFs / text / markdown into the dropzone. Each file is validated (doc-only allowlist, size limit), stored under `shows/{id}/sources/`, and listed back. Re-uploading the same filename replaces that source.
- **Step 3 — generate**: clicks **Generate episode**. The API creates an episode (`status=pending`) and kicks off a background task. The UI polls the episode and shows the blaze generating loader while `status` is `generating`.
- On success the episode flips to `ready`: an inline audio player appears and a link opens the episode in **Shows**.
- On failure the episode flips to `failed` and the error message is shown; the user can generate again.
- See: [Show Creation](features/show-creation.md), [Episode Generation](features/episode-generation.md)

## Browse the Shows Library

- User navigates to `/shows`
- Page lists shows (scoped to the `shows/` prefix in B2) as cards with source/episode counts
- Clicking a show opens `/shows/{id}`:
  - **Sources** — the documents attached to the show
  - **Episodes** — each episode card polls its status; `ready` episodes show an inline HTML5 audio player, a "Read transcript" disclosure (Host A / Host B dialogue), and **Audio** / **Transcript JSON** download buttons
  - In-progress episodes show the generating loader; failed episodes show the error
- See: [Shows Library](features/shows-library.md)

## View the Dashboard

- User navigates to `/` (home)
- Parallel API calls load podcast stats, recent episodes, and generation activity
- Stats cards show: total shows, total episodes, total listening minutes (sum of ready-episode durations), storage used
- Generation-activity chart shows episodes created per day over the last 7 days
- Recent-episodes table shows the latest episodes with show, length, created date, and status (links into the show)
- Empty state when no shows/episodes exist yet
- See: [Dashboard](features/dashboard.md)

## Upload Files (generic surface, kept)

- User navigates to `/upload`
- Drops or selects files in the dropzone; client validates size (max 100MB) and type
- Per-file progress; success toast / green check, failure shows error
- Files land under `uploads/`
- See: [File Upload](features/file-upload.md)

## Browse and Manage All Files (whole-bucket explorer, kept)

- User navigates to `/files`
- File list loads from the API (sorted newest-first) across the **entire** bucket — sources, transcripts, audio, and generic uploads all appear here
- Tree view with type-specific icons; hover a row for preview / download / delete
- See: [File Browser](features/file-browser.md)
