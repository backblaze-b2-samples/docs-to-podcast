from fastapi import APIRouter, HTTPException

from app.config import settings
from app.service.dashboard import (
    get_generation_activity,
    get_podcast_stats,
    get_recent_episodes,
)
from app.types import DailyEpisodeCount, PodcastStats, PublicConfig, RecentEpisode

router = APIRouter()


@router.get("/dashboard/stats", response_model=PodcastStats)
async def dashboard_stats_endpoint():
    return get_podcast_stats()


@router.get("/dashboard/recent-episodes", response_model=list[RecentEpisode])
async def recent_episodes_endpoint(limit: int = 10):
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
    return get_recent_episodes(limit=limit)


@router.get("/dashboard/activity", response_model=list[DailyEpisodeCount])
async def generation_activity_endpoint(days: int = 7):
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 90")
    return get_generation_activity(days=days)


@router.get("/config", response_model=PublicConfig)
async def public_config_endpoint():
    """Non-secret runtime config for the Settings screen (no credentials)."""
    return PublicConfig(
        host_a_name=settings.host_a_name,
        host_b_name=settings.host_b_name,
        voice_host_a=settings.tts_voice_host_a,
        voice_host_b=settings.tts_voice_host_b,
        llm_model=settings.llm_model,
        tts_model=settings.tts_model,
    )
