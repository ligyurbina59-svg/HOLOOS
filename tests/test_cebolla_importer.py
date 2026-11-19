import json

import pytest
from fastapi import HTTPException

from integrations.cebolla_importer import router as importer


@pytest.mark.anyio
async def test_status_reports_not_imported_when_directory_missing(tmp_path, monkeypatch):
    root = tmp_path / "imports" / "Cebolla"
    monkeypatch.setattr(importer, "ROOT", tmp_path)
    monkeypatch.setattr(importer, "IMPORT_DIR", root)
    monkeypatch.setattr(importer, "MANIFEST", root / ".mn24-import-manifest.json")
    result = await importer.status()
    assert result["imported"] is False
    assert result["repository"] == "ligyurbina59-svg/Cebolla"


@pytest.mark.anyio
async def test_status_reads_import_manifest(tmp_path, monkeypatch):
    root = tmp_path / "imports" / "Cebolla"
    root.mkdir(parents=True)
    manifest = root / ".mn24-import-manifest.json"
    manifest.write_text(json.dumps({
        "source_commit": "abc123",
        "file_count": 94,
        "total_bytes": 24662577,
    }), encoding="utf-8")
    monkeypatch.setattr(importer, "ROOT", tmp_path)
    monkeypatch.setattr(importer, "IMPORT_DIR", root)
    monkeypatch.setattr(importer, "MANIFEST", manifest)
    result = await importer.status()
    assert result["imported"] is True
    assert result["file_count"] == 94


@pytest.mark.anyio
async def test_inventory_requires_import(tmp_path, monkeypatch):
    root = tmp_path / "imports" / "Cebolla"
    monkeypatch.setattr(importer, "ROOT", tmp_path)
    monkeypatch.setattr(importer, "IMPORT_DIR", root)
    monkeypatch.setattr(importer, "MANIFEST", root / ".mn24-import-manifest.json")
    with pytest.raises(HTTPException) as error:
        await importer.inventory()
    assert error.value.status_code == 404


def test_backend_mounts_cebolla_web_android_and_api_routes():
    from android24creator_backend.main import app

    api_paths = set(app.openapi()["paths"])
    route_paths = {getattr(route, "path", None) for route in app.routes}
    assert "/api/cebolla/status" in api_paths
    assert "/api/cebolla/inventory" in api_paths
    assert "/app/cebolla" in route_paths
    assert "/projects/cebolla" in route_paths
