"""Lector del catálogo curricular en la app: ciclos, módulos, normativa y curso escolar (solo lectura).

El catálogo lo genera `scripts/catalogo.py construir` (docs/CATALOGO_Y_FUENTES.md). Aquí solo se lee:
- La carpeta por defecto es la del repositorio (`catalogo/`) o, en la app empaquetada, la copia que lleva dentro
  (`PROGRAMACIONES_CATALOGO` la cambia). Los catálogos descargados y verificados (F5) los busca `catalogo_remoto.py`
  en la carpeta de datos y se leen igual, cada uno en su carpeta.
- La versión sale de `version.yaml` (ADR-027); `diferencias` y `diferencias_catalogo` comparan dos versiones (ADR-015).
- Los textos se devuelven en el idioma pedido (hoy, «es»: ADR-013) y, si la fuente tiene una errata corregida
  (`corregido`), el texto corregido, que es el que va al documento (CarlosFB, 2026-10-17).
- Un dato que falta en la fuente llega con `pendiente`: la ficha lo junta en `pendientes` para la validación V-11.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
ESQUEMAS = Path(__file__).resolve().parent / "esquemas"


def carpeta_por_defecto() -> Path:
    if os.environ.get("PROGRAMACIONES_CATALOGO"):
        return Path(os.environ["PROGRAMACIONES_CATALOGO"])
    if getattr(sys, "frozen", False):  # app de PyInstaller: el catálogo va en sus datos (Programaciones.spec)
        return Path(sys._MEIPASS) / "catalogo"  # type: ignore[attr-defined]
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
        """«todos», un grado («GM») o una lista de siglas y grados (["SEA"], ["GM", "GS"], ["GB"])."""
        if self.aplica == "todos":
            return True
        if self.aplica in ("GM", "GS", "GB"):
            return self.aplica == grado
        return sigla in (self.aplica or []) or grado in (self.aplica or [])


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
    contenidos: list[dict] = field(default_factory=list)  # [{titulo, puntos: [texto]}]: contenidos básicos por bloques
    #: Propuesta de IA (no oficial) de las competencias de cada RA en este ciclo: {n: [letras]} (CarlosFB, 2026-10-17)
    propuesta_competencias: dict[int, list[str]] = field(default_factory=dict)

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
    def _version(self) -> dict:
        """`version.yaml` (ADR-027): versión AAAA.MM.DD[.n], fecha y huella del contenido. Sin él (una copia de las
        pruebas o un catálogo de antes de F5), la versión es la comprobación más reciente de los ciclos y la normativa."""
        p = self.carpeta / "version.yaml"
        if p.is_file():
            return _leer(p) or {}
        fechas = [str(self.ciclo(s).get("comprobado", "")) for s in self.siglas()]
        fechas.append(str(_leer(self.carpeta / "normativa.yaml").get("comprobado", "")))
        f = max(fechas)
        return {"version": f.replace("-", "."), "fecha": f}

    @cached_property
    def version(self) -> str:
        """La versión del catálogo («2026.10.17», «2026.10.20.1»): la que guarda cada programación (`catalogo`)."""
        return str(self._version["version"])

    @cached_property
    def fecha(self) -> str:
        """AAAA-MM-DD de la versión."""
        return str(self._version.get("fecha") or self.version[:10].replace(".", "-"))

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
        ra, comp, fuente, contenidos, propuesta = [], [], None, [], {}
        if e.get("modulo"):
            m = self.modulo(e["modulo"])
            propuesta = {int(n): list(v) for n, v in (m.get("propuesta_ra_competencias") or {}).get(sigla, {}).items()}
            contenidos = [{"titulo": texto(b["titulo"], idioma), "puntos": [texto(x, idioma) for x in b["puntos"]]}
                          for b in m.get("contenidos", [])]
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
                     competencias_modulo=comp, fuente_ra=fuente, pendientes=pendientes, contenidos=contenidos,
                     propuesta_competencias=propuesta)

    def normativa(self, sigla: str, ambito: str, curso_escolar: str | None = None) -> list[Norma]:
        """Normas de un ámbito que se aplican al ciclo, por fecha creciente. Las resoluciones de un curso escolar solo
        entran en el suyo."""
        grado = self.ciclo(sigla)["grado"]
        out = [n for n in self.normas.values() if n.ambito == ambito and n.aplica_a(sigla, grado)
               and (n.curso_escolar is None or n.curso_escolar == curso_escolar)]
        return sorted(out, key=lambda n: (n.fecha, n.id))

    def diferencias(self, otro: Catalogo, sigla: str, codigo: str, curso: int | None = None) -> list[str]:
        """Cambios de RA, criterios y horas de un módulo entre este catálogo (el de la programación) y `otro` (el nuevo):
        la base de la ventana «Cambios en el currículo» (ADR-015). Cada línea empieza por «RAn de …» o por «Horas»."""
        try:
            a = self.ficha(sigla, codigo, curso)
        except KeyError:
            a = None
        try:
            b = otro.ficha(sigla, codigo, curso)
        except KeyError:
            return [f"Módulo {codigo}: ya no está en {sigla}"] if a else []
        if a is None:
            return [f"Módulo {codigo}: nuevo en {sigla}"]
        out = []
        if a.horas != b.horas:
            out.append(f"Horas de {codigo}: {a.horas} h → {b.horas} h al año")
        if a.h_sem != b.h_sem:
            out.append(f"Horas de {codigo}: {a.h_sem} → {b.h_sem} h a la semana")
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


@dataclass
class Novedades:
    """Lo que cambia entre dos versiones del catálogo: normas y módulos afectados (`diferencias_catalogo`)."""
    anterior: str
    nueva: str
    normas: list[str] = field(default_factory=list)                       # Markdown, una línea por norma
    modulos: dict[tuple[str, int, str], list[str]] = field(default_factory=dict)   # (sigla, curso, código) → cambios
    nombres: dict[tuple[str, int, str], str] = field(default_factory=dict)
    otros: list[str] = field(default_factory=list)                        # curso escolar y lo que no es de un módulo

    @property
    def vacias(self) -> bool:
        return not (self.normas or self.modulos or self.otros)


def _textos(carpeta: Path, sub: str) -> dict[str, str]:
    d = carpeta / sub
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(d.glob("*.yaml"))} if d.is_dir() else {}


def _enlace(n: Norma | dict) -> str:
    cita = n.cita if isinstance(n, Norma) else texto(n.get("titulo")).rstrip(".")
    enlace = n.enlace if isinstance(n, Norma) else n.get("enlace", "")
    return f"[{cita}]({enlace})" if enlace else cita


def diferencias_catalogo(viejo: Catalogo, nuevo: Catalogo) -> Novedades:
    """Normas nuevas, quitadas o cambiadas (también un documento oficial con la huella distinta) y, por cada módulo de
    cada ciclo, los cambios de RA, criterios y horas. Solo se miran los archivos que han cambiado: es rápido."""
    nov = Novedades(viejo.version, nuevo.version)
    na, nb = viejo.normas, nuevo.normas
    for i in sorted(set(nb) - set(na), key=lambda i: (nb[i].fecha, i)):
        nov.normas.append(f"Norma nueva: {_enlace(nb[i])} ({nb[i].fecha})")
    for i in sorted(set(na) - set(nb), key=lambda i: (na[i].fecha, i)):
        nov.normas.append(f"Ya no se cita: {_enlace(na[i])}")
    for i in sorted(set(na) & set(nb)):
        if (na[i].titulo, na[i].fecha, na[i].enlace) != (nb[i].titulo, nb[i].fecha, nb[i].enlace):
            nov.normas.append(f"Cambia la referencia de {_enlace(nb[i])}")
    fa = {f["id"]: f for f in (_leer(viejo.carpeta / "fuentes.yaml") or {}).get("fuentes", [])}
    fb = {f["id"]: f for f in (_leer(nuevo.carpeta / "fuentes.yaml") or {}).get("fuentes", [])}
    for i in sorted(set(fa) & set(fb)):
        if fa[i].get("huella") != fb[i].get("huella"):
            nov.normas.append(f"Texto publicado distinto (huella nueva): {_enlace(fb[i])}")
    for i in sorted(set(fb) - set(fa)):
        if i not in nb:
            nov.normas.append(f"Fuente nueva: {_enlace(fb[i])}")

    mods_a, mods_b = _textos(viejo.carpeta, "modulos"), _textos(nuevo.carpeta, "modulos")
    cambiados = {Path(n).stem for n in set(mods_a) | set(mods_b) if mods_a.get(n) != mods_b.get(n)}
    ciclos_a, ciclos_b = _textos(viejo.carpeta, "ciclos"), _textos(nuevo.carpeta, "ciclos")
    for nombre in sorted(set(ciclos_a) | set(ciclos_b)):
        sigla = Path(nombre).stem
        if nombre not in ciclos_b:
            nov.otros.append(f"El ciclo {sigla} ya no está en el catálogo")
            continue
        filas = nuevo.ciclo(sigla)["modulos"]
        filas_a = viejo.ciclo(sigla)["modulos"] if nombre in ciclos_a else []
        ciclo_cambia = ciclos_a.get(nombre) != ciclos_b[nombre]
        claves = {(m["curso"], m["codigo"].rstrip("p")): m for m in filas_a}
        claves.update({(m["curso"], m["codigo"].rstrip("p")): m for m in filas})
        for (curso, codigo), m in sorted(claves.items()):
            if not ciclo_cambia and m.get("modulo") not in cambiados:
                continue
            cambios = viejo.diferencias(nuevo, sigla, codigo, curso) if nombre in ciclos_a else \
                [f"Módulo {codigo}: nuevo en {sigla}"]
            if cambios:
                nov.modulos[(sigla, curso, codigo)] = cambios
                nov.nombres[(sigla, curso, codigo)] = texto(m["nombre"])
    cursos_a, cursos_b = _textos(viejo.carpeta, "cursos"), _textos(nuevo.carpeta, "cursos")
    for nombre in sorted(set(cursos_a) | set(cursos_b)):
        if cursos_a.get(nombre) != cursos_b.get(nombre):
            nov.otros.append(f"Fechas del curso {Path(nombre).stem}: " + ("nuevas" if nombre not in cursos_a else
                                                                          "cambian" if nombre in cursos_b else "quitadas"))
    return nov


def texto_novedades(nov: Novedades, propias: set[tuple[str, int, str]] | None = None) -> str:
    """Markdown de «Cambios en el currículo» (la ventana de la app, la PR del vigía y `indice.json`): qué normas cambian,
    qué módulos afectan y la diferencia. `propias` marca los módulos con programación en este equipo."""
    propias = propias or set()
    lineas = []
    if nov.normas:
        lineas += ["### Normativa", "", *[f"- {x}" for x in nov.normas], ""]
    if nov.modulos:
        lineas += ["### Módulos afectados", ""]
        orden = sorted(nov.modulos, key=lambda k: (k not in propias, k))
        for k in orden:
            sigla, curso, codigo = k
            marca = " · **tu programación**" if k in propias else ""
            lineas.append(f"- **{sigla} {curso} - {codigo}** {nov.nombres.get(k, '')}{marca}")
            lineas += [f"    - {c}" for c in nov.modulos[k]]
        lineas.append("")
    if nov.otros:
        lineas += ["### Otros cambios", "", *[f"- {x}" for x in nov.otros], ""]
    return "\n".join(lineas).strip() or "Sin cambios de normativa, RA, criterios ni horas."


def esquema(nombre: str) -> dict:
    return json.loads((ESQUEMAS / f"{nombre}.schema.json").read_text(encoding="utf-8"))
