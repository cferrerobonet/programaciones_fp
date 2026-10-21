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


def titulo(texto, nivel=1):
    return f'<w:p><w:pPr><w:pStyle w:val="Ttulo{nivel}"/></w:pPr><w:r><w:t>{escape(texto)}</w:t></w:r></w:p>'


def tabla(*filas):
    return "<w:tbl>" + "".join("<w:tr>" + "".join(c if c.startswith("<w:tc") else celda(c) for c in f) + "</w:tr>"
                               for f in filas) + "</w:tbl>"


def docx_antiguo(portada_modulo="0961 - Sistemas de medida y regulación",
                 ciclo="Grado Superior: Automatización y Robótica Industrial", titulos_con_estilo=False,
                 cabecera_horas="Horas totales") -> bytes:
    """`titulos_con_estilo`: los títulos con estilo de título de Word (como las de 2026-09 de CarlosFB) en lugar de
    párrafos normales; `cabecera_horas`: «Horas» a secas en la tabla de ponderación (las horas totales del RA)."""
    t = titulo if titulos_con_estilo else p
    cuerpo = [
        tabla(["Familia profesional", "Electricidad y Electrónica"], ["Ciclo Formativo", ciclo],
              ["Módulo profesional", portada_modulo]),
        tabla(["Profesores:", "Profesora Ficticia\nProfesor Inventado"], ["Curso académico:", "2026-2027"]),
        t("1.- INTRODUCCIÓN AL MÓDULO"), p("El módulo ficticio tiene una duración de 133 horas."),
        t("4.- METODOLOGÍA"), p("Principios generales y pedagógicos"),
        p("Párrafo ficticio de metodología con el cuaderno de clase."),
        p("Segundo párrafo ficticio de metodología."),
        t("7.- TEMPORALIZACIÓN Y DISTRIBUCIÓN DE RESULTADOS DE APRENDIZAJE Y UNIDADES DE TRABAJO."),
        tabla(["UNIDAD DIDÁCTICA", "Sesiones/\nhoras", "Trim.", "Elementos de evaluación\n(Sesiones/horas)",
               "Peso en el módulo (%)", "RA asociados\n(Real Decreto 401/2023)"],
              ["UD1. Unidad ficticia uno.", "60", "1", "EXAMEN 1\n(60h)", "45,11%", "RA1"],
              ["Práctica/tarea 1", "11", "1", "PRÁCTICA/TAREA 1(11h)", "8,27%", "RA1"],
              ["UD2. Unidad ficticia dos.", "20", "2", celda("EXAMEN 2(40h)", "restart"), "30,08%", "RA2 y RA3"],
              ["UD3. Unidad ficticia tres.", "20", "2", celda("", "continue"), "30,08%", "RA2 y RA3"],
              ["UD4. Unidad ficticia cuatro.", "22", "3", "EXAMEN 3\n(22h)", "16,54%", "RA4 y RA5"],
              ["HORAS CENTRO", "133", "", "", "100%", ""],
              ["TOTAL, HORAS/SESIONES:", "133", "", "", "100%", ""]),
        t("7.1 PONDERACIÓN DE CADA RA."),
        tabla(["Resultado de aprendizaje", cabecera_horas, "Modalidad", "Horas en\nempresa"],
              ["RA.1. Resultado ficticio uno.", "71", "Mixto", "5"], ["RA.2. Resultado ficticio dos.", "20", "Centro", "0"],
              ["RA.3. Resultado ficticio tres.", "20", "Centro", "0"], ["RA.4. Resultado ficticio cuatro.", "11", "Centro", "0"],
              ["RA.5. Resultado ficticio cinco.", "11", "Centro", "0"], ["TOTAL", "133", "", "5"]),
        t("8.- PLAN DE EMPRESA"), p("Texto ficticio del plan de empresa."),
        t("9.- EVALUACIÓN."), p("Instrumentos de evaluación."),
        p(anclaje("instrumentos")),
        p("• Pruebas ficticias de conocimientos."), p("• Trabajos ficticios de taller."),
        p("La nota ficticia del módulo es la media de los RA."),
        p(anclaje("asistencia_y_pruebas")),
        p("• Repeticiones de pruebas:", negrita="• Repeticiones de pruebas:"),
        p("No se repite ninguna prueba ficticia."),
        p("• Visitas y actividades complementarias: la asistencia ficticia cuenta.",
          negrita="• Visitas y actividades complementarias:"),
        t("10.- ACTIVIDADES DE RECUPERACIÓN"), p("Recuperación ficticia en junio."),
        t("11.- RECURSOS"), p("Libro de texto ficticio y apuntes."), p("Aula ficticia con su material."),
        t("12.- ADAPTACIÓN FORMATIVA PARA ALUMNOS CON NECESIDADES ESPECÍFICAS DE APOYO EDUCATIVO E INCLUSIÓN. METODOLOGÍA."),
        p("Texto ficticio de atención a la diversidad."),
    ]
    return _empaquetar(cuerpo)


def _empaquetar(cuerpo: list[str]) -> bytes:
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


NOMBRE_GB = "TID 1 - 3001 - Módulo ficticio.docx"   # la sigla es la del módulo, no la del ciclo


def docx_antiguo_gb(cabecera="Elementos de Trabajo (ET)") -> bytes:
    """Formato antiguo de Grado Básico: tablas en 7 y 7.1, una fila por elemento de trabajo con el título de la unidad
    en la celda del examen, y la evaluación tras la ponderación, repartida por subtítulos."""
    cuerpo = [
        tabla(["Familia profesional", "Grado Básico"], ["Ciclo Formativo", "Servicios Administrativos"],
              ["Módulo profesional", "3001. Módulo ficticio"], ["Nº horas módulo", "100h"]),
        tabla(["Profesoras:", "Profesora Ficticia / Profesora Inventada"], ["Curso académico:", "2026-2027"]),
        p("4.- METODOLOGÍA"), p("Párrafo ficticio de metodología de Grado Básico."),
        p("5.- RESULTADOS DE APRENDIZAJE Y CRITERIOS DE EVALUACIÓN"), p("Resultado de Aprendizaje 1: ficticio."),
        p("7.- TEMPORALIZACIÓN Y DISTRIBUCIÓN DE RESULTADOS DE APRENDIZAJE Y UNIDADES DE TRABAJO."),
        tabla([cabecera, "HORAS", "RA ASOCIADO", "Trimestre"],
              ["EXAMEN UT1\nUT1. Unidad ficticia uno. (30h)", "10", "RA1", "1"],
              ["TAREAS UT1", "20", "RA1", "1"],
              ["EXAMEN UT2\nUT2. Unidad ficticia dos. (70h)", "20", "RA2", "2 y 3"],
              ["TAREAS UT2", "50", "RA2", "2 y 3"],
              ["Total", "100", "", ""]),
        p("7.1- PONDERACIÓN DE CADA RESULTADO DE APRENDIZAJE (RA)."),
        tabla(["Resultado de Aprendizaje (RA)", "Porcentaje", "Horas Centro", "Horas Empresa"],
              ["RA1. Resultado ficticio uno.", "30%", "30", "0"], ["RA2. Resultado ficticio dos.", "70%", "60", "10"],
              ["TOTAL", "100h / 100%", "90 / 90%", "10 / 10%"]),
        p("La evaluación ficticia será continua, formativa y objetiva."),
        p("Durante el curso se celebrarán las siguientes sesiones de evaluación:"),
        tabla(["Evaluación", "Fecha"], ["1.ª Evaluación", "01/12/2026"]),
        p("Instrumentos de evaluación"),
        p("Para valorar el grado de consecución de los criterios ficticios se utilizarán los siguientes instrumentos:"),
        p("• Exámenes (E): pruebas ficticias."), p("• Tareas (T): tareas ficticias."),
        p("Desempeño profesional"), p("El desempeño ficticio se observará a diario."),
        p("Criterios generales"), p("La asistencia ficticia deberá ser, al menos, del 85 %."),
        p("No se repetirán pruebas ficticias salvo causa justificada."),
        p("9.- ACTIVIDADES DE RECUPERACIÓN"), p("Recuperación ficticia."),
        p("10.- RECURSOS"), p("Libro ficticio de Grado Básico."), p("Aula ficticia de informática."),
    ]
    return _empaquetar(cuerpo)


@pytest.fixture
def antigua_gb(cat):
    return importar_docx.importar(docx_antiguo_gb(), cat, NOMBRE_GB)


def test_se_reconoce_el_formato_antiguo_de_grado_basico():
    from programaciones import contenido

    assert importar_antigua.es_antigua(contenido.leer(docx_antiguo_gb()))


def test_gb_el_modulo_sale_de_la_portada_aunque_el_nombre_lleve_la_sigla_del_modulo(antigua_gb):
    assert (antigua_gb["ciclo"], antigua_gb["curso"], antigua_gb["modulo"]) == ("SA", 1, "3001")
    assert antigua_gb["profesorado"] == ["Profesora Ficticia", "Profesora Inventada"]   # «A / B» en la misma celda
    assert antigua_gb["curso_escolar"] == "2026-2027"


def test_gb_una_unidad_por_elemento_de_trabajo_con_el_titulo_de_la_celda_del_examen(antigua_gb):
    el = {e["id"]: e for e in antigua_gb["elementos"]}
    filas = [(u["titulo"], u["horas"], u["trimestre"], el[u["elemento"]]["nombre"], el[u["elemento"]]["tipo"],
              el[u["elemento"]]["ra"]) for u in antigua_gb["unidades"]]
    assert filas == [
        ("UT1. Unidad ficticia uno.", 10, 1, "EXAMEN UT1", "E", [1]),        # sin el «(30h)» pegado al título
        ("TAREAS UT1", 20, 1, "TAREAS UT1", "T", [1]),
        ("UT2. Unidad ficticia dos.", 20, [2, 3], "EXAMEN UT2", "E", [2]),
        ("TAREAS UT2", 50, [2, 3], "TAREAS UT2", "T", [2]),
    ]
    assert all("detalle" not in e for e in antigua_gb["elementos"])   # el título de la unidad no es detalle
    assert antigua_gb["empresa"] == {"2": 10}
    assert antigua_gb["notas_tabla4"] == [] and antigua_gb["notas_tabla41"] == []   # la evaluación no son notas


def test_gb_la_evaluacion_se_reparte_por_sus_subtitulos(antigua_gb):
    propios = antigua_gb["textos_propios"]
    assert propios["elementos"] == [
        {"texto": "Exámenes (E): pruebas ficticias.", "nivel": 0}, {"texto": "Tareas (T): tareas ficticias.", "nivel": 0},
        {"texto": "**Desempeño profesional**"}, {"texto": "El desempeño ficticio se observará a diario."}]
    assert propios["asistencia_y_pruebas"] == [{"texto": "La asistencia ficticia deberá ser, al menos, del 85 %."},
                                               {"texto": "No se repetirán pruebas ficticias salvo causa justificada."}]
    assert set(propios) == {"elementos", "asistencia_y_pruebas"}   # lo anterior a los subtítulos es texto de la plantilla


def test_gb_parrafos_del_profesor_en_su_sitio(antigua_gb):
    assert [x["texto"] for x in antigua_gb["metodologia"]] == ["Párrafo ficticio de metodología de Grado Básico."]
    assert [x["texto"] for x in antigua_gb["recursos"]] == ["Libro ficticio de Grado Básico."]
    assert [x["texto"] for x in antigua_gb["espacios"]] == ["Aula ficticia de informática."]
    assert set(antigua_gb["bloques"].values()) == {"heredado"}


def test_gb_se_exporta_como_las_demas_y_vuelve_igual(antigua_gb, cat, curso):
    from conftest import programacion_minima

    docx = incrustar.incrustar(documento.generar(antigua_gb, cat, curso), antigua_gb)
    # los avisos del documento (títulos y normas sin enlace de Grado Básico, docs/PENDIENTE.md) son los de cualquier
    # programación de ese módulo, no de la importación
    vacia = documento.generar(programacion_minima(cat, "SA", 1, "3001"), cat, curso)
    assert exportacion.problemas(docx) == exportacion.problemas(vacia)
    assert importar_docx.importar(docx, cat, NOMBRE_GB) == antigua_gb


def test_la_sigla_del_modulo_en_el_nombre_no_vale_como_ciclo_en_el_formato_actual(cat):
    """Un Word de la plantilla actual llamado «TID 1 - 3001 - …» no se importa como del ciclo «TID»: se pide el módulo."""
    with pytest.raises(importar_docx.NoEsProgramacion, match="sigla del ciclo"):
        importar_docx.importar(docx_antiguo_gb(cabecera="Otra cosa"), cat, NOMBRE_GB)


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


def test_titulos_con_estilo_y_horas_a_secas_en_la_ponderacion(cat, antigua):
    """Las antiguas de 2026-09 llevan los títulos con estilo de título de Word y «Horas» a secas en la ponderación:
    se leen igual (antes, «sin los apartados de la plantilla» y horas de centro negativas)."""
    otra = importar_docx.importar(docx_antiguo(titulos_con_estilo=True, cabecera_horas="Horas"), cat, NOMBRE)
    sin_fecha = lambda x: {k: v for k, v in x.items() if k != "historial"}   # noqa: E731
    assert sin_fecha(otra) == sin_fecha(antigua)


def test_codigo_en_varios_ciclos_sin_ciclo_en_la_portada(cat):
    datos = docx_antiguo(portada_modulo="1709 - Itinerario personal para la empleabilidad I", ciclo="")
    with pytest.raises(importar_docx.NoEsProgramacion, match="renombra el archivo"):
        importar_docx.importar(datos, cat, NOMBRE)


def test_el_nombre_del_archivo_manda_sobre_la_portada(cat):
    datos = docx_antiguo(portada_modulo="1709 - Itinerario personal para la empleabilidad I", ciclo="")
    prog = importar_docx.importar(datos, cat, "ARI 1 - 1709 - Itinerario personal para la empleabilidad I.docx")
    assert (prog["ciclo"], prog["curso"], prog["modulo"]) == ("ARI", 1, "1709")


def test_con_el_modulo_elegido_y_la_portada_de_acuerdo(cat):
    prog = importar_docx.importar(docx_antiguo(), cat, NOMBRE, modulo=("ARI", 1, "0961"))
    assert (prog["ciclo"], prog["curso"], prog["modulo"]) == ("ARI", 1, "0961")


def test_la_portada_dice_otro_modulo_que_el_elegido(cat):
    with pytest.raises(importar_docx.ModuloDistinto) as e:
        importar_docx.importar(docx_antiguo(), cat, NOMBRE, modulo=("SEA", 1, "0519"))
    assert e.value.documento == ("ARI", 1, "0961")


def test_codigo_en_varios_ciclos_con_el_modulo_elegido(cat):
    """La portada solo dice el código (1709 está en todos los ciclos): el elegido decide el ciclo, sin preguntar."""
    datos = docx_antiguo(portada_modulo="1709 - Itinerario personal para la empleabilidad I", ciclo="")
    prog = importar_docx.importar(datos, cat, NOMBRE, modulo=("SEA", 1, "1709"))
    assert (prog["ciclo"], prog["curso"], prog["modulo"]) == ("SEA", 1, "1709")
    with pytest.raises(importar_docx.ModuloDistinto) as e:     # de otro código: se pregunta, sin ciclo conocido
        importar_docx.importar(datos, cat, NOMBRE, modulo=("ARI", 1, "0961"))
    assert e.value.documento == (None, None, "1709")


def _tablas_41(cabecera_41, *filas_41):
    """Elementos de una tabla 4 mínima (dos unidades, 40 h) y de una 4.1 con la cabecera y las filas dadas."""
    from programaciones import contenido
    docx = _empaquetar([
        tabla(["UNIDAD", "HORAS", "TRIMESTRE", "ELEMENTO DE EVALUACIÓN", "PESO", "RA ASOCIADOS"],
              ["UD01. Unidad ficticia uno", "20", "1", "EXAMEN 1", "50 %", "RA1"],
              ["UD02. Unidad ficticia dos", "20", "2", "EXAMEN 2", "50 %", "RA2"]),
        tabla(cabecera_41, *filas_41),
    ])
    els = contenido.leer(docx)
    tablas_ = [e for e in els if e.tipo == "tabla"]
    return [tablas_[0]], [tablas_[1]]


def test_horas_de_la_41_que_son_de_centro_y_no_el_total():
    """2026-10-21 (Sostenibilidad 1708): «Horas» y «Horas empresa»; «Horas» era la parte de centro (RA2: 10 de centro y
    20 de empresa). Leídas como total daban un centro de -10 y la programación no se podía heredar."""
    from programaciones import importar_docx
    s4, s41 = _tablas_41(["Resultado de aprendizaje", "Horas", "Horas empresa"],
                         ["RA1. Ficticio uno.", "10", "0"], ["RA2. Ficticio dos.", "10", "20"])
    prog = importar_docx.leer_tablas(s4, s41, [1, 2], horas=40)
    assert all(v >= 0 for v in prog["centro_ajustado"].values())
    assert prog["empresa"] == {"2": 20}
    assert int(prog["centro_ajustado"].get("2", 10)) == 10


def test_horas_de_la_41_que_son_el_total_siguen_igual():
    from programaciones import importar_docx
    s4, s41 = _tablas_41(["Resultado de aprendizaje", "Horas", "Horas empresa"],
                         ["RA1. Ficticio uno.", "10", "0"], ["RA2. Ficticio dos.", "30", "20"])
    prog = importar_docx.leer_tablas(s4, s41, [1, 2], horas=40)
    assert prog["empresa"] == {"2": 20}
    assert int(prog["centro_ajustado"].get("2", 10)) == 10 and all(v >= 0 for v in prog["centro_ajustado"].values())
