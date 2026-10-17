"""Lector del catálogo curricular en la app: ciclos, módulos, normativa y curso escolar (solo lectura).

El catálogo lo genera `scripts/catalogo.py construir` (docs/CATALOGO_Y_FUENTES.md). Aquí solo se lee:
- La carpeta por defecto es la del repositorio (`catalogo/`); con la app empaquetada y el catálogo remoto (F5), la que
  diga `PROGRAMACIONES_CATALOGO` o la que se le pase.
- Los textos se devuelven en el idioma pedido (hoy, «es»: ADR-013) y, si la fuente tiene una errata corregida
  (`corregido`), el texto corregido, que es el que va al documento (CarlosFB, 2026-10-17).
- Un dato que falta en la fuente llega con `pendiente`: la ficha lo junta en `pendientes` para la validación V-11.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
ESQUEMAS = Path(__file__).resolve().parent / "esquemas"


def carpeta_por_defecto() -> Path:
    if os.environ.get("PROGRAMACIONES_CATALOGO"):
        return Path(os.environ["PROGRAMACIONES_CATALOGO"])
    return RAIZ / "catalogo"


def _leer(p: Path):
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def texto(obj: dict | None, idioma: str = "es") -> str:
    """Texto de un objeto por idioma ({es: …}); el de «es» si no hay traducción."""
    if not obj:
        return ""
    return obj.get(idioma) or obj.get("es", "")


def texto_documento(elem: dict, idioma: str = "es") -> str:
    """El texto que va al documento: el corregido si la fuente tiene una errata, si no el literal."""
    return texto(elem.get("corregido") or elem["texto"], idioma)


RE_CITA = re.compile(r"^((?:Real Decreto|Ley Orgánica|Decreto|DECRETO|Orden|ORDEN)\s+\d+/\d{4}),\s+de\s+(\d{1,2}\s+de\s+"
                     r"[a-záéíóú]+)\b")


@dataclass
class Norma:
    id: str
    titulo: str
    fecha: str
    enlace: str
    diario: str
    ambito: str
    aplica: object
    curso_escolar: str | None = None

    @property
    def cita(self) -> str:
        """«Real Decreto 1127/2010, de 10 de septiembre» (o el título entero si no tiene esa forma)."""
        m = RE_CITA.match(self.titulo)
        return f"{m.group(1)}, de {m.group(2)}" if m else self.titulo.rstrip(".")

    @property
    def cita_corta(self) -> str:
        """«Real Decreto 1127/2010»."""
        m = RE_CITA.match(self.titulo)
        return m.group(1) if m else self.cita

    @property
    def resto_titulo(self) -> str:
        """El título sin la cita ni el punto final: «, por el que se establece el título de … mínimas»."""
        t = self.titulo.rstrip(".")
        return t[len(self.cita):] if t.startswith(self.cita) else ""

    def aplica_a(self, sigla: str, grado: str) -> bool:
        if self.aplica == "todos":
            return True
        if self.aplica in ("GM", "GS"):
            return self.aplica == grado
        return sigla in (self.aplica or [])


@dataclass
class Ficha:
    """Lo que el documento necesita de un módulo en un ciclo, ya resuelto (textos en el idioma pedido)."""
    sigla: str
    grado: str
    familia: str
    ciclo_nombre: str
    titulo: str
    curso: int
    codigo: str            # el del horario sin la «p» del Proyecto de 1.º: «0517», «0526»
    codigo_horario: str    # tal cual: «0526p»
    nombre: str            # el del Decreto 95/2026 (CarlosFB, 2026-10-17)
    horas: int
    h_sem: int
    tipo: str
    modulo_id: str | None
    ra: list[dict] = field(default_factory=list)          # [{n, texto, criterios: [{letra, texto}]}]
    competencias_modulo: list[str] = field(default_factory=list)
    fuente_ra: str | None = None                          # norma de la que salen los RA
    pendientes: list[str] = field(default_factory=list)

    @property
    def numeros_ra(self) -> list[int]:
        return [r["n"] for r in self.ra]


class Catalogo:
    """El catálogo de una carpeta. Carga perezosa: cada archivo se lee la primera vez que se pide."""

    def __init__(self, carpeta: Path | None = None):
        self.carpeta = Path(carpeta) if carpeta else carpeta_por_defecto()
        if not (self.carpeta / "normativa.yaml").is_file():
            raise FileNotFoundError(f"No hay catálogo en {self.carpeta}")
        self._ciclos: dict[str, dict] = {}
        self._modulos: dict[str, dict] = {}

    # -- archivos ----------------------------------------------------------------------------------------------------
    def ciclo(self, sigla: str) -> dict:
        if sigla not in self._ciclos:
            p = self.carpeta / "ciclos" / f"{sigla}.yaml"
            if not p.is_file():
                raise KeyError(f"Ciclo desconocido: {sigla}")
            self._ciclos[sigla] = _leer(p)
        return self._ciclos[sigla]

    def siglas(self) -> list[str]:
        return sorted(p.stem for p in (self.carpeta / "ciclos").glob("*.yaml"))

    def modulo(self, ident: str) -> dict:
        if ident not in self._modulos:
            p = self.carpeta / "modulos" / f"{ident}.yaml"
            if not p.is_file():
                raise KeyError(f"Módulo desconocido: {ident}")
            self._modulos[ident] = _leer(p)
        return self._modulos[ident]

    @cached_property
    def normas(self) -> dict[str, Norma]:
        d = _leer(self.carpeta / "normativa.yaml")
        return {n["id"]: Norma(id=n["id"], titulo=texto(n["titulo"]), fecha=n["fecha"], enlace=n["enlace"],
                               diario=n["diario"], ambito=n["ambito"], aplica=n["aplica"],
                               curso_escolar=n.get("curso_escolar")) for n in d["normas"]}

    def norma(self, ident: str) -> Norma:
        return self.normas[ident]

    @cached_property
    def version(self) -> str:
        """AAAA.MM.DD: la comprobación más reciente del catálogo (la versión publicada y firmada llega en F5)."""
        fechas = [str(self.ciclo(s).get("comprobado", "")) for s in self.siglas()]
        fechas.append(str(_leer(self.carpeta / "normativa.yaml").get("comprobado", "")))
        return max(fechas).replace("-", ".")

    def curso_escolar(self, curso: str) -> dict | None:
        """Fechas y periodos de un curso escolar (`cursos/AAAA-AAAA.yaml`) o None si aún no está dado de alta."""
        p = self.carpeta / "cursos" / f"{curso}.yaml"
        return _leer(p) if p.is_file() else None

    # -- consultas ---------------------------------------------------------------------------------------------------
    def entrada(self, sigla: str, codigo: str, curso: int | None = None) -> dict:
        """La fila del módulo en el horario del ciclo. «0526» con curso 1 es el «0526p» (Proyecto de 1.º)."""
        filas = self.ciclo(sigla)["modulos"]
        candidatas = [m for m in filas if m["codigo"] == codigo or m["codigo"].rstrip("p") == codigo]
        if curso is not None:
            candidatas = [m for m in candidatas if m["curso"] == curso] or candidatas
        if not candidatas:
            raise KeyError(f"{codigo} no es un módulo de {sigla}")
        return candidatas[0]

    def nombre_modulo(self, sigla: str, codigo: str) -> str:
        """Nombre del módulo en el ciclo: el del Decreto 95/2026 (portada, archivo y tabla del apartado 2)."""
        return texto(self.entrada(sigla, codigo)["nombre"])

    def ficha(self, sigla: str, codigo: str, curso: int | None = None, idioma: str = "es") -> Ficha:
        c = self.ciclo(sigla)
        e = self.entrada(sigla, codigo, curso)
        pendientes = []
        if e.get("pendiente"):
            pendientes.append(e["pendiente"])
        ra, comp, fuente = [], [], None
        if e.get("modulo"):
            m = self.modulo(e["modulo"])
            ra = [{"n": r["n"], "texto": texto_documento(r, idioma),
                   "criterios": [{"letra": x["letra"], "texto": texto_documento(x, idioma)} for x in r["criterios"]]}
                  for r in m["ra"]]
            comp = list(m.get("competencias_modulo", {}).get(sigla, []))
            fuente = m["fuente"]["norma"]
        elif not e.get("pendiente"):
            pendientes.append(f"{e['codigo']}: el catálogo no tiene sus RA")
        if c.get("pendiente_competencias"):
            pendientes.append(c["pendiente_competencias"])
        return Ficha(sigla=sigla, grado=c["grado"], familia=texto(c["familia"], idioma),
                     ciclo_nombre=texto(c["nombre"], idioma), titulo=texto(c["titulo"], idioma), curso=e["curso"],
                     codigo=e["codigo"].rstrip("p"), codigo_horario=e["codigo"], nombre=texto(e["nombre"], idioma),
                     horas=e["h_anuales"], h_sem=e["h_sem"], tipo=e["tipo"], modulo_id=e.get("modulo"), ra=ra,
                     competencias_modulo=comp, fuente_ra=fuente, pendientes=pendientes)

    def normativa(self, sigla: str, ambito: str, curso_escolar: str | None = None) -> list[Norma]:
        """Normas de un ámbito que se aplican al ciclo, por fecha creciente. Las resoluciones de un curso escolar solo
        entran en el suyo."""
        grado = self.ciclo(sigla)["grado"]
        out = [n for n in self.normas.values() if n.ambito == ambito and n.aplica_a(sigla, grado)
               and (n.curso_escolar is None or n.curso_escolar == curso_escolar)]
        return sorted(out, key=lambda n: (n.fecha, n.id))

    def diferencias(self, otro: Catalogo, sigla: str, codigo: str) -> list[str]:
        """Cambios de RA y criterios de un módulo entre este catálogo (el de la programación) y `otro` (el nuevo):
        la base de la ventana «Cambios en el currículo» (ADR-015)."""
        a, b = self.ficha(sigla, codigo), otro.ficha(sigla, codigo)
        out = []
        ra_a, ra_b = {r["n"]: r for r in a.ra}, {r["n"]: r for r in b.ra}
        for n in sorted(set(ra_a) | set(ra_b)):
            if n not in ra_b:
                out.append(f"RA{n} de {codigo}: ya no está")
            elif n not in ra_a:
                out.append(f"RA{n} de {codigo}: nuevo")
            else:
                if ra_a[n]["texto"] != ra_b[n]["texto"]:
                    out.append(f"RA{n} de {codigo}: enunciado nuevo")
                ca = {x["letra"]: x["texto"] for x in ra_a[n]["criterios"]}
                cb = {x["letra"]: x["texto"] for x in ra_b[n]["criterios"]}
                for letra in sorted(set(ca) | set(cb)):
                    if ca.get(letra) != cb.get(letra):
                        estado = "nuevo" if letra not in ca else "ya no está" if letra not in cb else "cambia"
                        out.append(f"RA{n} de {codigo}: criterio {letra}) {estado}")
        return out


def esquema(nombre: str) -> dict:
    return json.loads((ESQUEMAS / f"{nombre}.schema.json").read_text(encoding="utf-8"))
