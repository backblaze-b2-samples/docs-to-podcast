import re
import uuid
from datetime import UTC, datetime

from app.repo import (
    get_inline_presigned_url,
    get_json,
    get_presigned_url,
    list_prefixes,
    put_json,
)
from app.types import Episode, EpisodeStatus, Show, ShowSummary, SourceRef

SHOWS_PREFIX = "shows/"
# Show / episode ids are opaque hex tokens we mint ourselves, so a strict
# allowlist is enough to keep path traversal out of B2 keys.
_ID_RE = re.compile(r"^[a-f0-9]{12,32}$")


class ShowError(Exception):
    """Raised for invalid show/episode requests."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _now() -> datetime:
    return datetime.now(UTC)


def _validate_id(value: str) -> None:
    if not _ID_RE.match(value):
        raise ShowError("Invalid identifier", status_code=400)


def _show_key(show_id: str) -> str:
    return f"{SHOWS_PREFIX}{show_id}/show.json"


def _episode_key(show_id: str, episode_id: str) -> str:
    return f"{SHOWS_PREFIX}{show_id}/episodes/{episode_id}/episode.json"


def source_prefix(show_id: str) -> str:
    return f"{SHOWS_PREFIX}{show_id}/sources/"


def create_show(title: str) -> Show:
    show_id = uuid.uuid4().hex
    now = _now()
    show = Show(id=show_id, title=title, created_at=now, updated_at=now)
    put_json(_show_key(show_id), show.model_dump())
    return show


def get_show(show_id: str) -> Show:
    _validate_id(show_id)
    data = get_json(_show_key(show_id))
    if data is None:
        raise ShowError("Show not found", status_code=404)
    return Show(**data)


def save_show(show: Show) -> None:
    show.updated_at = _now()
    put_json(_show_key(show.id), show.model_dump())


def list_shows() -> list[ShowSummary]:
    summaries: list[ShowSummary] = []
    for prefix in list_prefixes(SHOWS_PREFIX):
        # prefix looks like "shows/{id}/"
        show_id = prefix[len(SHOWS_PREFIX):].rstrip("/")
        data = get_json(_show_key(show_id))
        if data is None:
            continue
        show = Show(**data)
        summaries.append(
            ShowSummary(
                id=show.id,
                title=show.title,
                created_at=show.created_at,
                source_count=len(show.sources),
                episode_count=len(show.episode_ids),
            )
        )
    summaries.sort(key=lambda s: s.created_at, reverse=True)
    return summaries


def add_source(show_id: str, ref: SourceRef) -> Show:
    show = get_show(show_id)
    # Replace any existing entry for the same key (re-upload), else append.
    show.sources = [s for s in show.sources if s.key != ref.key]
    show.sources.append(ref)
    save_show(show)
    return show


def new_episode(
    show: Show,
    title: str,
    host_a_name: str,
    host_b_name: str,
    voice_host_a: str,
    voice_host_b: str,
) -> Episode:
    episode_id = uuid.uuid4().hex
    now = _now()
    episode = Episode(
        id=episode_id,
        show_id=show.id,
        title=title,
        status=EpisodeStatus.PENDING,
        created_at=now,
        updated_at=now,
        host_a_name=host_a_name,
        host_b_name=host_b_name,
        voice_host_a=voice_host_a,
        voice_host_b=voice_host_b,
    )
    save_episode(episode)
    show.episode_ids.append(episode_id)
    save_show(show)
    return episode


def save_episode(episode: Episode) -> None:
    episode.updated_at = _now()
    put_json(_episode_key(episode.show_id, episode.id), episode.model_dump())


def get_episode(show_id: str, episode_id: str) -> Episode:
    _validate_id(show_id)
    _validate_id(episode_id)
    data = get_json(_episode_key(show_id, episode_id))
    if data is None:
        raise ShowError("Episode not found", status_code=404)
    return Episode(**data)


def list_episodes(show_id: str) -> list[Episode]:
    show = get_show(show_id)
    episodes: list[Episode] = []
    for ep_id in show.episode_ids:
        data = get_json(_episode_key(show_id, ep_id))
        if data is not None:
            episodes.append(Episode(**data))
    episodes.sort(key=lambda e: e.created_at, reverse=True)
    return episodes


def episode_audio_url(episode: Episode) -> str | None:
    """Presigned inline URL for the HTML5 player. None until audio exists."""
    if not episode.audio_key:
        return None
    return get_inline_presigned_url(episode.audio_key)


def episode_transcript_download_url(episode: Episode) -> str | None:
    if not episode.transcript_key:
        return None
    return get_presigned_url(episode.transcript_key, filename="transcript.json")
