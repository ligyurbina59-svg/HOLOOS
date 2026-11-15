import base64
import hashlib
import hmac
import json
import os
import time

import pytest
from fastapi import HTTPException

from integrations.mn24_live.router import verify_app_jwt, ROOM_RE


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def token(secret: str, claims: dict) -> str:
    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = b64(json.dumps(claims).encode())
    signed = f"{header}.{body}".encode()
    signature = b64(hmac.new(secret.encode(), signed, hashlib.sha256).digest())
    return f"{header}.{body}.{signature}"


def test_room_id_validation():
    assert ROOM_RE.fullmatch("mn24-global")
    assert not ROOM_RE.fullmatch("../etc/passwd")
    assert not ROOM_RE.fullmatch("ab")


def test_valid_app_jwt(monkeypatch):
    secret = "test-secret-that-is-at-least-32-bytes-long"
    monkeypatch.setenv("MN24_APP_JWT_SECRET", secret)
    jwt = token(secret, {"sub": "user_123", "exp": int(time.time()) + 120})
    assert verify_app_jwt(jwt)["sub"] == "user_123"


def test_expired_app_jwt_rejected(monkeypatch):
    secret = "test-secret-that-is-at-least-32-bytes-long"
    monkeypatch.setenv("MN24_APP_JWT_SECRET", secret)
    jwt = token(secret, {"sub": "user_123", "exp": int(time.time()) - 1})
    with pytest.raises(HTTPException) as error:
        verify_app_jwt(jwt)
    assert error.value.status_code == 401


def test_tampered_app_jwt_rejected(monkeypatch):
    secret = "test-secret-that-is-at-least-32-bytes-long"
    monkeypatch.setenv("MN24_APP_JWT_SECRET", secret)
    jwt = token(secret, {"sub": "user_123", "exp": int(time.time()) + 120})
    with pytest.raises(HTTPException) as error:
        verify_app_jwt(jwt + "tampered")
    assert error.value.status_code == 401

from fastapi import FastAPI
from fastapi.testclient import TestClient

from integrations.mn24_live.router import router, current_user

def test_room_create_and_duplicate(tmp_path, monkeypatch):
    import integrations.mn24_live.router as live
    monkeypatch.setattr(live, "DB_PATH", tmp_path / "live.sqlite3")
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[current_user] = lambda: {"sub": "demo_user"}
    client = TestClient(app)
    payload = {"room_id": "mn24-demo", "title": "MN24 Demo Live", "category": "gaming", "language": "es"}
    created = client.post("/api/live/rooms", json=payload)
    assert created.status_code == 201
    assert created.json()["owner"] == "demo_user"
    duplicate = client.post("/api/live/rooms", json=payload)
    assert duplicate.status_code == 409
    listed = client.get("/api/live/rooms")
    assert listed.status_code == 200
    assert listed.json()["rooms"][0]["room_id"] == "mn24-demo"
