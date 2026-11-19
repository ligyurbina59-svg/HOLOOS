"""Server-side AI provider gateway for HOLOOS / Android24Creator.

API credentials are read only from Termux/server environment variables.
No conversation history is persisted by this module.
"""
from __future__ import annotations

import os
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ai", tags=["MN24 AI Gateway"])

PROVIDERS = {
    "chatgpt": {
        "key_env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "default_model": "",
        "endpoint": "https://api.openai.com/v1/responses",
    },
    "claude": {
        "key_env": "ANTHROPIC_API_KEY",
        "model_env": "ANTHROPIC_MODEL",
        "default_model": "",
        "endpoint": "https://api.anthropic.com/v1/messages",
    },
    "deepseek": {
        "key_env": "DEEPSEEK_API_KEY",
        "model_env": "DEEPSEEK_MODEL",
        "default_model": "deepseek-flash",
        "endpoint": "https://api.deepseek.com/chat/completions",
    },
}

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=16000)

class ChatRequest(BaseModel):
    provider: Literal["chatgpt", "claude", "deepseek"]
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    max_tokens: int = Field(default=1200, ge=1, le=4096)

def _provider_status() -> list[dict]:
    result = []
    for name, config in PROVIDERS.items():
        key = bool(os.getenv(config["key_env"]))
        model = os.getenv(config["model_env"], config["default_model"])
        result.append({
            "id": name,
            "configured": key and bool(model),
            "credential_configured": key,
            "model_configured": bool(model),
            "model": model or None,
            "mode": "api",
        })
    result.append({
        "id": "claude_code",
        "configured": False,
        "credential_configured": False,
        "model_configured": False,
        "model": None,
        "mode": "external_handoff",
        "note": "Claude Code is a local coding-agent workflow, separate from Claude API chat.",
    })
    result.append({
        "id": "codex",
        "configured": False,
        "credential_configured": False,
        "model_configured": False,
        "model": None,
        "mode": "external_handoff",
        "note": "Codex is a coding-agent workflow, not a fourth chat API key in this gateway.",
    })
    return result

@router.get("/providers")
async def providers() -> dict:
    return {
        "service": "mn24-ai-gateway",
        "history_persistence": "disabled",
        "providers": _provider_status(),
    }

def _messages_text(messages: list[ChatMessage]) -> str:
    return "\n\n".join(f"{item.role.upper()}: {item.content}" for item in messages)

def _extract_openai_text(data: dict) -> str:
    chunks = []
    for item in data.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                    chunks.append(part["text"])
    return "\n".join(chunks).strip()

async def _call_provider(payload: ChatRequest) -> str:
    config = PROVIDERS[payload.provider]
    api_key = os.getenv(config["key_env"])
    model = os.getenv(config["model_env"], config["default_model"])
    if not api_key or not model:
        raise HTTPException(
            status_code=503,
            detail=f"Provider {payload.provider} is not configured. Set its server-side API key and model in Termux.",
        )

    timeout = httpx.Timeout(60.0, connect=10.0)
    if payload.provider == "chatgpt":
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body = {
            "model": model,
            "input": [{"role": m.role, "content": m.content} for m in payload.messages],
            "max_output_tokens": payload.max_tokens,
        }
    elif payload.provider == "claude":
        system_text = "\n\n".join(m.content for m in payload.messages if m.role == "system")
        chat_messages = [
            {"role": m.role, "content": m.content}
            for m in payload.messages if m.role in ("user", "assistant")
        ]
        headers = {
            "x-api-key": api_key,
            "anthropic-version": os.getenv("ANTHROPIC_VERSION", "2023-06-01"),
            "content-type": "application/json",
        }
        body = {"model": model, "max_tokens": payload.max_tokens, "messages": chat_messages}
        if system_text:
            body["system"] = system_text
    else:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in payload.messages],
            "max_tokens": payload.max_tokens,
            "stream": False,
        }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(config["endpoint"], headers=headers, json=body)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"{payload.provider} upstream request failed") from exc

    if response.status_code in (401, 403):
        raise HTTPException(status_code=502, detail=f"{payload.provider} rejected the configured credential")
    if response.status_code == 429:
        raise HTTPException(status_code=429, detail=f"{payload.provider} rate limit or quota reached")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"{payload.provider} returned HTTP {response.status_code}")

    try:
        data = response.json()
        if payload.provider == "chatgpt":
            text = _extract_openai_text(data)
        elif payload.provider == "claude":
            text = "\n".join(
                part.get("text", "") for part in data.get("content", [])
                if part.get("type") == "text"
            ).strip()
        else:
            text = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail=f"{payload.provider} returned an unrecognized response") from exc

    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=502, detail=f"{payload.provider} returned an empty response")
    return text

@router.post("/chat")
async def chat(payload: ChatRequest) -> dict:
    answer = await _call_provider(payload)
    return {"provider": payload.provider, "answer": answer, "stored": False}

@router.get("/claude-code")
async def claude_code_handoff() -> dict:
    return {
        "provider": "claude_code",
        "status": "external_handoff",
        "message": "Use Claude Code CLI or its supported application workflow separately. This API does not impersonate a Claude Code session.",
        "repository_workflow": "Use an isolated feature branch, review the diff, run tests, and open a pull request.",
    }

@router.get("/codex")
async def codex_handoff() -> dict:
    return {
        "provider": "codex",
        "status": "external_handoff",
        "message": "Use the Codex app or configured Codex CLI for repository-aware coding tasks. This API does not impersonate a Codex session.",
        "repository_workflow": "Create a feature branch, inspect changes, run tests, and open a pull request for review.",
    }
