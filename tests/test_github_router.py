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
