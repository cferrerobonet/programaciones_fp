"""Importar una programación .docx (RF-08 y RF-10).

- Si el .docx lo exportó la app, lleva los datos dentro (incrustar.py): se recuperan tal cual.
- Si no, se leen una vez sus bloques del profesor a partir de la estructura de la plantilla: profesorado, tabla 3
  (competencias de cada RA), tablas 4 y 4.1 (unidades, elementos, horas de empresa y reparto de centro por RA),
  y los párrafos propios de los apartados 4, 5.1, 6, 7 y 10. Lo que difiere de un bloque fijo de la plantilla en 9,
  11.1 y 11.2 se guarda como texto propio (`textos_propios`). Los bloques importados quedan «heredados»: el profesor
  los confirma antes de la definitiva (ADR-008).

`leer_curso` saca de una programación las fechas del curso escolar (apartados 9 y 9.1). Solo la usa la prueba de
regeneración: cada referencia se rehace con sus propias fechas, no con las de `catalogo/cursos/`.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from programaciones import calculos, contenido, documento, incrustar, programacion
from programaciones.catalogo import Catalogo
from programaciones.contenido import Elemento, forma
from programaciones.documento import MESES
from programaciones.ooxml import W, normal

RE_ARCHIVO = re.compile(r"^([A-Z]{2,3}) ([12]) - (\d{4}) - ")
RE_RA = re.compile(r"^R\.?\s?A\.?\s?(\d{1,2})\.?\s*[-.:]?\s*")


class NoEsProgramacion(ValueError):
    """El documento no tiene la estructura de una programación de la plantilla."""


# ---------------------------------------------------------------------------------------------------------------------
# La plantilla como referencia de lo que es fijo
# ---------------------------------------------------------------------------------------------------------------------
_PLANTILLA: dict | None = None


def plantilla() -> dict:
    """Texto de la plantilla por apartados, con las marcas, y sus bloques sustituibles."""
    global _PLANTILLA
    if _PLANTILLA is None:
        pq = documento.cargar_plantilla()
        els = contenido.leer(pq.a_bytes())
        sec = contenido.secciones(els)
        sustituibles = {}
        for nombre, ps in sec.items():
            textos = [e.texto for e in ps if e.tipo == "p"]
            for i, t in enumerate(textos):
                m = re.fullmatch(r"\{\{\?sustituible:(\w+)\}\}", t)
                if m:
                    fin = textos.index("{{/%s}}" % m.group(1), i)
                    sustituibles[m.group(1)] = {"seccion": nombre, "antes": textos[i - 1],
                                                "despues": textos[fin + 1] if fin + 1 < len(textos) else None,
                                                "bloque": _variantes(textos[i + 1:fin])}
        _PLANTILLA = {"secciones": sec, "sustituibles": sustituibles}
    return _PLANTILLA


def _variantes(bloque: list[str]) -> dict[bool, list[str]]:
    """El bloque de la plantilla para un módulo que no es proyecto (False) y para un proyecto (True)."""
    out: dict[bool, list[str]] = {False: [], True: []}
    actual = None
    for t in bloque:
        m = re.fullmatch(r"\{\{([?/])(no_proyecto|proyecto)\}\}", t)
        if m:
            actual = (m.group(2) == "proyecto") if m.group(1) == "?" else None
            continue
        for k in ((actual,) if actual is not None else (False, True)):
            out[k].append(t)
    return out


def _patron(texto_plantilla: str) -> re.Pattern:
    """Un párrafo de la plantilla como patrón: cada marca casa con cualquier texto."""
    partes = re.split(r"\{\{[^{}]+\}\}", texto_plantilla)
    return re.compile(".*?".join(re.escape(forma(p)) for p in partes) + r"$")


def es_fijo(texto: str, seccion: str) -> bool:
    """El párrafo es uno de los fijos de la plantilla en ese apartado (con sus marcas rellenas)."""
    clave = forma(texto)
    return any(e.tipo == "p" and not e.texto.startswith("{{") and _patron(e.texto).match(clave)
               for e in plantilla()["secciones"].get(seccion, []))


# ---------------------------------------------------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------------------------------------------------
def _negrita(r) -> bool:
    b = r.find(f"{W}rPr/{W}b")
    return b is not None and b.get(W + "val") not in ("0", "false")


def texto_con_negritas(p) -> str:
    """Texto del párrafo con «**…**» en lo que va en negrita (así se conserva en los párrafos del profesor)."""
    trozos: list[list] = []
    for r in p.iter(W + "r"):
        t = "".join(x.text or "" if x.tag == W + "t" else " " for x in r if x.tag in (W + "t", W + "tab"))
        if not t:
            continue
        b = _negrita(r)
        if trozos and trozos[-1][1] == b:
            trozos[-1][0] += t
        else:
            trozos.append([t, b])
    out = ""
    for t, b in trozos:
        if b and t.strip():
            izq, der = t[:len(t) - len(t.lstrip())], t[len(t.rstrip()):]
            out += f"{izq}**{t.strip()}**{der}"
        else:
            out += t
    return normal(out.replace("****", ""))


def _parrafo(e: Elemento) -> dict:
    d = {"texto": texto_con_negritas(e.xml) if e.xml is not None else e.texto}
    if e.nivel is not None:
        d["nivel"] = min(e.nivel, 2)
    return d


def _ras(texto: str) -> list[int]:
    t = texto.replace("→", "->")
    out = set()
    for a, b in re.findall(r"RA\s*(\d+)\s*->\s*RA\s*(\d+)", t):
        out.update(range(int(a), int(b) + 1))
    out.update(int(x) for x in re.findall(r"RA\s*(\d+)", t))
    return sorted(out)


def _trimestre(t: str):
    ns = [int(x) for x in re.findall(r"[1-3]", t)]
    if not ns:
        return None
    return ns[0] if len(ns) == 1 else sorted(set(ns))


def _tipo(nombre: str) -> str:
    n = forma(nombre)
    if n.startswith("examen"):
        return "E"
    if n.startswith("práctica") or n.startswith("practica"):
        return "P"
    return "T"


def _tabla(sec: list[Elemento], cabecera: str) -> tuple[Elemento | None, int]:
    for i, e in enumerate(sec):
        if e.tipo == "tabla" and e.filas and forma(e.filas[0][0]).startswith(cabecera):
            return e, i
    return None, -1


def _columnas(cab: list[str]) -> dict[str, int]:
    out = {}
    for i, c in enumerate(cab):
        for nombre, rx in contenido.COLUMNAS:
            if re.match(rx, forma(c)) and nombre not in out:
                out[nombre] = i
                break
    return out


def leer_tablas(sec4: list[Elemento], sec41: list[Elemento], ras: list[int], horas: int = 0) -> dict:
    t4, _i = _tabla(sec4, "unidad")
    if t4 is None:
        t4, _i = _tabla(sec4, "tarea")
    if t4 is None:
        raise NoEsProgramacion("sin la tabla del apartado 4")
    col = _columnas(t4.filas[0])
    unidades, elementos = [], []
    elemento_actual, trim_actual = None, None
    for k, (fila, pfila) in enumerate(zip(t4.filas[1:], t4.parrafos[1:], strict=True)):
        primero = forma(fila[0])
        if primero.startswith(("horas centro", "horas de empresa", "total")):
            continue
        def cel(nombre, fila=fila):
            return fila[col[nombre]] if nombre in col and col[nombre] < len(fila) else ""

        def pcel(nombre, pfila=pfila):
            return pfila[col[nombre]] if nombre in col and col[nombre] < len(pfila) else []

        tr = t4.xml.findall(contenido.W + "tr")[k + 1]
        tcs = contenido.celdas(tr)
        # elemento: celda combinada con la de arriba (o vacía) = el mismo
        idx_el = col.get("elemento")
        continua = False
        if idx_el is not None and idx_el < len(tcs):
            pr = tcs[idx_el].find(contenido.W + "tcPr")
            vm = pr.find(contenido.W + "vMerge") if pr is not None else None
            continua = (vm is not None and vm.get(contenido.W + "val") != "restart") or not normal(
                contenido.texto(tcs[idx_el]))
        if continua and elemento_actual is not None:
            el = elemento_actual
        else:
            ps = pcel("elemento") or [""]
            el = {"id": f"e{len(elementos) + 1}", "tipo": _tipo(ps[0]), "nombre": ps[0], "ra": _ras(cel("ra")),
                  "detalle": ps[1:], "_peso": cel("peso")}
            elementos.append(el)
            elemento_actual = el
        t = _trimestre(cel("trimestre"))
        trim_actual = t if t is not None else trim_actual
        ps = pcel("unidad") or [""]
        u = {"id": f"u{len(unidades) + 1}", "titulo": ps[0], "horas": int(re.sub(r"\D", "", cel("horas")) or 0),
             "trimestre": trim_actual, "elemento": el["id"]}
        if ps[1:]:
            u["descripcion"] = ps[1:]
        unidades.append(u)
    prog = {"unidades": unidades, "elementos": elementos}
    h = calculos.horas_elementos(prog)
    for el in elementos:   # el detalle por defecto es «(Nh)»: no se guarda
        if not el["detalle"] or forma(" ".join(el["detalle"])) == forma(f"({h[el['id']]}h)"):
            el.pop("detalle")
        # peso: si no es el calculado, ajuste del profesor (CarlosFB, 2026-10-17)
        escrito = el.pop("_peso").strip()
        calculado = calculos.peso(h[el["id"]], horas)
        if horas and escrito and forma(escrito) != forma(calculos.formato_peso(calculado)):
            m = re.fullmatch(r"(\d+(?:,\d+)?)\s*%", escrito)
            el["peso_ajustado"] = {"valor": float(m.group(1).replace(",", "."))} if m else \
                {"valor": float(calculado), "texto": escrito}
    # 4.1: horas de cada RA. Formato de PIICT: totales y empresa; desde la 0.2.0 (ADR-025): centro y empresa, con «-»
    # en lugar de 0
    t41, _i = _tabla(sec41, "resultado de aprendizaje")
    empresa, totales, modalidad = {}, {}, {}
    numero = lambda celda: int(re.sub(r"\D", "", celda) or 0)  # noqa: E731
    if t41 is not None:
        c41 = _columnas(t41.filas[0])
        if "pct" in c41:
            prog["columna_pct_curso"] = True
        for fila in t41.filas[1:]:
            m = RE_RA.match(fila[0])
            if not m:
                continue
            r = int(m.group(1))
            if "centro" in c41:
                totales[r] = numero(fila[c41["centro"]]) + (numero(fila[c41["empresa"]]) if "empresa" in c41 else 0)
            else:
                totales[r] = numero(fila[c41["total"]]) if "total" in c41 else 0
            if "empresa" in c41:
                v = re.sub(r"\D", "", fila[c41["empresa"]])
                if v and int(v):
                    empresa[str(r)] = int(v)
            if "modalidad" in c41:   # ADR-030: la que escribió el profesor
                m41 = next((x for x in calculos.MODALIDADES if forma(fila[c41["modalidad"]]) == forma(x)), "")
                if m41:
                    modalidad[str(r)] = m41
    for k, m41 in modalidad.items():   # un Mixto o un Empresa sin horas de empresa también va a empresa
        if m41 != "Centro":
            empresa.setdefault(k, 0)
    prog["empresa"] = empresa
    if modalidad:
        prog["modalidad"] = modalidad
    prop = calculos.propuesta_centro(prog, ras)
    ajuste = {}
    for r in ras:
        c = totales.get(r, 0) - int(empresa.get(str(r), 0))
        if r in totales and c != prop.get(r):
            ajuste[str(r)] = c
    prog["centro_ajustado"] = ajuste
    return prog


def _entre(sec: list[Elemento], tabla: Elemento | None, despues: bool) -> list[Elemento]:
    if tabla is None:
        return []
    i = sec.index(tabla)
    return [e for e in (sec[i + 1:] if despues else sec[:i]) if e.tipo == "p"]


def leer_textos_propios(sec: dict[str, list[Elemento]], proyecto: bool = False) -> dict:
    out = {}
    for clave, s in plantilla()["sustituibles"].items():
        modelo = s["bloque"][proyecto]
        ps = [e for e in sec.get(s["seccion"], []) if e.tipo == "p"]
        textos = [forma(e.texto) for e in ps]
        try:
            i = next(k for k, t in enumerate(textos) if _patron(s["antes"]).match(t))
            j = len(textos) if s["despues"] is None else next(
                k for k in range(i + 1, len(textos)) if _patron(s["despues"]).match(textos[k]))
        except StopIteration:
            continue
        bloque = ps[i + 1:j]
        iguales = len(bloque) == len(modelo) and all(
            _patron(p).match(forma(e.texto)) for p, e in zip(modelo, bloque, strict=True))
        if not iguales:
            out[clave] = [_parrafo(e) for e in bloque]
    return out


def importar(origen, cat: Catalogo, nombre_archivo: str | None = None) -> dict:
    """Los datos del profesor de una programación .docx (los incrustados si los lleva)."""
    datos = Path(origen).read_bytes() if isinstance(origen, (str, Path)) else origen
    incrustada = incrustar.leer(datos)
    if incrustada is not None:
        return incrustada.programacion
    nombre = nombre_archivo or (Path(origen).name if isinstance(origen, (str, Path)) else "")
    m = RE_ARCHIVO.match(nombre)
    if not m:
        raise NoEsProgramacion(f"«{nombre}» no sigue el patrón «SIGLA N - 0xxx - Nombre»")
    sigla, curso, codigo = m.group(1), int(m.group(2)), m.group(3)
    ficha = cat.ficha(sigla, codigo, curso)
    sec = contenido.secciones(contenido.leer(datos))
    if not {"1", "4", "11"} <= set(sec):
        raise NoEsProgramacion("sin los apartados de la plantilla")

    # Portada: profesorado y curso
    tablas_portada = [e for e in sec.get("portada", []) if e.tipo == "tabla"]
    profesorado, curso_escolar = [], ""
    for t in tablas_portada:
        for fila, pfila in zip(t.filas, t.parrafos, strict=True):
            if forma(fila[0]).startswith("profesor"):
                profesorado = pfila[1]
            if forma(fila[0]).startswith("curso académico"):
                curso_escolar = fila[1]
    if not re.fullmatch(r"\d{4}-\d{4}", curso_escolar):
        # sin curso en la portada: el último curso escolar que tiene el catálogo (su resolución de instrucciones)
        curso_escolar = max((n.curso_escolar for n in cat.normas.values() if n.curso_escolar), default="")
    prog = programacion.nueva(sigla, curso, codigo, curso_escolar, cat.version, documento.metadatos_plantilla()["version"])
    prog["profesorado"] = profesorado

    # 3: competencias de cada RA
    t3, _i = _tabla(sec.get("3", []), "resultado de aprendizaje")
    if t3 is not None:
        for fila in t3.filas[1:]:
            mm = RE_RA.match(fila[0])
            if mm:
                prog["ra_competencias"][mm.group(1)] = re.findall(r"([a-zñ])\)", fila[-1])

    # 4 y 4.1
    s4, s41 = sec.get("4", []), sec.get("4.1", [])
    prog.update(leer_tablas(s4, s41, ficha.numeros_ra, ficha.horas))
    t4 = next((e for e in s4 if e.tipo == "tabla"), None)
    prog["contenidos"] = [_parrafo(e) for e in _entre(s4, t4, False) if not es_fijo(e.texto, "4")]
    prog["notas_tabla4"] = [_parrafo(e) for e in _entre(s4, t4, True)]
    t41 = next((e for e in s41 if e.tipo == "tabla"), None)
    prog["notas_tabla41"] = [_parrafo(e) for e in _entre(s41, t41, True)]

    # 5.1: lo propio antes y después de los párrafos comunes del medio
    fijos51 = [e.texto for e in plantilla()["secciones"]["5.1"] if e.tipo == "p" and not e.texto.startswith("{{")]
    primero_medio = forma(fijos51[3]) if len(fijos51) > 3 else ""
    antes, despues, medio_visto = [], [], False
    for e in sec.get("5.1", []):
        if e.tipo != "p":
            continue
        if forma(e.texto) == primero_medio:
            medio_visto = True
        if es_fijo(e.texto, "5.1"):
            continue
        (despues if medio_visto else antes).append(_parrafo(e))
    prog["metodologia"], prog["metodologia_final"] = antes, despues

    # 6, 7 y 10: lo que no es de la plantilla
    for seccion, clave in (("6", "recursos"), ("7", "espacios"), ("10", "actividades")):
        prog[clave] = [_parrafo(e) for e in sec.get(seccion, []) if e.tipo == "p" and not es_fijo(e.texto, seccion)]

    prog["textos_propios"] = leer_textos_propios(sec, ficha.tipo == "proyecto")
    prog["bloques"] = {b: "heredado" for b in programacion.BLOQUES}
    prog["historial"] = [{"fecha": dt.datetime.now().isoformat(timespec="minutes"), "accion": f"importada de {nombre}"}]
    return programacion.validar(prog)


# ---------------------------------------------------------------------------------------------------------------------
# Fechas del curso escolar que trae una programación (solo para la prueba de regeneración)
# ---------------------------------------------------------------------------------------------------------------------
RE_FECHA_LARGA = r"(\d{1,2}) de (" + "|".join(MESES) + r")"


def _dia(texto_dia: str, anio: int) -> dt.date:
    d, mes = re.match(RE_FECHA_LARGA, texto_dia).groups()
    return dt.date(anio, MESES.index(mes) + 1, int(d))


def leer_curso(origen, grado: str, curso: int) -> dict:
    sec = contenido.secciones(contenido.leer(origen))
    ev, ordinaria, extra = {}, None, None
    for e in sec.get("9", []):
        m = re.match(r"^(Evaluación inicial|1ª evaluación|2ª evaluación|3ª evaluación):\s*(\d{2})/(\d{2})/(\d{4})", e.texto)
        if m:
            clave = {"Evaluación inicial": "inicial", "1ª evaluación": "primera", "2ª evaluación": "segunda",
                     "3ª evaluación": "tercera"}[m.group(1)]
            ev[clave] = dt.date(int(m.group(4)), int(m.group(3)), int(m.group(2))).isoformat()
        m = re.search(r"convocatoria ordinaria se realizará del " + RE_FECHA_LARGA + r"(?: de (\d{4}))? al "
                      + RE_FECHA_LARGA + r" de (\d{4}).*?comenzará el " + RE_FECHA_LARGA + r" de (\d{4})", e.texto)
        if m:
            fin = int(m.group(6))
            ini = int(m.group(3)) if m.group(3) else fin
            ordinaria = {"desde": dt.date(ini, MESES.index(m.group(2)) + 1, int(m.group(1))).isoformat(),
                         "hasta": dt.date(fin, MESES.index(m.group(5)) + 1, int(m.group(4))).isoformat()}
            extra = dt.date(int(m.group(9)), MESES.index(m.group(8)) + 1, int(m.group(7))).isoformat()
        # Ordinaria de un solo día (2026-2027): «se realizará el 8 de junio de 2027»
        m = re.search(r"convocatoria ordinaria se realizará el " + RE_FECHA_LARGA + r" de (\d{4}).*?comenzará el "
                      + RE_FECHA_LARGA + r" de (\d{4})", e.texto)
        if m:
            dia = dt.date(int(m.group(3)), MESES.index(m.group(2)) + 1, int(m.group(1))).isoformat()
            ordinaria = {"desde": dia, "hasta": dia}
            extra = dt.date(int(m.group(6)), MESES.index(m.group(5)) + 1, int(m.group(4))).isoformat()
    periodos = []
    for e in sec.get("9.1", []):
        m = re.search(r"(\d+)\s*h/día \((?:en total )?(\d+) días de formación[^)]*\):\s*(?:desde el|del) "
                      + RE_FECHA_LARGA + r"(?: de (\d{4}))? al " + RE_FECHA_LARGA + r" de (\d{4})", e.texto)
        if m:
            fin = int(m.group(8))
            hasta = dt.date(fin, MESES.index(m.group(7)) + 1, int(m.group(6)))
            ini = int(m.group(5)) if m.group(5) else fin
            desde = dt.date(ini, MESES.index(m.group(4)) + 1, int(m.group(3)))
            if desde > hasta:
                desde = desde.replace(year=ini - 1)
            periodos.append({"jornada": int(m.group(1)), "dias": int(m.group(2)), "desde": desde.isoformat(),
                             "hasta": hasta.isoformat()})
    return {"evaluaciones": ev, "ordinaria": ordinaria, "extraordinaria_desde": extra,
            "formacion_empresa": {grado: {curso: periodos}}}
