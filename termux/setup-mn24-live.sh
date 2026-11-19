#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python -m pip install --upgrade pip
python -m pip install -r requirements-mn24-live.txt
mkdir -p data
if [ ! -f .env.mn24-live ]; then
  cp .env.mn24-live.example .env.mn24-live
  echo "Creado .env.mn24-live: edita MN24_APP_JWT_SECRET y configura LIVEKIT_URL/API keys."
fi
echo "Dependencias instaladas. Para iniciar API: bash termux/run-mn24-live.sh"
