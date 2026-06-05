from datetime import datetime

from pydantic import BaseModel


class DailyUploadCount(BaseModel):
    date: str
    uploads: int


class UploadStats(BaseModel):
    total_files: int
    total_size_bytes: int
    total_size_human: str
    uploads_today: int
    total_downloads: int


class PodcastStats(BaseModel):
    """Headline metrics for the Docs to Podcast dashboard."""

    total_shows: int
    total_episodes: int
    total_listening_minutes: float
    total_size_bytes: int
    total_size_human: str


class DailyEpisodeCount(BaseModel):
    """Episodes generated per day, for the generation-activity chart."""

    date: str
    episodes: int


class RecentEpisode(BaseModel):
    """A row in the dashboard's recent-episodes table."""

    show_id: str
    episode_id: str
    show_title: str
    episode_title: str
    status: str
    created_at: datetime
    duration_seconds: float | None = None
