"""«Nueva a partir de…» (RF-09, ADR-008): una programación nueva desde la del curso pasado, la del profesor o de otro.

- Los bloques del profesor llegan como **heredados**: la exportación definitiva exige confirmarlos (V-06).
- Lo oficial no se copia: sale del catálogo de ahora. La programación nueva lleva la versión del catálogo y de la
  plantilla vigentes y el curso escolar nuevo (las fechas salen del curso escolar al generar el documento).
- Los RA que ya no tiene el módulo se quitan de elementos, empresa, ajustes de centro y competencias, y se avisa.
- La app nunca completa datos del profesor: lo que estaba vacío sigue vacío.
"""
from __future__ import annotations

import copy
import datetime as dt
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from programaciones import documento, importar_docx, programacion
from programaciones.catalogo import Catalogo

EXTENSIONES = (".docx", ".programacion")


@dataclass
class Origen:
    """Lo que trae el archivo elegido, antes de heredar."""
    programacion: dict
    archivo: str
    exportada_por_la_app: bool       # .programacion o .docx con los datos incrustados
    modificado_en_word: bool = False


@dataclass
class Herencia:
    programacion: dict
    avisos: list[str] = field(default_factory=list)

    @property
    def resumen(self) -> dict[str, int]:
        p = self.programacion
        return {"unidades": len(p.get("unidades", [])), "elementos": len(p.get("elementos", [])),
                "ra_empresa": sum(1 for v in (p.get("empresa") or {}).values() if v),
                "heredados": sum(1 for v in p["bloques"].values() if v == "heredado")}


def leer_origen(ruta: str | Path, cat: Catalogo, modulo: importar_docx.Modulo | None = None,
                comprobar: bool = True) -> Origen:
    """Lee un `.programacion` o un `.docx` (exportado por la app o una programación antigua con la plantilla).
    `modulo`: el elegido en la columna «Módulos», para un Word sin datos de la app (`importar_docx.decidir_modulo`).

    Lanza `programacion.ProgramacionNoValida`, `importar_docx.NoEsProgramacion`, `importar_docx.ModuloDistinto` o
    `incrustar.DatosDanados`."""
    from programaciones import incrustar

    ruta = Path(ruta)
    if ruta.suffix.lower() == ".programacion":
        return Origen(programacion.leer(ruta), ruta.name, True)
    if ruta.suffix.lower() != ".docx":
        raise importar_docx.NoEsProgramacion(f"«{ruta.name}» no es un .docx ni un .programacion")
    datos = ruta.read_bytes()
    try:
        incrustada = incrustar.leer(datos)
    except zipfile.BadZipFile as e:
        raise importar_docx.NoEsProgramacion(f"«{ruta.name}» no es un documento de Word válido") from e
    if incrustada is not None:
        return Origen(incrustada.programacion, ruta.name, True, incrustada.modificado_en_word)
    return Origen(importar_docx.importar(datos, cat, ruta.name, modulo, comprobar), ruta.name, False)


def heredar(origen: dict, cat: Catalogo, curso_escolar: str, archivo: str = "") -> Herencia:
    """La programación nueva del curso `curso_escolar` a partir de `origen` (ya validada)."""
    viejo = programacion.validar(origen)
    ficha = cat.ficha(viejo["ciclo"], viejo["modulo"], viejo.get("curso"))
    ras = set(ficha.numeros_ra)
    nuevo = programacion.nueva(viejo["ciclo"], viejo["curso"], viejo["modulo"], curso_escolar, cat.version,
                               documento.metadatos_plantilla()["version"])
    for clave in ("profesorado", "unidades", "elementos", "empresa", "centro_ajustado", "modalidad", "ra_competencias",
                  "partes", "textos_propios", *programacion.LISTAS_DE_PARRAFOS):
        if clave in viejo:
            nuevo[clave] = copy.deepcopy(viejo[clave])
    if "columna_pct_curso" in viejo:
        nuevo["columna_pct_curso"] = viejo["columna_pct_curso"]

    avisos = []
    quitados: set[int] = set()
    for e in nuevo["elementos"]:
        fuera = [int(r) for r in e.get("ra", []) if int(r) not in ras]
        if fuera:
            quitados.update(fuera)
            e["ra"] = [r for r in e["ra"] if int(r) in ras]
    for clave in ("empresa", "centro_ajustado", "modalidad", "ra_competencias"):
        fuera = [k for k in nuevo.get(clave, {}) if int(k) not in ras]
        quitados.update(int(k) for k in fuera)
        for k in fuera:
            del nuevo[clave][k]
    for r in sorted(quitados):
        avisos.append(f"RA{r}: el módulo ya no lo tiene; se ha quitado de tus bloques")
    for r in sorted(ras - {int(k) for k in nuevo["ra_competencias"]}):
        if viejo.get("ra_competencias"):
            avisos.append(f"RA{r}: nuevo o sin competencias; márcalas en «RA y competencias»")

    estados = viejo.get("bloques") or {}
    nuevo["bloques"] = {b: "heredado" if _con_datos(viejo, b) or estados.get(b) == "heredado" else "vacio"
                        for b in programacion.BLOQUES}
    profesor = next((p for p in viejo.get("profesorado", []) if p.strip()), "")
    nuevo["heredada_de"] = {k: v for k, v in (("profesor", profesor), ("curso_escolar", viejo["curso_escolar"]),
                                               ("archivo", archivo)) if v}
    nuevo["historial"] = [{"fecha": dt.datetime.now().isoformat(timespec="minutes"),
                           "accion": f"heredada de {archivo or 'otra programación'}"}]
    return Herencia(programacion.validar(nuevo), avisos)


#: Bloque de la programación → claves con sus datos (para saber si un bloque llega con algo).
CLAVES_BLOQUE = {
    "profesorado": ("profesorado",), "unidades": ("unidades", "elementos", "partes"), "empresa": ("empresa", "centro_ajustado", "modalidad"),
    "ra_competencias": ("ra_competencias",), "contenidos": ("contenidos",), "metodologia": ("metodologia",
                                                                                            "metodologia_final"),
    "recursos": ("recursos",), "espacios": ("espacios",), "notas": ("notas_tabla4", "notas_tabla41"),
    "actividades": ("actividades",), "textos_propios": ("textos_propios",),
}


def _con_datos(prog: dict, bloque: str) -> bool:
    return any(prog.get(k) for k in CLAVES_BLOQUE.get(bloque, ()))
