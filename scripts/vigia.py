#!/usr/bin/env python3
"""Vigía del catálogo (F5, `.github/workflows/vigia.yml`): revisa las fuentes oficiales y, si algo cambia, abre una PR.

Uso:
  vigia.py revisar [--dias N] [--simulacro] [--informe A.md] [--resultado A.json]
  vigia.py pr --resultado A.json --informe A.md --comprobaciones success|failure
  vigia.py curso                       en julio, agosto y septiembre: incidencia para dar de alta el curso que empieza

`revisar`:
1. Vuelve a leer todas las fuentes de `catalogo/fuentes.yaml` (BOE y DOGV) con una caché vacía y rehace el catálogo con
   `scripts/catalogo.py construir todo`: lo que cambia es lo que dice la fuente, con su huella nueva.
2. Busca normas nuevas que afecten a los ciclos (base: `vigilancia.py` de la guía apuntes-auditoria):
   - referencias posteriores nuevas de cada real decreto (las guarda `construir` en `ciclos/<SIGLA>.yaml`);
   - texto consolidado actualizado de las normas consolidadas de la normativa (página «act.php» del BOE);
   - disposiciones de FP o que citen los reales decretos del catálogo en los sumarios del BOE de los últimos días;
   - normas nuevas en la página de normativa de FP de la Conselleria (así se encontró el Decreto 95/2026).
   Lo ya visto se guarda en `catalogo/vigia.yaml` (punto de partida: la primera vez, nada es nuevo).
3. Clasifica: solo cambia el texto de RA o criterios de un real decreto → se publica solo si pasan las comprobaciones
   (ADR-015). Horas o anexos del DOGV (R2), RA o criterios que aparecen o desaparecen, normas nuevas, referencias
   posteriores, lo que no se ha podido leer → «Revisar a mano»: la PR queda abierta para CarlosFB. **No inventa nada:**
   si una fuente no se puede leer, el catálogo se deja como estaba y va a la PR.
4. Si una fuente no responde, falla (código 2) sin tocar el catálogo.

Peticiones con agente identificable y espacio entre ellas (`catalogo.UA`, `PROGRAMACIONES_PAUSA`).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import yaml  # noqa: E402

import catalogo as receta  # noqa: E402
from programaciones.catalogo import Catalogo, diferencias_catalogo, texto_novedades  # noqa: E402

ESTADO = "vigia.yaml"
URL_CEICE = ("https://ceice.gva.es/es/web/formacion-profesional/"
             "normativa-sobre-ordenacion-y-organizacion-academica-de-los-ciclos-formativos")
RE_CITA_CEICE = [r"(?:DECRETO|Decreto|ORDEN|Orden|RESOLUCIÓN|Resolución|Real Decreto) \d+/\d{4}",
                 r"Resolución de \d{1,2} de [a-záéíóú]+ de \d{4}"]
RE_FP = re.compile(r"Formación Profesional|t[íi]tulos? de Técnico|enseñanzas mínimas|ciclos? formativos?|"
                   r"Grado (?:Medio|Superior)|Catálogo Nacional de Estándares", re.I)
#: Lo que no es ordenación ni currículo, aunque sea del Ministerio de FP.
RE_EXCLUIR = re.compile(r"subvenci|ayudas?\b|becas?\b|premios?\b|convocatoria", re.I)
MINISTERIO = "Ministerio de Educación, Formación Profesional y Deportes"   # lleva «Formación Profesional» en el nombre


class FuenteCaida(Exception):
    """Una fuente oficial no responde: el vigía falla con aviso y no toca el catálogo."""


# ---------------------------------------------------------------------------------------------------------------------
# Red
# ---------------------------------------------------------------------------------------------------------------------
def pedir(url: str, json_api: bool = False) -> bytes:
    receta.esperar_turno()
    cab = dict(receta.UA, **({"Accept": "application/json"} if json_api else {}))
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return b""
        raise FuenteCaida(f"{url}: respuesta {e.code}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise FuenteCaida(f"{url}: {e}") from e


def texto_html(b: bytes) -> str:
    t = b.decode("utf-8", "ignore")
    t = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()


# ---------------------------------------------------------------------------------------------------------------------
# Normas nuevas (lo que `construir` no ve)
# ---------------------------------------------------------------------------------------------------------------------
def consolidados(normativa: dict, pedir=pedir) -> dict[str, str]:
    """Normas de la normativa con texto consolidado (enlace «act.php»): fecha de su última actualización y vigencia."""
    out = {}
    for n in normativa.get("normas", []):
        if "act.php" not in n.get("enlace", ""):
            continue
        t = texto_html(pedir(f"https://www.boe.es/buscar/act.php?id={n['id']}"))
        f = re.search(r"Última actualización,? publicada el (\d{2})/(\d{2})/(\d{4})", t)
        meta = pedir(f"https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{n['id']}/metadatos", True)
        vigente = "?"
        if meta:
            m = (json.loads(meta).get("data") or [{}])[0]
            vigente = "vigente" if (m.get("estatus_derogacion"), m.get("estatus_anulacion")) == ("N", "N") \
                else "NO vigente"
        out[n["id"]] = f"{f.group(3)}-{f.group(2)}-{f.group(1)}|{vigente}" if f else f"?|{vigente}"
    return out


def _lista(x) -> list:
    return x if isinstance(x, list) else [x] if x else []


def _items(diario):
    """(disposición, código de la sección, departamento) de un sumario del BOE (API de datos abiertos)."""
    for d in _lista(diario):
        for sec in _lista(d.get("seccion")):
            for dep in _lista(sec.get("departamento")):
                items = _lista(dep.get("item"))
                for ep in _lista(dep.get("epigrafe")):
                    items += _lista(ep.get("item"))
                for it in items:
                    if str(it.get("identificador", "")).startswith("BOE-A"):
                        yield it, str(sec.get("codigo", "")), str(dep.get("nombre", ""))


def sumarios_boe(citas: list[str], dias: int, hoy: dt.date, pedir=pedir) -> dict[str, dict]:
    """Disposiciones de los sumarios del BOE de los últimos `dias` que citan un real decreto del catálogo o que son
    disposiciones generales (sección I) de FP."""
    out = {}
    for k in range(dias):
        dia = hoy - dt.timedelta(days=k)
        crudo = pedir(f"https://www.boe.es/datosabiertos/api/boe/sumario/{dia:%Y%m%d}", True)
        if not crudo:        # domingo o festivo: no hay BOE
            continue
        diario = json.loads(crudo).get("data", {}).get("sumario", {}).get("diario", [])
        for item, seccion, departamento in _items(diario):
            t = item["titulo"]
            cita = next((c for c in citas if re.search(rf"\b{re.escape(c)}\b", t)), None)
            de_fp = seccion == "1" and "EDUCACI" in departamento.upper() and not RE_EXCLUIR.search(t) \
                and RE_FP.search(t.replace(MINISTERIO, ""))
            if cita or de_fp:
                out[item["identificador"]] = {"titulo": t, "fecha": dia.isoformat(),
                                              "enlace": f"https://www.boe.es/buscar/doc.php?id={item['identificador']}",
                                              "motivo": f"cita el {cita}" if cita else "disposición general de FP"}
    return out


def citas_ceice(pedir=pedir) -> list[str]:
    t = texto_html(pedir(URL_CEICE))
    if not t:
        raise FuenteCaida(f"{URL_CEICE}: página vacía")
    return sorted({m.group(0) for rx in RE_CITA_CEICE for m in re.finditer(rx, t)})


def citas_del_catalogo(cat: Catalogo) -> list[str]:
    """«Real Decreto 1127/2010»…: las normas estatales del catálogo, para buscarlas en los sumarios."""
    return sorted({n.cita_corta for n in cat.normas.values() if n.diario == "BOE" and "/" in n.cita_corta})


# ---------------------------------------------------------------------------------------------------------------------
# Revisión
# ---------------------------------------------------------------------------------------------------------------------
@dataclass
class Resultado:
    cambios: bool = False
    automatica: bool = False
    simulacro: bool = False
    titulo: str = ""
    firma: str = ""
    fecha: str = ""
    manual: list[str] = field(default_factory=list)
    fuentes: list[str] = field(default_factory=list)
    archivos: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)     # lo que no impide revisar (una fuente auxiliar caída)


def _yaml(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.is_file() else None


def _huellas(carpeta: Path) -> dict[str, dict]:
    return {f["id"]: f for f in (_yaml(carpeta / "fuentes.yaml") or {}).get("fuentes", [])}


def _archivos(carpeta: Path) -> dict[str, str]:
    return {p.relative_to(carpeta).as_posix(): p.read_text(encoding="utf-8") for p in sorted(carpeta.rglob("*.yaml"))}


def construir_real() -> None:
    """`scripts/catalogo.py construir todo` con una caché vacía: todo se vuelve a descargar."""
    receta.SIN_RED = False
    os.environ["PROGRAMACIONES_CACHE"] = tempfile.mkdtemp(prefix="vigia-fuentes-")
    receta.Construccion().construir(list(receta.CICLOS))


def huellas_descargadas() -> dict[str, str]:
    """Huella de lo que se ha llegado a descargar (para decir qué fuente cambió aunque no se haya podido leer)."""
    cache = Path(os.environ.get("PROGRAMACIONES_CACHE", ""))
    out = {}
    for p in cache.rglob("*") if cache.is_dir() else []:
        if p.is_file():
            out[p.stem] = receta.huella_bytes(p.read_bytes())
    return out


def clasificar(antes: Path, despues: Path, nov) -> list[str]:
    """Lo que no se publica solo: tiene que revisarlo CarlosFB (R2, R7, ADR-017)."""
    manual = []
    fa, fb = _huellas(antes), _huellas(despues)
    for i in sorted(set(fa) & set(fb)):
        if fa[i]["huella"] != fb[i]["huella"] and fb[i]["tipo"] == "dogv":
            manual.append(f"El PDF del DOGV {i} ha cambiado: los anexos del DOGV se revisan a mano (R2)")
    for i in sorted(set(fb) - set(fa)):
        manual.append(f"Fuente nueva en el catálogo: {i}")
    for linea in nov.normas:
        if not linea.startswith("Texto publicado distinto"):
            manual.append(linea)
    for (sigla, curso, codigo), cambios in sorted(nov.modulos.items()):
        for c in cambios:
            if not (c.endswith("enunciado nuevo") or c.endswith(") cambia")):
                manual.append(f"{sigla} {curso} - {codigo}: {c}")
    for p in sorted((despues / "ciclos").glob("*.yaml")):
        a, b = _yaml(antes / "ciclos" / p.name) or {}, _yaml(p) or {}
        nuevas = {x["id"] for x in b.get("rd", {}).get("posteriores", [])} - \
            {x["id"] for x in a.get("rd", {}).get("posteriores", [])}
        for x in b.get("rd", {}).get("posteriores", []):
            if x["id"] in nuevas:
                manual.append(f"Referencia posterior nueva del real decreto de {p.stem}: {x['id']} «{x['relacion']} "
                              f"{x['texto']}» (revisar si reescribe módulos: receta de scripts/catalogo.py)")
        a2, b2 = receta.sin_fechas(a), receta.sin_fechas(b)
        otros = sorted(k for k in set(a2) | set(b2) if k not in ("rd", "modulos", "fuentes") and a2.get(k) != b2.get(k))
        if otros:
            manual.append(f"Cambia el ciclo {p.stem}: {', '.join(otros)}")
    for p in sorted((despues / "modulos").glob("*.yaml")):
        a, b = _yaml(antes / "modulos" / p.name) or {}, _yaml(p) or {}
        a2, b2 = receta.sin_fechas(a), receta.sin_fechas(b)
        otros = sorted(k for k in set(a2) | set(b2) if k not in ("ra", "fuente") and a2.get(k) != b2.get(k))
        if otros:
            manual.append(f"Cambia el módulo {p.stem}: {', '.join(otros)}")
    return list(dict.fromkeys(manual))


def novedades_externas(cat: Catalogo, estado: dict, dias: int, hoy: dt.date, pedir=pedir) \
        -> tuple[list[str], dict, list[str]]:
    """Normas nuevas fuera de lo que lee `construir`. Devuelve (lo que hay que revisar a mano, estado nuevo, avisos)."""
    manual, avisos = [], []
    nuevo = dict(estado)
    normativa = _yaml(cat.carpeta / "normativa.yaml") or {}
    cons = consolidados(normativa, pedir)
    for i, v in sorted(cons.items()):
        antes = (estado.get("consolidados") or {}).get(i)
        if "consolidados" in estado and antes != v:
            manual.append(f"Texto consolidado de {cat.norma(i).cita_corta} actualizado ({antes or '—'} → {v}): "
                          f"https://www.boe.es/buscar/act.php?id={i}")
    nuevo["consolidados"] = cons
    vistas = dict(estado.get("boe") or {})
    for i, d in sorted(sumarios_boe(citas_del_catalogo(cat), dias, hoy, pedir).items()):
        if i not in vistas and i not in cat.normas:
            if "boe" in estado:
                manual.append(f"BOE {d['fecha']}: [{d['titulo']}]({d['enlace']}) ({d['motivo']})")
            vistas[i] = {"titulo": d["titulo"], "fecha": d["fecha"]}
    nuevo["boe"] = dict(sorted(vistas.items()))
    # La página de la Conselleria es una fuente auxiliar (para encontrar normas nuevas), no del catálogo: si no responde
    # tras tres intentos, se avisa y se sigue con lo que ya se había visto; el catálogo no depende de ella.
    citas = None
    for _ in range(3):
        try:
            citas = citas_ceice(pedir)
            break
        except FuenteCaida as e:
            fallo = str(e)
    if citas is None:
        avisos.append(f"La página de normativa de FP de la Conselleria no ha respondido ({fallo}): esta semana no se "
                      "ha podido buscar en ella normas nuevas. Se vuelve a mirar la próxima.")
    else:
        if "ceice" in estado:
            for c in sorted(set(citas) - set(estado["ceice"])):
                manual.append(f"Página de normativa de FP de la Conselleria: «{c}» nuevo ({URL_CEICE})")
        nuevo["ceice"] = citas
    return manual, nuevo, avisos


def escribir_estado(p: Path, estado: dict) -> None:
    datos = {"formato": "vigia/1", **{k: estado[k] for k in ("consolidados", "boe", "ceice") if k in estado}}
    texto = ("# Lo que el vigía ya ha visto (scripts/vigia.py): normas consolidadas, disposiciones del BOE y citas de la "
             "Conselleria. No se edita a mano.\n" + yaml.safe_dump(datos, allow_unicode=True, sort_keys=False, width=10_000))
    if not p.is_file() or p.read_text(encoding="utf-8") != texto:
        p.write_text(texto, encoding="utf-8")


SIMULACRO = ("0517", 1, "a", " (simulacro del vigía: cambio ficticio)")


def simular(carpeta: Path) -> None:
    """Simulacro (workflow_dispatch): un cambio ficticio en un criterio, como si el BOE lo hubiera cambiado."""
    modulo, n, letra, sufijo = SIMULACRO
    p = carpeta / "modulos" / f"{modulo}.yaml"
    m = _yaml(p)
    crit = next(c for c in next(r for r in m["ra"] if r["n"] == n)["criterios"] if c["letra"] == letra)
    crit["texto"]["es"] += sufijo
    if "corregido" in crit:
        crit["corregido"]["es"] += sufijo
    receta.escribir_yaml(p, m)


def revisar(dias: int = 8, simulacro: bool = False, hoy: dt.date | None = None, construir=construir_real,
            pedir=pedir, carpeta: Path | None = None) -> tuple[Resultado, str]:
    """Hace la revisión entera y devuelve (resultado, informe en Markdown para la PR)."""
    carpeta = Path(carpeta or receta.CATALOGO)
    hoy = hoy or dt.date.today()
    tmp = Path(tempfile.mkdtemp(prefix="vigia-antes-"))
    antes = tmp / "catalogo"
    shutil.copytree(carpeta, antes)
    manual: list[str] = []

    def restaurar():
        shutil.rmtree(carpeta)
        shutil.copytree(antes, carpeta)

    try:
        construir()
    except FuenteCaida:
        restaurar()
        raise
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        restaurar()
        raise FuenteCaida(str(e)) from e
    except (SystemExit, Exception) as e:  # noqa: BLE001 - lo que el lector no sabe leer: a mano, sin inventar
        restaurar()
        cambiadas = [f"{i} (huella nueva {h[:19]}…)" for i, h in sorted(huellas_descargadas().items())
                     if i in _huellas(antes) and _huellas(antes)[i]["huella"] != h]
        manual.append(f"No se ha podido rehacer el catálogo desde las fuentes: {e}. El catálogo se queda como estaba."
                      + (f" Fuentes con huella distinta: {', '.join(cambiadas)}" if cambiadas else ""))
    if simulacro:
        simular(carpeta)
        receta.actualizar_version(carpeta, hoy.isoformat())

    estado = _yaml(carpeta / ESTADO) or {}
    externas, estado_nuevo, avisos = novedades_externas(Catalogo(carpeta), estado, dias, hoy, pedir)
    manual += externas
    escribir_estado(carpeta / ESTADO, estado_nuevo)

    nov = diferencias_catalogo(Catalogo(antes), Catalogo(carpeta))
    manual = clasificar(antes, carpeta, nov) + manual
    va, vb = _archivos(antes), _archivos(carpeta)
    cambiados = sorted(r for r in set(va) | set(vb) if va.get(r) != vb.get(r))
    fa, fb = _huellas(antes), _huellas(carpeta)
    fuentes = [f"[{fb[i]['titulo']['es']}]({fb[i]['enlace']}) · {i} · huella `{fa[i]['huella'][7:19]}…` → "
               f"`{fb[i]['huella'][7:19]}…`" for i in sorted(set(fa) & set(fb)) if fa[i]["huella"] != fb[i]["huella"]]
    del_catalogo = [r for r in cambiados if r != ESTADO]
    res = Resultado(fecha=hoy.isoformat(), simulacro=simulacro, manual=manual, fuentes=fuentes, archivos=cambiados,
                    avisos=avisos)
    res.cambios = bool(cambiados or manual)
    res.automatica = bool(del_catalogo) and not manual and not simulacro
    firma = hashlib.sha256(json.dumps([manual, {r: vb.get(r) for r in cambiados}], ensure_ascii=False,
                                      sort_keys=True).encode()).hexdigest()
    res.firma = firma
    if simulacro:
        res.titulo = "[Simulacro] Currículo: cambio ficticio en un criterio de 0517 (no se fusiona)"
    elif nov.modulos:
        afect = sorted({f"{s} {c}-{m}" for s, c, m in nov.modulos})
        res.titulo = f"Currículo: cambios en {', '.join(afect[:4])}{'…' if len(afect) > 4 else ''}"
    elif manual:
        res.titulo = "Currículo: normativa que revisar a mano"
    else:
        res.titulo = "Currículo: huellas y estado del vigía"
    shutil.rmtree(tmp, ignore_errors=True)
    return res, informe(res, nov)


def informe(res: Resultado, nov) -> str:
    md = [f"## Vigía del catálogo · {res.fecha}", ""]
    if res.simulacro:
        md += ["> **Simulacro** lanzado a mano para probar el recorrido: el cambio es ficticio. Esta PR no se fusiona: se "
              "cierra sin publicar nada.", ""]
    if res.automatica:
        md += ["**Se publica solo** si pasan las comprobaciones (esquema, enlaces vivos y pruebas, ADR-015): solo cambia "
              "el texto de RA o criterios de un real decreto. Cada profesor lo acepta en su programación viendo la "
              "diferencia.", ""]
    elif res.manual:
        md += ["**Revisar a mano** (CarlosFB): hay algo que el vigía no publica solo. Pasos en docs/OPERACIONES.md, «Cuando "
              "el vigía abre una PR».", ""]
    md += ["### Normas y documentos que han cambiado", ""]
    md += [f"- {x}" for x in res.fuentes] or ["- Ningún documento de `fuentes.yaml` tiene la huella distinta."]
    md += ["", "### Diferencias (lo que verá el profesor en «Cambios en el currículo»)", "", texto_novedades(nov), ""]
    if res.manual:
        md += ["### Revisar a mano", "", *[f"- [ ] {x}" for x in res.manual], ""]
    if res.avisos:
        md += ["### Avisos", "", *[f"- {x}" for x in res.avisos], ""]
    md += ["### Archivos", "", *[f"- `catalogo/{r}`" for r in res.archivos], "",
          "Nada de esto se ha escrito a mano: lo que la fuente no dice de forma fiable va arriba, en «Revisar a mano»; "
          "el vigía no inventa RA, criterios ni horas.", "",
          f"<!-- vigia:firma={res.firma} modo={'auto' if res.automatica else 'manual'} -->"]
    return "\n".join(md) + "\n"


# ---------------------------------------------------------------------------------------------------------------------
# PR (en la CI, con gh)
# ---------------------------------------------------------------------------------------------------------------------
def _ejecutar(orden: list[str], capturar: bool = False) -> str:
    r = subprocess.run(orden, check=True, text=True, capture_output=capturar)
    return (r.stdout or "").strip() if capturar else ""


def abrir_pr(res: dict, informe_md: Path, comprobaciones: str, ejecutar=_ejecutar) -> str:
    """Rama, commit, PR y, si es automática y las comprobaciones pasan, fusión y publicación (`catalogo.yml`)."""
    if not res["cambios"]:
        print("Vigía: sin cambios")
        return "sin_cambios"
    abiertas = json.loads(ejecutar(["gh", "pr", "list", "--label", "vigia", "--state", "open", "--json",
                                    "number,body,isDraft"], True) or "[]")
    repetida = next((p for p in abiertas if f"vigia:firma={res['firma']}" in (p.get("body") or "")), None)
    if repetida:
        print(f"Vigía: los mismos cambios ya están en la PR #{repetida['number']}")
        return "repetida"
    rama = f"vigia/{res['fecha']}-{res['firma'][:8]}"
    ejecutar(["git", "switch", "-c", rama])
    ejecutar(["git", "add", "--", "catalogo"])
    ejecutar(["git", "commit", "-m", f"chore(catalogo): vigía {res['fecha']}: {res['titulo']}"])
    ejecutar(["git", "push", "-u", "origin", rama])
    ejecutar(["gh", "label", "create", "vigia", "--color", "C9A227", "--description", "PR del vigía del catálogo",
              "--force"])
    orden = ["gh", "pr", "create", "--base", "main", "--head", rama, "--title", res["titulo"], "--body-file",
             str(informe_md), "--label", "vigia"]
    if res.get("simulacro"):
        orden.append("--draft")
    url = ejecutar(orden, True)
    numero = url.rstrip("/").rsplit("/", 1)[-1]
    if not res.get("simulacro"):
        for p in abiertas:
            if not p.get("isDraft"):
                ejecutar(["gh", "pr", "close", str(p["number"]), "--delete-branch", "--comment",
                          f"Sustituida por #{numero}, con lo que ha visto el vigía después."])
    if res["automatica"] and comprobaciones == "success":
        ejecutar(["gh", "pr", "merge", numero, "--squash", "--delete-branch"])
        ejecutar(["gh", "workflow", "run", "catalogo.yml", "--ref", "main"])
        print(f"Vigía: PR #{numero} fusionada; catalogo.yml firma y publica")
        return "fusionada"
    motivo = "las comprobaciones automáticas han fallado" if comprobaciones != "success" else "hay que revisarla a mano"
    if not res.get("simulacro"):
        ejecutar(["gh", "pr", "comment", numero, "--body", f"Queda abierta para CarlosFB: {motivo}."])
    print(f"Vigía: PR #{numero} abierta ({motivo})")
    return "abierta"


def incidencia_curso(hoy: dt.date, carpeta: Path, ejecutar=_ejecutar) -> str:
    """En julio, agosto y septiembre, si el curso que empieza no está dado de alta, una incidencia (una sola)."""
    if hoy.month not in (7, 8, 9):
        return ""
    curso = f"{hoy.year}-{hoy.year + 1}"
    if (carpeta / "cursos" / f"{curso}.yaml").is_file():
        return ""
    titulo = f"Dar de alta el curso {curso}: resolución de instrucciones, fechas y FE"
    abiertas = json.loads(ejecutar(["gh", "issue", "list", "--state", "open", "--search", titulo, "--json", "title"],
                                   True) or "[]")
    if any(i["title"] == titulo for i in abiertas):
        return ""
    ejecutar(["gh", "issue", "create", "--title", titulo, "--body",
              f"Falta `catalogo/cursos/{curso}.yaml`: fechas de evaluación, ordinaria y extraordinaria, periodos de "
              "formación en empresa y la resolución de instrucciones del DOGV de julio (docs/OPERACIONES.md, «Alta del "
              "curso escolar»). Sin él, el documento enseña «pendiente» y la definitiva espera (V-11)."])
    return titulo


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    r = sub.add_parser("revisar")
    r.add_argument("--dias", type=int, default=8)
    r.add_argument("--simulacro", action="store_true")
    r.add_argument("--informe", type=Path, default=Path("vigia-informe.md"))
    r.add_argument("--resultado", type=Path, default=Path("vigia-resultado.json"))
    p = sub.add_parser("pr")
    p.add_argument("--informe", type=Path, required=True)
    p.add_argument("--resultado", type=Path, required=True)
    p.add_argument("--comprobaciones", default="skipped")
    sub.add_parser("curso")
    a = ap.parse_args()
    if a.orden == "revisar":
        try:
            res, md = revisar(a.dias, a.simulacro)
        except FuenteCaida as e:
            print(f"::error::Una fuente oficial no responde: {e}. El catálogo no se toca.")
            return 2
        a.informe.write_text(md, encoding="utf-8")
        a.resultado.write_text(json.dumps(asdict(res), ensure_ascii=False, indent=1), encoding="utf-8")
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
                f.write(f"cambios={'true' if res.cambios else 'false'}\n")
        for x in res.avisos:
            print(f"::warning::{x}")
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
                f.write(md if res.cambios else f"## Vigía del catálogo · {res.fecha}\n\nSin cambios en las fuentes."
                        + "".join(f"\n\n> {x}" for x in res.avisos) + "\n")
        print(md if res.cambios else "Vigía: sin cambios en las fuentes")
        return 0
    if a.orden == "pr":
        abrir_pr(json.loads(a.resultado.read_text(encoding="utf-8")), a.informe, a.comprobaciones)
        return 0
    t = incidencia_curso(dt.date.today(), receta.CATALOGO)
    print(f"Incidencia: {t}" if t else "Curso escolar: nada que avisar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
