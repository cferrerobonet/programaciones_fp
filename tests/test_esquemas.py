"""Esquemas JSON del catálogo (src/programaciones/esquemas/)."""
import copy
import json

import pytest
from jsonschema import Draft202012Validator

import catalogo
from programaciones.catalogo import Catalogo

NOMBRES = ["catalogo_ciclo", "catalogo_modulo", "catalogo_normativa", "catalogo_fuentes", "catalogo_curso",
           "catalogo_version"]
HUELLA = "sha256:" + "0" * 64

MODULO = {
    "formato": "catalogo/3", "id": "0999", "codigo": "0999", "nombre": {"es": "Módulo ficticio"}, "tipo": "propio",
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


def _como_json(datos):
    """El YAML del curso como lo vería el esquema: fechas en texto y claves de curso como texto."""
    return json.loads(json.dumps(datos, default=str))


def test_curso_escolar_2026_2027_valido_y_completo():
    datos = Catalogo().curso_escolar("2026-2027")
    assert datos is not None, "catalogo/cursos/2026-2027.yaml"
    assert errores("catalogo_curso", _como_json(datos)) == []
    assert datos["fuente"]["documentos"], "cada curso escolar lleva su fuente"


@pytest.mark.parametrize("cambio", [
    lambda d: d["evaluaciones"].pop("tercera"),
    lambda d: d["formacion_empresa"]["GS"]["1"][0].update(jornada=12),
    lambda d: d.update(fuente={"documentos": [], "confirmado": "2026-10-17"}),
    lambda d: d["pendiente"].append({"ciclo": "GA", "curso": 3, "motivo": "x"}),
])
def test_curso_escolar_que_no_cumple_el_esquema(cambio):
    datos = _como_json(Catalogo().curso_escolar("2026-2027"))
    cambio(datos)
    assert errores("catalogo_curso", datos)


def test_version_del_catalogo():
    v = {"formato": "catalogo/3", "version": "2030.01.15.1", "fecha": "2030-01-15", "huella": HUELLA}
    assert errores("catalogo_version", v) == []
    for malo in ({**v, "version": "2030-01-15"}, {**v, "huella": "md5:1"}, {**v, "extra": 1}):
        assert errores("catalogo_version", malo)
