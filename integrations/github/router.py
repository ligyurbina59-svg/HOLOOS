"""Read-only GitHub API bridge for Android24Creator AppBuilder.

The GitHub credential stays on the server. Never expose GITHUB_TOKEN to the browser.
"""
from __future__ import annotations

import os
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/integrations/github", tags=["GitHub"])

API_ROOT = "https://api.github.com"
DEFAULT_REPOSITORY = "ligyurbina59-svg/HOLOOS"


def _allowed_repositories() -> set[str]:
    raw = os.getenv("GITHUB_REPOSITORY_ALLOWLIST", DEFAULT_REPOSITORY)
    return {item.strip() for item in raw.split(",") if item.strip()}


def _repository(value: str) -> str:
    if value not in _allowed_repositories() or value.count("/") != 1:
        raise HTTPException(status_code=403, detail="Repository is not allowlisted")
    owner, name = value.split("/", 1)
    if not owner or not name or any(ch in value for ch in ("..", "\\", "?", "#")):
        raise HTTPException(status_code=400, detail="Invalid repository")
    return value


def _safe_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not value or any(part in ("", ".", "..") for part in value.split("/")):
        raise HTTPException(status_code=400, detail="Invalid repository path")
    return value


async def _get_github(url: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Android24Creator-AppBuilder",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            response = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="GitHub upstream request failed") from exc
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="GitHub resource not found")
    if response.status_code in (401, 403):
        raise HTTPException(status_code=502, detail="GitHub rejected the server credential or rate limit")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"GitHub returned HTTP {response.status_code}")
    return response.json()


@router.get("/health")
async def github_bridge_health() -> dict[str, Any]:
    return {
        "service": "android24creator-github-bridge",
        "mode": "read-only",
        "credential_configured": bool(os.getenv("GITHUB_TOKEN")),
        "allowlisted_repositories": sorted(_allowed_repositories()),
    }


@router.get("/repository")
async def repository_metadata(
    repository: str = Query(DEFAULT_REPOSITORY, min_length=3, max_length=200),
) -> Any:
    repo = _repository(repository)
    return await _get_github(f"{API_ROOT}/repos/{repo}")


@router.get("/contents")
async def repository_contents(
    path: str = Query("", max_length=500),
    repository: str = Query(DEFAULT_REPOSITORY, min_length=3, max_length=200),
    ref: str | None = Query(default=None, max_length=200),
) -> Any:
    repo = _repository(repository)
    suffix = f"/{quote(_safe_path(path), safe='/')}" if path else ""
    query = f"?ref={quote(ref, safe='')}" if ref else ""
    return await _get_github(f"{API_ROOT}/repos/{repo}/contents{suffix}{query}")


@router.get("/file")
async def repository_file(
    path: str = Query(..., min_length=1, max_length=500),
    repository: str = Query(DEFAULT_REPOSITORY, min_length=3, max_length=200),
    ref: str | None = Query(default=None, max_length=200),
) -> dict[str, Any]:
    repo = _repository(repository)
    suffix = f"?ref={quote(ref, safe='')}" if ref else ""
    item = await _get_github(
        f"{API_ROOT}/repos/{repo}/contents/{quote(_safe_path(path), safe='/')}{suffix}"
    )
    if not isinstance(item, dict) or item.get("type") != "file":
        raise HTTPException(status_code=400, detail="Path does not identify a single file")
    if item.get("encoding") != "base64" or not item.get("content"):
        raise HTTPException(status_code=415, detail="File is not available as a base64 text payload")
    import base64
    import binascii

    try:
        content = base64.b64decode(item["content"], validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=415, detail="Only UTF-8 text files are supported") from exc
    return {
        "name": item.get("name"),
        "path": item.get("path"),
        "sha": item.get("sha"),
        "html_url": item.get("html_url"),
        "content": content,
    }
