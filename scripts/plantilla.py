#!/usr/bin/env python3
"""Plantilla con marcas a partir de la programación de PIICT (0517), la plantilla vigente desde el 2026-10-06.

Uso:
  plantilla.py crear <PIICT.docx> --proyecto <0526.docx>   escribe src/programaciones/recursos/plantilla/es/
  plantilla.py comprobar                              la plantilla del repositorio: marcas, partes y datos personales

La plantilla se guarda desempaquetada (las partes XML del .docx): así la barrera de secretos lee su contenido y cada
cambio se ve en git (ADR-019). La app la empaqueta en memoria.

Qué hace `crear`:
- Quita lo que no es de la plantilla: comentarios, personas, metadatos de SharePoint (customXml, propiedades
  personalizadas), el autor, la configuración web y el correo del pie (repositorio público: va a Ajustes).
- Deja los textos fijos de PIICT y cambia por marcas lo que depende del ciclo, del módulo, del curso o del profesor
  (marcas en docs/DOCUMENTO_GENERADO.md, «Plantilla y marcas»).
- Quita los párrafos propios de PIICT (metodología, recursos, aula, unidades, RA…): los pone la app.
- Añade la variante de los proyectos (CarlosFB, 2026-10-17, ADR-020): la tabla 4 y los bloques de calificación (9),
  instrumentos (11.1) y elementos de evaluación (11.2) de la programación del Proyecto de 0526.
- Rehace la tabla 4.1 con las columnas que decidió CarlosFB el 2026-10-17 (ADR-025): RA · Modalidad · Horas Centro ·
  Horas Empresa · % Horas Centro · % Horas Empresa, y la fila TOTAL combinada.
- Quita Times New Roman de los estilos (restos de un pegado desde HTML, como `p1`) y de `docDefaults`: la fuente
  de cada ranura, también la asiática con la que Word dibuja «→», es la del texto de la plantilla.
"""
from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from lxml import etree  # noqa: E402

from programaciones import ooxml  # noqa: E402
from programaciones.ooxml import W, normal, texto  # noqa: E402

DESTINO = RAIZ / "src" / "programaciones" / "recursos" / "plantilla" / "es"

# Partes que se quedan; el resto (comentarios, personas, customXml, propiedades personalizadas, webSettings) fuera
PARTES = {
    "word/document.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    "word/styles.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
    "word/numbering.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml",
    "word/settings.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml",
    "word/fontTable.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml",
    "word/theme/theme1.xml": "application/vnd.openxmlformats-officedocument.theme+xml",
    "word/footnotes.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml",
    "word/endnotes.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml",
    "word/header1.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml",
    "word/header2.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml",
    "word/footer1.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
    "word/footer2.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
    "docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
    "docProps/app.xml": "application/vnd.openxmlformats-officedocument.extended-properties+xml",
}
CORE = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<cp:coreProperties xmlns:cp="http://schemas.openxml'
        'formats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms='
        '"http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Programación '
        'didáctica</dc:title><dc:creator>Programaciones</dc:creator><cp:lastModifiedBy>Programaciones</cp:lastModifiedBy>'
        '<dcterms:created xsi:type="dcterms:W3CDTF">2026-10-06T00:00:00Z</dcterms:created><dcterms:modified '
        'xsi:type="dcterms:W3CDTF">2026-10-06T00:00:00Z</dcterms:modified></cp:coreProperties>')
APP = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Properties xmlns="http://schemas.openxmlformats.org/'
       'officeDocument/2006/extended-properties"><Application>Microsoft Office Word</Application><DocSecurity>0'
       '</DocSecurity><AppVersion>16.0000</AppVersion></Properties>')
RELS_RAIZ = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxml'
             'formats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
             'officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" '
             'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
             'Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/'
             'officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>')
TIPOS_RELS_DOC = {"styles", "numbering", "settings", "fontTable", "theme", "footnotes", "endnotes", "header", "footer",
                  "hyperlink"}

MARCA = re.compile(r"\{\{[^{}]+\}\}")
VINETAS: dict[str, str] = {}
VERSION = "2026-10-17"   # la de PIICT revisada por CarlosFB con la 4.1 nueva; sube si cambia la plantilla (R5)
METADATOS = DESTINO.parent / "plantilla.yaml"


# ---------------------------------------------------------------------------------------------------------------------
# Marcas dentro de un párrafo
# ---------------------------------------------------------------------------------------------------------------------
def segmentos(p) -> list:
    """Hijos del párrafo con texto (runs e hipervínculos), en orden."""
    return [e for e in p if e.tag in (W + "r", W + "hyperlink") and (e.tag == W + "hyperlink" or e.find(W + "t") is not None)]


def _rpr(e):
    if e.tag == W + "hyperlink":
        r = e.find(W + "r")
        return ooxml.rpr_texto(r.find(W + "rPr") if r is not None else None)
    return e.find(W + "rPr")


def _partir(r, k: int):
    """Parte un run con un solo w:t en dos por la posición k del texto. Devuelve el segundo."""
    ts = r.findall(W + "t")
    if len(ts) != 1:
        raise SystemExit(f"run con {len(ts)} w:t: no se puede partir ({texto(r)!r})")
    t = ts[0].text or ""
    r2 = copy.deepcopy(r)
    ts[0].text = t[:k]
    ts[0].set(ooxml.XML_SPACE, "preserve")
    t2 = r2.find(W + "t")
    t2.text = t[k:]
    t2.set(ooxml.XML_SPACE, "preserve")
    r.addnext(r2)
    return r2


def marcar(p, objetivo: str, nombre: str) -> None:
    """Cambia por la marca {{nombre}} el tramo del párrafo cuyo texto es `objetivo` (parte runs si hace falta)."""
    total = "".join(texto(e) for e in segmentos(p))
    i = total.find(objetivo)
    if i < 0 or total.find(objetivo, i + 1) >= 0:
        raise SystemExit(f"«{objetivo}» no está una sola vez en «{total[:120]}…»")
    j = i + len(objetivo)
    for borde in (i, j):   # partir en los bordes
        pos = 0
        for e in segmentos(p):
            n = len(texto(e))
            if pos < borde < pos + n:
                if e.tag == W + "hyperlink":
                    raise SystemExit(f"el tramo «{objetivo}» corta un hipervínculo")
                _partir(e, borde - pos)
                break
            pos += n
    pos, cubiertos = 0, []
    for e in segmentos(p):
        n = len(texto(e))
        if i <= pos and pos + n <= j and n:
            cubiertos.append(e)
        pos += n
    rpr = _rpr(cubiertos[0])
    cubiertos[0].addprevious(ooxml.run("{{%s}}" % nombre, rpr))
    for e in cubiertos:
        p.remove(e)


def marcar_t(p, objetivo: str, nombre: str) -> None:
    """Cambia por la marca los runs seguidos de solo texto que dicen `objetivo` (deja los runs de tabulación)."""
    runs = [r for r in p if r.tag == W + "r"]
    solo_texto = [r if len(r.findall(W + "t")) == 1 and all(x.tag in (W + "rPr", W + "t", W + "tab") for x in r)
                  else None for r in runs]
    for a in range(len(runs)):
        acum = ""
        for b in range(a, len(runs)):
            if solo_texto[b] is None:
                break
            acum += runs[b].find(W + "t").text or ""
            if acum.strip() == objetivo:
                runs[a].find(W + "t").text = "{{%s}}" % nombre
                for r in runs[a + 1:b + 1]:
                    p.remove(r)
                return
            if len(acum) > len(objetivo) + 2:
                break
    raise SystemExit(f"«{objetivo}»: no está en runs de solo texto")


def marcar_parrafo(p, nombre: str, formato: str = "primero") -> None:
    """Deja el párrafo con una sola marca, con el formato de su primer texto o, con formato «normal», el de su texto
    más largo (para los párrafos del profesor: la negrita la ponen ellos con «**…**»)."""
    segs = segmentos(p)
    if formato == "normal" and segs:
        rpr = _rpr(max(segs, key=lambda e: len(texto(e))))
    else:
        rpr = _rpr(segs[0]) if segs else None
    for e in list(p):
        if e.tag != W + "pPr" and e.tag not in (W + "bookmarkStart", W + "bookmarkEnd"):
            p.remove(e)
    p.append(ooxml.run("{{%s}}" % nombre, rpr))


def marcador(proto, nombre: str, lista: bool = False):
    """Párrafo de control ({{#lista}}, {{/lista}}, {{?condición}}…) o hueco ({{*nombre}}) con el formato de `proto`;
    con `lista`, conserva su numeración (el hueco es un elemento más de la lista)."""
    p = copy.deepcopy(proto)
    ooxml.limpiar_ids(p)
    num = p.find(f"{W}pPr/{W}numPr")
    if num is not None and not lista:
        num.getparent().remove(num)
    marcar_parrafo(p, nombre, formato="normal")
    return p


# ---------------------------------------------------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------------------------------------------------
class Cuerpo:
    """El cuerpo de PIICT por apartados (título → elementos hasta el siguiente título)."""

    def __init__(self, body):
        self.body = body

    def elementos(self):
        return list(self.body)

    def titulo(self, numero: str):
        for e in self.body:
            if ooxml.es_titulo(e) and re.match(rf"^{re.escape(numero)}[.\-\s]", normal(texto(e))):
                return e
        raise SystemExit(f"sin el apartado {numero}")

    def apartado(self, numero: str) -> list:
        els = self.elementos()
        i = els.index(self.titulo(numero))
        out = []
        for e in els[i + 1:]:
            if ooxml.es_titulo(e) or e.tag == W + "sectPr":
                break
            out.append(e)
        return out

    def buscar(self, numero: str, empieza: str, tipo: str = "p"):
        for e in self.apartado(numero):
            if e.tag == W + tipo and normal(texto(e)).startswith(empieza):
                return e
        raise SystemExit(f"apartado {numero}: no encuentro «{empieza}»")

    def tabla(self, numero: str, k: int = 0):
        return [e for e in self.apartado(numero) if e.tag == W + "tbl"][k]


def celda(tr, k):
    return tr.findall(W + "tc")[k]


def marcar_dos(p, prefijo: str, resto: str) -> None:
    """El párrafo con dos marcas seguidas: la primera con el formato de su primer texto (p. ej., «R.A.1.» en negrita) y
    la segunda con el del último (el texto normal)."""
    segs = segmentos(p)
    rpr1, rpr2 = (_rpr(segs[0]), _rpr(segs[-1])) if segs else (None, None)
    for e in list(p):
        if e.tag != W + "pPr" and e.tag not in (W + "bookmarkStart", W + "bookmarkEnd"):
            p.remove(e)
    p.append(ooxml.run("{{%s}}" % prefijo, rpr1))
    p.append(ooxml.run("{{%s}}" % resto, rpr2))


def dejar_un_parrafo(tc) -> None:
    for p in tc.findall(W + "p")[1:]:
        tc.remove(p)


def marcar_celda(tc, nombre: str, conservar: int = 1) -> None:
    """Deja la celda con `conservar` párrafos; el primero con la marca."""
    ps = tc.findall(W + "p")
    for p in ps[conservar:]:
        tc.remove(p)
    marcar_parrafo(ps[0], nombre)


def despues_tabla(t, hueco) -> None:
    """El hueco de las notas de una tabla, tras el párrafo vacío que la sigue (sin él, el texto se monta en la tabla)."""
    sig = t.getnext()
    (sig if sig is not None and sig.tag == W + "p" and not normal(texto(sig)) else t).addnext(hueco)


def quitar(*els) -> None:
    for e in els:
        e.getparent().remove(e)


def rodear(primero, ultimo, nombre: str, proto=None) -> None:
    """Pone los párrafos de control {{?nombre}} y {{/nombre}} antes de `primero` y después de `ultimo`."""
    proto = proto if proto is not None else primero
    base = nombre.split(":")[-1] if ":" in nombre else nombre.lstrip("?#")
    primero.addprevious(marcador(proto, nombre))
    ultimo.addnext(marcador(proto, "/" + base))


# ---------------------------------------------------------------------------------------------------------------------
# Tabla 4.1 (CarlosFB, 2026-10-17, ADR-025)
# ---------------------------------------------------------------------------------------------------------------------
#: (cabecera en líneas, marca de la fila de cada RA, ancho en twips). Suman el ancho de la tabla de PIICT (8896).
COLUMNAS_41 = [
    (["Resultado de aprendizaje"], None, 4096),
    (["Modalidad"], "modalidad", 1000),
    (["Horas", "Centro"], "centro", 900),
    (["Horas", "Empresa"], "empresa", 900),
    (["% Horas", "Centro"], "pct_centro", 1000),
    (["% Horas", "Empresa"], "pct_empresa", 1000),
]


def _celda_41(proto, ancho: int, lineas: list[str], negrita: bool | None = None, span: int = 1):
    """Copia de la celda `proto` (su sombreado, alineación y formato de texto) con su ancho y sus líneas de texto."""
    tc = copy.deepcopy(proto)
    ooxml.limpiar_ids(tc)
    tcpr = ooxml.tcpr(tc)
    ooxml.hijo(tcpr, "tcW", ooxml.ORDEN_TCPR, w=str(ancho), type="dxa")
    if span > 1:
        ooxml.hijo(tcpr, "gridSpan", ooxml.ORDEN_TCPR, val=str(span))
    dejar_un_parrafo(tc)
    par = tc.find(W + "p")
    r = next(iter(par.iter(W + "r")), None)
    rpr = copy.deepcopy(r.find(W + "rPr")) if r is not None and r.find(W + "rPr") is not None else \
        etree.Element(W + "rPr")
    for e in list(rpr):
        if e.tag == W + "color":   # el rojo de «Horas totales» en PIICT no pasa
            rpr.remove(e)
    if negrita is not None:
        for nombre in ("b", "bCs"):
            e = rpr.find(W + nombre)
            if negrita and e is None:
                ooxml.hijo(rpr, nombre, ooxml.ORDEN_RPR)
            elif not negrita and e is not None:
                rpr.remove(e)
    for e in [e for e in par if e.tag != W + "pPr"]:
        par.remove(e)
    for i, linea in enumerate(lineas):
        if i:
            salto = etree.SubElement(par, W + "r")
            salto.append(copy.deepcopy(rpr))
            etree.SubElement(salto, W + "br")
        par.append(ooxml.run(linea, copy.deepcopy(rpr)))
    return tc


def tabla_41(t) -> None:
    """Cabecera en negrita sobre gris, una fila por RA (código subrayado y en negrita, enunciado justificado y el resto
    centrado; los % en negrita) y la fila TOTAL: «TOTAL» en RA y Modalidad combinadas, las dos sumas en negrita y los
    dos % combinados y vacíos."""
    filas = t.findall(W + "tr")
    cab, ra, total = filas[0], filas[1], filas[-1]
    p_cab_ra, p_cab, p_dato = celda(cab, 0), celda(cab, 1), celda(ra, 2)
    p_ra, p_total_txt, p_total = celda(ra, 0), celda(total, 0), celda(total, 1)
    grid = t.find(W + "tblGrid")
    for g in list(grid):
        grid.remove(g)
    for _c, _m, ancho in COLUMNAS_41:
        etree.SubElement(grid, W + "gridCol").set(W + "w", str(ancho))
    # cabecera
    for tc in cab.findall(W + "tc"):
        cab.remove(tc)
    for k, (lineas, _m, ancho) in enumerate(COLUMNAS_41):
        cab.append(_celda_41(p_cab_ra if k == 0 else p_cab, ancho, lineas, negrita=True))
    # fila de cada RA
    nueva_ra = copy.deepcopy(p_ra)
    ooxml.hijo(ooxml.tcpr(nueva_ra), "tcW", ooxml.ORDEN_TCPR, w=str(COLUMNAS_41[0][2]), type="dxa")
    dejar_un_parrafo(nueva_ra)
    par = nueva_ra.find(W + "p")
    marcar_dos(par, "@ponderacion.codigo", "@ponderacion.texto")
    ooxml.hijo(ooxml.ppr(par), "jc", ooxml.ORDEN_PPR, val="both")
    for tc in ra.findall(W + "tc"):
        ra.remove(tc)
    trpr = ra.find(W + "trPr")
    if trpr is None:
        trpr = etree.Element(W + "trPr")
        ra.insert(0, trpr)
    if trpr.find(W + "cantSplit") is None:
        trpr.insert(0, etree.Element(W + "cantSplit"))   # la fila de un RA no se parte entre dos páginas
    ra.append(nueva_ra)
    for _l, marca, ancho in COLUMNAS_41[1:]:
        ra.append(_celda_41(p_dato, ancho, ["{{@ponderacion.%s}}" % marca], negrita=marca.startswith("pct")))
    # TOTAL
    for tc in total.findall(W + "tc"):
        total.remove(tc)
    total.append(_celda_41(p_total_txt, COLUMNAS_41[0][2] + COLUMNAS_41[1][2], ["TOTAL "], negrita=True, span=2))
    total.append(_celda_41(p_total, COLUMNAS_41[2][2], ["{{t41_centro}}"], negrita=True))
    total.append(_celda_41(p_total, COLUMNAS_41[3][2], ["{{t41_empresa}}"], negrita=True))
    total.append(_celda_41(p_total, COLUMNAS_41[4][2] + COLUMNAS_41[5][2], [], span=2))
    quitar(*filas[2:-1])


# ---------------------------------------------------------------------------------------------------------------------
# Fuentes: nada en Times New Roman
# ---------------------------------------------------------------------------------------------------------------------
RANURAS = ("ascii", "hAnsi", "eastAsia", "cs")


def fuentes_de_la_plantilla(pq: ooxml.Paquete) -> None:
    """Times New Roman fuera de estilos y textos y `docDefaults` con la fuente del cuerpo (la de «Normal») en todas
    las ranuras. Así ningún texto que escriba la app cae en Times New Roman ni en una fuente que no está en el equipo
    (Liberation Serif, Noto CJK), tampoco en la ranura asiática, que Word usa para símbolos como «→» (CarlosFB,
    2026-10-17)."""
    estilos = pq.xml("word/styles.xml")
    normal_ = next(s for s in estilos.iter(W + "style") if s.get(W + "type") == "paragraph"
                   and s.get(W + "default") == "1")
    cuerpo = normal_.find(f"{W}rPr/{W}rFonts").get(W + "ascii")
    defecto = estilos.find(f"{W}docDefaults/{W}rPrDefault/{W}rPr")
    rf = ooxml.hijo(defecto, "rFonts", ooxml.ORDEN_RPR)
    for a in list(rf.attrib):
        del rf.attrib[a]
    for ranura in RANURAS:
        rf.set(W + ranura, cuerpo)
    for n in list(pq.partes) + list(pq._xml):
        if not (n.startswith("word/") and n.endswith(".xml")) or n in ("word/fontTable.xml",):
            continue
        for e in pq.xml(n).iter(W + "rFonts"):
            for ranura in RANURAS:
                if e.get(W + ranura) == "Times New Roman":
                    e.set(W + ranura, cuerpo)


def construir(origen: Path, proyecto: Path | None = None) -> ooxml.Paquete:
    pq = ooxml.Paquete.desde_docx(origen)
    bloques: dict[str, list] = {}
    doc = pq.xml("word/document.xml")
    body = doc.find(W + "body")
    c = Cuerpo(body)

    # -- comentarios fuera (marcas de rango y referencias) ------------------------------------------------------------
    for tag in ("commentRangeStart", "commentRangeEnd"):
        for e in list(doc.iter(W + tag)):
            e.getparent().remove(e)
    for e in list(doc.iter(W + "commentReference")):
        r = e.getparent()
        r.getparent().remove(r)

    # -- portada ------------------------------------------------------------------------------------------------------
    portada = []
    for e in c.elementos():
        if ooxml.es_titulo(e):
            break
        portada.append(e)
    t_port, t_prof = [e for e in portada if e.tag == W + "tbl"][:2]
    filas = t_port.findall(W + "tr")
    marcar_celda(celda(filas[0], 1), "familia")
    ps = celda(filas[1], 1).findall(W + "p")
    marcar_parrafo(ps[0], "grado")
    marcar_parrafo(ps[1], "ciclo")
    marcar_celda(celda(filas[2], 1), "modulo_portada")
    marcar_celda(celda(filas[3], 1), "horas")
    filas = t_prof.findall(W + "tr")
    marcar_celda(celda(filas[0], 0), "profesorado_etiqueta")
    marcar_celda(celda(filas[0], 1), "*profesorado")
    marcar_celda(celda(filas[1], 1), "curso_escolar")

    # -- 1 y normativa ------------------------------------------------------------------------------------------------
    p = c.apartado("1")[0]
    marcar(p, "Técnico Superior en Sistemas Electrotécnicos y Automatizados", "titulo")
    marcar(p, "Electricidad y Electrónica", "familia")
    # Normativa: se quedan las normas comunes de PIICT; las del título y la resolución del curso las pone la app, por
    # fecha (la de cada norma común sale de su enlace). El hueco va al final de cada lista.
    for numero, nombre, propias in (("1.1", "normativa_estatal", ("Real Decreto 1127/2010", "Real Decreto 401/2023")),
                                    ("1.2", "normativa_autonomica", ("RESOLUCIÓN de",))):
        items = [e for e in c.apartado(numero) if e.tag == W + "p" and normal(texto(e))]
        hueco = marcador(items[0], "*" + nombre)
        conservar = items[0].find(f"{W}pPr/{W}numPr")
        if conservar is not None:   # el hueco es un elemento más de la lista
            ooxml.ppr(hueco).insert(0, copy.deepcopy(conservar))
            ooxml.ordenar(ooxml.ppr(hueco), ooxml.ORDEN_PPR)
        items[-1].addnext(hueco)
        quitar(*[e for e in items if normal(texto(e)).startswith(propias)])

    # -- 2 ------------------------------------------------------------------------------------------------------------
    p = c.buscar("2", "El título de")
    marcar(p, "Técnico Superior en Sistemas Electrotécnicos y Automatizados", "titulo")
    marcar(p, "Real Decreto 1127/2010, de 10 de septiembre", "rd_cita")
    marcar(p, "actualizada por el Real Decreto 401/2023, de 29 de mayo", "rd_modificacion")
    # Las referencias que en Grado Básico son otras (el RD 127/2014 trae catorce títulos, uno por anexo): F8, ADR-032
    marcar(p, ", por el que se establece el título y se fijan sus enseñanzas mínimas", "rd_establece")
    p = c.buscar("2", "En consecuencia")
    marcar(p, "Real Decreto 1127/2010", "rd_cita_corta")
    marcar(p, "anexo V B) del ", "ref_correspondencias")
    marcar(p, ", en la redacción dada por el Real Decreto 401/2023", "anexo_v_redaccion")
    t = c.tabla("2")
    filas = t.findall(W + "tr")
    marcar_celda(celda(filas[1], 0), "@ecp.modulos")
    marcar_celda(celda(filas[1], 1), "@ecp.estandares")
    quitar(*filas[2:])
    p = c.buscar("2", "Según los Artículo 4 y 5")
    marcar(p, "Según los ", "ref_cg_inicio")
    marcar(p, "Artículo 4 y 5", "ref_cg_articulos")    # en cursiva
    marcar(p, "Real Decreto 1127/2010, de 10 de septiembre", "rd_cita")
    marcar(p, ", por el que se establece el título de Técnico Superior en Sistemas Electrotécnicos y Automatizados y se "
              "fijan sus enseñanzas mínimas", "rd_resto_titulo")
    total = normal(texto(p))
    marcar(p, total.split("consiste en ", 1)[1], "competencia_general")

    # -- 2.1 y 2.2 ----------------------------------------------------------------------------------------------------
    p = c.buscar("2.1", "De acuerdo con el artículo 5")
    marcar(p, "De acuerdo con el artículo 5 del ", "ref_competencias")
    marcar(p, "Real Decreto 1127/2010, de 10 de septiembre", "rd_cita")
    marcar(p, ", por el que se establece el título de Técnico Superior en Sistemas Electrotécnicos y Automatizados y se "
              "fijan sus enseñanzas mínimas", "rd_resto_titulo")
    items = [e for e in c.apartado("2.1") if e.tag == W + "p" and re.match(r"^[a-zñ]\) ", normal(texto(e)))]
    marcar_parrafo(items[0], "*competencias")
    quitar(*items[1:])
    p = c.buscar("2.2", "En segundo curso")
    marcar(p, "Técnico Superior en Sistemas Electrotécnicos y Automatizados", "titulo")
    t = c.tabla("2.2")
    filas = t.findall(W + "tr")
    for k, campo in enumerate(("codigo", "nombre", "curso")):
        marcar_celda(celda(filas[1], k), f"@optativos.{campo}")
    quitar(*filas[2:])
    resto = c.apartado("2.2")
    rodear(c.titulo("2.2"), resto[-1], "?con_optativos", proto=p)   # GB no tiene módulos optativos

    # -- 3 ------------------------------------------------------------------------------------------------------------
    p = c.buscar("3", "De acuerdo con el Real Decreto")
    marcar(p, "Real Decreto 1127/2010, de 10 de septiembre", "rd_cita")
    marcar(p, ", por el que se establece el título de Técnico Superior en Sistemas Electrotécnicos y Automatizados y se "
              "fijan sus enseñanzas mínimas", "rd_resto_titulo")
    p = c.buscar("3", "Para el presente módulo")
    marcar(p, "Real Decreto 1127/2010", "rd_cita_corta")
    p = c.buscar("3", "De acuerdo con las orientaciones")
    marcar(p, "orientaciones pedagógicas del anexo I del ", "ref_orientaciones")
    marcar(p, "Real Decreto 1127/2010, de 10 de septiembre", "rd_cita_redaccion_modulo")
    marcar(p, "0517. Procesos en instalaciones de infraestructuras comunes de telecomunicaciones", "modulo_codigo_nombre")
    marcar(p, "las competencias profesionales, personales y sociales a), b), d), e), f), g), h), j) y k) del título",
           "contribucion")
    t = c.tabla("3")
    filas = t.findall(W + "tr")
    dejar_un_parrafo(celda(filas[1], 0))
    marcar_dos(celda(filas[1], 0).find(W + "p"), "@ra_competencias.codigo", "@ra_competencias.texto")
    marcar_celda(celda(filas[1], 1), "@ra_competencias.competencias")
    quitar(*filas[2:])

    # -- 4 ------------------------------------------------------------------------------------------------------------
    p = c.buscar("4", "El presente módulo tiene una carga horaria")
    marcar(p, "5", "h_sem")
    contenidos = marcador(p, "*contenidos")
    p.addnext(contenidos)
    t = c.tabla("4")
    filas = t.findall(W + "tr")
    cab = filas[0]
    marcar_celda(celda(cab, 0), "t4_cabecera_unidad")
    pra = celda(cab, 5).findall(W + "p")[0]
    marcar(pra, "Real Decreto 1127/2010", "rd_cabecera_ra")
    proto = filas[1]
    # la unidad: código en negrita («UD00.»), título y, debajo, su descripción; el elemento: nombre y debajo «(Nh)»
    tc = celda(proto, 0)
    p0 = tc.findall(W + "p")[0]
    desc = copy.deepcopy(p0)
    ooxml.limpiar_ids(desc)
    marcar_dos(p0, "@unidades.codigo", "@unidades.titulo")
    marcar_parrafo(desc, "@unidades.descripcion")
    for x in desc.iter(W + "b"):
        x.getparent().remove(x)
    for p in tc.findall(W + "p")[1:]:
        tc.remove(p)
    p0.addnext(desc)
    marcar_celda(celda(proto, 1), "@unidades.horas")
    marcar_celda(celda(proto, 2), "@unidades.trimestre")
    tc = celda(proto, 3)
    ps = tc.findall(W + "p")
    marcar_celda(tc, "@unidades.elemento", conservar=2)
    marcar_parrafo(ps[1], "@unidades.detalle")
    marcar_celda(celda(proto, 4), "@unidades.peso")
    marcar_celda(celda(proto, 5), "@unidades.ra")
    quitar(*filas[2:-3])
    for fila, pref in zip(filas[-3:], ("centro", "empresa", "total"), strict=True):
        marcar_celda(celda(fila, 1), f"t4_{pref}_horas")
        marcar_celda(celda(fila, 2), f"t4_{pref}_pct")
        marcar_celda(celda(fila, 3), f"t4_{pref}_ra")
    despues_tabla(t, marcador(p, "*notas_tabla4"))
    bloques["tabla4"], proto4 = [t], p
    t = c.tabla("4.1")
    tabla_41(t)
    despues_tabla(t, marcador(p, "*notas_tabla41"))

    # -- 5.1: los párrafos propios de PIICT fuera; quedan los comunes y dos huecos ------------------------------------
    els = [e for e in c.apartado("5.1") if e.tag == W + "p" and normal(texto(e))]
    propios = els[3:6]
    final = els[-1]
    assert normal(texto(final)).startswith("Finalmente"), "5.1: el último párrafo de PIICT no es el «Finalmente…»"
    propios[0].addprevious(marcador(propios[0], "*metodologia"))
    final.addprevious(marcador(final, "*metodologia_final"))
    quitar(*propios, final)

    # -- 6 y 7 ----------------------------------------------------------------------------------------------------------
    items = [e for e in c.apartado("6") if ooxml.numeracion(e)]
    VINETAS["numId"] = ooxml.numeracion(items[0])[0]   # numeración de las viñetas para los párrafos del profesor
    fijo = items[-1]
    assert normal(texto(fijo)).startswith("Empleo de recursos didácticos multimedia"), "6: falta el recurso común"
    items[0].addprevious(marcador(items[0], "*recursos", lista=True))
    quitar(*items[:-1])
    items = [e for e in c.apartado("7") if ooxml.numeracion(e)]
    items[0].addprevious(marcador(items[0], "*espacios", lista=True))
    quitar(*items)

    # -- 9 y 9.1 ------------------------------------------------------------------------------------------------------
    p = c.buscar("9", "La calificación de cada evaluación")
    marcar(p, "38", "empresa_pct")
    marcar(p, "el profesor del módulo", "profesorado_del_modulo")
    rodear(p, p, "?sustituible:calificacion")
    bloques["calificacion"] = [p]
    for prefijo, nombre in (("Evaluación inicial", "ev_inicial"), ("1ª evaluación", "ev_primera"),
                            ("2ª evaluación", "ev_segunda"), ("3ª evaluación", "ev_tercera")):
        p = c.buscar("9", prefijo)
        marcar_t(p, normal(texto(p)).split(": ", 1)[1].strip(), nombre)
    p = c.buscar("9", "La convocatoria ordinaria")
    marcar(p, "del 31 de mayo al 3 de junio de 2027", "ordinaria")
    marcar(p, "14 de junio de 2027", "extraordinaria")
    items = [e for e in c.apartado("9.1") if e.tag == W + "p" and normal(texto(e)).startswith("Alumnos que realicen")]
    marcar_dos(items[0], "fe.jornada", "fe.resto")   # «Alumnos que realicen 8h/día» en negrita y el resto normal
    items[0].addprevious(marcador(items[0], "#formacion_empresa"))
    items[0].addnext(marcador(items[0], "/formacion_empresa"))
    quitar(*items[1:])

    # -- 10: hueco opcional para actividades propias -------------------------------------------------------------------
    ultimo = [e for e in c.apartado("10") if e.tag == W + "p" and normal(texto(e))][-1]
    ultimo.addnext(marcador(ultimo, "*actividades"))

    # -- 11: RA y criterios del catálogo ------------------------------------------------------------------------------
    p = c.buscar("11", "Siguiendo el")
    marcar(p, "Real Decreto 1127/2010, de 10 de septiembre", "rd_cita")
    marcar(p, ", por el que se establece el título de Técnico Superior en Sistemas Electrotécnicos y Automatizados y se "
              "fijan sus enseñanzas mínimas", "rd_resto_titulo")
    marcar(p, ", en su redacción actualizada por el Real Decreto 401/2023, de 29 de mayo", "rd_redaccion_ra")
    els = c.apartado("11")
    i = els.index(p)
    resto = els[i + 1:]
    enunciado, etiqueta, criterio = resto[0], resto[1], resto[2]
    vacio = next(e for e in resto[3:] if not normal(texto(e)))
    assert normal(texto(etiqueta)).startswith("Criterios de evaluación")
    marcar_dos(enunciado, "ra.codigo", "ra.texto")   # «R.A.1.» con su formato y el enunciado normal
    marcar_parrafo(criterio, "*ra.criterios")
    grupo = [enunciado, etiqueta, criterio, vacio]
    for e in resto:
        if e not in grupo:
            quitar(e)
    enunciado.addprevious(marcador(enunciado, "#resultados"))
    vacio.addnext(marcador(enunciado, "/resultados"))

    # -- 11.1 y 11.2: bloques que el profesor puede sustituir (p. ej., en el Proyecto, sin exámenes) -------------------
    items = [e for e in c.apartado("11.1") if ooxml.numeracion(e)]
    rodear(items[0], items[-1], "?sustituible:instrumentos")
    bloques["instrumentos"] = items
    els = [e for e in c.apartado("11.2") if e.tag == W + "p" and normal(texto(e))]
    asist = next(e for e in els if normal(texto(e)).startswith("La asistencia deberá ser"))
    visitas = next(e for e in els if normal(texto(e)).startswith("Visitas y actividades complementarias"))
    lista = els[1:els.index(asist)]
    rodear(lista[0], lista[-1], "?sustituible:elementos")
    bloques["elementos"] = lista
    tramo = els[els.index(asist) + 1:els.index(visitas)]
    rodear(tramo[0], tramo[-1], "?sustituible:asistencia_y_pruebas")
    bloques["asistencia_y_pruebas"] = tramo
    if proyecto is not None:
        variante_proyecto(pq, bloques, proto4, proyecto)

    # -- pie: el correo del departamento no va en el repositorio --------------------------------------------------------
    pie = pq.xml("word/footer2.xml")
    correo = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
    for p in pie.iter(W + "p"):
        m = correo.search("".join(texto(e) for e in segmentos(p)))   # solo el texto propio (no el de cuadros dentro)
        if m:
            marcar(p, m.group(0), "correo_pie")

    despejar_franja(pq)
    fuentes_de_la_plantilla(pq)
    return limpiar(pq)


# ---------------------------------------------------------------------------------------------------------------------
# Franja vertical del margen: por debajo del escudo (CarlosFB, 2026-10-17)
# ---------------------------------------------------------------------------------------------------------------------
MARGEN_FRANJA = 180_000   # EMU: 5 mm entre el escudo y el principio del texto vertical


def solapes_franja(pq: ooxml.Paquete, margen: int = MARGEN_FRANJA) -> list[str]:
    """La franja vertical que empieza a menos de `margen` del borde inferior de una imagen con la que coincide en
    horizontal, en cada encabezado. Lista vacía = bien."""
    doc = pq.xml("word/document.xml")
    out = []
    for n in sorted(pq.partes):
        if not re.fullmatch(r"word/header\d+\.xml", n):
            continue
        anclas = ooxml.anclas(pq.xml(n), doc)
        for f in (a for a in anclas if "Programación didáctica" in a["texto"]):
            for img in (a for a in anclas if a["imagen"]):
                if img["x0"] < f["x1"] and f["x0"] < img["x1"] and f["y0"] < img["y1"] + margen and img["y0"] < f["y1"]:
                    out.append(f"{n}: «{f['nombre']}» empieza en {f['y0']} EMU y «{img['nombre']}» acaba en {img['y1']}")
    return out


def despejar_franja(pq: ooxml.Paquete, margen: int = MARGEN_FRANJA) -> None:
    """Baja el principio del cuadro de texto vertical («Escuelas Profesionales Luis Amigó – Programación didáctica»)
    hasta `margen` por debajo del escudo y conserva su final (no se acerca al pie). Cambia la versión DrawingML y la
    VML de reserva."""
    doc = pq.xml("word/document.xml")
    for n in sorted(pq.partes):
        if not re.fullmatch(r"word/header\d+\.xml", n):
            continue
        raiz = pq.xml(n)
        medidas = ooxml.anclas(raiz, doc)
        for anc, f in zip(raiz.iter(ooxml.WP + "anchor"), medidas, strict=True):
            if "Programación didáctica" not in f["texto"]:
                continue
            imgs = [a for a in medidas if a["imagen"] and a["x0"] < f["x1"] and f["x0"] < a["x1"]]
            if not imgs:
                continue
            nuevo_y0 = max(a["y1"] for a in imgs) + margen
            if f["y0"] >= nuevo_y0:
                continue
            alto = f["y1"] - nuevo_y0
            alt = next(x for x in anc.iterancestors() if etree.QName(x).localname == "AlternateContent")
            # el texto, sin los espacios de relleno del final y con la letra en la proporción del cuadro (a la baja,
            # en medios puntos pares), para que quepa en una línea
            factor = alto / (f["y1"] - f["y0"])
            for caja in alt.iter(W + "txbxContent"):
                ts = [x for x in caja.iter(W + "t") if x.text]
                if ts:
                    ts[-1].text = ts[-1].text.rstrip()
                for sz in caja.iter(W + "sz", W + "szCs"):
                    sz.set(W + "val", str(int(int(sz.get(W + "val")) * factor) // 2 * 2))
            off = anc.find(f"{ooxml.WP}positionV/{ooxml.WP}posOffset")
            off.text = str(int(off.text) + nuevo_y0 - f["y0"])
            anc.find(ooxml.WP + "extent").set("cy", str(alto))
            for ext in anc.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}ext"):
                if ext.get("cy"):
                    ext.set("cy", str(alto))
            # VML de reserva (mc:Fallback): margen superior y alto en puntos (12 700 EMU por punto)
            for forma in alt.iter("{urn:schemas-microsoft-com:vml}shape"):
                estilo = forma.get("style", "")
                estilo = re.sub(r"margin-top:[\d.]+pt", f"margin-top:{int(off.text) / 12700:.2f}pt", estilo)
                estilo = re.sub(r"height:[\d.]+pt", f"height:{alto / 12700:.2f}pt", estilo)
                forma.set("style", estilo)
                gfx = "{urn:schemas-microsoft-com:office:office}gfxdata"
                if gfx in forma.attrib:   # copia antigua de la forma: con la geometría vieja
                    del forma.attrib[gfx]


# ---------------------------------------------------------------------------------------------------------------------
# Variante de proyecto (CarlosFB, 2026-10-17, ADR-020): la tabla 4 y los bloques de 9, 11.1 y 11.2 de 0526
# ---------------------------------------------------------------------------------------------------------------------
class Importador:
    """Trae elementos de otra programación al paquete de la plantilla: numeraciones (con ids nuevos), estilos que
    falten e hipervínculos."""

    def __init__(self, destino: ooxml.Paquete, origen: ooxml.Paquete):
        self.d, self.o = destino, origen
        self.num_d, self.num_o = destino.xml("word/numbering.xml"), origen.xml("word/numbering.xml")
        self.st_d, self.st_o = destino.xml("word/styles.xml"), origen.xml("word/styles.xml")
        self.rels_o = {r.get("Id"): r for r in origen.rels("word/document.xml")}
        self.nmap: dict[str, str] = {}

    def numeracion(self, nid: str) -> str:
        if nid in self.nmap:
            return self.nmap[nid]
        num = next((n for n in self.num_o.findall(W + "num") if n.get(W + "numId") == nid), None)
        if num is None:
            return nid
        aid = num.find(W + "abstractNumId").get(W + "val")
        absn = copy.deepcopy(next(a for a in self.num_o.findall(W + "abstractNum") if a.get(W + "abstractNumId") == aid))
        na = str(max(int(a.get(W + "abstractNumId")) for a in self.num_d.findall(W + "abstractNum")) + 1)
        nn = str(max(int(n.get(W + "numId")) for n in self.num_d.findall(W + "num")) + 1)
        absn.set(W + "abstractNumId", na)
        nsid = absn.find(W + "nsid")
        if nsid is not None:   # determinista: la misma plantilla da los mismos bytes
            nsid.set(W + "val", f"{(int(na) * 2654435761) & 0xFFFFFFFF:08X}")
        for x in absn.findall(W + "numStyleLink") + absn.findall(W + "styleLink"):
            absn.remove(x)
        self.num_d.findall(W + "num")[0].addprevious(absn)
        nuevo = copy.deepcopy(num)
        nuevo.set(W + "numId", nn)
        nuevo.find(W + "abstractNumId").set(W + "val", na)
        for a in [a for a in nuevo.attrib if not a.startswith(W)]:
            del nuevo.attrib[a]
        self.num_d.findall(W + "num")[-1].addnext(nuevo)
        self.nmap[nid] = nn
        return nn

    def estilo(self, sid: str) -> None:
        if any(s.get(W + "styleId") == sid for s in self.st_d.findall(W + "style")):
            return
        s = next((s for s in self.st_o.findall(W + "style") if s.get(W + "styleId") == sid), None)
        if s is None:
            return
        base = s.find(W + "basedOn")
        if base is not None:
            self.estilo(base.get(W + "val"))
        self.st_d.append(copy.deepcopy(s))

    def elemento(self, e):
        e = copy.deepcopy(e)
        ooxml.limpiar_ids(e)
        for x in list(e.iter()):
            if x.tag in (W + "commentRangeStart", W + "commentRangeEnd", W + "proofErr"):
                x.getparent().remove(x)
                continue
            if x.tag == W + "numId":
                x.set(W + "val", self.numeracion(x.get(W + "val")))
            if x.tag in (W + "pStyle", W + "rStyle", W + "tblStyle"):
                self.estilo(x.get(W + "val"))
            rid = x.get(ooxml.R + "id")
            if rid and rid in self.rels_o:
                r = self.rels_o[rid]
                x.set(ooxml.R + "id", self.d.relacion("word/document.xml", r.get("Type"), r.get("Target"),
                                                    r.get("TargetMode") == "External"))
        return e


def variante_proyecto(pq: ooxml.Paquete, bloques: dict[str, list], proto4, origen: Path) -> None:
    po = ooxml.Paquete.desde_docx(origen)
    co = Cuerpo(po.xml("word/document.xml").find(W + "body"))
    imp = Importador(pq, po)
    els = [e for e in co.apartado("11.2") if e.tag == W + "p" and normal(texto(e))]
    asist = next(i for i, e in enumerate(els) if normal(texto(e)).startswith("La asistencia deberá ser"))
    visitas = next(i for i, e in enumerate(els) if normal(texto(e)).startswith("Visitas y actividades complementarias"))
    origenes = {"calificacion": [co.buscar("9", "La calificación de cada evaluación")],
                "instrumentos": [e for e in co.apartado("11.1") if ooxml.numeracion(e)],
                "elementos": els[1:asist], "asistencia_y_pruebas": els[asist + 1:visitas],
                "tabla4": [co.tabla("4")]}
    for clave, propios in origenes.items():
        nuevos = [imp.elemento(e) for e in propios]
        for e in nuevos:
            for p in ([e] if e.tag == W + "p" else []):
                if "T01 a T08" in "".join(texto(s) for s in segmentos(p)):
                    marcar(p, "T01 a T08", "tareas")
        if clave == "tabla4":
            marcar_tabla_proyecto(nuevos[0])
        piict = bloques[clave]
        proto = proto4 if clave == "tabla4" else piict[0]
        piict[0].addprevious(marcador(proto, "?no_proyecto"))
        fin = marcador(proto, "/no_proyecto")
        piict[-1].addnext(fin)
        ancla = marcador(proto, "?proyecto")
        fin.addnext(ancla)
        for e in nuevos:
            ancla.addnext(e)
            ancla = e
        ancla.addnext(marcador(proto, "/proyecto"))


def marcar_tabla_proyecto(t) -> None:
    """La tabla 4 de 0526: cabecera tal cual (con el real decreto como marca), una fila modelo y la de total."""
    filas = t.findall(W + "tr")
    cab = celda(filas[0], 5)
    p = next(p for p in cab.findall(W + "p") if "Real Decreto" in texto(p))
    marcar(p, "Real Decreto 1127/2010", "rd_cabecera_ra")
    proto = filas[1]
    tc = celda(proto, 0)
    dejar_un_parrafo(tc)
    p0 = tc.find(W + "p")
    desc = copy.deepcopy(p0)
    marcar_dos(p0, "@unidades.codigo", "@unidades.titulo")
    marcar_parrafo(desc, "@unidades.descripcion")
    for x in desc.iter(W + "b"):
        x.getparent().remove(x)
    p0.addnext(desc)
    for k, campo in ((1, "horas"), (2, "trimestre"), (3, "peso"), (5, "ra")):
        marcar_celda(celda(proto, k), f"@unidades.{campo}")
    tc = celda(proto, 4)
    ps = tc.findall(W + "p")
    marcar_celda(tc, "@unidades.elemento", conservar=2)
    marcar_parrafo(ps[1], "@unidades.detalle")
    quitar(*filas[2:-1])
    marcar_celda(celda(filas[-1], 1), "t4_total_horas")
    marcar_celda(celda(filas[-1], 3), "t4_total_pct")


def limpiar(pq: ooxml.Paquete) -> ooxml.Paquete:
    """Solo las partes de la plantilla, sin datos personales, con sus relaciones y tipos."""
    for n in list(pq.partes):
        if n not in PARTES and not n.startswith("word/media/") and not n.endswith(".rels"):
            pq.quitar(n)
    for n in list(pq.partes):
        if n.endswith(".rels") and not (n == "_rels/.rels" or n.startswith("word/_rels/")):
            pq.quitar(n)
    pq.partes["docProps/core.xml"] = CORE.encode()
    pq.partes["docProps/app.xml"] = APP.encode()
    pq.partes["_rels/.rels"] = RELS_RAIZ.encode()
    pq._xml.pop("docProps/core.xml", None)
    # relaciones del documento: solo las de las partes que quedan y los hipervínculos que se usan
    rels = pq.rels("word/document.xml")
    for r in list(rels):
        tipo = r.get("Type").rsplit("/", 1)[-1]
        if tipo not in TIPOS_RELS_DOC:
            rels.remove(r)
    pq.quitar_relaciones_huerfanas("word/document.xml")
    pq.quitar_relaciones_huerfanas("word/footer2.xml")
    # identificadores aleatorios de Word (w16cid:durableId en las numeraciones): Word los rehace; fuera, que la barrera
    # de secretos los confunde con teléfonos
    for n in list(pq.partes) + list(pq._xml):
        if n.startswith("word/") and n.endswith(".xml"):
            raiz = pq.xml(n)
            for e in raiz.iter():
                for a in [a for a in e.attrib if a.startswith("{http://schemas.microsoft.com/office/word/2016/wordml/cid}")]:
                    del e.attrib[a]
    # ajustes: sin ruta a la plantilla adjunta ni variables del documento
    ajustes = pq.xml("word/settings.xml")
    for tag in ("attachedTemplate", "docVars", "rsids"):
        for e in list(ajustes.iter(W + tag)):
            e.getparent().remove(e)
    # tipos de contenido desde cero
    ct = etree.Element(ooxml.CT + "Types", nsmap={None: ooxml.NS["ct"]})
    for ext, tipo in (("rels", "application/vnd.openxmlformats-package.relationships+xml"), ("xml", "application/xml"),
                      ("png", "image/png"), ("jpeg", "image/jpeg"), ("jpg", "image/jpeg")):
        etree.SubElement(ct, ooxml.CT + "Default", Extension=ext, ContentType=tipo)
    for n, tipo in PARTES.items():
        etree.SubElement(ct, ooxml.CT + "Override", PartName="/" + n, ContentType=tipo)
    pq.poner_xml("[Content_Types].xml", ct)
    return pq


# ---------------------------------------------------------------------------------------------------------------------
# Comprobación
# ---------------------------------------------------------------------------------------------------------------------
PROHIBIDO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|Ferrero|Bonet|lastModifiedBy>[^<P]", re.I)


def comprobar(carpeta: Path = DESTINO) -> list[str]:
    errores = []
    pq = ooxml.Paquete.desde_carpeta(carpeta)
    sobran = [n for n in pq.partes if n not in PARTES and not n.startswith("word/media/") and not n.endswith(".rels")
              and n != "[Content_Types].xml"]
    if sobran:
        errores.append(f"partes que no son de la plantilla: {sobran}")
    errores += [f"franja vertical sobre el escudo: {s}" for s in solapes_franja(pq)]
    if any("vbaProject" in n for n in pq.partes):
        errores.append("la plantilla lleva macros")
    for n, datos in pq.partes.items():
        if n.endswith((".xml", ".rels")):
            t = datos.decode("utf-8")
            for m in PROHIBIDO.finditer(t):
                errores.append(f"{n}: dato personal o correo «{m.group(0)[:40]}»")
            if n.startswith("word/") and n.endswith(".xml"):
                for marca in MARCA.findall(texto(pq.xml(n))):
                    if not re.fullmatch(r"\{\{[#/?*@]?[\w.:]+\}\}", marca):
                        errores.append(f"{n}: marca mal formada {marca}")
    return errores


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    c = sub.add_parser("crear")
    c.add_argument("piict", type=Path)
    c.add_argument("--proyecto", type=Path, required=True,
                   help="programación del Proyecto intermodular de 0526: su variante para todos los proyectos")
    sub.add_parser("comprobar")
    a = ap.parse_args()
    if a.orden == "crear":
        pq = construir(a.piict, a.proyecto)
        DESTINO.mkdir(parents=True, exist_ok=True)
        pq.a_carpeta(DESTINO)
        for viejo in DESTINO.rglob("*"):   # partes que ya no están
            if viejo.is_file() and viejo.relative_to(DESTINO).as_posix() not in pq.partes:
                viejo.unlink()
        meta = (f"# Generado por scripts/plantilla.py crear: no se edita a mano.\nversion: '{VERSION}'\n"
                f"origen: Programación de PIICT (0517), plantilla del departamento revisada por CarlosFB\n"
                f"idiomas: [es]\nvinetas: '{VINETAS['numId']}'\n")
        if not METADATOS.is_file() or METADATOS.read_text(encoding="utf-8") != meta:
            METADATOS.write_text(meta, encoding="utf-8")
        print(f"Plantilla en {DESTINO.relative_to(RAIZ)}: {len(pq.partes)} partes")
    errores = comprobar()
    for e in errores:
        print("✗", e)
    print("Plantilla limpia" if not errores else f"{len(errores)} errores")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
