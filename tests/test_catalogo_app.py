"""Lector del catálogo en la app (src/programaciones/catalogo.py) sobre el catálogo del repositorio."""
import shutil

import pytest
import yaml

from programaciones.catalogo import Catalogo, Norma


def test_ficha_de_un_modulo(cat):
    f = cat.ficha("SEA", "0517")
    assert (f.horas, f.h_sem, f.curso, f.grado) == (166, 5, 2, "GS")
    assert f.nombre.startswith("Procesos en instalaciones de infraestructuras comunes")
    assert f.numeros_ra == [1, 2, 3, 4, 5, 6] and f.pendientes == []
    assert f.competencias_modulo == ["a", "b", "d", "e", "f", "g", "h", "j", "k"]


def test_la_ficha_da_el_texto_corregido_de_las_erratas(cat):
    crit = cat.ficha("SEA", "0517").ra[0]["criterios"][0]["texto"]
    assert "de acuerdo con la normativa" in crit
    literal = cat.modulo("0517")["ra"][0]["criterios"][0]["texto"]["es"]
    assert "de acuerdo a la normativa" in literal


def test_proyecto_de_primero_y_de_segundo(cat):
    assert cat.ficha("SEA", "0526", 2).horas == 100
    p1 = cat.ficha("SEA", "0526", 1)
    assert (p1.horas, p1.codigo_horario, p1.codigo) == (35, "0526p", "0526")


def test_nombre_del_decreto_95_2026(cat):
    """CarlosFB, 2026-10-17: en la portada y el archivo, el nombre del Decreto 95/2026."""
    assert cat.nombre_modulo("ARI", "0959") == "Sistemas eléctricos, neumáticos e hidráulicos"
    assert cat.modulo("0959")["nombre"]["es"] == "Sistemas eléctricos neumáticos e hidráulicos"


def test_proyecto_de_gm_pendiente(cat):
    f = cat.ficha("IEA", next(m["codigo"] for m in cat.ciclo("IEA")["modulos"] if m["tipo"] == "proyecto"))
    assert f.pendientes and f.ra == []


def test_normativa_por_fecha_y_resolucion_de_su_curso(cat):
    est = cat.normativa("SEA", "estatal")
    assert [n.fecha for n in est] == sorted(n.fecha for n in est)
    assert all(n.id != "BOE-A-2024-10684" for n in est)          # RD 499/2024 es de GM
    aut = cat.normativa("SEA", "autonomico", "2026-2027")
    assert any(n.curso_escolar == "2026-2027" for n in aut)
    assert not any(n.curso_escolar for n in cat.normativa("SEA", "autonomico", "2030-2031"))


def test_cita_de_una_norma():
    n = Norma(id="BOE-A-2000-1", titulo="Real Decreto 1/2000, de 2 de enero, por el que se establece el título "
              "ficticio y se fijan sus enseñanzas mínimas.", fecha="2000-01-03", enlace="https://example.com",
              diario="BOE", ambito="estatal", aplica=["ZZ"])
    assert n.cita == "Real Decreto 1/2000, de 2 de enero"
    assert n.cita_corta == "Real Decreto 1/2000"
    assert n.resto_titulo == ", por el que se establece el título ficticio y se fijan sus enseñanzas mínimas"
    assert n.aplica_a("ZZ", "GS") and not n.aplica_a("YY", "GS")


def test_version_del_catalogo(cat):
    """AAAA.MM.DD o, con otro cambio el mismo día, AAAA.MM.DD.n (ADR-027: lo destapó el simulacro del vigía)."""
    from programaciones.catalogo_remoto import RE_VERSION

    assert RE_VERSION.match(cat.version) and cat.version.startswith(cat.fecha.replace("-", "."))


def test_diferencias_entre_dos_catalogos(cat, tmp_path):
    copia = tmp_path / "catalogo"
    shutil.copytree(cat.carpeta, copia)
    p = copia / "modulos" / "0517.yaml"
    m = yaml.safe_load(p.read_text(encoding="utf-8"))
    m["ra"][2]["criterios"][1]["texto"]["es"] = "Se ha cambiado un criterio (ficticio)."
    m["ra"][2]["criterios"].append({"letra": "z", "texto": {"es": "Se ha añadido un criterio ficticio."}})
    p.write_text(yaml.safe_dump(m, allow_unicode=True), encoding="utf-8")
    dif = cat.diferencias(Catalogo(copia), "SEA", "0517")
    assert dif == ["RA3 de 0517: criterio b) cambia", "RA3 de 0517: criterio z) nuevo"]


def test_carpeta_sin_catalogo(tmp_path):
    with pytest.raises(FileNotFoundError):
        Catalogo(tmp_path)
