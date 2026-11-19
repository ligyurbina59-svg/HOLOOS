import pytest
from fastapi import HTTPException

from integrations.game_library import router as games


@pytest.mark.anyio
async def test_catalog_lists_web_games_and_archives(tmp_path, monkeypatch):
    monkeypatch.setattr(games, "ROOT", tmp_path)
    monkeypatch.setattr(games, "SOURCE", tmp_path / "imports" / "Cebolla")
    result = await games.catalog()
    assert len(result["web_games"]) == 4
    assert len(result["game_archives"]) == 3
    assert result["imported"] is False


@pytest.mark.anyio
async def test_catalog_detects_imported_html5_game(tmp_path, monkeypatch):
    source = tmp_path / "imports" / "Cebolla"
    source.mkdir(parents=True)
    (source / "HOLOCHRON_WEB.html").write_text("<html>test</html>", encoding="utf-8")
    monkeypatch.setattr(games, "ROOT", tmp_path)
    monkeypatch.setattr(games, "SOURCE", source)
    result = await games.catalog()
    holo = next(item for item in result["web_games"] if item["id"] == "holochron")
    assert holo["available"] is True
    assert holo["launch_url"] == "/api/games/play/holochron"


@pytest.mark.anyio
async def test_play_rejects_unknown_slug():
    with pytest.raises(HTTPException) as error:
        await games.play_game("../../../etc/passwd")
    assert error.value.status_code == 404


@pytest.mark.anyio
async def test_play_requires_imported_file(tmp_path, monkeypatch):
    monkeypatch.setattr(games, "ROOT", tmp_path)
    monkeypatch.setattr(games, "SOURCE", tmp_path / "imports" / "Cebolla")
    with pytest.raises(HTTPException) as error:
        await games.play_game("holochron")
    assert error.value.status_code == 404


def test_backend_mounts_game_library_routes():
    from android24creator_backend.main import app

    paths = set(app.openapi()["paths"])
    route_paths = {getattr(route, "path", None) for route in app.routes}
    assert "/api/games/catalog" in paths
    assert "/api/games/status" in paths
    assert "/api/games/play/{slug}" in paths
    assert "/app/games" in route_paths
