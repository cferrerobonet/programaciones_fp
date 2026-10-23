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

#: «SIGLA N - código - Nombre del módulo.docx». El código puede ser cualquiera de los del módulo: «0517», «1665031» o
#: «1665», «CV0015», el de la casilla de un optativo («CVOPS031») o «ANEXO X-I» (ADR-043)
RE_ARCHIVO = re.compile(r"^([A-Z]{2,3}) ([12]) - (.+?) - (.+?)(?:\.(?:docx|programacion|pdf|xlsx))?$", re.I)
RE_RA = re.compile(r"^R\.?\s?A\.?\s?(\d{1,2})\.?\s*[-.:]?\s*")


class NoEsProgramacion(ValueError):
    """El documento no tiene la estructura de una programación de la plantilla."""


AYUDA_MODULO = ("elige antes su módulo en la columna «Módulos» o renombra el archivo como «SIGLA N - 0xxx - Nombre "
                "del módulo.docx»")

#: Un módulo: (ciclo, curso, código), como («ARI», 1, «0961»)
Modulo = tuple[str, int, str]


class ModuloDistinto(Exception):
    """El documento dice que es de un módulo y en la columna «Módulos» hay otro elegido: la interfaz pregunta cuál.
    `documento` puede llevar solo el código (sin ciclo ni curso) si la portada no dice de qué ciclo es."""

    def __init__(self, documento: tuple[str | None, int | None, str], elegido: Modulo):
        def nombre(m):
            return f"{m[2]} de {m[0]} {m[1]}.º" if m[0] is not None else m[2]
        super().__init__(f"El documento es del módulo {nombre(documento)} y está elegido el {nombre(elegido)}")
        self.documento = documento
        self.elegido = elegido


def decidir_modulo(del_documento: Modulo | None, codigo_documento: str | None, elegido: Modulo | None,
                   comprobar: bool = True, cat: Catalogo | None = None) -> Modulo | None:
    """El módulo en el que se importa: el elegido en la columna «Módulos» si lo hay; si no, el que dice el documento
    (por el nombre del archivo o, en el formato antiguo, por la portada). Si el documento dice otro módulo que el
    elegido, `ModuloDistinto` (salvo con `comprobar=False`, cuando el profesor ya ha dicho que usa el elegido)."""
    if elegido is None:
        return del_documento
    if comprobar:
        if del_documento is not None and tuple(del_documento) != tuple(elegido):
            raise ModuloDistinto(del_documento, elegido)
        if del_documento is None and codigo_documento and codigo_documento != elegido[2] and not (
                cat is not None and cat.resolver(elegido[0], codigo_documento, elegido[1]) == elegido[2]):
            raise ModuloDistinto((None, None, codigo_documento), elegido)
    return tuple(elegido)


# ---------------------------------------------------------------------------------------------------------------------
# La plantilla como referencia de lo que es fijo
# ---------------------------------------------------------------------------------------------------------------------
_PLANTILLA: dict | None = None


def modulo_del_nombre(nombre: str, cat: Catalogo) -> Modulo | None:
    """«SIGLA N - código - Nombre» → (ciclo, curso, clave del módulo), solo si la sigla es un ciclo del catálogo. El
    código puede ser cualquiera de los del módulo y se pasa a su clave: «1665» de SEA es el «1665031»; el de la casilla
    de un optativo lo decide el nombre (`Catalogo.resolver`, ADR-043). En el formato antiguo de Grado Básico el
    archivo lleva la sigla del módulo («TID 1 - 3001 - …»): no dice el ciclo y no vale.
    Lanza `NoEsProgramacion` si el ciclo existe pero el código no es de un módulo suyo."""
    m = RE_ARCHIVO.match(Path(nombre).name)
    if not m or m.group(1) not in cat.siglas():
        return None
    sigla, curso, codigo, resto = m.group(1), int(m.group(2)), m.group(3).strip(), m.group(4)
    clave = cat.resolver(sigla, codigo, curso, resto)
    if clave is None:
        raise NoEsProgramacion(f"«{Path(nombre).name}»: {codigo} no es un módulo de {sigla} {curso}.º; {AYUDA_MODULO}")
    return sigla, curso, clave


RE_HORAS_PEGADAS = re.compile(r"\s*\(\d+\s*h\)\.?\s*$")


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


_APARTADOS: dict[str, str] | None = None


def apartados_plantilla() -> dict[str, str]:
    """Número de cada título de la plantilla por su texto sin número: {«principios generales y pedagógicos»: «5.1»}.
    En Word se borra a veces el número de un subtítulo y, sin él, sus párrafos no caían en su apartado."""
    global _APARTADOS
    if _APARTADOS is None:
        _APARTADOS = {}
        for t in contenido.titulos(documento.cargar_plantilla().a_bytes()):
            m = contenido.RE_APARTADO.match(t)
            if m:
                _APARTADOS.setdefault(forma(re.sub(r"^\d{1,2}(?:\.\d{1,2})?\.?\s*-?\s*", "", t)), m.group(1))
    return _APARTADOS


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


#: Una lista de RA escrita a mano: «RA1», «RA 2 y 5», «RA2, 5, y 6», «RA 1y 2», «R.A 4», «R1, 2 y 5» (sin la «A»), y
#: los intervalos «RA2 → RA6», «RA2 -> 6», «RA2 a RA6» o «RA2-RA6». Los números que siguen al primero son RA aunque no
#: repitan el «RA».
_RA = r"R\.?\s?A?\.?\s?"
_SIGUE = r"\s*(?:,\s*(?:y(?![^\W\d_])\s*)?|;|/|&|y(?![^\W\d_])|→|->|a(?![^\W\d_]))\s*(?:" + _RA + r")?\d{1,2}\b"
_HASTA = r"\s*[-–]\s*" + _RA + r"\d{1,2}\b"
RE_LISTA_RA = re.compile(r"\b" + _RA + r"\d{1,2}(?:" + _SIGUE + "|" + _HASTA + ")*", re.I)
RE_INTERVALO_RA = re.compile(r"(\d{1,2})\s*(?:→|->|a(?![^\W\d_])|[-–](?=\s*R))\s*(?:" + _RA + r")?(\d{1,2})", re.I)


def _ras(texto: str) -> list[int]:
    out = set()
    for m in RE_LISTA_RA.finditer(texto):
        lista = m.group(0)
        for a, b in RE_INTERVALO_RA.findall(lista):
            out.update(range(int(a), int(b) + 1))
        out.update(int(x) for x in re.findall(r"\d{1,2}", lista))
    return sorted(out)


def _trimestre(t: str):
    ns = [int(x) for x in re.findall(r"[1-3]", t)]
    if not ns:
        return None
    return ns[0] if len(ns) == 1 else sorted(set(ns))


def _tipo(nombre: str) -> str:
    """E, P o T por el nombre del elemento; también abreviado a mano: «Exám. 3», «Prác.6», «PR 3», «PR-MC1»."""
    n = forma(nombre)
    if n.startswith("examen") or re.match(r"ex[aá]m\b", n):
        return "E"
    if n.startswith("práctica") or n.startswith("practica") or re.match(r"pr(?:[aá]c\b|\b|(?=\d))", n):
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
        t4, _i = _tabla(sec4, "elemento")
    if t4 is None:
        raise NoEsProgramacion("sin la tabla del apartado 4")
    # Formato antiguo de Grado Básico: una fila por elemento de trabajo («EXAMEN UT1», «TAREAS UT1»), sin columna de
    # unidad: su título va como segundo párrafo de la celda del examen, con las horas pegadas («UT1. Equipos… (35h)»)
    por_elementos = forma(t4.filas[0][0]).startswith("elemento")
    col = _columnas(t4.filas[0])
    if "ra" not in col:   # «Resultados de Aprendizaje» en lugar de «RA asociados»
        i_ra = next((i for i, c in enumerate(t4.filas[0]) if re.match(r"resultados? de aprendizaje", forma(c))), None)
        if i_ra is not None:
            col["ra"] = i_ra
    unidades, elementos = [], []
    elemento_actual, trim_actual = None, None
    for k, (fila, pfila) in enumerate(zip(t4.filas[1:], t4.parrafos[1:], strict=True)):
        primero = forma(fila[0])
        if primero.startswith(("horas centro", "horas de empresa", "total")) or not any(c.strip() for c in fila):
            continue   # filas de totales y filas vacías
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
            # una celda vacía sin combinar con su propio peso o sus propios RA es otro elemento (sin nombre), no el de
            # arriba: si no, su peso se perdía y los pesos no sumaban (2026-10-23)
            if continua and vm is None and elemento_actual is not None and (
                    (cel("peso").strip() and forma(cel("peso")) != forma(elemento_actual["_peso"]))
                    or (cel("ra").strip() and _ras(cel("ra")) != elemento_actual["ra"])):
                continua = False
        ps_elemento = pcel("elemento") or [""]
        if por_elementos:
            ps_unidad = [RE_HORAS_PEGADAS.sub("", ps_elemento[1])] if len(ps_elemento) > 1 else [ps_elemento[0]]
            ps_elemento = ps_elemento[:1]
        else:
            ps_unidad = pcel("unidad") or [""]
        if continua and elemento_actual is not None:
            el = elemento_actual
        else:
            ps = ps_elemento
            # «PRÁCTICA/TAREA 1(2h)»: en el formato antiguo, las horas van pegadas al nombre
            pegadas = re.fullmatch(r"(.*?\S)\s*(\(\d+\s*h\))", ps[0])
            if pegadas and not re.search(r"\(\d+\s*h\)", pegadas.group(1)):   # no «PR 3(6h), PR 4 (6h)»
                ps = [pegadas.group(1), pegadas.group(2), *ps[1:]]
            el = {"id": f"e{len(elementos) + 1}", "tipo": _tipo(ps[0]), "nombre": ps[0], "ra": _ras(cel("ra")),
                  "detalle": ps[1:], "_peso": cel("peso")}
            elementos.append(el)
            elemento_actual = el
        t = _trimestre(cel("trimestre"))
        trim_actual = t if t is not None else trim_actual
        ps = ps_unidad
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
        if "total" not in c41 and "horas" in c41:   # formato antiguo: «Horas» a secas son las horas totales del RA
            c41["total"] = c41.pop("horas")
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
    # «Horas» a secas junto a «Horas empresa» puede ser el total del RA o solo su parte de centro: es de centro si alguna
    # es menor que sus horas de empresa o si, con las de empresa, suman las del módulo (y solas no). Leídas como total,
    # daban un reparto de centro negativo y la programación no se podía heredar (2026-10-21, Sostenibilidad 1708).
    if t41 is not None and "centro" not in c41 and "total" in c41 and empresa:
        s_t, s_e = sum(totales.values()), sum(empresa.values())
        if any(totales.get(int(k), 0) < v for k, v in empresa.items()) or (horas and s_t != horas and s_t + s_e == horas):
            for k, v in empresa.items():
                totales[int(k)] = totales.get(int(k), 0) + v
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
        if r in totales and c != prop.get(r) and c >= 0:   # un reparto negativo no se guarda: queda la propuesta
            ajuste[str(r)] = c
    prog["centro_ajustado"] = ajuste
    return prog


def _entre(sec: list[Elemento], tabla: Elemento | None, despues: bool) -> list[Elemento]:
    if tabla is None:
        return []
    i = sec.index(tabla)
    return [e for e in (sec[i + 1:] if despues else sec[:i]) if e.tipo == "p"]


RE_VINETA_A_MANO = re.compile(r"^[•·▪◦‣–-]\s*")


def _parecido(ancla: str, texto: str) -> bool:
    """El párrafo es una variante del de la plantilla hecha a mano en Word: con «•» delante, con más texto detrás
    («Visitas y actividades complementarias: la asistencia…», el título corto y su texto en el mismo párrafo) o con
    otra redacción que empieza con las mismas tres palabras («La asistencia deberá alcanzar…»)."""
    t = RE_VINETA_A_MANO.sub("", texto)
    partes = re.split(r"\{\{[^{}]+\}\}", ancla)
    if re.match(".*?".join(re.escape(forma(p)) for p in partes), t):
        return True
    palabras = forma(partes[0]).split()[:3]
    return len(palabras) == 3 and t.split()[:3] == palabras


def _fijos_fuera_de_bloques(seccion: str) -> list[str]:
    """Los párrafos fijos de un apartado de la plantilla que no están dentro de un bloque sustituible."""
    out, dentro = [], None
    for e in plantilla()["secciones"].get(seccion, []):
        if e.tipo != "p":
            continue
        m = re.fullmatch(r"\{\{([?/])(?:sustituible:)?(\w+)\}\}", e.texto)
        if m and m.group(1) == "?" and e.texto.startswith("{{?sustituible:"):
            dentro = m.group(2)
        elif m and m.group(1) == "/" and m.group(2) == dentro:
            dentro = None
        elif dentro is None and not e.texto.startswith("{{"):
            out.append(e.texto)
    return out


def _limites_bloque(s: dict, textos: list[str]) -> tuple[int, int, bool] | None:
    """Índices del párrafo de entrada y del de salida de un bloque sustituible, y si el documento no lleva la salida.
    Primero, los de la plantilla tal cual (los de un documento exportado por la app); si no están, sus variantes hechas a
    mano (`_parecido`) y, sin párrafo de salida, el bloque acaba en el siguiente párrafo fijo del apartado
    (2026-10-23). El tercer valor solo es cierto si la salida no está en ninguna forma y el bloque acaba justo en el
    párrafo fijo que la sigue en la plantilla: el texto del profesor la sustituye (`sustituyen_salida`)."""
    i = next((k for k, t in enumerate(textos) if _patron(s["antes"]).match(t)), None)
    if i is None:
        i = next((k for k, t in enumerate(textos) if _parecido(s["antes"], t)), None)
    if i is None:
        return None
    if s["despues"] is None:
        return i, len(textos), False
    j = next((k for k in range(i + 1, len(textos)) if _patron(s["despues"]).match(textos[k])), None)
    if j is not None:
        return i, j, False
    fuera = _fijos_fuera_de_bloques(s["seccion"])
    fijos = [_patron(f) for f in fuera]
    j = next((k for k in range(i + 1, len(textos)) if _parecido(s["despues"], textos[k])
              or any(f.match(textos[k]) for f in fijos)), len(textos))
    sin_salida = not any(_parecido(s["despues"], t) for t in textos[i + 1:])
    k = next((n for n, f in enumerate(fuera) if f == s["despues"]), None)
    siguiente = fuera[k + 1] if k is not None and k + 1 < len(fuera) else None
    sustituye = sin_salida and siguiente is not None and j < len(textos) and bool(_patron(siguiente).match(textos[j]))
    return i, j, sustituye


def leer_textos_propios(sec: dict[str, list[Elemento]], proyecto: bool = False,
                        sustituyen: list[str] | None = None) -> dict:
    """Los bloques sustituibles que el profesor cambió. En `sustituyen` (si se pasa), los que además sustituyen al
    párrafo fijo que los sigue en la plantilla, porque el documento no lo lleva (`_limites_bloque`)."""
    out = {}
    for clave, s in plantilla()["sustituibles"].items():
        modelo = s["bloque"][proyecto]
        ps = [e for e in sec.get(s["seccion"], []) if e.tipo == "p"]
        textos = [forma(e.texto) for e in ps]
        limites = _limites_bloque(s, textos)
        if limites is None:
            continue
        i, j, sustituye = limites
        bloque = ps[i + 1:j]
        iguales = len(bloque) == len(modelo) and all(
            _patron(p).match(forma(e.texto)) for p, e in zip(modelo, bloque, strict=True))
        if not iguales:
            out[clave] = [_parrafo(e) for e in bloque]
            if sustituye and bloque and sustituyen is not None:
                sustituyen.append(clave)
    return out


def ra_del_documento(sec: dict[str, list[Elemento]], ficha) -> dict[str, str]:
    """Enunciados de RA de las tablas 3 y 4.1 que no son los del currículo (V-16), con el texto del documento."""
    oficiales = {r["n"]: forma(r["texto"]) for r in ficha.ra}
    out: dict[str, str] = {}
    for seccion in ("3", "4.1"):
        t, _i = _tabla(sec.get(seccion, []), "resultado de aprendizaje")
        for fila in (t.filas[1:] if t is not None else []):
            m = RE_RA.match(fila[0])
            texto_doc = fila[0][m.end():].strip() if m else ""
            n = int(m.group(1)) if m else None
            if n in oficiales and texto_doc and forma(texto_doc) != oficiales[n] and str(n) not in out:
                out[str(n)] = texto_doc
    return out


def leer_portada(elementos: list[Elemento], cat: Catalogo) -> tuple[list[str], str]:
    """Profesorado y curso escolar de las tablas de la portada (las mismas filas en el formato actual y en el antiguo)."""
    profesorado, curso_escolar = [], ""
    for t in (e for e in elementos if e.tipo == "tabla"):
        for fila, pfila in zip(t.filas, t.parrafos, strict=True):
            if len(fila) < 2:
                continue
            if forma(fila[0]).startswith("profesor"):
                # un párrafo por persona; también «Nombre Uno / Nombre Dos» en el mismo párrafo
                profesorado = [n.strip() for p in pfila[1] for n in re.split(r"\s+/\s+", p) if n.strip()]
            if forma(fila[0]).startswith("curso académico"):
                curso_escolar = re.sub(r"\s*/\s*", "-", fila[1].strip())   # también «2026/2027»
    if not re.fullmatch(r"\d{4}-\d{4}", curso_escolar):
        # sin curso en la portada: el último curso escolar que tiene el catálogo (su resolución de instrucciones)
        curso_escolar = max((n.curso_escolar for n in cat.normas.values() if n.curso_escolar), default="")
    return profesorado, curso_escolar


def importar(origen, cat: Catalogo, nombre_archivo: str | None = None, modulo: Modulo | None = None,
             comprobar: bool = True) -> dict:
    """Los datos del profesor de una programación .docx (los incrustados si los lleva). Lee también el formato
    antiguo de las programaciones (importar_antigua.py). `modulo`: el elegido en la columna «Módulos»; con él no hace
    falta que el archivo se llame «SIGLA N - 0xxx - Nombre» (`decidir_modulo`)."""
    datos = Path(origen).read_bytes() if isinstance(origen, (str, Path)) else origen
    incrustada = incrustar.leer(datos)
    if incrustada is not None:
        return incrustada.programacion
    nombre = nombre_archivo or (Path(origen).name if isinstance(origen, (str, Path)) else "")
    elementos = contenido.leer(datos)
    sec = contenido.secciones(elementos)
    from programaciones import importar_ambito

    if importar_ambito.es_ambito(sec):
        return importar_ambito.importar(elementos, cat, nombre, modulo, comprobar)
    # el formato actual tiene los apartados 1, 4 y 11 y la tabla 4.1; el antiguo, la ponderación en otro sitio (7.1)
    if not ({"1", "4", "11"} <= set(sec) and "4.1" in sec):
        from programaciones import importar_antigua

        # el formato antiguo lleva los títulos como párrafos normales o, en algunas, con estilo de título de Word
        for els in (elementos, contenido.leer(datos, titulos=True)):
            if importar_antigua.es_antigua(els):
                return importar_antigua.importar(els, cat, nombre, modulo, comprobar)
    # formato actual: los subtítulos sin número («Principios generales y pedagógicos») van a su apartado
    sec = contenido.secciones(contenido.leer(datos, apartados=apartados_plantilla()))
    elegido = decidir_modulo(modulo_del_nombre(nombre, cat), None, modulo, comprobar, cat)
    if elegido is None:
        raise NoEsProgramacion(f"«{nombre}» no sigue el patrón «SIGLA N - 0xxx - Nombre» (con la sigla del ciclo): "
                               f"{AYUDA_MODULO}")
    sigla, curso, codigo = elegido
    ficha = cat.ficha(sigla, codigo, curso)
    if not {"1", "4", "11"} <= set(sec):
        raise NoEsProgramacion("sin los apartados de la plantilla")

    # Portada: profesorado y curso
    profesorado, curso_escolar = leer_portada(sec.get("portada", []), cat)
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
    # la nota de Educamos pegada a la tabla (ADR-042) es de la plantilla, no del profesor
    prog["notas_tabla41"] = [_parrafo(e) for e in _entre(s41, t41, True) if not es_fijo(e.texto, "4.1")]

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

    sustituyen: list[str] = []
    prog["textos_propios"] = leer_textos_propios(sec, ficha.tipo == "proyecto", sustituyen)
    if sustituyen:
        prog["sustituyen_salida"] = sustituyen
    ra_doc = ra_del_documento(sec, ficha)
    if ra_doc:
        prog["ra_documento"] = ra_doc
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
    ev = {}
    for e in sec.get("9", []):
        m = re.match(r"^(Evaluación inicial|1ª evaluación|2ª evaluación|3ª evaluación):\s*(\d{2})/(\d{2})/(\d{4})", e.texto)
        if m:
            clave = {"Evaluación inicial": "inicial", "1ª evaluación": "primera", "2ª evaluación": "segunda",
                     "3ª evaluación": "tercera"}[m.group(1)]
            ev[clave] = dt.date(int(m.group(4)), int(m.group(3)), int(m.group(2))).isoformat()
        # Fechas de fin de las convocatorias (ADR-033): «La convocatoria ordinaria finalizará el 8 de junio de 2027 y
        # la convocatoria extraordinaria finalizará el 22 de junio de 2027»
        m = re.search(r"convocatoria ordinaria finalizará el " + RE_FECHA_LARGA + r" de (\d{4}).*?extraordinaria "
                      r"finalizará el " + RE_FECHA_LARGA + r" de (\d{4})", e.texto)
        if m:
            ev["ordinaria"] = dt.date(int(m.group(3)), MESES.index(m.group(2)) + 1, int(m.group(1))).isoformat()
            ev["extraordinaria"] = dt.date(int(m.group(6)), MESES.index(m.group(5)) + 1, int(m.group(4))).isoformat()
        # Programaciones anteriores: «se realizará del 31 de mayo al 3 de junio de 2027 y la convocatoria extraordinaria
        # comenzará el 14 de junio de 2027». Del intervalo, su fin; de la extraordinaria solo se sabe el inicio.
        m = re.search(r"convocatoria ordinaria se realizará del " + RE_FECHA_LARGA + r"(?: de (\d{4}))? al "
                      + RE_FECHA_LARGA + r" de (\d{4}).*?comenzará el " + RE_FECHA_LARGA + r" de (\d{4})", e.texto)
        if m:
            ev["ordinaria"] = dt.date(int(m.group(6)), MESES.index(m.group(5)) + 1, int(m.group(4))).isoformat()
            ev["extraordinaria"] = dt.date(int(m.group(9)), MESES.index(m.group(8)) + 1, int(m.group(7))).isoformat()
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
    return {"evaluaciones": ev, "formacion_empresa": {grado: {curso: periodos}}}
