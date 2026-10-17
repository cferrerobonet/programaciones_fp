"""Novedades de la 0.2.0 con pytest-qt, sin pantalla y con datos ficticios: el curso escolar en Ajustes, la gestión del
listado «Programaciones» (abrir, vista previa, exportar a carpeta, enviar por correo y borrar), el correo con el
cliente simulado (`conftest.ClienteSimulado`: nunca se abre un programa de verdad) y los módulos favoritos."""
import os

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QDialog, QLabel, QMessageBox

from conftest import programacion_minima
from programaciones import almacen, correo, exportacion
from programaciones.ajustes import ASUNTO_UNA, GestorAjustes

pytestmark = pytest.mark.ui


class Modales(list):
    """`exec()` no bloquea: guarda el diálogo y, si hay una respuesta para su clase, la ejecuta («Cancelar» si no)."""

    def __init__(self):
        super().__init__()
        self.respuestas = {}


@pytest.fixture
def modales(monkeypatch):
    abiertos = Modales()

    def exec_(self):
        abiertos.append(self)
        respuesta = abiertos.respuestas.get(type(self).__name__)
        return respuesta(self) if respuesta else QDialog.DialogCode.Rejected

    monkeypatch.setattr(QDialog, "exec", exec_)
    return abiertos


@pytest.fixture
def ctx(contexto, curso):
    contexto.datos_curso = curso
    contexto.gestor.poner(nombre_profesor="Profesora Ficticia Uno", programa_pdf="libreoffice")
    return contexto


@pytest.fixture
def ventana(qtbot, ctx):
    from programaciones.ui.ventana import VentanaPrincipal

    v = VentanaPrincipal(ctx)
    qtbot.addWidget(v)
    v.show()
    return v


@pytest.fixture
def progs(ctx, cat):
    """Tres programaciones de SEA guardadas en este equipo: dos completas y una con un bloque heredado (bloquea)."""
    modulos = [m for m in ctx.modulos if m.sigla == "SEA" and m.curso == 2][:3]
    out = []
    for i, m in enumerate(modulos):
        p = programacion_minima(cat, m.sigla, m.curso, m.codigo, ctx.curso_escolar)
        if i == 2:
            p["bloques"]["profesorado"] = "heredado"
        ctx.almacen.guardar(p)
        out.append(p)
    ctx.recargar_programaciones()
    return out


def ident(p):
    return f"{p['curso_escolar']}/{almacen.identificador(p)}"


def listado(qtbot, ctx, padre=None):
    from programaciones.ui.programaciones import DialogoProgramaciones

    d = DialogoProgramaciones(ctx, padre)
    if padre is None:
        qtbot.addWidget(d)
    return d


def nombre(ctx, p):
    return exportacion.destinos(p, ctx.catalogo, ctx.almacen.carpeta, ["docx"])[0].stem


# ---------------------------------------------------------------------------------------------------------------------
# 1. Curso escolar en Ajustes
# ---------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def ajustes(qtbot, ctx):
    from programaciones.ui.ajustes import DialogoAjustes

    d = DialogoAjustes(ctx, None, "Curso escolar")
    qtbot.addWidget(d)
    return d


def textos(widget):
    return " ".join(w.text() for w in widget.findChildren(QLabel))


def test_curso_escolar_es_un_apartado_de_ajustes_con_todo_lo_del_curso(ajustes, ctx, tmp_path):
    from programaciones.ui.ajustes import APARTADOS

    assert ajustes.nav.currentItem().text() == "Curso escolar" and APARTADOS[1] == "Curso escolar"
    pagina = ajustes.pila.widget(APARTADOS.index("Curso escolar"))
    assert ajustes.curso.text() == ctx.curso_escolar
    assert "fechas de evaluación y de empresa dadas de alta" in ajustes.fechas_curso.text()
    assert f"Carpeta de entrega {ctx.curso_escolar}" in textos(pagina)
    ajustes.poner_carpeta(str(tmp_path))
    assert ctx.gestor.carpeta_entrega(ctx.curso_escolar) == str(tmp_path) and ajustes.abrir_carpeta.isEnabled()
    catalogo = ajustes.pila.widget(APARTADOS.index("Catálogo"))
    assert "Curso escolar" not in textos(catalogo), "lo del curso ya no está repartido en «Catálogo»"


def test_sin_fechas_el_curso_sale_pendiente(qtbot, contexto):
    from programaciones.ui.ajustes import DialogoAjustes

    contexto.datos_curso = None
    d = DialogoAjustes(contexto, None, "Curso escolar")
    qtbot.addWidget(d)
    assert f"{contexto.curso_escolar}: pendiente" in d.fechas_curso.text()


def test_la_barra_ya_no_tiene_el_boton_del_curso_y_el_menu_lleva_al_apartado(ventana, ctx, modales):
    from PyQt6.QtWidgets import QPushButton

    assert not [b for b in ventana.findChildren(QPushButton) if b.text() == ctx.curso_escolar]
    assert ventana.boton_actualizar.parentWidget() is not None and ventana.zona_avisos.indexOf(
        ventana.boton_actualizar) == 0, "el aviso de F5 irá en `zona_avisos`, junto al de actualizaciones"
    ventana.accion_curso.trigger()
    assert modales[-1].nav.currentItem().text() == "Curso escolar"


# ---------------------------------------------------------------------------------------------------------------------
# 2. Gestión del listado «Programaciones»
# ---------------------------------------------------------------------------------------------------------------------
def test_los_botones_se_activan_segun_las_marcadas(qtbot, ctx, progs):
    d = listado(qtbot, ctx)
    activos = lambda: {c for c, b in d.botones.items() if b.isEnabled()}  # noqa: E731
    assert activos() == set() and d.cuantas.text() == "Ninguna marcada"
    d.tabla.marcar([ident(progs[0])])
    assert activos() == {"abrir", "vista_previa", "exportar", "correo", "borrar"}
    d.tabla.marcar([ident(progs[0]), ident(progs[1])])
    assert activos() == {"vista_previa", "exportar", "correo", "borrar"}, "«Abrir», solo con una"
    assert [d.botones[c].text() for c in ("exportar", "correo", "borrar")] == [
        "Exportar 2 a carpeta…", "Enviar 2 por correo…", "Borrar 2…"]
    assert d.cuantas.text() == "2 marcadas"
    # Marcar con la casilla, como el profesor
    d.tabla.marcar([])
    fila = next(r for r in range(d.tabla.tabla.rowCount()) if d.tabla.fila_en(r)["prog"] == progs[1])
    d.tabla.tabla.item(fila, 0).setCheckState(Qt.CheckState.Checked)
    assert activos() == {"abrir", "vista_previa", "exportar", "correo", "borrar"}
    d.hacer("abrir")
    assert d.elegida == progs[1] and d.result() == QDialog.DialogCode.Accepted


def test_menu_contextual_con_las_mismas_acciones(qtbot, ctx, progs):
    d = listado(qtbot, ctx)
    fila = next(f for f in ctx.programaciones if f["prog"] == progs[2])
    menu = d.menu_contextual(fila)
    assert [f["id"] for f in d.tabla.marcadas()] == [ident(progs[2])], "clic derecho en una sin marcar: solo esa"
    acciones = {a.text(): a.isEnabled() for a in menu.actions() if a.text()}
    assert acciones == {"Abrir": True, "Vista previa": True, "Exportar a carpeta…": True, "Enviar por correo…": True,
                        "Borrar…": True}
    d.tabla.marcar([ident(progs[0]), ident(progs[2])])
    menu = d.menu_contextual(fila)
    assert len(d.tabla.marcadas()) == 2, "en una ya marcada, se quedan todas"
    assert {a.text(): a.isEnabled() for a in menu.actions() if a.text()}["Abrir"] is False
    # El clic derecho de verdad llega por la señal de la tabla
    d.tabla.tabla.customContextMenuRequested.emit(QPoint(40, 5))
    assert d.ultimo_menu is not None and d.ultimo_menu is not menu
    d.ultimo_menu.close()


def test_abrir_desde_el_listado_abre_la_programacion_en_la_ventana(qtbot, ventana, ctx, progs, modales):
    modales.respuestas["DialogoProgramaciones"] = lambda d: (d.tabla.marcar([ident(progs[1])]), d.hacer("abrir"),
                                                             d.result())[-1]
    ventana.abrir_programaciones()
    assert ctx.prog["modulo"] == progs[1]["modulo"] and ctx.modulo.codigo == progs[1]["modulo"]


def test_vista_previa_de_varias(qtbot, ctx, progs, modales, pdf_falso):
    from programaciones.ui.vista_previa import DialogoVistaPrevia

    d = listado(qtbot, ctx)
    d.tabla.marcar([ident(progs[0]), ident(progs[1])])
    d.hacer("vista_previa")
    qtbot.waitUntil(lambda: any(isinstance(x, DialogoVistaPrevia) for x in modales), timeout=60000)
    visor = next(x for x in modales if isinstance(x, DialogoVistaPrevia))
    assert not visor.elegir.isHidden() and visor.elegir.count() == 2
    assert [visor.elegir.itemText(i) for i in range(2)] == [nombre(ctx, p) for p in progs[:2]]
    visor.elegir.setCurrentIndex(1)
    assert visor.pila.currentWidget() is visor.visor and visor.documento.pageCount() == 1
    assert len(pdf_falso) == 2


def test_exportar_a_carpeta_sin_sustituir_sin_preguntar(qtbot, ctx, progs, modales, pdf_falso, tmp_path, monkeypatch):
    from programaciones.ui.modales import DialogoExportando

    destino = tmp_path / "Destino ficticio"
    destino.mkdir()

    def elegir(d):
        d.poner_carpeta(destino)
        assert "avisos en rojo" in d.filas[nombre(ctx, progs[2])].text()
        return QDialog.DialogCode.Accepted

    modales.respuestas["DialogoExportarCarpeta"] = elegir
    d = listado(qtbot, ctx)
    d.tabla.marcar([ident(p) for p in progs])

    def exportar():
        n = len([x for x in modales if isinstance(x, DialogoExportando)])
        d.hacer("exportar")
        hechos = [x for x in modales if isinstance(x, DialogoExportando)]
        if len(hechos) == n:
            return None
        qtbot.waitUntil(lambda: hechos[-1]._terminado, timeout=60000)
        return hechos[-1]

    hecho = exportar()
    archivos = sorted(f.name for f in destino.iterdir())
    esperados = sorted(f"{nombre(ctx, p)}.{x}" for p in progs[:2] for x in ("docx", "pdf"))
    assert archivos == esperados, "la que tiene avisos en rojo no se exporta"
    assert "No se exporta" in hecho.error.text() and hecho.titulo.text() == "Exportadas"
    estados = {f["id"]: f["estado_clave"] for f in ctx.programaciones}
    assert estados[ident(progs[0])] == estados[ident(progs[1])] == "exportada"

    # Ya existen: «No» exporta solo lo que falta
    preguntas = []
    respuesta = [QMessageBox.StandardButton.No]
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: preguntas.append(a[2]) or respuesta[0])
    quitado = destino / f"{nombre(ctx, progs[1])}.pdf"
    quitado.unlink()
    antes = {f.name: f.stat().st_mtime_ns for f in destino.iterdir()}
    hecho = exportar()
    assert preguntas and nombre(ctx, progs[0]) in preguntas[-1]
    assert quitado.is_file() and {f.name: f.stat().st_mtime_ns for f in destino.iterdir() if f != quitado} == antes
    # «Cancelar»: no se escribe nada
    respuesta[0] = QMessageBox.StandardButton.Cancel
    antes = {f.name: f.stat().st_mtime_ns for f in destino.iterdir()}
    assert exportar() is None and {f.name: f.stat().st_mtime_ns for f in destino.iterdir()} == antes
    # «Sí»: se sustituyen
    respuesta[0] = QMessageBox.StandardButton.Yes
    os.utime(destino / f"{nombre(ctx, progs[0])}.docx", ns=(1, 1))
    exportar()
    assert (destino / f"{nombre(ctx, progs[0])}.docx").stat().st_mtime_ns != 1


# ---------------------------------------------------------------------------------------------------------------------
# 3. Enviar por correo
# ---------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def entrega(ctx, tmp_path):
    carpeta = tmp_path / "Teams ficticio"
    carpeta.mkdir()
    ctx.gestor.poner_carpeta_entrega(ctx.curso_escolar, str(carpeta))
    ctx.gestor.poner(destinatarios=["jefatura@example.com", "departamento@example.com"])
    return carpeta


def exportada_antes(ctx, p, carpeta, tamano=1000):
    """Deja el Word y el PDF de `p` en la carpeta, como si se hubieran exportado, y lo apunta en su historial."""
    rutas = exportacion.destinos(p, ctx.catalogo, carpeta, ["docx", "pdf"])
    for r in rutas:
        with open(r, "wb") as f:
            f.truncate(tamano)
    almacen.anotar(p, "exportada: " + ", ".join(r.name for r in rutas))
    ctx.almacen.guardar(p)
    ctx.recargar_programaciones()
    return rutas


def enviar(qtbot, ctx, d, modales):
    from programaciones.ui.modales import DialogoExportando

    d.hacer("correo")
    hecho = [x for x in modales if isinstance(x, DialogoExportando)][-1]
    qtbot.waitUntil(lambda: hecho._terminado, timeout=60000)
    return hecho


def test_enviar_varias_abre_un_borrador_con_los_adjuntos(qtbot, ctx, progs, entrega, modales, pdf_falso,
                                                          cliente_correo, monkeypatch):
    monkeypatch.setattr(correo, "metodos", lambda cliente="auto", plataforma=None: ["mail", "mailto"])
    ya = exportada_antes(ctx, progs[0], entrega)
    vista = {}

    def rellenar(d):
        vista["plan"] = [(a.ruta.name, a.estado) for a in d.plan]
        vista["asunto"] = d.asunto.text()
        vista["cuerpo"] = d.cuerpo.toPlainText()
        vista["chips"] = list(d.chips_para)
        d.chips_para["jefatura@example.com"].click()
        d.otros.setText("tutoria@example.com")
        return QDialog.DialogCode.Accepted

    modales.respuestas["DialogoCorreo"] = rellenar
    d = listado(qtbot, ctx)
    d.tabla.marcar([ident(progs[0]), ident(progs[1])])
    hecho = enviar(qtbot, ctx, d, modales)

    nuevos = exportacion.destinos(progs[1], ctx.catalogo, entrega, ["docx", "pdf"])
    assert vista["chips"] == ["jefatura@example.com", "departamento@example.com"]
    assert vista["plan"] == [(ya[0].name, "listo"), (ya[1].name, "listo"), (nuevos[0].name, "exportar"),
                             (nuevos[1].name, "exportar")]
    assert vista["asunto"] == f"Programaciones didácticas — 2 módulos ({ctx.curso_escolar})"
    assert all(f"- {r.name}" in vista["cuerpo"] for r in ya + nuevos)
    assert all(r.is_file() for r in nuevos), "lo que faltaba se exporta antes, con el nombre normalizado"
    (orden,) = cliente_correo.ordenes
    assert orden[2] == correo.APPLESCRIPT_MAIL and orden[3] == vista["asunto"]
    assert orden[5].split("\n") == ["jefatura@example.com", "tutoria@example.com"]
    assert orden[6].split("\n") == [str(r.resolve()) for r in ya + nuevos]
    assert "Correo creado en Mail" in hecho.error.text() and hecho.titulo.text() == "Correo creado"
    estados = {f["id"]: f["estado_clave"] for f in ctx.programaciones}
    assert estados[ident(progs[1])] == "exportada", "la exportación de antes del correo queda en su historial"


def test_correo_de_una_con_la_plantilla_de_ajustes_y_la_reserva_mailto(qtbot, ctx, progs, entrega, modales,
                                                                       cliente_correo):
    ctx.gestor.poner(cliente_correo="mailto", asunto_una="PD {modulo} · {curso}")
    exportada_antes(ctx, progs[0], entrega)
    vista = {}

    def solo_pdf(d):
        d.chips["docx"].click()
        vista["plan"] = [a.formato for a in d.plan]
        vista["asunto"] = d.asunto.text()
        return QDialog.DialogCode.Accepted

    modales.respuestas["DialogoCorreo"] = solo_pdf
    d = listado(qtbot, ctx)
    d.tabla.marcar([ident(progs[0])])
    hecho = enviar(qtbot, ctx, d, modales)
    assert vista["plan"] == ["pdf"] and vista["asunto"] == f"PD {ctx.nombre_modulo(progs[0])} · {ctx.curso_escolar}"
    carpeta, enlace = cliente_correo.abiertos
    assert carpeta == str(entrega.resolve()) and enlace.startswith("mailto:?subject=")
    assert not cliente_correo.ordenes
    assert "adjúntalos a mano" in hecho.error.text() and hecho.titulo.text() == "Correo nuevo abierto"


def test_correo_avisa_del_tamano_y_de_lo_que_no_se_puede_adjuntar(qtbot, ctx, progs, entrega, modales):
    from programaciones.ui.correo import DialogoCorreo

    exportada_antes(ctx, progs[0], entrega, tamano=11 * 1024 * 1024)  # 22 MB entre los dos
    d = listado(qtbot, ctx)
    c = DialogoCorreo(d.gestion, [progs[0], progs[2]])
    qtbot.addWidget(c)
    assert c.supera_limite() and "pasa de 20 MB" in c.total.text() and c.total.property("rol") == "aviso-texto"
    assert [a.estado for a in c.plan] == ["listo", "listo", "bloqueada", "bloqueada"]
    assert c.asunto.text().startswith("Programación didáctica — "), "la que no se adjunta no cuenta en el asunto"
    assert "avisos en rojo" in c.filas[-1].text() and c.crear.isEnabled()
    c.chips["docx"].click()
    assert not c.supera_limite() and "pasa de" not in c.total.text()
    solo = DialogoCorreo(d.gestion, [progs[2]])
    qtbot.addWidget(solo)
    assert not solo.crear.isEnabled(), "nada que adjuntar"
    solo.otros.setText("no es un correo")
    assert "No parece un correo" in solo.estado_para.text()


def test_correo_con_cambios_despues_de_exportar(qtbot, ctx, progs, entrega, modales):
    from programaciones.ui.correo import DialogoCorreo

    exportada_antes(ctx, progs[0], entrega)
    almacen.anotar(progs[0], "modificada tras exportar")
    ctx.almacen.guardar(progs[0])
    ctx.recargar_programaciones()
    d = listado(qtbot, ctx)
    c = DialogoCorreo(d.gestion, [progs[0]])
    qtbot.addWidget(c)
    assert [a.estado for a in c.plan] == ["cambiada", "cambiada"] and not c.reexportar.isHidden()
    assert "antes de tus últimos cambios" in c.filas[0].text()
    c.reexportar.setChecked(True)
    assert [a.estado for a in c.plan] == ["exportar", "exportar"]
    c.asunto.setText("Asunto escrito por el profesor")
    c.asunto.textEdited.emit("Asunto escrito por el profesor")
    c.chips["pdf"].click()
    assert c.asunto.text() == "Asunto escrito por el profesor", "lo que escribe el profesor no se pisa"
    assert ASUNTO_UNA.split("—")[0] not in c.asunto.text()


# ---------------------------------------------------------------------------------------------------------------------
# Borrar
# ---------------------------------------------------------------------------------------------------------------------
def test_borrar_a_la_papelera_sin_tocar_lo_exportado(qtbot, ctx, progs, entrega, modales, papelera, monkeypatch):
    exportados = exportada_antes(ctx, progs[0], entrega)
    ctx.abrir(progs[0])
    trabajo = ctx.almacen.ruta(progs[0])
    copias = ctx.almacen.copias / f"{progs[0]['curso_escolar']}-{almacen.identificador(progs[0])}"
    assert trabajo.is_file() and copias.is_dir()
    preguntas = []
    respuesta = [QMessageBox.StandardButton.No]
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: preguntas.append(a[2]) or respuesta[0])
    d = listado(qtbot, ctx)
    d.tabla.marcar([ident(progs[0])])
    d.hacer("borrar")
    assert nombre(ctx, progs[0]) in preguntas[0] and "papelera" in preguntas[0]
    assert "No se borra nada de lo exportado" in preguntas[0]
    assert trabajo.is_file() and not papelera, "con «No», nada"
    respuesta[0] = QMessageBox.StandardButton.Yes
    d.hacer("borrar")
    assert not trabajo.exists() and not copias.exists()
    assert [p.name.split("-", 1)[1] for p in papelera] == [trabajo.name, copias.name]
    assert all(r.is_file() for r in exportados), "los Word y PDF exportados se quedan"
    assert ctx.prog is None, "la abierta se cierra"
    assert ident(progs[0]) not in {f["id"] for f in ctx.programaciones}
    assert d.tabla.total == 2 and not d.tabla.marcadas()
    ctx.guardar()
    assert not trabajo.exists(), "ni el autoguardado la vuelve a escribir"


def test_si_la_papelera_no_la_acepta_no_se_borra(qtbot, ctx, progs, modales, monkeypatch):
    from programaciones.ui import gestion

    monkeypatch.setattr(gestion, "papelera", lambda ruta: False)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    avisos = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: avisos.append(a[2]))
    d = listado(qtbot, ctx)
    d.tabla.marcar([ident(progs[1])])
    d.hacer("borrar")
    assert avisos and "papelera" in avisos[0]
    assert ctx.almacen.ruta(progs[1]).is_file() and d.tabla.total == 3


# ---------------------------------------------------------------------------------------------------------------------
# Ajustes → Correo
# ---------------------------------------------------------------------------------------------------------------------
def test_ajustes_correo_destinatarios_programa_y_plantilla(ajustes, ctx):
    assert not ajustes.anadir_destinatario("no es un correo")
    assert ctx.gestor.valores.destinatarios == [] and ajustes.estado_destinatarios.property("rol") == "aviso-texto"
    assert ajustes.anadir_destinatario("jefatura@example.com, departamento@example.com")
    assert ajustes.anadir_destinatario("jefatura@example.com")
    assert ctx.gestor.valores.destinatarios == ["jefatura@example.com", "departamento@example.com"]
    assert ajustes.destinatarios.count() == 2
    ajustes.destinatarios.setCurrentRow(0)
    ajustes.quitar_destinatario.click()
    assert GestorAjustes(ctx.carpeta).valores.destinatarios == ["departamento@example.com"]
    ajustes.cliente.setCurrentIndex(ajustes.cliente.findData("mailto"))
    assert ctx.gestor.valores.cliente_correo == "mailto" and "adjuntarlos tú" in ajustes.estado_cliente.text()
    ajustes.asunto_una.setText("PD {modulo}")
    ajustes.asunto_una.editingFinished.emit()
    ajustes.cuerpo.setPlainText("Cuerpo ficticio {archivos}")
    assert ctx.gestor.valores.asunto_una == "PD {modulo}"
    assert ctx.gestor.valores.cuerpo_correo == "Cuerpo ficticio {archivos}"
    ajustes.restablecer_plantilla()
    assert ctx.gestor.valores.asunto_una == ASUNTO_UNA and ajustes.asunto_una.text() == ASUNTO_UNA
    assert "ADR-014" not in textos(ajustes) and "contraseñas" in textos(ajustes)


# ---------------------------------------------------------------------------------------------------------------------
# 4. Favoritos
# ---------------------------------------------------------------------------------------------------------------------
def test_favoritos_con_la_estrella_el_menu_y_el_atajo(qtbot, ventana, ctx):
    col = ventana.modulos
    entrada = ctx.entrada("SEA", 2, "0517")
    fila = next(f for f in col.filas if f.entrada == entrada)
    assert not fila.estrella.isChecked() and "0517" in fila.estrella.accessibleName()
    assert fila.estrella.accessibleDescription() == "Favorito: sin marcar"
    qtbot.mouseClick(fila.estrella, Qt.MouseButton.LeftButton)
    assert ctx.gestor.valores.favoritos == ["SEA-2-0517"] and fila.estrella.isChecked()
    assert fila.estrella.accessibleDescription() == "Favorito: marcado"
    assert "Quitar de favoritos" in fila.estrella.toolTip()
    assert GestorAjustes(ctx.carpeta).valores.favoritos == ["SEA-2-0517"], "se guarda en este equipo"

    # Chip «Favoritos» y «Limpiar»
    col.chip_favoritos.click()
    assert col.visibles() == [entrada] and "favoritos" in col.cuenta.text() and col.limpiar.isEnabled()
    col.limpiar_filtros()
    assert not col.chip_favoritos.isChecked() and len(col.visibles()) == len(ctx.modulos)

    # Clic derecho
    menu = col.menu_favorito(entrada)
    assert [a.text() for a in menu.actions()] == ["Quitar de favoritos"]
    menu.actions()[0].trigger()
    assert ctx.gestor.valores.favoritos == [] and not fila.estrella.isChecked()
    assert [a.text() for a in col.menu_favorito(entrada).actions()] == ["Añadir a favoritos"]
    col.lista.customContextMenuRequested.emit(col.lista.visualItemRect(col.lista.item(0)).center())
    assert col.ultimo_menu is not None
    col.ultimo_menu.close()

    # Atajo sobre la fila elegida
    col.elegir(entrada)
    ventana.activateWindow()
    col.lista.setFocus()
    qtbot.keyClick(col.lista, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)
    assert ctx.gestor.valores.favoritos == ["SEA-2-0517"] and fila.estrella.isChecked()


def test_chip_favoritos_sin_ninguno_marcado(ventana, ctx):
    col = ventana.modulos
    col.chip_favoritos.click()
    assert col.visibles() == [] and "pulsa la estrella" in col.cuenta.text()
    col.chip_favoritos.click()
    assert len(col.visibles()) == len(ctx.modulos)
