# Cebolla games — Web integration

## Source audit
The inspected Cebolla main tree contains four standalone HTML5/Canvas games:
- `HOLOCHRON_WEB.html`
- `SIGNAL_EARTH_WEB.html`
- `STORMRUNNER_RAGNAROK.html`
- `PANTHEON_FRONT_WEB.html`

Each has an inline script, Canvas renderer, and no external script or stylesheet references in the inspected HTML. Three game-oriented ZIP packages were also found: RunicArena, SkyBolt, and Stormrunner: Thunder of the North. Their archive contents have not been inspected by the GitHub text fetcher and must be extracted locally with the safe extraction script before any web-launch claim.

APK files are Android application artifacts, not HTML5 web games. They remain separate; no automatic install or conversion is performed.

## Termux
```bash
cd ~/HOLOOS
git pull --ff-only origin feat/android24creator-github-integration
bash termux/import-cebolla.sh       # only if imports/Cebolla does not exist
bash termux/extract-cebolla-games.sh
bash termux/run.sh
```

Open `http://127.0.0.1:8000/app/games`.

## Routes
- `GET /api/games/catalog`
- `GET /api/games/status`
- `GET /api/games/play/holochron`
- `GET /api/games/play/signal-earth`
- `GET /api/games/play/stormrunner-ragnarok`
- `GET /api/games/play/pantheon-front`
- ZIP contents are extracted to a private local directory and are not served to the browser until manual review and an explicit launch integration.

The game player uses an iframe sandbox. These source games use Canvas and inline JavaScript; the sandbox permits scripts and same-origin localStorage, but denies top-level navigation and popups.

## Tests
```bash
. .venv/bin/activate
pytest -q
```

## Security limits
The ZIP extractor accepts only the three named game archives; rejects path traversal, symlinks, excessive entry counts, extraction above 100 MiB, and compression ratios above 200; and never runs extracted code. HTML/JavaScript is still untrusted content: review it before enabling wider network access or publishing publicly. A same-origin sandbox is not a complete security boundary against a malicious game; production hosting should isolate games on a separate origin.

## Status
- VERIFIED: source tree lists four standalone HTML5/Canvas game files and three game-oriented ZIP files.
- IMPLEMENTED: Web catalog, allowlisted launch endpoint, sandboxed player, Termux ZIP extraction utility, tests.
- PENDING: actual Termux extraction and validation of archive entrypoints and game runtime.
- PENDING: APK analysis/compatibility and any native-to-Web port.
- PENDING: production Web hosting and HTTPS.
