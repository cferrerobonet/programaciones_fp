"""PDF con LibreOffice (automático, también en la CI) y órdenes de Word (sin ejecutarlo: prueba manual)."""
import sys

import pytest

from programaciones import documento, pdf

hay_libreoffice = pytest.mark.skipif(not pdf.soffice(), reason="Sin LibreOffice")


@hay_libreoffice
def test_pdf_con_libreoffice_y_el_indice_numerado(prog, cat, curso, tmp_path):
    docx = documento.generar(prog, cat, curso)
    destino = pdf.exportar_pdf(docx, tmp_path / "ficticia.pdf", motor="libreoffice")
    paginas = pdf.paginas_pdf(destino)
    if not paginas:
        pytest.skip("Sin pdftotext para leer el PDF")
    assert len(paginas) > 10
    assert "PROGRAMACIÓN DIDÁCTICA" in paginas[0]
    # cada entrada del índice apunta a la página en la que está su título
    texto = "\n".join(paginas)
    assert "12.- ACTIVIDADES DE RECUPERACIÓN" in texto


def test_numerar_indice_con_paginas_inventadas(prog, cat, curso):
    docx = documento.generar(prog, cat, curso)
    paginas = ["portada", "índice", "1.- DATOS IDENTIFICATIVOS: MARCO NORMATIVO 1.1. Normativa básica estatal",
               "2.- RELACIÓN ENTRE ESTÁNDARES DE COMPETENCIA Y LOS MÓDULOS DEL CICLO FORMATIVO"]
    nuevo, cambios = pdf.numerar_indice(docx, paginas)
    assert cambios >= 1 and nuevo != docx


def test_sin_motor_error_claro(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf, "soffice", lambda: None)
    monkeypatch.setattr(pdf, "hay_word", lambda: False)
    with pytest.raises(pdf.ErrorPDF, match="LibreOffice"):
        pdf.convertir(tmp_path / "x.docx", motor="libreoffice")


def test_tiempo_agotado(monkeypatch, tmp_path):
    def lento(*_a, **_k):
        raise pdf.subprocess.TimeoutExpired(cmd="soffice", timeout=1)
    monkeypatch.setattr(pdf, "soffice", lambda: "soffice")
    monkeypatch.setattr(pdf.subprocess, "run", lento)
    with pytest.raises(pdf.ErrorPDF, match="tarda más"):
        pdf.con_libreoffice(tmp_path / "x.docx", tmp_path / "x.pdf", tiempo_max=1)


def test_orden_de_word_segun_el_sistema(monkeypatch, tmp_path):
    ordenes = []
    monkeypatch.setattr(pdf, "_ejecutar", lambda orden, t: ordenes.append(orden) or (tmp_path / "x.pdf").write_bytes(b"%PDF"))
    pdf.con_word(tmp_path / "x.docx", tmp_path / "x.pdf")
    if sys.platform == "darwin":
        assert ordenes[0][0] == "osascript" and "Microsoft Word" in ordenes[0][2]
    elif sys.platform.startswith("win"):
        assert ordenes[0][0] == "powershell"


def test_auto_prueba_libreoffice_si_word_falla(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf, "hay_word", lambda: True)
    monkeypatch.setattr(pdf, "con_word", lambda *_a, **_k: (_ for _ in ()).throw(pdf.ErrorPDF("Word falla")))
    monkeypatch.setattr(pdf, "con_libreoffice", lambda d, p, t=120, formato="pdf": p)
    assert pdf.convertir(tmp_path / "x.docx", tmp_path / "y.pdf") == tmp_path / "y.pdf"
