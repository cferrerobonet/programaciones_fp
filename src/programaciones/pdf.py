"""PDF de la programación con el Word del equipo o, si no hay, con LibreOffice sin interfaz (TRD §1).

- Word: AppleScript en macOS y COM (PowerShell) en Windows. Sin probar en la CI: prueba manual (docs/PLAN_DE_PRUEBAS.md).
  En macOS se convierte en una carpeta fija de la app, para que Word pida permiso solo la primera vez.
- LibreOffice: `soffice --headless --convert-to pdf` con un perfil propio y temporal, para no chocar con un LibreOffice
  abierto ni dejar rastro.
- Siempre con tiempo máximo y un error claro. Con LibreOffice, el índice se rehace después con las páginas del PDF
  (`numerar_indice`), porque LibreOffice no actualiza el campo al convertir.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import uuid
from pathlib import Path

from programaciones import ooxml
from programaciones.ooxml import W

TIEMPO_MAX = 120   # segundos (RNF-04)
RUTAS_SOFFICE = ["/Applications/LibreOffice.app/Contents/MacOS/soffice",
                 r"C:\Program Files\LibreOffice\program\soffice.exe",
                 r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"]


class ErrorPDF(RuntimeError):
    """No se ha podido hacer el PDF (sin Word ni LibreOffice, tiempo agotado o error del programa)."""


def soffice() -> str | None:
    for nombre in ("soffice", "libreoffice"):
        ruta = shutil.which(nombre)
        if ruta:
            return ruta
    return next((r for r in RUTAS_SOFFICE if Path(r).is_file()), None)


def word_registrado(winreg) -> bool:
    """¿Word se puede abrir por COM? La clave «Word.Application» puede quedar sin su componente (restos de un Office
    desinstalado, o solo Word en la web): entonces PowerShell falla con «Clase no registrada» (80040154) y el CLSID
    {00000000-…}. Se mira que la clave lleve su CLSID y que este tenga su programa (LocalServer32), en la vista de
    64 bits y en la de 32 (un Office de 32 bits se registra en esta)."""
    for vista in (getattr(winreg, "KEY_WOW64_64KEY", 0), getattr(winreg, "KEY_WOW64_32KEY", 0)):
        acceso = winreg.KEY_READ | vista
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application\CLSID", 0, acceso) as clave:
                clsid = winreg.QueryValue(clave, None)
            if not clsid:
                continue
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"CLSID\{clsid}\LocalServer32", 0, acceso):
                return True
        except OSError:
            continue
    return False


def hay_word() -> bool:
    if sys.platform == "darwin":
        return Path("/Applications/Microsoft Word.app").is_dir()
    if sys.platform.startswith("win"):
        import winreg

        return word_registrado(winreg)
    return False


SIN_PROGRAMA = ("En este equipo no hay Word de escritorio ni LibreOffice para hacer el PDF. Instala LibreOffice "
                "(gratis, en libreoffice.org) y vuelve a probar; mientras, el Word (.docx) sí se exporta.")


def word_falla_sin_libreoffice(detalle: str) -> str:
    reparar = (" o repara Office (Configuración › Aplicaciones › Microsoft 365 › Modificar › Reparación rápida)"
               if sys.platform.startswith("win") else "")
    return ("Word no ha podido hacer el PDF y en este equipo no hay LibreOffice para hacerlo en su lugar. Instala "
            f"LibreOffice (gratis, en libreoffice.org){reparar}; mientras, el Word (.docx) sí se exporta. "
            f"Detalle: {detalle}")


def motores() -> list[str]:
    out = []
    if hay_word():
        out.append("word")
    if soffice():
        out.append("libreoffice")
    return out


def _ejecutar(orden: list[str], tiempo_max: int) -> None:
    try:
        r = subprocess.run(orden, capture_output=True, text=True, timeout=tiempo_max)
    except subprocess.TimeoutExpired as e:
        raise ErrorPDF(f"El PDF tarda más de {tiempo_max} s: se cancela") from e
    except OSError as e:
        raise ErrorPDF(f"No se puede ejecutar {Path(orden[0]).name}: {e}") from e
    if r.returncode != 0:
        raise ErrorPDF(f"{Path(orden[0]).name} ha fallado: {(r.stderr or r.stdout).strip()[:300]}")


def con_libreoffice(docx: Path, pdf: Path, tiempo_max: int = TIEMPO_MAX, formato: str = "pdf") -> Path:
    """Convierte con LibreOffice (también sirve para abrir y guardar un .docx: formato «docx:MS Word 2007 XML»)."""
    programa = soffice()
    if not programa:
        raise ErrorPDF("No hay LibreOffice en este equipo")
    with tempfile.TemporaryDirectory(prefix="programaciones-lo-") as tmp:
        perfil = Path(tmp) / "perfil"
        salida = Path(tmp) / "salida"
        salida.mkdir()
        _ejecutar([programa, f"-env:UserInstallation={perfil.as_uri()}", "--headless", "--convert-to", formato,
                   "--outdir", str(salida), str(docx)], tiempo_max)
        hechos = list(salida.iterdir())
        if not hechos:
            raise ErrorPDF("LibreOffice no ha escrito el archivo")
        pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(hechos[0]), pdf)
    return pdf


#: `open` vuelve antes de que Word tenga el documento: guardar enseguida daba «-1708, no entiende el mensaje save as».
#: Se espera a que exista (por su nombre, que no se repite) y el guardado se reintenta unos segundos. La salida va como
#: ruta POSIX (con una ruta HFS, Word no guarda). El documento llega sin `updateFields` (`sin_actualizar_campos`): con él,
#: Word pregunta «¿Desea actualizar los campos?» y se queda esperando; el índice se rehace aquí (entradas y páginas). Pase lo que
#: pase, el documento se cierra sin guardar. En segundo plano (CarlosFB, 2026-10-17): si Word no estaba abierto, se
#: arranca sin traerlo al frente y se cierra al terminar; si lo estaba, solo se cierra el documento. Sin pasar a
#: los recientes de Word.
APPLESCRIPT = '''on run argv
  set entrada to POSIX file (item 1 of argv)
  set salida to item 2 of argv
  set nombre to item 3 of argv
  set estaba to application "Microsoft Word" is running
  if not estaba then launch application "Microsoft Word"
  tell application "Microsoft Word"
    open entrada add to recent files false
    set k to 0
    repeat until (exists document nombre)
      set k to k + 1
      if k > 120 then error "Word no ha abierto el documento"
      delay 0.5
    end repeat
    set d to document nombre
    try
      repeat with t in (tables of contents of d)
        update t
      end repeat
    end try
    set fallo to ""
    repeat 20 times
      try
        save as d file name salida file format format PDF
        set fallo to ""
        exit repeat
      on error e
        set fallo to e
        delay 0.5
      end try
    end repeat
    try
      close d saving no
    end try
    if not estaba and (count of documents) = 0 then quit saving no
    if fallo is not "" then error fallo
  end tell
end run'''

POWERSHELL = ("$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
              "try {{ $d = $w.Documents.Open('{entrada}', $false, $true); $d.SaveAs([ref]'{salida}', [ref]17); "
              "$d.Close($false) }} finally {{ $w.Quit() }}")


def sin_actualizar_campos(docx: bytes) -> bytes:
    """El .docx sin `w:updateFields`, para Word: con él, Word pregunta al abrirlo si actualiza los campos."""
    pq = ooxml.Paquete.desde_docx(docx)
    ajustes = pq.xml("word/settings.xml")
    for uf in ajustes.findall(W + "updateFields"):
        ajustes.remove(uf)
    return pq.a_bytes()


def volver_al_frente() -> None:
    """En macOS, la app instalada vuelve delante cuando Word acaba (Word puede haberse puesto al frente al abrir el
    documento). `open -a` con la app que ya está abierta solo la activa. En desarrollo, nada."""
    from .actualizaciones import app_en_ejecucion

    app = app_en_ejecucion()
    if app is not None:
        subprocess.run(["/usr/bin/open", "-a", str(app)], check=False, capture_output=True, timeout=10)  # nosec B603


def con_word(docx: Path, pdf: Path, tiempo_max: int = TIEMPO_MAX) -> Path:
    if sys.platform == "darwin":
        try:
            _ejecutar(["osascript", "-e", APPLESCRIPT, str(docx.resolve()), str(pdf.resolve()), docx.name],
                      tiempo_max)
        except ErrorPDF as e:
            raise ErrorPDF(f"{e}. {AYUDA_PERMISO_WORD}") from e
        finally:
            volver_al_frente()
    elif sys.platform.startswith("win"):
        orden = POWERSHELL.format(entrada=str(docx.resolve()).replace("'", "''"),
                                  salida=str(pdf.resolve()).replace("'", "''"))
        _ejecutar(["powershell", "-NoProfile", "-NonInteractive", "-Command", orden], tiempo_max)
    else:
        raise ErrorPDF("Word solo está en macOS y Windows")
    if not pdf.is_file():
        raise ErrorPDF("Word no ha escrito el PDF")
    return pdf


def convertir(docx: Path, pdf: Path | None = None, motor: str = "auto", tiempo_max: int = TIEMPO_MAX) -> Path:
    """PDF de un .docx. `motor`: «auto» (Word y, si falla o no está, LibreOffice), «word» o «libreoffice»."""
    docx = Path(docx)
    pdf = Path(pdf) if pdf else docx.with_suffix(".pdf")
    if motor == "auto" and not motores():
        raise ErrorPDF(SIN_PROGRAMA)
    errores = []
    for m in (["word", "libreoffice"] if motor == "auto" else [motor]):
        if m == "word" and (motor == "word" or hay_word()):
            try:
                return con_word(docx, pdf, tiempo_max)
            except ErrorPDF as e:
                errores.append(str(e))
        elif m == "libreoffice":
            try:
                return con_libreoffice(docx, pdf, tiempo_max)
            except ErrorPDF as e:
                errores.append(str(e))
    if motor == "auto" and errores and not soffice():
        raise ErrorPDF(word_falla_sin_libreoffice(errores[0]))
    raise ErrorPDF("; ".join(errores) or SIN_PROGRAMA)


# ---------------------------------------------------------------------------------------------------------------------
# Páginas del índice desde el PDF (paginas_indice.py de la guía programacion-didactica)
# ---------------------------------------------------------------------------------------------------------------------
def paginas_pdf(pdf: Path) -> list[str]:
    """Texto de cada página (pdftotext de poppler). Lista vacía si no está."""
    if not shutil.which("pdftotext"):
        return []
    r = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, timeout=60)
    return r.stdout.split("\f") if r.returncode == 0 else []


def numerar_indice(docx: bytes, paginas: list[str], desde: int = 3) -> tuple[bytes, int]:
    """Pone en las entradas del índice la página en la que aparece cada título. Devuelve el .docx y cuántas cambian."""
    if not paginas:
        return docx, 0
    norm = lambda s: re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).upper()  # noqa: E731
    textos = [norm(p) for p in paginas]
    pq = ooxml.Paquete.desde_docx(docx)
    doc = pq.xml("word/document.xml")
    cambios, actual = 0, desde
    for p in doc.iter(W + "p"):
        if ooxml.estilo(p) not in ("TDC2", "TDC3"):
            continue
        for h in p.iter(W + "hyperlink"):
            ts = list(h.iter(W + "t"))
            if not ts or not re.fullmatch(r"\d+", ts[-1].text or ""):
                continue
            titulo = re.sub(r"\s*\d+$", "", "".join(t.text or "" for t in ts)).strip()
            real = next((i for i in range(actual, len(textos) + 1) if norm(titulo)[:40] in textos[i - 1]), None)
            if real:
                actual = real
                if ts[-1].text != str(real):
                    ts[-1].text = str(real)
                    cambios += 1
    return pq.a_bytes(), cambios


#: Carpeta de trabajo de Word en macOS, dentro de la de datos de la app. Word va aislado (sandbox) y pide permiso
#: («Conceder acceso al archivo») por cada carpeta que no conoce: con la temporal del sistema, que cambia en cada PDF,
#: lo pedía siempre; con una fija, solo la primera vez, y lo recuerda. Su propio contenedor no vale: macOS no deja que
#: otra app escriba en él («Operation not permitted»).
CARPETA_WORD = "conversion"
AYUDA_PERMISO_WORD = ("Si Word ha pedido «Conceder acceso al archivo», pulsa «Seleccionar…» y después «Conceder "
                      "acceso»: solo lo pide la primera vez.")


def carpeta_de_trabajo(usa_word: bool) -> Path | None:
    """Dónde convertir: en macOS con Word, la carpeta fija; si no, una temporal del sistema (None)."""
    if usa_word and sys.platform == "darwin":
        from .rutas import carpeta_datos

        carpeta = carpeta_datos() / CARPETA_WORD
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta
    return None


def exportar_pdf(docx: bytes, pdf: Path, motor: str = "auto", tiempo_max: int = TIEMPO_MAX) -> Path:
    """PDF de la programación. Con LibreOffice, dos pasadas: la segunda con las páginas del índice ya puestas."""
    pdf = Path(pdf)
    usa_word = motor == "word" or (motor == "auto" and hay_word())
    fija = carpeta_de_trabajo(usa_word)
    with tempfile.TemporaryDirectory(prefix="programaciones-pdf-") as tmp:
        # En la carpeta fija, directamente en ella (no en una subcarpeta nueva) y con un nombre que no se repite
        base = fija / f"{pdf.stem}-{uuid.uuid4().hex[:8]}" if fija else Path(tmp) / pdf.stem
        entrada, salida = Path(f"{base}.docx"), Path(f"{base}.pdf")
        try:
            entrada.write_bytes(sin_actualizar_campos(docx) if usa_word else docx)
            hecho = convertir(entrada, salida, motor, tiempo_max)
            if not usa_word:
                nuevo, cambios = numerar_indice(docx, paginas_pdf(hecho))
                if cambios:
                    entrada.write_bytes(nuevo)
                    hecho = convertir(entrada, salida, "libreoffice", tiempo_max)
            pdf.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(hecho), pdf)
        finally:
            entrada.unlink(missing_ok=True)
            salida.unlink(missing_ok=True)
    os.utime(pdf)
    return pdf
