#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="https://github.com/ligyurbina59-svg/Cebolla.git"
BRANCH="${CEBOLLA_BRANCH:-main}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMPORTS="$ROOT/imports"
TARGET="$IMPORTS/Cebolla"
WORK="$IMPORTS/.Cebolla-source-$$"
STAGE="$IMPORTS/.Cebolla-stage-$$"

if ! command -v git >/dev/null 2>&1; then
  echo "Git no está instalado. Ejecuta: pkg install git" >&2
  exit 1
fi
if [ -e "$TARGET" ]; then
  echo "Destino existente: $TARGET" >&2
  echo "No se sobrescribirá. Respáldalo o renómbralo manualmente antes de reintentar." >&2
  exit 2
fi

mkdir -p "$IMPORTS"
cleanup() { rm -rf "$WORK" "$STAGE"; }
trap cleanup EXIT INT TERM

echo "Clonando $REPO (rama $BRANCH)…"
git clone --depth 1 --branch "$BRANCH" "$REPO" "$WORK"
SOURCE_COMMIT="$(git -C "$WORK" rev-parse HEAD)"
mkdir -p "$STAGE"
cp -a "$WORK/." "$STAGE/"
rm -rf "$STAGE/.git"

echo "Generando inventario SHA-256…"
python - "$STAGE" "$SOURCE_COMMIT" "$BRANCH" <<'PY'
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

root = pathlib.Path(sys.argv[1]).resolve()
commit, branch = sys.argv[2], sys.argv[3]
files = []
for path in sorted(root.rglob("*")):
    if not path.is_file() or path.name == ".mn24-import-manifest.json":
        continue
    rel = path.relative_to(root).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    files.append({"path": rel, "size": path.stat().st_size, "sha256": digest})
manifest = {
    "schema_version": 1,
    "repository": "https://github.com/ligyurbina59-svg/Cebolla",
    "source_branch": branch,
    "source_commit": commit,
    "imported_at_utc": datetime.now(timezone.utc).isoformat(),
    "file_count": len(files),
    "total_bytes": sum(item["size"] for item in files),
    "files": files,
    "execution_policy": "assets imported as data; APKs, archives and scripts are not executed or installed",
}
(root / ".mn24-import-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"Archivos importados: {len(files)}")
print(f"Bytes importados: {manifest['total_bytes']}")
print(f"Commit fuente: {commit}")
PY

mv "$STAGE" "$TARGET"
rm -rf "$WORK"
trap - EXIT INT TERM
echo "Importación completada: $TARGET"
echo "Abre: http://127.0.0.1:8000/app/cebolla"
