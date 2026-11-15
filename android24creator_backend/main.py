"""Termux-local FastAPI entry point for Android24Creator + HOLOOS."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from integrations.github.router import router as github_router
from integrations.ai_gateway.router import router as ai_router
from integrations.cebolla_importer.router import router as cebolla_router
from integrations.game_library.router import router as game_router
from integrations.mn24_live.router import router as live_router

ROOT = Path(__file__).resolve().parents[1]
UI_DIR = ROOT / "android24creator"
ASSET_DIR = ROOT / "assets"
CEBOLLA_DIR = ROOT / "imports" / "Cebolla"
app = FastAPI(title="Android24Creator Local Backend", version="0.3.0")
origins = [
    item.strip()
    for item in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Content-Type"],
)
app.include_router(github_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(cebolla_router, prefix="/api")
app.include_router(game_router, prefix="/api")
app.include_router(live_router, prefix="/api")
app.mount("/assets", StaticFiles(directory=str(ASSET_DIR), check_dir=False), name="assets")
app.mount(
    "/projects/cebolla",
    StaticFiles(directory=str(CEBOLLA_DIR), html=True, check_dir=False),
    name="cebolla-assets",
)


@app.get("/health", tags=["System"])
async def health() -> dict[str, str]:
    return {
        "service": "android24creator-local-backend",
        "status": "ok",
        "runtime": "termux-ready",
        "version": "0.3.0",
    }


@app.get("/app/github-manager", include_in_schema=False)
async def github_manager():
    file = UI_DIR / "github-manager.html"
    if not file.is_file():
        return JSONResponse(status_code=404, content={"detail": "GitHub Manager UI file not found"})
    return FileResponse(file, media_type="text/html")


@app.get("/app/expansion", include_in_schema=False)
async def expansion():
    file = UI_DIR / "expansion.html"
    if not file.is_file():
        return JSONResponse(status_code=404, content={"detail": "Expansion UI file not found"})
    return FileResponse(file, media_type="text/html")


@app.get("/app/m-radio", include_in_schema=False)
async def m_radio():
    file = UI_DIR / "m-radio-control.html"
    if not file.is_file():
        return JSONResponse(status_code=404, content={"detail": "M-Radio UI file not found"})
    return FileResponse(file, media_type="text/html")


@app.get("/app/appbuilder", include_in_schema=False)
async def appbuilder_importer():
    file = UI_DIR / "appbuilder-importer.html"
    if not file.is_file():
        return JSONResponse(status_code=404, content={"detail": "AppBuilder importer UI file not found"})
    return FileResponse(file, media_type="text/html")


@app.get("/app/cebolla", include_in_schema=False)
async def cebolla_import():
    file = UI_DIR / "cebolla-import.html"
    if not file.is_file():
        return JSONResponse(status_code=404, content={"detail": "Cebolla import UI file not found"})
    return FileResponse(file, media_type="text/html")


@app.get("/app/games", include_in_schema=False)
async def game_library():
    file = UI_DIR / "games.html"
    if not file.is_file():
        return JSONResponse(status_code=404, content={"detail": "Game library UI file not found"})
    return FileResponse(file, media_type="text/html")

@app.get("/app/clipboard", include_in_schema=False)
async def clipboard_demo():
    file = UI_DIR / "clipboard.html"
    if not file.is_file():
        return JSONResponse(status_code=404, content={"detail": "Clipboard UI file not found"})
    return FileResponse(file, media_type="text/html")


@app.get("/app/clipboard.js", include_in_schema=False)
async def clipboard_script():
    file = UI_DIR / "clipboard.js"
    if not file.is_file():
        return JSONResponse(status_code=404, content={"detail": "Clipboard script file not found"})
    return FileResponse(file, media_type="application/javascript")


@app.get("/app/reality-4d", include_in_schema=False)
async def reality_4d():
    file = UI_DIR / "reality-4d.html"
    if not file.is_file():
        return JSONResponse(status_code=404, content={"detail": "MN24 Reality 4D page not found"})
    return FileResponse(file, media_type="text/html")


@app.get("/app/live", include_in_schema=False)
async def live_global():
    file = UI_DIR / "live.html"
    if not file.is_file():
        return JSONResponse(status_code=404, content={"detail": "MN24 Live Global page not found"})
    return FileResponse(file, media_type="text/html")
