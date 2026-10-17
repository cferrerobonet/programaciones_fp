"""Propuestas para una programación nueva desde cero: unidades desde los contenidos básicos (CarlosFB, 2026-10-17)."""
import pytest

from programaciones import propuesta


@pytest.mark.parametrize("pesos, total, esperado", [
    ([1, 1, 1], 9, [3, 3, 3]),
    ([1, 2, 1], 166, [42, 82, 42]),       # proporcional, al menos 1 cada uno, suma exacta
    ([100, 1], 10, [9, 1]),               # nunca 0 horas
    ([5, 5, 5], 2, [1, 1, 0]),            # menos horas que unidades
    ([], 30, []),
])
def test_reparto_de_horas(pesos, total, esperado):
    r = propuesta.reparto(pesos, total)
    assert r == esperado and (not pesos or sum(r) == min(total, sum(r)))


def test_trimestre_por_el_punto_medio():
    assert [propuesta.trimestre(i, 10, 90) for i in (0, 25, 30, 55, 60, 80)] == [1, 2, 2, 3, 3, 3]


def test_unidades_desde_la_ficha(cat):
    ficha = cat.ficha("SEA", "0517", 2)
    assert ficha.contenidos, "0517 tiene contenidos básicos en el catálogo"
    us = propuesta.unidades(ficha)
    assert len(us) == len(ficha.contenidos) and sum(u["horas"] for u in us) == ficha.horas
    assert us[0]["titulo"].startswith("UD01. ") and all(u["elemento"] == "" for u in us)
    assert len({u["id"] for u in us}) == len(us)


def test_sin_contenidos_no_hay_propuesta(cat):
    ficha = cat.ficha("SEA", "0526", 2)          # el Proyecto no tiene contenidos básicos
    assert not ficha.contenidos and propuesta.unidades(ficha) == []


def test_competencias_propuestas_y_diferencias(cat):
    import dataclasses

    ficha = dataclasses.replace(cat.ficha("SEA", "0517", 2), propuesta_competencias={1: ["a", "b"], 2: ["d"]})
    assert propuesta.competencias(ficha) == {"1": ["a", "b"], "2": ["d"]}
    assert propuesta.difieren({"ra_competencias": {"1": ["b", "a"], "2": ["d"]}}, ficha) == []
    assert propuesta.difieren({"ra_competencias": {"1": ["a"]}}, ficha) == [1, 2]
    sin = dataclasses.replace(ficha, propuesta_competencias={})
    assert propuesta.competencias(sin) == {} and propuesta.difieren({"ra_competencias": {}}, sin) == []
