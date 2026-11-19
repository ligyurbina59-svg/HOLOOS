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
    raw = os.getenv(
        "GITHUB_REPOSITORY_ALLOWLIST",
        "ligyurbina59-svg/HOLOOS,ligyurbina59-svg/Cebolla",
    )
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


@router.get("/project/inspect")
async def inspect_project(
    repository: str = Query(DEFAULT_REPOSITORY, min_length=3, max_length=200),
    ref: str = Query("main", min_length=1, max_length=200),
    path: str = Query("", max_length=500),
) -> dict[str, Any]:
    """Build a safe project manifest from Git tree metadata; never downloads or executes files."""
    repo = _repository(repository)
    if any(ch in ref for ch in ("..", "\\", "?", "#")):
        raise HTTPException(status_code=400, detail="Invalid Git reference")
    prefix = _safe_path(path) if path else ""
    branch_data = await _get_github(f"{API_ROOT}/repos/{repo}/branches/{quote(ref, safe='')}")
    tree_sha = (
        branch_data.get("commit", {}).get("commit", {}).get("tree", {}).get("sha")
        if isinstance(branch_data, dict) else None
    )
    if not tree_sha:
        raise HTTPException(status_code=502, detail="GitHub did not return a branch tree SHA")
    payload = await _get_github(f"{API_ROOT}/repos/{repo}/git/trees/{quote(tree_sha, safe='')}?recursive=1")
    if not isinstance(payload, dict) or not isinstance(payload.get("tree"), list):
        raise HTTPException(status_code=502, detail="GitHub returned an invalid Git tree")
    entries = []
    for node in payload["tree"]:
        node_path = node.get("path", "")
        if prefix and not (node_path == prefix or node_path.startswith(prefix + "/")):
            continue
        relative = node_path[len(prefix):].lstrip("/") if prefix else node_path
        if not relative:
            continue
        entries.append({"path": relative, "type": node.get("type"), "size": node.get("size")})
    entries = entries[:1000]
    names = {item["path"].lower() for item in entries if item["type"] == "blob"}
    extensions = {PurePosixPath(name).suffix for name in names}
    if "package.json" in names or any(name.endswith((".tsx", ".jsx", ".ts", ".js")) for name in names):
        technology = "JavaScript/TypeScript"
    elif "pyproject.toml" in names or "requirements.txt" in names or any(name.endswith(".py") for name in names):
        technology = "Python"
    elif any(name.endswith((".glb", ".gltf", ".fbx", ".blend")) for name in names):
        technology = "3D / digital assets"
    elif any(name.endswith((".mp4", ".webm", ".mov", ".wav", ".mp3")) for name in names):
        technology = "Multimedia"
    else:
        technology = "Undetermined"
    if any(name.endswith("androidmanifest.xml") or name.endswith("build.gradle") or name.endswith("settings.gradle") for name in names):
        category = "android_app"
    elif any(name.endswith((".glb", ".gltf", ".fbx", ".blend")) for name in names):
        category = "3d_product"
    elif any(name.endswith((".mp4", ".webm", ".mov", ".wav", ".mp3")) for name in names):
        category = "multimedia"
    elif any(name.endswith((".unity", ".godot")) or "/scenes/" in name for name in names):
        category = "game"
    elif "package.json" in names or "pyproject.toml" in names or "requirements.txt" in names:
        category = "software"
    else:
        category = "unclassified"
    manifest = {
        "schema_version": "1.0",
        "source": {"provider": "github", "repository": repo, "ref": ref, "path": prefix or "."},
        "project": {
            "name": (prefix.split("/")[-1] if prefix else repo.split("/")[-1]),
            "category": category,
            "technology_hint": technology,
            "file_count": sum(1 for item in entries if item["type"] == "blob"),
            "entry_count": len(entries),
            "extensions": sorted(extensions),
        },
        "files": entries,
        "safety": {
            "inspection_only": True,
            "files_downloaded": False,
            "code_executed": False,
            "manual_review_required": True,
            "tree_truncated_by_github": bool(payload.get("truncated")),
            "manifest_entry_limit": 1000,
        },
    }
    return manifest

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
