"""Generation pipeline tests with fully mocked LLM + TTS providers.

No real API calls, no network, no keys. We monkeypatch the repo adapters and
the B2 manifest/object helpers so the orchestration logic is exercised in
isolation.
"""

from datetime import UTC, datetime

import pytest

from app.service import generation as gen
from app.service import shows as shows_service
from app.types import Episode, EpisodeStatus, Show, SourceRef


def _show() -> Show:
    now = datetime.now(UTC)
    return Show(
        id="a" * 12,
        title="Test Show",
        created_at=now,
        updated_at=now,
        sources=[
            SourceRef(
                key="shows/aaaaaaaaaaaa/sources/notes.txt",
                filename="notes.txt",
                size_bytes=10,
                size_human="10 B",
                content_type="text/plain",
                uploaded_at=now,
            )
        ],
        episode_ids=["b" * 12],
    )


def _episode() -> Episode:
    now = datetime.now(UTC)
    return Episode(
        id="b" * 12,
        show_id="a" * 12,
        title="Episode 1",
        status=EpisodeStatus.PENDING,
        created_at=now,
        updated_at=now,
        host_a_name="Alex",
        host_b_name="Sam",
        voice_host_a="alloy",
        voice_host_b="verse",
    )


def _patch_common(monkeypatch, saved):
    monkeypatch.setattr(gen.shows_service, "get_episode", lambda s, e: _episode())
    monkeypatch.setattr(gen.shows_service, "get_show", lambda s: _show())
    monkeypatch.setattr(gen, "get_object_bytes", lambda key: b"Some source text about storage.")
    monkeypatch.setattr(gen, "upload_file", lambda data, key, ct: None)

    def _save(ep):
        saved.append(ep.status)

    monkeypatch.setattr(gen.shows_service, "save_episode", _save)


def test_generation_happy_path(monkeypatch):
    saved: list[EpisodeStatus] = []
    _patch_common(monkeypatch, saved)
    monkeypatch.setattr(
        gen,
        "generate_script",
        lambda prompt, max_lines=60: [
            {"speaker": "A", "text": "Welcome to the show."},
            {"speaker": "B", "text": "Glad to be here."},
        ],
    )
    monkeypatch.setattr(gen, "synthesize_line", lambda text, voice: b"\xff\xf3mp3")

    gen.generate_episode("a" * 12, "b" * 12)

    assert saved[-1] == EpisodeStatus.READY
    assert EpisodeStatus.GENERATING in saved


def test_generation_no_sources_fails(monkeypatch):
    saved: list[EpisodeStatus] = []
    _patch_common(monkeypatch, saved)
    # No readable text comes back from any source.
    monkeypatch.setattr(gen, "get_object_bytes", lambda key: None)
    monkeypatch.setattr(gen, "generate_script", lambda *a, **k: pytest.fail("should not call LLM"))

    gen.generate_episode("a" * 12, "b" * 12)

    assert saved[-1] == EpisodeStatus.FAILED


def test_generation_llm_error_marks_failed(monkeypatch):
    from app.repo.llm_client import LLMError

    saved: list[EpisodeStatus] = []
    _patch_common(monkeypatch, saved)

    def _boom(prompt, max_lines=60):
        raise LLMError("rate limited")

    monkeypatch.setattr(gen, "generate_script", _boom)

    gen.generate_episode("a" * 12, "b" * 12)

    assert saved[-1] == EpisodeStatus.FAILED


def test_generation_tts_error_marks_failed(monkeypatch):
    from app.repo.tts_client import TTSError

    saved: list[EpisodeStatus] = []
    _patch_common(monkeypatch, saved)
    monkeypatch.setattr(
        gen,
        "generate_script",
        lambda prompt, max_lines=60: [{"speaker": "A", "text": "Hi"}],
    )

    def _boom(text, voice):
        raise TTSError("voice unavailable")

    monkeypatch.setattr(gen, "synthesize_line", _boom)

    gen.generate_episode("a" * 12, "b" * 12)

    assert saved[-1] == EpisodeStatus.FAILED


def test_voice_routing():
    ep = _episode()
    assert gen._voice_for(ep, "A") == "alloy"
    assert gen._voice_for(ep, "B") == "verse"


def test_duration_estimate_is_positive():
    from app.types import ScriptLine

    lines = [ScriptLine(speaker="A", text="one two three four five")]
    assert gen._estimate_duration(lines) > 0


def test_show_id_validation_rejects_traversal(monkeypatch):
    with pytest.raises(shows_service.ShowError):
        shows_service.get_show("../etc/passwd")


def test_episode_id_validation_rejects_bad_id(monkeypatch):
    with pytest.raises(shows_service.ShowError):
        shows_service.get_episode("a" * 12, "not a hex id")
