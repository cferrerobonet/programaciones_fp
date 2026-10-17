#!/bin/bash
# Ningún flujo ni script aprueba ni fusiona PR (CarlosFB, 2026-10-17, ADR-028): todo lo que detecta el vigía lo revisa y
# lo fusiona CarlosFB. Busca en .github/ y scripts/ (o en las carpetas que se le pasen) fusiones, aprobaciones y
# auto-merge por gh, por la API REST o GraphQL y por acciones de terceros. Lo usan comprobar.yml y tests/test_proyecto.py.
# Los patrones se arman por trozos para que este archivo no se encuentre a sí mismo.
set -uo pipefail
cd "$(dirname "$0")/.."
[ $# -gt 0 ] && carpetas=("$@") || carpetas=(.github scripts)
g="g""h"; p="p""r"
s="[[:space:]\"',]+"                                                     # separadores, también de una lista
patron="$g$s$p$s(merge|review)"                                            # gh pr merge · gh pr review --approve
patron+="|--appro""ve|\bAPPRO""VE\b|event[\"':= ]+APPRO""VE"              # aprobar por cualquier vía
patron+="|enable(Pull[A-Za-z]*)?Auto[-_ ]?Mer""ge|auto[-_]?mer""ge"         # auto-merge (GraphQL, acciones)
patron+="|pulls/[^[:space:]]*/mer""ge|mergePull""Request|pulls\.mer""ge"   # REST, GraphQL, octokit
patron+="|auto-appro""ve"                                                  # acciones de aprobación
hallado=$(grep -rnEi --exclude="$(basename "$0")" -- "$patron" "${carpetas[@]}" 2>/dev/null)
if [ -n "$hallado" ]; then
    echo "$hallado"
    echo "Sin fusión automática: un flujo o un script aprueba o fusiona PR. Lo del vigía lo fusiona CarlosFB (ADR-028)."
    exit 1
fi
echo "Sin fusión automática: ningún flujo ni script aprueba ni fusiona PR"
