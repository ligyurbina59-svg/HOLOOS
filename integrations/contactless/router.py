"""MN24 Contactless AI: one-time QR/NFC-assisted data handoff.

This module does not process payments or store card/bank credentials.
Authentication reuses the existing MN24 app JWT verifier.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import Literal

import qrcode
from qrcode.image.svg import SvgPathImage
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from integrations.mn24_live.router import current_user

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("MN24_CONTACTLESS_DB", str(ROOT / "data" / "mn24_contactless.sqlite3")))
router = APIRouter(prefix="/contactless", tags=["MN24 Contactless AI"])


class HandoffCreate(BaseModel):
    kind: Literal["text", "url"] = "text"
    content: str = Field(min_length=1, max_length=4096)
    expires_in: int = Field(default=180, ge=60, le=600)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str, info):
        value = value.strip()
        if not value:
            raise ValueError("content cannot be blank")
        return value


class HandoffRedeem(BaseModel):
    token: str = Field(min_length=32, max_length=128)


class PaymentIntentRequest(BaseModel):
    amount_minor: int = Field(gt=0, le=100_000_000)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    recipient_reference: str = Field(min_length=3, max_length=120)


def _validate_payload(kind: str, content: str) -> str:
    clean = content.strip()
    if not clean or len(clean) > 4096:
        raise HTTPException(status_code=422, detail="Content must contain 1–4096 characters")
    if kind == "url" and not clean.startswith("https://"):
        raise HTTPException(status_code=422, detail="Only HTTPS URLs are accepted")
    return clean


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@contextmanager
def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contactless_handoffs (
                handoff_id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                consumed_at INTEGER
            )
        """)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _qr_svg(payload: str) -> bytes:
    code = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=3)
    code.add_data(payload)
    code.make(fit=True)
    image = code.make_image(image_factory=SvgPathImage)
    output = BytesIO()
    image.save(output)
    return output.getvalue()


@router.get("/health")
async def contactless_health() -> dict:
    return {
        "module": "MN24 Contactless AI",
        "status": "limited",
        "handoff": "one-time QR data transfer enabled",
        "nfc": "native Android reader/writer bridge required",
        "wallet": "provider integration pending",
        "payments": "disabled; no funds are processed",
        "authentication": "MN24 app JWT",
    }


@router.post("/handoffs", status_code=201)
async def create_handoff(payload: HandoffCreate, user: dict = Depends(current_user)) -> dict:
    content = _validate_payload(payload.kind, payload.content)
    token = secrets.token_urlsafe(32)
    handoff_id = str(uuid.uuid4())
    now = int(time.time())
    expires_at = now + payload.expires_in
    with _db() as conn:
        conn.execute(
            "INSERT INTO contactless_handoffs(handoff_id,owner,kind,content,token_hash,created_at,expires_at) VALUES(?,?,?,?,?,?,?)",
            (handoff_id, user["sub"], payload.kind, content, _token_digest(token), now, expires_at),
        )
    return {
        "handoff_id": handoff_id,
        "token": token,
        "kind": payload.kind,
        "expires_at": expires_at,
        "single_use": True,
        "qr_endpoint": f"/api/contactless/handoffs/{handoff_id}/qr",
    }


@router.post("/handoffs/{handoff_id}/qr")
async def handoff_qr(handoff_id: str, request: Request, payload: HandoffRedeem, user: dict = Depends(current_user)) -> Response:
    with _db() as conn:
        row = conn.execute(
            "SELECT owner,token_hash,expires_at,consumed_at FROM contactless_handoffs WHERE handoff_id=?",
            (handoff_id,),
        ).fetchone()
    if row is None or row["owner"] != user["sub"]:
        raise HTTPException(status_code=404, detail="Handoff not found")
    if row["consumed_at"] is not None or row["expires_at"] <= int(time.time()):
        raise HTTPException(status_code=410, detail="Handoff expired or already consumed")
    if not hmac.compare_digest(row["token_hash"], _token_digest(payload.token)):
        raise HTTPException(status_code=403, detail="Invalid handoff token")
    target = str(request.base_url).rstrip("/") + "/app/contactless#redeem=" + payload.token
    return Response(content=_qr_svg(target), media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@router.post("/redeem")
async def redeem_handoff(payload: HandoffRedeem, user: dict = Depends(current_user)) -> dict:
    digest = _token_digest(payload.token)
    now = int(time.time())
    with _db() as conn:
        row = conn.execute(
            "SELECT handoff_id,kind,content,expires_at,consumed_at FROM contactless_handoffs WHERE token_hash=?",
            (digest,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Handoff not found")
        if row["consumed_at"] is not None or row["expires_at"] <= now:
            raise HTTPException(status_code=410, detail="Handoff expired or already consumed")
        changed = conn.execute(
            "UPDATE contactless_handoffs SET consumed_at=? WHERE handoff_id=? AND consumed_at IS NULL AND expires_at>?",
            (now, row["handoff_id"], now),
        ).rowcount
        if changed != 1:
            raise HTTPException(status_code=409, detail="Handoff already redeemed")
        result = {"handoff_id": row["handoff_id"], "kind": row["kind"], "content": row["content"]}
    return {"status": "redeemed", "single_use": True, "recipient": user["sub"], **result}


@router.get("/payments/capabilities")
async def payment_capabilities() -> dict:
    return {
        "wallet_ui": "planned",
        "payment_provider": os.getenv("MN24_PAYMENT_PROVIDER", ""),
        "payment_enabled": False,
        "supported_rails": [],
        "message": "No payment provider is configured. This module cannot move money.",
    }


@router.post("/payments/intents", status_code=501)
async def create_payment_intent(payload: PaymentIntentRequest, user: dict = Depends(current_user)) -> None:
    raise HTTPException(
        status_code=503,
        detail="Payment processing is disabled until an authorized provider, merchant account, compliance checks and webhook verification are configured.",
    )
