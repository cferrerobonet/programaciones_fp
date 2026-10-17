"""Regeneración de las seis programaciones de referencia (criterio de cierre de F2).

Cada programación se importa de su .docx de la bóveda, se genera de nuevo con la plantilla y el catálogo y se compara
apartado a apartado (contenido.comparar: las diferencias de forma no cuentan). Las diferencias que quedan tienen que ser
exactamente las aceptadas de abajo, cada una con su motivo. Las programaciones se leen en local y no se copian: aquí
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

DEC95 = "Decisión 4 de CarlosFB (2026-10-17): el Decreto 95/2026 se cita en 1.2"
ECP = "Decisión 2: los ECP con la denominación del RD 532/2025"
NOMBRE = "Decisión 3: en la portada, el nombre del módulo del Decreto 95/2026"
RESOLUCION = "Título oficial de la resolución de instrucciones del curso (catálogo, PDF del DOGV)"
FE_PRIMERO = "Formación en empresa de 1.º: la redacción y el orden de la plantilla (pendiente de CarlosFB)"
FILA_CENTRO = "Fila de horas de centro de la tabla 4: la plantilla no lista los RA (pendiente de CarlosFB)"
CABECERA = "Cabecera de la tabla 4: cita el real decreto, como la plantilla"
ANEXO_V = "Apartado 2: redacción común sobre el anexo V B) (pendiente de CarlosFB)"
TABLA_PROYECTO = "Tabla 4 del Proyecto: las cabeceras de la plantilla"
PESOS = "Pesos calculados (horas del elemento / horas del módulo); la referencia los pone a mano (pendiente de CarlosFB)"
PESO_PRACTICA = "Peso por práctica en la referencia; la app da el del elemento (pendiente de CarlosFB)"
COLUMNA = "Columna «% del curso» propia de la referencia: la plantilla no la tiene"

COMUNES = {("1.2", "cambia", "RESOLUCIÓN de 16 de j", ()): RESOLUCION, ("1.2", "sobra", "Decreto 95/2026, de 1", ()): DEC95}
SEA = {("2", "cambia", "0518", ()): ECP, ("2", "cambia", "0602", ()): ECP}
FE = {("9.1", "cambia", "Alumnos que realicen 7h/día", ()): FE_PRIMERO,
      ("9.1", "cambia", "Alumnos que realicen 8h/día", ()): FE_PRIMERO}
ACEPTADAS = {
    "0517": {**COMUNES, **SEA},
    "0524": {**COMUNES, **SEA, **FE, ("4", "cambia", "HORAS CENTRO", ()): FILA_CENTRO},
    "0525": {**COMUNES, **FE, ("2", "cambia", "En consecuencia, para", ()): ANEXO_V,
             ("4", "cambia", "UNIDAD DIDÁCTICA", ("ra",)): CABECERA},
    "0526": {**COMUNES, **SEA, ("portada", "cambia", "Módulo profesional:", ()): NOMBRE,
             ("4", "cambia", "UNIDAD DIDÁCTICA", ("elemento", "horas", "peso", "unidad")): TABLA_PROYECTO},
    "0962": {**COMUNES, **FE, ("2", "cambia", "En consecuencia, para", ()): ANEXO_V,
             ("4", "cambia", "UNIDAD DIDÁCTICA", ("ra",)): CABECERA,
             ("4", "cambia", "fila de unidad", ("peso",)): PESOS,
             ("4.1", "cambia", "Resultado de aprendizaje", ("pct",)): COLUMNA,
             ("4.1", "cambia", "fila de RA", ("pct",)): COLUMNA, ("4.1", "cambia", "TOTAL", ("pct",)): COLUMNA},
    "0963": {**COMUNES, **FE, ("4", "cambia", "HORAS CENTRO", ()): FILA_CENTRO,
             ("4", "cambia", "fila de unidad", ("peso",)): PESO_PRACTICA},
}
CUANTAS = {("0962", ("4", "cambia", "fila de unidad", ("peso",))): 23, ("0962", ("4.1", "cambia", "fila de RA", ("pct",))): 7,
           ("0963", ("4", "cambia", "fila de unidad", ("peso",))): 5}
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
def test_sin_diferencias_de_contenido_salvo_las_aceptadas(regeneradas, codigo):
    ruta, _prog, docx = regeneradas[codigo]
    difs, _forma = contenido.comparar(ruta.read_bytes(), docx)
    hay = Counter(clave(d) for d in difs)
    esperado = Counter({k: CUANTAS.get((codigo, k), 1) for k in ACEPTADAS[codigo]})
    sobran = [f"{k}: {[str(d) for d in difs if clave(d) == k][:1]}" for k in hay - esperado]
    faltan = [f"{k} ({ACEPTADAS[codigo][k]})" for k in esperado - hay]
    assert not sobran and not faltan, f"Diferencias nuevas: {sobran} · aceptadas que ya no están: {faltan}"


@pytest.mark.parametrize("codigo", regenerar.CODIGOS)
def test_las_regeneradas_cumplen_las_comprobaciones_de_la_skill(regeneradas, codigo):
    _ruta, _prog, docx = regeneradas[codigo]
    v = contenido.verificar(docx, contenido.titulos(documento.cargar_plantilla().a_bytes()))
    assert v["titulos_iguales"] and v["campo_toc"] == 1 and v["update_fields"]
    assert v["citas_sin_enlace"] == [] and not v["termino_vetado"]


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
