"""Validaciones V-xx de una programación (docs/DOCUMENTO_GENERADO.md, «Validaciones»).

Rojas: bloquean la exportación definitiva. Ámbar: solo avisan. La vista previa se genera siempre.
"""
from __future__ import annotations

from dataclasses import dataclass

from programaciones import calculos
from programaciones.catalogo import Ficha

ROJA, AMBAR = "roja", "ámbar"
TOLERANCIA_PESOS = 0.5   # puntos: los pesos calculados llevan un decimal y no siempre suman exacto


@dataclass(frozen=True)
class Aviso:
    id: str
    gravedad: str
    mensaje: str


def _trimestres(u: dict) -> list[int]:
    t = u.get("trimestre")
    return list(t) if isinstance(t, list) else [t] if t is not None else []


def validar(prog: dict, ficha: Ficha, cambios_de_curriculo: list[str] | None = None) -> list[Aviso]:
    """Avisos de la programación frente a la ficha del módulo. `cambios_de_curriculo`: los que el profesor aún no ha
    aceptado (ADR-015)."""
    out: list[Aviso] = []

    def aviso(ident, gravedad, mensaje):
        out.append(Aviso(ident, gravedad, mensaje))

    ras = ficha.numeros_ra
    H = ficha.horas
    unidades, elementos = prog.get("unidades", []), prog.get("elementos", [])
    ids_elementos = {e["id"] for e in elementos}
    empresa = {int(k): int(v or 0) for k, v in (prog.get("empresa") or {}).items()}

    # V-01 · horas
    total = calculos.horas_centro(prog) + calculos.horas_empresa(prog)
    if total != H:
        aviso("V-01", ROJA, f"Unidades ({calculos.horas_centro(prog)} h) + empresa ({calculos.horas_empresa(prog)} h) "
                            f"= {total} h; el módulo tiene {H} h")
    # V-02 · cada RA evaluado
    en_elementos = {int(r) for e in elementos for r in e.get("ra", [])}
    for r in ras:
        if r not in en_elementos and not empresa.get(r):
            aviso("V-02", ROJA, f"RA{r} no está en ningún elemento de evaluación ni en empresa")
    # V-03 · unidades y elementos completos
    for u in unidades:
        nombre = u.get("titulo") or u.get("id")
        if not u.get("horas"):
            aviso("V-03", ROJA, f"«{nombre}»: sin horas")
        if not _trimestres(u) or any(t not in (1, 2, 3) for t in _trimestres(u)):
            aviso("V-03", ROJA, f"«{nombre}»: sin trimestre (1-3)")
        if u.get("elemento") not in ids_elementos:
            aviso("V-03", ROJA, f"«{nombre}»: sin elemento de evaluación")
    for e in elementos:
        if not e.get("ra"):
            aviso("V-03", ROJA, f"«{e.get('nombre') or e['id']}»: sin RA")
        fuera = [r for r in e.get("ra", []) if int(r) not in ras]
        if fuera:
            aviso("V-03", ROJA, f"«{e.get('nombre') or e['id']}»: RA que no tiene el módulo ({fuera})")
    # V-04 · horas de centro por RA dentro de sus límites y cuadradas
    centro = calculos.centro(prog, ras)
    lim = calculos.limites(prog, ras)
    for r in ras:
        mn, mx = lim[r]
        if not mn <= centro[r] <= mx:
            aviso("V-04", ROJA, f"RA{r}: {centro[r]} h de centro, fuera de sus límites ({mn}-{mx} h)")
    if sum(centro.values()) != calculos.horas_centro(prog):
        aviso("V-04", ROJA, f"Las horas de centro de los RA suman {sum(centro.values())} h; las unidades, "
                            f"{calculos.horas_centro(prog)} h")
    # V-05 · profesorado
    if not [p for p in prog.get("profesorado", []) if p.strip()]:
        aviso("V-05", ROJA, "Sin profesorado")
    # V-06 · bloques heredados sin confirmar
    for bloque, estado in (prog.get("bloques") or {}).items():
        if estado == "heredado":
            aviso("V-06", ROJA, f"Bloque «{bloque}» heredado sin confirmar")
    # V-07 · competencias de cada RA
    rc = prog.get("ra_competencias") or {}
    for r in ras:
        if not rc.get(str(r)):
            aviso("V-07", ROJA, f"RA{r} sin competencias en la tabla del apartado 3")
    # V-08 · cambios de currículo sin aceptar
    if cambios_de_curriculo:
        aviso("V-08", AMBAR, f"{len(cambios_de_curriculo)} cambios del currículo sin aceptar: se exportaría con la "
                             "versión anterior")
    # V-09 · trimestre vacío
    usados = {t for u in unidades for t in _trimestres(u)}
    for t in (1, 2, 3):
        if unidades and t not in usados:
            aviso("V-09", AMBAR, f"{t}.er trimestre sin unidades" if t != 2 else "2.º trimestre sin unidades")
    # V-10 · RA sin horas (ni centro ni empresa): sin modalidad posible
    for fila in calculos.tabla41(prog, ras):
        if fila.total == 0:
            aviso("V-10", ROJA, f"RA{fila.ra} sin horas de centro ni de empresa")
    # V-12 · pesos ajustados por el profesor: suman el % de centro del módulo
    if any(e.get("peso_ajustado") for e in elementos):
        h_el = calculos.horas_elementos(prog)
        suma = sum(calculos.peso_efectivo(e, h_el.get(e["id"], 0), H) for e in elementos)
        objetivo = calculos.porcentaje_centro(prog, H)
        if abs(float(suma) - objetivo) > TOLERANCIA_PESOS:
            aviso("V-12", ROJA, f"Los pesos suman {str(suma).replace('.', ',')} %; las horas de centro son el "
                                f"{objetivo} % del módulo")
    # V-11 · dato que falta en el catálogo
    for motivo in ficha.pendientes:
        aviso("V-11", ROJA, f"Sin dato en el catálogo: {motivo}")
    return out


def bloquean(avisos: list[Aviso]) -> bool:
    return any(a.gravedad == ROJA for a in avisos)
