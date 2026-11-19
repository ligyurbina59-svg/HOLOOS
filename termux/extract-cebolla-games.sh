#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/imports/Cebolla"
TARGET="$ROOT/imports/Cebolla-games"
if [ ! -d "$SOURCE" ]; then echo "No existe imports/Cebolla. Ejecuta primero bash termux/import-cebolla.sh" >&2; exit 1; fi
mkdir -p "$TARGET"
python - "$SOURCE" "$TARGET" <<'PY'
import pathlib, stat, sys, zipfile, shutil
source, target = map(pathlib.Path, sys.argv[1:])
archives = {
 "runic-arena": "MN24_RunicArena_v1.0.zip",
 "skybolt": "MN24_SkyBolt_v1.0.zip",
 "stormrunner-thunder": "STORMRUNER_THUNDER_OF_THE_NORTH_MVP_v0.1.zip",
}
MAX_FILES, MAX_BYTES, MAX_RATIO = 1000, 100*1024*1024, 200
for slug, filename in archives.items():
    archive = source / filename
    if not archive.is_file():
        print(f"PENDIENTE: {filename} no está en imports/Cebolla")
        continue
    dest = target / slug
    if dest.exists():
        print(f"OMITIDO: {dest} ya existe; no se sobrescribe")
        continue
    stage = target / (".stage-" + slug)
    if stage.exists(): shutil.rmtree(stage)
    stage.mkdir()
    total = 0
    try:
        with zipfile.ZipFile(archive) as z:
            infos = z.infolist()
            if len(infos) > MAX_FILES: raise ValueError("demasiadas entradas")
            for info in infos:
                p = pathlib.PurePosixPath(info.filename)
                mode = info.external_attr >> 16
                if p.is_absolute() or ".." in p.parts or not p.parts:
                    raise ValueError(f"ruta insegura: {info.filename}")
                if stat.S_ISLNK(mode):
                    raise ValueError(f"enlace simbólico rechazado: {info.filename}")
                total += info.file_size
                if total > MAX_BYTES: raise ValueError("límite de 100 MiB excedido")
                if info.file_size and info.compress_size == 0:
                    raise ValueError("ratio ZIP inválido")
                if info.compress_size and info.file_size / info.compress_size > MAX_RATIO:
                    raise ValueError("ratio de compresión sospechoso")
                out = stage.joinpath(*p.parts)
                resolved = out.resolve()
                if stage.resolve() not in resolved.parents and resolved != stage.resolve():
                    raise ValueError(f"salida fuera del destino: {info.filename}")
                if info.is_dir():
                    out.mkdir(parents=True, exist_ok=True)
                else:
                    out.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(info) as src, out.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
        (stage / ".mn24-extraction-review.txt").write_text(
            "Extraído como datos no confiables. Inspeccionar HTML, JavaScript, licencias y dependencias antes de publicar o ejecutar.\n",
            encoding="utf-8")
        stage.rename(dest)
        print(f"EXTRAÍDO: {filename} -> {dest} ({len(infos)} entradas, {total} bytes)")
    except Exception as exc:
        shutil.rmtree(stage, ignore_errors=True)
        print(f"RECHAZADO: {filename}: {exc}")
        raise SystemExit(2)
print("Extracción finalizada. Los paquetes aún requieren inspección manual.")
PY
