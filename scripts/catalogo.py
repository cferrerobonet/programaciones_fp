#!/usr/bin/env python3
"""Catálogo curricular de Programaciones: lo construye desde el BOE y el DOGV y lo comprueba.

Uso:
  catalogo.py construir <SIGLA>|todo [--sin-red]   rehace catalogo/ desde las fuentes oficiales
  catalogo.py comprobar [--red]                    esquemas, horas, RA, fuentes y huellas (--red: enlaces vivos)
  catalogo.py comparar <programación.docx>…        RA y criterios de una programación frente al catálogo

Fuentes (docs/CATALOGO_Y_FUENTES.md):
- Módulos propios: anexo I del real decreto de cada título, en su redacción vigente. Los reales decretos de los
  títulos no están consolidados en el BOE: se lee el original (XML del BOE) y, encima, lo que reescriben las normas
  que lo modifican (RD 401/2023 en ARI, RD 289/2023 en ISO). RD 499/2024 y RD 500/2024 solo quitan FOL, EIE y FCT,
  añaden los módulos comunes y renombran el proyecto: no cambian los RA de los módulos propios.
- Competencia general y competencias del título: artículos 4 y 5 del real decreto.
- Correspondencias con los estándares de competencia: anexo V B) del real decreto (o el que lo sustituye) y la
  denominación de cada ECP del anexo I del RD 532/2025.
- Módulos, curso, h/semana y h/año: anexo IV del Decreto 95/2026, que da nueva redacción a los anexos I y II del
  Decreto 114/2025 (DOGV, PDF).
- RA de los módulos comunes y de los optativos: anexos III a X del Decreto 114/2025 y anexo V del Decreto 95/2026.

El lector del BOE parte de `curriculo.py boe` de la skill apuntes-auditoria (mismas reglas para RA, criterios con y sin
letra y fin del bloque), pero lee el XML del BOE y atraviesa los bloques citados de las normas que modifican el título.

Lo que no está en la fuente no se pone: el módulo queda con `pendiente` y su motivo.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True  # sin __pycache__ en iCloud

import yaml  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
CATALOGO = RAIZ / "catalogo"
ESQUEMAS = RAIZ / "src" / "programaciones" / "esquemas"
FORMATO = "catalogo/1"
HOY = dt.date.today().isoformat()
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Programaciones-catalogo"}


def _cache() -> Path:
    if os.environ.get("PROGRAMACIONES_CACHE"):
        return Path(os.environ["PROGRAMACIONES_CACHE"])
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "programaciones" / "fuentes"
    return Path.home() / ".cache" / "programaciones" / "fuentes"


# ---------------------------------------------------------------------------------------------------------------------
# Receta: de dónde sale cada ciclo. Lo demás (nombres, horas, RA) se lee de las fuentes.
# ---------------------------------------------------------------------------------------------------------------------
DOGV_114 = "DOGV-C-2025-29742"   # Decreto 114/2025
DOGV_95 = "DOGV-C-2026-21170"    # Decreto 95/2026 (nuevos anexos I y II del 114/2025 y anexo XII)
RD_532 = "BOE-A-2025-13147"      # estándares de competencias (ECP)

DOCUMENTOS_DOGV = {
    DOGV_114: {"url": "https://dogv.gva.es/datos/2025/08/04/pdf/2025_29742_es.pdf",
               "enlace": "https://dogv.gva.es/es/eli/es-vc/d/2025/07/29/114/dof/spa/html", "publicado": "2025-08-04"},
    DOGV_95: {"url": "https://dogv.gva.es/datos/2026/06/25/pdf/2026_21170_es.pdf",
              "enlace": "https://dogv.gva.es/es/eli/es-vc/d/2026/06/19/95", "publicado": "2026-06-25"},
    "DOGV-C-2026-22324": {"url": "https://dogv.gva.es/datos/2026/06/29/pdf/2026_22324_es.pdf",
                          "enlace": "https://dogv.gva.es/va/eli/es-vc/d/2026/06/19/95/corrigendum/20260629",
                          "publicado": "2026-06-29"},
    "DOGV-C-2025-13083": {"url": "https://dogv.gva.es/datos/2025/04/30/pdf/2025_13083_es.pdf",
                          "enlace": "https://dogv.gva.es/es/eli/es-vc/o/2025/04/22/8/dof/spa/html", "publicado": "2025-04-30"},
    "DOGV-C-2026-10102": {"url": "https://dogv.gva.es/datos/2026/04/07/pdf/2026_10102_es.pdf",
                          "enlace": "https://dogv.gva.es/es/eli/es-vc/o/2026/04/01/(1)/dof/spa/html", "publicado": "2026-04-07"},
    "DOGV-C-2026-24495": {"url": "https://dogv.gva.es/datos/2026/07/20/pdf/2026_24495_es.pdf",
                          "enlace": "https://dogv.gva.es/datos/2026/07/20/pdf/2026_24495_es.pdf", "publicado": "2026-07-20"},
    # Orden 20/2019 (DOGV núm. 8540): sin CVE; el identificador es su código de inserción (2019/4442)
    "DOGV-C-2019-4442": {"url": "https://dogv.gva.es/datos/2019/05/03/pdf/2019_4442.pdf",
                         "enlace": "https://dogv.gva.es/es/eli/es-vc/o/2019/04/30/20/dof/spa/html", "publicado": "2019-05-03"},
}

# Erratas del BOE que el documento corrige (CarlosFB, 2026-10-17: el catálogo guarda el texto literal y la corrección,
# y el documento sale corregido, como las programaciones de 0517 y 0524). Clave: (módulo, RA, letra del criterio o
# None para el enunciado). Valor: (fragmento literal, fragmento corregido, motivo). Si el BOE cambia y el fragmento ya
# no está, la construcción se para.
CORRECCIONES = {
    ("0517", 1, "a"): ("de acuerdo a la normativa", "de acuerdo con la normativa",
                       "Errata del BOE: «de acuerdo a» por «de acuerdo con»"),
    ("0517", 1, "c"): ("(ITC)", "(ICT)", "Errata del BOE: la sigla de la Infraestructura Común de Telecomunicaciones es ICT"),
    ("0517", 4, "d"): ("en las medidas, cumplen", "en las medidas cumplen",
                       "Errata del BOE: coma entre el sujeto y el verbo"),
    ("0524", 1, "a"): ("las distintos tipos", "los distintos tipos", "Errata del BOE: concordancia «los distintos tipos»"),
}

# Lo mismo en los textos del ciclo: (sigla, campo) → (fragmento literal, fragmento corregido, motivo).
CORRECCIONES_CICLO = {
    ("SEA", "competencia_general"): ("(REBT).También", "(REBT). También",
                                     "Errata del BOE: falta el espacio tras el punto"),
}

# UC mal escritas en un anexo V B) (norma → UC impresa → (UC correcta, motivo)). El ECP se busca con la correcta.
ERRATAS_UC = {
    "BOE-A-2024-10684": {"0626_3": ("0626_2", "Errata del RD 499/2024: los anexos V A) y V B) dicen UC0626_3, pero su "
                                              "art. 6 y el RD 532/2025 dan UC0626_2, con la misma denominación")},
}

CICLOS = {
    "GA": {"grado": "GM", "rd": "BOE-A-2009-19148", "horario": "Gestión administrativa",
           "anexo_v": ("BOE-A-2024-10684", r"Real Decreto 1631/2009")},
    "IT": {"grado": "GM", "rd": "BOE-A-2009-18404", "horario": "Instalaciones de telecomunicaciones"},
    "IEA": {"grado": "GM", "rd": "BOE-A-2008-3957", "horario": "Instalaciones eléctricas y automáticas",
            "anexo_v": ("BOE-A-2024-10684", r"Real Decreto 177/2008")},
    "CAR": {"grado": "GM", "rd": "BOE-A-2008-3524", "horario": "Carrocería"},
    "EMV": {"grado": "GM", "rd": "BOE-A-2010-8119", "horario": "Electromecánica de vehículos automóviles",
            "anexo_v": ("BOE-A-2024-10684", r"Real Decreto 453/2010")},
    "ADM": {"grado": "GS", "rd": "BOE-A-2011-19533", "horario": "Administración y finanzas"},
    "ISO": {"grado": "GS", "rd": "BOE-A-2012-10866", "horario": "Integración social",
            "reescritos": [("BOE-A-2023-10395", r"^Artículo segundo\.", r"^Artículo tercero\.")],
            "art4": ("BOE-A-2023-10395", r"^Artículo segundo\.", r"^Artículo tercero\.")},
    "AUT": {"grado": "GS", "rd": "BOE-A-2008-18991", "horario": "Automoción"},
    "SEA": {"grado": "GS", "rd": "BOE-A-2010-15355", "horario": "Sistemas electrotécnicos y automatizados",
            "anexo_v": ("BOE-A-2023-13217", r"^Artículo cuarto\.")},
    "STI": {"grado": "GS", "rd": "BOE-A-2011-12724", "horario": "Sistemas de telecomunicaciones e informáticos"},
    "ARI": {"grado": "GS", "rd": "BOE-A-2011-19530", "horario": "Automatización y robótica industrial",
            "reescritos": [("BOE-A-2023-13217", r"^Artículo segundo\.", r"^Artículo tercero\.")]},
}
ORDEN_CICLOS = ["SEA", "STI", "ARI", "IEA", "IT", "GA", "ADM", "ISO", "AUT", "CAR", "EMV"]

# Optativos que oferta el centro (apartado 2.2 de las programaciones de SEA, STI y ARI; el 0179 lo confirmó CarlosFB el
# 2026-10-14). El código es el que usa el centro: el decreto no da código a los optativos.
OPTATIVOS_ELECTRICIDAD = [
    {"modulo": "OPT-INGLES-ORAL", "codigo": "0179"},
    {"modulo": "OPT-EE-IA", "codigo": "CVOPS031"},
    {"modulo": "OPT-EE-FV", "codigo": "CVOPS141"},
]
OPTATIVOS_OFERTADOS = {s: OPTATIVOS_ELECTRICIDAD for s in ("SEA", "STI", "ARI")}

# Módulos comunes y optativos: anexo del Decreto 114/2025 (o del 95/2026) del que salen sus RA.
COMUNES = {
    "0156": {"tipo": "ingles", "doc": DOGV_114, "inicio": r"^\s*ANEXO III\. 0156 INGLÉS PROFESIONAL \(GM\)"},
    "0179": {"tipo": "ingles", "doc": DOGV_114, "inicio": r"^\s*ANEXO IV\. 0179 INGLÉS PROFESIONAL \(GS\)"},
    "1709": {"tipo": "empleabilidad", "doc": DOGV_114, "inicio": r"^\s*ANEXO V\. 1709 ITINERARIO PERSONAL"},
    "1710": {"tipo": "empleabilidad", "doc": DOGV_114, "inicio": r"^\s*ANEXO VI\. 1710 ITINERARIO PERSONAL"},
    "1664": {"tipo": "digitalizacion", "doc": DOGV_114, "inicio": r"^\s*ANEXO VII\. 1664 DIGITALIZACIÓN"},
    "1665": {"tipo": "digitalizacion", "doc": DOGV_114, "inicio": r"^\s*ANEXO VIII\. 1665 DIGITALIZACIÓN"},
    "1708": {"tipo": "sostenibilidad", "doc": DOGV_114, "inicio": r"^\s*ANEXO IX\. 1708 SOSTENIBILIDAD"},
    "CV0014": {"tipo": "autonomico", "doc": DOGV_95, "inicio": r"^\s*ANEXO XII-II\. CV0014 "},
    "CV0015": {"tipo": "autonomico", "doc": DOGV_95, "inicio": r"^\s*ANEXO XII-III\. CV0015 "},
    "OPT-INGLES-ORAL": {"tipo": "optativo", "doc": DOGV_114, "nombre": "Inglés oral para entornos profesionales",
                        "inicio": r"^\s*ANEXO X-I: MÓDULO: INGLÉS ORAL PARA ENTORNOS PROFESIONALES"},
    "OPT-EE-FV": {"tipo": "optativo", "doc": DOGV_114,
                  "nombre": "Operaciones de montaje y mantenimiento de instalaciones solares fotovoltaicas",
                  "seccion": r"^\s*ANEXO X-IX\. FAMILIA PROFESIONAL: ELECTRICIDAD",
                  "inicio": r"^\s*MÓDULO: OPERACIONES DE MONTAJE Y MANTENIMIENTO DE INSTALACIONES SOLARES"},
    "OPT-EE-IA": {"tipo": "optativo", "doc": DOGV_114,
                  "nombre": "Programación con inteligencia artificial en sistemas electrónicos y automáticos",
                  "seccion": r"^\s*ANEXO X-IX\. FAMILIA PROFESIONAL: ELECTRICIDAD",
                  "inicio": r"^\s*MÓDULO: PROGRAMACIÓN CON INTELIGENCIA ARTIFICIAL"},
}

# Lo que falta en las fuentes o depende de CarlosFB (docs/PENDIENTE.md).
PENDIENTE_PROYECTO_GM = "Fuente de los RA del Proyecto intermodular de GM sin localizar (docs/PENDIENTE.md)"
PENDIENTE_OPTATIVO = "El centro aún no ha dicho qué optativo ofrece en este ciclo (docs/PENDIENTE.md)"


# ---------------------------------------------------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------------------------------------------------
def limpio(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").replace(" ", " ").replace("­", "")
    return re.sub(r"\s+", " ", s).strip()


def es(texto: str) -> dict:
    return {"es": limpio(texto)}


def huella_bytes(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def huella_texto(partes) -> str:
    return huella_bytes("\n".join(partes).encode("utf-8"))


SIN_RED = False


def descargar(url: str, nombre: str) -> bytes:
    """Documento oficial con caché local (fuera de iCloud). Con --sin-red solo vale la caché."""
    destino = _cache() / nombre
    if destino.is_file() and (SIN_RED or destino.stat().st_size > 0):
        return destino.read_bytes()
    if SIN_RED:
        raise SystemExit(f"Sin red y sin caché de {nombre} ({url})")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        datos = r.read()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(datos)
    return datos


# ---------------------------------------------------------------------------------------------------------------------
# BOE (XML del diario: https://www.boe.es/diario_boe/xml.php?id=…)
# ---------------------------------------------------------------------------------------------------------------------
class Boe:
    def __init__(self, ident: str):
        from lxml import etree
        self.id = ident
        self.bytes = descargar(f"https://www.boe.es/diario_boe/xml.php?id={ident}", f"boe/{ident}.xml")
        self.xml = etree.fromstring(self.bytes)
        self.meta = {e.tag: limpio(e.text or "") for e in self.xml.find("metadatos")}
        self.elems = self._planos()

    def _planos(self) -> list[dict]:
        """Párrafos y tablas del texto en orden, también los que van dentro de las citas (blockquote)."""
        out = []
        for e in self.xml.find("texto").iter("p", "table"):
            if any(a.tag in ("table", "tr", "td", "th") for a in e.iterancestors()):
                continue
            if e.tag == "p":
                out.append({"tipo": "p", "clase": e.get("class") or "", "texto": limpio("".join(e.itertext()))})
            else:
                filas = [[limpio("".join(c.itertext())) for c in tr if c.tag in ("td", "th")] for tr in e.iter("tr")]
                out.append({"tipo": "tabla", "clase": e.get("class") or "", "filas": filas,
                            "texto": limpio(" ".join(" ".join(f) for f in filas))})
        return out

    @property
    def titulo(self) -> str:
        return self.meta.get("titulo", "")

    @property
    def publicado(self) -> str:
        f = self.meta.get("fecha_publicacion", "")
        return f"{f[:4]}-{f[4:6]}-{f[6:]}" if len(f) == 8 else ""

    @property
    def enlace(self) -> str:
        return f"https://www.boe.es/buscar/doc.php?id={self.id}"

    def posteriores(self) -> list[dict]:
        return [{"id": p.get("referencia"), "relacion": limpio(p.findtext("palabra") or ""),
                 "texto": limpio(p.findtext("texto") or "")}
                for p in self.xml.iterfind("analisis/referencias/posteriores/posterior")]

    def seccion(self, inicio: str, fin: str | None = None) -> list[dict]:
        """Elementos desde el que casa con `inicio` hasta el siguiente que casa con `fin` (o con otro artículo)."""
        candidatos = [k for k, e in enumerate(self.elems) if re.search(inicio, e["texto"])]
        # un artículo, por su encabezado (clase «articulo»), no por la línea del índice del principio
        i = next((k for k in candidatos if self.elems[k]["clase"] == "articulo"), candidatos[0] if candidatos else None)
        if i is None:
            raise SystemExit(f"{self.id}: no encuentro «{inicio}»")
        fin = fin or r"^(Artículo [a-zé]+\.|Disposición )"
        j = next((k for k in range(i + 1, len(self.elems)) if re.search(fin, self.elems[k]["texto"])), len(self.elems))
        return self.elems[i:j]

    def seccion_de_rd(self, articulo: str, rd: str) -> list[dict]:
        """En una norma que modifica muchos títulos: el apartado («Seis. En el Real Decreto …») de un real decreto."""
        art = self.seccion(rf"^{articulo}")
        ordinal = r"^[A-ZÁÉÍÓÚ][a-záéíóúñ]+(?: y [a-záéíóúñ]+)?\. En (?:el|los) [Rr]eal [Dd]ecreto"
        i = next((k for k, e in enumerate(art) if re.search(ordinal, e["texto"]) and re.search(rd, e["texto"])), None)
        if i is None:
            raise SystemExit(f"{self.id}: no encuentro el apartado de {rd} en «{articulo}»")
        j = next((k for k in range(i + 1, len(art)) if re.search(ordinal, art[k]["texto"])), len(art))
        return art[i:j]


RE_CODIGO = re.compile(r"^(?:MÓDULOS PROFESIONALES\s+)?(?:M[óo]dulo [Pp]rofesional:\s*.+?\.?\s+)?Código:?\s*(\d{4})\.?$")
RE_NOMBRE = re.compile(r"^(?:MÓDULOS PROFESIONALES\s+)?M[óo]dulo [Pp]rofesional:\s*(.+?)(?:\.?\s+Código:?\s*\d{4})?\.?$")
RE_ECTS = re.compile(r"\.?\s*\(?Equivalencia en créditos ECTS:?\s*\d*\)?\.?$")
RE_RA = re.compile(r"^(\d{1,2})(?:\.\s*|\s+(?=[A-ZÁÉÍÓÚ]))(\S.+)$")   # «4 Determina…»: hay RA sin punto
RE_CE = re.compile(r"^([a-zñ])\)\s*(.+)$")
LETRAS = "abcdefghijklmnñopqrstuvwxyz"


def modulos_boe(elems: list[dict]) -> dict[str, dict]:
    """RA, criterios y competencias de cada módulo del anexo I (o de un bloque que lo reescribe)."""
    inicios = [k for k, e in enumerate(elems) if e["tipo"] == "p" and RE_CODIGO.match(e["texto"].lstrip("«"))]
    out = {}
    for n, i in enumerate(inicios):
        codigo = RE_CODIGO.match(elems[i]["texto"].lstrip("«")).group(1)
        k_nombre = next((k for k in range(i, max(i - 5, -1), -1) if RE_NOMBRE.match(elems[k]["texto"].lstrip("«"))), None)
        nombre = RE_NOMBRE.match(elems[k_nombre]["texto"].lstrip("«")).group(1) if k_nombre is not None else ""
        nombre = RE_ECTS.sub("", nombre)
        fin = inicios[n + 1] if n + 1 < len(inicios) else len(elems)
        bloque = []
        for e in elems[i + 1:fin]:
            if e["clase"] in ("anexo_num",) or re.match(r"(?i)^«?anexo [IVX]+\b", e["texto"]):
                break
            bloque.append(e)
        # el nombre del módulo siguiente queda al final del bloque: fuera
        while bloque and RE_NOMBRE.match(bloque[-1]["texto"].lstrip("«")) or (bloque and re.match(
                r"^(Equivalencia en créditos|El módulo profesional \d{4}\b)", bloque[-1]["texto"])):
            bloque.pop()
        textos, competencias = [], []
        for e in bloque:
            t = e["texto"].strip("«»").strip()
            if e["tipo"] != "p":
                continue
            textos.append(t)
            m = re.search(r"contribuye a alcanzar .*?\bobjetivos? general(?:es)?\b.*?\b(todas las )?competencias?\b(.*)$", t)
            if re.search(r"se relaciona con la totalidad de los objetivos generales del ciclo y (?:de )?las competencias", t):
                competencias = ["todas"]   # módulo de proyecto: «… con la totalidad de … las competencias … del título»
            elif m and m.group(1):
                competencias = ["todas"]   # «… y todas las competencias del título»: se expanden con las del ciclo
            elif m:
                tramo = re.split(r"\bdel (?:título|ciclo)\b|\bde este título\b", m.group(2))[0]
                competencias = sorted(set(re.findall(r"(?<![a-zñ])([a-zñ])\)", tramo)), key=LETRAS.index)
        out[codigo] = {"codigo": codigo, "nombre": nombre, "ra": leer_ra(textos), "competencias": competencias,
                       "huella": huella_texto([e["texto"] for e in bloque])}
    return out


def _siguientes(letras: list[str]) -> set[str]:
    """Letra que puede seguir a una lista de criterios (hay BOE que se saltan la ñ)."""
    if not letras:
        return {"a"}
    i = LETRAS.index(letras[-1])
    sig = {LETRAS[i + 1]} if i + 1 < len(LETRAS) else set()
    if letras[-1] == "n":
        sig.add("o")
    return sig


def trocear(texto: str) -> list[str]:
    """Separa en trozos un párrafo que junta varios elementos («… a) Se ha … b) Se ha …»): BOE anteriores a 2009."""
    texto = re.sub(r"\s*Criterios de evaluación:?\s*", "\n", texto)
    texto = re.sub(r"(?<=[.:;])\s+(?=(?:\d{1,2}\.\s+[A-ZÁÉÍÓÚ]|[a-zñ]\)\s))", "\n", texto)
    texto = re.sub(r"(?<=\S)\s+(?=[a-zñ]\)\s+Se\s+ha)", "\n", texto)   # criterio sin punto final delante
    texto = re.sub(r"\s+(?=(?:Duración:|Contenidos básicos|Orientaciones pedagógicas))", "\n", texto)
    return [x.strip() for x in texto.split("\n") if x.strip()]


def leer_ra(textos: list[str], sin_letra: bool = True) -> list[dict]:
    """RA y criterios de evaluación de un módulo, en el orden del BOE.

    - Un número o una letra en secuencia abre elemento nuevo; fuera de secuencia, solo si el trozo tiene forma de RA
      (va seguido de un criterio) o de criterio («Se ha…»). Si no, es texto del elemento anterior.
    - `n` y `letra` son la posición del elemento. Cuando el BOE imprime otro número u otra letra (erratas: un «2.»
      repetido en 0292, un «ñ)» suelto en 0558, una «i)» que falta en 0453), se guarda lo impreso en `n_boe` o
      `letra_boe`.
    - Hay BOE (RD 883/2011, RD 453/2010) que no escriben la letra: la pinta la lista o un guion. Se numeran en orden,
      como en curriculo.py.
    """
    trozos: list[tuple[str, bool]] = []   # (texto, empieza párrafo y es el único trozo)
    for parrafo in textos:
        if re.match(r"^(Duración|Contenidos básicos|Orientaciones pedagógicas)", parrafo):
            if trozos:
                break
            continue   # hay normas que ponen la duración antes de los RA
        parrafo = re.sub(r"^Resultados de aprendizaje y criterios de evaluación[.:]?\s*", "", parrafo)
        partes = trocear(parrafo) if parrafo else []
        corte = next((k for k, t in enumerate(partes) if re.match(r"^(Duración|Contenidos básicos|Orientaciones pedagógicas)", t)), None)
        if corte is not None and (trozos or corte > 0):
            trozos += [(t, False) for t in partes[:corte]]
            break
        trozos += [(t, len(partes) == 1) for t in partes]

    def es_criterio(t: str, solo: bool) -> bool:
        return bool(RE_CE.match(t) and re.match(r"^[a-zñ]\)\s*Se\s", t)) or (
            sin_letra and solo and re.match(r"^(?:[−–-]\s*)?Se (ha|han) ", t) is not None)

    ra, actual, ultimo = [], None, None
    for k, (t, solo) in enumerate(trozos):
        m, c = RE_RA.match(t), RE_CE.match(t)
        siguiente = trozos[k + 1] if k + 1 < len(trozos) else ("", False)
        if m and (int(m.group(1)) == len(ra) + 1 or (re.match(r"^[A-ZÁÉÍÓÚ]", m.group(2)) and es_criterio(*siguiente))):
            actual = {"n": len(ra) + 1, "texto": m.group(2), "criterios": []}
            if int(m.group(1)) != actual["n"]:
                actual["n_boe"] = int(m.group(1))
            ra.append(actual)
            ultimo = actual
        elif c and actual is not None and (c.group(1) in _siguientes([x["letra"] for x in actual["criterios"]])
                                           or re.match(r"^Se\s", c.group(2))):
            letra = LETRAS[len(actual["criterios"])] if c.group(1) not in _siguientes(
                [x["letra"] for x in actual["criterios"]]) else c.group(1)
            ultimo = {"letra": letra, "texto": c.group(2)}
            if letra != c.group(1):
                ultimo["letra_boe"] = c.group(1)
            actual["criterios"].append(ultimo)
        elif actual is not None and sin_letra and solo and re.match(r"^(?:[−–-]\s*)?Se (ha|han) ", t):
            ultimo = {"letra": LETRAS[len(actual["criterios"])], "texto": re.sub(r"^[−–-]\s*", "", t)}
            actual["criterios"].append(ultimo)
        elif ultimo is not None:
            ultimo["texto"] = ultimo["texto"] + " " + t
    return ra


def con_letras(competencias: list[dict]) -> list[dict]:
    """GA e IT: el art. 5 numera (1., 2.…) y las orientaciones del anexo I citan letras. CarlosFB (2026-10-17): la
    competencia 1 es la a), y el documento usa letras en todos los ciclos (con la ñ, como el anexo I). El número que
    imprime el BOE se guarda en `numero_boe`."""
    if not competencias or not competencias[0]["letra"].isdigit():
        return competencias
    return [{"letra": LETRAS[int(c["letra"]) - 1], "numero_boe": int(c["letra"]), "texto": c["texto"]}
            for c in competencias]


def articulo_texto(elems: list[dict], n: int) -> list[str]:
    i = next((k for k, e in enumerate(elems) if re.match(rf"^«?Artículo {n}\.", e["texto"])), None)
    if i is None:
        return []
    out = []
    for e in elems[i + 1:]:
        if re.match(r"^«?(Artículo \d+\.|CAPÍTULO|Capítulo)", e["texto"]) or re.match(
                r"^[A-ZÁÉÍÓÚ][a-záéíóúñ]+\. (El|Se) ", e["texto"]):
            break
        out.append(e["texto"].strip("«»").strip())
    return [t for t in out if t]


def competencias_titulo(elems: list[dict]) -> list[dict]:
    """Lista del art. 5 tal como la escribe el BOE: con letras a), b)… o, en algunos títulos, con números 1., 2.…"""
    out, ultimo = [], None
    for parrafo in articulo_texto(elems, 5):
        for t in trocear(parrafo):
            c = RE_CE.match(t)
            n = re.match(r"^(\d{1,2})\.\s+(.+)$", t)
            if c and c.group(1) in _siguientes([x["letra"] for x in out]):
                ultimo = {"letra": c.group(1), "texto": c.group(2)}
                out.append(ultimo)
            elif n and int(n.group(1)) == len(out) + 1 and (not out or out[0]["letra"].isdigit()):
                ultimo = {"letra": n.group(1), "texto": n.group(2)}
                out.append(ultimo)
            elif ultimo is not None:
                ultimo["texto"] += " " + t
    return out


def anexo_vb(elems: list[dict]) -> list[dict]:
    """Filas del anexo V B): módulos superados → unidades de competencia acreditables."""
    i = next((k for k, e in enumerate(elems) if re.match(r"(?i)^«?anexo V\.? ?B\)", e["texto"])), None)
    if i is None:
        return []
    tabla = next((e for e in elems[i:i + 4] if e["tipo"] == "tabla"), None)   # a veces el título va en la tabla
    if tabla is None:
        return []
    out = []
    for fila in tabla["filas"]:
        if len(fila) < 2:
            continue
        modulos = re.findall(r"(?<!\d)(\d{4})\.\s", fila[0] + " ")
        uc = [(m.group(1), limpio(m.group(2))) for m in re.finditer(
            r"UC(\d{4}_\d)\s*[:.-]?\s*(.+?)(?=\s*UC\d{4}_\d|$)", fila[1].strip("«»"))]
        if modulos and uc:
            out.append({"modulos": modulos, "uc": uc})
    return out


class Ecp:
    """Denominación de cada ECP (anexo I del RD 532/2025) y UC suprimidas con su ECP equivalente."""

    def __init__(self):
        self.doc = Boe(RD_532)
        self.nombres, self.suprimidas = {}, {}
        for e in self.doc.elems:
            if e["tipo"] != "tabla":
                continue
            cab = " ".join(e["filas"][0]) if e["filas"] else ""
            for f in e["filas"][1:]:
                if "suprimidos" in cab and len(f) >= 3:
                    for uc in re.findall(r"(?:UC|ECP)(\d{4}_\d)", f[0]):
                        self.suprimidas.setdefault(uc, []).extend(re.findall(r"ECP(\d{4}_\d)", f[2]))
                for c in f:
                    m = re.match(r"^ECP(\d{4}_\d)\s*-\s*(.+)$", c)
                    if m:
                        self.nombres[m.group(1)] = m.group(2)


# ---------------------------------------------------------------------------------------------------------------------
# DOGV (PDF): texto con pdftotext -layout
# ---------------------------------------------------------------------------------------------------------------------
class Dogv:
    def __init__(self, cve: str):
        d = DOCUMENTOS_DOGV[cve]
        self.id, self.url, self.enlace, self.publicado = cve, d["url"], d["enlace"], d["publicado"]
        self.bytes = descargar(self.url, f"dogv/{cve}.pdf")
        pdf = _cache() / f"dogv/{cve}.pdf"
        txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, check=True).stdout
        lineas = unicodedata.normalize("NFC", txt.decode("utf-8")).replace("\f", "\n").split("\n")
        # fuera cabeceras y pies de página
        self.lineas = [x.rstrip() for x in lineas
                       if not re.match(r"^\s*(CVE: DOGV-C-|Núm\. \d+ / \d{2}\.\d{2}\.\d{4})", x)]
        primera = subprocess.run(["pdftotext", "-l", "1", str(pdf), "-"], capture_output=True, check=True).stdout
        self.portada = unicodedata.normalize("NFC", primera.decode("utf-8"))

    def titulo(self) -> str:
        return titulo_dogv(self.portada)

    def buscar(self, patron: str, desde: int = 0) -> int:
        for k in range(desde, len(self.lineas)):
            if re.search(patron, self.lineas[k]):
                return k
        raise SystemExit(f"{self.id}: no encuentro «{patron}»")


def titulo_dogv(portada: str) -> str:
    """Título en castellano de la primera página de un PDF del DOGV (los antiguos llevan detrás «[año/inserción]»)."""
    m = re.search(r"((?:DECRETO|ORDEN|RESOLUCIÓN|CORRECCIÓN DE ERRORES) .+?\.)\s+(?:\[\d{4}/\d+\]\s+)?"
                  r"(?:Índice|ÍNDICE|ÍNDEX|La |Advertido|Preámbulo)", limpio(portada))
    return m.group(1) if m else ""


RE_COD_HORARIO = r"(\d{4}p?|\d{7}|\d{4}[A-Z]\d{2}|CVOP[MS]\d{3}|CV\d{4})"


def horario(doc: Dogv, ciclo: str, grado: str) -> dict:
    """Módulos de un ciclo con curso, h/semana y h/año (anexo IV del Decreto 95/2026)."""
    ini = doc.buscar(r"ANEXO IV\. Modificación de los anexos I y II del Decreto 114/2025")
    gm = doc.buscar(r"^\s*ANEXO I\. Secuenciación y horario GM", ini)
    gs = doc.buscar(r"^\s*ANEXO II\. Secuenciación y horario GS", gm)
    fin = doc.buscar(r"^\s*ANEXO V\. Incorporación", gs)
    a, b = (gm, gs) if grado == "GM" else (gs, fin)
    k = next((k for k in range(a, b) if re.fullmatch(rf"\s+{re.escape(ciclo)}\s*", doc.lineas[k])), None)
    if k is None:
        raise SystemExit(f"{doc.id}: no encuentro el ciclo «{ciclo}» en el anexo {'I' if grado == 'GM' else 'II'}")
    filas, curso, totales, previos, bloque = [], None, {}, [], []
    for linea in doc.lineas[k + 1:b]:
        bloque.append(linea)
        s = linea.strip()
        if not s:
            continue
        if re.match(r"^Total( ciclo)?$", s) or re.match(r"^Total ciclo\s+60", s):
            break
        m_tot = re.match(r"^Total ([12])º\s+(\d+)\s+([\d.]+)$", s)
        if m_tot:
            totales[int(m_tot.group(1))] = (int(m_tot.group(2)), int(m_tot.group(3).replace(".", "")))
            previos = []
            continue
        m = re.match(rf"^(?:([12])º\s+)?{RE_COD_HORARIO}(?:\s+(.*?))?\s+(\d{{1,2}})\s+([\d.]+)$", s)
        if m:
            if m.group(1):
                curso = int(m.group(1))
            nombre = (m.group(3) or "").strip()
            fila = {"codigo": m.group(2), "curso": curso, "h_sem": int(m.group(4)),
                    "h_anuales": int(m.group(5).replace(".", "")), "nombre": nombre, "partido": not nombre}
            if not nombre:
                fila["nombre"] = " ".join(previos)
            previos = []
            filas.append(fila)
        elif re.match(r"^[12]º$", s):
            curso = int(s[0])
        else:
            # trozo de nombre partido en varias líneas: antes de un código sin nombre o detrás de uno partido
            if filas and filas[-1]["partido"] and not previos:
                filas[-1]["nombre"] = (filas[-1]["nombre"] + " " + s).strip()
                filas[-1]["partido"] = False
            else:
                previos.append(s)
    for f in filas:
        f.pop("partido", None)
        f["nombre"] = limpio(f["nombre"])
    return {"filas": filas, "totales": totales, "huella": huella_texto(bloque)}


def ra_dogv(doc: Dogv, inicio: str, seccion: str | None = None) -> dict:
    """RA y criterios de un anexo del DOGV, desde su encabezado hasta «CONTENIDOS»."""
    desde = doc.buscar(seccion) if seccion else 0
    k = doc.buscar(inicio, desde)
    r = doc.buscar(r"^\s*RESULTADOS DE APRENDIZAJE", k)
    f = doc.buscar(r"^\s*CONTENIDOS", r)
    # Las mismas reglas que en el BOE: cada línea es un párrafo (las que continúan uno se pegan al anterior)
    texto = "\n".join(x.strip() for x in doc.lineas[r + 1:f] if x.strip())
    texto = re.sub(r"\s*Criterios\s+de\s+evaluación:?", "\n", texto)
    lineas = [re.sub(r"^RA\s*(?=\d)", "", x) for x in texto.split("\n") if x.strip()]
    ra = leer_ra(lineas, sin_letra=False)   # en el DOGV todos los criterios llevan letra
    for x in ra:
        x["texto"] = limpio(x["texto"])
        for c in x["criterios"]:
            c["texto"] = limpio(c["texto"])
    return {"ra": ra, "huella": huella_texto(doc.lineas[k:f])}


# ---------------------------------------------------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------------------------------------------------
def leer_yaml(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.is_file() else None


class _Dumper(yaml.SafeDumper):
    """Los códigos («0518», «1665031») siempre entre comillas: en YAML 1.2 una cifra con cero delante sería un número."""


def _str(dumper, s):
    estilo = "'" if re.fullmatch(r"[\d_.:+-]+|[\d]+p?|no|yes|on|off|y|n", s, re.I) else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", s, style=estilo)


_Dumper.add_representer(str, _str)


def escribir_yaml(p: Path, datos) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    texto = yaml.dump(datos, Dumper=_Dumper, allow_unicode=True, sort_keys=False, width=10_000, default_flow_style=False)
    texto = "# Generado por scripts/catalogo.py construir: no se edita a mano.\n" + texto
    if not p.is_file() or p.read_text(encoding="utf-8") != texto:   # sin reescrituras inútiles (iCloud las duplica)
        p.write_text(texto, encoding="utf-8")


def ra_catalogo(ra: list[dict]) -> list[dict]:
    """RA leídos → formato del catálogo (textos por idioma; `n_boe` y `letra_boe` solo si el BOE imprime otra cosa)."""
    out = []
    for r in ra:
        x = {"n": r["n"]}
        if "n_boe" in r:
            x["n_boe"] = r["n_boe"]
        x["texto"] = es(r["texto"])
        x["criterios"] = []
        for c in r["criterios"]:
            y = {"letra": c["letra"]}
            if "letra_boe" in c:
                y["letra_boe"] = c["letra_boe"]
            y["texto"] = es(c["texto"])
            x["criterios"].append(y)
        out.append(x)
    return out


def tipo_de(codigo: str, nombre: str) -> str:
    if codigo in ("0156", "0179"):
        return "ingles"
    if codigo in ("1709", "1710"):
        return "empleabilidad"
    if codigo.startswith("1664") or codigo.startswith("1665"):
        return "digitalizacion"
    if codigo.startswith("1708") and len(codigo) == 7:
        return "sostenibilidad"
    if codigo.startswith("CVOP"):
        return "optativo"
    if codigo.startswith("CV"):
        return "autonomico"
    if codigo.startswith("1713") or nombre.lower().startswith("proyecto intermodular"):
        return "proyecto"
    return "propio"


def base_de(codigo: str, tipo: str) -> str | None:
    """Archivo de modulos/ con los RA de un código del horario (1665031 → 1665, 0526p → 0526)."""
    if tipo == "optativo":
        return None
    if tipo in ("digitalizacion", "sostenibilidad"):
        return codigo[:4]
    return codigo.rstrip("p")


class Construccion:
    def __init__(self):
        self.boe: dict[str, Boe] = {}
        self.dogv: dict[str, Dogv] = {}
        self._ecp = None
        self.fuentes: dict[str, dict] = {}   # cada documento leído en esta construcción, con su huella
        self.avisos: list[str] = []

    def b(self, ident: str) -> Boe:
        if ident not in self.boe:
            self.boe[ident] = Boe(ident)
            d = self.boe[ident]
            self.fuentes[ident] = {"id": ident, "tipo": "boe", "titulo": es(d.titulo),
                                   "url": f"https://www.boe.es/diario_boe/xml.php?id={ident}", "enlace": d.enlace,
                                   "publicado": d.publicado, "huella": huella_bytes(d.bytes), "consultado": HOY}
        return self.boe[ident]

    def d(self, cve: str) -> Dogv:
        if cve not in self.dogv:
            self.dogv[cve] = Dogv(cve)
            d = self.dogv[cve]
            self.fuentes[cve] = {"id": cve, "tipo": "dogv", "titulo": es(d.titulo()), "url": d.url, "enlace": d.enlace,
                                 "publicado": d.publicado, "huella": huella_bytes(d.bytes), "consultado": HOY}
        return self.dogv[cve]

    @property
    def ecp(self) -> Ecp:
        if self._ecp is None:
            self.b(RD_532)
            self._ecp = Ecp()
        return self._ecp

    # -- módulos ------------------------------------------------------------------------------------------------------
    def modulos_titulo(self, sigla: str) -> tuple[dict, dict]:
        """Módulos del anexo I en su redacción vigente y la norma de la que sale cada uno."""
        receta = CICLOS[sigla]
        base = self.b(receta["rd"])
        mods = modulos_boe(base.seccion(r"(?i)^anexo I$", r"(?i)^anexo II\b"))
        origen = {c: (receta["rd"], "Anexo I") for c in mods}
        for norma, ini, fin in receta.get("reescritos", []):
            nuevos = modulos_boe(self.b(norma).seccion(ini, fin))
            for c, m in nuevos.items():
                mods[c] = m
                origen[c] = (norma, limpio(ini.strip("^\\.").replace("\\", "")) + ", anexo I")
        return mods, origen

    def construir_ciclo(self, sigla: str) -> dict:
        receta = CICLOS[sigla]
        rd = self.b(receta["rd"])
        hor_doc = self.d(DOGV_95)
        hor = horario(hor_doc, receta["horario"], receta["grado"])
        if sorted(hor["totales"]) != [1, 2]:
            raise SystemExit(f"{sigla}: no encuentro los totales de 1.º y 2.º en el horario")
        for curso, (hs, ha) in hor["totales"].items():
            fs = [f for f in hor["filas"] if f["curso"] == curso]
            if sum(f["h_sem"] for f in fs) != hs or sum(f["h_anuales"] for f in fs) != ha:
                raise SystemExit(f"{sigla}: el horario de {curso}.º no suma los totales del decreto")
        mods, origen = self.modulos_titulo(sigla)

        # Familia y título (art. 2 y título del real decreto)
        art2 = " ".join(articulo_texto(rd.elems, 2))
        familia = re.search(r"Familia [Pp]rofesional:\s*(.+?)\.", art2)
        titulo = re.search(r"título de (T[ée]cnico(?: Superior)? en .+?) y se fijan", rd.titulo, re.I)
        if not familia or not titulo:
            raise SystemExit(f"{sigla}: no encuentro familia o título en {rd.id}")
        titulo_txt = titulo.group(1)
        titulo_txt = titulo_txt[0].upper() + titulo_txt[1:]

        # Competencia general (art. 4) y competencias (art. 5)
        elems_art4 = rd.elems
        if receta.get("art4"):
            norma, ini, fin = receta["art4"]
            elems_art4 = self.b(norma).seccion(ini, fin)
        cg = " ".join(articulo_texto(elems_art4, 4))
        competencias = con_letras(competencias_titulo(rd.elems))
        self.competencias = getattr(self, "competencias", {})
        self.competencias[sigla] = competencias
        if not cg or not competencias:
            raise SystemExit(f"{sigla}: sin competencia general o competencias en {rd.id}")

        # Anexo V B)
        if receta.get("anexo_v"):
            norma, patron = receta["anexo_v"]
            doc_v = self.b(norma)
            elems_v = doc_v.seccion(patron, r"^Disposición ") if patron.startswith("^") else \
                doc_v.seccion_de_rd(r"Artículo tercero\.", patron)
            fuente_v = norma
        else:
            elems_v, fuente_v = rd.elems, rd.id
        correspondencias = []
        filas_v = anexo_vb(elems_v)
        if not filas_v:
            self.avisos.append(f"{sigla}: sin anexo V B) en {fuente_v}")
        for fila in filas_v:
            ecps = []
            for uc, texto_uc in fila["uc"]:
                errata = ERRATAS_UC.get(fuente_v, {}).get(uc)
                if errata:
                    ecps.append({"codigo": f"ECP{errata[0]}", "texto": es(self.ecp.nombres[errata[0]]),
                                 "uc": f"UC{errata[0]}", "uc_boe": f"UC{uc}", "correccion": errata[1]})
                elif uc in self.ecp.nombres:
                    ecps.append({"codigo": f"ECP{uc}", "texto": es(self.ecp.nombres[uc]), "uc": f"UC{uc}"})
                elif uc in self.ecp.suprimidas:
                    for eq in self.ecp.suprimidas[uc]:
                        ecps.append({"codigo": f"ECP{eq}", "texto": es(self.ecp.nombres.get(eq, "")), "uc": f"UC{uc}",
                                     "equivalente": True})
                else:
                    ecps.append({"codigo": None, "texto": es(texto_uc), "uc": f"UC{uc}",
                                 "pendiente": "La UC no está en el anexo I del RD 532/2025: sin ECP; texto de la UC "
                                              "(docs/PENDIENTE.md)"})
                    self.avisos.append(f"{sigla}: UC{uc} sin ECP en el RD 532/2025")
            correspondencias.append({"modulos": fila["modulos"], "ecp": ecps, "fuente": fuente_v})

        # Módulos del ciclo (horario) y sus archivos de RA
        modulos = []
        for f in hor["filas"]:
            tipo = tipo_de(f["codigo"], f["nombre"])
            entrada = {"codigo": f["codigo"], "modulo": base_de(f["codigo"], tipo), "nombre": es(f["nombre"]),
                       "curso": f["curso"], "h_sem": f["h_sem"], "h_anuales": f["h_anuales"], "tipo": tipo}
            if tipo == "optativo":
                entrada["modulo"] = None
                if sigla not in OPTATIVOS_OFERTADOS:
                    entrada["pendiente"] = PENDIENTE_OPTATIVO
            if tipo == "proyecto" and receta["grado"] == "GM":
                entrada["modulo"] = None
                entrada["pendiente"] = PENDIENTE_PROYECTO_GM
            modulos.append(entrada)
            if entrada["modulo"] and tipo in ("propio", "proyecto"):
                c = entrada["modulo"]
                if c not in mods:
                    entrada["pendiente"] = f"El módulo no está en el anexo I de {receta['rd']}"
                    entrada["modulo"] = None
                    self.avisos.append(f"{sigla}: {c} no está en el anexo I de {receta['rd']}")
                    continue
                self.propios.setdefault(c, {})[sigla] = (mods[c], origen[c], f["nombre"], tipo)
        proyecto = next((m["codigo"] for m in modulos if m["tipo"] == "proyecto" and not m["codigo"].endswith("p")), None)

        optativos = []
        for o in OPTATIVOS_OFERTADOS.get(sigla, []):
            optativos.append({"codigo": o["codigo"], "modulo": o["modulo"], "nombre": es(COMUNES[o["modulo"]]["nombre"]),
                              "curso": 2, "fuente": "Oferta del centro: programaciones de SEA, STI y ARI (2.2), "
                                                    "0179 confirmado por CarlosFB el 2026-10-14"})

        posteriores = rd.posteriores()
        modificado_por = [p["id"] for p in posteriores if "MODIFICA" in p["relacion"].upper()]
        correcciones = [p["id"] for p in posteriores if "CORRECCI" in p["relacion"].upper()]
        for p in modificado_por + correcciones:
            self.b(p)
        datos = {
            "formato": FORMATO,
            "sigla": sigla,
            "grado": receta["grado"],
            "familia": es(familia.group(1)),
            "nombre": es(receta["horario"]),
            "titulo": es(titulo_txt),
            "rd": {"id": rd.id, "nombre": es(rd.titulo), "enlace": rd.enlace, "modificado_por": modificado_por,
                   "correcciones": correcciones, "posteriores": posteriores},
            "competencia_general": es(cg),
            **corregir_ciclo(sigla, "competencia_general", limpio(cg)),
            "competencias": [{"letra": c["letra"], **({"numero_boe": c["numero_boe"]} if "numero_boe" in c else {}),
                              "texto": es(c["texto"])} for c in competencias],
            "correspondencias_ecp": correspondencias,
            "modulos": modulos,
            "optativos_ofertados": optativos,
            "proyecto": proyecto,
            "fuentes": {"titulo": rd.id, "competencia_general": elems_art4 is rd.elems and rd.id or receta["art4"][0],
                        "competencias": rd.id, "correspondencias_ecp": fuente_v, "ecp": RD_532,
                        "horario": hor_doc.id, "huella_horario": hor["huella"]},
            "comprobado": HOY,
        }
        return datos

    def modulos_propios(self) -> dict[str, dict]:
        """Archivos de modulos/ de los módulos propios y de proyecto. Un módulo de dos títulos (0237 y 0238 en IT e IEA,
        0260 en CAR y EMV) va en un solo archivo si su texto es idéntico en los dos reales decretos; si no, uno por
        título (`0237-IT`, `0237-IEA`) y cada ciclo apunta al suyo."""
        out, ids = {}, {}
        for codigo, por_ciclo in sorted(self.propios.items()):
            grupos: list[tuple[list, list[str]]] = []
            for sigla, (m, _origen, _nh, _t) in por_ciclo.items():
                ra = ra_catalogo(m["ra"])
                g = next((g for g in grupos if g[0] == ra), None)
                if g:
                    g[1].append(sigla)
                else:
                    grupos.append((ra, [sigla]))
            for ra, siglas in grupos:
                ident = codigo if len(grupos) == 1 else f"{codigo}-{'-'.join(siglas)}"
                if len(grupos) > 1:
                    self.avisos.append(f"{codigo}: el texto cambia según el título; {'/'.join(siglas)} → modulos/{ident}.yaml")
                m, origen, nombre_horario, tipo = por_ciclo[siglas[0]]
                nombre = limpio(m["nombre"])
                if tipo == "proyecto":
                    # RD 500/2024: «Proyecto» pasa a «Proyecto intermodular»; el nombre, el del Decreto 95/2026
                    nombre = nombre_horario
                elif limpio(nombre_horario).lower() != nombre.lower():
                    self.avisos.append(f"{codigo}: nombre en el RD «{nombre}» y en el Decreto 95/2026 «{nombre_horario}»")
                normas = []
                for s in siglas:
                    if por_ciclo[s][1][0] not in normas:
                        normas.append(por_ciclo[s][1][0])
                fuente = {"norma": normas[0], "bloque": f"{origen[1]}, módulo {codigo}",
                          "version": self.b(normas[0]).publicado, "huella": m["huella"], "comprobado": HOY}
                if normas[1:]:
                    fuente["tambien"] = normas[1:]
                comp = {}
                for s in siglas:
                    cm = por_ciclo[s][0]["competencias"]
                    comp[s] = [x["letra"] for x in self.competencias[s]] if cm == ["todas"] else cm
                out[ident] = {"formato": FORMATO, "id": ident, "codigo": codigo, "nombre": es(nombre), "tipo": tipo,
                              "competencias_modulo": comp,
                              "ra": ra, "fuente": fuente}
                for s in siglas:
                    ids[(codigo, s)] = ident
        self.ids_propios = ids
        return out

    def construir_comunes(self) -> dict[str, dict]:
        out = {}
        for codigo, receta in COMUNES.items():
            doc = self.d(receta["doc"])
            r = ra_dogv(doc, receta["inicio"], receta.get("seccion"))
            nombre = receta.get("nombre") or self._nombre_comun.get(codigo, "")
            if not nombre:
                self.avisos.append(f"{codigo}: sin nombre en el horario")
            ra = ra_catalogo(r["ra"])
            out[codigo] = {"formato": FORMATO, "id": codigo, "codigo": codigo, "nombre": es(nombre), "tipo": receta["tipo"],
                           "competencias_modulo": {}, "ra": ra,
                           "fuente": {"norma": doc.id, "bloque": limpio(re.sub(r"^\^\\s\*|\\", "", receta["inicio"])),
                                      "version": doc.publicado, "huella": r["huella"], "comprobado": HOY}}
        return out

    def construir_normativa(self, ciclos: dict[str, dict]) -> dict:
        """Normas de los apartados 1.1 y 1.2 (docs/DOCUMENTO_GENERADO.md), con su título oficial y enlace."""
        estatal = [("BOE-A-2006-7899", "todos", "https://www.boe.es/buscar/act.php?id=BOE-A-2006-7899"),
                   ("BOE-A-2020-17264", "todos", "https://www.boe.es/buscar/doc.php?id=BOE-A-2020-17264"),
                   ("BOE-A-2022-5139", "todos", "https://www.boe.es/buscar/act.php?id=BOE-A-2022-5139"),
                   ("BOE-A-2023-16889", "todos", "https://www.boe.es/buscar/act.php?id=BOE-A-2023-16889"),
                   ("BOE-A-2024-10684", "GM", "https://www.boe.es/buscar/doc.php?id=BOE-A-2024-10684"),
                   ("BOE-A-2024-10685", "GS", "https://www.boe.es/buscar/doc.php?id=BOE-A-2024-10685"),
                   (RD_532, "todos", "https://www.boe.es/buscar/doc.php?id=BOE-A-2025-13147")]
        normas = []
        for ident, aplica, enlace in estatal:
            d = self.b(ident)
            normas.append({"id": ident, "ambito": "estatal", "titulo": es(d.titulo), "fecha": d.publicado,
                           "diario": "BOE", "enlace": enlace, "aplica": aplica})
        # Real decreto de cada título, las normas que lo modifican y sus correcciones de errores (apartado 1.1)
        generales = {ident for ident, _a, _e in estatal}
        por_norma: dict[str, list[str]] = {}
        for sigla in ORDEN_CICLOS:
            rd = ciclos[sigla]["rd"]
            for ident in [rd["id"], *rd["modificado_por"], *rd.get("correcciones", [])]:
                if ident not in generales:
                    por_norma.setdefault(ident, []).append(sigla)
        for ident, siglas in por_norma.items():
            d = self.b(ident)
            normas.append({"id": ident, "ambito": "estatal", "titulo": es(d.titulo), "fecha": d.publicado,
                           "diario": "BOE", "enlace": d.enlace, "aplica": siglas})
        for cve, aplica in (("DOGV-C-2019-4442", "todos"), (DOGV_114, "todos"), (DOGV_95, "todos"),
                            ("DOGV-C-2026-22324", "todos"), ("DOGV-C-2025-13083", "todos"),
                            ("DOGV-C-2026-10102", "todos"), ("DOGV-C-2026-24495", "todos")):
            d = self.d(cve)
            n = {"id": cve, "ambito": "autonomico", "titulo": es(d.titulo()), "fecha": d.publicado, "diario": "DOGV",
                 "enlace": d.enlace, "aplica": aplica}
            if cve == "DOGV-C-2026-24495":
                n["curso_escolar"] = "2026-2027"
            normas.append(n)
        normas.sort(key=lambda n: (n["fecha"], n["id"]))
        return {"formato": FORMATO, "normas": normas, "comprobado": HOY}

    def construir(self, siglas: list[str]) -> None:
        """Rehace todo en memoria (los módulos compartidos dependen de varios ciclos) y escribe lo de `siglas`."""
        self.propios = {}
        ciclos = {s: self.construir_ciclo(s) for s in ORDEN_CICLOS}
        propios = self.modulos_propios()
        self._nombre_comun = {}
        for s, datos in ciclos.items():
            for m in datos["modulos"]:
                if m["tipo"] in ("propio", "proyecto") and m["modulo"]:
                    m["modulo"] = self.ids_propios[(m["modulo"], s)]
                if m["tipo"] in COMUNES_TIPOS and m["modulo"]:
                    self._nombre_comun.setdefault(m["modulo"], m["nombre"]["es"])
        comunes = self.construir_comunes()
        modulos = {**propios, **comunes}
        aplicar_correcciones(modulos)
        todo = set(siglas) == set(CICLOS)
        if todo:
            for viejo in list((CATALOGO / "modulos").glob("*.yaml")) + list((CATALOGO / "ciclos").glob("*.yaml")):
                if viejo.stem not in modulos and viejo.stem not in ciclos:
                    viejo.unlink()
        usados = {m["modulo"] for s in siglas for m in ciclos[s]["modulos"] if m["modulo"]}
        usados |= {o["modulo"] for s in siglas for o in ciclos[s]["optativos_ofertados"]}
        for s in siglas:
            escribir_yaml(CATALOGO / "ciclos" / f"{s}.yaml", ciclos[s])
            print(f"✓ {s}: {len(ciclos[s]['modulos'])} módulos")
        for ident, datos in sorted(modulos.items()):
            if todo or ident in usados:
                escribir_yaml(CATALOGO / "modulos" / f"{ident}.yaml", datos)
        escribir_yaml(CATALOGO / "normativa.yaml", self.construir_normativa(ciclos))
        escribir_yaml(CATALOGO / "fuentes.yaml", {"formato": FORMATO, "fuentes": sorted(self.fuentes.values(),
                                                                                         key=lambda f: f["id"])})
        for a in self.avisos:
            print("  aviso:", a)


COMUNES_TIPOS = ("ingles", "empleabilidad", "digitalizacion", "sostenibilidad", "autonomico")


def corregir_ciclo(sigla: str, campo: str, literal: str, correcciones: dict | None = None) -> dict:
    """{campo}_corregida y {campo}_correccion si el texto del ciclo tiene una errata en CORRECCIONES_CICLO."""
    c = (CORRECCIONES_CICLO if correcciones is None else correcciones).get((sigla, campo))
    if not c:
        return {}
    viejo, nuevo, motivo = c
    if literal.count(viejo) != 1:
        raise SystemExit(f"Corrección de {sigla} {campo}: «{viejo}» no está (una vez) en el texto del BOE")
    return {f"{campo}_corregida": es(literal.replace(viejo, nuevo)), f"{campo}_correccion": motivo}


def aplicar_correcciones(modulos: dict[str, dict], correcciones: dict | None = None) -> None:
    """Añade a los RA y criterios de CORRECCIONES el texto corregido y su motivo; el literal se queda en `texto`."""
    for (ident, n, letra), (viejo, nuevo, motivo) in (CORRECCIONES if correcciones is None else correcciones).items():
        ra = next((r for r in modulos.get(ident, {}).get("ra", []) if r["n"] == n), None)
        elem = ra if ra is None or letra is None else next((c for c in ra["criterios"] if c["letra"] == letra), None)
        if elem is None:
            raise SystemExit(f"Corrección de {ident} RA{n} {letra or ''}: no existe en el catálogo")
        literal = elem["texto"]["es"]
        if literal.count(viejo) != 1:
            raise SystemExit(f"Corrección de {ident} RA{n} {letra or ''}: «{viejo}» no está (una vez) en el texto del BOE")
        elem["corregido"] = es(literal.replace(viejo, nuevo))
        elem["correccion"] = motivo


# ---------------------------------------------------------------------------------------------------------------------
# Comprobación
# ---------------------------------------------------------------------------------------------------------------------
def esquema(nombre: str) -> dict:
    return json.loads((ESQUEMAS / f"{nombre}.schema.json").read_text(encoding="utf-8"))


def comprobar(catalogo: Path = CATALOGO, red: bool = False, siglas: set[str] | None = None) -> list[str]:
    """Errores del catálogo (lista vacía = limpio)."""
    from jsonschema import Draft202012Validator
    errores: list[str] = []

    def validar(datos, nombre, donde):
        for e in Draft202012Validator(esquema(nombre)).iter_errors(datos):
            ruta = "/".join(str(x) for x in e.absolute_path)
            errores.append(f"{donde}: {ruta or '(raíz)'}: {e.message}")

    fuentes_doc = leer_yaml(catalogo / "fuentes.yaml")
    if fuentes_doc is None:
        return [f"{catalogo / 'fuentes.yaml'}: no existe"]
    validar(fuentes_doc, "catalogo_fuentes", "fuentes.yaml")
    fuentes = {f["id"]: f for f in fuentes_doc.get("fuentes", [])}

    modulos = {}
    for p in sorted((catalogo / "modulos").glob("*.yaml")):
        m = leer_yaml(p)
        validar(m, "catalogo_modulo", f"modulos/{p.name}")
        if not isinstance(m, dict):
            continue
        if m.get("id") != p.stem or not p.stem.startswith(str(m.get("codigo"))):
            errores.append(f"modulos/{p.name}: id {m.get('id')} o código {m.get('codigo')} no casan con el archivo")
        modulos[p.stem] = m
        ns = [r["n"] for r in m.get("ra", [])]
        if ns != list(range(1, len(ns) + 1)):
            errores.append(f"modulos/{p.name}: RA no numerados de 1 a {len(ns)}: {ns}")
        for r in m.get("ra", []):
            letras = [c["letra"] for c in r.get("criterios", [])]
            if letras != list(LETRAS[:len(letras)]) and letras != [x for x in LETRAS if x != "ñ"][:len(letras)]:
                errores.append(f"modulos/{p.name}: RA{r['n']}: criterios fuera de orden {letras}")
            if not letras:
                errores.append(f"modulos/{p.name}: RA{r['n']} sin criterios")
            for x in [r, *r.get("criterios", [])]:
                if "corregido" in x and x["corregido"].get("es") == x["texto"].get("es"):
                    errores.append(f"modulos/{p.name}: RA{r['n']} {x.get('letra', '')}: corrección igual al texto literal")
        norma = (m.get("fuente") or {}).get("norma")
        if norma not in fuentes:
            errores.append(f"modulos/{p.name}: su fuente {norma} no está en fuentes.yaml")

    usados = set()
    ciclos = {}
    for p in sorted((catalogo / "ciclos").glob("*.yaml")):
        c = leer_yaml(p)
        validar(c, "catalogo_ciclo", f"ciclos/{p.name}")
        if not isinstance(c, dict):
            continue
        ciclos[c.get("sigla")] = c
        for curso in (1, 2):
            fs = [m for m in c.get("modulos", []) if m.get("curso") == curso]
            if sum(m.get("h_sem", 0) for m in fs) != 30:
                errores.append(f"ciclos/{p.name}: {curso}.º suma {sum(m.get('h_sem', 0) for m in fs)} h/semana (no 30)")
            if sum(m.get("h_anuales", 0) for m in fs) != 1000:
                errores.append(f"ciclos/{p.name}: {curso}.º suma {sum(m.get('h_anuales', 0) for m in fs)} h/año (no 1000)")
        if c.get("competencia_general_corregida") == c.get("competencia_general"):
            errores.append(f"ciclos/{p.name}: competencia general corregida igual a la literal")
        letras = {x["letra"] for x in c.get("competencias", [])}
        codigos = {m["codigo"].rstrip("p") for m in c.get("modulos", [])}
        for m in c.get("modulos", []):
            ref = m.get("modulo")
            if ref:
                usados.add(ref)
                if ref not in modulos:
                    errores.append(f"ciclos/{p.name}: {m['codigo']} apunta a modulos/{ref}.yaml, que no existe")
                elif m.get("tipo") in ("propio", "proyecto"):
                    cm = modulos[ref].get("competencias_modulo", {}).get(c["sigla"])
                    if cm is None:
                        errores.append(f"modulos/{ref}.yaml: sin competencias del módulo en {c['sigla']}")
                    elif not set(cm) <= letras and not c.get("pendiente_competencias"):
                        errores.append(f"modulos/{ref}.yaml: competencias {sorted(set(cm) - letras)} que no tiene {c['sigla']}")
            elif not m.get("pendiente") and m.get("tipo") != "optativo":
                errores.append(f"ciclos/{p.name}: {m['codigo']} sin RA y sin motivo de pendiente")
            if m.get("tipo") == "optativo" and not m.get("pendiente") and not c.get("optativos_ofertados"):
                errores.append(f"ciclos/{p.name}: {m['codigo']} optativo sin oferta del centro ni pendiente")
        for o in c.get("optativos_ofertados", []):
            usados.add(o["modulo"])
            if o["modulo"] not in modulos:
                errores.append(f"ciclos/{p.name}: optativo {o['modulo']} sin modulos/{o['modulo']}.yaml")
        for corr in c.get("correspondencias_ecp", []):
            for mc in corr["modulos"]:
                if mc not in codigos:
                    errores.append(f"ciclos/{p.name}: correspondencia ECP con {mc}, que no es del ciclo")
        for clave, fid in (c.get("fuentes") or {}).items():
            if not clave.startswith("huella") and fid not in fuentes:
                errores.append(f"ciclos/{p.name}: fuente {fid} ({clave}) no está en fuentes.yaml")
    esperadas = set(CICLOS) if siglas is None else siglas
    if set(ciclos) != esperadas:
        errores.append(f"ciclos: faltan {sorted(esperadas - set(ciclos))} o sobran {sorted(set(ciclos) - esperadas)}")
    for codigo in sorted(set(modulos) - usados):
        errores.append(f"modulos/{codigo}.yaml: ningún ciclo lo usa")

    normativa = leer_yaml(catalogo / "normativa.yaml")
    validar(normativa, "catalogo_normativa", "normativa.yaml")
    fechas = [n["fecha"] for n in (normativa or {}).get("normas", [])]
    if fechas != sorted(fechas):
        errores.append("normativa.yaml: las normas no van por fecha creciente")

    if red:
        enlaces = {n["enlace"] for n in (normativa or {}).get("normas", [])} | {f["enlace"] for f in fuentes.values()}
        for u in sorted(enlaces):
            try:
                with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                    if r.status != 200:
                        errores.append(f"enlace {u}: respuesta {r.status}")
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                errores.append(f"enlace {u}: {e}")
    return errores


# ---------------------------------------------------------------------------------------------------------------------
# Comparación con una programación (.docx): apartado 11, RA y criterios literales
# ---------------------------------------------------------------------------------------------------------------------
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def ra_programacion(ruta: Path) -> list[dict]:
    """RA y criterios del apartado 11 («Criterios y procedimientos para la evaluación») de una programación."""
    from lxml import etree
    with zipfile.ZipFile(ruta) as z:
        x = etree.fromstring(z.read("word/document.xml"))
    parrafos = []
    for p in x.find(W + "body").iter(W + "p"):
        if any(a.tag == W + "tbl" for a in p.iterancestors()):
            continue
        estilo = p.find(f"{W}pPr/{W}pStyle")
        parrafos.append((estilo.get(W + "val") if estilo is not None else "",
                         limpio("".join(t.text or "" for t in p.iter(W + "t")))))
    i = next((k for k, (est, t) in enumerate(parrafos) if est.startswith("T") and est != "TDC2" and est != "TDC3"
              and re.match(r"^11\.\s*CRITERIOS Y PROCEDIMIENTOS", t, re.I)), None)
    if i is None:
        raise SystemExit(f"{ruta.name}: sin apartado 11")
    ra, actual = [], None
    for est, t in parrafos[i + 1:]:
        if est.startswith("Ttulo") or est.startswith("Heading"):
            break
        m = re.match(r"^R\.?\s?A\.?\s?(\d{1,2})\.?\s*[-.:]?\s*(.+)$", t)
        if m:
            actual = {"n": int(m.group(1)), "texto": m.group(2), "criterios": []}
            ra.append(actual)
        elif actual is not None and t and not re.match(r"^Criterios de evaluaci[óo]n[.:]?$", t, re.I):
            actual["criterios"].append(re.sub(r"^[a-zñ]\)\s*", "", t))
    return ra


def normal(s: str) -> str:
    s = limpio(s).replace("“", "«").replace("”", "»").replace('"', "«").replace("’", "'")
    return s.rstrip(" .;")


def comparar(ruta: Path, catalogo: Path = CATALOGO) -> list[dict]:
    """Diferencias entre los RA y criterios de la programación y los del catálogo (lista vacía = idénticos).

    Cada diferencia: {codigo, ra, letra (None si es el enunciado del RA), tipo, programacion, catalogo}."""
    m = re.match(r"^([A-Z]+) [12] - (\d{4}) - ", ruta.name)
    if not m:
        raise SystemExit(f"{ruta.name}: no sigue el patrón «SIGLA N - 0xxx - Nombre»")
    sigla, codigo = m.group(1), m.group(2)
    ciclo = leer_yaml(catalogo / "ciclos" / f"{sigla}.yaml") or {}
    ref = next((x["modulo"] for x in ciclo.get("modulos", []) if x["codigo"] == codigo and x.get("modulo")), None)
    mod = leer_yaml(catalogo / "modulos" / f"{ref}.yaml") if ref else None
    if not mod:
        return [{"codigo": codigo, "ra": None, "letra": None, "tipo": "sin módulo en el catálogo",
                 "programacion": "", "catalogo": ""}]
    prog = ra_programacion(ruta)
    dif = []

    def d(ra, letra, tipo, a, b):
        dif.append({"codigo": codigo, "ra": ra, "letra": letra, "tipo": tipo, "programacion": a, "catalogo": b})

    if len(prog) != len(mod["ra"]):
        d(None, None, "número de RA", str(len(prog)), str(len(mod["ra"])))
    for p, c in zip(prog, mod["ra"], strict=False):
        texto = c.get("corregido", c["texto"])["es"]   # el documento lleva la corrección de las erratas
        if normal(p["texto"]) != normal(texto):
            d(c["n"], None, "enunciado", p["texto"], texto)
        crit = c["criterios"]
        if len(p["criterios"]) != len(crit):
            d(c["n"], None, "número de criterios", str(len(p["criterios"])), str(len(crit)))
        for a, b in zip(p["criterios"], crit, strict=False):
            texto = b.get("corregido", b["texto"])["es"]
            if normal(a) != normal(texto):
                d(c["n"], b["letra"], "criterio", a, texto)
    return dif


def describir(x: dict) -> str:
    donde = f"{x['codigo']}" + (f" RA{x['ra']}" if x["ra"] else "") + (f" {x['letra']})" if x["letra"] else "")
    if x["tipo"] in ("enunciado", "criterio"):
        return f"{donde}: programación «{x['programacion']}» · catálogo «{x['catalogo']}»"
    return f"{donde}: {x['tipo']}: programación {x['programacion']} · catálogo {x['catalogo']}"


# ---------------------------------------------------------------------------------------------------------------------
def main() -> int:
    global SIN_RED
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    c = sub.add_parser("construir")
    c.add_argument("ciclo", help="sigla del ciclo o «todo»")
    c.add_argument("--sin-red", action="store_true", help="solo con los documentos ya descargados")
    k = sub.add_parser("comprobar")
    k.add_argument("--red", action="store_true", help="comprueba además que los enlaces responden")
    k.add_argument("--catalogo", type=Path, default=CATALOGO)
    p = sub.add_parser("comparar")
    p.add_argument("docx", nargs="+", type=Path)
    a = ap.parse_args()
    if a.orden == "construir":
        SIN_RED = a.sin_red
        siglas = list(CICLOS) if a.ciclo.lower() == "todo" else [a.ciclo.upper()]
        if not set(siglas) <= set(CICLOS):
            raise SystemExit(f"Ciclo desconocido: {a.ciclo}. Ciclos: {', '.join(ORDEN_CICLOS)}")
        Construccion().construir(siglas)
        return 0
    if a.orden == "comprobar":
        errores = comprobar(a.catalogo, red=a.red)
        for e in errores:
            print("✗", e)
        print(f"{'Catálogo limpio' if not errores else f'{len(errores)} errores'}")
        return 1 if errores else 0
    total = 0
    for ruta in a.docx:
        dif = comparar(ruta)
        total += len(dif)
        print(f"{'✓' if not dif else '✗'} {ruta.name}: {'RA y criterios idénticos' if not dif else f'{len(dif)} diferencias'}")
        for x in dif:
            print("   ", describir(x))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
