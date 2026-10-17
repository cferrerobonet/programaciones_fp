"""«Nueva a partir de…» (RF-09, ADR-008) y el archivo de trabajo de este equipo (RF-05): datos ficticios."""
import datetime as dt

import pytest

from programaciones import almacen, documento, herencia, incrustar, programacion, validacion

NOMBRE = "SEA 2 - 0517 - Procesos en instalaciones de infraestructuras comunes de telecomunicaciones.docx"


def test_heredar_marca_los_bloques_y_pone_el_curso_nuevo(prog, cat):
    prog["bloques"] = {b: "confirmado" for b in prog["bloques"]}
    h = herencia.heredar(prog, cat, "2031-2032", "anterior.programacion")
    nuevo = h.programacion
    assert nuevo["curso_escolar"] == "2031-2032" and nuevo["catalogo"] == cat.version
    assert nuevo["unidades"] == prog["unidades"] and nuevo["elementos"] == prog["elementos"]
    con_datos = {b for b in programacion.BLOQUES if herencia._con_datos(prog, b)}
    assert {b for b, e in nuevo["bloques"].items() if e == "heredado"} == con_datos
    assert nuevo["heredada_de"] == {"profesor": "Profesora Ficticia Uno", "curso_escolar": "2030-2031",
                                    "archivo": "anterior.programacion"}
    assert h.resumen == {"unidades": 15, "elementos": 10, "ra_empresa": 5, "heredados": len(con_datos)}
    assert not h.avisos


def test_lo_heredado_bloquea_la_definitiva_hasta_confirmarlo(prog, cat):
    nuevo = herencia.heredar(prog, cat, "2031-2032").programacion
    ficha = cat.ficha("SEA", "0517", 2)
    assert "V-06" in {a.id for a in validacion.validar(nuevo, ficha) if a.gravedad == validacion.ROJA}
    nuevo["bloques"] = {b: "confirmado" for b in nuevo["bloques"]}
    assert "V-06" not in {a.id for a in validacion.validar(nuevo, ficha)}


def test_un_bloque_vacio_no_llega_heredado(prog, cat):
    prog["actividades"] = []
    nuevo = herencia.heredar(prog, cat, "2031-2032").programacion
    assert nuevo["bloques"]["actividades"] == "vacio"


def test_los_ra_que_ya_no_estan_se_quitan_y_se_avisa(prog, cat):
    prog["elementos"][0]["ra"] = [6, 9]
    prog["empresa"]["9"] = 4
    prog["ra_competencias"]["9"] = ["a"]
    h = herencia.heredar(prog, cat, "2031-2032")
    assert h.programacion["elementos"][0]["ra"] == [6]
    assert "9" not in h.programacion["empresa"] and "9" not in h.programacion["ra_competencias"]
    assert any(a.startswith("RA9") for a in h.avisos)


def test_leer_origen_de_un_docx_exportado_y_de_un_programacion(prog, cat, curso, tmp_path):
    docx = tmp_path / NOMBRE
    docx.write_bytes(incrustar.incrustar(documento.generar(prog, cat, curso), prog))
    origen = herencia.leer_origen(docx, cat)
    assert origen.exportada_por_la_app and not origen.modificado_en_word and origen.programacion == prog
    archivo = tmp_path / "x.programacion"
    programacion.escribir(archivo, prog)
    assert herencia.leer_origen(archivo, cat).programacion == prog


def test_leer_origen_de_un_word_sin_datos_lo_importa(prog, cat, curso, tmp_path):
    docx = tmp_path / NOMBRE
    docx.write_bytes(documento.generar(prog, cat, curso))
    origen = herencia.leer_origen(docx, cat)
    assert not origen.exportada_por_la_app
    assert set(origen.programacion["bloques"].values()) == {"heredado"}


def test_leer_origen_rechaza_otro_archivo(cat, tmp_path):
    otro = tmp_path / "notas.txt"
    otro.write_text("nada", encoding="utf-8")
    with pytest.raises(ValueError):
        herencia.leer_origen(otro, cat)


# Archivo de trabajo de este equipo
def test_almacen_guarda_con_diez_copias_y_lista(prog, tmp_path):
    a = almacen.Almacen(tmp_path)
    inicio = dt.datetime(2030, 10, 1, 9, 0)
    for i in range(12):
        a.guardar(prog, inicio + dt.timedelta(minutes=i))
    copias = list((tmp_path / "autoguardado").glob("*/*.programacion"))
    assert len(copias) == almacen.VERSIONES
    assert a.cargar("2030-2031", "SEA", 2, "0517") == prog
    assert a.cargar("2030-2031", "SEA", 2, "0518") is None
    assert [g.id for g in a.todas()] == ["2030-2031/SEA-2-0517"]


def test_estado_de_cada_paso_y_de_la_programacion(prog):
    prog["bloques"] = {b: "confirmado" for b in prog["bloques"]}
    assert almacen.confirmados(prog) == 5 and almacen.estado(prog) == "en_curso"
    prog["bloques"]["recursos"] = "heredado"
    assert almacen.estado_paso(prog, "metodologia") == "heredado"
    assert almacen.texto_estado(prog) == "Heredada · sin revisar"
    prog["bloques"]["recursos"] = "confirmado"
    almacen.anotar(prog, "exportada: x.docx")
    assert almacen.estado(prog) == "exportada" and almacen.ultima_exportacion(prog)
    almacen.marcar_cambio(prog)
    assert almacen.estado(prog) == "en_curso" and almacen.texto_estado(prog) == "En curso · 5 de 5"
    almacen.marcar_cambio(prog)
    assert len(prog["historial"]) == 2, "solo se anota una vez tras cada exportación"
