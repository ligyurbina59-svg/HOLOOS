"""MN24 Live Global APIs: rooms, JWT-authenticated LiveKit tokens and chat signaling."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
import time
from collections import defaultdict
from contextlib import contextmanager
from urllib.parse import urlsplit
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("MN24_LIVE_DB", str(ROOT / "data" / "mn24_live.sqlite3")))
ROOM_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,47}$")
IDENTITY_RE = re.compile(r"^[A-Za-z0-9_.@-]{3,80}$")
router = APIRouter(prefix="/live", tags=["MN24 Live Global"])


class RoomCreate(BaseModel):
    room_id: str = Field(min_length=3, max_length=48, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=3, max_length=100)
    category: str = Field(default="social", max_length=32)
    language: str = Field(default="es", min_length=2, max_length=12)


class TokenRequest(BaseModel):
    room_id: str = Field(min_length=3, max_length=48)
    role: str = Field(default="viewer", pattern="^(viewer|host|speaker)$")


class ChatHub:
    def __init__(self) -> None:
        self.members: dict[str, set[WebSocket]] = defaultdict(set)
        self.lock = asyncio.Lock()

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            self.members[room_id].add(websocket)

    async def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        async with self.lock:
            self.members[room_id].discard(websocket)
            if not self.members[room_id]:
                self.members.pop(room_id, None)

    async def broadcast(self, room_id: str, payload: dict[str, Any]) -> None:
        async with self.lock:
            peers = list(self.members.get(room_id, set()))
        stale = []
        for peer in peers:
            try:
                await peer.send_json(payload)
            except Exception:
                stale.append(peer)
        for peer in stale:
            await self.disconnect(room_id, peer)


chat_hub = ChatHub()


@contextmanager
def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS live_rooms (
                room_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                language TEXT NOT NULL,
                owner TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'scheduled',
                created_at INTEGER NOT NULL
            )
        """)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def verify_app_jwt(token: str) -> dict[str, Any]:
    """Verify HS256 app access token. No secret means fail closed."""
    secret = os.getenv("MN24_APP_JWT_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(status_code=503, detail="App authentication is not configured")
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Invalid access token")
    signing_input = (parts[0] + "." + parts[1]).encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    try:
        supplied = _b64url_decode(parts[2])
        header = json.loads(_b64url_decode(parts[0]))
        claims = json.loads(_b64url_decode(parts[1]))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid access token") from exc
    if header.get("alg") != "HS256" or not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="Invalid access token")
    now = int(time.time())
    if int(claims.get("exp", 0)) <= now or int(claims.get("nbf", 0)) > now:
        raise HTTPException(status_code=401, detail="Expired or inactive access token")
    subject = claims.get("sub")
    if not isinstance(subject, str) or not IDENTITY_RE.fullmatch(subject):
        raise HTTPException(status_code=401, detail="Invalid token subject")
    return claims


def current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer app access token required")
    return verify_app_jwt(authorization[7:].strip())


@router.get("/health")
async def live_health() -> dict[str, Any]:
    livekit_url = os.getenv("LIVEKIT_URL", "")
    configured = bool(livekit_url and os.getenv("LIVEKIT_API_KEY") and os.getenv("LIVEKIT_API_SECRET"))
    return {
        "module": "MN24 LIVE GLOBAL",
        "status": "ready" if configured else "limited",
        "livekit_configured": configured,
        "auth_configured": len(os.getenv("MN24_APP_JWT_SECRET", "")) >= 32,
        "chat_transport": "websocket-process-local",
        "media_transport": "livekit-webrtc-sfu" if configured else "not-configured",
    }


@router.get("/rooms")
async def list_rooms() -> dict[str, Any]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT room_id,title,category,language,status,created_at FROM live_rooms "
            "WHERE status IN ('scheduled','live') ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    return {"rooms": [dict(row) for row in rows]}


@router.post("/rooms", status_code=201)
async def create_room(payload: RoomCreate, user: dict = Depends(current_user)) -> dict[str, Any]:
    room_id = payload.room_id.lower()
    if not ROOM_RE.fullmatch(room_id):
        raise HTTPException(status_code=422, detail="Invalid room id")
    now = int(time.time())
    try:
        with _db() as conn:
            conn.execute(
                "INSERT INTO live_rooms(room_id,title,category,language,owner,status,created_at) "
                "VALUES(?,?,?,?,?,'scheduled',?)",
                (room_id, payload.title.strip(), payload.category, payload.language, user["sub"], now),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Room id already exists") from exc
    return {"room_id": room_id, "title": payload.title.strip(), "status": "scheduled", "owner": user["sub"]}


@router.post("/token")
async def create_livekit_token(payload: TokenRequest, user: dict = Depends(current_user)) -> dict[str, Any]:
    if not ROOM_RE.fullmatch(payload.room_id):
        raise HTTPException(status_code=422, detail="Invalid room id")
    with _db() as conn:
        room = conn.execute("SELECT owner,status FROM live_rooms WHERE room_id=?", (payload.room_id,)).fetchone()
    if room is None or room["status"] not in ("scheduled", "live"):
        raise HTTPException(status_code=404, detail="Live room not found")
    if payload.role in ("host", "speaker") and room["owner"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Only the room owner may publish in this version")
    url = os.getenv("LIVEKIT_URL", "")
    api_key, api_secret = os.getenv("LIVEKIT_API_KEY", ""), os.getenv("LIVEKIT_API_SECRET", "")
    if not (url and api_key and api_secret):
        raise HTTPException(status_code=503, detail="LiveKit SFU is not configured")
    try:
        from livekit import api
        grants = api.VideoGrants(
            room_join=True,
            room=payload.room_id,
            can_publish=payload.role in ("host", "speaker"),
            can_subscribe=True,
            can_publish_data=True,
        )
        token = api.AccessToken(api_key, api_secret).with_identity(user["sub"]).with_grants(grants).to_jwt()
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Install livekit-api dependency") from exc
    return {"server_url": url, "token": token, "room_id": payload.room_id, "identity": user["sub"]}


@router.websocket("/ws/{room_id}")
async def room_chat(websocket: WebSocket, room_id: str, token: str = Query(default="")) -> None:
    if not ROOM_RE.fullmatch(room_id):
        await websocket.close(code=1008, reason="Invalid room")
        return
    origin = websocket.headers.get("origin")
    if origin:
        origin_host = urlsplit(origin).netloc
        request_host = websocket.headers.get("host", "")
        allowed = {
            item.strip()
            for item in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
            if item.strip()
        }
        if origin_host != request_host and origin not in allowed:
            await websocket.close(code=1008, reason="Origin not allowed")
            return
    try:
        claims = verify_app_jwt(token)
    except HTTPException:
        await websocket.close(code=1008, reason="Authentication required")
        return
    with _db() as conn:
        exists = conn.execute("SELECT 1 FROM live_rooms WHERE room_id=?", (room_id,)).fetchone()
    if not exists:
        await websocket.close(code=1008, reason="Room not found")
        return
    await chat_hub.connect(room_id, websocket)
    await chat_hub.broadcast(room_id, {"type": "presence", "event": "joined", "identity": claims["sub"]})
    last_sent = 0.0
    try:
        while True:
            payload = await websocket.receive_json()
            now = time.monotonic()
            if now - last_sent < 0.7:
                await websocket.send_json({"type": "error", "detail": "Rate limit: wait before sending"})
                continue
            if not isinstance(payload, dict) or payload.get("type") != "chat":
                continue
            message = str(payload.get("message", "")).strip()
            if not message or len(message) > 500:
                await websocket.send_json({"type": "error", "detail": "Message must contain 1–500 characters"})
                continue
            last_sent = now
            await chat_hub.broadcast(room_id, {
                "type": "chat", "identity": claims["sub"],
                "message": message, "timestamp": int(time.time()),
            })
    except WebSocketDisconnect:
        pass
    finally:
        await chat_hub.disconnect(room_id, websocket)
        await chat_hub.broadcast(room_id, {"type": "presence", "event": "left", "identity": claims["sub"]})
