"""Importar una programación .docx (RF-08 y RF-10): ida y vuelta con documentos generados con datos ficticios."""
import pytest

from programaciones import documento, importar_docx, incrustar

NOMBRE = "SEA 2 - 0517 - Procesos en instalaciones de infraestructuras comunes de telecomunicaciones.docx"


def sin_ids(prog):
    """Unidades y elementos comparables (los identificadores los pone el importador)."""
    el = {e["id"]: e for e in prog["elementos"]}
    return [(u["titulo"], u["horas"], u["trimestre"], el[u["elemento"]]["nombre"], el[u["elemento"]]["tipo"],
             el[u["elemento"]]["ra"], u.get("descripcion"), el[u["elemento"]].get("detalle")) for u in prog["unidades"]]


@pytest.fixture
def importado(prog, cat, curso):
    return importar_docx.importar(documento.generar(prog, cat, curso), cat, NOMBRE)


def test_ida_y_vuelta_de_los_bloques_del_profesor(importado, prog):
    assert sin_ids(importado) == sin_ids(prog)
    for clave in ("profesorado", "empresa", "centro_ajustado", "ra_competencias", "metodologia", "metodologia_final",
                  "recursos", "espacios", "notas_tabla4", "notas_tabla41", "contenidos", "actividades",
                  "textos_propios"):
        assert importado[clave] == prog[clave], clave


def test_lo_importado_queda_heredado(importado):
    assert set(importado["bloques"].values()) == {"heredado"}


def test_descripcion_trimestres_y_detalle(prog, cat, curso):
    prog["unidades"][0]["descripcion"] = ["Descripción ficticia de la unidad."]
    prog["unidades"][1]["trimestre"] = [1, 2]
    prog["elementos"][2]["detalle"] = ["(7h)", "MEMORIA ficticia"]
    imp = importar_docx.importar(documento.generar(prog, cat, curso), cat, NOMBRE)
    assert sin_ids(imp) == sin_ids(prog)


def test_textos_propios_ida_y_vuelta(prog, cat, curso):
    prog["textos_propios"] = {"instrumentos": [{"texto": "Entrega de las tareas ficticias.", "nivel": 0}],
                              "calificacion": [{"texto": "La calificación ficticia sale de las tareas."}]}
    imp = importar_docx.importar(documento.generar(prog, cat, curso), cat, NOMBRE)
    assert imp["textos_propios"] == prog["textos_propios"]


def test_con_datos_incrustados_los_recupera_tal_cual(prog, cat, curso):
    exportado = incrustar.incrustar(documento.generar(prog, cat, curso), prog)
    assert importar_docx.importar(exportado, cat, NOMBRE) == prog


def test_fechas_del_curso(prog, cat, curso):
    leido = importar_docx.leer_curso(documento.generar(prog, cat, curso), "GS", 2)
    assert leido["evaluaciones"] == curso["evaluaciones"]   # también las convocatorias (ADR-033)
    assert leido["formacion_empresa"]["GS"][2] == curso["formacion_empresa"]["GS"][2]


def test_fechas_del_curso_de_una_programacion_anterior(prog, cat, curso):
    """Una programación de antes de ADR-033 («se realizará del … al … y … comenzará el …»): de la ordinaria, su fin."""
    import io
    import zipfile
    d = documento.generar(prog, cat, curso)
    entrada, salida = zipfile.ZipFile(io.BytesIO(d)), io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for i in entrada.infolist():
            datos = entrada.read(i.filename)
            if i.filename == "word/document.xml":
                datos = (datos.decode().replace("finalizará el 10 de junio de 2031", "se realizará del 2 de junio al 5 de junio de 2031")
                         .replace("finalizará el 24 de junio de 2031", "comenzará el 16 de junio de 2031").encode())
            z.writestr(i, datos)
    leido = importar_docx.leer_curso(salida.getvalue(), "GS", 2)
    assert leido["evaluaciones"]["ordinaria"] == "2031-06-05" and leido["evaluaciones"]["extraordinaria"] == "2031-06-16"


def test_nombre_que_no_es_de_programacion(prog, cat, curso):
    with pytest.raises(importar_docx.NoEsProgramacion):
        importar_docx.importar(documento.generar(prog, cat, curso), cat, "documento cualquiera.docx")


@pytest.mark.parametrize("texto, ras", [("RA1 y RA2", [1, 2]), ("RA3, RA4 y RA6", [3, 4, 6]), ("RA2 → RA6", [2, 3, 4, 5, 6]),
                                        ("RA1, RA3, RA4", [1, 3, 4])])
def test_lista_de_ra(texto, ras):
    assert importar_docx._ras(texto) == ras


def test_la_modalidad_se_lee_de_la_tabla_41(prog, cat, curso):
    """ADR-030: la columna «Modalidad» del documento rellena la de la app; un Mixto sin horas de empresa sigue en
    empresa (con 0 h) para que el profesor las ponga."""
    prog["modalidad"] = {"2": "Mixto"}
    prog["empresa"]["2"] = 0
    imp = importar_docx.importar(documento.generar(prog, cat, curso), cat, NOMBRE)
    assert imp["modalidad"] == {"1": "Centro", "2": "Mixto", "3": "Mixto", "4": "Mixto", "5": "Empresa", "6": "Mixto"}
    assert imp["empresa"]["2"] == 0


def test_pesos_ajustados_y_columna_del_curso_ida_y_vuelta(prog, cat, curso):
    prog["elementos"][0]["peso_ajustado"] = {"valor": 2.15}
    prog["elementos"][2]["peso_ajustado"] = {"valor": 4.2, "texto": "1,4 % / x práctica"}
    prog["columna_pct_curso"] = True
    imp = importar_docx.importar(documento.generar(prog, cat, curso), cat, NOMBRE)
    assert [e.get("peso_ajustado") for e in imp["elementos"]] == [e.get("peso_ajustado") for e in prog["elementos"]]
    assert imp["columna_pct_curso"] is True
