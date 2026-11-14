"""Termux-local FastAPI entry point for Android24Creator + HOLOOS."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from integrations.github.router import router as github_router

ROOT = Path(__file__).resolve().parents[1]
UI_FILE = ROOT / "android24creator" / "github-manager.html"
app = FastAPI(title="Android24Creator Local Backend", version="0.2.0")
origins = [item.strip() for item in os.getenv("CORS_ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET"], allow_headers=["Accept", "Content-Type"])
app.include_router(github_router, prefix="/api")

@app.get("/health", tags=["System"])
async def health() -> dict[str, str]:
    return {"service": "android24creator-local-backend", "status": "ok", "runtime": "termux-ready"}

@app.get("/app/github-manager", include_in_schema=False)
async def github_manager():
    if not UI_FILE.is_file():
        return JSONResponse(status_code=404, content={"detail": "GitHub Manager UI file not found"})
    return FileResponse(UI_FILE, media_type="text/html")
