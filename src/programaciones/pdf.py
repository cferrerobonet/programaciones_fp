"""PDF de la programación con el Word del equipo o, si no hay, con LibreOffice sin interfaz (TRD §1).

- Word: AppleScript en macOS y COM (PowerShell) en Windows. Sin probar en la CI: prueba manual (docs/PLAN_DE_PRUEBAS.md).
  En macOS se convierte dentro del contenedor de Word, para que no pida permiso a cada vista previa.
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


def hay_word() -> bool:
    if sys.platform == "darwin":
        return Path("/Applications/Microsoft Word.app").is_dir()
    if sys.platform.startswith("win"):
        try:
            import winreg

            winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application")
            return True
        except OSError:
            return False
    return False


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


APPLESCRIPT = '''on run argv
  set entrada to POSIX file (item 1 of argv)
  set salida to item 2 of argv
  tell application "Microsoft Word"
    open entrada
    set d to active document
    save as d file name salida file format format PDF
    close d saving no
  end tell
end run'''

POWERSHELL = ("$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
              "try {{ $d = $w.Documents.Open('{entrada}', $false, $true); $d.SaveAs([ref]'{salida}', [ref]17); "
              "$d.Close($false) }} finally {{ $w.Quit() }}")


def con_word(docx: Path, pdf: Path, tiempo_max: int = TIEMPO_MAX) -> Path:
    if sys.platform == "darwin":
        _ejecutar(["osascript", "-e", APPLESCRIPT, str(docx.resolve()), str(pdf.resolve())], tiempo_max)
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
    raise ErrorPDF("; ".join(errores) or "No hay Word ni LibreOffice en este equipo: solo se exporta el Word (R3)")


# ---------------------------------------------------------------------------------------------------------------------
# Páginas del índice desde el PDF (paginas_indice.py de la skill programacion-didactica)
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


#: Carpeta de trabajo de Word en macOS. Word va aislado (sandbox): fuera de su contenedor pide permiso por cada carpeta
#: nueva («Conceder acceso al archivo»), y la temporal del sistema cambia en cada PDF; dentro de él, no pregunta.
CONTENEDOR_WORD = Path.home() / "Library" / "Containers" / "com.microsoft.Word" / "Data" / "tmp"


def carpeta_de_trabajo(usa_word: bool) -> str | None:
    """Dónde convertir: en macOS con Word, su contenedor; si no, la temporal del sistema (None)."""
    if usa_word and sys.platform == "darwin" and CONTENEDOR_WORD.parent.is_dir():
        CONTENEDOR_WORD.mkdir(exist_ok=True)
        return str(CONTENEDOR_WORD)
    return None


def exportar_pdf(docx: bytes, pdf: Path, motor: str = "auto", tiempo_max: int = TIEMPO_MAX) -> Path:
    """PDF de la programación. Con LibreOffice, dos pasadas: la segunda con las páginas del índice ya puestas."""
    pdf = Path(pdf)
    usa_word = motor == "word" or (motor == "auto" and hay_word())
    with tempfile.TemporaryDirectory(prefix="programaciones-pdf-", dir=carpeta_de_trabajo(usa_word)) as tmp:
        entrada = Path(tmp) / (pdf.stem + ".docx")
        entrada.write_bytes(docx)
        hecho = convertir(entrada, Path(tmp) / (pdf.stem + ".pdf"), motor, tiempo_max)
        if not usa_word:
            nuevo, cambios = numerar_indice(docx, paginas_pdf(hecho))
            if cambios:
                entrada.write_bytes(nuevo)
                hecho = convertir(entrada, Path(tmp) / (pdf.stem + ".pdf"), "libreoffice", tiempo_max)
        pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(hecho), pdf)
    os.utime(pdf)
    return pdf
