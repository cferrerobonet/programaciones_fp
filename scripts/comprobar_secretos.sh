#!/usr/bin/env bash
# El repositorio es público: ningún dato del servidor de correo (servidor, puerto,
# buzón, usuario) ni contraseñas entra en él (ADR-016). Se usa en dos sitios:
#   .githooks/pre-commit  → --preparado (lo que se va a confirmar)
#   .github/workflows/secretos.yml → --todo (todo el árbol, en cada push)
# Los patrones se escriben con [.] y [_] para que este archivo no se detecte a sí mismo.
set -uo pipefail

PATRONES='smtp[.][a-z0-9-]+[.][a-z]{2,}'                                    # servidor smtp.dominio.tld
PATRONES+='|ionos[.](es|com|de|fr|co[.]uk)|1and1'                          # dominios del alojamiento
PATRONES+='|no[_]contestar@|aplicaciones[.]epla[.]es'                       # buzón compartido de las apps
PATRONES+='|(puerto|port)[_a-z]*[ ]*(:[ ]*[a-z]+[ ]*)?[:=][ ]*["'"'"']?(25|465|587|2525)\b'    # puerto de correo asignado
PATRONES+='|[a-z0-9.-]+:(465|587|2525)\b'                                   # servidor:puerto
PATRONES+='|(smtp|correo|mail)[_a-z]*(usuario|user|servidor|server|host|remitente)[_a-z]*[ ]*(:[ ]*[a-z]+[ ]*)?=[ ]*["'"'"'][^"'"'"']+["'"'"']'  # valor por defecto
PATRONES+='|(password|passwd|pwd|contrasena|contraseña)[_a-z]*[ ]*[:=][ ]*["'"'"'][^"'"'"']{4,}["'"'"']'  # contraseña escrita

modo="${1:---todo}"
fallo=0
revisar() {  # $1 = ruta mostrada; contenido por stdin
    local salida
    salida=$(grep -n -I -i -E "$PATRONES" 2>/dev/null) || return 0
    echo "secretos: $1 contiene datos del servidor de correo o una contraseña:" >&2
    echo "$salida" | sed 's/^/    /' | cut -c1-160 >&2
    fallo=1
}

case "$modo" in
    --preparado)
        while IFS= read -r -d '' f; do
            [ "$f" = "scripts/comprobar_secretos.sh" ] && continue
            revisar "$f" < <(git show ":$f")   # sin tubería: en una subcapa se perdería «fallo»
        done < <(git diff --cached --name-only --diff-filter=ACM -z)
        ;;
    --todo)
        while IFS= read -r -d '' f; do
            [ "$f" = "scripts/comprobar_secretos.sh" ] && continue
            revisar "$f" < "$f"
        done < <(git ls-files -z)
        ;;
    *) echo "uso: $0 [--preparado|--todo]" >&2; exit 2 ;;
esac

if [ "$fallo" -ne 0 ]; then
    echo "secretos: los datos del correo van en Ajustes de cada equipo y la contraseña en el llavero; nunca en el repositorio (docs/SEGURIDAD_Y_DATOS.md)." >&2
    exit 1
fi
exit 0
