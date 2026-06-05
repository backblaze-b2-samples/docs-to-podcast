from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EpisodeStatus(StrEnum):
    """Lifecycle of a generated episode, persisted in its B2 manifest."""

    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class ScriptLine(BaseModel):
    """One line of the two-host dialogue."""

    speaker: str  # "A" or "B"
    text: str


class SourceRef(BaseModel):
    """A source document attached to a show."""

    key: str
    filename: str
    size_bytes: int
    size_human: str
    content_type: str
    uploaded_at: datetime


class Episode(BaseModel):
    """An episode manifest (shows/{show_id}/episodes/{id}/episode.json)."""

    id: str
    show_id: str
    title: str
    status: EpisodeStatus = EpisodeStatus.PENDING
    created_at: datetime
    updated_at: datetime
    host_a_name: str
    host_b_name: str
    voice_host_a: str
    voice_host_b: str
    line_count: int = 0
    duration_seconds: float | None = None
    audio_key: str | None = None
    transcript_key: str | None = None
    error: str | None = None


class Show(BaseModel):
    """A show manifest (shows/{show_id}/show.json)."""

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    sources: list[SourceRef] = Field(default_factory=list)
    episode_ids: list[str] = Field(default_factory=list)


class ShowSummary(BaseModel):
    """Lightweight show row for the Shows library listing."""

    id: str
    title: str
    created_at: datetime
    source_count: int
    episode_count: int


class CreateShowRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class GenerateEpisodeRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class EpisodeDetail(BaseModel):
    """Episode plus presigned playback/transcript URLs and inline lines.

    Returned by the episode-status endpoint the UI polls. URLs are None until
    the corresponding artifact exists in B2.
    """

    episode: Episode
    audio_url: str | None = None
    transcript_url: str | None = None
    lines: list[ScriptLine] = Field(default_factory=list)


class ShowDetail(BaseModel):
    """A show with its sources and episode list, for the Shows library."""

    show: Show
    episodes: list[Episode] = Field(default_factory=list)


class PublicConfig(BaseModel):
    """Non-secret runtime config surfaced to the Settings screen.

    Deliberately excludes OPENAI_API_KEY and B2 credentials — only the
    host names, voices, and model ids are exposed.
    """

    host_a_name: str
    host_b_name: str
    voice_host_a: str
    voice_host_b: str
    llm_model: str
    tts_model: str
