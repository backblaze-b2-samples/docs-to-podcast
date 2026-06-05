"""Dashboard aggregation tests with mocked show/episode data."""

from datetime import UTC, datetime

from app.service import dashboard as dash
from app.types import Episode, EpisodeStatus, ShowSummary


def _summary(show_id: str, title: str) -> ShowSummary:
    return ShowSummary(
        id=show_id,
        title=title,
        created_at=datetime.now(UTC),
        source_count=1,
        episode_count=2,
    )


def _episode(show_id: str, status: EpisodeStatus, duration: float | None) -> Episode:
    now = datetime.now(UTC)
    return Episode(
        id="e" * 12,
        show_id=show_id,
        title="Ep",
        status=status,
        created_at=now,
        updated_at=now,
        host_a_name="Alex",
        host_b_name="Sam",
        voice_host_a="alloy",
        voice_host_b="verse",
        duration_seconds=duration,
    )


def test_podcast_stats_counts_and_minutes(monkeypatch):
    monkeypatch.setattr(dash.shows_service, "list_shows", lambda: [_summary("a" * 12, "One")])
    monkeypatch.setattr(
        dash.shows_service,
        "list_episodes",
        lambda sid: [
            _episode(sid, EpisodeStatus.READY, 120.0),
            _episode(sid, EpisodeStatus.GENERATING, None),
        ],
    )
    monkeypatch.setattr(
        dash,
        "get_upload_stats",
        lambda: {"total_size_bytes": 2048, "total_size_human": "2.0 KB"},
    )

    stats = dash.get_podcast_stats()
    assert stats.total_shows == 1
    assert stats.total_episodes == 2
    # Only the READY episode (120s = 2.0 min) counts toward listening minutes.
    assert stats.total_listening_minutes == 2.0
    assert stats.total_size_human == "2.0 KB"


def test_recent_episodes_sorted_newest_first(monkeypatch):
    monkeypatch.setattr(dash.shows_service, "list_shows", lambda: [_summary("a" * 12, "Show")])
    monkeypatch.setattr(
        dash.shows_service,
        "list_episodes",
        lambda sid: [_episode(sid, EpisodeStatus.READY, 60.0)],
    )
    monkeypatch.setattr(
        dash, "get_upload_stats", lambda: {"total_size_bytes": 0, "total_size_human": "0 B"}
    )
    recent = dash.get_recent_episodes(limit=5)
    assert len(recent) == 1
    assert recent[0].show_title == "Show"
    assert recent[0].status == "ready"


def test_generation_activity_zero_filled(monkeypatch):
    monkeypatch.setattr(dash.shows_service, "list_shows", lambda: [])
    monkeypatch.setattr(dash.shows_service, "list_episodes", lambda sid: [])
    activity = dash.get_generation_activity(days=7)
    assert len(activity) == 7
    assert all(d.episodes == 0 for d in activity)
