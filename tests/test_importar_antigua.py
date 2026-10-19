"""Importar una programación del formato antiguo: un .docx ficticio con su estructura (títulos en párrafos normales,
tablas de temporalización y de ponderación, viñetas «•» escritas a mano y horas pegadas al nombre del elemento)."""
import io
import zipfile
from xml.sax.saxutils import escape

import pytest

from programaciones import documento, exportacion, importar_antigua, importar_docx, incrustar

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NOMBRE = "Programación antigua.docx"


def anclaje(clave):
    """El párrafo de entrada de un bloque sustituible de la plantilla, con sus marcas rellenas con texto ficticio."""
    import re

    return re.sub(r"\{\{[^{}]+\}\}", "texto ficticio", importar_docx.plantilla()["sustituibles"][clave]["antes"])


def p(texto, negrita=""):
    """Párrafo normal; `negrita`, un principio del texto en negrita."""
    runs = ""
    if negrita:
        runs += f'<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{escape(negrita)}</w:t></w:r>'
        texto = texto[len(negrita):]
    if texto:
        runs += f'<w:r><w:t xml:space="preserve">{escape(texto)}</w:t></w:r>'
    return f"<w:p>{runs}</w:p>"


def celda(texto, combinada=None):
    """Celda con un párrafo por «\\n»; `combinada`: «restart» o «continue» (combinación vertical)."""
    pr = f'<w:tcPr><w:vMerge w:val="{combinada}"/></w:tcPr>' if combinada else ""
    ps = "".join(p(t) for t in texto.split("\n")) if texto else "<w:p/>"
    return f"<w:tc>{pr}{ps}</w:tc>"


def tabla(*filas):
    return "<w:tbl>" + "".join("<w:tr>" + "".join(c if c.startswith("<w:tc") else celda(c) for c in f) + "</w:tr>"
                               for f in filas) + "</w:tbl>"


def docx_antiguo(portada_modulo="0961 - Sistemas de medida y regulación",
                 ciclo="Grado Superior: Automatización y Robótica Industrial") -> bytes:
    cuerpo = [
        tabla(["Familia profesional", "Electricidad y Electrónica"], ["Ciclo Formativo", ciclo],
              ["Módulo profesional", portada_modulo]),
        tabla(["Profesores:", "Profesora Ficticia\nProfesor Inventado"], ["Curso académico:", "2026-2027"]),
        p("1.- INTRODUCCIÓN AL MÓDULO"), p("El módulo ficticio tiene una duración de 133 horas."),
        p("4.- METODOLOGÍA"), p("Principios generales y pedagógicos"),
        p("Párrafo ficticio de metodología con el cuaderno de clase."),
        p("Segundo párrafo ficticio de metodología."),
        p("7.- TEMPORALIZACIÓN Y DISTRIBUCIÓN DE RESULTADOS DE APRENDIZAJE Y UNIDADES DE TRABAJO."),
        tabla(["UNIDAD DIDÁCTICA", "Sesiones/\nhoras", "Trim.", "Elementos de evaluación\n(Sesiones/horas)",
               "Peso en el módulo (%)", "RA asociados\n(Real Decreto 401/2023)"],
              ["UD1. Unidad ficticia uno.", "60", "1", "EXAMEN 1\n(60h)", "45,11%", "RA1"],
              ["Práctica/tarea 1", "11", "1", "PRÁCTICA/TAREA 1(11h)", "8,27%", "RA1"],
              ["UD2. Unidad ficticia dos.", "20", "2", celda("EXAMEN 2(40h)", "restart"), "30,08%", "RA2 y RA3"],
              ["UD3. Unidad ficticia tres.", "20", "2", celda("", "continue"), "30,08%", "RA2 y RA3"],
              ["UD4. Unidad ficticia cuatro.", "22", "3", "EXAMEN 3\n(22h)", "16,54%", "RA4 y RA5"],
              ["HORAS CENTRO", "133", "", "", "100%", ""],
              ["TOTAL, HORAS/SESIONES:", "133", "", "", "100%", ""]),
        p("7.1 PONDERACIÓN DE CADA RA."),
        tabla(["Resultado de aprendizaje", "Horas totales", "Modalidad", "Horas en\nempresa"],
              ["RA.1. Resultado ficticio uno.", "71", "Mixto", "5"], ["RA.2. Resultado ficticio dos.", "20", "Centro", "0"],
              ["RA.3. Resultado ficticio tres.", "20", "Centro", "0"], ["RA.4. Resultado ficticio cuatro.", "11", "Centro", "0"],
              ["RA.5. Resultado ficticio cinco.", "11", "Centro", "0"], ["TOTAL", "133", "", "5"]),
        p("8.- PLAN DE EMPRESA"), p("Texto ficticio del plan de empresa."),
        p("9.- EVALUACIÓN."), p("Instrumentos de evaluación."),
        p(anclaje("instrumentos")),
        p("• Pruebas ficticias de conocimientos."), p("• Trabajos ficticios de taller."),
        p("La nota ficticia del módulo es la media de los RA."),
        p(anclaje("asistencia_y_pruebas")),
        p("• Repeticiones de pruebas:", negrita="• Repeticiones de pruebas:"),
        p("No se repite ninguna prueba ficticia."),
        p("• Visitas y actividades complementarias: la asistencia ficticia cuenta.",
          negrita="• Visitas y actividades complementarias:"),
        p("10.- ACTIVIDADES DE RECUPERACIÓN"), p("Recuperación ficticia en junio."),
        p("11.- RECURSOS"), p("Libro de texto ficticio y apuntes."), p("Aula ficticia con su material."),
        p("12.- ADAPTACIÓN FORMATIVA PARA ALUMNOS CON NECESIDADES ESPECÍFICAS DE APOYO EDUCATIVO E INCLUSIÓN. METODOLOGÍA."),
        p("Texto ficticio de atención a la diversidad."),
    ]
    documento_xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W_NS}"><w:body>'
                     + "".join(cuerpo) + "</w:body></w:document>")
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/'
                   'xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
                   'officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("word/document.xml", documento_xml)
    return salida.getvalue()


@pytest.fixture
def antigua(cat):
    return importar_docx.importar(docx_antiguo(), cat, NOMBRE)


def test_se_reconoce_el_formato_antiguo():
    from programaciones import contenido

    assert importar_antigua.es_antigua(contenido.leer(docx_antiguo()))


def test_modulo_y_portada_salen_de_la_portada(antigua):
    assert (antigua["ciclo"], antigua["curso"], antigua["modulo"]) == ("ARI", 1, "0961")
    assert antigua["profesorado"] == ["Profesora Ficticia", "Profesor Inventado"]
    assert antigua["curso_escolar"] == "2026-2027"


def test_unidades_y_elementos_de_la_tabla_de_temporalizacion(antigua):
    el = {e["id"]: e for e in antigua["elementos"]}
    filas = [(u["titulo"], u["horas"], u["trimestre"], el[u["elemento"]]["nombre"], el[u["elemento"]]["tipo"],
              el[u["elemento"]]["ra"]) for u in antigua["unidades"]]
    assert filas == [
        ("UD1. Unidad ficticia uno.", 60, 1, "EXAMEN 1", "E", [1]),
        ("Práctica/tarea 1", 11, 1, "PRÁCTICA/TAREA 1", "P", [1]),      # «(11h)» pegado al nombre
        ("UD2. Unidad ficticia dos.", 20, 2, "EXAMEN 2", "E", [2, 3]),
        ("UD3. Unidad ficticia tres.", 20, 2, "EXAMEN 2", "E", [2, 3]),  # celda combinada: el mismo elemento
        ("UD4. Unidad ficticia cuatro.", 22, 3, "EXAMEN 3", "E", [4, 5]),
    ]
    assert len(antigua["elementos"]) == 4
    assert all("detalle" not in e for e in antigua["elementos"])        # «(Nh)» es el detalle por defecto


def test_empresa_y_modalidad_de_la_tabla_de_ponderacion(antigua):
    assert antigua["empresa"] == {"1": 5}
    assert antigua["modalidad"]["1"] == "Mixto" and antigua["modalidad"]["2"] == "Centro"


def test_parrafos_del_profesor_en_su_sitio(antigua):
    assert [x["texto"] for x in antigua["metodologia"]] == [
        "Párrafo ficticio de metodología con el cuaderno de clase.", "Segundo párrafo ficticio de metodología."]
    assert [x["texto"] for x in antigua["recursos"]] == ["Libro de texto ficticio y apuntes."]
    assert [x["texto"] for x in antigua["espacios"]] == ["Aula ficticia con su material."]
    assert antigua["actividades"] == [] and antigua["contenidos"] == []


def test_evaluacion_solo_lo_que_difiere_de_la_plantilla(antigua):
    propios = antigua["textos_propios"]
    assert propios["instrumentos"] == [{"texto": "Pruebas ficticias de conocimientos.", "nivel": 0},
                                       {"texto": "Trabajos ficticios de taller.", "nivel": 0},
                                       {"texto": "La nota ficticia del módulo es la media de los RA."}]
    # acaba antes de «Visitas y actividades complementarias», que sigue en el mismo párrafo que su texto
    assert propios["asistencia_y_pruebas"] == [{"texto": "**Repeticiones de pruebas:**", "nivel": 0},
                                               {"texto": "No se repite ninguna prueba ficticia."}]


def test_sin_relacion_ra_competencias_y_todo_heredado(antigua):
    assert antigua["ra_competencias"] == {}
    assert set(antigua["bloques"].values()) == {"heredado"}
    assert "formato antiguo" in antigua["historial"][0]["accion"]


def test_se_exporta_como_las_demas_y_vuelve_igual(antigua, cat, curso):
    docx = incrustar.incrustar(documento.generar(antigua, cat, curso), antigua)
    assert exportacion.problemas(docx) == []
    assert importar_docx.importar(docx, cat, "ARI 1 - 0961 - Sistemas de medida y regulación.docx") == antigua


def test_codigo_en_varios_ciclos_sin_ciclo_en_la_portada(cat):
    datos = docx_antiguo(portada_modulo="1709 - Itinerario personal para la empleabilidad I", ciclo="")
    with pytest.raises(importar_docx.NoEsProgramacion, match="renombra el archivo"):
        importar_docx.importar(datos, cat, NOMBRE)


def test_el_nombre_del_archivo_manda_sobre_la_portada(cat):
    datos = docx_antiguo(portada_modulo="1709 - Itinerario personal para la empleabilidad I", ciclo="")
    prog = importar_docx.importar(datos, cat, "ARI 1 - 1709 - Itinerario personal para la empleabilidad I.docx")
    assert (prog["ciclo"], prog["curso"], prog["modulo"]) == ("ARI", 1, "1709")
