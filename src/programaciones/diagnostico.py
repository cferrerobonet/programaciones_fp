"""Comprobación de los datos que la app lleva dentro: catálogo, esquemas y plantilla (sin Qt).

La usa la prueba de arranque de la app compilada (`PROGRAMACIONES_PRUEBA_DE_ARRANQUE`, `compilar.yml`): que el
ejecutable exista no basta, también tiene que encontrar y leer sus datos. Cada línea que devuelve va al registro con la
marca `MARCA_DATOS`, y la CI la busca.
"""

from __future__ import annotations

from .catalogo import Catalogo
from .documento import cargar_plantilla, metadatos_plantilla
from .programacion import nueva, validar
from .rutas import recursos

MARCA_DATOS = "PRUEBA DE ARRANQUE: datos empaquetados"
#: Un módulo que existe en el catálogo desde F1, para leer una ficha de verdad.
MUESTRA = ("SEA", "0517")
PARTES_PLANTILLA = ("[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/_rels/document.xml.rels")


def comprobar_datos(catalogo: Catalogo | None = None) -> list[str]:
    """Lee todo lo empaquetado y devuelve una línea por pieza. Lanza una excepción si falta algo."""
    cat = catalogo or Catalogo()
    siglas = cat.siglas()
    if not siglas:
        raise FileNotFoundError(f"El catálogo de {cat.carpeta} no tiene ciclos")
    filas = sum(len(cat.ciclo(s)["modulos"]) for s in siglas)
    ficha = cat.ficha(*MUESTRA)
    if not ficha.ra:
        raise ValueError(f"La ficha de {MUESTRA[1]} no tiene RA")
    meta = metadatos_plantilla()
    paquete = cargar_plantilla("es")
    faltan = [p for p in PARTES_PLANTILLA if p not in paquete.partes]
    if faltan:  # «_rels/.rels» empieza por punto: un empaquetador que se salte los ocultos la rompe
        raise FileNotFoundError(f"A la plantilla le faltan {', '.join(faltan)}")
    validar(nueva(MUESTRA[0], ficha.curso, MUESTRA[1], "2030-2031", cat.version, str(meta.get("version", ""))))
    fuentes = sorted(p.name for p in (recursos() / "fuentes").glob("*.ttf"))
    if not fuentes:
        raise FileNotFoundError("No hay tipografías en los recursos")
    return [
        f"catálogo {cat.version}: {len(siglas)} ciclos y {filas} módulos; {MUESTRA[1]} con {len(ficha.ra)} RA",
        f"plantilla {meta.get('version', '?')} con {len(paquete.partes)} partes",
        "esquema de la programación: una programación nueva es válida",
        f"{len(fuentes)} tipografías",
    ]
