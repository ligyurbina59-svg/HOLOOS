#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ ! -f .env.mn24-live ]; then
  echo "Falta .env.mn24-live. Ejecuta: bash termux/setup-mn24-live.sh" >&2
  exit 1
fi
set -a
. ./.env.mn24-live
set +a
if [ "${MN24_APP_JWT_SECRET:-}" = "replace-with-random-secret-at-least-32-characters" ] || [ "${#MN24_APP_JWT_SECRET}" -lt 32 ]; then
  echo "Configura MN24_APP_JWT_SECRET (mínimo 32 caracteres) antes de iniciar." >&2
  exit 1
fi
python -m uvicorn android24creator_backend.main:app --host 0.0.0.0 --port 8000
