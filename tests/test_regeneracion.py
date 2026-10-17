"""Regeneración de las seis programaciones de referencia (criterio de cierre de F2).

Cada programación se importa de su .docx de la bóveda, se genera de nuevo con la plantilla y el catálogo y se compara
apartado a apartado (contenido.comparar: las diferencias de forma no cuentan). Las diferencias que quedan tienen que ser
exactamente las esperadas por decisión de CarlosFB, cada una con su motivo. Las programaciones se leen en local y no se copian: aquí
solo hay posiciones (apartado, tipo de cambio, columnas) y el principio del texto generado, que sale de la plantilla o
del catálogo; las filas de unidades se cuentan sin su texto.

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

# Diferencias esperadas por decisión de CarlosFB (2026-10-17, ADR-018). Las de forma (punto 8) siguen la plantilla de
# PIICT y el texto oficial: las referencias que no lo hacen se alinean al regenerar.
DEC95 = "Decisión 4: el Decreto 95/2026 se cita en 1.2"
ECP = "Decisión 2: los ECP con la denominación del RD 532/2025"
NOMBRE = "Decisión 3: en la portada, el nombre del módulo del Decreto 95/2026"
RESOLUCION = "Decisión 8: el título oficial de la resolución de instrucciones del curso (DOGV)"
FE_PRIMERO = "Decisión 8: la redacción y el orden de la plantilla en los periodos de empresa"
FILA_CENTRO = "Decisión 8: la fila de horas de centro de la tabla 4, como PIICT (sin los RA)"
ANEXO_V = "Decisión 8: el párrafo del anexo V B), con la redacción común"
CABECERA = "Decisión 8: la cabecera de la tabla 4 cita el real decreto, como PIICT"

COMUNES = {("1.2", "cambia", "RESOLUCIÓN de 16 de j", ()): RESOLUCION, ("1.2", "sobra", "Decreto 95/2026, de 1", ()): DEC95}
SEA = {("2", "cambia", "0518", ()): ECP, ("2", "cambia", "0602", ()): ECP}
FE = {("9.1", "cambia", "Alumnos que realicen 7h/día", ()): FE_PRIMERO,
      ("9.1", "cambia", "Alumnos que realicen 8h/día", ()): FE_PRIMERO}
ESPERADAS = {
    "0517": {**COMUNES, **SEA},
    "0524": {**COMUNES, **SEA, **FE, ("4", "cambia", "HORAS CENTRO", ()): FILA_CENTRO},
    "0525": {**COMUNES, **FE, ("2", "cambia", "En consecuencia, para", ()): ANEXO_V,
             ("4", "cambia", "UNIDAD DIDÁCTICA", ("ra",)): CABECERA},
    "0526": {**COMUNES, **SEA, ("portada", "cambia", "Módulo profesional:", ()): NOMBRE},
    "0962": {**COMUNES, **FE, ("2", "cambia", "En consecuencia, para", ()): ANEXO_V,
             ("4", "cambia", "UNIDAD DIDÁCTICA", ("ra",)): CABECERA},
    "0963": {**COMUNES, **FE, ("4", "cambia", "HORAS CENTRO", ()): FILA_CENTRO},
}
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
    esperado = Counter({k: 1 for k in ESPERADAS[codigo]})
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


def test_reparto_de_piict_regla_y_ajuste_del_profesor(regeneradas):
    """Decisión 7: la regla da 7 / 9 / 12 en los RA 3, 4 y 6; la referencia lleva 8 / 10 / 10, que se conserva como
    ajuste del profesor (centro_ajustado)."""
    _ruta, prog, _docx = regeneradas["0517"]
    prop = calculos.propuesta_centro(prog, [1, 2, 3, 4, 5, 6])
    assert (prop[3], prop[4], prop[6]) == (7, 9, 12)
    assert prog["centro_ajustado"] == {"3": 8, "4": 10, "6": 10}


@pytest.mark.parametrize("codigo", regenerar.CODIGOS)
def test_la_importacion_de_la_regenerada_da_los_mismos_datos(regeneradas, codigo):
    """Los datos que lleva dentro la regenerada son los importados de la referencia."""
    _ruta, prog, docx = regeneradas[codigo]
    assert importar_docx.importar(docx, Catalogo(), _ruta.name) == prog
