# Codex instructions — HOLOOS

## Scope
Implement and maintain MN24 REALITY / Hipercubo 4D in this repository. The current integration branch is `feat/android24creator-github-integration`; the active draft PR is #2. Do not target `main` directly.

## Source of truth
- Godot 4 game: `examples/mn24_4d5d_game/`
- Existing 4D/5D design and run instructions: `docs/MN24_4D5D_VIDEO_GAME_STUDIO.md`
- New visual experience: `android24creator/reality-4d.html`
- Image asset location (must be supplied separately): `assets/images/mn24-4d-reality.png`

## Guardrails
- Inspect repository state before editing; preserve unrelated PR work.
- Do not overwrite existing files without reading them first.
- Do not fabricate image files, credentials, integrations, test results, APKs, or deployment status.
- Keep the artwork clearly identified as a conceptual illustration of 4D/spacetime, not a literal photograph of a fourth spatial dimension.
- Use accessible, responsive HTML/CSS and local assets. Avoid external tracking scripts.
- Do not add API keys or secrets to source control.

## Validation
Run the tests relevant to changed files and report exact commands/results:
```bash
python -m compileall -q android24creator_backend integrations
pytest -q
```
Godot runtime/device validation is separate and must be reported as PENDING until executed on a real compatible runtime.
