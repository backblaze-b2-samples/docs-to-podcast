import functools

from openai import OpenAI, OpenAIError

from app.config import settings


class TTSError(RuntimeError):
    """Raised when speech synthesis fails. Wraps the SDK's typed errors."""


@functools.lru_cache(maxsize=1)
def _client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def synthesize_line(text: str, voice: str) -> bytes:
    """Render a single script line to MP3 bytes with the given voice.

    Provider-agnostic by design: the rest of the pipeline only knows it gets
    MP3 bytes back per line, so swapping in ElevenLabs/another TTS later means
    changing only this adapter. Raises TTSError on any SDK failure.
    """
    try:
        response = _client().audio.speech.create(
            model=settings.tts_model,
            voice=voice,
            input=text,
            response_format="mp3",
        )
        # `.read()` pulls the full binary body for the synthesized clip.
        return response.read()
    except OpenAIError as e:
        raise TTSError(f"TTS synthesis failed: {e}") from e
