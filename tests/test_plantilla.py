"""La plantilla con marcas del repositorio: sin datos personales, con los títulos de PIICT y todas sus marcas."""
import re

import yaml

import plantilla
from programaciones import contenido, documento
from programaciones.ooxml import texto

#: Los títulos de PIICT con el texto del diseño (ADR-044): sin número escrito (lo pone la numeración de Word)
TITULOS = [
    ("1", "Datos identificativos: marco normativo y contextualización del módulo"),
    ("1.1", "Normativa básica estatal"), ("1.2", "Normativa autonómica (Comunidad Valenciana)"),
    ("2", "Relación entre estándares de competencia y los módulos del ciclo formativo"),
    ("2.1", "Competencias profesionales, personales y sociales"), ("2.2", "Módulos optativos ofertados"),
    ("3", "Contribución de los RA a las competencias generales"),
    ("4", "Esquema general y secuenciación de las unidades de programación"), ("4.1", "Ponderación de cada RA"),
    ("5", "Metodología del proceso de enseñanza-aprendizaje"), ("5.1", "Principios generales y pedagógicos"),
    ("6", "Recursos"), ("7", "Uso de espacios y equipamientos"), ("8", "Medidas de atención a la diversidad"),
    ("9", "Evaluación del aprendizaje"), ("9.1", "Períodos Formación en Empresa"),
    ("10", "Actividades complementarias y extraescolares"), ("11", "Criterios y procedimientos para la evaluación"),
    ("11.1", "Instrumentos y procedimiento de evaluación"), ("11.2", "Elementos de evaluación"),
    ("12", "Actividades de recuperación"),
]


def test_plantilla_limpia():
    assert plantilla.comprobar() == []


def test_sin_partes_personales_ni_macros():
    pq = documento.cargar_plantilla()
    assert not [n for n in pq.partes if re.search(r"comments|people|customXml|custom\.xml|vbaProject|webSettings", n)]
    core = pq.partes["docProps/core.xml"].decode("utf-8")
    assert "<dc:creator>Programaciones</dc:creator>" in core


def test_titulos_de_la_plantilla_numerados_por_word():
    """El número de cada título lo pone la numeración de su estilo; la app lo sabe contándolos."""
    plantilla_ = documento.cargar_plantilla().a_bytes()
    assert contenido.numerados_por_word(plantilla_)
    assert contenido.titulos_numerados(plantilla_) == TITULOS


def test_metadatos():
    meta = yaml.safe_load((documento.PLANTILLA / "plantilla.yaml").read_text(encoding="utf-8"))
    assert meta["version"] == "2026-11-07" and meta["idiomas"] == ["es"] and meta["vinetas"]


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


def test_diseno_repetible_y_con_barlow_incrustada():
    """ADR-044: volver a aplicar el diseño a las dos plantillas no cambia nada, y su comprobación pasa (las siete
    fuentes Barlow se recuperan con su clave y ningún texto usa un tipo del sistema)."""
    import diseno
    from programaciones import ooxml
    for ambito in (False, True):
        antes = documento.cargar_plantilla(ambito=ambito)
        despues = diseno.aplicar(ooxml.Paquete.desde_docx(antes.a_bytes()), plantilla.NOTA_EDUCAMOS, ambito=ambito)
        assert diseno.comprobar(despues) == []
        a, b = ooxml.Paquete.desde_docx(antes.a_bytes()), ooxml.Paquete.desde_docx(despues.a_bytes())
        assert {n: a.partes[n] for n in a.partes} == {n: b.partes[n] for n in b.partes}


def test_la_comprobacion_detecta_un_tipo_del_sistema():
    from lxml import etree

    import diseno
    from programaciones import ooxml
    from programaciones.ooxml import W
    pq = documento.cargar_plantilla()
    r = next(pq.xml("word/document.xml").iter(W + "r"))
    rpr = r.find(W + "rPr")
    if rpr is None:
        rpr = etree.Element(W + "rPr")
        r.insert(0, rpr)
    ooxml.hijo(rpr, "rFonts", ooxml.ORDEN_RPR, ascii="Calibri")
    assert any("Calibri" in e for e in diseno.comprobar(pq))
