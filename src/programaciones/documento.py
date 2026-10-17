"""Documento de la programación: rellena la plantilla con marcas y aplica el retoque final (ADR-006 y ADR-018).

Entrada: la programación (datos del profesor), el catálogo y el curso escolar (fechas y formación en empresa).
Salida: el .docx en bytes. Lo que va en cada apartado y de dónde sale está en docs/DOCUMENTO_GENERADO.md.

Marcas de la plantilla (las pone scripts/plantilla.py):
- `{{nombre}}`: un run que se sustituye por texto o hipervínculos.
- `{{*nombre}}`: un párrafo que se repite por cada elemento de una lista (normas, competencias, párrafos del profesor).
- `{{@lista.campo}}`: celda de una fila de tabla que se repite por cada elemento de la lista.
- `{{#lista}}` … `{{/lista}}`: grupo de párrafos que se repite (RA con sus criterios); cada copia reinicia sus listas.
- `{{?condición}}` … `{{/condición}}`: grupo que solo queda si se cumple; `{{?sustituible:clave}}`, bloque fijo que el
  profesor puede sustituir por el suyo (`textos_propios`).
"""
from __future__ import annotations

import copy
import datetime as dt
import re
from collections import ChainMap
from dataclasses import dataclass
from pathlib import Path

import yaml
from lxml import etree

from programaciones import calculos, ooxml
from programaciones.catalogo import Catalogo, Ficha, Norma
from programaciones.ooxml import W, normal, texto

RECURSOS = Path(__file__).resolve().parent / "recursos"
PLANTILLA = RECURSOS / "plantilla"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
# Normas autonómicas del catálogo que se citan en 1.2 además de las comunes de la plantilla y de la resolución del curso:
# el Decreto 95/2026, que da nueva redacción a los anexos I y II (horario) del Decreto 114/2025 (CarlosFB, 2026-10-17).
AUTONOMICAS = ("DOGV-C-2026-21170",)
RE_MARCA = re.compile(r"\{\{([#/?*@]?)([\w.:]+)\}\}")


@dataclass(frozen=True)
class Enlace:
    texto: str
    url: str


@dataclass(frozen=True)
class Negrita:
    texto: str


@dataclass
class Parrafo:
    """Párrafo del profesor: texto y nivel de viñeta (None: párrafo normal)."""
    segmentos: object
    nivel: int | None = None


@dataclass
class Opciones:
    borrador: bool = False          # vista previa: marca de agua «BORRADOR»
    correo_pie: str = ""            # correo del pie (Ajustes); vacío por defecto (repositorio público)
    fecha: dt.date | None = None    # fecha del documento (propiedades); hoy por defecto
    idioma: str = "es"


def metadatos_plantilla() -> dict:
    with open(PLANTILLA / "plantilla.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def cargar_plantilla(idioma: str = "es") -> ooxml.Paquete:
    return ooxml.Paquete.desde_carpeta(PLANTILLA / idioma)


# ---------------------------------------------------------------------------------------------------------------------
# Formatos
# ---------------------------------------------------------------------------------------------------------------------
def fecha(d: str | dt.date) -> dt.date:
    return d if isinstance(d, dt.date) else dt.date.fromisoformat(str(d))


def fecha_corta(d) -> str:
    return fecha(d).strftime("%d/%m/%Y")


def fecha_larga(d, con_anio: bool = True) -> str:
    d = fecha(d)
    return f"{d.day} de {MESES[d.month - 1]}" + (f" de {d.year}" if con_anio else "")


def intervalo(desde, hasta, prefijo: str = "del") -> str:
    """«del 31 de mayo al 3 de junio de 2027» (el año una vez si coincide)."""
    a, b = fecha(desde), fecha(hasta)
    return f"{prefijo} {fecha_larga(a, a.year != b.year)} al {fecha_larga(b)}"


def letras(lista: list[str]) -> str:
    """«a), b), d) y k)»."""
    xs = [f"{x})" for x in lista]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1] if xs else ""


def nombre_archivo(ficha: Ficha, extension: str = "docx") -> str:
    """«SEA 2 - 0517 - Procesos en instalaciones de infraestructuras comunes de telecomunicaciones.docx»."""
    nombre = re.sub(r'[/:*?"<>|\\]', "-", ficha.nombre)
    return f"{ficha.sigla} {ficha.curso} - {ficha.codigo} - {nombre}.{extension}"


# ---------------------------------------------------------------------------------------------------------------------
# Contexto: el valor de cada marca
# ---------------------------------------------------------------------------------------------------------------------
def _parrafos(lista) -> list[Parrafo]:
    return [Parrafo(p["texto"], p.get("nivel")) for p in (lista or [])]


def _enlace(n: Norma, corta: bool = False) -> Enlace:
    return Enlace(n.cita_corta if corta else n.cita, n.enlace)


def _modificadores(cat: Catalogo, ciclo: dict) -> list[Norma]:
    """Normas que modifican el real decreto del título, salvo las generales de 2024 (RD 499/2024 y RD 500/2024)."""
    out = []
    for ident in ciclo["rd"]["modificado_por"]:
        n = cat.norma(ident)
        if not re.search(r"por el que se modifican determinados reales decretos", n.titulo):
            out.append(n)
    return sorted(out, key=lambda n: n.fecha)


def _general_2024(cat: Catalogo, ciclo: dict) -> Norma | None:
    for ident in ciclo["rd"]["modificado_por"]:
        n = cat.norma(ident)
        if re.search(r"por el que se modifican determinados reales decretos", n.titulo):
            return n
    return None


def contexto(prog: dict, cat: Catalogo, curso: dict | None, opciones: Opciones | None = None) -> dict:
    opciones = opciones or Opciones()
    ficha = cat.ficha(prog["ciclo"], prog["modulo"], prog.get("curso"), opciones.idioma)
    ciclo = cat.ciclo(prog["ciclo"])
    rd = cat.norma(ciclo["rd"]["id"])
    mods = _modificadores(cat, ciclo)
    general = _general_2024(cat, ciclo)
    H = ficha.horas
    ras = ficha.numeros_ra
    proyecto = ficha.tipo == "proyecto"
    ctx: dict = {"ficha": ficha, "proyecto": proyecto, "no_proyecto": not proyecto}
    n_tareas = max(1, sum(1 for e in prog.get("elementos", []) if e.get("tipo") == "T"))
    ctx["tareas"] = f"T01 a T{n_tareas:02d}"   # variante de proyecto: «tareas del proyecto (T01 a T08)»

    # Portada
    profesorado = [p for p in prog.get("profesorado", []) if p.strip()]
    ctx.update(
        familia=ficha.familia, grado=f"{'Grado Superior' if ficha.grado == 'GS' else 'Grado Medio'}: ",
        ciclo=ficha.ciclo_nombre, modulo_portada=f"{ficha.codigo} – {ficha.nombre}", horas=str(H),
        profesorado_etiqueta="Profesor:" if len(profesorado) <= 1 else "Profesores:", profesorado=profesorado,
        curso_escolar=prog["curso_escolar"], titulo=ficha.titulo, correo_pie=opciones.correo_pie)

    # Real decreto del título y su redacción
    ctx.update(rd_cita=_enlace(rd), rd_cita_corta=_enlace(rd, corta=True), rd_resto_titulo=rd.resto_titulo)
    if mods:
        verbo = "actualizada" if any("actualiza" in m.titulo for m in mods) else "modificada"
        ctx["rd_modificacion"] = [f"{verbo} por el ", *_lista_enlaces(mods)]
        ctx["rd_redaccion_ra"] = [f", en su redacción {verbo} por el ", *_lista_enlaces(mods)]
    else:
        ctx["rd_modificacion"] = ["modificada por el ", _enlace(general)] if general else ["sin modificaciones"]
        ctx["rd_redaccion_ra"] = [", en su redacción vigente, modificada por el ", _enlace(general)] if general else [""]
    if proyecto and general:
        ctx["rd_redaccion_ra"] = [*ctx["rd_redaccion_ra"], ", y por el ", _enlace(general),
                                  ", que da al módulo la denominación de «Proyecto intermodular» y mantiene sus "
                                  "resultados de aprendizaje y criterios de evaluación"]
    fuente_v = ciclo["fuentes"]["correspondencias_ecp"]
    if fuente_v != rd.id:
        ctx["anexo_v_redaccion"] = [", en la redacción dada por el ", _enlace(cat.norma(fuente_v), corta=True)]
    elif mods:
        ctx["anexo_v_redaccion"] = [" (anexo que el ", _enlace(mods[0], corta=True), " no modifica)"]
    elif general:
        ctx["anexo_v_redaccion"] = [", cuya redacción no ha sido modificada por el ", _enlace(general, corta=True)]
    else:
        ctx["anexo_v_redaccion"] = ""
    cg = (ciclo.get("competencia_general_corregida") or ciclo["competencia_general"])["es"]
    ctx["competencia_general"] = re.sub(r"^La competencia general de este título consiste en\s+", "", cg)

    # Normativa: la del título y la del curso (las comunes ya están en la plantilla)
    estatal = [rd, *[cat.norma(i) for i in ciclo["rd"].get("correcciones", [])], *mods]
    if general:
        estatal.append(general)
    ctx["normativa_estatal"] = [(n, [Enlace(n.titulo, n.enlace)]) for n in estatal]
    autonomica = [n for n in cat.normativa(prog["ciclo"], "autonomico", prog["curso_escolar"])
                  if n.curso_escolar == prog["curso_escolar"] or n.id in AUTONOMICAS]
    ctx["normativa_autonomica"] = [(n, [Enlace(_titulo_dogv(n.titulo), n.enlace)]) for n in autonomica]

    # 2: estándares de competencia, competencias y optativos
    ctx["ecp"] = filas_ecp(cat, ciclo, ficha, rd)
    ctx["competencias"] = [f"{c['letra']}) {c['texto']['es']}" for c in ciclo["competencias"]]
    ctx["optativos"] = [{"codigo": o["codigo"], "nombre": o["nombre"]["es"], "curso": f"{o['curso']}.º"}
                        for o in ciclo.get("optativos_ofertados", [])]

    # 3: contribución a las competencias
    cita_mod = [_enlace(rd)]
    if ficha.fuente_ra and ficha.fuente_ra != rd.id and ficha.fuente_ra.startswith("BOE"):
        cita_mod += [", en la redacción dada por el ", _enlace(cat.norma(ficha.fuente_ra))]
    ctx["rd_cita_redaccion_modulo"] = cita_mod
    ctx["modulo_codigo_nombre"] = f"{ficha.codigo}. {ficha.nombre}"
    todas = [c["letra"] for c in ciclo["competencias"]]
    comp = ficha.competencias_modulo
    if comp and comp == todas:
        ctx["contribucion"] = (f"la totalidad de las competencias profesionales, personales y sociales del título, "
                               f"de la {todas[0]}) a la {todas[-1]})")
    else:
        ctx["contribucion"] = f"las competencias profesionales, personales y sociales {letras(comp)} del título"
    rc = prog.get("ra_competencias") or {}
    ctx["ra_competencias"] = [{"codigo": f"R.A.{r['n']}.", "texto": f" {r['texto']}", "competencias": ", ".join(
        f"{x})" for x in rc.get(str(r["n"]), []))} for r in ficha.ra]

    # 4 y 4.1: tablas
    ctx["h_sem"] = str(ficha.h_sem)
    ctx["t4_cabecera_unidad"] = "UNIDAD DIDÁCTICA"
    cab = [_enlace(rd, corta=True)]
    if ficha.fuente_ra and ficha.fuente_ra != rd.id and ficha.fuente_ra.startswith("BOE"):
        # dos normas en una columna estrecha: «RD 1581/2011, redacción RD 401/2023», como la programación de 0963
        rf = cat.norma(ficha.fuente_ra)
        cab = [Enlace(rd.cita_corta.replace("Real Decreto", "RD"), rd.enlace), ", redacción ",
               Enlace(rf.cita_corta.replace("Real Decreto", "RD"), rf.enlace)]
    ctx["rd_cabecera_ra"] = cab
    ctx.update(tablas(prog, ficha))
    for clave in ("contenidos", "notas_tabla4", "notas_tabla41", "metodologia", "metodologia_final", "recursos",
                  "espacios", "actividades"):
        ctx[clave] = _parrafos(prog.get(clave))

    # 9 y 9.1
    ctx["empresa_pct"] = str(calculos.porcentaje_empresa(prog, H))
    ctx["profesorado_del_modulo"] = "el profesor del módulo" if len(profesorado) <= 1 else "el profesorado del módulo"
    ctx.update(fechas_curso(curso, ficha))

    # 11: RA y criterios
    ctx["resultados"] = [{"ra.codigo": f"R.A.{r['n']}.", "ra.texto": f" {r['texto']}",
                          "ra.criterios": [c["texto"] for c in r["criterios"]]} for r in ficha.ra]
    ctx["textos_propios"] = {k: _parrafos(v) for k, v in (prog.get("textos_propios") or {}).items() if v}
    ctx["ras"] = ras
    return ctx


def _titulo_dogv(t: str) -> str:
    """«DECRETO 95/2026, …» → «Decreto 95/2026, …», como el Decreto 114/2025 en la plantilla."""
    return re.sub(r"^DECRETO\b", "Decreto", t)


def _lista_enlaces(normas: list[Norma]) -> list:
    out: list = []
    for i, n in enumerate(normas):
        if i:
            out.append(" y por el " if i == len(normas) - 1 else ", por el ")
        out.append(_enlace(n))
    return out


def filas_ecp(cat: Catalogo, ciclo: dict, ficha: Ficha, rd: Norma) -> list[dict]:
    """Tabla del apartado 2: las correspondencias del anexo V B) y los módulos técnicos y el Proyecto sin
    correspondencia. Primero las filas del módulo de la programación; después, por el código del primer módulo."""
    nombres = {m["codigo"].rstrip("p"): m["nombre"]["es"] for m in ciclo["modulos"]}
    sin = ["Sin correspondencia directa con estándares de competencia acreditables en el anexo V B) del ",
           Enlace(f"RD {rd.cita_corta.split()[-1]}", rd.enlace), "."]
    filas, con = [], set()
    for corr in ciclo["correspondencias_ecp"]:
        codigos = sorted(corr["modulos"])
        con.update(codigos)
        filas.append({"_codigos": codigos,
                      "modulos": [f"{c}. {nombres.get(c, '')}." for c in codigos],
                      "estandares": [f"{e['codigo']} – {e['texto']['es']}" if e.get("codigo") else e["texto"]["es"]
                                     for e in corr["ecp"]]})
    tecnicos = [m["codigo"] for m in ciclo["modulos"] if m["tipo"] == "propio"]
    if ciclo.get("proyecto"):
        tecnicos.append(ciclo["proyecto"])
    for c in tecnicos:
        if c not in con:
            filas.append({"_codigos": [c], "modulos": [f"{c}. {nombres.get(c, '')}."], "estandares": [sin]})
    propias = [f for f in filas if ficha.codigo in f["_codigos"]]
    resto = sorted((f for f in filas if ficha.codigo not in f["_codigos"]), key=lambda f: f["_codigos"][0])
    return propias + resto


def tablas(prog: dict, ficha: Ficha) -> dict:
    """Valores de las tablas 4 y 4.1."""
    H = ficha.horas
    ras = ficha.numeros_ra
    h_el = calculos.horas_elementos(prog)
    elementos = {e["id"]: e for e in prog.get("elementos", [])}
    filas, anterior, inicio = [], None, None
    for u in prog.get("unidades", []):
        e = elementos.get(u.get("elemento"), {"id": None, "nombre": "", "ra": []})
        t = u.get("trimestre")
        trim = " y ".join(str(x) for x in t) if isinstance(t, list) else str(t if t is not None else "")
        codigo, titulo = partir_titulo(u.get("titulo", ""))
        fila = {"codigo": codigo, "titulo": titulo, "descripcion": list(u.get("descripcion", [])),
                "horas": str(u.get("horas", "")), "trimestre": trim, "elemento": e["nombre"],
                "detalle": list(e.get("detalle") or [f"({h_el.get(e['id'], 0)}h)"]),
                "peso": calculos.formato_peso_ajustado(e["peso_ajustado"]) if e.get("peso_ajustado")
                else calculos.formato_peso(calculos.peso(h_el.get(e["id"], 0), H)),
                "ra": calculos.lista_ra(e.get("ra", []))}
        if anterior is not None and anterior["_elemento"] == e["id"] and e["id"] is not None:
            # unidades seguidas del mismo elemento: celdas de elemento, peso y RA combinadas en vertical
            inicio.setdefault("_vmerge", {k: "restart" for k in ("elemento", "detalle", "peso", "ra")})
            fila["_vmerge"] = {k: "continue" for k in ("elemento", "detalle", "peso", "ra")}
        else:
            inicio = fila
        fila["_elemento"] = e["id"]
        filas.append(fila)
        anterior = fila
    t41 = calculos.tabla41(prog, ras)
    h_c, h_e = calculos.horas_centro(prog), calculos.horas_empresa(prog)
    pe = calculos.porcentaje_empresa(prog, H)
    textos_ra = {r["n"]: r["texto"] for r in ficha.ra}
    return {
        "unidades": filas,
        "t4_centro_horas": str(h_c), "t4_centro_pct": f"{100 - pe} %", "t4_centro_ra": "",
        "t4_empresa_horas": str(h_e), "t4_empresa_pct": f"{pe} %",
        "t4_empresa_ra": calculos.lista_ra([f.ra for f in t41 if f.empresa]),
        "t4_total_horas": str(h_c + h_e), "t4_total_pct": "100 %", "t4_total_ra": "",
        "ponderacion": [{"codigo": f"R.A.{f.ra}.", "texto": f" {textos_ra.get(f.ra, '')}", "total": str(f.total),
                         "modalidad": f.modalidad, "empresa": str(f.empresa) if f.empresa else "—"} for f in t41],
        "t41_total": str(sum(f.total for f in t41)), "t41_total_modalidad": "—", "t41_empresa": str(h_e),
        "con_empresa": h_e > 0,
        "pct_curso": ["% del curso (aprox.)", *[calculos.pct_curso(f.total, H) for f in t41], "100 %"]
        if prog.get("columna_pct_curso") else None,
    }


PENDIENTE = "pendiente"


def fechas_curso(curso: dict | None, ficha: Ficha) -> dict:
    """Fechas de evaluación y periodos de formación en empresa del curso escolar (por grado y curso).

    Sin el curso escolar dado de alta (`catalogo/cursos/`), las fechas salen como «pendiente»: solo sirve para la vista
    previa, porque la validación V-11 bloquea la exportación definitiva."""
    if curso is None:
        return {**{k: PENDIENTE for k in ("ev_inicial", "ev_primera", "ev_segunda", "ev_tercera")},
                "ordinaria": PENDIENTE, "extraordinaria": PENDIENTE,
                "formacion_empresa": [{"fe.jornada": "Periodos de formación en empresa", "fe.resto": f": {PENDIENTE}"}]}
    ev = curso["evaluaciones"]
    out = {"ev_inicial": fecha_corta(ev["inicial"]), "ev_primera": fecha_corta(ev["primera"]),
           "ev_segunda": fecha_corta(ev["segunda"]), "ev_tercera": fecha_corta(ev["tercera"]),
           "ordinaria": intervalo(curso["ordinaria"]["desde"], curso["ordinaria"]["hasta"]),
           "extraordinaria": fecha_larga(curso["extraordinaria_desde"])}
    periodos = (curso.get("formacion_empresa", {}).get(ficha.grado, {}) or {}).get(ficha.curso) or \
        (curso.get("formacion_empresa", {}).get(ficha.grado, {}) or {}).get(str(ficha.curso)) or []
    out["formacion_empresa"] = [
        {"fe.jornada": f"Alumnos que realicen {p['jornada']}h/día",
         "fe.resto": f" (en total {p['dias']} días de formación): {intervalo(p['desde'], p['hasta'], 'desde el')}"}
        for p in sorted(periodos, key=lambda p: -p["jornada"])]
    return out


RE_CODIGO_UNIDAD = re.compile(r"^(.{1,30}?[.:]-?)(\s+\S.*)$")


def partir_titulo(titulo: str) -> tuple[str, str]:
    """«UD00. PRL en las instalaciones» → («UD00.», « PRL en las instalaciones»): el código va en negrita."""
    m = RE_CODIGO_UNIDAD.match(titulo)
    return (m.group(1), m.group(2)) if m else ("", titulo)


# ---------------------------------------------------------------------------------------------------------------------
# Citas de normas en los párrafos del profesor: con su enlace (regla 1 de la guía programacion-didactica)
# ---------------------------------------------------------------------------------------------------------------------
RE_CITA_TEXTO = re.compile(r"\b(Real Decreto|RD|Decreto|DECRETO|Orden|ORDEN|Ley Orgánica)\s+(\d+)/(\d{4})"
                           r"(,\s+de\s+\d{1,2}\s+de\s+[a-záéíóú]+)?")


def enlazar(texto_parrafo: str, cat: Catalogo) -> list:
    """El texto con las normas del catálogo que cita convertidas en hipervínculos («Real Decreto 1127/2010, de 10 de
    septiembre», «RD 1127/2010», «Decreto 114/2025»…). Las que no están en el catálogo se quedan como texto."""
    out, pos = [], 0
    for m in RE_CITA_TEXTO.finditer(texto_parrafo):
        clase = {"RD": "Real Decreto", "DECRETO": "Decreto", "ORDEN": "Orden"}.get(m.group(1), m.group(1))
        norma = next((n for n in cat.normas.values()
                      if re.match(rf"^{clase}\s+{m.group(2)}/{m.group(3)}\b", n.titulo, re.I)), None)
        if norma is None:
            continue
        out.append(texto_parrafo[pos:m.start()])
        out.append(Enlace(m.group(0), norma.enlace))
        pos = m.end()
    out.append(texto_parrafo[pos:])
    return [x for x in out if x != ""]


# ---------------------------------------------------------------------------------------------------------------------
# Motor de marcas
# ---------------------------------------------------------------------------------------------------------------------
class Motor:
    def __init__(self, pq: ooxml.Paquete, parte: str, vinetas: str, cat: Catalogo | None = None):
        self.pq = pq
        self.parte = parte
        self.vinetas = vinetas
        self.cat = cat
        self.numeracion = pq.xml("word/numbering.xml")

    def segmentos_profesor(self, s):
        """Párrafo del profesor: «**texto**» en negrita y las normas del catálogo que cita, con enlace."""
        if not isinstance(s, str):
            return s
        out = []
        for k, trozo in enumerate(s.split("**")):
            if not trozo:
                continue
            if k % 2:
                out.append(Negrita(trozo))
            else:
                out.extend(enlazar(trozo, self.cat) if self.cat is not None else [trozo])
        return out

    # -- runs ----------------------------------------------------------------------------------------------------------
    def runs(self, valor, rpr) -> list:
        segs = valor if isinstance(valor, (list, tuple)) else [valor]
        out = []
        for s in segs:
            if s is None or s == "":
                continue
            if isinstance(s, Enlace):
                rid = self.pq.relacion(self.parte, ooxml.TIPO_HIPERVINCULO, s.url, externa=True)
                h = etree.Element(W + "hyperlink")
                h.set(ooxml.R + "id", rid)
                h.set(W + "history", "1")
                h.append(ooxml.run(s.texto, ooxml.rpr_enlace(rpr)))
                out.append(h)
            elif isinstance(s, Negrita):
                r = ooxml.run(s.texto, rpr)
                pr = r.find(W + "rPr")
                if pr is None:
                    pr = etree.Element(W + "rPr")
                    r.insert(0, pr)
                ooxml.hijo(pr, "b", ooxml.ORDEN_RPR)
                out.append(r)
            elif isinstance(s, (list, tuple)):
                out.extend(self.runs(s, rpr))
            else:
                out.append(ooxml.run(str(s), rpr))
        return out

    def rellenar(self, elem, ctx) -> None:
        """Marcas en línea de un elemento (párrafo, celda, fila…)."""
        for r in list(elem.iter(W + "r")):
            t = r.find(W + "t")
            if t is None or not t.text or "{{" not in t.text:
                continue
            m = RE_MARCA.fullmatch(t.text.strip())
            solo = [x.tag for x in r if x.tag != W + "rPr"] == [W + "t"]
            if m and not m.group(1) and solo:
                valor = _valor(ctx, m.group(2))
                rpr = r.find(W + "rPr")
                nuevos = self.runs(valor, rpr)
                for n in nuevos:
                    r.addprevious(n)
                r.getparent().remove(r)
            else:
                t.text = RE_MARCA.sub(lambda m: _plano(_valor(ctx, m.group(2))), t.text)

    # -- párrafos ------------------------------------------------------------------------------------------------------
    def nivel(self, p, nivel: int | None) -> None:
        pp = ooxml.ppr(p)
        num = pp.find(W + "numPr")
        if nivel is None:
            if num is not None:
                pp.remove(num)
            return
        num_id = num.find(W + "numId").get(W + "val") if num is not None and num.find(W + "numId") is not None \
            else self.vinetas
        if num is not None:
            pp.remove(num)
        ind = pp.find(W + "ind")
        if ind is not None:
            pp.remove(ind)
        num = etree.SubElement(pp, W + "numPr")
        etree.SubElement(num, W + "ilvl").set(W + "val", str(nivel))
        etree.SubElement(num, W + "numId").set(W + "val", num_id)
        ooxml.ordenar(pp, ooxml.ORDEN_PPR)

    def repetir_parrafo(self, p, valores, ctx, marca: str) -> list:
        """Una copia de `p` por valor, con la marca sustituida. Devuelve las copias (ya en el documento)."""
        copias = []
        for v in valores:
            q = copy.deepcopy(p)
            ooxml.limpiar_ids(q)
            if isinstance(v, Parrafo):
                self.nivel(q, v.nivel)
                v = self.segmentos_profesor(v.segmentos)
            sub = ChainMap({marca: v}, ctx)
            for r in q.iter(W + "r"):
                t = r.find(W + "t")
                if t is not None and t.text and t.text.strip() == "{{*%s}}" % marca:
                    t.text = "{{%s}}" % marca
            self.rellenar(q, sub)
            p.addprevious(q)
            copias.append(q)
        padre = p.getparent()
        if not copias and padre.tag == W + "tc" and len(padre.findall(W + "p")) == 1:
            for x in list(p):   # una celda necesita un párrafo: queda vacío
                if x.tag != W + "pPr":
                    p.remove(x)
            return []
        padre.remove(p)
        return copias

    def repetidos(self, raiz, ctx) -> None:
        for p in list(raiz.iter(W + "p")):
            m = _marca_parrafo(p)
            if m and m[0] == "*":
                if p.getparent() is None:
                    continue
                self.repetir_parrafo(p, _valor(ctx, m[1]) or [], ctx, m[1])

    # -- numeración ----------------------------------------------------------------------------------------------------
    def reiniciar(self, num_id: str) -> str:
        """Una numeración nueva con la misma definición que `num_id`, empezando en 1."""
        orig = next(n for n in self.numeracion.findall(W + "num") if n.get(W + "numId") == num_id)
        nuevo = str(max(int(n.get(W + "numId")) for n in self.numeracion.findall(W + "num")) + 1)
        n = etree.Element(W + "num")
        n.set(W + "numId", nuevo)
        etree.SubElement(n, W + "abstractNumId").set(W + "val", orig.find(W + "abstractNumId").get(W + "val"))
        lo = etree.SubElement(n, W + "lvlOverride")
        lo.set(W + "ilvl", "0")
        etree.SubElement(lo, W + "startOverride").set(W + "val", "1")
        ultimo = self.numeracion.findall(W + "num")[-1]
        ultimo.addnext(n)
        return nuevo

    # -- grupos ---------------------------------------------------------------------------------------------------------
    def bloques(self, body, ctx) -> None:
        """Condiciones y grupos repetidos al nivel del cuerpo."""
        while True:
            hijos = list(body)
            ini = next(((i, m) for i, e in enumerate(hijos) if (m := _marca_parrafo(e)) and m[0] in ("?", "#")), None)
            if ini is None:
                return
            i, (tipo, nombre) = ini
            base = nombre.split(":")[-1]
            fin = next(k for k in range(i + 1, len(hijos)) if _marca_parrafo(hijos[k]) == ("/", base))
            dentro = hijos[i + 1:fin]
            if tipo == "?" and nombre.startswith("sustituible:"):
                propios = ctx["textos_propios"].get(base)
                if propios:
                    modelos = [e for e in dentro if e.tag == W + "p" and _marca_parrafo(e) is None] or dentro
                    normal_p = next((e for e in modelos if ooxml.numeracion(e) is None), modelos[0])
                    lista_p = next((e for e in modelos if ooxml.numeracion(e)), normal_p)
                    for par in propios:
                        q = copy.deepcopy(lista_p if par.nivel is not None else normal_p)
                        ooxml.limpiar_ids(q)
                        for x in list(q):
                            if x.tag != W + "pPr":
                                q.remove(x)
                        base = lista_p if par.nivel is not None else normal_p
                        runs = [r for r in base.iter(W + "r") if r.find(W + "t") is not None]
                        largo = max(runs, key=lambda r: len(r.find(W + "t").text or ""), default=None)
                        rpr = largo.find(W + "rPr") if largo is not None else None
                        self.nivel(q, par.nivel)
                        q.extend(self.runs(self.segmentos_profesor(par.segmentos), rpr))
                        hijos[i].addprevious(q)
                    for e in dentro:
                        body.remove(e)
            elif tipo == "?":
                if not ctx.get(nombre):
                    for e in dentro:
                        body.remove(e)
            else:   # «#»: grupo repetido
                for item in _valor(ctx, nombre) or []:
                    sub = ChainMap(item, ctx)
                    copias = [copy.deepcopy(e) for e in dentro]
                    cambios: dict[str, str] = {}
                    for c in copias:
                        ooxml.limpiar_ids(c)
                        for nid in c.iter(W + "numId"):
                            v = nid.get(W + "val")
                            if v not in cambios:
                                cambios[v] = self.reiniciar(v)
                            nid.set(W + "val", cambios[v])
                        hijos[i].addprevious(c)
                    for c in copias:
                        self.repetidos(c, sub)
                        if c.getparent() is not None:
                            self.rellenar(c, sub)
                for e in dentro:
                    body.remove(e)
            body.remove(hijos[i])
            body.remove(hijos[fin])

    # -- tablas -------------------------------------------------------------------------------------------------------
    def filas(self, raiz, ctx) -> None:
        """Filas con marcas {{@lista.campo}}: una copia por elemento de la lista. Un párrafo con una sola marca cuyo
        valor es una lista se repite (celdas de varios párrafos); si no, se rellenan sus marcas."""
        for tr in list(raiz.iter(W + "tr")):
            marcas = [m.group(2) for m in RE_MARCA.finditer(texto(tr)) if m.group(1) == "@"]
            if not marcas:
                continue
            lista = marcas[0].split(".")[0]
            for item in _valor(ctx, lista) or []:
                q = copy.deepcopy(tr)
                ooxml.limpiar_ids(q)
                sub = ChainMap(item, ctx)
                for tc in q.findall(W + "tc"):
                    campos = [m.group(2).split(".", 1)[1] for m in RE_MARCA.finditer(texto(tc)) if m.group(1) == "@"]
                    if not campos:
                        continue
                    vm = next((v for c in campos if (v := (item.get("_vmerge") or {}).get(c))), None)
                    if vm:
                        ooxml.hijo(ooxml.tcpr(tc), "vMerge", ooxml.ORDEN_TCPR)
                        if vm == "restart":
                            tc.find(f"{W}tcPr/{W}vMerge").set(W + "val", "restart")
                    for p in [p for p in tc.findall(W + "p") if "{{@" in texto(p)]:
                        de_p = [m.group(2).split(".", 1)[1] for m in RE_MARCA.finditer(texto(p)) if m.group(1) == "@"]
                        if vm == "continue":
                            for r in list(p.iter(W + "r")):
                                r.getparent().remove(r)
                            continue
                        for r in p.iter(W + "r"):
                            x = r.find(W + "t")
                            if x is not None and x.text and "{{@" in x.text:
                                x.text = RE_MARCA.sub(lambda m: "{{%s}}" % m.group(2).split(".", 1)[1], x.text)
                        if len(de_p) == 1 and isinstance(item.get(de_p[0]), list):
                            for r in p.iter(W + "r"):
                                x = r.find(W + "t")
                                if x is not None and x.text == "{{%s}}" % de_p[0]:
                                    x.text = "{{*%s}}" % de_p[0]
                            self.repetir_parrafo(p, item[de_p[0]], sub, de_p[0])
                        else:
                            self.rellenar(p, sub)
                    if not tc.findall(W + "p"):
                        etree.SubElement(tc, W + "p")
                tr.addprevious(q)
            tr.getparent().remove(tr)


def _valor(ctx, nombre: str):
    if nombre in ctx:
        return ctx[nombre]
    raise KeyError(f"La plantilla pide {{{{{nombre}}}}}, que el documento no tiene")


def _plano(valor) -> str:
    if isinstance(valor, (Enlace, Negrita)):
        return valor.texto
    if isinstance(valor, (list, tuple)):
        return "".join(_plano(v) for v in valor)
    return "" if valor is None else str(valor)


def _marca_parrafo(e) -> tuple[str, str] | None:
    if e.tag != W + "p":
        return None
    m = RE_MARCA.fullmatch(normal(texto(e)))
    return (m.group(1), m.group(2)) if m else None


# ---------------------------------------------------------------------------------------------------------------------
# Normativa: las normas del título y del curso, en su sitio por fecha
# ---------------------------------------------------------------------------------------------------------------------
def _fecha_parrafo(p, motor: Motor, cat: Catalogo) -> str:
    rels = {r.get("Id"): r.get("Target") for r in motor.pq.rels(motor.parte)}
    for h in p.iter(W + "hyperlink"):
        n = norma_de_url(rels.get(h.get(ooxml.R + "id"), ""), cat)
        if n:
            return n.fecha
    return "9999"


def norma_de_url(url: str, cat: Catalogo) -> Norma | None:
    """La norma del catálogo a la que apunta un enlace del BOE (por su id) o del DOGV (por su ruta ELI)."""
    m = re.search(r"BOE-A-\d{4}-\d+", url)
    if m:
        return cat.normas.get(m.group(0))
    m = re.search(r"/eli/(es-vc/[a-z]+/\d{4}/\d{2}/\d{2}/[^/]+)", url)
    if m:
        for n in cat.normas.values():
            if m.group(1) in n.enlace:
                return n
    return None


def normativa(body, motor: Motor, ctx, cat: Catalogo) -> None:
    for nombre in ("normativa_estatal", "normativa_autonomica"):
        hueco = next(p for p in body.iter(W + "p") if _marca_parrafo(p) == ("*", nombre))
        hermanos = []
        e = hueco.getprevious()
        while e is not None and e.tag == W + "p" and ooxml.numeracion(e) and not ooxml.es_titulo(e):
            hermanos.insert(0, e)
            e = e.getprevious()
        # las comunes que no se aplican al grado del ciclo (RD 500/2024 en GM) fuera
        ficha = ctx["ficha"]
        for h in list(hermanos):
            rels = {r.get("Id"): r.get("Target") for r in motor.pq.rels(motor.parte)}
            ns = [norma_de_url(rels.get(x.get(ooxml.R + "id"), ""), cat) for x in h.iter(W + "hyperlink")]
            n = next((x for x in ns if x), None)
            if n and not n.aplica_a(ficha.sigla, ficha.grado):
                h.getparent().remove(h)
                hermanos.remove(h)
        presentes = set()
        for h in hermanos:
            rels = {r.get("Id"): r.get("Target") for r in motor.pq.rels(motor.parte)}
            for x in h.iter(W + "hyperlink"):
                n = norma_de_url(rels.get(x.get(ooxml.R + "id"), ""), cat)
                if n:
                    presentes.add(n.id)
        nuevos = [(n, segs) for n, segs in ctx[nombre] if n.id not in presentes]
        ancla = (hermanos[0] if hermanos else hueco).getprevious()   # el título del apartado
        copias = motor.repetir_parrafo(hueco, [segs for _n, segs in nuevos], ctx, nombre)
        items = [(_fecha_parrafo(h, motor, cat), h) for h in hermanos]
        items += [(n.fecha, c) for (n, _s), c in zip(nuevos, copias, strict=True)]
        items.sort(key=lambda x: x[0])
        if not items:
            continue
        padre = items[0][1].getparent()
        for _f, p in items:
            padre.remove(p)
        for _f, p in reversed(items):
            ancla.addnext(p)


# ---------------------------------------------------------------------------------------------------------------------
# Retoques
# ---------------------------------------------------------------------------------------------------------------------
def sin_empresa(body) -> None:
    """Módulo sin horas de empresa (el Proyecto): fuera las filas de centro y empresa de la tabla 4 y la columna de
    horas en empresa de la 4.1 (como la programación de 0526)."""
    for tr in list(body.iter(W + "tr")):
        t = normal(texto(tr))
        if t.startswith(("HORAS CENTRO", "HORAS DE EMPRESA")):
            tr.getparent().remove(tr)
    for tbl in body.iter(W + "tbl"):
        filas = tbl.findall(W + "tr")
        if not filas or normal(texto(filas[0].findall(W + "tc")[-1])) != "Horas en empresa":
            continue
        grid = tbl.find(W + "tblGrid").findall(W + "gridCol")
        ancho = int(grid[-1].get(W + "w"))
        grid[0].set(W + "w", str(int(grid[0].get(W + "w")) + ancho))
        grid[-1].getparent().remove(grid[-1])
        for tr in filas:
            tcs = tr.findall(W + "tc")
            tr.remove(tcs[-1])
            w = tcs[0].find(f"{W}tcPr/{W}tcW")
            if w is not None and w.get(W + "w"):
                w.set(W + "w", str(int(w.get(W + "w")) + ancho))


def columna_pct_curso(body, valores: list[str]) -> None:
    """Columna opcional «% del curso (aprox.)» en la tabla 4.1, tras «Horas totales» (CarlosFB, 2026-10-17)."""
    tbl = next(t for t in body.iter(W + "tbl") if t.findall(W + "tr") and
               normal(texto(t.findall(W + "tr")[0].findall(W + "tc")[1])) == "Horas totales")
    grid = tbl.find(W + "tblGrid").findall(W + "gridCol")
    ancho = int(grid[1].get(W + "w"))
    grid[0].set(W + "w", str(max(int(grid[0].get(W + "w")) - ancho, ancho)))
    grid[1].addnext(copy.deepcopy(grid[1]))
    for tr, valor in zip(tbl.findall(W + "tr"), valores, strict=True):
        tcs = tr.findall(W + "tc")
        nueva = copy.deepcopy(tcs[1])
        ooxml.limpiar_ids(nueva)
        ps = nueva.findall(W + "p")
        for p in ps[1:]:
            nueva.remove(p)
        r = next(iter(ps[0].iter(W + "r")), None)
        rpr = r.find(W + "rPr") if r is not None else None
        for x in [x for x in ps[0] if x.tag != W + "pPr"]:
            ps[0].remove(x)
        ps[0].append(ooxml.run(valor, rpr))
        tcs[1].addnext(nueva)


def mantener_titulos(body) -> None:
    """keepNext en los títulos: ninguno se queda solo al pie de una página."""
    for p in body.iter(W + "p"):
        if ooxml.es_titulo(p):
            ooxml.hijo(ooxml.ppr(p), "keepNext", ooxml.ORDEN_PPR)


def actualizar_campos(pq: ooxml.Paquete) -> None:
    ajustes = pq.xml("word/settings.xml")
    ooxml.hijo(ajustes, "updateFields", None, val="true")
    # w:updateFields va antes de w:compat y del resto en el esquema; Word lo acepta en cualquier sitio razonable,
    # pero se coloca tras w:zoom/w:proofState para cumplir la secuencia.
    uf = ajustes.find(W + "updateFields")
    ajustes.remove(uf)
    ancla = None
    for nombre in ("zoom", "removePersonalInformation", "removeDateAndTime", "doNotDisplayPageBoundaries",
                   "displayBackgroundShape", "printPostScriptOverText", "printFractionalCharacterWidth",
                   "printFormsData", "embedTrueTypeFonts", "embedSystemFonts", "saveSubsetFonts",
                   "saveFormsData", "mirrorMargins", "alignBordersAndEdges", "bordersDoNotSurroundHeader",
                   "bordersDoNotSurroundFooter", "gutterAtTop", "hideSpellingErrors", "hideGrammaticalErrors",
                   "activeWritingStyle", "proofState", "formsDesign", "attachedTemplate", "linkStyles",
                   "stylePaneFormatFilter", "stylePaneSortMethod", "documentType", "mailMerge", "revisionView",
                   "trackRevisions", "doNotTrackMoves", "doNotTrackFormatting", "documentProtection",
                   "autoFormatOverride", "styleLockTheme", "styleLockQFSet", "defaultTabStop", "autoHyphenation",
                   "consecutiveHyphenLimit", "hyphenationZone", "doNotHyphenateCaps", "showEnvelope",
                   "summaryLength", "clickAndTypeStyle", "defaultTableStyle", "evenAndOddHeaders",
                   "bookFoldRevPrinting", "bookFoldPrinting", "bookFoldPrintingSheets",
                   "drawingGridHorizontalSpacing", "drawingGridVerticalSpacing",
                   "displayHorizontalDrawingGridEvery", "displayVerticalDrawingGridEvery",
                   "doNotUseMarginsForDrawingGridOrigin", "drawingGridHorizontalOrigin",
                   "drawingGridVerticalOrigin", "doNotShadeFormData", "noPunctuationKerning",
                   "characterSpacingControl", "printTwoOnOne", "strictFirstAndLastChars", "noLineBreaksAfter",
                   "noLineBreaksBefore", "savePreviewPicture", "doNotValidateAgainstSchema",
                   "saveInvalidXml", "ignoreMixedContent", "alwaysShowPlaceholderText", "doNotDemarcateInvalidXml",
                   "saveXmlDataOnly", "useXSLTWhenSaving", "saveThroughXslt", "showXMLTags",
                   "alwaysMergeEmptyNamespace"):
        e = ajustes.find(W + nombre)
        if e is not None:
            ancla = e
    if ancla is not None:
        ancla.addnext(uf)
    else:
        ajustes.insert(0, uf)


MARCA_AGUA = (
    '<w:p xmlns:w="{w}" xmlns:v="{v}" xmlns:o="{o}"><w:pPr><w:pStyle w:val="Encabezado"/></w:pPr><w:r><w:pict>'
    '<v:shapetype id="_x0000_t136" coordsize="21600,21600" o:spt="136" adj="10800" path="m@7,l@8,m@5,21600l@6,21600e">'
    '<v:formulas><v:f eqn="sum #0 0 10800"/><v:f eqn="prod #0 2 1"/><v:f eqn="sum 21600 0 @1"/>'
    '<v:f eqn="sum 0 0 @2"/><v:f eqn="sum 21600 0 @3"/><v:f eqn="if @0 @3 0"/><v:f eqn="if @0 21600 @1"/>'
    '<v:f eqn="if @0 0 @2"/><v:f eqn="if @0 @4 21600"/><v:f eqn="mid @5 @6"/><v:f eqn="mid @8 @5"/>'
    '<v:f eqn="mid @7 @8"/><v:f eqn="mid @6 @7"/><v:f eqn="sum @6 0 @5"/></v:formulas>'
    '<v:path textpathok="t" o:connecttype="custom" o:connectlocs="@9,0;@10,10800;@11,21600;@12,10800" '
    'o:connectangles="270,180,90,0"/><v:textpath on="t" fitshape="t"/>'
    '<o:lock v:ext="edit" text="t" shapetype="t"/></v:shapetype>'
    '<v:shape id="MarcaBorrador" o:spid="_x0000_s2049" type="#_x0000_t136" style="position:absolute;'
    'margin-left:0;margin-top:0;width:468pt;height:117pt;rotation:315;z-index:-251657216;'
    'mso-position-horizontal:center;mso-position-horizontal-relative:margin;mso-position-vertical:center;'
    'mso-position-vertical-relative:margin" o:allowincell="f" fillcolor="silver" stroked="f">'
    '<v:fill opacity=".5"/><v:textpath style="font-family:&quot;Calibri&quot;;font-size:1pt" string="BORRADOR"/>'
    '</v:shape></w:pict></w:r></w:p>')


def marca_borrador(pq: ooxml.Paquete) -> None:
    """Vista previa: «BORRADOR» en diagonal en el encabezado de las páginas con encabezado."""
    xml = MARCA_AGUA.format(w=ooxml.NS["w"], v=ooxml.NS["v"], o=ooxml.NS["o"])
    for n in sorted(pq.partes):
        if re.fullmatch(r"word/header\d+\.xml", n):
            raiz = pq.xml(n)
            if texto(raiz).strip():   # solo el encabezado con contenido (el de la portada está vacío)
                raiz.append(etree.fromstring(xml))


def propiedades(pq: ooxml.Paquete, ficha: Ficha, cuando: dt.date) -> None:
    core = pq.xml("docProps/core.xml")
    ns = {"dc": "http://purl.org/dc/elements/1.1/", "dcterms": "http://purl.org/dc/terms/"}
    t = core.find("dc:title", ns)
    if t is not None:
        t.text = f"Programación didáctica · {ficha.sigla} {ficha.curso} · {ficha.codigo} {ficha.nombre}"
    for nombre in ("created", "modified"):
        e = core.find(f"dcterms:{nombre}", ns)
        if e is not None:
            e.text = f"{cuando.isoformat()}T00:00:00Z"


# ---------------------------------------------------------------------------------------------------------------------
# Generar
# ---------------------------------------------------------------------------------------------------------------------
def generar(prog: dict, cat: Catalogo, curso: dict | None, opciones: Opciones | None = None) -> bytes:
    """El .docx de la programación (sin datos incrustados: los pone incrustar.py al exportar)."""
    opciones = opciones or Opciones()
    meta = metadatos_plantilla()
    ctx = contexto(prog, cat, curso, opciones)
    pq = cargar_plantilla(opciones.idioma)
    motor = Motor(pq, "word/document.xml", str(meta["vinetas"]), cat)
    body = pq.xml("word/document.xml").find(W + "body")

    motor.bloques(body, ctx)
    normativa(body, motor, ctx, cat)
    motor.filas(body, ctx)
    motor.repetidos(body, ctx)
    motor.rellenar(body, ctx)
    if not ctx["con_empresa"]:
        sin_empresa(body)
    if ctx["pct_curso"]:
        columna_pct_curso(body, ctx["pct_curso"])
    for n in sorted(pq.partes):
        if re.fullmatch(r"word/(header|footer)\d+\.xml", n):
            otro = Motor(pq, n, str(meta["vinetas"]))
            otro.rellenar(pq.xml(n), ctx)
    restos = [m.group(0) for m in RE_MARCA.finditer(texto(body))]
    if restos:
        raise ValueError(f"Marcas sin rellenar: {restos[:5]}")
    mantener_titulos(body)
    actualizar_campos(pq)
    if opciones.borrador:
        marca_borrador(pq)
    pq.quitar_relaciones_huerfanas("word/document.xml")
    propiedades(pq, ctx["ficha"], opciones.fecha or dt.date.today())
    return pq.a_bytes()
