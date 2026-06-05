import json
import logging

from app.repo import get_object_bytes, upload_file
from app.repo.llm_client import LLMError, generate_script
from app.repo.tts_client import TTSError, synthesize_line
from app.service import shows as shows_service
from app.service.text_extract import extract_text
from app.types import Episode, EpisodeStatus, ScriptLine, Show

logger = logging.getLogger(__name__)

# Rough spoken-word rate (~150 wpm) used to estimate episode duration without
# decoding the MP3 — good enough for a dashboard "listening minutes" metric.
_WORDS_PER_SECOND = 2.5


def _build_prompt(show_title: str, source_texts: list[str]) -> str:
    joined = "\n\n---\n\n".join(source_texts)
    return (
        f"Show title: {show_title}\n\n"
        "Write a two-host podcast episode discussing the following source "
        "material. Host A introduces topics and asks questions; Host B adds "
        "depth and examples. Open with a brief hook and close with a wrap-up.\n\n"
        f"SOURCE MATERIAL:\n{joined}"
    )


def _gather_source_texts(show: Show) -> list[str]:
    texts: list[str] = []
    for ref in show.sources:
        data = get_object_bytes(ref.key)
        if data is None:
            logger.warning("Source missing during generation: %s", ref.key)
            continue
        text = extract_text(data, ref.content_type)
        if text:
            texts.append(text)
    return texts


def _voice_for(episode: Episode, speaker: str) -> str:
    return episode.voice_host_a if speaker == "A" else episode.voice_host_b


def _estimate_duration(lines: list[ScriptLine]) -> float:
    words = sum(len(line.text.split()) for line in lines)
    return round(words / _WORDS_PER_SECOND, 1)


def generate_episode(show_id: str, episode_id: str) -> None:
    """Run the full generation pipeline for one episode.

    Designed to run as a FastAPI BackgroundTask. Status + result are persisted
    to the episode's B2 manifest at each phase so the UI can poll progress and
    so a crash leaves a `failed`/partial record rather than a silent gap.
    """
    episode = shows_service.get_episode(show_id, episode_id)
    episode.status = EpisodeStatus.GENERATING
    shows_service.save_episode(episode)

    try:
        show = shows_service.get_show(show_id)
        source_texts = _gather_source_texts(show)
        if not source_texts:
            raise ValueError("No readable source documents to generate from")

        prompt = _build_prompt(show.title, source_texts)
        raw_lines = generate_script(prompt)
        lines = [ScriptLine(speaker=line["speaker"], text=line["text"]) for line in raw_lines]

        transcript_key = f"shows/{show_id}/episodes/{episode_id}/transcript.json"
        transcript_body = json.dumps(
            {"lines": [line.model_dump() for line in lines]}
        ).encode("utf-8")
        upload_file(transcript_body, transcript_key, "application/json")
        episode.transcript_key = transcript_key
        episode.line_count = len(lines)
        shows_service.save_episode(episode)

        segments = [
            synthesize_line(line.text, _voice_for(episode, line.speaker))
            for line in lines
        ]
        # v1 assembly: concatenate per-line MP3 segments (zero system deps).
        # Gapless/normalized assembly via pydub+ffmpeg is tracked as tech debt.
        audio = b"".join(segments)
        audio_key = f"shows/{show_id}/episodes/{episode_id}/episode.mp3"
        upload_file(audio, audio_key, "audio/mpeg")

        episode.audio_key = audio_key
        episode.duration_seconds = _estimate_duration(lines)
        episode.status = EpisodeStatus.READY
        episode.error = None
        shows_service.save_episode(episode)
        logger.info(
            "Episode generated: show=%s episode=%s lines=%d",
            show_id,
            episode_id,
            len(lines),
        )
    except (LLMError, TTSError, ValueError) as e:
        logger.warning("Episode generation failed: %s", e)
        episode.status = EpisodeStatus.FAILED
        episode.error = str(e)
        shows_service.save_episode(episode)
    except Exception as e:  # never leave an episode stuck "generating"
        logger.exception("Unexpected generation error")
        episode.status = EpisodeStatus.FAILED
        episode.error = f"Unexpected error: {e}"
        shows_service.save_episode(episode)
