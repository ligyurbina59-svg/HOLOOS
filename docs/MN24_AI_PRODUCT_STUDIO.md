# MN24 AI Product Studio — Android24Creator AppBuilder

**Repository:** `ligyurbina59-svg/HOLOOS`  
**Integration base:** `feat/android24creator-github-integration`  
**Implementation branch:** `feat/mn24-ai-product-studio`  
**Target:** Web + Android + PWA  
**Prototype budget ceiling:** US$100

## Scope

This is an additive module. It does not replace the existing HOLOOS, Android24Creator, Cebolla, HOLOCHRON, PANTHEON FRONT, MN24 LIVE GLOBAL, M-Radio, GitHub Manager, AI Gateway, Clipboard Bridge, game library, or other existing modules.

Six engines are represented:

1. Lovable-inspired AI App Builder — prompt-to-app direction and visual editing roadmap.
2. MN24 Vibe Coding AI — prompt-driven specification and implementation task planning.
3. UX/UI Design Studio — responsive wireframe, design tokens, component inventory and accessibility deliverables.
4. User-Centered Design — interviews, user journeys and usability-test plan.
5. MN24 Value Investing Engine — simplified discounted-cash-flow scenario calculator.
6. AI Testing & Deployment — quality checklist and release-readiness roadmap.

## Current implementation boundary

`integrations/product_studio/router.py` exposes:

- `GET /api/studio/status`
- `POST /api/studio/plan`
- `POST /api/studio/finance/evaluate`
- `GET /api/studio/qa/checklist`

The plan endpoint is deterministic and template-based. It does not invoke a model provider, generate executable source code, write files, run code, or publish an app. The finance endpoint is an illustrative DCF scenario, not an investment recommendation. The QA endpoint returns a checklist; it does not execute the checks.

## Architecture

```text
Android24Creator Web / PWA / Android WebView
                  |
           FastAPI /api/studio
                  |
       +----------+-----------+
       |          |           |
  Product Spec  Finance     QA Plan
       |          |           |
 UX/UI + UCD   DCF model   Release checklist
       |
 Existing MN24 CORE / AI Gateway (future adapter)
```

The existing AI Gateway remains the only planned provider boundary. API keys stay server-side in Termux environment variables. Never put secrets in browser code or commit them.

## US$100 prototype budget

Use local deterministic features first. Budget is a spending ceiling, not a cost guarantee:

- US$0: local FastAPI, HTML/JS, PWA manifest/service worker, pytest and Playwright where already available.
- US$0–30: optional domain/hosting only if needed; prefer existing GitHub Pages or local Termux preview first.
- US$0–50: optional model API experiments with hard usage limits; keep provider integration disabled by default.
- Reserve the remainder for unforeseen hosting or testing costs.

Do not purchase paid subscriptions or deploy billable infrastructure automatically. Actual hosting, domain, API, and store fees must be checked before spending.

## Security and product rules

- Generated code must be reviewed before execution.
- No shell execution endpoint is included.
- Keep API credentials server-side only.
- Apply authentication, per-user quotas, request-size limits and audit logs before exposing endpoints publicly.
- Financial outputs must show assumptions and uncertainty; no buy/sell recommendations.
- Collect user research with consent and minimize personal data.
- Deployment and Android signing remain manual until a secure CI/release pipeline exists.

## Termux / Linux

```bash
cd ~/HOLOOS
git fetch origin
git checkout feat/mn24-ai-product-studio
bash termux/setup.sh
source .venv/bin/activate
pytest -q
bash termux/run.sh
```

Open `http://127.0.0.1:8000/app/product-studio` and API docs at `http://127.0.0.1:8000/docs`.

## Status vocabulary

- IMPLEMENTADO: source files and routes exist in this feature branch.
- SIMULADO: behavior is represented by a deterministic template/preview rather than a live AI generation provider.
- PENDIENTE: runtime, provider, device, security, deployment or integration work not yet verified.
- PROPUESTO: future architecture or feature not yet present in source.

No production deployment, Android APK, live model generation, or successful test run is claimed by this document.
