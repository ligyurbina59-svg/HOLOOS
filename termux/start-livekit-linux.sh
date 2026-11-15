#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
command -v docker >/dev/null || { echo "Docker no está instalado." >&2; exit 1; }
docker compose -f docker-compose.mn24-live.yml up -d
docker compose -f docker-compose.mn24-live.yml ps
