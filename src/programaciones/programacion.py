"""Archivo de trabajo `.programacion` (JSON, formato `programaciones/1`): datos del profesor, lectura y escritura.

Solo se guarda lo que el profesor introduce; lo oficial sale del catálogo y lo calculado se recalcula
(docs/MODELO_DE_DATOS.md §2). La misma copia viaja dentro del .docx exportado (incrustar.py).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

from programaciones.catalogo import esquema

FORMATO = "programaciones/1"
BLOQUES = ("profesorado", "unidades", "empresa", "ra_competencias", "contenidos", "metodologia", "recursos", "espacios",
           "notas", "actividades", "textos_propios")
LISTAS_DE_PARRAFOS = ("contenidos", "notas_tabla4", "notas_tabla41", "metodologia", "metodologia_final", "recursos",
                      "espacios", "actividades")


class ProgramacionNoValida(ValueError):
    """El archivo no cumple el esquema o es de un formato que la app no sabe abrir."""


def nueva(ciclo: str, curso: int, modulo: str, curso_escolar: str, catalogo: str, plantilla: str) -> dict:
    """Programación vacía de un módulo: todos los bloques del profesor, vacíos."""
    return {
        "formato": FORMATO, "catalogo": catalogo, "plantilla": plantilla, "curso_escolar": curso_escolar,
        "ciclo": ciclo, "curso": curso, "modulo": modulo, "profesorado": [], "unidades": [], "elementos": [],
        "empresa": {}, "centro_ajustado": {}, "ra_competencias": {}, **{k: [] for k in LISTAS_DE_PARRAFOS},
        "textos_propios": {}, "bloques": {b: "vacio" for b in BLOQUES}, "historial": [],
    }


def errores(datos: dict) -> list[str]:
    v = Draft202012Validator(esquema("programacion"))
    return [f"{'/'.join(str(x) for x in e.absolute_path) or '(raíz)'}: {e.message}" for e in v.iter_errors(datos)]


def migrar(datos: dict) -> dict:
    """Formatos anteriores → el actual. Hoy solo existe programaciones/1."""
    if datos.get("formato") != FORMATO:
        raise ProgramacionNoValida(f"Formato desconocido: {datos.get('formato')!r}")
    return datos


def validar(datos: dict) -> dict:
    datos = migrar(copy.deepcopy(datos))
    e = errores(datos)
    if e:
        raise ProgramacionNoValida("; ".join(e[:5]))
    return datos


def canonico(datos: dict) -> bytes:
    """JSON canónico (claves ordenadas, sin espacios): el de las huellas."""
    return json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def huella(datos: dict) -> str:
    return "sha256:" + hashlib.sha256(canonico(datos)).hexdigest()


def leer(ruta: Path) -> dict:
    try:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ProgramacionNoValida(f"No se puede leer {Path(ruta).name}: {e}") from e
    return validar(datos)


def escribir(ruta: Path, datos: dict) -> None:
    """Escritura atómica: archivo temporal en la misma carpeta y sustitución."""
    datos = validar(datos)
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".", suffix=".tmp", dir=ruta.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(tmp, ruta)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
