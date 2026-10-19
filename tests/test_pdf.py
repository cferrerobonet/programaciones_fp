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
    assert "update t\n" in pdf.APPLESCRIPT and "exists document nombre" in pdf.APPLESCRIPT


def test_en_macos_word_recibe_el_nombre_del_documento(monkeypatch, tmp_path):
    ordenes = []
    monkeypatch.setattr(pdf.sys, "platform", "darwin")
    monkeypatch.setattr(pdf, "_ejecutar", lambda orden, t: ordenes.append(orden) or (tmp_path / "x.pdf").write_bytes(b"%PDF"))
    pdf.con_word(tmp_path / "x.docx", tmp_path / "x.pdf")
    assert ordenes[0][-1] == "x.docx", "el AppleScript espera a que Word tenga abierto el documento con ese nombre"


def test_word_trabaja_en_segundo_plano_y_se_cierra_si_no_estaba_abierto():
    """CarlosFB, 2026-10-17: que el profesor no vea Word, solo la vista previa."""
    for trozo in ('set estaba to application "Microsoft Word" is running', 'launch application "Microsoft Word"',
                  "add to recent files false", "if not estaba and (count of documents) = 0 then quit saving no"):
        assert trozo in pdf.APPLESCRIPT, trozo


def test_la_app_vuelve_al_frente_tras_word(monkeypatch, tmp_path):
    from programaciones import actualizaciones

    ordenes = []
    monkeypatch.setattr(pdf.sys, "platform", "darwin")
    monkeypatch.setattr(pdf, "_ejecutar", lambda orden, t: (tmp_path / "x.pdf").write_bytes(b"%PDF"))
    monkeypatch.setattr(pdf.subprocess, "run", lambda orden, **k: ordenes.append(orden))
    monkeypatch.setattr(actualizaciones, "app_en_ejecucion", lambda: tmp_path / "Programaciones.app")
    pdf.con_word(tmp_path / "x.docx", tmp_path / "x.pdf")
    assert ordenes == [["/usr/bin/open", "-a", str(tmp_path / "Programaciones.app")]]


class _RegistroFalso:
    """Lo justo de `winreg` para `pdf.word_registrado`: claves por vista (64 o 32 bits) con su valor por defecto."""
    HKEY_CLASSES_ROOT = "HKCR"
    KEY_READ = 1
    KEY_WOW64_64KEY = 0x100
    KEY_WOW64_32KEY = 0x200

    def __init__(self, claves):
        self.claves = claves   # {(vista, ruta): valor por defecto}

    def OpenKey(self, raiz, ruta, _reservado=0, acceso=0):
        vista = acceso & (self.KEY_WOW64_64KEY | self.KEY_WOW64_32KEY)
        if (vista, ruta) not in self.claves:
            raise OSError(2, "No existe")
        return _ClaveFalsa(self.claves[(vista, ruta)])

    def QueryValue(self, clave, _nombre):
        return clave.valor


class _ClaveFalsa:
    def __init__(self, valor):
        self.valor = valor

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


CLSID = "{000209FF-0000-0000-C000-000000000046}"


@pytest.mark.parametrize("vista", [_RegistroFalso.KEY_WOW64_64KEY, _RegistroFalso.KEY_WOW64_32KEY])
def test_word_registrado_en_64_o_en_32_bits(vista):
    reg = _RegistroFalso({(vista, r"Word.Application\CLSID"): CLSID, (vista, rf"CLSID\{CLSID}\LocalServer32"): ""})
    assert pdf.word_registrado(reg)


def test_la_clave_de_word_sin_su_componente_no_es_word():
    """Restos de un Office desinstalado: «Word.Application» sin CLSID, o con un CLSID sin programa. PowerShell
    fallaba con «Clase no registrada» (80040154) en vez de pasar a LibreOffice o decir qué falta."""
    v64 = _RegistroFalso.KEY_WOW64_64KEY
    assert not pdf.word_registrado(_RegistroFalso({(v64, "Word.Application"): ""}))
    assert not pdf.word_registrado(_RegistroFalso({(v64, r"Word.Application\CLSID"): ""}))
    assert not pdf.word_registrado(_RegistroFalso({(v64, r"Word.Application\CLSID"): CLSID}))


def test_sin_word_ni_libreoffice_dice_que_instalar(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf, "soffice", lambda: None)
    monkeypatch.setattr(pdf, "hay_word", lambda: False)
    with pytest.raises(pdf.ErrorPDF, match="Instala LibreOffice") as e:
        pdf.convertir(tmp_path / "x.docx")
    assert "el Word (.docx) sí se exporta" in str(e.value)


@pytest.mark.parametrize("sistema, repara", [("win32", True), ("darwin", False)])
def test_si_word_falla_y_no_hay_libreoffice_lo_explica_antes_del_detalle(monkeypatch, tmp_path, sistema, repara):
    monkeypatch.setattr(pdf.sys, "platform", sistema)
    monkeypatch.setattr(pdf, "soffice", lambda: None)
    monkeypatch.setattr(pdf, "hay_word", lambda: True)
    monkeypatch.setattr(pdf, "con_word", lambda *_a, **_k: (_ for _ in ()).throw(pdf.ErrorPDF("powershell ha fallado")))
    with pytest.raises(pdf.ErrorPDF) as e:
        pdf.convertir(tmp_path / "x.docx")
    texto = str(e.value)
    assert texto.startswith("Word no ha podido hacer el PDF") and texto.endswith("Detalle: powershell ha fallado")
    assert ("repara Office" in texto) == repara
