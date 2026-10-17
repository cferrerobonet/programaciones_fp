"""Vigía del catálogo (scripts/vigia.py) con fuentes falsas: nunca toca la red, git ni GitHub de verdad.

La prueba de cierre de F5 está al final: un cambio simulado en una norma recorre todo el camino (vigía → PR → catálogo
firmado → la app avisa → la profesora acepta en su programación)."""
import base64
import datetime as dt
import json
import shutil
from dataclasses import asdict

import pytest
import yaml
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

import catalogo as receta
import vigia
from programaciones import catalogo_remoto as cr
from programaciones import firma
from programaciones.catalogo import Catalogo

HOY = dt.date(2030, 1, 15)
RD_SEA = "BOE-A-2010-15355"


class FuentesFalsas:
    """BOE, API de datos abiertos y página de la Conselleria, falsos. `sumarios`: fecha → [(id, título, sección,
    departamento)]."""

    def __init__(self):
        self.sumarios = {}
        self.ceice = ["Decreto 95/2026, de 19 de junio"]
        self.consolidado = "08/06/2024"
        self.pedidas = []

    def __call__(self, url, json_api=False):
        self.pedidas.append(url)
        if "act.php" in url:
            return f"<p>Última actualización publicada el {self.consolidado}</p>".encode()
        if "/metadatos" in url:
            return json.dumps({"data": [{"estatus_derogacion": "N", "estatus_anulacion": "N"}]}).encode()
        if "/sumario/" in url:
            dia = dt.datetime.strptime(url.rsplit("/", 1)[1], "%Y%m%d").date()
            if dia not in self.sumarios:
                return b""
            deps = [{"nombre": dep, "item": [{"identificador": i, "titulo": t}]}
                    for i, t, _sec, dep in self.sumarios[dia]]
            secs = [{"codigo": sec, "departamento": [d]} for (_i, _t, sec, _dep), d in zip(self.sumarios[dia], deps)]
            return json.dumps({"data": {"sumario": {"diario": [{"seccion": secs}]}}}).encode()
        if "ceice.gva.es" in url:
            return ("<html>" + " ".join(f"<p>{c}</p>" for c in self.ceice) + "</html>").encode()
        raise AssertionError(url)


@pytest.fixture
def repo(tmp_path):
    """Copia del catálogo del repositorio, con el estado del vigía de partida hecho con las fuentes falsas."""
    carpeta = tmp_path / "catalogo"
    shutil.copytree(Catalogo().carpeta, carpeta, ignore=shutil.ignore_patterns("vigia.yaml"))
    fuentes = FuentesFalsas()
    _, estado = vigia.novedades_externas(Catalogo(carpeta), {}, 3, HOY, fuentes)
    vigia.escribir_estado(carpeta / vigia.ESTADO, estado)
    return carpeta, fuentes


def boe_cambia_un_criterio(carpeta, texto="Se ha cambiado un criterio en el BOE (ficticio)."):
    """Lo que haría `construir` si el BOE cambiara el criterio b) del RA3 de 0517: texto nuevo y huella nueva."""
    def construir():
        p = carpeta / "fuentes.yaml"
        f = yaml.safe_load(p.read_text(encoding="utf-8"))
        nueva = "sha256:" + "a" * 64
        next(x for x in f["fuentes"] if x["id"] == RD_SEA)["huella"] = nueva
        receta.escribir_yaml(p, f)
        p = carpeta / "modulos" / "0517.yaml"
        m = yaml.safe_load(p.read_text(encoding="utf-8"))
        m["ra"][2]["criterios"][1]["texto"]["es"] = texto
        m["fuente"]["huella"] = nueva
        receta.escribir_yaml(p, m)
        receta.actualizar_version(carpeta, HOY.isoformat())
    return construir


def revisar(carpeta, fuentes, construir=lambda: None, **k):
    return vigia.revisar(dias=3, hoy=HOY, construir=construir, pedir=fuentes, carpeta=carpeta, **k)


class GitHubFalso:
    """git y gh simulados: guarda las órdenes y contesta como gh."""

    def __init__(self, abiertas=()):
        self.ordenes = []
        self.abiertas = list(abiertas)

    def __call__(self, orden, capturar=False):
        self.ordenes.append(orden)
        if orden[:3] == ["gh", "pr", "list"]:
            return json.dumps(self.abiertas)
        if orden[:3] == ["gh", "pr", "create"]:
            return "https://github.com/cferrerobonet/programaciones_fp/pull/42"
        if orden[:3] == ["gh", "issue", "list"]:
            return "[]"
        return ""

    def hay(self, *inicio):
        return any(o[:len(inicio)] == list(inicio) for o in self.ordenes)


# ---------------------------------------------------------------------------------------------------------------------
# Revisión
# ---------------------------------------------------------------------------------------------------------------------
def test_sin_cambios_en_las_fuentes_no_hay_nada_que_hacer(repo):
    carpeta, fuentes = repo
    res, _ = revisar(carpeta, fuentes)
    assert not res.cambios and res.manual == [] and res.archivos == []


def test_la_primera_vez_todo_es_punto_de_partida(tmp_path):
    carpeta = tmp_path / "catalogo"
    shutil.copytree(Catalogo().carpeta, carpeta, ignore=shutil.ignore_patterns("vigia.yaml"))
    fuentes = FuentesFalsas()
    fuentes.sumarios[HOY] = [("BOE-A-2030-1", "Real Decreto 1/2030 por el que se modifica el Real Decreto 1127/2010 "
                                              "(ficticio)", "1", "MINISTERIO DE EDUCACIÓN")]
    res, _ = revisar(carpeta, fuentes)
    assert res.manual == [] and res.archivos == ["vigia.yaml"]


def test_un_criterio_cambiado_en_el_boe_se_publica_solo(repo):
    carpeta, fuentes = repo
    res, md = revisar(carpeta, fuentes, boe_cambia_un_criterio(carpeta))
    assert res.cambios and res.automatica and res.manual == []
    assert "RA3 de 0517: criterio b) cambia" in md and "SEA 2 - 0517" in md
    assert RD_SEA in md and "huella" in md and "→" in md, "qué norma cambia, con su huella nueva"
    assert "modulos/0517.yaml" in md and "**Se publica solo**" in md
    assert Catalogo(carpeta).version == "2030.01.15"


def test_horas_y_anexos_del_dogv_van_a_mano(repo):
    """R2: lo que sale de un PDF del DOGV (horas, anexos) lo revisa siempre CarlosFB."""
    carpeta, fuentes = repo

    def construir():
        p = carpeta / "fuentes.yaml"
        f = yaml.safe_load(p.read_text(encoding="utf-8"))
        next(x for x in f["fuentes"] if x["id"] == "DOGV-C-2026-21170")["huella"] = "sha256:" + "b" * 64
        receta.escribir_yaml(p, f)
        p = carpeta / "ciclos" / "SEA.yaml"
        c = yaml.safe_load(p.read_text(encoding="utf-8"))
        fila = next(m for m in c["modulos"] if m["codigo"] == "0517")
        fila["h_anuales"] -= 1
        receta.escribir_yaml(p, c)
        receta.actualizar_version(carpeta, HOY.isoformat())

    res, md = revisar(carpeta, fuentes, construir)
    assert res.cambios and not res.automatica
    assert any("DOGV-C-2026-21170" in x and "R2" in x for x in res.manual)
    assert any("Horas de 0517" in x for x in res.manual) and "Revisar a mano" in md


def test_un_ra_que_aparece_va_a_mano(repo):
    carpeta, fuentes = repo

    def construir():
        p = carpeta / "modulos" / "0517.yaml"
        m = yaml.safe_load(p.read_text(encoding="utf-8"))
        m["ra"].append({"n": 7, "texto": {"es": "RA ficticio."}, "criterios": [{"letra": "a", "texto": {"es": "x"}}]})
        receta.escribir_yaml(p, m)

    res, _ = revisar(carpeta, fuentes, construir)
    assert not res.automatica and any("RA7 de 0517: nuevo" in x for x in res.manual)


@pytest.mark.parametrize("titulo, seccion, departamento, va", [
    ("Real Decreto 1/2030, por el que se modifica el Real Decreto 1127/2010 (ficticio)", "3", "OTRO", True),
    ("Orden ficticia por la que se regula la Formación Profesional", "1", "MINISTERIO DE EDUCACIÓN, FORMACIÓN "
     "PROFESIONAL Y DEPORTES", True),
    ("Real Decreto ficticio de subvenciones en el ámbito de la formación profesional", "1", "MINISTERIO DE EDUCACIÓN",
     False),
    ("Real Decreto ficticio en el ámbito del Ministerio de Educación, Formación Profesional y Deportes", "1",
     "MINISTERIO DE EDUCACIÓN", False),
])
def test_normas_nuevas_en_los_sumarios_del_boe(repo, titulo, seccion, departamento, va):
    carpeta, fuentes = repo
    fuentes.sumarios[HOY - dt.timedelta(days=1)] = [("BOE-A-2030-77", titulo, seccion, departamento)]
    res, md = revisar(carpeta, fuentes)
    assert (any("BOE-A-2030-77" in x for x in res.manual)) is va
    if va:
        assert not res.automatica and "Revisar a mano" in md
        res2, _ = revisar(carpeta, fuentes)
        assert res2.manual == [], "lo ya visto no vuelve a salir"


def test_norma_nueva_en_la_pagina_de_la_conselleria(repo):
    carpeta, fuentes = repo
    fuentes.ceice.append("DECRETO 1/2030, de 2 de enero (ficticio)")
    res, _ = revisar(carpeta, fuentes)
    assert any("DECRETO 1/2030" in x for x in res.manual)


def test_texto_consolidado_actualizado(repo):
    carpeta, fuentes = repo
    fuentes.consolidado = "10/01/2030"
    res, _ = revisar(carpeta, fuentes)
    assert any("Texto consolidado" in x and "2030-01-10" in x for x in res.manual)


def test_si_una_fuente_no_responde_falla_y_no_toca_el_catalogo(repo):
    carpeta, fuentes = repo
    antes = {p.name: p.read_bytes() for p in (carpeta / "modulos").glob("*.yaml")}

    def construir():
        boe_cambia_un_criterio(carpeta)()
        raise vigia.FuenteCaida("https://www.boe.es/…: respuesta 503")

    with pytest.raises(vigia.FuenteCaida):
        revisar(carpeta, fuentes, construir)
    assert {p.name: p.read_bytes() for p in (carpeta / "modulos").glob("*.yaml")} == antes


def test_lo_que_no_se_sabe_leer_va_a_mano_sin_inventar(repo):
    carpeta, fuentes = repo
    antes = (carpeta / "modulos" / "0517.yaml").read_text(encoding="utf-8")

    def construir():
        boe_cambia_un_criterio(carpeta)()
        raise SystemExit("BOE-A-2010-15355: no encuentro «^anexo I$»")

    res, md = revisar(carpeta, fuentes, construir)
    assert (carpeta / "modulos" / "0517.yaml").read_text(encoding="utf-8") == antes, "el catálogo se queda como estaba"
    assert not res.automatica and any("No se ha podido rehacer" in x and "anexo I" in x for x in res.manual)
    assert "no inventa" in md


def test_simulacro_va_a_una_pr_en_borrador_que_no_se_fusiona(repo, tmp_path):
    carpeta, fuentes = repo
    res, md = revisar(carpeta, fuentes, simulacro=True)
    assert res.simulacro and not res.automatica and "Simulacro" in md and res.titulo.startswith("[Simulacro]")
    assert "RA1 de 0517: criterio a) cambia" in md
    gh = GitHubFalso(abiertas=[{"number": 7, "body": "otra", "isDraft": False}])
    informe = tmp_path / "informe.md"
    informe.write_text(md, encoding="utf-8")
    assert vigia.abrir_pr(asdict(res), informe, "success", gh) == "abierta"
    crear = next(o for o in gh.ordenes if o[:3] == ["gh", "pr", "create"])
    assert "--draft" in crear and not gh.hay("gh", "pr", "merge") and not gh.hay("gh", "pr", "close")


# ---------------------------------------------------------------------------------------------------------------------
# PR
# ---------------------------------------------------------------------------------------------------------------------
def _resultado(**k):
    return {"cambios": True, "automatica": True, "simulacro": False, "titulo": "Currículo: ficticio", "firma": "f" * 64,
            "fecha": "2030-01-15", **k}


def test_pr_automatica_con_las_comprobaciones_en_verde_se_fusiona_y_publica(tmp_path):
    gh = GitHubFalso(abiertas=[{"number": 7, "body": "<!-- vigia:firma=otra -->", "isDraft": False}])
    assert vigia.abrir_pr(_resultado(), tmp_path / "i.md", "success", gh) == "fusionada"
    assert gh.hay("git", "switch", "-c", "vigia/2030-01-15-ffffffff")
    assert gh.hay("git", "add", "--", "catalogo"), "solo el catálogo"
    assert gh.hay("gh", "pr", "close", "7"), "la anterior se sustituye"
    assert gh.hay("gh", "pr", "merge", "42", "--squash")
    assert gh.hay("gh", "workflow", "run", "catalogo.yml")


@pytest.mark.parametrize("res, comprobaciones", [(_resultado(automatica=False), "success"),
                                                 (_resultado(), "failure")])
def test_pr_que_queda_abierta_para_carlosfb(tmp_path, res, comprobaciones):
    gh = GitHubFalso()
    assert vigia.abrir_pr(res, tmp_path / "i.md", comprobaciones, gh) == "abierta"
    assert not gh.hay("gh", "pr", "merge") and not gh.hay("gh", "workflow", "run")
    assert gh.hay("gh", "pr", "comment", "42")


def test_los_mismos_cambios_no_abren_otra_pr(tmp_path):
    gh = GitHubFalso(abiertas=[{"number": 7, "body": f"… <!-- vigia:firma={'f' * 64} modo=auto -->", "isDraft": False}])
    assert vigia.abrir_pr(_resultado(), tmp_path / "i.md", "success", gh) == "repetida"
    assert not gh.hay("git", "switch")


def test_sin_cambios_no_se_abre_pr(tmp_path):
    gh = GitHubFalso()
    assert vigia.abrir_pr(_resultado(cambios=False), tmp_path / "i.md", "success", gh) == "sin_cambios"
    assert gh.ordenes == []


def test_incidencia_del_curso_que_empieza(tmp_path):
    (tmp_path / "cursos").mkdir()
    gh = GitHubFalso()
    assert vigia.incidencia_curso(dt.date(2030, 7, 20), tmp_path, gh).startswith("Dar de alta el curso 2030-2031")
    assert gh.hay("gh", "issue", "create")
    (tmp_path / "cursos" / "2030-2031.yaml").write_text("x: 1\n")
    assert vigia.incidencia_curso(dt.date(2030, 7, 27), tmp_path, GitHubFalso()) == ""
    assert vigia.incidencia_curso(dt.date(2030, 3, 2), tmp_path, GitHubFalso()) == ""


# ---------------------------------------------------------------------------------------------------------------------
# Prueba de cierre de F5: de la norma cambiada a la programación aceptada
# ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.ui
def test_recorrido_completo_de_un_cambio_en_una_norma(qtbot, repo, tmp_path, monkeypatch, datos):
    from PyQt6.QtWidgets import QDialog

    from conftest import programacion_ficticia
    from programaciones.contexto import Contexto
    from programaciones.ui import estilo
    from programaciones.ui.modales import DialogoCambios, DialogoCurriculoNuevo
    from programaciones.ui.ventana import VentanaPrincipal

    carpeta, fuentes = repo
    k = Ed25519PrivateKey.generate()
    clave = base64.b64encode(k.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())).decode()
    monkeypatch.setattr(firma, "clave_publica", lambda: k.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))

    # Lo que hay publicado y lo que lleva la app: la versión de ahora (V0)
    rama = tmp_path / "catalogo-publicado"
    v0 = receta.publicar(rama, carpeta, clave=clave)
    app = tmp_path / "app" / "catalogo"
    shutil.copytree(carpeta, app, ignore=shutil.ignore_patterns("vigia.yaml"))

    # 1. Vigía: el BOE cambia un criterio de 0517 (fuente falsa) → PR automática, que se fusiona
    res, md = revisar(carpeta, fuentes, boe_cambia_un_criterio(carpeta, "Se ha cambiado en el BOE (ficticio)."))
    assert res.automatica and "RA3 de 0517: criterio b) cambia" in md
    informe = tmp_path / "informe.md"
    informe.write_text(md, encoding="utf-8")
    gh = GitHubFalso()
    assert vigia.abrir_pr(asdict(res), informe, "success", gh) == "fusionada"
    assert gh.hay("gh", "workflow", "run", "catalogo.yml")

    # 2. catalogo.yml: firma y publica la versión nueva (V1)
    v1 = receta.publicar(rama, carpeta, clave=clave)
    assert v1 == "2030.01.15" and receta.verificar(str(rama)) == v1

    # 3. La app (con V0 dentro) y una programación ficticia hecha con V0
    monkeypatch.setenv("PROGRAMACIONES_CATALOGO", str(app))
    servidor_pedidas = []

    def servidor(url, timeout=None):
        import io
        servidor_pedidas.append(url)
        return io.BytesIO((rama / url[len(cr.URL_BASE):]).read_bytes())

    monkeypatch.setattr(cr, "_abrir", servidor)
    estilo.cargar_fuentes()
    ctx = Contexto(datos)
    assert ctx.catalogo.version == v0
    prog = programacion_ficticia()
    prog.update(catalogo=v0, curso_escolar=ctx.curso_escolar, bloques={b: "confirmado" for b in prog["bloques"]})
    ctx.abrir(prog)
    abiertos = []
    respuesta = {"DialogoCurriculoNuevo": QDialog.DialogCode.Rejected, "DialogoCambios": QDialog.DialogCode.Accepted}

    def exec_(self):
        abiertos.append(self)
        return respuesta.get(type(self).__name__, QDialog.DialogCode.Rejected)

    monkeypatch.setattr(QDialog, "exec", exec_)
    ventana = VentanaPrincipal(ctx)
    qtbot.addWidget(ventana)
    ventana.show()
    assert not ventana.boton_curriculo.isVisible()

    # 4. Al arrancar: comprueba, descarga, verifica y avisa como con una versión nueva (botón dorado y diálogo)
    ventana.comprobar_catalogo()
    qtbot.waitUntil(lambda: ctx.catalogo.version == v1, timeout=10_000)
    qtbot.waitUntil(lambda: any(isinstance(d, DialogoCurriculoNuevo) for d in abiertos), timeout=5_000)
    aviso = next(d for d in abiertos if isinstance(d, DialogoCurriculoNuevo))
    texto = aviso.notas.toPlainText()
    assert aviso.windowTitle() == "Cambios en el currículo" and "§" in aviso.findChildren(type(aviso.titulo))[0].text()
    assert "RA3 de 0517: criterio b) cambia" in texto and "tu programación" in texto
    assert RD_SEA not in texto or "huella" in texto
    assert aviso.aceptar.text() == "Revisar mis programaciones"
    assert ventana.boton_curriculo.isVisible() and ventana.boton_curriculo.text().endswith("· 1")
    assert ctx.prog["catalogo"] == v0, "la app no aplica nada por su cuenta"
    assert "V-08" in {a.id for a in ctx.avisos()}, "lo no aceptado se recuerda"

    # 5. La profesora revisa su programación, ve la diferencia y acepta
    respuesta["DialogoCurriculoNuevo"] = QDialog.DialogCode.Accepted
    ventana.ofrecer_curriculo()
    cambios = next(d for d in abiertos if isinstance(d, DialogoCambios))
    assert "RA3" in cambios.notas.toPlainText() and cambios.aceptar.text() == "Aceptar cambios"
    assert ctx.prog["catalogo"] == v1 and not ctx.cambios_de_curriculo()
    assert ctx.prog["bloques"]["unidades"] == "heredado", "los bloques que usan el RA3 quedan por revisar"
    assert not ventana.boton_curriculo.isVisible(), "aceptado: el aviso desaparece"
    assert all(u.startswith(cr.URL_BASE) for u in servidor_pedidas)


@pytest.mark.ui
def test_sin_red_la_app_sigue_con_su_catalogo(qtbot, contexto, monkeypatch):
    import urllib.error

    from programaciones.ui.ventana import VentanaPrincipal

    def sin_red(url, timeout=None):
        raise urllib.error.URLError("sin red (simulado)")

    monkeypatch.setattr(cr, "_abrir", sin_red)
    antes = contexto.catalogo.version
    ventana = VentanaPrincipal(contexto)
    qtbot.addWidget(ventana)
    ventana.show()
    ventana.comprobar_catalogo()
    qtbot.waitUntil(lambda: cr.leer_estado(contexto.carpeta).get("resultado") == "sin_red", timeout=10_000)
    assert contexto.catalogo.version == antes and not ventana.boton_curriculo.isVisible()
