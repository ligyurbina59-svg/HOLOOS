# HOLOOS — MN24 / Android24Creator integration

HOLOOS is the selected source repository for the Android24Creator AppBuilder integration.

## Verified repository baseline

- Repository: https://github.com/ligyurbina59-svg/HOLOOS
- Default branch at inspection: `main`
- Visibility: public
- GitHub connector permissions observed: admin / maintain / pull / push
- Existing repository contents include multiple APK/ZIP artifacts, PWA manifests, two standalone HTML experiences, and `chat_project_merger.py`.
- The README describes HOLOOS as a holographic/spatial computing platform.
- The root contains several unrelated or vendor-derived PWA manifests. Do not treat them as one canonical AppBuilder manifest.
- Binary APK/ZIP artifacts were inventoried by metadata only; they were not downloaded, unpacked, malware-scanned, or validated.

## Integration architecture

```text
ChatGPT GitHub connector ── review / search / issues / PRs / commits
                                  │
                                  ▼
                         HOLOOS (source of truth)
                                  ▲
                                  │ HTTPS, allowlisted read-only API
                                  ▼
Android24Creator UI ──► FastAPI GitHub Bridge ──► GitHub REST API
                                  │
                                  └── server-side GITHUB_TOKEN only
```

The ChatGPT connector and the AppBuilder runtime are separate clients. A connected GitHub account in ChatGPT does not automatically give a deployed AppBuilder server access. The AppBuilder bridge therefore uses its own server-side credential.

## Phased delivery

1. **Read-only MVP:** repository metadata, directory listing and UTF-8 text file retrieval.
2. **AppBuilder UI:** repository selector, branch selector, tree/file viewer, project import manifest.
3. **Controlled writes:** create a feature branch, stage files, review diff, open pull request. No direct writes to `main`.
4. **CI and release:** tests, dependency/security scans, build artifacts and release approvals.
5. **Global expansion:** multiple allowlisted repositories, organizations, project templates, locale packs and per-project access policies.

## Backend setup

Python 3.12+:

```bash
python -m pip install fastapi uvicorn httpx
```

Set server environment variables (never in Vite `VITE_*` variables):

```bash
export GITHUB_TOKEN="YOUR_FINE_GRAINED_TOKEN"
export GITHUB_REPOSITORY_ALLOWLIST="ligyurbina59-svg/HOLOOS"
```

For initial read-only operation, grant the fine-grained token only repository **Metadata: read** and **Contents: read** for HOLOOS. Do not use a classic personal access token with broad scopes. If public unauthenticated reads are sufficient, omit `GITHUB_TOKEN`; rate limits will be lower.

Mount the router in the existing FastAPI application:

```python
from integrations.github.router import router as github_router
app.include_router(github_router, prefix="/api")
```

Run locally:

```bash
bash termux/run.sh
```

Endpoints:

- `GET /api/integrations/github/health`
- `GET /api/integrations/github/repository`
- `GET /api/integrations/github/contents?path=`
- `GET /api/integrations/github/file?path=README.md`
- `GET /api/integrations/github/project/inspect?ref=main`

Optional query parameters: `repository=owner/name`, `ref=branch-or-tag`. Only repositories in `GITHUB_REPOSITORY_ALLOWLIST` are accepted.

## Termux local runtime

The repository includes a minimal FastAPI entry point at `android24creator_backend/main.py`, a Termux setup script, and a launcher. From the cloned repository root in Termux:

```bash
bash termux/setup.sh
bash termux/run.sh
```

Open `http://127.0.0.1:8000/app/github-manager`. Check `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/docs`. The default bind address is loopback only; do not set `HOST=0.0.0.0` on an untrusted network. The bridge can read public HOLOOS data without a token. If needed, configure a fine-grained GitHub token as a Termux environment variable; never paste it into the HTML or commit it.

## Universal Project Importer

`GET /api/integrations/github/project/inspect?repository=ligyurbina59-svg/HOLOOS&ref=main` builds a JSON manifest from Git tree metadata. It estimates category and technology, lists up to 1,000 entries, and marks the result inspection-only. It does not download source files, run build scripts, install dependencies, or inspect binary contents. Treat category and technology as heuristic hints and review the manifest manually before import.

## AppBuilder browser UI

A static, read-only browser interface is available at `android24creator/github-manager.html`. Serve it from the same origin as FastAPI (or configure CORS for a specific trusted origin). Set the API base URL in the UI if the backend is mounted elsewhere. It lists directories and opens UTF-8 text files; it never receives a GitHub token and never executes repository files.

## Local tests

Install test dependencies:

```bash
python -m pip install pytest
pytest -q
```

The included tests cover repository allowlisting, path validation, safe Git reference validation and manifest generation. CI is configured to run them on pushes to the feature branch and pull requests to `main`. The CI workflow has not yet been observed running successfully.

## Security controls and required production work

Implemented in this bridge:
- fixed GitHub API origin (no arbitrary URL fetch / SSRF parameter);
- repository allowlist;
- path traversal rejection;
- server-side token only; no token response field;
- read-only endpoints only;
- bounded HTTP timeout;
- explicit upstream error handling;
- UTF-8 text-only file endpoint.

Before public deployment:
- put the token in a secret manager, not a committed `.env`;
- use a GitHub App installation token for production where practical;
- restrict CORS to the exact AppBuilder origin;
- add user authentication, authorization and audit logs to the FastAPI app;
- add rate limiting, response-size limits, caching policy and structured redacted logs;
- add unit/integration tests and CI;
- rotate/revoke exposed credentials immediately;
- never import or execute repository files automatically;
- scan downloaded archives/APKs before use;
- require explicit approval and pull-request review for all writes.

## Status

- **IMPLEMENTED:** isolated read-only bridge source and this integration plan committed on a feature branch.
- **VERIFIED:** GitHub repository metadata, default branch and selected text files inspected through the connected GitHub integration.
- **IMPLEMENTED:** Termux FastAPI entry point, local UI route, setup/launcher scripts, project tree inspection endpoint, and GitHub Actions test workflow are committed on the feature branch.
- **PENDING:** install on the user’s Termux device, configure optional server-side token, execute tests locally or observe a passing CI run, import source files into a selected AppBuilder project, deploy.
- **NOT VERIFIED:** APK contents, ZIP contents, runtime behavior, build reproducibility, security scan and production deployment.

Do not merge this branch or enable write operations until the pending checks are completed.


## Additional MN24 modules (feature branch)

The feature branch also adds the AI gateway, M-Radio interface and expansion shell. See `docs/MN24_AI_RADIO_EXPANSION.md`.

New local routes:
- `GET /app/expansion`
- `GET /app/m-radio`
- `GET /app/appbuilder`
- `GET /api/ai/providers`
- `POST /api/ai/chat`
- `GET /api/ai/codex`
- `GET /api/ai/claude-code`

The GitHub read-only allowlist defaults to HOLOOS and Cebolla. Override it with `GITHUB_REPOSITORY_ALLOWLIST` in the Termux environment.

AI API credentials are optional and provider-specific. ChatGPT/OpenAI API, Claude API and DeepSeek API calls are made only when the corresponding server-side key and model variables are configured. Claude Code and Codex are external coding-agent handoffs, not API chat providers. No third-party credentials were added to the repository.

The AppBuilder page currently inspects repository metadata and generates a manifest only; source import/build execution remains gated pending manual review and explicit approval. M-Radio is a user-interface scaffold; no native Bluetooth/USB HID implementation is claimed.
