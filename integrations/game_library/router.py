"""Allowlisted HTML5 games from the imported Cebolla repository."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "imports" / "Cebolla"

WEB_GAMES = {
    "holochron": {"title": "HOLOCHRON", "file": "HOLOCHRON_WEB.html", "genre": "Acción / runner", "description": "Archivo holocromático con cinco capas jugables."},
    "signal-earth": {"title": "SIGNAL://EARTH", "file": "SIGNAL_EARTH_WEB.html", "genre": "Acción / sci-fi", "description": "Videojuego web de ciencia ficción; demo HTML5."},
    "stormrunner-ragnarok": {"title": "STORMRUNNER RAGNAROK", "file": "STORMRUNNER_RAGNAROK.html", "genre": "Acción", "description": "Demo de acción vikinga en HTML5."},
    "pantheon-front": {"title": "PANTHEON FRONT", "file": "PANTHEON_FRONT_WEB.html", "genre": "Acción / mitología", "description": "Demo web PANTHEON FRONT."},
}

ARCHIVES = [
    {"id": "runic-arena", "file": "MN24_RunicArena_v1.0.zip", "title": "MN24 RunicArena"},
    {"id": "skybolt", "file": "MN24_SkyBolt_v1.0.zip", "title": "MN24 SkyBolt"},
    {"id": "stormrunner-thunder", "file": "STORMRUNER_THUNDER_OF_THE_NORTH_MVP_v0.1.zip", "title": "Stormrunner: Thunder of the North"},
]

router = APIRouter(prefix="/games", tags=["Game Library"])


@router.get("/catalog")
async def catalog() -> dict:
    web = []
    for slug, game in WEB_GAMES.items():
        present = (SOURCE / game["file"]).is_file()
        web.append({
            "id": slug, **game, "type": "html5",
            "available": present,
            "launch_url": f"/games/play/{slug}" if present else None,
        })
    archives = []
    archive_root = ROOT / "imports" / "Cebolla-games"
    for item in ARCHIVES:
        source_present = (SOURCE / item["file"]).is_file()
        target = archive_root / item["id"]
        extracted = target.is_dir()
        archives.append({
            **item, "type": "zip_source", "available": source_present,
            "extracted": extracted,
            "launch_url": f"/games/archives/{item['id']}/" if extracted else None,
        })
    return {
        "source_repository": "ligyurbina59-svg/Cebolla",
        "imported": SOURCE.is_dir(),
        "web_games": web,
        "game_archives": archives,
        "policy": "HTML5 entries are launched in a same-origin iframe. ZIP archives must be safely extracted and inspected before launch. APK files are not web games and are never executed here.",
    }


@router.get("/play/{slug}")
async def play_game(slug: str):
    game = WEB_GAMES.get(slug)
    if game is None:
        raise HTTPException(status_code=404, detail="Unknown game id")
    source = (SOURCE / game["file"]).resolve()
    if source.parent != SOURCE.resolve() or not source.is_file():
        raise HTTPException(status_code=404, detail="Game file not imported")
    return FileResponse(source, media_type="text/html", headers={"X-Content-Type-Options": "nosniff"})


@router.get("/status")
async def status() -> dict:
    data = await catalog()
    return {
        "imported": data["imported"],
        "web_games_available": sum(1 for game in data["web_games"] if game["available"]),
        "archives_available": sum(1 for item in data["game_archives"] if item["available"]),
        "archives_extracted": sum(1 for item in data["game_archives"] if item["extracted"]),
    }
