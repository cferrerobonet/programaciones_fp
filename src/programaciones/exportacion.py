"""Exportar la programación (RF-06, RF-07): el trabajo que la interfaz lanza en una `Tarea` (RNF-03). Sin Qt.

- `exportar`: rellena la plantilla, incrusta los datos del profesor (ADR-002), comprueba el documento con las reglas de
  la guía `programacion-didactica` (`contenido.verificar`) y escribe el `.docx` y, si se pide, el `.pdf` con el nombre
  normalizado. Si no hay Word, LibreOffice ni ONLYOFFICE, queda el `.docx` y se avisa (R3).
- `vista_previa`: el mismo documento con la marca «BORRADOR», convertido a PDF en una carpeta temporal.

`avance(paso, total, texto)` cuenta cada paso a la ventana «Exportando».
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from programaciones import contenido, documento, excel_ra, incrustar, pdf
from programaciones.ajustes import estado_carpeta
from programaciones.catalogo import Catalogo

Avance = Callable[[int, int, str], None]
NOMBRES_MOTOR = {"word": "Word", "libreoffice": "LibreOffice", "onlyoffice": "ONLYOFFICE"}


class DocumentoConErrores(RuntimeError):
    """El documento generado no pasa las comprobaciones de la guía: no se escribe."""


@dataclass
class Resultado:
    archivos: list[Path] = field(default_factory=list)
    error_pdf: str = ""


def destinos(prog: dict, cat: Catalogo, carpeta: Path, formatos: list[str]) -> list[Path]:
    """Los archivos que escribirá la exportación, con el nombre normalizado (`documento.nombre_archivo`). El Excel de RA
    solo en los módulos que lo tienen (no en los ámbitos de GB)."""
    ficha = cat.ficha(prog["ciclo"], prog["modulo"], prog.get("curso"))
    return [Path(carpeta) / documento.nombre_archivo(ficha, f) for f in ("docx", "pdf", "xlsx")
            if f in formatos and (f != "xlsx" or excel_ra.aplica(ficha))]


def carpeta_habitual(carpeta_entrega: str, curso_escolar: str, documentos: Path) -> Path:
    """Dónde deja la app los archivos de un curso cuando no pregunta: la carpeta de entrega si es de este equipo; si no
    (enlace de Teams, sin carpeta o no encontrada), «Documentos/Programaciones <curso>» (ADR-021)."""
    if estado_carpeta(carpeta_entrega) == "local":
        return Path(carpeta_entrega).expanduser()
    return Path(documentos) / f"Programaciones {curso_escolar}"


def texto_motor(motor: str) -> str:
    if motor == "auto":
        return "Word" if pdf.hay_word() else "LibreOffice" if pdf.soffice() else "ONLYOFFICE"
    return NOMBRES_MOTOR.get(motor, motor)


def problemas(docx: bytes) -> list[str]:
    """Lo que `verificar.py` de la guía daría como aviso en el documento generado."""
    esperados = contenido.titulos(documento.cargar_plantilla().a_bytes())
    v = contenido.verificar(docx, esperados)
    out = []
    # Grado Básico no lleva el 2.2 de optativos ofertados (documento.py: con_optativos); los ámbitos, su plantilla
    validos = [[t for t in esperados if not t.startswith("2.2")],
               contenido.titulos(documento.cargar_plantilla(ambito=True).a_bytes())]
    titulos = [t.rstrip() for t in contenido.titulos(docx)]
    if not v["titulos_iguales"] and not any(titulos == [t.rstrip() for t in otros] for otros in validos):
        out.append("los títulos no son los de la plantilla")
    if v["campo_toc"] != 1:
        out.append("falta el índice automático")
    if v["citas_sin_enlace"]:
        out.append(f"normas citadas sin enlace: {', '.join(v['citas_sin_enlace'][:3])}")
    if v["termino_vetado"]:
        out.append("palabra no permitida en el documento")
    if not v["update_fields"]:
        out.append("el índice no se actualiza al abrir")
    return out


def _escribir(ruta: Path, datos: bytes) -> None:
    """Escritura atómica: un temporal en la misma carpeta y sustitución (no deja un .docx a medias)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".", suffix=ruta.suffix, dir=ruta.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(datos)
        os.replace(tmp, ruta)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def exportar(prog: dict, cat: Catalogo, curso: dict | None, carpeta: Path, formatos: list[str],
             opciones: documento.Opciones, motor: str = "auto", avance: Avance | None = None) -> Resultado:
    avance = avance or (lambda *_: None)
    total = 3 if "pdf" in formatos else 2
    avance(0, total, "Rellenando la plantilla")
    docx = incrustar.incrustar(documento.generar(prog, cat, curso, opciones), prog)
    avance(1, total, "Comprobando el documento")
    fallos = problemas(docx)
    if fallos:
        raise DocumentoConErrores("El documento no pasa las comprobaciones: " + "; ".join(fallos))
    rutas = {r.suffix[1:]: r for r in destinos(prog, cat, carpeta, formatos)}
    res = Resultado()
    if "docx" in rutas:
        _escribir(rutas["docx"], docx)
        res.archivos.append(rutas["docx"])
    if "xlsx" in rutas:
        _escribir(rutas["xlsx"], excel_ra.generar(prog, cat))
        res.archivos.append(rutas["xlsx"])
    if "pdf" in rutas:
        avance(2, total, f"Convirtiendo a PDF con {texto_motor(motor)}")
        try:
            res.archivos.append(pdf.exportar_pdf(docx, rutas["pdf"], motor))
        except pdf.ErrorPDF as e:
            res.error_pdf = str(e)
    avance(total, total, "Hecho")
    return res


def vista_previa(prog: dict, cat: Catalogo, curso: dict | None, opciones: documento.Opciones, carpeta: Path,
                 motor: str = "auto", avance: Avance | None = None) -> Path:
    """PDF con la marca «BORRADOR» en `carpeta` (temporal). Lanza `pdf.ErrorPDF` si no hay con qué convertir."""
    avance = avance or (lambda *_: None)
    avance(0, 2, "Rellenando la plantilla")
    borrador = documento.Opciones(borrador=True, correo_pie=opciones.correo_pie, idioma=opciones.idioma)
    docx = documento.generar(prog, cat, curso, borrador)
    avance(1, 2, f"Convirtiendo a PDF con {texto_motor(motor)}")
    ficha = cat.ficha(prog["ciclo"], prog["modulo"], prog.get("curso"))
    salida = pdf.exportar_pdf(docx, Path(carpeta) / documento.nombre_archivo(ficha, "pdf"), motor)
    avance(2, 2, "Hecho")
    return salida
