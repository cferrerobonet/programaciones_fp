"""Dónde vive cada cosa: los datos de este equipo y lo que va dentro de la app (también congelada)."""

import os
import sys
from pathlib import Path

CARPETA = "Programaciones"


def congelada() -> bool:
    """True dentro del ejecutable de PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def carpeta_datos() -> Path:
    """Carpeta de datos del usuario. `PROGRAMACIONES_DATOS` la cambia (pruebas)."""
    propia = os.environ.get("PROGRAMACIONES_DATOS")
    if propia:
        base = Path(propia)
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / CARPETA
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home()) / CARPETA
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / CARPETA
    base.mkdir(parents=True, exist_ok=True)
    return base


def base_empaquetada() -> Path:
    """Raíz de los datos de la app congelada (`sys._MEIPASS`)."""
    return Path(sys._MEIPASS)  # type: ignore[attr-defined]


def recursos() -> Path:
    """Tipografías, logos, icono y plantilla: dentro del paquete o de la app congelada."""
    if congelada():
        return base_empaquetada() / "programaciones" / "recursos"
    return Path(__file__).resolve().parent / "recursos"
