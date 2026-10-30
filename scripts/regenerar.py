#!/usr/bin/env python3
"""Regenera las programaciones de referencia y las compara con su .docx (criterio de cierre de F2).

Uso:
  regenerar.py <carpeta 01 DOCENCIA/FP> [código…] [--salida <carpeta>] [--pdf]

Para cada programación de referencia («SIGLA N - 0xxx - Nombre.docx» en «<módulo>/01 Programación/»):
1. importa sus datos del profesor (importar_docx.importar);
2. toma de ella las fechas del curso (mientras no exista catalogo/cursos/2026-2027.yaml);
3. genera el documento con la plantilla y el catálogo;
4. compara el contenido apartado a apartado (contenido.comparar) y escribe las diferencias.
Las programaciones de la carpeta 02 EPLA se leen en local y nada de ellas se escribe en el repositorio: la salida va a la
carpeta que se indique (por defecto, una temporal fuera de iCloud).
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from programaciones import contenido, documento, importar_docx, incrustar  # noqa: E402
from programaciones.catalogo import Catalogo  # noqa: E402

CODIGOS = ["0517", "0524", "0525", "0526", "0962", "0963"]


def referencia(carpeta: Path, codigo: str) -> Path:
    encontradas = sorted(carpeta.glob(f"*/01 Programación/* - {codigo} - *.docx"))
    if len(encontradas) != 1:
        raise SystemExit(f"{codigo}: {len(encontradas)} programaciones en {carpeta}")
    return encontradas[0]


def regenerar(ruta: Path, cat: Catalogo) -> tuple[dict, bytes]:
    prog = importar_docx.importar(ruta, cat)
    ficha = cat.ficha(prog["ciclo"], prog["modulo"], prog["curso"])
    curso = cat.curso_escolar(prog["curso_escolar"]) or importar_docx.leer_curso(ruta, ficha.grado, ficha.curso)
    docx = documento.generar(prog, cat, curso)
    return prog, incrustar.incrustar(docx, prog)


def palabras(a: str, b: str) -> str:
    """Las palabras que cambian: «− referencia + generado»."""
    import difflib
    x, y = a.split(), b.split()
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, x, y, autojunk=False).get_opcodes():
        if op != "equal":
            out.append(f"−«{' '.join(x[i1:i2])}» +«{' '.join(y[j1:j2])}»")
    return " · ".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carpeta", type=Path)
    ap.add_argument("codigos", nargs="*", default=CODIGOS)
    ap.add_argument("--salida", type=Path, default=Path(tempfile.gettempdir()) / "programaciones-regeneradas")
    ap.add_argument("--detalle", action="store_true", help="en lo que cambia, solo las palabras distintas")
    a = ap.parse_args()
    cat = Catalogo()
    a.salida.mkdir(parents=True, exist_ok=True)
    total = 0
    for codigo in a.codigos:
        ruta = referencia(a.carpeta, codigo)
        _prog, docx = regenerar(ruta, cat)
        destino = a.salida / ruta.name
        destino.write_bytes(docx)
        difs, de_forma = contenido.comparar(ruta.read_bytes(), docx)
        total += len(difs)
        print(f"{'✓' if not difs else '✗'} {codigo}: {len(difs)} diferencias de contenido, {de_forma} de forma → {destino}")
        for d in difs:
            print("   ", d)
            if a.detalle and d.cambio == "cambia":
                print("       ", palabras(d.referencia, d.generado))
            if a.detalle:
                print("        firma:", d.firma)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
