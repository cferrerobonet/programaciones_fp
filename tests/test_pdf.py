"""PDF con LibreOffice (automático, también en la CI) y órdenes de Word (sin ejecutarlo: prueba manual)."""
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


@pytest.mark.parametrize("sistema, programa", [("darwin", "osascript"), ("win32", "powershell"), ("linux", None)])
def test_orden_de_word_segun_el_sistema(monkeypatch, tmp_path, sistema, programa):
    ordenes = []
    monkeypatch.setattr(pdf.sys, "platform", sistema)
    monkeypatch.setattr(pdf, "_ejecutar", lambda orden, t: ordenes.append(orden) or (tmp_path / "x.pdf").write_bytes(b"%PDF"))
    if programa is None:
        with pytest.raises(pdf.ErrorPDF, match="macOS y Windows"):
            pdf.con_word(tmp_path / "x.docx", tmp_path / "x.pdf")
        return
    pdf.con_word(tmp_path / "x.docx", tmp_path / "x.pdf")
    assert ordenes[0][0] == programa
    assert "Microsoft Word" in ordenes[0][2] if programa == "osascript" else "Word.Application" in ordenes[0][-1]


def test_auto_prueba_libreoffice_si_word_falla(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf, "hay_word", lambda: True)
    monkeypatch.setattr(pdf, "con_word", lambda *_a, **_k: (_ for _ in ()).throw(pdf.ErrorPDF("Word falla")))
    monkeypatch.setattr(pdf, "con_libreoffice", lambda d, p, t=120, formato="pdf": p)
    assert pdf.convertir(tmp_path / "x.docx", tmp_path / "y.pdf") == tmp_path / "y.pdf"


@pytest.mark.parametrize("sistema", ["darwin", "win32"])
def test_en_macos_word_convierte_en_una_carpeta_fija(monkeypatch, tmp_path, sistema):
    """Word (sandbox) pide «Conceder acceso al archivo» por cada carpeta nueva: en macOS se convierte siempre en la
    misma, dentro de la de datos de la app, y no en una temporal nueva (ni en el contenedor de Word, que macOS cierra)."""
    monkeypatch.setenv("PROGRAMACIONES_DATOS", str(tmp_path / "datos"))
    monkeypatch.setattr(pdf.sys, "platform", sistema)
    monkeypatch.setattr(pdf, "hay_word", lambda: True)
    monkeypatch.setattr(pdf, "sin_actualizar_campos", lambda docx: docx)
    entradas = []

    def convertir(docx, salida, motor, tiempo_max):
        entradas.append(docx)
        salida.write_bytes(b"%PDF")
        return salida
    monkeypatch.setattr(pdf, "convertir", convertir)
    for n in range(2):
        destino = pdf.exportar_pdf(b"docx", tmp_path / "salida" / f"ficticia{n}.pdf")
        assert destino.read_bytes() == b"%PDF"
    fija = tmp_path / "datos" / pdf.CARPETA_WORD
    if sistema == "darwin":
        assert [e.parent for e in entradas] == [fija, fija] and entradas[0] != entradas[1]
        assert list(fija.iterdir()) == [], "sin rastro al terminar"
    else:
        assert fija not in entradas[0].parents


def test_si_word_falla_en_macos_dice_como_dar_el_permiso(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf.sys, "platform", "darwin")

    def falla(orden, t):
        raise pdf.ErrorPDF("osascript ha fallado: Microsoft Word ha detectado un error")
    monkeypatch.setattr(pdf, "_ejecutar", falla)
    with pytest.raises(pdf.ErrorPDF, match="Conceder acceso"):
        pdf.con_word(tmp_path / "x.docx", tmp_path / "x.pdf")


def test_word_recibe_el_documento_sin_actualizar_campos(prog, cat, curso):
    """Con `w:updateFields`, Word pregunta al abrirlo «¿Desea actualizar los campos?» y la conversión se queda
    esperando: la copia para Word va sin él (las páginas del índice las pone el AppleScript)."""
    from programaciones import documento

    docx = documento.generar(prog, cat, curso)
    assert b"updateFields" in pdf.ooxml.Paquete.desde_docx(docx).partes["word/settings.xml"]
    limpio = pdf.ooxml.Paquete.desde_docx(pdf.sin_actualizar_campos(docx))
    assert b"updateFields" not in limpio.partes["word/settings.xml"]
    assert "update page numbers" in pdf.APPLESCRIPT and "exists document nombre" in pdf.APPLESCRIPT


def test_en_macos_word_recibe_el_nombre_del_documento(monkeypatch, tmp_path):
    ordenes = []
    monkeypatch.setattr(pdf.sys, "platform", "darwin")
    monkeypatch.setattr(pdf, "_ejecutar", lambda orden, t: ordenes.append(orden) or (tmp_path / "x.pdf").write_bytes(b"%PDF"))
    pdf.con_word(tmp_path / "x.docx", tmp_path / "x.pdf")
    assert ordenes[0][-1] == "x.docx", "el AppleScript espera a que Word tenga abierto el documento con ese nombre"
