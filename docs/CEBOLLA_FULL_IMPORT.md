# Cebolla full import — Android24Creator / HOLOOS

Source: `https://github.com/ligyurbina59-svg/Cebolla`  
Source branch: `main`  
Target runtime: Termux local FastAPI  
Target clients: responsive Web and Android browser/PWA shell

## Source inventory inspected

GitHub recursive tree inspection returned 94 tracked files and 24,662,577 bytes (about 23.52 MiB) on the inspected main branch. Types: 53 APK, 7 HTML, 5 ZIP, 13 JPG, 2 JPEG, 2 PNG, 1 MP4, 1 AVIF, 1 XLSX, 3 JSON, 2 Markdown, 2 Python, 1 TXT and 1 extensionless file. Source contains the `analisis-ia` FastAPI/HTML MVP and many independent game/app artifacts.

This is an inventory of the inspected GitHub tree, not proof that all files have been downloaded to a user's device.

## Full import command

From the HOLOOS repository root in Termux:

```bash
bash termux/import-cebolla.sh
```

The script:
1. shallow-clones the source `main` branch to a temporary directory;
2. copies the complete checked-out working tree, including APK/ZIP/media assets, into `imports/Cebolla`;
3. removes the nested Git metadata from the web-served copy;
4. creates `.mn24-import-manifest.json` with source commit, file count, byte total and SHA-256 per file;
5. atomically renames the staging directory into place;
6. refuses to overwrite an existing import.

No APK, archive, HTML or script is automatically executed or installed. This import copies source artifacts; it does not establish that every APK is safe, compatible, signed, or reproducible.

## Local endpoints

- `GET /app/cebolla` — responsive Web/Android import dashboard
- `GET /projects/cebolla/` — static browse of imported files
- `GET /api/cebolla/status` — import status
- `GET /api/cebolla/inventory` — full SHA-256 inventory

The server defaults to `127.0.0.1:8000`, suitable for the same Android device. Network/LAN or public deployment requires HTTPS, authentication, authorization, rate limits, and a deliberate deployment configuration. Do not expose the import directory as a public download site without reviewing the contents and licensing.

## Running the source ANÁLISIS VIRTUAL IA MVP

After import, the source project can be launched separately:

```bash
cd ~/HOLOOS/imports/Cebolla/analisis-ia
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

Open `http://127.0.0.1:8010/`. It is a separate process and does not replace the HOLOOS backend. The current source documentation describes deterministic rules, not a trained AI model. Do not run this second service on the same port as HOLOOS.

## Tests and verification

Run from HOLOOS root:

```bash
. .venv/bin/activate
pytest -q
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/cebolla/status
curl -fsS http://127.0.0.1:8000/api/cebolla/inventory
```

Tests validate importer API status and missing-import behavior. The actual full repository download, checksum validation and Android installation must be verified on the user's Termux device.

## Status

- VERIFIED: public source repository and default branch `main`.
- VERIFIED: GitHub tree has 94 files / 24,662,577 bytes at inspection time.
- IMPLEMENTED IN HOLOOS FEATURE BRANCH: import script, manifest generation, API, Web/Android dashboard, static asset mount, tests.
- PENDING ON DEVICE: run the clone/import script and confirm manifest count/checksums.
- PENDING: inspect APK signatures, permissions, package IDs, licenses and runtime compatibility before any manual install.
- PENDING: publish a production Web/PWA deployment and create/rebuild a signed Android APK/AAB.
