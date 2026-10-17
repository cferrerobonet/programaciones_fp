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
    assert leido["evaluaciones"] == curso["evaluaciones"] and leido["ordinaria"] == curso["ordinaria"]
    assert leido["extraordinaria_desde"] == curso["extraordinaria_desde"]
    assert leido["formacion_empresa"]["GS"][2] == curso["formacion_empresa"]["GS"][2]


def test_nombre_que_no_es_de_programacion(prog, cat, curso):
    with pytest.raises(importar_docx.NoEsProgramacion):
        importar_docx.importar(documento.generar(prog, cat, curso), cat, "documento cualquiera.docx")


@pytest.mark.parametrize("texto, ras", [("RA1 y RA2", [1, 2]), ("RA3, RA4 y RA6", [3, 4, 6]), ("RA2 → RA6", [2, 3, 4, 5, 6]),
                                        ("RA1, RA3, RA4", [1, 3, 4])])
def test_lista_de_ra(texto, ras):
    assert importar_docx._ras(texto) == ras
