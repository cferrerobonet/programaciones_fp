"""Ajustes de este equipo: el profesor, la carpeta de entrega de cada curso y la exportación (TRD §7).

Cada profesor instala la app en su equipo y la configura a su manera. Aquí no hay contraseñas ni datos del servidor de
correo (ADR-016): el repositorio es público y los valores por defecto van vacíos. El correo del departamento que sale
en el pie del documento (ADR-018, decisión 11) también se escribe en Ajustes de cada equipo, nunca en el repositorio.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field, fields
from datetime import date
from pathlib import Path

FORMATOS = ("docx", "pdf")
PROGRAMAS_PDF = {"auto": "Automático (Word → LibreOffice)", "word": "Microsoft Word", "libreoffice": "LibreOffice"}
IDIOMAS = {"es": "Castellano", "va": "Valencià", "en": "English"}  # solo «es» hasta F10 (ADR-013)
RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class Ajustes:
    nombre_profesor: str = ""
    #: Curso escolar («2026-2027») → carpeta de entrega: ruta local sincronizada con OneDrive o enlace de Teams.
    carpetas_entrega: dict[str, str] = field(default_factory=dict)
    formatos: list[str] = field(default_factory=lambda: list(FORMATOS))
    programa_pdf: str = "auto"
    idioma: str = "es"
    correo_pie: str = ""


def curso_escolar_de(dia: date | None = None) -> str:
    """Curso escolar de una fecha: de septiembre a agosto («2026-2027» del 2026-09-01 al 2027-08-31)."""
    dia = dia or date.today()
    inicio = dia.year if dia.month >= 9 else dia.year - 1
    return f"{inicio}-{inicio + 1}"


def correo_valido(texto: str) -> bool:
    return bool(RE_CORREO.match(texto.strip()))


def estado_carpeta(valor: str) -> str:
    """«vacia», «enlace» (de Teams o SharePoint: se exporta en local y se abre en el navegador, ADR-009), «local» o
    «no_encontrada»."""
    valor = (valor or "").strip()
    if not valor:
        return "vacia"
    if valor.lower().startswith(("https://", "http://")):
        return "enlace"
    return "local" if Path(valor).expanduser().is_dir() else "no_encontrada"


def _limpios(datos: dict) -> dict:
    """Solo las claves conocidas y con el tipo de su valor por defecto: un archivo tocado a mano no tumba la app."""
    defecto = Ajustes()
    out = {}
    for f in fields(Ajustes):
        if f.name in datos and isinstance(datos[f.name], type(getattr(defecto, f.name))):
            out[f.name] = datos[f.name]
    if "carpetas_entrega" in out:
        out["carpetas_entrega"] = {str(k): str(v) for k, v in out["carpetas_entrega"].items()}
    if "formatos" in out:
        out["formatos"] = [f for f in out["formatos"] if f in FORMATOS]
    if out.get("programa_pdf") not in (None, *PROGRAMAS_PDF):
        del out["programa_pdf"]
    if out.get("idioma") not in (None, *IDIOMAS):
        del out["idioma"]
    return out


class GestorAjustes:
    def __init__(self, carpeta: Path):
        self.carpeta = Path(carpeta)
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self.ruta = self.carpeta / "ajustes.json"
        self.valores = self._cargar()

    def _cargar(self) -> Ajustes:
        if not self.ruta.exists():
            return Ajustes()
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return Ajustes()
        return Ajustes(**_limpios(datos)) if isinstance(datos, dict) else Ajustes()

    def guardar(self) -> None:
        temporal = self.ruta.with_suffix(".tmp")
        temporal.write_text(json.dumps(asdict(self.valores), ensure_ascii=False, indent=2), encoding="utf-8")
        temporal.replace(self.ruta)

    def poner(self, **cambios) -> None:
        for k, v in cambios.items():
            if not hasattr(self.valores, k):
                raise AttributeError(f"Ajuste desconocido: {k}")
            setattr(self.valores, k, v)
        self.guardar()

    def carpeta_entrega(self, curso: str) -> str:
        return self.valores.carpetas_entrega.get(curso, "")

    def poner_carpeta_entrega(self, curso: str, valor: str) -> None:
        carpetas = dict(self.valores.carpetas_entrega)
        if valor.strip():
            carpetas[curso] = valor.strip()
        else:
            carpetas.pop(curso, None)
        self.poner(carpetas_entrega=carpetas)
