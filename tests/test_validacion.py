"""Validaciones V-01 a V-11: cada una con un caso que la cumple y otro que no."""
import copy

import pytest

from programaciones import validacion
from programaciones.catalogo import Ficha


def ficha(**cambios):
    datos = dict(sigla="ZZ", grado="GS", familia="Familia ficticia", ciclo_nombre="Ciclo ficticio",
                 titulo="Técnico Superior en Pruebas", curso=2, codigo="0991", codigo_horario="0991",
                 nombre="Módulo ficticio", horas=166, h_sem=5, tipo="propio", modulo_id="0991",
                 ra=[{"n": n, "texto": f"RA ficticio {n}.", "criterios": [{"letra": "a", "texto": "Se ha hecho."}]}
                     for n in range(1, 7)], competencias_modulo=["a"], fuente_ra="BOE-A-2000-1")
    datos.update(cambios)
    return Ficha(**datos)


def ids(prog, f=None, **kw):
    return {a.id for a in validacion.validar(prog, f or ficha(), **kw)}


def test_programacion_ficticia_sin_avisos_rojos(prog):
    prog["bloques"] = {k: "confirmado" for k in prog["bloques"]}
    assert not validacion.bloquean(validacion.validar(prog, ficha()))


@pytest.mark.parametrize("cambio, ident", [
    (lambda p: p["unidades"][0].update(horas=5), "V-01"),
    (lambda p: [e.update(ra=[x for x in e["ra"] if x != 1]) for e in p["elementos"]], "V-02"),
    (lambda p: p["unidades"][0].update(trimestre=4), "V-03"),
    (lambda p: p["unidades"][0].update(elemento="no-existe"), "V-03"),
    (lambda p: p["elementos"][0].update(ra=[]), "V-03"),
    (lambda p: p["elementos"][0].update(ra=[9]), "V-03"),
    (lambda p: p["centro_ajustado"].update({"6": 30}), "V-04"),
    (lambda p: p["centro_ajustado"].update({"3": 7}), "V-04"),
    (lambda p: p.update(profesorado=[" "]), "V-05"),
    (lambda p: p["bloques"].update(unidades="heredado"), "V-06"),
    (lambda p: p["ra_competencias"].pop("5"), "V-07"),
    (lambda p: [u.update(trimestre=1) for u in p["unidades"]], "V-09"),
    (lambda p: p["empresa"].pop("5"), "V-10"),
])
def test_cada_regla_salta(prog, cambio, ident):
    prog["bloques"] = {k: "confirmado" for k in prog["bloques"]}
    prog["unidades"][-1]["trimestre"] = 3   # sin trimestre vacío de partida (V-09)
    assert ident not in ids(prog)
    p = copy.deepcopy(prog)
    cambio(p)
    assert ident in ids(p)


def test_v08_cambios_de_curriculo_ambar(prog):
    avisos = validacion.validar(prog, ficha(), cambios_de_curriculo=["RA1 de 0991: criterio a) cambia"])
    v08 = [a for a in avisos if a.id == "V-08"]
    assert v08 and v08[0].gravedad == validacion.AMBAR


def test_v11_dato_que_falta_en_el_catalogo(prog):
    assert "V-11" in ids(prog, ficha(pendientes=["Sin fuente de los RA (ficticio)"]))


def test_ambar_no_bloquea(prog):
    prog["bloques"] = {k: "confirmado" for k in prog["bloques"]}
    for u in prog["unidades"]:
        u["trimestre"] = 1
    avisos = validacion.validar(prog, ficha())
    assert {a.id for a in avisos} == {"V-09"} and not validacion.bloquean(avisos)


def test_v12_pesos_ajustados_que_no_suman_el_centro(prog):
    prog["bloques"] = {k: "confirmado" for k in prog["bloques"]}
    prog["unidades"][-1]["trimestre"] = 3
    calculado = {e["id"]: float(validacion.calculos.peso(h, 166))
                 for e in prog["elementos"] for i, h in validacion.calculos.horas_elementos(prog).items() if i == e["id"]}
    # ajustes que reparten el 62 % de centro de otra forma: válidos
    prog["elementos"][0]["peso_ajustado"] = {"valor": calculado["e0"] + 1}
    prog["elementos"][1]["peso_ajustado"] = {"valor": calculado["e1"] - 1}
    assert "V-12" not in ids(prog)
    prog["elementos"][1]["peso_ajustado"] = {"valor": 1}
    assert "V-12" in ids(prog)


def test_v15_elemento_sin_nombre_en_una_unidad_ambar(prog):
    """Un elemento sin nombre que ya usa alguna unidad saldría con su celda vacía en la tabla 4. Mientras se crea en la
    interfaz (sin unidades) no avisa."""
    prog["bloques"] = {k: "confirmado" for k in prog["bloques"]}
    prog["unidades"][-1]["trimestre"] = 3
    prog["elementos"].append({"id": "e99", "tipo": "E", "nombre": "", "ra": [1]})
    assert "V-15" not in ids(prog)
    prog["elementos"][1]["nombre"] = " "
    avisos = [a for a in validacion.validar(prog, ficha()) if a.id == "V-15"]
    assert len(avisos) == 1 and avisos[0].gravedad == validacion.AMBAR and not validacion.bloquean(avisos)
    assert avisos[0].mensaje.startswith("«UD02. Unidad ficticia 2» y 1 más: su elemento de evaluación no tiene nombre")


def test_v16_enunciados_de_ra_del_documento_distintos_mientras_el_bloque_sigue_heredado(prog):
    prog["ra_documento"] = {"2": "Enunciado ficticio que no es el oficial.", "4": "Otro enunciado ficticio.",
                            "9": "RA que el módulo no tiene."}
    prog["bloques"]["ra_competencias"] = "heredado"
    v16 = [a for a in validacion.validar(prog, ficha()) if a.id == "V-16"]
    assert len(v16) == 1 and v16[0].gravedad == validacion.AMBAR
    assert v16[0].mensaje == ("RA2 y RA4: el enunciado del documento importado no es el del currículo; el documento "
                              "se regenera con el oficial")
    prog["bloques"]["ra_competencias"] = "confirmado"
    assert "V-16" not in ids(prog)
