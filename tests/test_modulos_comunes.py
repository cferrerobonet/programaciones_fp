"""Módulos que están en varios ciclos o con varios códigos y optativos ofertados (ADR-043, CarlosFB 2026-10-21).

- Un módulo se reconoce por cualquiera de sus códigos: el del horario de su ciclo («1665031»), el general del módulo
  («1665»), los que no son de cuatro cifras («CV0015») y el de la casilla de un optativo («CVOPS031»), que pueden
  compartir varios optativos: los distingue el nombre.
- Cada optativo que oferta el centro es un módulo programable, con sus RA; la clave que guarda la programación es su
  identificador («OPT-EE-IA») y el código que se ve, el de la casilla.
- «Copiar a otro ciclo»: la programación de un módulo común de un ciclo sirve de base para la de otro.
"""
import pytest

from conftest import programacion_minima
from programaciones import documento, herencia, importar_docx, incrustar
from programaciones.contexto import modulos_del_catalogo


@pytest.mark.parametrize("sigla, curso, codigo, clave", [
    ("SEA", 2, "1665031", "1665031"), ("SEA", 2, "1665", "1665031"), ("ADM", 2, "1708", "1708001"),
    ("SEA", 1, "0179", "0179"), ("ADM", 1, "CV0015", "CV0015"), ("SEA", 1, "0526", "0526"),
    ("SEA", 2, "OPT-EE-IA", "OPT-EE-IA"), ("AUT", 2, "CVOPS192", None), ("SEA", 1, "9999", None),
])
def test_cualquier_codigo_del_modulo(cat, sigla, curso, codigo, clave):
    assert cat.resolver(sigla, codigo, curso) == clave


def test_el_codigo_de_la_casilla_lo_decide_el_nombre(cat):
    assert cat.resolver("AUT", "CVOPS192", 2, "Peritación de daños y realización de presupuestos") == "OPT-TMV-PERITACION"
    assert cat.resolver("AUT", "CVOPS192", 2, "Inglés oral para entornos profesionales") == "OPT-INGLES-ORAL"
    assert cat.resolver("SEA", "CVOPS141", 2) == "OPT-EE-FV"   # una sola con ese código: no hace falta el nombre


def test_los_optativos_ofertados_son_modulos_con_sus_ra(cat):
    """La casilla «Módulo optativo» deja paso a cada optativo ofertado, con el código de la casilla a la vista."""
    sea2 = {m.codigo: m for m in modulos_del_catalogo(cat) if (m.sigla, m.curso) == ("SEA", 2)}
    assert "CVOPS031" not in sea2
    assert {k: sea2[k].mostrar for k in ("OPT-INGLES-ORAL", "OPT-EE-IA", "OPT-EE-FV")} == \
        {"OPT-INGLES-ORAL": "CVOPS031", "OPT-EE-IA": "CVOPS031", "OPT-EE-FV": "CVOPS141"}
    f = cat.ficha("AUT", "OPT-TMV-PERITACION", 2)
    assert (f.codigo, f.clave, f.tipo, f.horas, len(f.ra)) == ("CVOPS192", "OPT-TMV-PERITACION", "optativo", 100, 17)
    assert cat.ficha("ADM", "OPT-INGLES-ORAL", 2).codigo == "CVOPS001"
    # un ciclo sin optativos ofertados sigue con la casilla, pendiente
    iso = [m for m in modulos_del_catalogo(cat) if m.sigla == "ISO" and m.codigo.startswith("CVOP")]
    assert iso and all(m.pendiente for m in iso)


@pytest.mark.parametrize("sigla, n, clave", [
    ("SEA", 2, "1665031"), ("SEA", 2, "1708031"), ("ADM", 1, "CV0015"), ("AUT", 2, "OPT-TMV-PERITACION"),
    ("SEA", 2, "OPT-INGLES-ORAL"), ("SEA", 2, "OPT-EE-IA"),
])
def test_abrir_heredar_e_importar_con_el_nombre_que_pone_la_app(cat, curso, tmp_path, sigla, n, clave):
    """Antes, un Word sin datos de la app con códigos que no eran de cuatro cifras no se podía importar."""
    p = programacion_minima(cat, sigla, n, clave)
    d = documento.generar(p, cat, curso)
    nombre = documento.nombre_archivo(cat.ficha(sigla, clave, n))
    ruta = tmp_path / nombre
    ruta.write_bytes(incrustar.incrustar(d, p))
    o = herencia.leer_origen(ruta, cat)
    assert herencia.heredar(o.programacion, cat, "2027-2028", nombre).programacion["modulo"] == clave
    r = importar_docx.importar(d, cat, nombre)
    assert (r["ciclo"], r["curso"], r["modulo"]) == (sigla, n, clave)


def test_word_con_el_codigo_general_del_modulo(cat, curso):
    d = documento.generar(programacion_minima(cat, "SEA", 2, "1665031"), cat, curso)
    nombre = "SEA 2 - 1665 - Digitalización aplicada al sistema productivo.docx"
    assert importar_docx.importar(d, cat, nombre)["modulo"] == "1665031"
    # con el módulo elegido ya no avisa de «módulo distinto»: 1665 y 1665031 son el mismo
    assert importar_docx.importar(d, cat, nombre, ("SEA", 2, "1665031"))["modulo"] == "1665031"


def test_codigo_que_no_es_del_ciclo_avisa_claro(cat, curso):
    d = documento.generar(programacion_minima(cat, "SEA", 2, "0517"), cat, curso)
    with pytest.raises(importar_docx.NoEsProgramacion, match="9999 no es un módulo de SEA 2.º"):
        importar_docx.importar(d, cat, "SEA 2 - 9999 - Algo.docx")


def test_modulo_distinto_nombra_los_ciclos(cat, curso):
    d = documento.generar(programacion_minima(cat, "SEA", 1, "0179"), cat, curso)
    with pytest.raises(importar_docx.ModuloDistinto, match="0179 de SEA 1.º y está elegido el 0179 de STI 1.º"):
        importar_docx.importar(d, cat, "SEA 1 - 0179 - Inglés profesional GS.docx", ("STI", 1, "0179"))


@pytest.mark.parametrize("de, a", [
    (("SEA", 1, "0179"), ("STI", 1, "0179")), (("SEA", 2, "1665031"), ("ADM", 2, "1665001")),
    (("SEA", 2, "OPT-INGLES-ORAL"), ("AUT", 2, "OPT-INGLES-ORAL")),
])
def test_copiar_a_otro_ciclo(cat, de, a):
    """Lo del profesor se copia; las competencias de cada RA, no (son las letras del título de origen)."""
    p = programacion_minima(cat, *de)
    h = herencia.heredar(p, cat, "2027-2028", "base.docx", a)
    n = h.programacion
    assert (n["ciclo"], n["curso"], n["modulo"]) == a
    assert n["unidades"] == p["unidades"] and n["elementos"] == p["elementos"]
    assert n["ra_competencias"] == {} and n["bloques"]["ra_competencias"] == "vacio"
    assert any("marca las competencias" in x for x in h.avisos)
    assert f"copiada a {a[0]} {a[1]}.º" in n["historial"][0]["accion"]


def test_copiar_a_otro_ciclo_solo_el_mismo_modulo(cat):
    with pytest.raises(ValueError, match="no son el mismo módulo"):
        herencia.heredar(programacion_minima(cat, "SEA", 2, "0517"), cat, "2027-2028", "x.docx", ("STI", 1, "0179"))
