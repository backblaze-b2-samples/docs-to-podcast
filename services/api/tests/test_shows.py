"""Show/episode manifest CRUD tests against an in-memory B2 JSON store."""

import pytest

from app.service import shows as shows_service
from app.types import EpisodeStatus, SourceRef


@pytest.fixture
def fake_b2(monkeypatch):
    """Replace the B2 JSON helpers with an in-memory dict keyed by object key."""
    store: dict[str, dict] = {}

    monkeypatch.setattr(shows_service, "put_json", lambda key, data: store.__setitem__(key, data))
    monkeypatch.setattr(shows_service, "get_json", lambda key: store.get(key))

    def _list_prefixes(prefix):
        ids = set()
        for k in store:
            if k.startswith(prefix):
                rest = k[len(prefix):]
                ids.add(prefix + rest.split("/", 1)[0] + "/")
        return sorted(ids)

    monkeypatch.setattr(shows_service, "list_prefixes", _list_prefixes)
    return store


def test_create_and_get_show(fake_b2):
    show = shows_service.create_show("My Show")
    assert show.title == "My Show"
    fetched = shows_service.get_show(show.id)
    assert fetched.id == show.id


def test_get_missing_show_raises(fake_b2):
    with pytest.raises(shows_service.ShowError) as exc:
        shows_service.get_show("a" * 12)
    assert exc.value.status_code == 404


def test_list_shows_returns_summaries(fake_b2):
    s1 = shows_service.create_show("One")
    s2 = shows_service.create_show("Two")
    summaries = shows_service.list_shows()
    ids = {s.id for s in summaries}
    assert {s1.id, s2.id} <= ids


def test_add_source_dedupes_by_key(fake_b2):
    show = shows_service.create_show("Docs")
    ref = SourceRef(
        key=f"shows/{show.id}/sources/a.txt",
        filename="a.txt",
        size_bytes=5,
        size_human="5 B",
        content_type="text/plain",
        uploaded_at="2026-06-05T00:00:00Z",
    )
    shows_service.add_source(show.id, ref)
    shows_service.add_source(show.id, ref)  # same key again
    updated = shows_service.get_show(show.id)
    assert len(updated.sources) == 1


def test_new_episode_links_to_show(fake_b2):
    show = shows_service.create_show("Linked")
    ep = shows_service.new_episode(
        show=show,
        title="Episode 1",
        host_a_name="Alex",
        host_b_name="Sam",
        voice_host_a="alloy",
        voice_host_b="verse",
    )
    assert ep.status == EpisodeStatus.PENDING
    reloaded = shows_service.get_show(show.id)
    assert ep.id in reloaded.episode_ids
    fetched_ep = shows_service.get_episode(show.id, ep.id)
    assert fetched_ep.title == "Episode 1"


def test_episode_audio_url_none_until_ready(fake_b2):
    show = shows_service.create_show("Audio")
    ep = shows_service.new_episode(
        show=show,
        title="E",
        host_a_name="Alex",
        host_b_name="Sam",
        voice_host_a="alloy",
        voice_host_b="verse",
    )
    assert shows_service.episode_audio_url(ep) is None
