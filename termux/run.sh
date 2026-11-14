#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  echo "Missing .venv. Run: bash termux/setup.sh" >&2
  exit 1
fi
. .venv/bin/activate
export GITHUB_REPOSITORY_ALLOWLIST="${GITHUB_REPOSITORY_ALLOWLIST:-ligyurbina59-svg/HOLOOS,ligyurbina59-svg/Cebolla}"
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8000}"
exec uvicorn android24creator_backend.main:app --host "$HOST" --port "$PORT"
