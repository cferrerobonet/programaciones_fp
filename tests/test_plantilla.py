"""La plantilla con marcas del repositorio: sin datos personales, con los títulos de PIICT y todas sus marcas."""
import re

import yaml

import plantilla
from programaciones import contenido, documento
from programaciones.ooxml import texto

TITULOS = [
    "1.- DATOS IDENTIFICATIVOS: MARCO NORMATIVO Y CONTEXTUALIZACIÓN DEL MÓDULO.", "1.1. Normativa básica estatal",
    "1.2. Normativa autonómica (Comunidad Valenciana)",
    "2.- RELACIÓN ENTRE ESTÁNDARES DE COMPETENCIA Y LOS MÓDULOS DEL CICLO FORMATIVO",
    "2.1.- Competencias profesionales, personales y sociales", "2.2.- Módulos optativos ofertados",
    "3.- CONTRIBUCIÓN DE LOS RA A LAS COMPETENCIAS GENERALES",
    "4.- ESQUEMA GENERAL Y SECUENCIACIÓN DE LAS UNIDADES DE PROGRAMACIÓN.", "4.1. Ponderación de cada RA.",
    "5.- METODOLOGÍA DEL PROCESO DE ENSEÑANZA-APRENDIZAJE", "5.1.- Principios generales y pedagógicos",
    "6.- RECURSOS", "7. USO DE ESPACIOS Y EQUIPAMIENTOS", "8.- MEDIDAS DE ATENCIÓN A LA DIVERSIDAD",
    "9.- EVALUACIÓN DEL APRENDIZAJE", "9.1.- Períodos Formación en Empresa",
    "10. ACTIVIDADES COMPLEMENTARIAS Y EXTRAESCOLARES", "11. CRITERIOS Y PROCEDIMIENTOS PARA LA EVALUACIÓN",
    "11.1.- Instrumentos y procedimiento de evaluación", "11.2.- Elementos de evaluación",
    "12.- ACTIVIDADES DE RECUPERACIÓN",
]


def test_plantilla_limpia():
    assert plantilla.comprobar() == []


def test_sin_partes_personales_ni_macros():
    pq = documento.cargar_plantilla()
    assert not [n for n in pq.partes if re.search(r"comments|people|customXml|custom\.xml|vbaProject|webSettings", n)]
    core = pq.partes["docProps/core.xml"].decode("utf-8")
    assert "<dc:creator>Programaciones</dc:creator>" in core


def test_titulos_literales_de_la_plantilla():
    assert contenido.titulos(documento.cargar_plantilla().a_bytes()) == TITULOS


def test_metadatos():
    meta = yaml.safe_load((documento.PLANTILLA / "plantilla.yaml").read_text(encoding="utf-8"))
    assert meta["version"] == "2026-10-06" and meta["idiomas"] == ["es"] and meta["vinetas"]


def test_todas_las_marcas_tienen_valor(prog, cat, curso):
    """El documento rellena cada marca de la plantilla (si faltara una, generar lanzaría un error)."""
    pq = documento.cargar_plantilla()
    marcas = {m.group(2) for n in pq.partes if n.startswith("word/") and n.endswith(".xml")
              for m in documento.RE_MARCA.finditer(texto(pq.xml(n)))}
    assert {"rd_cita", "contribucion", "competencia_general", "correo_pie"} <= marcas
    documento.generar(prog, cat, curso)
