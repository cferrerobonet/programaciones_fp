---
name: tests
description: Ejecutar y depurar las pruebas de Programaciones — dominio (catálogo, cálculos, documento, PDF), interfaz con pytest-qt sin pantalla, comparación con las programaciones de referencia de la bóveda y comprobación del catálogo y de la plantilla. Usar cuando se pida «pasa los tests», antes de publicar, o para diagnosticar un fallo.
---

# Pruebas

Copia de la skill de Partes de salida. Reglas para escribirlas: `.claude/rules/tests.md`.

## Intérprete

`~/.venvs/programaciones/bin/python` (fuera de iCloud: dentro, iCloud duplica binarios y Qt deja de arrancar). Recrear con `make venv`.

## Comandos (la salida completa queda en `/tmp/programaciones-qa-<tarea>.log`)

| Qué | Comando |
| --- | --- |
| Lint + catálogo + plantilla + suite (lo de antes de publicar) | `scripts/qa.sh todo` |
| Solo ruff | `scripts/qa.sh lint` |
| Sin interfaz | `scripts/qa.sh rapido` |
| Solo interfaz (pytest-qt) | `scripts/qa.sh ui` |
| Un fichero | `QT_QPA_PLATFORM=offscreen ~/.venvs/programaciones/bin/python -m pytest tests/test_x.py -x` |
| Con las programaciones de referencia de la bóveda | `PROGRAMACIONES_REFERENCIAS="<…/01 DOCENCIA/FP>" … -m pytest -m referencias` (se salta si no está) |

Un fallo se lee en el log: `grep -n -B2 -A15 FAILED /tmp/programaciones-qa-todo.log`. **No relanzar la suite entera para ver un error.**

## Diagnóstico de fallos que no son del código

| Síntoma | Causa y arreglo |
| --- | --- |
| `Could not load the Qt platform plugin` | Falta `QT_QPA_PLATFORM=offscreen` (o, en Linux, las librerías `libxcb-*` de `comprobar.yml`) |
| Qt aborta al crear la aplicación | Intérprete dentro de iCloud: usar el de `~/.venvs/programaciones` |
| Pruebas del PDF o de R1 omitidas | Sin LibreOffice o sin `pdftotext` en el equipo (en la CI, sí están) |
| `timeout` no existe en macOS | `perl -e 'alarm N; exec @ARGV' <orden>` |

## Lo que la suite no prueba

La app compilada: eso lo hace `compilar.yml` (comprobación de los datos empaquetados y prueba de arranque con QtPdf en macOS y Windows). Tampoco Word: la prueba R1 es manual (`scripts/prueba_word.py`, `docs/PENDIENTE.md`).
