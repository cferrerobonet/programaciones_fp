"""Regeneración de las seis programaciones de referencia (criterio de cierre de F2).

Cada programación se importa de su .docx de la bóveda, se genera de nuevo con la plantilla y el catálogo y se compara
apartado a apartado (contenido.comparar: las diferencias de forma no cuentan). Desde el 2026-10-19 las referencias son
las exportadas con la app (llevan sus datos dentro): regenerarlas no puede dar ninguna diferencia. Las programaciones se leen en local y no se copian: aquí
solo hay posiciones (apartado, tipo de cambio, columnas) y el principio del texto generado, que sale de la plantilla o
del catálogo; las filas de unidades se cuentan sin su texto.

Se compara el cuerpo. Los encabezados y pies son formato: la franja vertical del margen, que la plantilla recoloca bajo el
escudo (CarlosFB, 2026-10-17; tests/test_plantilla.py), es una diferencia de formato aceptada y no se cuenta aquí.

    PROGRAMACIONES_REFERENCIAS="…/02 EPLA/01 DOCENCIA/FP" ~/.venvs/programaciones/bin/python -m pytest -m referencias
"""
import os
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

from programaciones import calculos, contenido, documento, importar_docx
from programaciones.catalogo import Catalogo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import regenerar  # noqa: E402

pytestmark = pytest.mark.referencias
CARPETA = Path(os.environ.get("PROGRAMACIONES_REFERENCIAS", "/no-existe"))

# Desde el 2026-10-19 (CarlosFB): las referencias son las programaciones exportadas con la app, que sustituyeron en la
# bóveda a los originales del departamento el 2026-10-18. Regenerarlas tiene que dar lo mismo: ninguna diferencia
# esperada. Las de los originales (ADR-018, ADR-023, ADR-025, ADR-033) ya cumplieron su papel al cerrar F2.
# ADR-042 (CarlosFB, 2026-10-21): la nota de Educamos pegada a la 4.1 es texto fijo de la plantilla; las referencias
# exportadas con la 0.13.0 no la llevan hasta que se vuelvan a exportar.
NOTA_EDUCAMOS = ("4.1", "sobra", "Tabla de Educamos: Menú Evaluación → Competencias clave → Pestaña perfil"[:21], ())   # clave(): 21 caracteres
ESPERADAS: dict[str, dict] = {c: {NOTA_EDUCAMOS: "ADR-042: nota de Educamos de la plantilla"} for c in regenerar.CODIGOS}
FILAS_DE_PLANTILLA = ("UNIDAD DIDÁCTICA", "HORAS CENTRO", "HORAS DE EMPRESA", "TOTAL", "Resultado de aprendizaje",
                      "Módulo profesional")


def clave(d: contenido.Diferencia) -> tuple:
    """La firma de la diferencia sin texto de la referencia ni del profesor."""
    sec, cambio, inicio, cols = d.firma
    if d.clase == "fila" and sec == "4" and not inicio.startswith(FILAS_DE_PLANTILLA):
        inicio = "fila de unidad"
    elif d.clase == "fila" and sec == "4.1" and inicio.startswith("R.A."):
        inicio = "fila de RA"
    elif d.clase == "fila" and sec == "2":
        inicio = inicio[:4]
    elif sec == "9.1":
        inicio = re.match(r"Alumnos que realicen \d+h/día", inicio).group(0)
    elif d.clase == "parrafo":
        inicio = inicio[:21]
    return (sec, cambio, inicio, cols)


@pytest.fixture(scope="module")
def regeneradas():
    if not CARPETA.is_dir():
        pytest.skip("Sin PROGRAMACIONES_REFERENCIAS (carpeta 01 DOCENCIA/FP de la bóveda): solo en local")
    cat = Catalogo()
    out = {}
    for codigo in regenerar.CODIGOS:
        ruta = regenerar.referencia(CARPETA, codigo)
        prog, docx = regenerar.regenerar(ruta, cat)
        out[codigo] = (ruta, prog, docx)
    return out


@pytest.mark.parametrize("codigo", regenerar.CODIGOS)
def test_sin_diferencias_de_contenido_salvo_las_esperadas_por_decision(regeneradas, codigo):
    ruta, _prog, docx = regeneradas[codigo]
    difs, _forma = contenido.comparar(ruta.read_bytes(), docx)
    hay = Counter(clave(d) for d in difs)
    esperado = Counter({k: v[1] if isinstance(v, tuple) else 1 for k, v in ESPERADAS[codigo].items()})
    sobran = [f"{k}: {[str(d) for d in difs if clave(d) == k][:1]}" for k in hay - esperado]
    faltan = [f"{k} ({ESPERADAS[codigo][k]})" for k in esperado - hay]
    assert not sobran and not faltan, f"Diferencias nuevas: {sobran} · esperadas que ya no están: {faltan}"


@pytest.mark.parametrize("codigo", regenerar.CODIGOS)
def test_las_regeneradas_cumplen_las_comprobaciones_de_la_skill(regeneradas, codigo):
    _ruta, _prog, docx = regeneradas[codigo]
    v = contenido.verificar(docx, contenido.titulos(documento.cargar_plantilla().a_bytes()))
    assert v["titulos_iguales"] and v["campo_toc"] == 1 and v["update_fields"]
    assert v["citas_sin_enlace"] == [] and not v["termino_vetado"]


def test_pesos_a_mano_como_ajuste_del_profesor(regeneradas):
    """Decisión 9: los pesos que no salen de las horas son ajustes del profesor (0962, a mano; 0963, por práctica) y
    la columna «% del curso» de 0962 es opcional; los de las demás, calculados."""
    ajustes = {c: sum(1 for e in regeneradas[c][1]["elementos"] if e.get("peso_ajustado")) for c in regenerar.CODIGOS}
    assert ajustes["0962"] > 0 and ajustes["0963"] > 0
    assert all(ajustes[c] == 0 for c in ("0517", "0524", "0525", "0526"))
    assert regeneradas["0962"][1].get("columna_pct_curso") is True
    assert not any(e.get("texto") for e in [x.get("peso_ajustado", {}) for x in regeneradas["0962"][1]["elementos"]])
    assert any(e.get("peso_ajustado", {}).get("texto") for e in regeneradas["0963"][1]["elementos"])


def test_reparto_de_piict_regla(regeneradas):
    """Decisión 7: la regla da 7 / 9 / 12 en los RA 3, 4 y 6. El original llevaba 8 / 10 / 10 como ajuste del profesor;
    la programación exportada con la app que lo sustituyó (2026-10-18) no lleva ajuste, así que manda la regla."""
    _ruta, prog, _docx = regeneradas["0517"]
    prop = calculos.propuesta_centro(prog, [1, 2, 3, 4, 5, 6])
    assert (prop[3], prop[4], prop[6]) == (7, 9, 12)
    centro = {r: prop[r] for r in (3, 4, 6)}
    assert all(int(prog["centro_ajustado"].get(str(r), centro[r])) == centro[r] for r in centro)


@pytest.mark.parametrize("codigo", regenerar.CODIGOS)
def test_la_importacion_de_la_regenerada_da_los_mismos_datos(regeneradas, codigo):
    """Los datos que lleva dentro la regenerada son los importados de la referencia."""
    _ruta, prog, docx = regeneradas[codigo]
    assert importar_docx.importar(docx, Catalogo(), _ruta.name) == prog
