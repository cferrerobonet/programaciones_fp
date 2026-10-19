"""Importar una programación del formato antiguo del departamento (anterior a la plantilla de PIICT).

Los datos del profesor son los mismos, en otros apartados y con títulos que son párrafos normales («7.- TEMPORALIZACIÓN…»,
sin estilo de título):

| Formato antiguo | Formato actual |
| --- | --- |
| Portada: «Profesores», «Curso académico», «Ciclo formativo» y «Módulo profesional: 0xxx - …» | Portada y nombre del archivo |
| Temporalización y distribución de RA y unidades (tabla) | Tabla del apartado 4 |
| Ponderación de cada RA (tabla) | Tabla 4.1 |
| Metodología | 5.1 (párrafos propios) |
| Recursos | 6 Recursos y 7 Espacios (los que empiezan por aula, taller o laboratorio) |
| Evaluación | 9, 11.1 y 11.2: solo lo que difiere de la plantilla, como en el formato actual |

La normativa, los objetivos, las competencias, los RA con sus criterios, los contenidos básicos, el plan de empresa y la
atención a la diversidad son datos oficiales o texto fijo: los pone el catálogo o la plantilla y no se importan. El
formato antiguo no relaciona cada RA con sus competencias: `ra_competencias` queda vacío para que lo complete el
profesor. Como en el formato actual, todo lo importado queda «heredado» hasta que el profesor lo confirma (ADR-008).
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import functools
import re

from programaciones import documento, programacion
from programaciones.catalogo import Catalogo, texto
from programaciones.contenido import Elemento, forma
from programaciones.importar_docx import (
    AYUDA_MODULO,
    RE_ARCHIVO,
    Modulo,
    NoEsProgramacion,
    _entre,
    _parrafo,
    decidir_modulo,
    es_fijo,
    leer_portada,
    leer_tablas,
    plantilla,
)
from programaciones.ooxml import W, es_titulo, normal
from programaciones.ooxml import texto as texto_xml

#: Viñeta escrita a mano al principio del párrafo («• …»), en lugar de una lista de Word
RE_VINETA = re.compile(r"^(\*\*)?[•·▪◦‣–-]\s+")

#: «7.- TEMPORALIZACIÓN …», «7.1 PONDERACIÓN …»: número y título en mayúsculas en un párrafo normal
RE_TITULO = re.compile(r"^(\d{1,2}(?:\.\d{1,2})?)\s*\.?\s*-?\s+(\S.*)$")

#: Apartados del formato antiguo por el principio de su título (sin número: puede cambiar de una programación a otra)
APARTADOS = (("unidades", "temporalizaci"), ("ponderacion", "ponderaci"), ("metodologia", "metodolog"),
             ("recursos", "recursos"), ("evaluacion", "evaluaci"),
             ("actividades", "actividades complementarias"), ("actividades", "actividades extraescolares"))

ESPACIOS = ("aula", "taller", "laboratorio")

AYUDA_NOMBRE = AYUDA_MODULO


def titulo(e: Elemento) -> str | None:
    """El título sin número si el párrafo es un título del formato antiguo; si no, None."""
    if e.tipo != "p" or e.nivel is not None:
        return None
    m = RE_TITULO.match(e.texto)
    if not m or not re.search(r"[A-ZÁÉÍÓÚÑ]{3}", m.group(2)) or m.group(2) != m.group(2).upper():
        return None
    return m.group(2)


def sin_vineta(e: Elemento) -> Elemento:
    """«• texto» escrito a mano pasa a ser una viñeta (nivel 0) con el texto sin el símbolo."""
    if e.tipo != "p" or e.nivel is not None or not RE_VINETA.match(e.texto):
        return e
    return dataclasses.replace(e, texto=RE_VINETA.sub("", e.texto), nivel=0)


@functools.cache
def titulos_plantilla() -> frozenset[str]:
    """Los títulos de la plantilla sin su número («Principios generales y pedagógicos»): en el formato antiguo, alguno
    va como párrafo dentro del apartado y, importado, repetiría el título que ya pone la plantilla."""
    doc = documento.cargar_plantilla().xml("word/document.xml")
    return frozenset(forma(re.sub(r"^\d{1,2}(?:\.\d{1,2})?\.?\s*-?\s*", "", normal(texto_xml(p))))
                     for p in doc.iter(W + "p") if es_titulo(p))


def propio(e: Elemento, seccion: str) -> bool:
    """Párrafo del profesor: ni fijo de la plantilla en ese apartado ni uno de sus títulos."""
    return e.tipo == "p" and not es_fijo(e.texto, seccion) and forma(e.texto) not in titulos_plantilla()


def parrafo(e: Elemento) -> dict:
    """El párrafo del profesor (con sus negritas), sin el «•» escrito a mano."""
    d = _parrafo(e)
    m = RE_VINETA.match(d["texto"])
    if m:
        d["texto"] = (m.group(1) or "") + d["texto"][m.end():]
    return d


def apartados(elementos: list[Elemento]) -> dict[str, list[Elemento]]:
    """Elementos por apartado del formato antiguo («portada» y las claves de APARTADOS; el resto, «otros»)."""
    out: dict[str, list[Elemento]] = {"portada": []}
    actual = "portada"
    for e in elementos:
        t = titulo(e)
        if t is not None:
            actual = next((clave for clave, inicio in APARTADOS if forma(t).startswith(inicio)), "otros")
            out.setdefault(actual, [])
            continue
        out.setdefault(actual, []).append(sin_vineta(e))
    return out


def _al_principio(texto_plantilla: str) -> re.Pattern:
    """Un párrafo de la plantilla como patrón que casa con el principio del párrafo (sus marcas, con cualquier texto):
    en el formato antiguo, un título corto («Visitas y actividades complementarias:») sigue en el mismo párrafo."""
    partes = re.split(r"\{\{[^{}]+\}\}", texto_plantilla)
    return re.compile(".*?".join(re.escape(forma(p)) for p in partes))


def textos_propios(evaluacion: list[Elemento], proyecto: bool) -> dict:
    """Los bloques sustituibles de la plantilla (9, 11.1 y 11.2) que el profesor cambió, buscados en el apartado de
    evaluación del formato antiguo: cada uno empieza tras su párrafo de entrada y acaba en el siguiente párrafo de
    entrada o de salida de cualquier bloque. Si queda igual que el de la plantilla, no se guarda."""
    sustituibles = plantilla()["sustituibles"]
    anclas = [_al_principio(t) for s in sustituibles.values() for t in (s["antes"], s["despues"]) if t]
    ps = [e for e in evaluacion if e.tipo == "p"]
    textos = [forma(e.texto) for e in ps]
    out = {}
    for clave, s in sustituibles.items():
        entrada = _al_principio(s["antes"])
        i = next((k for k, t in enumerate(textos) if entrada.match(t)), None)
        if i is None:
            continue
        j = next((k for k in range(i + 1, len(textos)) if any(a.match(textos[k]) for a in anclas)), len(textos))
        bloque, modelo = ps[i + 1:j], s["bloque"][proyecto]
        iguales = len(bloque) == len(modelo) and all(
            re.fullmatch(_al_principio(p).pattern + r"$", forma(e.texto)) for p, e in zip(modelo, bloque, strict=True))
        if bloque and not iguales:
            out[clave] = [parrafo(e) for e in bloque]
    return out


def es_antigua(elementos: list[Elemento]) -> bool:
    """Tiene los títulos del formato antiguo y su tabla de unidades."""
    sec = apartados(elementos)
    tabla = next((e for e in sec.get("unidades", []) if e.tipo == "tabla"), None)
    return tabla is not None and bool(tabla.filas) and forma(tabla.filas[0][0]).startswith(("unidad", "tarea"))


def _celda(elementos: list[Elemento], inicio: str) -> str:
    for t in (e for e in elementos if e.tipo == "tabla"):
        for fila in t.filas:
            if len(fila) > 1 and forma(fila[0]).startswith(inicio):
                return fila[1]
    return ""


def modulo(portada: list[Elemento], cat: Catalogo, nombre: str, elegido: Modulo | None = None,
           comprobar: bool = True) -> Modulo:
    """Ciclo, curso y código del módulo: el elegido en la columna «Módulos» si lo hay; si no, el del nombre del
    archivo si sigue el patrón y, si no, el de la portada («Módulo profesional: 0961 - …» y, si el código está en
    varios ciclos, «Ciclo formativo»). Si el documento dice otro que el elegido, `ModuloDistinto` (`decidir_modulo`)."""
    m = RE_ARCHIVO.match(nombre)
    del_documento, codigo, motivo = None, None, ""
    if m:
        del_documento, codigo = (m.group(1), int(m.group(2)), m.group(3)), m.group(3)
    else:
        cod = re.search(r"\b(\d{4})\b", _celda(portada, "módulo profesional"))
        codigo = cod.group(1) if cod else None
        candidatos = sorted({(s, f["curso"]) for s in cat.siglas() for f in cat.ciclo(s)["modulos"]
                             if f["codigo"].rstrip("p") == codigo}) if codigo else []
        if len(candidatos) > 1:
            ciclo = forma(_celda(portada, "ciclo formativo"))
            candidatos = [c for c in candidatos if forma(texto(cat.ciclo(c[0]).get("nombre"))) in ciclo] or candidatos
        if len(candidatos) == 1:
            del_documento = (*candidatos[0], codigo)
        elif not codigo:
            motivo = f"La portada no dice el código del módulo: {AYUDA_NOMBRE}"
        elif not candidatos:
            motivo = f"El módulo {codigo} no está en el catálogo: {AYUDA_NOMBRE}"
        else:
            motivo = f"El módulo {codigo} está en varios ciclos o cursos y la portada no dice cuál: {AYUDA_NOMBRE}"
    decidido = decidir_modulo(del_documento, codigo, elegido, comprobar)
    if decidido is None:
        raise NoEsProgramacion(motivo)
    return decidido


def importar(elementos: list[Elemento], cat: Catalogo, nombre: str, elegido: Modulo | None = None,
             comprobar: bool = True) -> dict:
    """Los datos del profesor de una programación del formato antiguo, en el modelo de siempre."""
    sec = apartados(elementos)
    sigla, curso, codigo = modulo(sec["portada"], cat, nombre, elegido, comprobar)
    ficha = cat.ficha(sigla, codigo, curso)
    profesorado, curso_escolar = leer_portada(sec["portada"], cat)
    prog = programacion.nueva(sigla, curso, codigo, curso_escolar, cat.version,
                              documento.metadatos_plantilla()["version"])
    prog["profesorado"] = profesorado

    unidades, ponderacion = sec.get("unidades", []), sec.get("ponderacion", [])
    prog.update(leer_tablas(unidades, ponderacion, ficha.numeros_ra, ficha.horas))
    t4 = next((e for e in unidades if e.tipo == "tabla"), None)
    t41 = next((e for e in ponderacion if e.tipo == "tabla"), None)
    prog["notas_tabla4"] = [parrafo(e) for e in _entre(unidades, t4, True)]
    prog["notas_tabla41"] = [parrafo(e) for e in _entre(ponderacion, t41, True)]

    prog["metodologia"] = [parrafo(e) for e in sec.get("metodologia", []) if propio(e, "5.1")]
    recursos = [e for e in sec.get("recursos", []) if propio(e, "6") and propio(e, "7")]
    prog["espacios"] = [parrafo(e) for e in recursos if forma(e.texto).startswith(ESPACIOS)]
    prog["recursos"] = [parrafo(e) for e in recursos if not forma(e.texto).startswith(ESPACIOS)]
    prog["actividades"] = [parrafo(e) for e in sec.get("actividades", []) if propio(e, "10")]

    # Evaluación: un solo apartado en el formato antiguo; cada bloque sustituible de la plantilla se busca en él
    prog["textos_propios"] = textos_propios(sec.get("evaluacion", []), ficha.tipo == "proyecto")
    prog["bloques"] = {b: "heredado" for b in programacion.BLOQUES}
    prog["historial"] = [{"fecha": dt.datetime.now().isoformat(timespec="minutes"),
                          "accion": f"importada de {nombre} (formato antiguo)"}]
    return programacion.validar(prog)
