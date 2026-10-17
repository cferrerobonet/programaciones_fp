"""Los datos del profesor dentro del .docx exportado (ADR-002): una parte XML personalizada (customXml).

La parte lleva el espacio de nombres `urn:epla:programaciones:1`, la versión del catálogo y de la plantilla, el JSON
completo de la programación y dos huellas SHA-256:
- la del JSON canónico: si no coincide, los datos están dañados;
- la del texto del cuerpo al exportar (sin el índice, que Word rehace): si no coincide, el documento se tocó en Word
  después de exportarlo, y esos cambios no se recuperan (RF-08).

Riesgo R1: que Word la conserve al abrir y guardar. La prueba automática se hace con LibreOffice; la de Word de macOS
y Windows es manual (docs/PLAN_DE_PRUEBAS.md, docs/PENDIENTE.md).
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass

from lxml import etree

from programaciones import contenido, ooxml, programacion

ESPACIO = "urn:epla:programaciones:1"
NS_DS = "http://schemas.openxmlformats.org/officeDocument/2006/customXml"


class DatosDanados(ValueError):
    """La huella del JSON incrustado no coincide: los datos no son fiables."""


@dataclass
class Incrustada:
    programacion: dict
    catalogo: str
    plantilla: str
    modificado_en_word: bool    # el texto del cuerpo no es el que se exportó
    parte: str


def huella_texto(docx: bytes) -> str:
    return "sha256:" + hashlib.sha256(contenido.texto_cuerpo(docx).encode("utf-8")).hexdigest()


def _partes_propias(pq: ooxml.Paquete) -> list[str]:
    out = []
    for n in sorted(pq.partes):
        if re.fullmatch(r"customXml/item\d+\.xml", n):
            try:
                raiz = etree.fromstring(pq.partes[n])
            except etree.XMLSyntaxError:
                continue
            if etree.QName(raiz).namespace == ESPACIO:
                out.append(n)
    return out


def incrustar(docx: bytes, prog: dict) -> bytes:
    """El .docx con la parte de datos (sustituye la que tuviera)."""
    prog = programacion.validar(prog)
    pq = ooxml.Paquete.desde_docx(docx)
    for n in _partes_propias(pq):   # una exportación nueva sustituye la anterior
        quitar_parte(pq, n)
    k = 1
    while pq.existe(f"customXml/item{k}.xml"):
        k += 1
    item, props = f"customXml/item{k}.xml", f"customXml/itemProps{k}.xml"
    raiz = etree.Element("{%s}programacion" % ESPACIO, nsmap={None: ESPACIO})
    raiz.set("formato", "1")
    raiz.set("catalogo", prog["catalogo"])
    raiz.set("plantilla", prog["plantilla"])
    raiz.set("huella_json", programacion.huella(prog))
    raiz.set("huella_texto", huella_texto(docx))
    raiz.text = programacion.canonico(prog).decode("utf-8")
    pq.partes[item] = etree.tostring(raiz, xml_declaration=True, encoding="UTF-8", standalone=True)
    ds = etree.Element("{%s}datastoreItem" % NS_DS, nsmap={"ds": NS_DS})
    ds.set("{%s}itemID" % NS_DS, "{%s}" % str(uuid.uuid5(uuid.NAMESPACE_URL, ESPACIO + prog["modulo"])).upper())
    refs = etree.SubElement(ds, "{%s}schemaRefs" % NS_DS)
    etree.SubElement(refs, "{%s}schemaRef" % NS_DS).set("{%s}uri" % NS_DS, ESPACIO)
    pq.partes[props] = etree.tostring(ds, xml_declaration=True, encoding="UTF-8", standalone=True)
    pq.relacion(item, ooxml.TIPO_CUSTOMXML_PROPS, f"itemProps{k}.xml")
    pq.relacion("word/document.xml", ooxml.TIPO_CUSTOMXML, f"../{item}")
    pq.tipo_override(props, ooxml.CT_CUSTOMXML_PROPS)
    return pq.a_bytes()


def quitar_parte(pq: ooxml.Paquete, item: str) -> None:
    k = re.search(r"(\d+)\.xml$", item).group(1)
    props = f"customXml/itemProps{k}.xml"
    for n in (item, props, f"customXml/_rels/item{k}.xml.rels"):
        pq.quitar(n)
    pq.tipo_override(props, None)
    rels = pq.rels("word/document.xml")
    for r in list(rels):
        if r.get("Type") == ooxml.TIPO_CUSTOMXML and r.get("Target", "").endswith(f"customXml/item{k}.xml"):
            rels.remove(r)


def leer(docx: bytes) -> Incrustada | None:
    """Los datos incrustados, o None si el documento no los lleva. Lanza DatosDanados si la huella del JSON falla."""
    pq = ooxml.Paquete.desde_docx(docx)
    partes = _partes_propias(pq)
    if not partes:
        return None
    raiz = etree.fromstring(pq.partes[partes[-1]])
    try:
        datos = json.loads(raiz.text or "")
    except json.JSONDecodeError as e:
        raise DatosDanados(f"JSON ilegible: {e}") from e
    if programacion.huella(datos) != raiz.get("huella_json"):
        raise DatosDanados("La huella del JSON no coincide")
    prog = programacion.validar(datos)
    return Incrustada(programacion=prog, catalogo=raiz.get("catalogo", ""), plantilla=raiz.get("plantilla", ""),
                      modificado_en_word=huella_texto(docx) != raiz.get("huella_texto"), parte=partes[-1])
