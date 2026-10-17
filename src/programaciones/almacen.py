"""Programaciones guardadas en este equipo (RF-05, RNF-05): el archivo de trabajo de cada una y sus copias.

En la carpeta de datos (TRD §5):
- `programaciones/<curso escolar>/<SIGLA>-<curso>-<código>.programacion`: la de cada módulo y curso escolar, que la app
  guarda sola al cambiar algo (escritura atómica de `programacion.escribir`).
- `autoguardado/<id>/AAAAMMDD-HHMMSS.programacion`: las 10 últimas versiones de cada una, para recuperarse de un error.

Lo que no se puede perder viaja además dentro del `.docx` exportado (ADR-002). Sin Qt.
"""
from __future__ import annotations

import datetime as dt
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from programaciones import programacion

logger = logging.getLogger(__name__)
VERSIONES = 10
#: Pasos de la interfaz → bloques de la programación que confirma cada uno (DESIGN.md, «Bloques del profesor»).
PASOS = {
    "profesorado": ("Profesorado", ("profesorado",)),
    "unidades": ("Unidades y evaluación", ("unidades", "contenidos", "notas")),
    "empresa": ("Empresa por RA", ("empresa",)),
    "ra_competencias": ("RA y competencias", ("ra_competencias",)),
    "metodologia": ("Metodología y recursos", ("metodologia", "recursos", "espacios", "actividades", "textos_propios")),
}


#: Ámbitos de GB (ADR-032): sin empresa por RA ni RA y competencias (sus descriptores los da la norma). Una
#: programación de ámbito se reconoce por llevar `partes`.
PASOS_AMBITO = ("profesorado", "unidades", "metodologia")


def pasos(prog: dict | None) -> list[str]:
    """Los pasos que tiene una programación: los cinco o, en un ámbito, tres."""
    return list(PASOS_AMBITO) if prog is not None and "partes" in prog else list(PASOS)


def identificador(prog: dict) -> str:
    return f"{prog['ciclo']}-{prog['curso']}-{prog['modulo']}"


def estado_paso(prog: dict, paso: str) -> str:
    """«heredado» si alguno de sus bloques lo está; «confirmado» si alguno está confirmado; si no, «vacio»."""
    estados = [prog.get("bloques", {}).get(b, "vacio") for b in PASOS[paso][1]]
    if "heredado" in estados:
        return "heredado"
    return "confirmado" if "confirmado" in estados else "vacio"


def confirmados(prog: dict) -> int:
    return sum(1 for p in pasos(prog) if estado_paso(prog, p) == "confirmado")


def ultima_exportacion(prog: dict) -> str:
    """Fecha ISO de la última exportación (del historial) o «»."""
    return next((h["fecha"] for h in reversed(prog.get("historial", [])) if h["accion"].startswith("exportada")), "")


def estado(prog: dict) -> str:
    """«heredada», «exportada» (sin cambios desde la última exportación) o «en_curso»."""
    if any(estado_paso(prog, p) == "heredado" for p in PASOS):
        return "heredada"
    historial = prog.get("historial", [])
    if historial and historial[-1]["accion"].startswith("exportada"):
        return "exportada"
    return "en_curso"


def texto_estado(prog: dict) -> str:
    e = estado(prog)
    if e == "heredada":
        return "Heredada · sin revisar"
    if e == "exportada":
        return "Exportada"
    return f"En curso · {confirmados(prog)} de {len(pasos(prog))}"


def anotar(prog: dict, accion: str, cuando: dt.datetime | None = None) -> None:
    prog.setdefault("historial", []).append(
        {"fecha": (cuando or dt.datetime.now()).isoformat(timespec="minutes"), "accion": accion})


def marcar_cambio(prog: dict) -> None:
    """Tras un cambio del profesor: si estaba exportada, deja constancia de que ya no es la exportada."""
    historial = prog.get("historial", [])
    if historial and historial[-1]["accion"].startswith("exportada"):
        anotar(prog, "modificada tras exportar")


@dataclass
class Guardada:
    ruta: Path
    programacion: dict

    @property
    def id(self) -> str:
        return f"{self.programacion['curso_escolar']}/{identificador(self.programacion)}"


class Almacen:
    def __init__(self, carpeta: Path):
        self.carpeta = Path(carpeta)
        self.raiz = self.carpeta / "programaciones"
        self.copias = self.carpeta / "autoguardado"

    def ruta(self, prog: dict) -> Path:
        return self.raiz / prog["curso_escolar"] / f"{identificador(prog)}.programacion"

    def guardar(self, prog: dict, cuando: dt.datetime | None = None) -> Path:
        """Escribe la programación y una copia fechada; conserva las `VERSIONES` últimas."""
        ruta = self.ruta(prog)
        programacion.escribir(ruta, prog)
        sello = (cuando or dt.datetime.now()).strftime("%Y%m%d-%H%M%S-%f")
        carpeta = self.copias / f"{prog['curso_escolar']}-{identificador(prog)}"
        programacion.escribir(carpeta / f"{sello}.programacion", prog)
        for vieja in sorted(carpeta.glob("*.programacion"))[:-VERSIONES]:
            vieja.unlink(missing_ok=True)
        return ruta

    def cargar(self, curso_escolar: str, ciclo: str, curso: int, modulo: str) -> dict | None:
        ruta = self.raiz / curso_escolar / f"{ciclo}-{curso}-{modulo}.programacion"
        if not ruta.is_file():
            return None
        try:
            return programacion.leer(ruta)
        except programacion.ProgramacionNoValida:
            logger.exception("No se puede leer %s", ruta)
            return None

    def todas(self) -> list[Guardada]:
        out = []
        for ruta in sorted(self.raiz.glob("*/*.programacion")):
            try:
                out.append(Guardada(ruta, programacion.leer(ruta)))
            except programacion.ProgramacionNoValida:
                logger.warning("Se ignora %s: no es una programación válida", ruta)
        return out

    def quitar(self, prog: dict, papelera: Callable[[Path], bool]) -> list[Path]:
        """Quita la programación de este equipo: su archivo de trabajo y sus copias de autoguardado van a la papelera
        del sistema, de donde se pueden recuperar (ADR-024). Nunca toca lo exportado (Word, PDF, Teams). Si la papelera
        no acepta el archivo de trabajo, no se quita nada y se lanza OSError."""
        movidos = []
        carpeta = self.copias / f"{prog['curso_escolar']}-{identificador(prog)}"
        for ruta in (self.ruta(prog), carpeta):
            if not ruta.exists():
                continue
            if not papelera(ruta):
                raise OSError(f"No se ha podido mover «{ruta.name}» a la papelera")
            movidos.append(ruta)
        return movidos
