import base64
import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

from android24creator_backend.main import app
from integrations.contactless import router as contactless


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _jwt(secret: str, subject: str = "test-user") -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    claims = _b64(json.dumps({"sub": subject, "exp": int(time.time()) + 600, "nbf": int(time.time()) - 1}).encode())
    signing = f"{header}.{claims}".encode()
    signature = _b64(hmac.new(secret.encode(), signing, hashlib.sha256).digest())
    return f"{header}.{claims}.{signature}"


def test_one_time_handoff_round_trip(monkeypatch, tmp_path):
    secret = "test-secret-that-is-longer-than-32-bytes"
    monkeypatch.setenv("MN24_APP_JWT_SECRET", secret)
    monkeypatch.setenv("MN24_CONTACTLESS_DB", str(tmp_path / "contactless.sqlite3"))
    client = TestClient(app)
    auth = {"Authorization": "Bearer " + _jwt(secret)}
    created = client.post(
        "/api/contactless/handoffs",
        headers=auth,
        json={"kind": "text", "content": "Hola desde MN24", "expires_in": 60},
    )
    assert created.status_code == 201
    token = created.json()["token"]
    redeemed = client.post("/api/contactless/redeem", headers=auth, json={"token": token})
    assert redeemed.status_code == 200
    assert redeemed.json()["content"] == "Hola desde MN24"
    again = client.post("/api/contactless/redeem", headers=auth, json={"token": token})
    assert again.status_code == 410


def test_url_handoff_requires_https():
    from fastapi import HTTPException
    try:
        contactless._validate_payload("url", "http://example.com")
    except HTTPException as error:
        assert error.status_code == 422
    else:
        raise AssertionError("HTTP URL should be rejected")


def test_qr_svg_generation():
    svg = contactless._qr_svg("https://example.com/receive")
    assert b"<svg" in svg
    assert b"example.com" not in svg  # QR is vector path data, not embedded text


def test_payment_is_disabled(monkeypatch):
    monkeypatch.delenv("MN24_PAYMENT_PROVIDER", raising=False)
    result = TestClient(app).get("/api/contactless/payments/capabilities")
    assert result.status_code == 200
    assert result.json()["payment_enabled"] is False
