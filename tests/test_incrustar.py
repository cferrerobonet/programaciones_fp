"""Datos incrustados en el .docx (ADR-002): ida y vuelta, huellas y riesgo R1 con LibreOffice."""
import io
import zipfile

import pytest

from programaciones import documento, incrustar, pdf
from programaciones.ooxml import Paquete, W, estilo


@pytest.fixture
def exportado(prog, cat, curso):
    return incrustar.incrustar(documento.generar(prog, cat, curso), prog)


def test_ida_y_vuelta(exportado, prog):
    r = incrustar.leer(exportado)
    assert r.programacion == prog and not r.modificado_en_word
    assert r.catalogo == prog["catalogo"] and r.plantilla == "2026-10-06"


def test_sin_datos(prog, cat, curso):
    assert incrustar.leer(documento.generar(prog, cat, curso)) is None


def test_una_sola_parte_aunque_se_exporte_dos_veces(exportado, prog):
    otra = incrustar.incrustar(exportado, dict(prog, profesorado=["Otra persona ficticia"]))
    z = zipfile.ZipFile(io.BytesIO(otra))
    assert len([n for n in z.namelist() if n.startswith("customXml/item") and "Props" not in n]) == 1
    assert incrustar.leer(otra).programacion["profesorado"] == ["Otra persona ficticia"]


def test_tocado_en_word(exportado):
    pq = Paquete.desde_docx(exportado)
    doc = pq.partes["word/document.xml"].decode("utf-8")
    pq.partes["word/document.xml"] = doc.replace("Profesora Ficticia Uno", "Profesora Ficticia Cambiada", 1).encode()
    r = incrustar.leer(pq.a_bytes())
    assert r.modificado_en_word and r.programacion["profesorado"] == ["Profesora Ficticia Uno"]


def test_datos_danados(exportado):
    pq = Paquete.desde_docx(exportado)
    item = next(n for n in pq.partes if n.startswith("customXml/item") and "Props" not in n)
    pq.partes[item] = pq.partes[item].replace(b"Profesora Ficticia Uno", b"Profesora Ficticia Mala")
    with pytest.raises(incrustar.DatosDanados):
        incrustar.leer(pq.a_bytes())


def test_el_indice_actualizado_no_cuenta_como_cambio(exportado):
    """Word rehace el índice al abrir (updateFields): la huella del texto no lo incluye."""
    pq = Paquete.desde_docx(exportado)
    cambiados = 0
    for p in pq.xml("word/document.xml").iter(W + "p"):
        ts = list(p.iter(W + "t"))
        if estilo(p) in ("TDC2", "TDC3") and ts:
            ts[-1].text = "99"                       # otra página en cada entrada del índice
            cambiados += 1
    assert cambiados > 10
    assert not incrustar.leer(pq.a_bytes()).modificado_en_word


@pytest.mark.skipif(not pdf.soffice(), reason="Sin LibreOffice")
def test_r1_libreoffice_conserva_la_parte_al_abrir_y_guardar(exportado, prog, tmp_path):
    """Riesgo R1 con LibreOffice (automático). Con Word de macOS y Windows, prueba manual (docs/PENDIENTE.md)."""
    entrada = tmp_path / "exportado.docx"
    entrada.write_bytes(exportado)
    guardado = pdf.con_libreoffice(entrada, tmp_path / "guardado.docx", formato="docx:MS Word 2007 XML")
    r = incrustar.leer(guardado.read_bytes())
    assert r is not None and r.programacion == prog and not r.modificado_en_word
