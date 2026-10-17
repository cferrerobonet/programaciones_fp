"""Propuestas para una programación nueva desde cero (CarlosFB, 2026-10-17): lo que la app rellena para que el
profesor lo revise, nunca como definitivo (el bloque queda «heredado» hasta que lo confirma).

- **Unidades (apartado 4):** una por bloque de contenidos básicos del módulo (BOE o DOGV, en el catálogo), con las
  horas del módulo repartidas según la extensión de cada bloque y el trimestre por su posición en el curso. Sin
  elementos de evaluación: los pone el profesor.
- **Competencias de cada RA (apartado 3):** la propuesta de IA del catálogo (`propuesta_ra_competencias`, no
  oficial: el real decreto solo dice a qué competencias contribuye el módulo entero). Es también la que se ofrece con
  «Proponer corrección con IA» cuando la de una programación importada o heredada no coincide.
"""
from __future__ import annotations

import math

from .catalogo import Ficha


def reparto(pesos: list[int], total: int) -> list[int]:
    """`total` horas en enteros proporcionales a `pesos` (al menos 1 cada uno; restos mayores primero, y a igualdad,
    el primero). Siempre suman `total` si hay horas para todos."""
    n = len(pesos)
    if not n:
        return []
    if total < n:
        return [1 if k < total else 0 for k in range(n)]
    base = [1] * n
    libre, suma = total - n, sum(pesos) or n
    exacto = [libre * (p or 1) / suma for p in pesos]
    enteros = [math.floor(x) for x in exacto]
    faltan = libre - sum(enteros)
    for k in sorted(range(n), key=lambda k: (-(exacto[k] - enteros[k]), k))[:faltan]:
        enteros[k] += 1
    return [b + e for b, e in zip(base, enteros, strict=True)]


def trimestre(inicio: int, horas: int, total: int) -> int:
    """El trimestre del punto medio de la unidad, con el curso partido en tres tercios de horas."""
    if total <= 0:
        return 1
    medio = inicio + horas / 2
    return min(3, int(medio * 3 // total) + 1)


def unidades(ficha: Ficha) -> list[dict]:
    """Unidades del apartado 4 desde los contenidos básicos; vacía si el catálogo no los tiene."""
    if not ficha.contenidos:
        return []
    pesos = [len(b["titulo"]) + sum(len(p) for p in b["puntos"]) for b in ficha.contenidos]
    horas = reparto(pesos, ficha.horas)
    out, inicio = [], 0
    for k, (b, h) in enumerate(zip(ficha.contenidos, horas, strict=True), start=1):
        out.append({"id": f"u{k}", "titulo": f"UD{k:02d}. {b['titulo']}", "horas": h,
                    "trimestre": trimestre(inicio, h, ficha.horas), "elemento": ""})
        inicio += h
    return out


def competencias(ficha: Ficha) -> dict[str, list[str]]:
    """La propuesta de competencias por RA en el formato de la programación ({"1": ["a", "c"]}); vacía si no hay."""
    return {str(n): list(ficha.propuesta_competencias[n]) for n in ficha.numeros_ra if n in ficha.propuesta_competencias}


def difieren(prog: dict, ficha: Ficha) -> list[int]:
    """RA cuyas competencias en la programación no son las de la propuesta (sin propuesta, ninguno)."""
    prop = competencias(ficha)
    if not prop:
        return []
    actual = prog.get("ra_competencias") or {}
    return [n for n in ficha.numeros_ra if str(n) in prop and sorted(actual.get(str(n), [])) != sorted(prop[str(n)])]
