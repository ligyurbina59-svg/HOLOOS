"""Read-only status and inventory API for the local Cebolla import."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

ROOT = Path(__file__).resolve().parents[2]
IMPORT_DIR = ROOT / "imports" / "Cebolla"
MANIFEST = IMPORT_DIR / ".mn24-import-manifest.json"

router = APIRouter(prefix="/cebolla", tags=["Cebolla Import"])


def _safe_root() -> Path:
    root = IMPORT_DIR.resolve()
    expected_parent = (ROOT / "imports").resolve()
    if root.parent != expected_parent:
        raise HTTPException(status_code=500, detail="Import path failed safety validation")
    return root


@router.get("/status")
async def status() -> dict:
    root = _safe_root()
    if not root.is_dir() or not MANIFEST.is_file():
        return {
            "repository": "ligyurbina59-svg/Cebolla",
            "imported": False,
            "destination": "imports/Cebolla",
            "instruction": "Run: bash termux/import-cebolla.sh",
        }
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Import manifest is unreadable") from exc
    return {
        "repository": "ligyurbina59-svg/Cebolla",
        "imported": True,
        "destination": "imports/Cebolla",
        "commit": data.get("source_commit"),
        "file_count": data.get("file_count"),
        "total_bytes": data.get("total_bytes"),
        "manifest": "/projects/cebolla/.mn24-import-manifest.json",
    }


@router.get("/inventory")
async def inventory() -> dict:
    root = _safe_root()
    if not root.is_dir() or not MANIFEST.is_file():
        raise HTTPException(status_code=404, detail="Cebolla is not imported yet")
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Import manifest is unreadable") from exc
    return {
        "repository": "ligyurbina59-svg/Cebolla",
        "source_commit": data.get("source_commit"),
        "file_count": data.get("file_count"),
        "total_bytes": data.get("total_bytes"),
        "files": data.get("files", []),
    }
