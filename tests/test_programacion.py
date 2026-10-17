"""Archivo de trabajo .programacion: esquema, ida y vuelta, escritura atómica y formatos."""
import json

import pytest

from programaciones import programacion


def test_nueva_es_valida():
    p = programacion.nueva("SEA", 2, "0517", "2030-2031", "2026.10.17", "2026-10-06")
    assert programacion.errores(p) == []
    assert set(p["bloques"].values()) == {"vacio"}


def test_ida_y_vuelta(tmp_path, prog):
    ruta = tmp_path / "SEA 2 - 0517 - Ficticio.programacion"
    programacion.escribir(ruta, prog)
    assert programacion.leer(ruta) == prog
    assert [p.name for p in tmp_path.iterdir()] == [ruta.name]   # sin temporales


def test_escribir_no_toca_el_archivo_si_no_es_valido(tmp_path, prog):
    ruta = tmp_path / "x.programacion"
    programacion.escribir(ruta, prog)
    antes = ruta.read_bytes()
    malo = dict(prog, curso=3)
    with pytest.raises(programacion.ProgramacionNoValida):
        programacion.escribir(ruta, malo)
    assert ruta.read_bytes() == antes


@pytest.mark.parametrize("cambio", [
    lambda p: p.update(formato="programaciones/9"),
    lambda p: p.update(ciclo="sea"),
    lambda p: p["unidades"][0].update(trimestre=5),
    lambda p: p["elementos"][0].update(tipo="X"),
    lambda p: p["empresa"].update({"2": -1}),
    lambda p: p["ra_competencias"].update({"1": ["A"]}),
    lambda p: p["recursos"].append({"texto": "x", "nivel": 7}),
    lambda p: p.update(extra=1),
])
def test_rechaza_lo_que_no_cumple_el_esquema(tmp_path, prog, cambio):
    cambio(prog)
    ruta = tmp_path / "x.programacion"
    ruta.write_text(json.dumps(prog), encoding="utf-8")
    with pytest.raises(programacion.ProgramacionNoValida):
        programacion.leer(ruta)


def test_huella_canonica(prog):
    otra = json.loads(json.dumps(prog, sort_keys=False))
    assert programacion.huella(prog) == programacion.huella(otra)
    otra["profesorado"] = ["Otra persona ficticia"]
    assert programacion.huella(prog) != programacion.huella(otra)


def test_trimestre_de_varios_trimestres(prog):
    prog["unidades"][0]["trimestre"] = [1, 2]
    assert programacion.errores(prog) == []
