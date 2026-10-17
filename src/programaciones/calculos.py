"""Cálculos de la programación (RF-04): pesos, reparto de horas por RA, tabla 4.1, modalidad y porcentajes.

Puro y sin estado: recibe la programación (dict del archivo `.programacion`), las horas del módulo y los RA del
catálogo. Fórmulas y comprobación con PIICT en docs/MODELO_DE_DATOS.md §3.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction


def _clave(ra) -> str:
    return str(int(ra))


def horas_elementos(prog: dict) -> dict[str, int]:
    """h(e): suma de las horas de las unidades de cada elemento (los elementos sin unidades, 0)."""
    h = {e["id"]: 0 for e in prog.get("elementos", [])}
    for u in prog.get("unidades", []):
        if u.get("elemento") in h:
            h[u["elemento"]] += int(u.get("horas") or 0)
    return h


def horas_centro(prog: dict) -> int:
    return sum(int(u.get("horas") or 0) for u in prog.get("unidades", []))


def horas_empresa(prog: dict) -> int:
    return sum(int(v or 0) for v in prog.get("empresa", {}).values())


def peso(h: int, total: int) -> Decimal:
    """Peso de un elemento en %, con un decimal y redondeo al alza en la mitad (24/166 → 14,5)."""
    if not total:
        return Decimal("0.0")
    return (Decimal(h) * 100 / Decimal(total)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def formato_peso(p: Decimal) -> str:
    return f"{p:.1f}".replace(".", ",") + " %"


def peso_efectivo(elemento: dict, h: int, total: int) -> Decimal:
    """El peso que pone el profesor (`peso_ajustado`, CarlosFB 2026-10-17) o, si no, el calculado."""
    ajuste = elemento.get("peso_ajustado")
    return Decimal(str(ajuste["valor"])) if ajuste else peso(h, total)


def formato_peso_ajustado(ajuste: dict) -> str:
    """Peso del profesor tal como lo escribe: su texto («1,25 % / x práctica») o su valor con sus decimales."""
    if ajuste.get("texto"):
        return ajuste["texto"]
    return f"{Decimal(str(ajuste['valor'])).normalize():f}".replace(".", ",") + " %"


def pct_curso(horas_ra: int, total: int) -> str:
    """% del módulo de las horas totales de un RA, con un decimal (columna opcional «% del curso» de la tabla 4.1)."""
    return formato_peso(peso(horas_ra, total))


def porcentaje_empresa(prog: dict, total: int) -> int:
    """% de empresa del módulo, entero y redondeado hacia arriba (63/166 = 37,95 → 38)."""
    return math.ceil(Fraction(100 * horas_empresa(prog), total)) if total else 0


def porcentaje_centro(prog: dict, total: int) -> int:
    return 100 - porcentaje_empresa(prog, total)


def reparto(prog: dict, ras: list[int]) -> dict[int, Fraction]:
    """Horas de centro de cada RA a partes iguales: Σ h(e) / |R(e)| sobre los elementos que lo contienen."""
    h = horas_elementos(prog)
    out = {r: Fraction(0) for r in ras}
    for e in prog.get("elementos", []):
        rs = [int(r) for r in e.get("ra", []) if int(r) in out]
        for r in rs:
            out[r] += Fraction(h.get(e["id"], 0), len(rs))
    return out


def limites(prog: dict, ras: list[int]) -> dict[int, tuple[int, int]]:
    """(mínimo, máximo) de horas de centro de cada RA: las de sus elementos exclusivos y las de todos los que lo
    incluyen (regla 3 de la skill programacion-didactica, V-04)."""
    h = horas_elementos(prog)
    out = {r: (0, 0) for r in ras}
    for e in prog.get("elementos", []):
        rs = [int(r) for r in e.get("ra", []) if int(r) in out]
        for r in rs:
            mn, mx = out[r]
            out[r] = (mn + (h.get(e["id"], 0) if len(rs) == 1 else 0), mx + h.get(e["id"], 0))
    return out


def propuesta_centro(prog: dict, ras: list[int]) -> dict[int, int]:
    """Propuesta de horas de centro por RA (CarlosFB, 2026-10-17): cada reparto al entero más cercano y lo que sobre o
    falte para cuadrar las horas de centro va al RA con más horas de los que se han redondeado.

    PIICT: 7,33 / 9,33 / 11,33 → 7 / 9 / 12 (el profesor lo puede ajustar: en su programación, 8 / 10 / 10)."""
    exacto = reparto(prog, ras)
    out = {r: math.floor(v + Fraction(1, 2)) for r, v in exacto.items()}   # al más cercano; ,5 hacia arriba
    resto = round(sum(exacto.values())) - sum(out.values())
    if resto and out:
        redondeados = [r for r, v in exacto.items() if v.denominator != 1] or list(out)
        destino = max(redondeados, key=lambda r: (exacto[r], -r))
        out[destino] += resto
    return out


def centro(prog: dict, ras: list[int]) -> dict[int, int]:
    """Horas de centro definitivas: las que ajustó el profesor (`centro_ajustado`) o, si no, la propuesta."""
    ajuste = {int(k): int(v) for k, v in (prog.get("centro_ajustado") or {}).items()}
    prop = propuesta_centro(prog, ras)
    return {r: ajuste.get(r, prop[r]) for r in ras}


#: Modalidades que elige el profesor en la tabla 4.1 (ADR-030), en el orden del desplegable.
MODALIDADES = ("Centro", "Mixto", "Empresa")


def modalidad(h_centro: int, h_empresa: int) -> str:
    """«Centro», «Empresa» o «Mixto»; un RA sin horas (0/0, V-10) no tiene modalidad: «-»."""
    if h_centro == 0 and h_empresa == 0:
        return "-"
    if h_empresa == 0:
        return "Centro"
    if h_centro == 0:
        return "Empresa"
    return "Mixto"


@dataclass
class FilaRA:
    ra: int
    centro: int
    empresa: int
    #: La que eligió el profesor (ADR-030); vacía en las programaciones de antes, que la deducen de las horas.
    elegida: str = ""

    @property
    def total(self) -> int:
        return self.centro + self.empresa

    @property
    def modalidad(self) -> str:
        return self.elegida or modalidad(self.centro, self.empresa)

    @property
    def incoherencia(self) -> str:
        """Por qué la modalidad elegida no casa con las horas (V-13); vacío si casa o no se ha elegido."""
        if self.elegida == "Centro" and self.empresa:
            return f"modalidad Centro con {self.empresa} h de empresa"
        if self.elegida == "Empresa" and self.centro:
            return f"modalidad Empresa con {self.centro} h de centro"
        if self.elegida == "Mixto" and not (self.centro and self.empresa):
            return f"modalidad Mixto sin horas de {'centro' if not self.centro else 'empresa'}"
        return ""

    @property
    def porcentajes(self) -> tuple[int, int] | None:
        """(% centro, % empresa) del RA, solo si es «Mixto» (CarlosFB, 2026-10-17): % de empresa al entero más
        cercano (la mitad, hacia arriba) y % de centro = 100 − empresa, para que siempre sumen 100. Así salen los
        ejemplos de CarlosFB: 10 + 4 → 71/29; 27 + 4, 21 + 3 y 20 + 3 → 87/13 (con 21 + 3, el centro es 87,5)."""
        if self.modalidad != "Mixto" or not (self.centro and self.empresa):
            return None
        pe = math.floor(Fraction(100 * self.empresa, self.total) + Fraction(1, 2))
        return 100 - pe, pe


def tabla41(prog: dict, ras: list[int]) -> list[FilaRA]:
    """Ponderación de cada RA (apartado 4.1): horas totales = centro + empresa, modalidad y horas en empresa."""
    c = centro(prog, ras)
    emp = {int(k): int(v or 0) for k, v in (prog.get("empresa") or {}).items()}
    elegida = {int(k): v for k, v in (prog.get("modalidad") or {}).items() if v in MODALIDADES}
    return [FilaRA(r, c[r], emp.get(r, 0), elegida.get(r, "")) for r in ras]


def horas_o_guion(h: int) -> str:
    """Horas en la tabla 4.1: el número o «-» si es 0."""
    return str(h) if h else "-"


def formato_pct(n: int | None) -> str:
    return f"{n} %" if n is not None else "-"


def lista_ra(ras: list[int], rango_desde: int = 5) -> str:
    """«RA1 y RA2», «RA3, RA4 y RA6» o, con cinco o más seguidos, «RA2 → RA6» (como en las programaciones)."""
    ras = sorted(set(int(r) for r in ras))
    if not ras:
        return ""
    if len(ras) >= rango_desde and ras == list(range(ras[0], ras[-1] + 1)):
        return f"RA{ras[0]} → RA{ras[-1]}"
    nombres = [f"RA{r}" for r in ras]
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]
