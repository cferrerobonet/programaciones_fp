"""Exportar la programación (RF-06, RF-07): el trabajo que la interfaz lanza en una `Tarea` (RNF-03). Sin Qt.

- `exportar`: rellena la plantilla, incrusta los datos del profesor (ADR-002), comprueba el documento con las reglas de
  la guía `programacion-didactica` (`contenido.verificar`) y escribe el `.docx` y, si se pide, el `.pdf` con el nombre
  normalizado. Si no hay Word ni LibreOffice, queda el `.docx` y se avisa (R3).
- `vista_previa`: el mismo documento con la marca «BORRADOR», convertido a PDF en una carpeta temporal.

`avance(paso, total, texto)` cuenta cada paso a la ventana «Exportando».
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from programaciones import contenido, documento, incrustar, pdf
from programaciones.catalogo import Catalogo

Avance = Callable[[int, int, str], None]
NOMBRES_MOTOR = {"word": "Word", "libreoffice": "LibreOffice"}


class DocumentoConErrores(RuntimeError):
    """El documento generado no pasa las comprobaciones de la guía: no se escribe."""


@dataclass
class Resultado:
    archivos: list[Path] = field(default_factory=list)
    error_pdf: str = ""


def destinos(prog: dict, cat: Catalogo, carpeta: Path, formatos: list[str]) -> list[Path]:
    """Los archivos que escribirá la exportación, con el nombre normalizado (`documento.nombre_archivo`)."""
    ficha = cat.ficha(prog["ciclo"], prog["modulo"], prog.get("curso"))
    return [Path(carpeta) / documento.nombre_archivo(ficha, f) for f in ("docx", "pdf") if f in formatos]


def texto_motor(motor: str) -> str:
    if motor == "auto":
        return "Word" if pdf.hay_word() else "LibreOffice"
    return NOMBRES_MOTOR.get(motor, motor)


def problemas(docx: bytes) -> list[str]:
    """Lo que `verificar.py` de la guía daría como aviso en el documento generado."""
    v = contenido.verificar(docx, contenido.titulos(documento.cargar_plantilla().a_bytes()))
    out = []
    if not v["titulos_iguales"]:
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
    rutas = destinos(prog, cat, carpeta, formatos)
    res = Resultado()
    if "docx" in formatos:
        _escribir(rutas[0], docx)
        res.archivos.append(rutas[0])
    if "pdf" in formatos:
        avance(2, total, f"Convirtiendo a PDF con {texto_motor(motor)}")
        try:
            res.archivos.append(pdf.exportar_pdf(docx, rutas[-1], motor))
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
