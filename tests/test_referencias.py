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

# Criterios en los que la programación corrige una errata del BOE y no copia el texto literal (comprobado en el PDF
# del BOE el 2026-10-17). El catálogo guarda el texto literal; la decisión es de CarlosFB (docs/PENDIENTE.md).
# Solo la posición (módulo, RA, criterio): los textos no se copian aquí.
CORREGIDOS_EN_LA_PROGRAMACION = {
    ("0517", 1, "a"),   # BOE: «de acuerdo a la normativa»
    ("0517", 1, "c"),   # BOE: «(ITC)» por «(ICT)»
    ("0517", 4, "d"),   # BOE: «en las medidas, cumplen»
    ("0524", 1, "a"),   # BOE: «las distintos tipos»
}


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
def test_criterios_identicos_salvo_erratas_corregidas(codigo):
    dif = catalogo.comparar(programacion(codigo))
    distintos = {(d["codigo"], d["ra"], d["letra"]) for d in dif if d["tipo"] == "criterio"}
    esperados = {x for x in CORREGIDOS_EN_LA_PROGRAMACION if x[0] == codigo}
    assert distintos == esperados, [catalogo.describir(d) for d in dif]
