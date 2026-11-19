# Claude Code instructions — HOLOOS / MN24 REALITY

## Project context
- Product: MN24 REALITY / Hipercubo 4D inside HOLOOS and Android24Creator.
- Active integration branch: `feat/android24creator-github-integration`.
- Existing Godot 4 prototype: `examples/mn24_4d5d_game/` (4D tesseract and 5D penteract).
- Existing technical specification: `docs/MN24_4D5D_VIDEO_GAME_STUDIO.md`.

## Working rules
1. Work on the active feature branch; never commit directly to `main`.
2. Inspect existing code and tests before editing. Preserve current APIs and unrelated work.
3. Treat the generated 4D Reality artwork as a visual asset, not as a scientific claim or a real 4D capture.
4. Expected image path: `assets/images/mn24-4d-reality.png`. If the file is absent, report it as PENDING; do not create a fake replacement or claim it was uploaded.
5. Keep UI responsive and accessible: semantic HTML, alt text, keyboard navigation, reduced-motion support, and no autoplay audio/video.
6. Keep secrets in environment variables. Never commit API keys, tokens, credentials, or private user data.
7. Do not claim tests, Android export, deployment, or publication unless actually executed and verified.

## Implementation workflow
- Review `android24creator/reality-4d.html`, `android24creator_backend/main.py`, and the Godot project before changing them.
- Keep the 4D landing page linked to the existing playable Godot 4D/5D project; do not duplicate the geometry engine in browser JS.
- Run:
  ```bash
  python -m compileall -q android24creator_backend integrations
  pytest -q
  ```
- For Godot validation, open `examples/mn24_4d5d_game/project.godot` in Godot 4 and record the actual engine/device version and result.
- Summarize changed files, tests actually run, and remaining PENDING work.
