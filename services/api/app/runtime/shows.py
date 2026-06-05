import json
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile

from app.config import settings
from app.repo import get_object_bytes
from app.service import shows as shows_service
from app.service.generation import generate_episode
from app.service.shows import ShowError, source_prefix
from app.service.upload import DOC_TYPES, UploadError, process_upload
from app.types import (
    CreateShowRequest,
    EpisodeDetail,
    GenerateEpisodeRequest,
    ScriptLine,
    Show,
    ShowDetail,
    ShowSummary,
    SourceRef,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/shows", response_model=Show)
async def create_show_endpoint(body: CreateShowRequest):
    return shows_service.create_show(body.title)


@router.get("/shows", response_model=list[ShowSummary])
async def list_shows_endpoint():
    return shows_service.list_shows()


@router.get("/shows/{show_id}", response_model=ShowDetail)
async def get_show_endpoint(show_id: str):
    try:
        show = shows_service.get_show(show_id)
        episodes = shows_service.list_episodes(show_id)
    except ShowError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None
    return ShowDetail(show=show, episodes=episodes)


@router.post("/shows/{show_id}/sources", response_model=Show)
async def add_source_endpoint(show_id: str, request: Request, file: UploadFile):
    try:
        show = shows_service.get_show(show_id)
    except ShowError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None

    content_type = file.content_type or "application/octet-stream"
    content_length_header = request.headers.get("content-length")
    content_length = int(content_length_header) if content_length_header else None

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > settings.max_file_size:
            raise HTTPException(status_code=413, detail="File too large")
        chunks.append(chunk)
    file_data = b"".join(chunks)

    try:
        result = process_upload(
            file_data=file_data,
            filename=file.filename or "",
            content_type=content_type,
            content_length=content_length,
            key_prefix=source_prefix(show_id),
            allowed_types=DOC_TYPES,
        )
    except UploadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None

    ref = SourceRef(
        key=result.key,
        filename=result.filename,
        size_bytes=result.size_bytes,
        size_human=result.size_human,
        content_type=result.content_type,
        uploaded_at=result.uploaded_at,
    )
    updated = shows_service.add_source(show.id, ref)
    logger.info("Source added: show=%s key=%s", show.id, result.key)
    return updated


@router.post("/shows/{show_id}/episodes", response_model=EpisodeDetail)
async def create_episode_endpoint(
    show_id: str, body: GenerateEpisodeRequest, background: BackgroundTasks
):
    try:
        show = shows_service.get_show(show_id)
    except ShowError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None

    if not show.sources:
        raise HTTPException(
            status_code=400, detail="Add at least one source document first"
        )

    title = body.title or f"Episode {len(show.episode_ids) + 1}"
    episode = shows_service.new_episode(
        show=show,
        title=title,
        host_a_name=settings.host_a_name,
        host_b_name=settings.host_b_name,
        voice_host_a=settings.tts_voice_host_a,
        voice_host_b=settings.tts_voice_host_b,
    )
    # Full-episode render runs in the background; the UI polls status.
    background.add_task(generate_episode, show_id, episode.id)
    return EpisodeDetail(episode=episode)


@router.get("/shows/{show_id}/episodes/{episode_id}", response_model=EpisodeDetail)
async def get_episode_endpoint(show_id: str, episode_id: str):
    try:
        episode = shows_service.get_episode(show_id, episode_id)
    except ShowError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None

    lines: list[ScriptLine] = []
    if episode.transcript_key:
        raw = get_object_bytes(episode.transcript_key)
        if raw is not None:
            data = json.loads(raw.decode("utf-8"))
            lines = [ScriptLine(**line) for line in data.get("lines", [])]

    return EpisodeDetail(
        episode=episode,
        audio_url=shows_service.episode_audio_url(episode),
        transcript_url=shows_service.episode_transcript_download_url(episode),
        lines=lines,
    )
