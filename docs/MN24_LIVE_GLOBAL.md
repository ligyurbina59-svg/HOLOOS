# MN24 LIVE GLOBAL — AppBuilder / Expansion

## Purpose
A BIGO LIVE-inspired but independently branded social-live module for Android24Creator AppBuilder and MN24 Global Expansion. It does not reuse BIGO branding, assets, code, or private APIs.

## Entry points
- Expansion card: `android24creator/expansion.html`
- Live module: `android24creator/live.html`
- FastAPI page route: `GET /app/live`
- Local assets remain served from the existing `/assets` mount.

## Prototype functions
- Live Studio: browser camera permission and local preview.
- Audio Live: browser microphone permission and local mute control.
- Multi-Guest: participant tile layout; remote invitations are not connected.
- Game Live: browser screen-share permission and local preview.
- PK Battle: local demo counters only.
- Virtual Gifts: symbolic demo interactions only; no purchase, balance, or cash conversion.
- Room Chat: local page-only chat; no remote delivery or persistence.
- Safety: local demo report/block controls; no server moderation persistence.

## Production architecture still required
1. Identity service, OAuth/session management, role and age eligibility.
2. WebRTC signaling over authenticated WebSockets.
3. SFU media infrastructure for multi-party rooms, TURN/STUN, bandwidth adaptation.
4. Live ingest and distribution pipeline (e.g. WHIP/RTMP ingest and HLS/LL-HLS delivery).
5. Persistent chat, presence, invitations, notifications, reporting and moderation APIs.
6. Secure object storage, transcoding, retention and deletion controls.
7. Payments provider, ledger, refunds, fraud controls, spending limits, creator payout compliance and regional legal review.
8. Real-time translation/subtitles and avatar pipeline as later phases.

## Security and privacy
- Camera, microphone and screen capture are only requested after an explicit user click.
- Tracks are stopped when the page is closed; the Stop button releases camera tracks.
- No captured media is uploaded or recorded by this prototype.
- Do not store payment credentials or provider secrets in browser code.
- Before public launch, implement consent, privacy notices, reporting, blocking, rate limits, abuse response and age-appropriate safeguards.

## Status
- IMPLEMENTADO: dashboard entry, HTML page, FastAPI route, local camera/microphone/screen preview controls, local chat, demo PK counters, symbolic gifts, and demo safety controls.
- SIMULADO: multi-guest layout, PK scoring, gifts, chat and report/block interactions.
- PENDIENTE: remote WebRTC calls, SFU, signaling, real streaming distribution, persistence, authentication, moderation backend, payments, payouts, translation integration, load tests and Android device validation.
