# MN24 Contactless AI — Android24Creator AppBuilder

Target repository: `ligyurbina59-svg/HOLOOS`
Target branch: `feat/android24creator-github-integration`
Target device: Honor Android (model and Android version must be checked on-device).

## Scope implemented in this branch

- Authenticated, one-time QR handoff for short text and HTTPS links.
- Expiring handoff tokens (60–600 seconds), SHA-256 token hashes at rest, atomic single-use redemption.
- SVG QR generation without embedding credentials in the browser.
- AppBuilder page at `/app/contactless`.
- API health and payment-capability status.
- Native Android NFC NDEF reader/writer sample for HTTPS handoff URLs.
- Tests for one-time redemption, URL validation, QR generation and disabled payment state.

The router reuses the existing `MN24_APP_JWT_SECRET` HS256 verifier from MN24 Live. Configure the same random secret (at least 32 characters) in both the existing MN24 JWT issuer and this backend as `MN24_APP_JWT_SECRET`. This repository contains the verifier but does not establish a user-login/token-issuing screen for Contactless AI; obtain the Bearer JWT from the existing authenticated MN24 session. Do not invent a production token issuer or use a development token in production. The browser does not persist the access token. QR generation sends the one-time token in a POST body; the QR encodes it in a URL fragment so it is not sent in the initial HTTP request.

## API

- `GET /api/contactless/health`
- `POST /api/contactless/handoffs` — authenticated; JSON: `{"kind":"text","content":"hello","expires_in":180}`
- `POST /api/contactless/handoffs/{handoff_id}/qr` — authenticated owner only; token in JSON body, returns SVG QR — authenticated owner only; returns SVG QR
- `POST /api/contactless/redeem` — authenticated recipient; JSON: `{"token":"..."}`; token is single-use
- `GET /api/contactless/payments/capabilities`
- `POST /api/contactless/payments/intents` — deliberately disabled (503)

## Important payment boundary

This implementation does NOT accept card numbers, bank credentials, PAN, CVV, PINs, payment tokens or money. It does not move funds, emulate a payment card, or connect to a bank. Payment capability reports disabled. A production wallet/payment module needs a licensed/acquiring payment provider, merchant onboarding, tokenization, supported country/rail checks, webhook signature verification, idempotency, reconciliation, fraud controls and legal/compliance review. Never store raw card data.

NFC in this implementation is NDEF tag reader/writer for short HTTPS handoff links. It does not provide direct phone-to-phone NFC exchange: Android Beam is deprecated and HCE is not implemented. It is not EMV contactless payment, HCE wallet emulation, or Android default wallet integration. NFC hardware and OS behavior vary by Honor model/region; test adapter presence, NFC enabled state, NDEF tag support and permissions on the actual device. QR remains the cross-device fallback. TeleTransfer money movement and provider-backed wallet remain separate pending integrations.

## Honor Android native integration

- Merge `android24creator/native/contactless/AndroidManifest.fragment.xml` into the existing manifest; do not replace it.
- Add `ContactlessNfcActivity.kt` to the existing Android module and connect its callbacks to the AppBuilder bridge.
- Do not add payment AIDs or `HostApduService` until an authorized wallet/payment provider explicitly supplies that architecture.
- NFC tag writing is user-initiated; show destination and expiry before writing.
- Never put payment credentials or long-lived bearer tokens in NDEF. The sample accepts HTTPS links only.
- The Kotlin sample is source-level integration material; this repository is not a confirmed Gradle Android project, so no APK build is claimed.

## Termux setup

From the HOLOOS repository root:

```bash
git switch feat/android24creator-github-integration
git pull --ff-only
bash termux/setup.sh
export MN24_APP_JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
bash termux/run.sh
```

Open `http://127.0.0.1:8000/app/contactless`. Obtain a valid app JWT from the existing authentication service; the contactless page does not issue credentials. Loopback mode is local development only: a second phone cannot reach the sender's `127.0.0.1`. For device-to-device QR redemption, deploy the backend on a trusted HTTPS host reachable by both devices and configure the reverse proxy correctly. Do not expose the Termux development server directly to public networks.

If you need to retain the secret across terminal sessions, store it in a local ignored environment file with permissions 600; never commit it. The existing project authentication must issue compatible HS256 JWTs using this same secret. Do not create a second identity system.

## Tests

```bash
. .venv/bin/activate
pytest -q tests/test_contactless.py
pytest -q
```

## Security notes

- HTTPS is mandatory outside localhost.
- Handoff payload is limited to 4096 characters; URL handoffs accept HTTPS only.
- Tokens are generated with a cryptographically secure random generator; only SHA-256 hashes are stored.
- Handoffs expire and are atomically consumed once.
- API endpoints require existing MN24 app JWT authentication except health and payment capability status.
- QR response is marked no-store.
- No raw card/bank details are accepted.
- Add rate limits, audit events, user/device binding and abuse monitoring before production.
- Add database cleanup for expired handoffs and enforce per-user quotas before public deployment.

## Status

- IMPLEMENTED IN FEATURE BRANCH: backend QR handoff API, UI page, native NFC NDEF source sample, tests, documentation and FastAPI route mount.
- NOT YET VERIFIED ON DEVICE: Honor NFC hardware/OS compatibility, NFC tag exchange, camera QR scanning, Termux runtime, APK packaging.
- PAYMENT/WALLET MONEY MOVEMENT: PENDING provider and compliance integration; disabled in code.
- TELETRANSFER: connected at the architecture level only; this handoff service is not yet connected to TeleTransfer's money-transfer backend.
- NOT CLAIMED: production readiness, bank integration, EMV certification, completed APK or deployment.
