"""La base de la app con pytest-qt, sin pantalla: arranque, navegación de la maqueta, Ajustes y QtPdf."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QMenu

pytestmark = pytest.mark.ui


@pytest.fixture
def ventana(qtbot, contexto):
    from programaciones.ui.ventana import VentanaPrincipal

    v = VentanaPrincipal(contexto)
    qtbot.addWidget(v)
    v.show()
    return v


@pytest.fixture
def sin_modales(monkeypatch):
    """`exec()` de los diálogos no bloquea: guarda el diálogo que se iba a abrir y vuelve al momento."""
    abiertos = []

    def exec_(self):
        abiertos.append(self)
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(QDialog, "exec", exec_)
    return abiertos


# Arranque
def test_arranca_con_la_barra_y_las_tres_zonas(ventana, contexto):
    assert ventana.windowTitle() == "Programaciones"
    assert ventana.minimumSize().width() == 980
    assert ventana.modulos.width() == 300 and ventana.estado.width() == 340
    assert not hasattr(ventana, "boton_curso"), "el curso escolar está en Ajustes, no en la barra"
    assert f"Curso {contexto.curso_escolar}" in ventana.recuento.text()
    assert ventana.boton_programaciones.text() == "Programaciones · 0"
    assert f"{len(contexto.modulos)} módulos" in ventana.recuento.text()
    assert contexto.catalogo.fecha in ventana.catalogo.text()
    assert not ventana.boton_actualizar.isVisible()


def test_estado_vacio_elige_un_modulo(ventana):
    assert ventana.ficha.pila.currentWidget() is ventana.ficha.vacio
    assert ventana.ficha.vacio.titulo.text() == "Elige un módulo"
    assert not ventana.estado.boton_exportar.isEnabled()
    assert ventana.estado.resumen.text() == "Elige un módulo para empezar"
    assert ventana.estado.chip_word.isChecked() and ventana.estado.chip_pdf.isChecked()


def test_lista_de_modulos_desde_el_catalogo(contexto):
    claves = {(m.sigla, m.curso, m.codigo) for m in contexto.modulos}
    assert ("SEA", 2, "0517") in claves
    assert len(claves) == len(contexto.modulos), "cada fila del horario, una sola vez"
    assert {m.grado for m in contexto.modulos} == {"GB", "GM", "GS"}


def test_prueba_de_arranque_comprueba_datos_y_qtpdf(ventana, caplog):
    import logging

    from programaciones.app import MARCA_PRUEBA, prueba_de_arranque
    from programaciones.diagnostico import MARCA_DATOS
    from programaciones.ui.vista_previa import MARCA_QTPDF

    with caplog.at_level(logging.INFO):
        assert prueba_de_arranque(ventana)
    for marca in (MARCA_DATOS, MARCA_QTPDF, MARCA_PRUEBA):
        assert marca in caplog.text


def test_prueba_de_arranque_falla_sin_datos(ventana, monkeypatch):
    from programaciones import diagnostico
    from programaciones.app import prueba_de_arranque

    monkeypatch.setattr(diagnostico, "PARTES_PLANTILLA", ("word/no-existe.xml",))
    assert not prueba_de_arranque(ventana)


def test_qtpdf_abre_un_pdf(qapp):
    from programaciones.ui.vista_previa import comprobar_qtpdf

    assert "1 página" in comprobar_qtpdf()


def test_vista_previa_abre_un_pdf(qtbot, tmp_path):
    from PyQt6.QtGui import QPainter, QPdfWriter

    from programaciones.ui.vista_previa import DialogoVistaPrevia

    ruta = tmp_path / "borrador.pdf"
    escritor = QPdfWriter(str(ruta))  # vivo mientras pinta: si se libera antes, Qt se cae
    p = QPainter(escritor)
    p.drawText(100, 100, "BORRADOR")
    p.end()
    d = DialogoVistaPrevia()
    qtbot.addWidget(d)
    assert d.pila.currentWidget() is d.vacio
    assert d.abrir(ruta) and d.pila.currentWidget() is d.visor and d.documento.pageCount() == 1
    assert not d.abrir(tmp_path / "no-existe.pdf") and d.pila.currentWidget() is d.vacio


# Navegación de la maqueta
def test_barra_abre_programaciones_y_ajustes(qtbot, ventana, sin_modales):
    qtbot.mouseClick(ventana.boton_programaciones, Qt.MouseButton.LeftButton)
    ventana.accion_curso.trigger()  # lo que hacía el chip del curso de la barra
    ventana.abrir_ajustes("Carpeta de entrega")  # el nombre antiguo lleva a «Exportación», donde está la carpeta
    listado, ajustes, antiguo = sin_modales
    assert listado.windowTitle() == "Programaciones" and listado.tabla.total == 0
    assert not listado.abrir.isEnabled() and not listado.enviar.isEnabled()
    assert ajustes.windowTitle() == "Ajustes"
    assert ajustes.nav.currentItem().text() == "Curso escolar" and antiguo.nav.currentItem().text() == "Exportación"


def test_menu_de_la_app(ventana, sin_modales):
    acciones = {a.text(): a for m in ventana.menuBar().findChildren(QMenu)
                for a in m.actions()}
    for texto in ("Abrir…", "Nueva a partir de…", "Vista previa", "Exportar", "Programaciones…", "Curso escolar…",
                  "Ajustes…",
                  "Buscar actualizaciones", "Acerca de Programaciones"):
        assert texto in acciones, texto
    assert not any("Teams" in t or "OneDrive" in t for t in acciones), "sin la ayuda de Teams (ADR-047)"
    # Abrir un archivo siempre se puede; sin programación abierta no hay nada que guardar, previsualizar ni exportar.
    assert acciones["Abrir…"].isEnabled() and not acciones["Exportar"].isEnabled()
    assert not acciones["Vista previa"].isEnabled() and not acciones["Guardar"].isEnabled()
    acciones["Nueva a partir de…"].trigger()
    (heredar,) = sin_modales
    assert heredar.windowTitle() == "Nueva a partir de…" and not heredar.heredar.isEnabled()


def test_heredar_acepta_el_archivo_soltado(qtbot, contexto, tmp_path):
    from programaciones.ui.programaciones import DialogoHeredar

    d = DialogoHeredar(contexto)
    qtbot.addWidget(d)
    d.zona.archivos.emit([str(tmp_path / "anterior.docx")])
    assert d.archivo.name == "anterior.docx" and "anterior.docx" in d.resumen.text()


def test_actualizacion_disponible_muestra_el_boton_dorado(ventana, monkeypatch):
    from programaciones.ui import dialogos

    ofrecidas = []
    monkeypatch.setattr(dialogos, "ofrecer", lambda padre, *a: ofrecidas.append(a))
    ventana.actualizacion_disponible("9.9.9", "https://github.com/x", "- Novedad ficticia")
    assert ventana.boton_actualizar.isVisible() and "9.9.9" in ventana.boton_actualizar.text()
    assert ofrecidas == [("9.9.9", "https://github.com/x", "- Novedad ficticia")]
    ventana.actualizacion_disponible("9.9.9", "https://github.com/x", "- Novedad ficticia")
    assert len(ofrecidas) == 1, "la misma versión no vuelve a abrir el diálogo"


def test_dialogo_de_novedades(qtbot):
    from programaciones.ui.dialogos import DialogoActualizacion

    d = DialogoActualizacion("9.9.9", "### Añadido\n\n- Novedad ficticia")
    qtbot.addWidget(d)
    assert "9.9.9" in d.titulo.text() and "Novedad ficticia" in d.notas.toPlainText()
    assert d.aceptar.text() == "Actualizar ahora"


# Ajustes
@pytest.fixture
def ajustes(qtbot, contexto):
    from programaciones.ui.ajustes import APARTADOS, DialogoAjustes

    d = DialogoAjustes(contexto)
    qtbot.addWidget(d)
    assert [d.nav.item(i).text() for i in range(d.nav.count())] == APARTADOS
    return d


def test_ajustes_apartados_de_la_maqueta(ajustes):
    assert [ajustes.nav.item(i).text() for i in range(ajustes.nav.count())] == [
        "Profesor", "Curso escolar", "Exportación", "Correo", "Catálogo", "Acerca de"]
    for i in range(ajustes.nav.count()):
        ajustes.nav.setCurrentRow(i)
        assert ajustes.pila.currentIndex() == i


def test_ajustes_nombre_del_profesor(ajustes, contexto):
    ajustes.nombre.setText("Profesora Ficticia")
    ajustes.nombre.editingFinished.emit()
    assert contexto.gestor.valores.nombre_profesor == "Profesora Ficticia"


def textos(widget):
    return " ".join(w.text() for w in widget.findChildren(QLabel))


def test_ajustes_carpeta_de_exportacion(ajustes, contexto, tmp_path):
    """ADR-047: una sola carpeta, en «Exportación», sin Teams ni OneDrive ni una por curso."""
    from programaciones.ui.ajustes import APARTADOS

    assert "Carpeta de exportación" in textos(ajustes.pila.widget(APARTADOS.index("Exportación")))
    assert "Teams" not in textos(ajustes) and "OneDrive" not in textos(ajustes)
    ajustes.poner_carpeta(str(tmp_path))
    assert contexto.gestor.carpeta_exportacion() == str(tmp_path)
    assert ajustes.estado_carpeta.property("rol") == "ok" and ajustes.abrir_carpeta.isEnabled()
    ajustes.poner_carpeta("https://example.com/sites/departamento/Programaciones")
    assert ajustes.estado_carpeta.property("rol") == "aviso-texto" and not ajustes.abrir_carpeta.isEnabled()
    ajustes.poner_carpeta(str(tmp_path / "no-existe"))
    assert ajustes.estado_carpeta.property("rol") == "aviso-texto" and not ajustes.abrir_carpeta.isEnabled()
    ajustes.poner_carpeta("")
    assert contexto.gestor.carpeta_exportacion() == ""


def test_ajustes_correo_del_pie(ajustes, contexto):
    assert not ajustes.poner_correo_pie("no es un correo")
    assert contexto.gestor.valores.correo_pie == ""
    assert ajustes.estado_correo_pie.property("rol") == "aviso-texto"
    assert ajustes.poner_correo_pie(" departamento@example.com ")
    assert contexto.gestor.valores.correo_pie == "departamento@example.com"
    assert ajustes.poner_correo_pie("")
    assert contexto.gestor.valores.correo_pie == ""


def test_ajustes_formatos_al_menos_uno(ajustes, contexto):
    ajustes.formatos["pdf"].setChecked(False)
    assert contexto.gestor.valores.formatos == ["docx"]
    ajustes.formatos["docx"].setChecked(False)
    assert ajustes.formatos["docx"].isChecked() and contexto.gestor.valores.formatos == ["docx"]


def test_ajustes_programa_pdf_e_idioma(ajustes, contexto):
    ajustes.programa.setCurrentIndex(ajustes.programa.findData("libreoffice"))
    assert contexto.gestor.valores.programa_pdf == "libreoffice"


def test_ajustes_lo_pendiente_se_ve_como_pendiente(ajustes, contexto):
    """Sin datos, no se implementa: las fechas del curso. El correo y el catálogo publicado (F5) ya no están pendientes."""
    textos = " ".join(w.text() for w in ajustes.findChildren(QLabel))
    assert "ADR-014" not in textos and "pendiente de decidir" not in textos.lower()
    assert "F5" not in textos and ajustes.boton_comprobar_catalogo.text() == "Comprobar ahora"
    if contexto.datos_curso is None:
        assert f"{contexto.curso_escolar}: pendiente" in textos


def test_cambiar_ajustes_avisa_a_la_ventana(ventana, contexto):
    contexto.gestor.poner(formatos=["pdf"])
    contexto.ajustes_cambiados.emit()
    assert not ventana.estado.chip_word.isChecked() and ventana.estado.chip_pdf.isChecked()


def test_error_aviso_y_consejo_se_distinguen(qtbot):
    """ADR-046 (CarlosFB): un error, un aviso y un consejo no se confunden ni con la marca. Tonos separados en claro
    y en oscuro, distintivo de forma distinta y el código del módulo y la etapa en el verde, no en el ocre."""
    from PyQt6.QtGui import QColor

    from programaciones import validacion
    from programaciones.ui import estilo
    from programaciones.ui.columnas import FilaAviso

    def tono(c: str) -> float:
        return QColor(c).hslHueF() * 360

    for t in (estilo.CLARO, estilo.OSCURO):
        tonos = {k: tono(t[k]) for k in ("danger", "warn", "info", "accent")}
        for a, b in (("danger", "warn"), ("danger", "info"), ("warn", "info"), ("warn", "accent")):
            d = abs(tonos[a] - tonos[b])
            assert min(d, 360 - d) >= 25, f"{a} y {b} casi del mismo tono"
        hoja = estilo.hoja(t)
        for rol in ('QLabel[rol="codigo"]', 'QFrame[rol="codigo"]', 'QLabel[rol="tag-etapa"]'):
            regla = hoja.split(rol, 1)[1].split("}", 1)[0]
            assert not any(t[k] in regla for k in ("gold", "gold_soft", "warn", "warn_soft")), rol
        assert t["danger_soft"] in hoja.split('QFrame[rol="aviso-roja"]', 1)[1].split("}", 1)[0]
    for gravedad in (validacion.ROJA, validacion.AMBAR):
        f = FilaAviso("Aviso ficticio", gravedad)
        qtbot.addWidget(f)
        assert not f.distintivo.pixmap().isNull()
    assert {estilo.GRAVEDADES[g][1:] for g in ("error", "aviso", "consejo")} == {
        ("circulo", "×"), ("triangulo", "!"), ("circulo", "i")}
