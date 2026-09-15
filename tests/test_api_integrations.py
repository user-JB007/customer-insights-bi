"""Smoke tests for API source/sink."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.integrations.api_source import build_engagement_events, fetch_engagement
from src.integrations.api_sink import build_kpi_snapshot, push_kpi_snapshot
from src.integrations.http_client import get_json, post_json


def test_build_engagement_events():
    users = [{"id": 1, "name": "Ada", "email": "a@x.com", "username": "ada"}]
    posts = [{"id": 10, "userId": 1, "title": "Hello", "body": "world"}]
    comments = [{"id": 99, "postId": 10, "name": "Bob", "email": "b@x.com", "body": "nice"}]
    df = build_engagement_events(users, posts, comments)
    assert len(df) == 2
    assert set(df["event_type"]) == {"post", "comment"}


def test_fetch_engagement_mocked(tmp_path, monkeypatch):
    import src.integrations.api_source as mod

    monkeypatch.setattr(mod, "ROOT", tmp_path)
    (tmp_path / "data" / "raw" / "api").mkdir(parents=True)
    (tmp_path / "data" / "marts").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "pipeline.yaml").write_text(
        "api_source:\n  base_url: https://jsonplaceholder.typicode.com\n"
    )

    users = [{"id": 1, "name": "Ada", "email": "a@x.com"}]
    posts = [{"id": 1, "userId": 1, "title": "t", "body": "b"}]
    comments = [{"id": 1, "postId": 1, "name": "c", "email": "c@x.com", "body": "x"}]
    with patch("src.integrations.api_source.get_json", side_effect=[users, posts, comments]):
        result = fetch_engagement(use_network=True)
    assert result["engagement_events"] == 2
    assert (tmp_path / "data" / "marts" / "engagement_events.csv").exists()


def test_push_kpi_external_mocked(tmp_path, monkeypatch):
    import src.integrations.api_sink as mod

    monkeypatch.setattr(mod, "ROOT", tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "pipeline.yaml").write_text("api_sink: {}\n")
    (tmp_path / "data" / "marts").mkdir(parents=True)

    with patch("src.integrations.api_sink.post_json", return_value={"id": 42}):
        result = push_kpi_snapshot(post_local=False, post_external=True, payload={"kpis": {"x": 1}})
    assert result["deliveries"]["external"]["ok"] is True


@pytest.mark.network
def test_live_jsonplaceholder_optional():
    try:
        data = get_json("https://jsonplaceholder.typicode.com/users", timeout=10, retries=1)
    except Exception as exc:
        pytest.skip(f"network unavailable: {exc}")
    assert isinstance(data, list) and len(data) > 0
