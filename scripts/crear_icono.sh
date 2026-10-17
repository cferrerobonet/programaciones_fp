#!/bin/bash
# Crea los iconos de la app a partir de imagenes/icono.png (1024 × 1024, con transparencia):
#   imagenes/icono.ico   Windows: 16, 24, 32, 48, 64, 128 y 256 px (Pillow). Va en el repositorio.
#   imagenes/icono.icns  macOS (sips e iconutil, solo en macOS). No se versiona: lo rehace la compilación.
# Como scripts/build/crear_icono.sh de Partes de salida.
set -e
cd "$(dirname "$0")/.."
PY="${PY:-$HOME/.venvs/programaciones/bin/python}"
[ -f imagenes/icono.png ] || { echo "Falta imagenes/icono.png"; exit 1; }

"$PY" -I - <<'PY'
from PIL import Image
im = Image.open("imagenes/icono.png").convert("RGBA")
im.save("imagenes/icono.ico", sizes=[(t, t) for t in (16, 24, 32, 48, 64, 128, 256)])
PY
echo "Icono creado: imagenes/icono.ico"

if command -v iconutil >/dev/null 2>&1; then
    SET="$(mktemp -d)/icono.iconset"
    mkdir -p "$SET"
    for t in 16 32 128 256 512; do
        sips -z $t $t imagenes/icono.png --out "$SET/icon_${t}x${t}.png" >/dev/null
        d=$((t * 2))
        sips -z $d $d imagenes/icono.png --out "$SET/icon_${t}x${t}@2x.png" >/dev/null
    done
    iconutil -c icns "$SET" -o imagenes/icono.icns
    rm -rf "$(dirname "$SET")"
    echo "Icono creado: imagenes/icono.icns"
fi
