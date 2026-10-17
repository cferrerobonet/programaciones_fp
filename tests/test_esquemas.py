"""Esquemas JSON del catálogo (src/programaciones/esquemas/)."""
import copy
import json

import pytest
from jsonschema import Draft202012Validator

import catalogo

NOMBRES = ["catalogo_ciclo", "catalogo_modulo", "catalogo_normativa", "catalogo_fuentes"]
HUELLA = "sha256:" + "0" * 64

MODULO = {
    "formato": "catalogo/1", "id": "0999", "codigo": "0999", "nombre": {"es": "Módulo ficticio"}, "tipo": "propio",
    "competencias_modulo": {"SEA": ["a", "b"]},
    "ra": [{"n": 1, "texto": {"es": "Monta instalaciones ficticias."},
            "criterios": [{"letra": "a", "texto": {"es": "Se ha montado la instalación ficticia."}}]}],
    "fuente": {"norma": "BOE-A-2000-1", "bloque": "Anexo I, módulo 0999", "version": "2000-01-01", "huella": HUELLA,
               "comprobado": "2026-10-17"},
}


def errores(nombre, datos):
    return list(Draft202012Validator(catalogo.esquema(nombre)).iter_errors(datos))


@pytest.mark.parametrize("nombre", NOMBRES)
def test_los_esquemas_son_validos(nombre):
    Draft202012Validator.check_schema(catalogo.esquema(nombre))


@pytest.mark.parametrize("nombre", NOMBRES)
def test_los_esquemas_son_json_con_id_propio(nombre):
    d = json.loads((catalogo.ESQUEMAS / f"{nombre}.schema.json").read_text(encoding="utf-8"))
    assert d["$id"].endswith(f"/{nombre}.schema.json")
    assert d["additionalProperties"] is False


def test_modulo_ficticio_valido():
    assert errores("catalogo_modulo", MODULO) == []


@pytest.mark.parametrize("cambio", [
    lambda m: m.pop("fuente"),
    lambda m: m["fuente"].update(huella="md5:123"),
    lambda m: m["ra"][0]["criterios"][0].update(letra="A"),
    lambda m: m["ra"][0].update(criterios=[]),
    lambda m: m["ra"][0]["texto"].update(es=""),
    lambda m: m.update(ra=[]),
    lambda m: m.update(tipo="otro"),
    lambda m: m.update(extra=1),
    lambda m: m["nombre"].update(fr="Module"),          # idiomas: es, va, en (ADR-013)
    lambda m: m["fuente"].update(norma="Real Decreto 1/2000"),
])
def test_modulo_no_valido(cambio):
    m = copy.deepcopy(MODULO)
    cambio(m)
    assert errores("catalogo_modulo", m)


def test_erratas_del_boe_se_guardan_aparte():
    m = copy.deepcopy(MODULO)
    m["ra"][0]["n_boe"] = 2
    m["ra"][0]["criterios"][0]["letra_boe"] = "ñ"
    assert errores("catalogo_modulo", m) == []


def test_ecp_pendiente_sin_codigo():
    ciclo_ecp = catalogo.esquema("catalogo_ciclo")["properties"]["correspondencias_ecp"]["items"]["properties"]["ecp"]
    v = Draft202012Validator({"$defs": catalogo.esquema("catalogo_ciclo")["$defs"], **ciclo_ecp})
    ok = [{"codigo": None, "texto": {"es": "Mantener algo ficticio."}, "uc": "UC0001_2",
           "pendiente": "La UC no está en el anexo I del RD 532/2025"}]
    assert list(v.iter_errors(ok)) == []
    assert list(v.iter_errors([{"codigo": "UC0001_2", "texto": {"es": "x"}, "uc": "UC0001_2"}]))


def test_correccion_de_errata_exige_su_motivo():
    m = copy.deepcopy(MODULO)
    crit = m["ra"][0]["criterios"][0]
    crit["corregido"] = {"es": "Se ha montado la instalación ficticia bien."}
    assert errores("catalogo_modulo", m)
    crit["correccion"] = "Errata ficticia de prueba"
    assert errores("catalogo_modulo", m) == []


def test_uc_con_errata_y_competencia_numerada():
    ciclo = catalogo.esquema("catalogo_ciclo")
    ecp = Draft202012Validator({"$defs": ciclo["$defs"], **ciclo["properties"]["correspondencias_ecp"]["items"]["properties"]["ecp"]})
    bien = {"codigo": "ECP0001_2", "texto": {"es": "Mantener algo ficticio."}, "uc": "UC0001_2", "uc_boe": "UC0001_3",
            "correccion": "Errata ficticia de prueba"}
    assert list(ecp.iter_errors([bien])) == []
    assert list(ecp.iter_errors([{k: v for k, v in bien.items() if k != "correccion"}]))
    comp = Draft202012Validator({"$defs": ciclo["$defs"], **ciclo["properties"]["competencias"]})
    assert list(comp.iter_errors([{"letra": "a", "numero_boe": 1, "texto": {"es": "Tramitar algo ficticio."}}])) == []
