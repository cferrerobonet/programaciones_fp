#!/usr/bin/env python3
"""Prueba manual del riesgo R1: ¿Word conserva los datos incrustados al abrir y guardar? (docs/PLAN_DE_PRUEBAS.md)

Uso:
  prueba_word.py preparar <carpeta>     escribe «Prueba R1 - ficticia.docx» (datos inventados) en la carpeta
  prueba_word.py comprobar <docx>…      dice si cada .docx guardado en Word conserva los datos y si el texto cambió

Pasos para CarlosFB (en Word de macOS y en Word de Windows, por separado):
1. `prueba_word.py preparar ~/Desktop` (o copiar el archivo que deja a un equipo con Windows).
2. Abrirlo en Word, aceptar la actualización de campos si la pide, escribir una palabra al final, guardar (Cmd/Ctrl+S)
   y cerrar. Hacer otra copia y guardarla también con «Guardar como…» .docx.
3. `prueba_word.py comprobar <cada archivo guardado>`.
Resultado esperado: «datos: sí» y «texto: cambiado en Word» (por la palabra añadida). Si sale «datos: no», Word quita la
parte y hay que aplicar el plan B de R1 (docs/HOJA_DE_RUTA.md).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from programaciones import documento, incrustar, programacion  # noqa: E402
from programaciones.catalogo import Catalogo  # noqa: E402

CURSO = {"evaluaciones": {"inicial": "2030-09-30", "primera": "2030-11-22", "segunda": "2031-02-28",
                          "tercera": "2031-05-30", "ordinaria": "2031-06-10", "extraordinaria": "2031-06-24"},
         "formacion_empresa": {"GS": {2: [{"jornada": 8, "dias": 43, "desde": "2031-03-03", "hasta": "2031-05-30"}]}}}


def ficticia(cat: Catalogo) -> dict:
    p = programacion.nueva("SEA", 2, "0517", "2030-2031", cat.version, documento.metadatos_plantilla()["version"])
    p["profesorado"] = ["Profesora de Prueba"]
    p["elementos"] = [{"id": "e1", "tipo": "E", "nombre": "EXAMEN 1", "ra": [1, 2]},
                      {"id": "e2", "tipo": "P", "nombre": "PRÁCTICA 1", "ra": [3, 4, 5, 6]}]
    p["unidades"] = [{"id": "u1", "titulo": "UD01. Unidad de prueba", "horas": 60, "trimestre": 1, "elemento": "e1"},
                     {"id": "u2", "titulo": "Práctica 1: Práctica de prueba", "horas": 43, "trimestre": 2,
                      "elemento": "e2"}]
    p["empresa"] = {"2": 12, "3": 13, "4": 13, "5": 13, "6": 12}
    p["ra_competencias"] = {str(n): ["a"] for n in range(1, 7)}
    p["metodologia"] = [{"texto": "Texto de prueba para comprobar que Word conserva los datos incrustados."}]
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    pr = sub.add_parser("preparar")
    pr.add_argument("carpeta", type=Path)
    co = sub.add_parser("comprobar")
    co.add_argument("docx", nargs="+", type=Path)
    a = ap.parse_args()
    if a.orden == "preparar":
        cat = Catalogo()
        prog = ficticia(cat)
        docx = incrustar.incrustar(documento.generar(prog, cat, CURSO), prog)
        destino = a.carpeta.expanduser() / "Prueba R1 - ficticia.docx"
        destino.write_bytes(docx)
        print(f"Escrito {destino}. Ábrelo en Word, añade una palabra, guárdalo y pasa «comprobar».")
        return 0
    fallos = 0
    for ruta in a.docx:
        try:
            r = incrustar.leer(ruta.read_bytes())
        except incrustar.DatosDanados as e:
            print(f"✗ {ruta.name}: datos dañados ({e})")
            fallos += 1
            continue
        if r is None:
            print(f"✗ {ruta.name}: datos: no (Word ha quitado la parte incrustada: plan B de R1)")
            fallos += 1
        else:
            estado = "cambiado en Word" if r.modificado_en_word else "igual que al exportar"
            print(f"✓ {ruta.name}: datos: sí ({r.parte}, catálogo {r.catalogo}) · texto: {estado}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
