"""RA de las seis programaciones de referencia frente al catálogo (criterio de cierre de F1).

Las programaciones están en la bóveda y no entran nunca en el repositorio: la prueba recibe por variable de entorno la
carpeta `01 DOCENCIA/FP` y se salta si no está (en la CI no está).

    PROGRAMACIONES_REFERENCIAS="…/02 EPLA/01 DOCENCIA/FP" ~/.venvs/programaciones/bin/python -m pytest -m referencias
"""
import os
from pathlib import Path

import pytest

import catalogo

pytestmark = pytest.mark.referencias

CARPETA = Path(os.environ.get("PROGRAMACIONES_REFERENCIAS", "/no-existe"))
CODIGOS = ["0517", "0524", "0525", "0526", "0962", "0963"]

# Erratas del BOE que las programaciones corrigen (comprobadas en el PDF del BOE el 2026-10-17). El catálogo guarda el
# literal y la corrección (CORRECCIONES de scripts/catalogo.py), y el documento sale corregido (CarlosFB, 2026-10-17).
# Solo la posición (módulo, RA, criterio): los textos no se copian aquí.
CORREGIDOS_EN_LA_PROGRAMACION = {("0517", 1, "a"), ("0517", 1, "c"), ("0517", 4, "d"), ("0524", 1, "a")}
#: Erratas que no salen de una referencia, sino de leer el BOE (el RA4 de 0959 del RD 401/2023: «Criterios de
#: calificación:» pegado al enunciado). No están en ninguna de las seis programaciones de referencia.
CORREGIDOS_AL_LEER_EL_BOE = {("0959", 4, None)}


def programacion(codigo: str) -> Path:
    if not CARPETA.is_dir():
        pytest.skip("Sin PROGRAMACIONES_REFERENCIAS (carpeta 01 DOCENCIA/FP de la bóveda): solo en local")
    encontradas = sorted(CARPETA.glob(f"*/01 Programación/* - {codigo} - *.docx"))
    assert len(encontradas) == 1, f"{codigo}: {len(encontradas)} programaciones en {CARPETA}"
    return encontradas[0]


@pytest.mark.parametrize("codigo", CODIGOS)
def test_ra_identicos(codigo):
    dif = catalogo.comparar(programacion(codigo))
    assert [catalogo.describir(d) for d in dif if d["tipo"] != "criterio"] == []


@pytest.mark.parametrize("codigo", CODIGOS)
def test_criterios_identicos_con_las_erratas_corregidas(codigo):
    dif = catalogo.comparar(programacion(codigo))
    assert [catalogo.describir(d) for d in dif] == []


def test_las_erratas_que_corrigen_las_programaciones_estan_en_el_catalogo():
    assert {(m, n, letra) for m, n, letra in catalogo.CORRECCIONES} == \
        CORREGIDOS_EN_LA_PROGRAMACION | CORREGIDOS_AL_LEER_EL_BOE
