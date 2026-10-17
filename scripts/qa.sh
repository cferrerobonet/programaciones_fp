#!/bin/bash
# Comprobaciones con la salida completa en /tmp/programaciones-qa-<tarea>.log y solo el resumen en pantalla (copia del
# de Partes de salida): un fallo se lee con grep en el log, nunca relanzando la suite entera.
#   scripts/qa.sh lint | test | rapido | ui | todo
set -uo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-$HOME/.venvs/programaciones/bin/python}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
tarea="${1:-todo}"
log="/tmp/programaciones-qa-${tarea}.log"

case "$tarea" in
    lint) "$PY" -m ruff check scripts src tests >"$log" 2>&1 ;;
    test) "$PY" -m pytest >"$log" 2>&1 ;;
    rapido) "$PY" -m pytest -m "not ui" >"$log" 2>&1 ;;
    ui) "$PY" -m pytest -m ui >"$log" 2>&1 ;;
    todo) { "$PY" -m ruff check scripts src tests && "$PY" scripts/catalogo.py comprobar \
            && "$PY" scripts/plantilla.py comprobar && "$PY" -m pytest; } >"$log" 2>&1 ;;
    *) echo "Uso: scripts/qa.sh lint|test|rapido|ui|todo"; exit 64 ;;
esac
codigo=$?
tail -n 6 "$log"
[ $codigo -eq 0 ] && echo "QA $tarea: OK (log: $log)" || echo "QA $tarea: FALLA ($codigo) — grep -n -B2 -A15 FAILED $log"
exit $codigo
