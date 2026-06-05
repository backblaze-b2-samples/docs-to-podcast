from collections import defaultdict
from datetime import UTC, datetime, timedelta

from app.repo import get_upload_stats
from app.service import shows as shows_service
from app.types import (
    DailyEpisodeCount,
    EpisodeStatus,
    PodcastStats,
    RecentEpisode,
)
from app.types.formatting import humanize_bytes


def _all_episodes_with_show() -> list[tuple[str, object]]:
    """Return (show_title, episode) for every episode across every show."""
    rows: list[tuple[str, object]] = []
    for summary in shows_service.list_shows():
        for episode in shows_service.list_episodes(summary.id):
            rows.append((summary.title, episode))
    return rows


def get_podcast_stats() -> PodcastStats:
    """Aggregate shows, episodes, listening minutes, and storage used."""
    summaries = shows_service.list_shows()
    rows = _all_episodes_with_show()

    ready_seconds = sum(
        ep.duration_seconds or 0
        for _, ep in rows
        if ep.status == EpisodeStatus.READY
    )
    storage = get_upload_stats()

    return PodcastStats(
        total_shows=len(summaries),
        total_episodes=len(rows),
        total_listening_minutes=round(ready_seconds / 60, 1),
        total_size_bytes=storage["total_size_bytes"],
        total_size_human=storage["total_size_human"],
    )


def get_recent_episodes(limit: int = 10) -> list[RecentEpisode]:
    rows = _all_episodes_with_show()
    recent = [
        RecentEpisode(
            show_id=ep.show_id,
            episode_id=ep.id,
            show_title=show_title,
            episode_title=ep.title,
            status=ep.status.value,
            created_at=ep.created_at,
            duration_seconds=ep.duration_seconds,
        )
        for show_title, ep in rows
    ]
    recent.sort(key=lambda e: e.created_at, reverse=True)
    return recent[:limit]


def get_generation_activity(days: int = 7) -> list[DailyEpisodeCount]:
    """Episodes created per day over the last N days (zero-filled)."""
    rows = _all_episodes_with_show()
    today = datetime.now(UTC).date()
    cutoff = today - timedelta(days=days - 1)

    counts: dict[str, int] = defaultdict(int)
    for _, ep in rows:
        d = ep.created_at.date()
        if d >= cutoff:
            counts[d.isoformat()] += 1

    return [
        DailyEpisodeCount(
            date=(cutoff + timedelta(days=i)).isoformat(),
            episodes=counts.get((cutoff + timedelta(days=i)).isoformat(), 0),
        )
        for i in range(days)
    ]


# humanize_bytes is re-exported here so the runtime layer never reaches into
# types.formatting directly for dashboard composition.
__all__ = [
    "get_generation_activity",
    "get_podcast_stats",
    "get_recent_episodes",
    "humanize_bytes",
]
