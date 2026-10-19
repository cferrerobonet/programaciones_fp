"""Importar la programación de un ámbito de Grado Básico sin datos de la app (ADR-040).

Los ámbitos (ADR-032) no llevan las tablas 4 y 4.1: en el apartado 3 hay una tabla por parte del ámbito, precedida de
«Para Matemáticas II (99 h) es la siguiente:», con «Elementos de trabajo · Unidades de trabajo · Competencias
específicas (CE) · Horas · Trimestre»; en el 3.1, la ponderación de cada CE por parte. Vale para el modelo del
departamento (3164) y para un ámbito exportado con la app que ha perdido sus datos.

- **Módulo:** el elegido en la columna «Módulos»; si no, el nombre del archivo (si la sigla es un ciclo) o la portada
  (filas «Código» o «Ámbito» y, si el código está en varios ciclos, «Ciclo formativo»), como en el formato antiguo.
- **Partes, unidades y elementos:** de cada tabla del 3, una fila por unidad con su propio elemento (tipo por el
  nombre: examen, práctica o tarea) y sus CE en `ra`. La parte, del párrafo «Para … (N h)» que precede a la tabla.
- **El 3.1 no se importa:** la app lo calcula de la tabla 3 (`calculos.ponderacion_parte`). Los párrafos propios del 3.1
  van a sus notas.
- **Párrafos del profesor:** los que no son de la plantilla de ámbitos en 3 (antes de las tablas: contenidos; después:
  notas), 4 o 4.1 (metodología), 5 (recursos), 6 (espacios) y 9 (actividades). La plantilla de ámbitos no tiene bloques
  sustituibles en la evaluación (8, 10 y 11): esos apartados no se importan.

Todo queda «heredado» hasta que el profesor lo confirma (ADR-008).
"""
from __future__ import annotations

import datetime as dt
import difflib
import functools
import re

from programaciones import contenido, documento, programacion
from programaciones.catalogo import Catalogo
from programaciones.contenido import Elemento, forma
from programaciones.importar_antigua import modulo as modulo_portada
from programaciones.importar_antigua import parrafo, titulos_plantilla
from programaciones.importar_docx import Modulo, _patron, _tipo, _trimestre, leer_portada

RE_PARTE = re.compile(r"^Para\s+(.+?)\s*\((\d+)\s*h", re.I)
RE_CE = re.compile(r"CE\s*(\d{1,2})")
#: Apartado de la plantilla de ámbitos de cada bloque de párrafos (la metodología del modelo va en el 4)
APARTADOS = {"metodologia": ("4", "4.1"), "recursos": ("5",), "espacios": ("6",), "actividades": ("9",)}


@functools.cache
def _secciones_plantilla() -> dict[str, list[Elemento]]:
    return contenido.secciones(contenido.leer(documento.cargar_plantilla("es", ambito=True).a_bytes()))


#: Un párrafo casi igual a uno fijo de la plantilla es ese párrafo: el modelo del departamento, del que sale la plantilla
#: de ámbitos, cambia alguna palabra («las 166 h totales del módulo» por «… del ámbito») y, importado, saldría dos veces
PARECIDO = 0.95


def es_fijo(texto: str, seccion: str) -> bool:
    """El párrafo es uno de los fijos de la plantilla de ámbitos en ese apartado (con sus marcas rellenas) o casi igual
    a uno de ellos (`PARECIDO`, sin contar las marcas)."""
    clave = forma(texto)
    fijos = [e.texto for e in _secciones_plantilla().get(seccion, []) if e.tipo == "p" and not e.texto.startswith("{{")]
    if any(_patron(t).match(clave) for t in fijos):
        return True
    def limpio(s: str) -> str:   # sin cifras ni marcas, que cambian de un documento a otro
        return re.sub(r"\s+", " ", re.sub(r"\d+|\{\{[^{}]+\}\}", "", s)).strip()

    a = limpio(clave)
    return any(difflib.SequenceMatcher(None, a, limpio(forma(t))).ratio() >= PARECIDO for t in fijos)


def propio(e: Elemento, seccion: str) -> bool:
    return e.tipo == "p" and not es_fijo(e.texto, seccion) and forma(e.texto) not in titulos_plantilla() \
        and not RE_PARTE.match(e.texto)


def _es_tabla_ce(e: Elemento) -> bool:
    return e.tipo == "tabla" and bool(e.filas) and any("competencias específicas" in forma(c) for c in e.filas[0])


def es_ambito(sec: dict[str, list[Elemento]]) -> bool:
    """Tiene, en el apartado 3, la tabla de unidades de un ámbito (con la columna de competencias específicas)."""
    return any(_es_tabla_ce(e) for e in sec.get("3", []))


def _columnas(cabecera: list[str]) -> dict[str, int]:
    out = {}
    for i, c in enumerate(cabecera):
        f = forma(c)
        clave = ("elemento" if f.startswith("elemento") else "unidad" if f.startswith("unidad") else
                 "ce" if "competencias" in f else "horas" if f.startswith(("horas", "sesiones")) else
                 "trimestre" if f.startswith("trim") else None)
        if clave and clave not in out:
            out[clave] = i
    return out


def leer_partes(sec3: list[Elemento], nombre_ambito: str) -> dict:
    """Partes, unidades y elementos de las tablas del apartado 3."""
    partes, unidades, elementos = [], [], []
    parte_pendiente = None
    for e in sec3:
        if e.tipo == "p":
            m = RE_PARTE.match(e.texto)
            if m:
                parte_pendiente = (m.group(1).strip(), int(m.group(2)))
            continue
        if not _es_tabla_ce(e):
            continue
        col = _columnas(e.filas[0])
        pid = f"p{len(partes) + 1}"
        suma = 0
        for fila in e.filas[1:]:
            def cel(clave, fila=fila, col=col):
                return fila[col[clave]].strip() if clave in col and col[clave] < len(fila) else ""

            if forma(fila[0]).startswith("total") or not any(c.strip() for c in fila):
                continue
            horas = int(re.sub(r"\D", "", cel("horas")) or 0)
            eid = f"e{len(elementos) + 1}"
            nombre_el = cel("elemento") or cel("unidad")
            elementos.append({"id": eid, "tipo": _tipo(nombre_el), "nombre": nombre_el,
                              "ra": sorted({int(x) for x in RE_CE.findall(cel("ce"))})})
            unidades.append({"id": f"u{len(unidades) + 1}", "titulo": cel("unidad") or nombre_el, "horas": horas,
                             "trimestre": _trimestre(cel("trimestre")) or 1, "elemento": eid, "parte": pid})
            suma += horas
        nombre, horas_parte = parte_pendiente or (nombre_ambito, suma)
        partes.append({"id": pid, "nombre": nombre, "horas": horas_parte})
        parte_pendiente = None
    return {"partes": partes, "unidades": unidades, "elementos": elementos}


def importar(elementos: list[Elemento], cat: Catalogo, nombre: str, elegido: Modulo | None = None,
             comprobar: bool = True) -> dict:
    """Los datos del profesor de la programación de un ámbito, en el modelo de siempre."""
    sec = contenido.secciones(elementos)
    sigla, curso, codigo = modulo_portada(sec.get("portada", []), cat, nombre, elegido, comprobar,
                                          filas=("código", "ámbito", "módulo"))
    ficha = cat.ficha(sigla, codigo, curso)
    profesorado, curso_escolar = leer_portada(sec.get("portada", []), cat)
    prog = programacion.nueva(sigla, curso, codigo, curso_escolar, cat.version,
                              documento.metadatos_plantilla()["version"])
    prog["profesorado"] = profesorado
    prog.update(leer_partes(sec.get("3", []), ficha.nombre))

    s3 = sec.get("3", [])
    tablas = [i for i, e in enumerate(s3) if _es_tabla_ce(e)]
    prog["contenidos"] = [parrafo(e) for e in s3[:tablas[0]] if propio(e, "3")]
    prog["notas_tabla4"] = [parrafo(e) for e in s3[tablas[-1] + 1:] if propio(e, "3")]
    prog["notas_tabla41"] = [parrafo(e) for e in sec.get("3.1", []) if propio(e, "3.1")]
    for clave, apartados in APARTADOS.items():
        prog[clave] = [parrafo(e) for a in apartados for e in sec.get(a, []) if propio(e, apartados[-1])]

    prog["bloques"] = {b: "heredado" for b in programacion.BLOQUES}
    prog["historial"] = [{"fecha": dt.datetime.now().isoformat(timespec="minutes"),
                          "accion": f"importada de {nombre} (ámbito)"}]
    return programacion.validar(prog)
