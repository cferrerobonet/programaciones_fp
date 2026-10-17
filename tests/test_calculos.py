"""Cálculos (RF-04): pesos, reparto de centro por RA, límites, tabla 4.1, modalidad y porcentajes."""
from decimal import Decimal

import pytest

from programaciones import calculos

RAS = [1, 2, 3, 4, 5, 6]


def test_peso_un_decimal_y_redondeo_en_la_mitad():
    assert calculos.peso(24, 166) == Decimal("14.5")
    assert calculos.peso(7, 166) == Decimal("4.2")
    assert calculos.peso(5, 166) == Decimal("3.0")
    assert calculos.peso(1, 8) == Decimal("12.5")      # 12,5 exacto
    assert calculos.peso(1, 16) == Decimal("6.3")      # 6,25 → 6,3
    assert calculos.formato_peso(Decimal("14.5")) == "14,5 %"


def test_porcentajes_enteros_empresa_hacia_arriba(prog):
    assert calculos.porcentaje_empresa(prog, 166) == 38   # 63/166 = 37,95
    assert calculos.porcentaje_centro(prog, 166) == 62
    prog["empresa"] = {"4": 17, "7": 10}
    assert calculos.porcentaje_empresa(prog, 166) == 17   # 27/166 = 16,27


def test_reparto_a_partes_iguales_como_piict(prog):
    r = calculos.reparto(prog, RAS)
    assert r[1] == 34 and r[2] == 41 and r[5] == 0
    assert float(r[3]) == pytest.approx(7.333, abs=1e-3)
    assert float(r[4]) == pytest.approx(9.333, abs=1e-3)
    assert float(r[6]) == pytest.approx(11.333, abs=1e-3)


def test_propuesta_al_entero_mas_cercano_y_el_resto_al_ra_con_mas_horas(prog):
    """CarlosFB, 2026-10-17: PIICT 7,33 / 9,33 / 11,33 → 7 / 9 / 12."""
    prop = calculos.propuesta_centro(prog, RAS)
    assert (prop[3], prop[4], prop[6]) == (7, 9, 12)
    assert (prop[1], prop[2], prop[5]) == (34, 41, 0)
    assert sum(prop.values()) == calculos.horas_centro(prog) == 103


def test_resto_negativo_va_al_mayor_redondeado():
    p = {"unidades": [{"id": "u1", "horas": 5, "elemento": "e1"}, {"id": "u2", "horas": 5, "elemento": "e2"}],
         "elementos": [{"id": "e1", "ra": [1, 2]}, {"id": "e2", "ra": [2, 3]}]}
    # repartos 2,5 / 5 / 2,5 → 3 / 5 / 3 = 11: sobra 1, se quita al mayor de los redondeados (el RA1, por orden)
    prop = calculos.propuesta_centro(p, [1, 2, 3])
    assert sum(prop.values()) == 10 and prop[2] == 5


def test_el_ajuste_del_profesor_manda(prog):
    c = calculos.centro(prog, RAS)
    assert (c[3], c[4], c[6]) == (8, 10, 10)


def test_limites(prog):
    lim = calculos.limites(prog, RAS)
    assert lim[1] == (0, 68)           # sin elementos exclusivos; 24 + 16 + 12 + 16
    assert lim[6] == (4, 26)           # EXAMEN 0 es solo suyo
    assert lim[5] == (0, 0)


def test_tabla41_y_modalidad(prog):
    filas = {f.ra: f for f in calculos.tabla41(prog, RAS)}
    assert (filas[1].total, filas[1].modalidad) == (34, "Centro")
    assert (filas[2].total, filas[2].modalidad) == (53, "Mixto")
    assert (filas[5].total, filas[5].modalidad) == (13, "Empresa")
    assert sum(f.total for f in filas.values()) == 166


@pytest.mark.parametrize("centro, empresa, modalidad, pct", [
    (10, 4, "Mixto", (71, 29)), (27, 4, "Mixto", (87, 13)), (21, 3, "Mixto", (87, 13)), (20, 3, "Mixto", (87, 13)),
    (34, 0, "Centro", None), (0, 13, "Empresa", None), (0, 0, "-", None),
])
def test_porcentajes_de_cada_ra_de_la_tabla_41(centro, empresa, modalidad, pct):
    """Los ejemplos de CarlosFB (2026-10-17): solo los RA mixtos llevan %, que suman siempre 100."""
    f = calculos.FilaRA(1, centro, empresa)
    assert f.modalidad == modalidad and f.porcentajes == pct
    if pct:
        assert sum(pct) == 100
    assert calculos.horas_o_guion(0) == "-" and calculos.horas_o_guion(13) == "13"
    assert calculos.formato_pct(71) == "71 %" and calculos.formato_pct(None) == "-"


def test_un_ra_sin_horas_da_el_aviso_v10(prog, cat):
    """Un RA con 0 h de centro y 0 h de empresa no debería existir: aviso rojo V-10."""
    from programaciones import validacion
    prog["empresa"].pop("5")
    assert calculos.tabla41(prog, RAS)[4].modalidad == "-"
    avisos = validacion.validar(prog, cat.ficha("SEA", "0517", 2))
    assert any(a.id == "V-10" and "RA5" in a.mensaje and a.gravedad == validacion.ROJA for a in avisos)


@pytest.mark.parametrize("ras, esperado", [
    ([1], "RA1"), ([2, 1], "RA1 y RA2"), ([3, 4, 6], "RA3, RA4 y RA6"), ([4, 5, 6, 7], "RA4, RA5, RA6 y RA7"),
    ([2, 3, 4, 5, 6], "RA2 → RA6"), ([], ""),
])
def test_lista_de_ra(ras, esperado):
    assert calculos.lista_ra(ras) == esperado


def test_peso_ajustado_por_el_profesor():
    assert calculos.peso_efectivo({"peso_ajustado": {"valor": 4.2}}, 15, 166) == Decimal("4.2")
    assert calculos.peso_efectivo({}, 15, 166) == Decimal("9.0")
    assert calculos.formato_peso_ajustado({"valor": 2.15}) == "2,15 %"
    assert calculos.formato_peso_ajustado({"valor": 15}) == "15 %"
    assert calculos.formato_peso_ajustado({"valor": 20, "texto": "1,25 % / x práctica"}) == "1,25 % / x práctica"


def test_porcentaje_del_curso_de_un_ra():
    assert calculos.pct_curso(29, 166) == "17,5 %"
