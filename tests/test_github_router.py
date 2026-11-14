import os
import pytest
from fastapi import HTTPException

from integrations.github.router import _repository, _safe_path


def test_default_repository_is_allowlisted(monkeypatch):
    monkeypatch.delenv("GITHUB_REPOSITORY_ALLOWLIST", raising=False)
    assert _repository("ligyurbina59-svg/HOLOOS") == "ligyurbina59-svg/HOLOOS"


def test_reject_repository_not_allowlisted(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY_ALLOWLIST", "ligyurbina59-svg/HOLOOS")
    with pytest.raises(HTTPException) as error:
        _repository("someone/other")
    assert error.value.status_code == 403


@pytest.mark.parametrize("path", ["../secret", "a/../secret", "/etc/passwd", "a//b", ""])
def test_reject_unsafe_or_empty_file_paths(path):
    with pytest.raises(HTTPException):
        _safe_path(path)


def test_accept_nested_relative_path():
    assert _safe_path("src/components/App.tsx") == "src/components/App.tsx"

import asyncio
from integrations.github import router as github_router


def test_project_inspection_builds_safe_manifest(monkeypatch):
    async def fake_github(url):
        if "/branches/" in url:
            return {"commit": {"commit": {"tree": {"sha": "tree-sha"}}}}
        return {
            "truncated": False,
            "tree": [
                {"path": "package.json", "type": "blob", "size": 80},
                {"path": "src/main.tsx", "type": "blob", "size": 120},
                {"path": "src", "type": "tree"},
            ],
        }

    monkeypatch.setattr(github_router, "_get_github", fake_github)
    result = asyncio.run(github_router.inspect_project(
        repository="ligyurbina59-svg/HOLOOS",
        ref="main",
        path="",
    ))
    assert result["project"]["category"] == "software"
    assert result["project"]["technology_hint"] == "JavaScript/TypeScript"
    assert result["safety"]["inspection_only"] is True
    assert result["safety"]["code_executed"] is False
    assert result["project"]["file_count"] == 2
    assert result["project"]["entry_count"] == 3


def test_project_inspection_rejects_invalid_ref():
    with pytest.raises(HTTPException) as error:
        asyncio.run(github_router.inspect_project(ref="../main"))
    assert error.value.status_code == 400
