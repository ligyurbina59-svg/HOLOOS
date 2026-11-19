# MN24 LIVE GLOBAL — Web + Android + PC

## Scope
Independent MN24 Labs social-live product. BIGO LIVE is a feature reference only; no BIGO trademarks, source code, private APIs, or assets are reused.

## Architecture
- Web/PWA: `android24creator/live.html`; responsive browser interface.
- Android: Android Chrome/PWA now; wrap as native Android app later if needed.
- PC: Chrome/Edge/Firefox browser interface; desktop wrapper is optional.
- API: FastAPI router at `/api/live`.
- Auth: app-issued HS256 JWT. Configure `MN24_APP_JWT_SECRET` to the same secret used by the trusted MN24 identity service. This module does not issue app login JWTs.
- Media: LiveKit SFU using WebRTC; server-side room tokens are generated only by the backend.
- Chat: authenticated WebSocket at `/api/live/ws/{room_id}?token=<app-jwt>`; current broadcast hub is process-local and ephemeral.
- Persistence: SQLite room metadata; move to PostgreSQL for production.
- Future scale: Redis-backed presence/chat, multi-node SFU deployment, TURN, metrics, object storage, moderation workers and CDN/LL-HLS distribution.

## API
- `GET /api/live/health`
- `GET /api/live/rooms`
- `POST /api/live/rooms` (Bearer app JWT; owner creates room)
- `POST /api/live/token` (Bearer app JWT; owner may request publisher token, others viewer token)
- `WS /api/live/ws/{room_id}?token=<app-jwt>`

## Roles
- `viewer`: subscribe only.
- `host`: publish and subscribe; only room owner.
- `speaker`: reserved for owner in this first cut. Moderator-approved guest promotion is not implemented.

## Run locally
1. Install the existing backend requirements plus `requirements-mn24-live.txt`.
2. Copy `.env.mn24-live.example` to `.env.mn24-live`, replace secrets.
3. Start LiveKit with `docker compose -f docker-compose.mn24-live.yml up -d`.
4. Export environment variables from the env file into the backend process.
5. Start FastAPI using the existing project entrypoint.

## Security notes
- JWT validation is fail-closed; secret must be at least 32 characters.
- LiveKit API secret remains backend-only. Never place it in HTML, JavaScript, APK assets or Git.
- Token endpoint checks room ownership for publisher grants.
- WebSocket chat requires an app JWT, validates room IDs, limits message length and applies per-connection throttling. Query-string JWTs should be short-lived and redacted from reverse-proxy access logs.
- Camera/microphone/screen capture require explicit browser permission. Production access requires HTTPS (localhost is suitable for local development).
- Add production identity/session revocation, account age eligibility, report/block persistence, human moderation, rate limits across nodes, abuse monitoring, privacy retention/deletion and payment compliance before public launch.

## Platform notes
- Web: browser PWA.
- Android: HTTPS PWA or Android WebView/native wrapper; verify camera/mic permissions and lifecycle on physical devices.
- PC: browser PWA; optional Tauri/Electron wrapper.
- Media requires network/firewall planning. Host networking in Compose is a local Linux development shortcut and may not behave identically on all Android/Termux environments.

## Status
- IMPLEMENTADO in repository: room metadata API, app JWT verification, role-scoped LiveKit token minting, authenticated WebSocket chat, UI integration, health endpoint, test suite and local LiveKit config.
- SIMULADO: PK battle counters, symbolic gifts, creator engagement widgets, local UI fallbacks.
- PENDIENTE: connect existing MN24 login issuer and frontend SDK bundle, PostgreSQL migration, Redis multi-instance chat, TURN/TLS public deployment, Egress/recording, moderation workflows, translation provider, payment/payout ledger, Android native QA, PC packaging, load/security testing and production monitoring.
