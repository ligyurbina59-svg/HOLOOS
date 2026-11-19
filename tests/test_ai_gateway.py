import pytest
from fastapi import HTTPException

from integrations.ai_gateway.router import ChatMessage, ChatRequest, _provider_status


def test_provider_status_does_not_expose_secrets(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    rows = _provider_status()
    openai = next(row for row in rows if row["id"] == "chatgpt")
    assert openai["configured"] is True
    assert "api_key" not in openai
    assert "test-secret" not in str(rows)


def test_codex_is_handoff_not_fake_chat_api():
    codex = next(row for row in _provider_status() if row["id"] == "codex")
    assert codex["configured"] is False
    assert codex["mode"] == "external_handoff"


def test_chat_request_limits_messages():
    with pytest.raises(Exception):
        ChatRequest(provider="deepseek", messages=[])


def test_chat_message_limits_content():
    with pytest.raises(Exception):
        ChatMessage(role="user", content="x" * 16001)


def test_backend_mounts_mn24_routes():
    from android24creator_backend.main import UI_DIR, app

    paths = set(app.openapi()["paths"])
    assert "/api/ai/providers" in paths
    assert "/api/ai/chat" in paths
    assert "/api/integrations/github/project/inspect" in paths
    assert (UI_DIR / "expansion.html").is_file()
    assert (UI_DIR / "m-radio-control.html").is_file()
    assert (UI_DIR / "appbuilder-importer.html").is_file()
