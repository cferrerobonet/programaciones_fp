"""Importar un ámbito de Grado Básico sin datos de la app (ADR-040): un .docx ficticio con la forma del modelo del
departamento (tablas por parte en el 3 y el 3.1) y un ámbito exportado con la app que ha perdido sus datos."""
import pytest

from programaciones import documento, exportacion, importar_docx
from test_grado_basico import programacion_ambito
from test_importar_antigua import _empaquetar, p, tabla

NOMBRE = "Ámbito ficticio.docx"


def titulo(texto, nivel=1):
    return f'<w:p><w:pPr><w:pStyle w:val="Ttulo{nivel}"/></w:pPr><w:r><w:t>{texto}</w:t></w:r></w:p>'


def docx_ambito(ciclo="INFORMÁTICA Y COMUNICACIONES") -> bytes:
    cab = ["Elementos de Trabajo", "Unidades de Trabajo", "Competencias Específicas (CE)", "Horas", "Trimestre"]
    return _empaquetar([
        p("PROGRAMACIÓN DIDÁCTICA"),
        tabla(["Familia profesional", "FICTICIA"], ["Ciclo Formativo", ciclo], ["Ámbito", "CIENCIAS APLICADAS II"],
              ["Código", "3164"], ["Nº horas módulo", "166 h."]),
        tabla(["Profesor:", "Profesor Ficticio"], ["Curso académico:", "2026/2027"]),
        titulo("3.- TEMPORALIZACIÓN Y DISTRIBUCIÓN DE LAS COMPETENCIAS ESPECÍFICAS"),
        p("Para Matemáticas ficticias (100h) es la siguiente:"),
        tabla(cab, ["Tarea 1-4", "Números ficticios", "CE1, CE7", "60", "1"],
              ["Examen de números", "Números ficticios", "CE1", "40", "2 y 3"], ["TOTAL", "100", ""]),
        p("Para Ciencias ficticias (66 h) es la siguiente:"),
        tabla(cab, ["Tareas 5-6", "Materia ficticia", "CE2, CE3", "66", "1-2"], ["TOTAL", "66", ""]),
        p("Nota ficticia tras las tablas."),
        titulo("3.1.- PONDERACIÓN DE CADA COMPETENCIA ESPECÍFICA", 2),
        p("Nota ficticia de la ponderación."),
        p("Para Matemáticas ficticias:"),
        tabla(["Competencia Específica (CE)", "Peso en horas"], ["CE1. Ficticia", "99"], ["TOTAL", "99"]),
        titulo("4.- METODOLOGÍA"), p("Metodología ficticia del ámbito."),
        titulo("5.- RECURSOS"), p("Libro ficticio de ciencias."),
        titulo("6.- USO DE ESPACIOS Y EQUIPAMIENTOS"), p("Laboratorio ficticio."),
        titulo("9.- ACTIVIDADES COMPLEMENTARIAS Y EXTRAESCOLARES"), p("Visita ficticia a un museo."),
    ])


@pytest.fixture
def ambito(cat):
    return importar_docx.importar(docx_ambito(), cat, NOMBRE)


def test_el_modulo_sale_de_la_portada_con_el_ciclo(ambito):
    assert (ambito["ciclo"], ambito["curso"], ambito["modulo"]) == ("IC", 2, "3164")   # 3164 está en EE, IC, MV y SA
    assert ambito["profesorado"] == ["Profesor Ficticio"] and ambito["curso_escolar"] == "2026-2027"   # «2026/2027»


def test_partes_unidades_y_elementos_de_las_tablas_del_3(ambito):
    assert ambito["partes"] == [{"id": "p1", "nombre": "Matemáticas ficticias", "horas": 100},
                                {"id": "p2", "nombre": "Ciencias ficticias", "horas": 66}]
    el = {e["id"]: e for e in ambito["elementos"]}
    assert [(u["titulo"], u["horas"], u["trimestre"], u["parte"], el[u["elemento"]]["nombre"],
             el[u["elemento"]]["tipo"], el[u["elemento"]]["ra"]) for u in ambito["unidades"]] == [
        ("Números ficticios", 60, 1, "p1", "Tarea 1-4", "T", [1, 7]),
        ("Números ficticios", 40, [2, 3], "p1", "Examen de números", "E", [1]),
        ("Materia ficticia", 66, [1, 2], "p2", "Tareas 5-6", "T", [2, 3]),
    ]


def test_parrafos_del_profesor_en_su_sitio(ambito):
    textos = {k: [x["texto"] for x in ambito[k]] for k in
              ("contenidos", "notas_tabla4", "notas_tabla41", "metodologia", "recursos", "espacios", "actividades")}
    assert textos == {"contenidos": [], "notas_tabla4": ["Nota ficticia tras las tablas."],
                      "notas_tabla41": ["Nota ficticia de la ponderación."],
                      "metodologia": ["Metodología ficticia del ámbito."], "recursos": ["Libro ficticio de ciencias."],
                      "espacios": ["Laboratorio ficticio."], "actividades": ["Visita ficticia a un museo."]}
    assert set(ambito["bloques"].values()) == {"heredado"} and "(ámbito)" in ambito["historial"][0]["accion"]


def test_codigo_en_varios_ciclos_sin_ciclo_reconocible(cat):
    with pytest.raises(importar_docx.NoEsProgramacion, match="varios ciclos"):
        importar_docx.importar(docx_ambito(ciclo="CICLO FICTICIO"), cat, NOMBRE)
    prog = importar_docx.importar(docx_ambito(ciclo="CICLO FICTICIO"), cat, NOMBRE, modulo=("SA", 2, "3164"))
    assert prog["ciclo"] == "SA"


def test_un_ambito_exportado_sin_datos_vuelve_con_sus_partes_y_unidades(cat):
    original = programacion_ambito(cat)
    sin_datos = documento.generar(original, cat, cat.curso_escolar("2026-2027"))   # sin incrustar
    assert exportacion.problemas(sin_datos) == []        # los títulos de la plantilla de ámbitos valen
    leido = importar_docx.importar(sin_datos, cat, "Ámbito exportado.docx", modulo=("EE", 2, "3164"))
    assert leido["partes"] == original["partes"]
    assert [(u["titulo"], u["horas"], u["trimestre"], u["parte"]) for u in leido["unidades"]] == \
        [(u["titulo"], u["horas"], u["trimestre"], u["parte"]) for u in original["unidades"]]
    assert [e["ra"] for e in leido["elementos"]] == [e["ra"] for e in original["elementos"]]
