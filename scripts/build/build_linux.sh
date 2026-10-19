#!/bin/bash
# Compila la app en Linux (x86_64) y la empaqueta en un tar.gz portable. Copia del de Partes de salida.
# Solo lo ejecuta la CI (compilar.yml): no se compila en local.
#   PY=<python>     intérprete con las dependencias (por defecto, python3 del sistema)
# El tar.gz lleva la app, un lanzador, el icono y el script que crea el acceso directo del menú. La carpeta dist/ se
# deja: la CI comprueba el paquete y arranca la app desde ella.
set -euo pipefail
cd "$(dirname "$0")/../.."

APP_NAME="Programaciones"
PY="${PY:-$(command -v python3)}"
VERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)
# Nombre fijo del instalador: lo usa el actualizador de la app (empaquetado.md).
ARCH="x86_64"
SALIDA="Programaciones-${VERSION}-Linux-${ARCH}.tar.gz"
echo "== $APP_NAME $VERSION → $SALIDA"
[ "$(uname -m)" = "$ARCH" ] || { echo "La máquina es $(uname -m) y el paquete es para $ARCH"; exit 1; }

rm -rf build dist
"$PY" -m PyInstaller Programaciones.spec --clean --noconfirm
APP_PATH="dist/${APP_NAME}"
[ -d "$APP_PATH" ] || { echo "No se generó $APP_PATH"; exit 1; }
[ -x "$APP_PATH/$APP_NAME" ] || { echo "No se generó el ejecutable $APP_PATH/$APP_NAME"; exit 1; }

# El icono lo lleva el acceso directo del menú, no el ejecutable.
cp imagenes/icono.png "$APP_PATH/icono.png"

cat > "$APP_PATH/${APP_NAME}.sh" <<'SH'
#!/bin/sh
# Lanzador de Programaciones en Linux: arranca la app desde la carpeta donde está.
CARPETA="$(cd "$(dirname "$0")" && pwd)"
chmod +x "$CARPETA/Programaciones" 2>/dev/null || true
exec "$CARPETA/Programaciones" "$@"
SH
chmod +x "$APP_PATH/${APP_NAME}.sh"

cat > "$APP_PATH/instalar.sh" <<'SH'
#!/bin/sh
# Acceso directo de Programaciones en el menú de aplicaciones (XDG) y permiso de ejecución.
CARPETA="$(cd "$(dirname "$0")" && pwd)"
DESTINO="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$DESTINO"
cat > "$DESTINO/programaciones.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Programaciones
Comment=Programaciones didácticas de los módulos de FP de EPLA
Exec=$CARPETA/Programaciones.sh
Icon=$CARPETA/icono.png
Terminal=false
Categories=Office;Education;
EOF
chmod +x "$CARPETA/Programaciones" "$CARPETA/Programaciones.sh" 2>/dev/null || true
echo "Acceso directo creado: $DESTINO/programaciones.desktop"
echo "Para actualizar, extrae el tar.gz nuevo encima de esta carpeta."
SH
chmod +x "$APP_PATH/instalar.sh"

cat > "$APP_PATH/LEEME.txt" <<'TXT'
Programaciones para Linux (carpeta portable)

1. Ejecuta «Programaciones.sh» (o el archivo «Programaciones») para abrir la app.
2. Si quieres que aparezca en el menú de aplicaciones, ejecuta «instalar.sh» una vez.
3. Para actualizar, descarga el tar.gz nuevo y extráelo encima de esta carpeta.

Los ajustes y las programaciones se guardan en ~/.local/share/Programaciones.
TXT

tar -czf "$SALIDA" -C dist "$APP_NAME"
echo "Creado: $SALIDA ($(du -h "$SALIDA" | cut -f1))"
