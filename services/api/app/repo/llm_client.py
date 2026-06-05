import functools
import json

from openai import OpenAI, OpenAIError

from app.config import settings

# JSON schema the model must return: a two-host dialogue as a list of lines.
# Using a strict json_schema response format means we never have to repair
# free-form text — the SDK guarantees parseable JSON matching this shape.
_SCRIPT_SCHEMA = {
    "name": "podcast_script",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "lines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "speaker": {"type": "string", "enum": ["A", "B"]},
                        "text": {"type": "string"},
                    },
                    "required": ["speaker", "text"],
                },
            }
        },
        "required": ["lines"],
    },
}


class LLMError(RuntimeError):
    """Raised when script generation fails. Wraps the SDK's typed errors."""


@functools.lru_cache(maxsize=1)
def _client() -> OpenAI:
    # The OpenAI SDK reads the key from the environment by default, but we pass
    # it explicitly from settings so the single repo-root .env is the only
    # source of truth (mirrors how the B2 client is wired).
    return OpenAI(api_key=settings.openai_api_key)


def generate_script(prompt: str, max_lines: int = 60) -> list[dict]:
    """Ask the LLM for a structured two-host dialogue.

    Returns a list of {"speaker": "A"|"B", "text": str}. Raises LLMError on
    any SDK failure or malformed response. Network/SDK exceptions are caught
    via the SDK's typed `OpenAIError`, never by string-matching messages.
    """
    try:
        completion = _client().chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a podcast scriptwriter. Write a lively, "
                        "accurate two-host audio overview as a dialogue between "
                        "Host A and Host B. Keep each line to a few sentences. "
                        f"Aim for at most {max_lines} lines. Cover the key ideas "
                        "from the provided source material; do not invent facts "
                        "that are not supported by the sources."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_schema", "json_schema": _SCRIPT_SCHEMA},
            max_completion_tokens=8192,
        )
    except OpenAIError as e:
        raise LLMError(f"LLM script generation failed: {e}") from e

    content = completion.choices[0].message.content or "{}"
    try:
        lines = json.loads(content).get("lines", [])
    except json.JSONDecodeError as e:
        raise LLMError(f"LLM returned non-JSON content: {e}") from e
    if not lines:
        raise LLMError("LLM returned an empty script")
    return lines
