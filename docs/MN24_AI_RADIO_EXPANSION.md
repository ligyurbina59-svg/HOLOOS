# MN24 AI, M-Radio and Global Expansion modules

Target repository: `ligyurbina59-svg/HOLOOS`
Target branch: `feat/android24creator-github-integration`
Runtime: local FastAPI backend in Termux.

## Modules added in this feature branch

- `integrations/ai_gateway/router.py`: server-side provider gateway for OpenAI Responses API, Anthropic Messages API, and DeepSeek Chat Completions.
- `android24creator/expansion.html`: MN24 module launcher and AI chat panel.
- `android24creator/m-radio-control.html`: M-Radio UI concept; physical controls remain disabled until a native Android HID bridge exists.
- `tests/test_ai_gateway.py`: provider status and input validation tests.

## Provider configuration

Set these variables in the Termux shell or a private, ignored environment file:

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="..."
export ANTHROPIC_API_KEY="..."
export ANTHROPIC_MODEL="..."
export ANTHROPIC_VERSION="2023-06-01"
export DEEPSEEK_API_KEY="..."
export DEEPSEEK_MODEL="deepseek-flash"
```

Do not commit real keys, place them in HTML/JavaScript, or expose them to the browser. The gateway returns only configured flags and model names, never credentials. The ChatGPT API is billed and authenticated separately from a ChatGPT consumer subscription.

### Provider behavior

- ChatGPT / OpenAI: calls the OpenAI Responses API at the fixed official endpoint.
- Claude: calls Anthropic Messages API at the fixed official endpoint.
- DeepSeek: calls DeepSeek Chat Completions at the fixed official endpoint.
- Codex: represented as an external coding-agent handoff. This gateway does not claim to launch or authenticate a Codex session. Use the Codex app/CLI separately with explicit repository permissions.

The chat endpoint is stateless and does not persist messages. Provider requests leave the local device and are subject to each provider's terms, data controls, rate limits and billing. No provider key is required to start the local backend; an unconfigured provider returns HTTP 503.

## API endpoints

- `GET /api/ai/providers`
- `POST /api/ai/chat`
- `GET /api/ai/codex`

Example request:

```json
{
  "provider": "deepseek",
  "messages": [{"role": "user", "content": "Resume el estado del proyecto."}],
  "max_tokens": 1200
}
```

## M-Radio scope

The web page is a UI scaffold only. It does not connect to Bluetooth, USB HID, radio frequency hardware, microphone, or speakers. A later Android-native module must request OS permissions, pair devices explicitly, and expose a narrow authenticated local bridge before controls are enabled. Push-to-talk must be user-initiated and visibly active.

## Global expansion scope

The dashboard is a navigation and integration shell, not a deployed global service. Regional catalogues, translations, payment rails, tenant management, cloud deployment, analytics and publishing workflows remain separate deliverables requiring provider accounts, legal review, testing and operational infrastructure.

## Security and verification

- API keys stay server-side in Termux environment variables.
- Provider endpoints are fixed in source; clients cannot supply arbitrary URLs.
- Request messages are bounded by Pydantic validation.
- HTTP timeouts and sanitized upstream errors are used.
- Chat history persistence is disabled.
- Existing GitHub Bridge remains read-only.
- Bind the FastAPI server to 127.0.0.1 for local device use. Add authentication, rate limiting and audit logging before exposing it to a network.

## Status

- IMPLEMENTED IN BRANCH: provider gateway code, expansion UI, M-Radio UI scaffold, tests and this document.
- EXISTING IMPLEMENTED: GitHub read-only bridge and GitHub Manager.
- PENDING: mount the new routers/pages in FastAPI, run test suite/CI, configure API keys, verify provider billing and responses.
- PENDING: native Android Bluetooth/USB HID implementation and device testing.
- PENDING: Codex app/CLI handoff workflow.
- PENDING: full AppBuilder project creation/import and global distribution systems.
- NOT CLAIMED: deployed production service, connected physical radio hardware, or active third-party accounts.
