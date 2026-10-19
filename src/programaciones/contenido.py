"""Contenido de una programación .docx: el cuerpo por apartados, su comparación con otra y la verificación del documento.

- `leer`: párrafos y tablas del cuerpo, sin el índice ni los párrafos vacíos, con el apartado de cada uno. En las
  tablas, una celda combinada en vertical repite el texto de la de arriba (lo que se ve).
- `comparar`: diferencias de contenido entre dos programaciones, apartado a apartado. Las de forma (mayúsculas,
  comillas, guiones, «RD» por «Real Decreto», espacios ante «%», el orden de las filas…) no cuentan.
- `texto_cuerpo`: el texto que firma la huella de la parte incrustada (incrustar.py).
- `verificar`: lo de `verificar.py` de la guía programacion-didactica (títulos, campo TOC, citas sin enlace y
  términos vetados).
"""
from __future__ import annotations

import difflib
import hashlib
import re
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

from lxml import etree

from programaciones.ooxml import W, es_titulo, estilo, normal, numeracion, texto

RE_APARTADO = re.compile(r"^(\d{1,2}(?:\.\d)?)[.\-\s]")


@dataclass
class Elemento:
    seccion: str
    tipo: str                       # «p» o «tabla»
    texto: str = ""                 # párrafo: texto normalizado
    filas: list[list[str]] = field(default_factory=list)   # tabla: celdas (párrafos unidos con « / »)
    parrafos: list[list[list[str]]] = field(default_factory=list)  # tabla: párrafos de cada celda
    nivel: int | None = None        # párrafo de lista: nivel; si no, None
    xml: object = None


def _docx(origen) -> bytes:
    if isinstance(origen, (str, Path)):
        return Path(origen).read_bytes()
    return origen


def documento_xml(origen) -> etree._Element:
    with zipfile.ZipFile(BytesIO(_docx(origen))) as z:
        return etree.fromstring(z.read("word/document.xml"))


def celdas(tr) -> list:
    return tr.findall(W + "tc")


def tabla(tbl) -> tuple[list[list[str]], list[list[list[str]]]]:
    """Filas de una tabla como texto por celda y párrafos por celda, con las combinaciones verticales rellenas."""
    filas, parrafos = [], []
    arriba: dict[int, tuple[str, list[str]]] = {}
    for tr in tbl.findall(W + "tr"):
        fila, pfila, col = [], [], 0
        for tc in celdas(tr):
            pr = tc.find(W + "tcPr")
            span = int(pr.find(W + "gridSpan").get(W + "val")) if pr is not None and pr.find(W + "gridSpan") is not None else 1
            vm = pr.find(W + "vMerge") if pr is not None else None
            ps = [normal(texto(p)) for p in tc.findall(W + "p")]
            ps = [x for x in ps if x]
            if vm is not None and vm.get(W + "val") != "restart" and col in arriba:
                t, ps = arriba[col]
            else:
                t = " / ".join(ps)
            arriba[col] = (t, ps)
            fila.append(t)
            pfila.append(ps)
            col += span
        filas.append(fila)
        parrafos.append(pfila)
    return filas, parrafos


def leer(origen, titulos: bool = False) -> list[Elemento]:
    """Párrafos y tablas del cuerpo, cada uno con su apartado. Los títulos (estilo de título) solo cambian el apartado;
    con `titulos`, también se devuelven como párrafos (el formato antiguo con títulos con estilo los necesita)."""
    body = documento_xml(origen).find(W + "body")
    out, seccion = [], "portada"
    for e in body:
        if e.tag == W + "p":
            if es_titulo(e):
                m = RE_APARTADO.match(normal(texto(e)))
                seccion = m.group(1) if m else normal(texto(e))[:20]
                if titulos and normal(texto(e)):
                    out.append(Elemento(seccion, "p", normal(texto(e)), xml=e))
                continue
            if estilo(e).startswith("TDC") or estilo(e) == "Ttulodelatabla":
                continue
            t = normal(texto(e))
            if t:
                n = numeracion(e)
                out.append(Elemento(seccion, "p", t, nivel=n[1] if n else None, xml=e))
        elif e.tag == W + "tbl":
            filas, parrafos = tabla(e)
            out.append(Elemento(seccion, "tabla", filas=filas, parrafos=parrafos, xml=e))
    return out


def secciones(elementos: list[Elemento]) -> dict[str, list[Elemento]]:
    out: dict[str, list[Elemento]] = {}
    for e in elementos:
        out.setdefault(e.seccion, []).append(e)
    return out


def texto_cuerpo(origen) -> str:
    """Texto del cuerpo sin el índice (Word lo rehace al abrir): lo que firma la huella del texto."""
    partes = []
    for e in leer(origen):
        partes.append(e.texto if e.tipo == "p" else "\n".join(" || ".join(f) for f in e.filas))
    return "\n".join(partes)


# ---------------------------------------------------------------------------------------------------------------------
# Comparación
# ---------------------------------------------------------------------------------------------------------------------
EQUIVALENCIAS = [   # diferencias de forma conocidas entre las programaciones (docs/PLAN_DE_PRUEBAS.md)
    (r"[“”«»\"‘’]", '"'), (r"[–—‑−]", "-"), (r"\breal decreto\b", "rd"), (r"(\s*/\s*)+", "/"),
    (r"\br\.\s?a\.\s?(\d)", r"ra\1"), (r"\s+y\s+(ra\d)", r", \1"),
    (r"\bhoras de centro\b", "horas centro"), (r"\btotal,\s*horas", "total horas"),
    (r"^profesor(?:es|/a)?:$", "profesor:"), (r"\b([1-3])/([1-3])\b", r"\1 y \2"),
    (r"\s*\(\s*", " ("), (r"\s+\)", ")"),
]


def _pct(m) -> str:
    v = float(m.group(1).replace(",", "."))
    return f"{v:g}%"


def forma(s: str) -> str:
    """Clave de comparación: el texto sin lo que no es contenido."""
    s = normal(s).casefold()
    for patron, sustituto in EQUIVALENCIAS:
        s = re.sub(patron, sustituto, s)
    s = re.sub(r"(\d+(?:,\d+)?)\s*%", _pct, s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.rstrip(" .:;")


COLUMNAS = [   # cabeceras de las tablas 4 y 4.1 → columna (para comparar aunque cambie el orden)
    ("unidad", r"^(unidad|tarea)"), ("horas", r"^(sesiones|horas$)"), ("trimestre", r"^trim"),
    ("elemento", r"^elemento"), ("peso", r"^peso"), ("ra", r"^ra asociados?"),
    ("resultado", r"^resultado de aprendizaje"),
    ("total", r"^horas totales"), ("pct", r"^% del curso"), ("modalidad", r"^modalidad"),
    ("centro", r"^horas\W*centro"), ("empresa", r"^horas\W*(en\W+)?empresa"), ("pct_centro", r"^% horas\W*centro"),
    ("pct_empresa", r"^% horas\W*empresa"),
]


def _orden_columnas(cabecera: list[str]) -> list[int] | None:
    claves = []
    for c in cabecera:
        k = next((n for n, rx in COLUMNAS if re.match(rx, forma(c))), None)
        if k is None:
            return None
        claves.append(k)
    orden = [n for n, _ in COLUMNAS]
    return sorted(range(len(claves)), key=lambda i: orden.index(claves[i]))


def _claves_columnas(cabecera: list[str]) -> list[str] | None:
    claves = [next((n for n, rx in COLUMNAS if re.match(rx, forma(c))), None) for c in cabecera]
    return None if None in claves else claves


def unidades(elementos: list[Elemento]) -> list[tuple]:
    """(clase, texto, clave de forma, celdas por columna o None) de cada párrafo y de cada fila de cada tabla."""
    out = []
    for e in elementos:
        if e.tipo == "p":
            out.append(("parrafo", e.texto, forma(e.texto), None))
            continue
        orden = _orden_columnas(e.filas[0]) if e.filas else None
        claves = _claves_columnas(e.filas[0]) if e.filas else None
        for fila in e.filas:
            cel = [fila[i] for i in orden] if orden and len(fila) == len(orden) else fila
            t = " || ".join(cel)
            # en la clave, sin celdas vacías y con los párrafos de cada celda en orden (el orden dentro de una celda
            # y una celda vacía de más son forma)
            norm = [" / ".join(sorted(forma(x) for x in c.split(" / "))) for c in cel]
            por_columna = dict(zip(claves, (norm[orden.index(i)] for i in range(len(claves))), strict=True)) \
                if claves and orden and len(fila) == len(claves) else None
            out.append(("fila", t, " || ".join(c for c in norm if c), por_columna))
    return out


@dataclass
class Diferencia:
    seccion: str
    cambio: str            # «cambia», «falta» (está en la referencia y no en el generado) o «sobra»
    clase: str             # «parrafo» o «fila»
    referencia: str | None
    generado: str | None
    columnas: list[str] | None = None   # filas de las tablas 4 y 4.1: las columnas que cambian

    @property
    def firma(self) -> tuple:
        """Lo que identifica la diferencia sin el texto de la referencia: apartado, cambio, el principio del texto
        generado (que sale de la plantilla o del catálogo) y, en las filas, las columnas que cambian."""
        inicio = (self.generado or "").split(" || ")[0][:40] if self.cambio != "falta" else ""
        return (self.seccion, self.cambio, inicio, tuple(self.columnas or ()))

    def __str__(self) -> str:
        if self.cambio == "cambia":
            return f"[{self.seccion}] {self.clase}: «{self.referencia[:150]}» → «{self.generado[:150]}»"
        t = self.referencia if self.cambio == "falta" else self.generado
        return f"[{self.seccion}] {self.clase} que {self.cambio}: «{(t or '')[:150]}»"


def comparar(referencia, generado) -> tuple[list[Diferencia], int]:
    """Diferencias de contenido (lista) y número de diferencias solo de forma."""
    a, b = secciones(leer(referencia)), secciones(leer(generado))
    difs, de_forma = [], 0
    for sec in list(a) + [s for s in b if s not in a]:
        ua, ub = unidades(a.get(sec, [])), unidades(b.get(sec, []))
        de_forma += sum(1 for x, y in zip(ua, ub, strict=False) if x[2] == y[2] and x[1] != y[1])
        sm = difflib.SequenceMatcher(None, [x[2] for x in ua], [x[2] for x in ub], autojunk=False)
        faltan, sobran = [], []
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            faltan += ua[i1:i2]
            sobran += ub[j1:j2]
        # mismo contenido en otro orden: forma
        ca, cb = Counter(x[2] for x in faltan), Counter(x[2] for x in sobran)
        comunes = ca & cb
        de_forma += sum(comunes.values())
        faltan = [x for x in faltan if not _consumir(comunes, x[2], "a")]
        comunes = ca & cb
        sobran = [x for x in sobran if not _consumir(comunes, x[2], "b")]
        # emparejar lo que cambia (por parecido) y dejar el resto como falta/sobra
        usados = set()
        for x in faltan:
            mejor, k_mejor = 0.0, None
            for k, y in enumerate(sobran):
                if k in usados or y[0] != x[0]:
                    continue
                r = difflib.SequenceMatcher(None, x[2][:300], y[2][:300]).ratio()
                if r > mejor:
                    mejor, k_mejor = r, k
            if k_mejor is not None and mejor >= 0.5:
                usados.add(k_mejor)
                y = sobran[k_mejor]
                cols = None
                if x[3] is not None and y[3] is not None:
                    cols = sorted(k for k in set(x[3]) | set(y[3]) if x[3].get(k) != y[3].get(k))
                difs.append(Diferencia(sec, "cambia", x[0], x[1], y[1], cols))
            else:
                difs.append(Diferencia(sec, "falta", x[0], x[1], None))
        difs += [Diferencia(sec, "sobra", y[0], None, y[1]) for k, y in enumerate(sobran) if k not in usados]
    return difs, de_forma


def _consumir(comunes: Counter, clave: str, _lado: str) -> bool:
    if comunes.get(clave, 0) > 0:
        comunes[clave] -= 1
        return True
    return False


# ---------------------------------------------------------------------------------------------------------------------
# Verificación (verificar.py de la guía programacion-didactica)
# ---------------------------------------------------------------------------------------------------------------------
RE_CITA = re.compile(r"(Real Decreto|RD|Decreto|Orden|ORDEN|Ley Orgánica|Resolución|RESOLUCIÓN)\s+"
                     r"(\d+/\d{4}|de \d+ de \w+ de \d{4})")
# Huella SHA-256 de los términos vetados (en minúsculas), para no escribirlos aquí.
VETADOS = frozenset({"c857d09db23e6822e3600bc06ad8d58f92ed62bc8efd81c753f77048662cb97d"})


def _tiene_vetados(xml: bytes) -> bool:
    """Si el XML lleva algún término vetado como palabra, sin distinguir mayúsculas."""
    texto = xml.decode("utf-8", "ignore").lower()
    return any(hashlib.sha256(p.encode()).hexdigest() in VETADOS for p in set(re.findall(r"[^\W\d_]+", texto)))


def titulos(origen) -> list[str]:
    d = documento_xml(origen)
    return [normal(texto(p)) for p in d.iter(W + "p") if estilo(p) in ("Ttulo1", "Ttulo2", "Ttulo3")]


def citas_sin_enlace(origen) -> list[str]:
    """Citas de normas fuera de un hipervínculo o de un campo (deben ser 0)."""
    d = documento_xml(origen)
    out = []
    for p in d.iter(W + "p"):
        txt, prof = "", 0
        for r in p.iter(W + "r"):
            fc = r.find(W + "fldChar")
            if fc is not None:
                ty = fc.get(W + "fldCharType")
                prof += 1 if ty == "begin" else -1 if ty == "end" else 0
                continue
            if r.getparent().tag == W + "hyperlink" or prof > 0:
                txt += "⁣"
                continue
            txt += "".join(t.text or "" for t in r.iter(W + "t"))
        out += [m.group(0) for m in RE_CITA.finditer(txt)]
    return out


def verificar(origen, plantilla_titulos: list[str]) -> dict:
    datos = _docx(origen)
    with zipfile.ZipFile(BytesIO(datos)) as z:
        vetado = any(_tiene_vetados(z.read(n)) for n in z.namelist() if n.endswith((".xml", ".rels")))
        ajustes = z.read("word/settings.xml").decode("utf-8") if "word/settings.xml" in z.namelist() else ""
    d = documento_xml(datos)
    return {
        "titulos_iguales": [t.rstrip() for t in titulos(datos)] == [t.rstrip() for t in plantilla_titulos],
        "campo_toc": sum(1 for i in d.iter(W + "instrText") if "TOC" in (i.text or "")),
        "citas_sin_enlace": citas_sin_enlace(datos),
        "termino_vetado": vetado,
        "update_fields": 'updateFields w:val="true"' in ajustes,
    }
