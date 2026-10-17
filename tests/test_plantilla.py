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
    assert meta["version"] == "2026-10-17" and meta["idiomas"] == ["es"] and meta["vinetas"]


def test_todas_las_marcas_tienen_valor(prog, cat, curso):
    """El documento rellena cada marca de la plantilla (si faltara una, generar lanzaría un error)."""
    pq = documento.cargar_plantilla()
    marcas = {m.group(2) for n in pq.partes if n.startswith("word/") and n.endswith(".xml")
              for m in documento.RE_MARCA.finditer(texto(pq.xml(n)))}
    assert {"rd_cita", "contribucion", "competencia_general", "correo_pie"} <= marcas
    documento.generar(prog, cat, curso)


def test_variante_de_proyecto():
    """CarlosFB, 2026-10-17 (ADR-020): la tabla 4 y los bloques de 9, 11.1 y 11.2 de 0526, para todos los proyectos."""
    pq = documento.cargar_plantilla()
    t = texto(pq.xml("word/document.xml"))
    assert t.count("{{?proyecto}}") == 5 and t.count("{{?no_proyecto}}") == 5
    assert "TAREA (Item del proyecto)" in t and "{{tareas}}" in t


def test_la_franja_vertical_empieza_bajo_el_escudo(prog, cat, curso):
    """CarlosFB, 2026-10-17: el texto vertical del margen no se monta en el escudo (5 mm de margen) ni toca el pie.
    En la plantilla y en un documento generado, medido en EMU desde las anclas del encabezado y del pie."""
    from programaciones import ooxml
    for pq in (documento.cargar_plantilla(), ooxml.Paquete.desde_docx(documento.generar(prog, cat, curso))):
        assert plantilla.solapes_franja(pq) == []
        doc = pq.xml("word/document.xml")
        franja = next(a for a in ooxml.anclas(pq.xml("word/header2.xml"), doc) if "Programación didáctica" in a["texto"])
        escudo = max(a["y1"] for a in ooxml.anclas(pq.xml("word/header2.xml"), doc) if a["imagen"])
        pie = min(a["y0"] for a in ooxml.anclas(pq.xml("word/footer2.xml"), doc, es_pie=True))
        assert franja["y0"] >= escudo + plantilla.MARGEN_FRANJA and franja["y1"] < pie


def test_la_comprobacion_detecta_la_franja_sobre_el_escudo():
    from programaciones import ooxml
    pq = documento.cargar_plantilla()
    cab = pq.xml("word/header2.xml")
    anc = next(a for a in cab.iter(ooxml.WP + "anchor") if "Programación didáctica" in ooxml.texto(a))
    off = anc.find(f"{ooxml.WP}positionV/{ooxml.WP}posOffset")
    off.text = str(int(off.text) - 500_000)   # como en la plantilla del departamento: 8,6 mm sobre el escudo
    assert plantilla.solapes_franja(pq)
