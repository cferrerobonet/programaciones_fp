"""Ventana principal: barra superior, tres zonas (módulos · ficha y bloques · estado y exportar) y menú de la app.

La navegación es la de la maqueta v0 (aprobada el 2026-10-17): «Programaciones · N» abre el listado y «Ajustes» sus
apartados; el curso escolar y su carpeta de entrega están en Ajustes → Curso escolar (también en el menú, «Curso
escolar…»), y el menú tiene «Abrir…», «Nueva a partir de…», «Guardar», la vista previa, «Exportar», la ayuda y «Acerca
de». Las zonas son de `columnas.py`.

Vista previa y exportar van en una `Tarea` (RNF-03, `gestion.Gestion`) con la ventana «Exportando». Exportar no pregunta
nada salvo que vaya a sustituir un archivo del mismo nombre (DESIGN.md, «Don'ts»).
"""

from __future__ import annotations

import copy
import logging
from pathlib import Path

from PyQt6.QtCore import QSize, QStandardPaths, Qt
from PyQt6.QtGui import QAction, QFont, QKeySequence, QPixmap
from PyQt6.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget

from .. import NOMBRE_APP, __version__, exportacion, herencia, importar_docx, incrustar, programacion, validacion
from ..ajustes import estado_carpeta
from . import estilo
from .columnas import ColumnaEstado, ColumnaFicha, ColumnaModulos
from .componentes import AvisoFlotante, boton, etiqueta, separador_vertical
from .gestion import Gestion

logger = logging.getLogger(__name__)


class VentanaPrincipal(QMainWindow):
    def __init__(self, contexto):
        super().__init__()
        self.ctx = contexto
        self._actualizacion: tuple[str, str, str] | None = None
        self.gestion = Gestion(contexto, self)
        self.ultimo_dialogo = None
        self.setWindowTitle(NOMBRE_APP)
        self.resize(1100, 700)
        self.setMinimumSize(980, 620)

        raiz = QWidget()
        raiz.setObjectName("lienzo_raiz")
        raiz.setStyleSheet(f"#lienzo_raiz {{ background: {estilo.T['surface']}; }}")
        self.setCentralWidget(raiz)
        vertical = QVBoxLayout(raiz)
        vertical.setContentsMargins(0, 0, 0, 0)
        vertical.setSpacing(0)
        vertical.addWidget(self._barra())
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(0)
        self.modulos = ColumnaModulos(contexto)
        self.ficha = ColumnaFicha(contexto)
        self.estado = ColumnaEstado(contexto)
        cuerpo.addWidget(self.modulos)
        cuerpo.addWidget(separador_vertical())
        cuerpo.addWidget(self.ficha, 1)
        cuerpo.addWidget(separador_vertical())
        cuerpo.addWidget(self.estado)
        vertical.addLayout(cuerpo, 1)
        self.aviso = AvisoFlotante(raiz)
        self._menu()
        self.ficha.pedir_heredar.connect(self.abrir_heredar)
        self.ficha.pedir_curriculo.connect(self.ver_curriculo)
        self.estado.pedir_vista_previa.connect(self.abrir_vista_previa)
        self.estado.pedir_exportar.connect(self.exportar)
        self.estado.pedir_paso.connect(self.ficha.ir)
        self.estado.pedir_cambios.connect(self.revisar_cambios)
        self.estado.pedir_programaciones.connect(self.abrir_programaciones)
        self.estado.pedir_abrir.connect(self.abrir_programacion)
        self.ctx.ajustes_cambiados.connect(self.recargar)
        self.ctx.programaciones_cambiadas.connect(self.recargar)
        self.ctx.programacion_abierta.connect(lambda _p: self._acciones())
        self.ctx.programacion_cambiada.connect(self._acciones)
        self.ctx.catalogo_cambiado.connect(self._catalogo_cambiado)
        self.recargar()
        self.pintar_curriculo()

    # Construcción
    def _barra(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("barra")
        barra.setStyleSheet(
            f"#barra {{ background: {estilo.T['surface2']}; border-bottom: 1px solid {estilo.T['line']}; }}"
        )
        fila = QHBoxLayout(barra)
        fila.setContentsMargins(16, 9, 12, 9)
        fila.setSpacing(8)
        titulo = QLabel(NOMBRE_APP)
        titulo.setFont(estilo.fuente(20, QFont.Weight.Bold, estilo.TITULAR))
        fila.addWidget(titulo)
        fila.addWidget(etiqueta("· Formación Profesional", "muted"))
        fila.addStretch(1)
        icono = QLabel()
        icono.setPixmap(estilo.icono_visto(estilo.T["accent"], 15, circulo=True))
        fila.addWidget(icono)
        self.catalogo = etiqueta(f"Catálogo · comprobado el {self.ctx.catalogo.fecha}", "ok")
        self.catalogo.setToolTip("Datos oficiales del BOE y del DOGV. La app comprueba al arrancar, como mucho una vez "
                                 "al día, si hay un catálogo nuevo publicado y firmado (Ajustes → Catálogo).")
        fila.addWidget(self.catalogo)
        fila.addSpacing(6)
        self.recuento = etiqueta("", "muted")
        fila.addWidget(self.recuento)
        fila.addSpacing(6)
        # Avisos dorados de la barra: el de versión nueva (abre el diálogo de actualizar) y el del catálogo publicado
        # con cambios de normativa (F5), con el mismo estilo y comportamiento: botón fijo y, la primera vez, el diálogo.
        self.zona_avisos = QHBoxLayout()
        self.zona_avisos.setSpacing(8)
        self.boton_actualizar = boton("", pequeno=True, dorado=True)
        self.boton_actualizar.hide()
        self.boton_actualizar.clicked.connect(self._ofrecer_actualizacion)
        self.zona_avisos.addWidget(self.boton_actualizar)
        self.boton_curriculo = boton("", pequeno=True, dorado=True)
        self.boton_curriculo.hide()
        self.boton_curriculo.clicked.connect(self.ofrecer_curriculo)
        self.zona_avisos.addWidget(self.boton_curriculo)
        fila.addLayout(self.zona_avisos)
        self.boton_programaciones = boton("", pequeno=True, primario=True)
        self.boton_programaciones.setToolTip("Tus programaciones: abrir, vista previa, exportar, enviar por correo y borrar")
        self.boton_programaciones.clicked.connect(self.abrir_programaciones)
        fila.addWidget(self.boton_programaciones)
        ajustes = boton("Ajustes", pequeno=True)
        ajustes.setToolTip("Ajustes (Ctrl+,)")
        ajustes.clicked.connect(lambda: self.abrir_ajustes())
        fila.addWidget(ajustes)
        return barra

    def _menu(self) -> None:
        barra = self.menuBar()

        def accion(menu, texto: str, disparo, atajo=None, rol=None, activa: bool = True) -> QAction:
            a = QAction(texto, self)
            if atajo is not None:
                a.setShortcut(QKeySequence(atajo))
            if rol is not None:
                a.setMenuRole(rol)
            a.setEnabled(activa)
            a.triggered.connect(disparo)
            menu.addAction(a)
            return a

        archivo = barra.addMenu("Archivo")
        # Guardar, la vista previa y exportar se activan cuando hay una programación abierta.
        self.accion_abrir = accion(archivo, "Abrir…", lambda: self.abrir_archivo(), QKeySequence.StandardKey.Open)
        accion(archivo, "Nueva a partir de…", self.abrir_heredar, "Ctrl+Shift+N")
        self.accion_guardar = accion(archivo, "Guardar", self.guardar, QKeySequence.StandardKey.Save, activa=False)
        archivo.addSeparator()
        self.accion_vista_previa = accion(archivo, "Vista previa", self.abrir_vista_previa,
                                          QKeySequence.StandardKey.Print, activa=False)
        self.accion_exportar = accion(archivo, "Exportar", self.exportar, "Ctrl+E", activa=False)
        archivo.addSeparator()
        accion(archivo, "Programaciones…", self.abrir_programaciones)
        # Lo que hacía el chip del curso de la barra (0.1): abre Ajustes en «Curso escolar».
        self.accion_curso = accion(archivo, "Curso escolar…", lambda: self.abrir_ajustes("Curso escolar"))
        accion(archivo, "Ajustes…", lambda: self.abrir_ajustes(), "Ctrl+,", QAction.MenuRole.PreferencesRole)
        ayuda = barra.addMenu("Ayuda")
        accion(ayuda, "Añadir la carpeta de Teams a OneDrive", self.abrir_ayuda_teams)
        accion(ayuda, "Buscar actualizaciones", lambda: self.buscar_actualizaciones(avisar_si_al_dia=True))
        accion(ayuda, f"Acerca de {NOMBRE_APP}", self.acerca_de, rol=QAction.MenuRole.AboutRole)

    # Datos
    def recargar(self) -> None:
        n = len(self.ctx.programaciones)
        self.recuento.setText(f"Curso {self.ctx.curso_escolar} · {len(self.ctx.modulos)} módulos · {n} programaciones")
        self.boton_programaciones.setText(f"Programaciones · {n}")
        self.estado.recargar()
        self._acciones()

    def _acciones(self) -> None:
        hay = self.ctx.prog is not None
        self.accion_guardar.setEnabled(hay)
        self.accion_vista_previa.setEnabled(hay)
        self.accion_exportar.setEnabled(hay and not validacion.bloquean(self.ctx.avisos()))
        cambios = bool(self.ctx.cambios_de_curriculo())
        self.catalogo.setText("Cambios en el currículo" if cambios else
                              f"Catálogo · comprobado el {self.ctx.catalogo.fecha}")
        self.catalogo.setProperty("rol", "aviso-texto" if cambios else "ok")
        self.catalogo.style().unpolish(self.catalogo)
        self.catalogo.style().polish(self.catalogo)

    # Programación
    def guardar(self) -> None:
        if self.ctx.prog is None:
            return
        self.ctx.guardar()
        self.aviso.mostrar("Guardada en este equipo")

    def abrir_programacion(self, prog: dict) -> None:
        try:
            self.ctx.abrir(prog)
        except programacion.ProgramacionNoValida as e:
            QMessageBox.warning(self, "Abrir", str(e))
            return
        self.revisar_cambios()

    def abrir_archivo(self, ruta: str | Path | None = None) -> None:
        """Un .docx exportado por la app (recupera todos los datos, RF-08) o un .programacion. Un Word sin datos de la
        app (programación antigua) se trae como punto de partida, con sus bloques heredados (RF-10)."""
        if ruta is None:
            ruta, _ = QFileDialog.getOpenFileName(self, "Abrir una programación", str(Path.home()),
                                                  "Programaciones (*.docx *.programacion)")
            if not ruta:
                return
        ruta = Path(ruta)
        try:
            origen = herencia.leer_origen(ruta, self.ctx.catalogo)
        except (OSError, KeyError, ValueError, importar_docx.NoEsProgramacion, incrustar.DatosDanados,
                programacion.ProgramacionNoValida) as e:
            QMessageBox.warning(self, "Abrir", f"No se puede abrir «{ruta.name}»: {e}")
            return
        if not origen.exportada_por_la_app:
            self.abrir_heredar(ruta)
            return
        if origen.modificado_en_word:
            from .modales import DialogoModificadoWord

            self.ultimo_dialogo = DialogoModificadoWord(ruta, self)
            self.ultimo_dialogo.exec()
        self.abrir_programacion(origen.programacion)

    def revisar_cambios(self) -> None:
        """Si el currículo del módulo ha cambiado desde que se hizo la programación, lo enseña (ADR-015)."""
        cambios = self.ctx.cambios_de_curriculo()
        if not cambios:
            return
        from .modales import DialogoCambios

        dialogo = DialogoCambios(self.ctx, cambios, self)
        self.ultimo_dialogo = dialogo
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.aceptar_cambios()

    def aceptar_cambios(self) -> None:
        afectados = self.ctx.aceptar_cambios()
        self._acciones()
        self.pintar_curriculo()
        self.aviso.mostrar("Cambios del currículo aceptados" + (": revisa los bloques marcados" if afectados else ""))

    def ver_curriculo(self) -> None:
        from .modales import DialogoCurriculo

        self.ultimo_dialogo = DialogoCurriculo(self.ctx, self)
        self.ultimo_dialogo.exec()

    def primer_arranque(self) -> None:
        """Al empezar un curso escolar, la app solo pregunta el nombre y la carpeta de entrega (HU-11)."""
        from .modales import DialogoBienvenida

        if DialogoBienvenida.hace_falta(self.ctx):
            self.ultimo_dialogo = DialogoBienvenida(self.ctx, self)
            self.ultimo_dialogo.exec()

    # Vista previa y exportar
    def _motor(self) -> str:
        return self.ctx.gestor.valores.programa_pdf

    def abrir_vista_previa(self) -> None:
        from .vista_previa import DialogoVistaPrevia

        if self.ctx.prog is None:
            DialogoVistaPrevia(self).exec()
            return
        self.gestion.vista_previa([self.ctx.prog], self, lambda rutas: self._miniatura(Path(rutas[0][1])))
        self.ultimo_dialogo = self.gestion.ultimo_dialogo
        self.vista_previa = self.gestion.ultimo_visor

    def _miniatura(self, ruta: Path) -> None:
        from PyQt6.QtPdf import QPdfDocument

        documento = QPdfDocument(self)
        if documento.load(str(ruta)) != QPdfDocument.Error.None_:
            return
        imagen = QPixmap.fromImage(documento.render(0, QSize(212, 300)))
        self.estado.poner_previo(ruta, documento.pageCount(), imagen)
        documento.close()

    def carpeta_destino(self, prog: dict) -> tuple[Path | None, str]:
        """(carpeta donde se escriben los archivos, enlace de Teams que se abre después o «»): la carpeta de entrega
        del curso (ADR-009) o, si no hay, la que elija el profesor."""
        valor = self.ctx.gestor.carpeta_entrega(prog["curso_escolar"])
        estado = estado_carpeta(valor)
        if estado == "local":
            return Path(valor).expanduser(), ""
        if estado == "enlace":
            documentos = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            return Path(documentos or Path.home()) / f"Programaciones {prog['curso_escolar']}", valor
        ruta = QFileDialog.getExistingDirectory(self, "¿Dónde se guarda la programación?", str(Path.home()))
        return (Path(ruta), "") if ruta else (None, "")

    def exportar(self) -> None:
        from .modales import DialogoExportando

        prog = self.ctx.prog
        if prog is None:
            return
        if validacion.bloquean(self.ctx.avisos()):
            self.aviso.mostrar("Corrige los avisos en rojo para exportar")
            return
        carpeta, enlace = self.carpeta_destino(prog)
        if carpeta is None:
            return
        formatos = list(self.ctx.gestor.valores.formatos)
        cat = self.ctx.catalogo
        destinos = exportacion.destinos(prog, cat, carpeta, formatos)
        existentes = [d for d in destinos if d.exists()]
        if existentes:
            r = QMessageBox.question(self, "Exportar", "Ya existe en la carpeta:\n" + "\n".join(d.name for d in existentes)
                                     + "\n\n¿Lo sustituyes?")
            if r != QMessageBox.StandardButton.Yes:
                return
        motor = self._motor()
        pasos = ["Rellenando la plantilla", "Comprobando el documento"]
        if "pdf" in formatos:
            pasos.append(f"Convirtiendo a PDF con {exportacion.texto_motor(motor)}")
        dialogo = DialogoExportando("Exportando", destinos[0].stem, pasos, self)
        self.ultimo_dialogo = dialogo
        datos = copy.deepcopy(prog)
        curso, opciones = self.ctx.datos_curso_de(prog), self.ctx.opciones_documento()

        def listo(res):
            self.ctx.exportada(res.archivos)
            aviso = ""
            if res.error_pdf:
                aviso = f"El PDF no se ha podido hacer ({res.error_pdf}). El Word sí está exportado."
            dialogo.terminar("Exportada", res.archivos, aviso, enlace)

        self.gestion.lanzar(lambda avance: exportacion.exportar(datos, cat, curso, carpeta, formatos, opciones, motor,
                                                                avance), dialogo, listo)
        dialogo.exec()

    def closeEvent(self, e):  # noqa: N802
        self.ctx.guardar()
        self.gestion.esperar()
        self.gestion.limpiar()
        super().closeEvent(e)

    # Ventanas
    def abrir_ajustes(self, apartado: str | None = None) -> None:
        from .ajustes import DialogoAjustes

        dialogo = DialogoAjustes(self.ctx, self, apartado)
        dialogo.exec()
        self.ctx.ajustes_cambiados.emit()

    def abrir_programaciones(self) -> None:
        from .programaciones import DialogoProgramaciones

        dialogo = DialogoProgramaciones(self.ctx, self)
        self.ultimo_dialogo = dialogo
        if dialogo.exec() == QDialog.DialogCode.Accepted and dialogo.elegida:
            self.abrir_programacion(dialogo.elegida)

    def abrir_heredar(self, ruta: str | Path | None = None) -> None:
        from .programaciones import DialogoHeredar

        dialogo = DialogoHeredar(self.ctx, self)
        self.ultimo_dialogo = dialogo
        if ruta:
            dialogo.poner_archivo(ruta)
        if dialogo.exec() == QDialog.DialogCode.Accepted and dialogo.herencia:
            self.heredada(dialogo.herencia)

    def heredada(self, h) -> None:
        self.abrir_programacion(h.programacion)
        self.aviso.mostrar("Programación heredada: revisa y confirma cada bloque")

    def abrir_ayuda_teams(self) -> None:
        from .ayuda import AYUDA_TEAMS, DialogoAyuda

        DialogoAyuda(AYUDA_TEAMS, self).exec()

    def acerca_de(self) -> None:
        from .presentacion import acerca_de

        self._acerca = acerca_de(self)

    # Actualizaciones
    def actualizacion_disponible(self, version: str, url: str, notas: str) -> None:
        """Hay versión nueva: botón dorado fijo y, la primera vez, el diálogo por encima."""
        nueva = self._actualizacion is None or self._actualizacion[0] != version
        self._actualizacion = (version, url, notas)
        self.boton_actualizar.setText(f"↑  Actualizar a {version}")
        self.boton_actualizar.setToolTip("Hay una versión nueva de la aplicación")
        self.boton_actualizar.show()
        if nueva and self.isVisible():
            self._ofrecer_actualizacion()

    def _ofrecer_actualizacion(self) -> None:
        from .dialogos import ofrecer

        if self._actualizacion:
            self.mostrar_al_frente()
            ofrecer(self, *self._actualizacion)

    def buscar_actualizaciones(self, avisar_si_al_dia: bool = False) -> None:
        from .dialogos import buscar_actualizaciones

        buscar_actualizaciones(self, avisar_si_al_dia, al_encontrar=self.actualizacion_disponible)

    # Catálogo publicado (F5)
    def comprobar_catalogo(self, forzar: bool = False) -> None:
        """Al arrancar (y desde Ajustes, con `forzar`): catálogo publicado nuevo → aviso dorado y, la primera vez, el
        diálogo. Sin red, nada: la app sigue con el catálogo que tiene."""
        from .dialogos import buscar_catalogo

        buscar_catalogo(self.ctx, forzar, lambda _r: self.pintar_curriculo(abrir=True))

    def _catalogo_cambiado(self) -> None:
        self.recargar()
        self.pintar_curriculo()

    def pintar_curriculo(self, abrir: bool = False) -> None:
        """«§ Cambios en el currículo» mientras haya un aviso sin ver o programaciones con cambios sin aceptar (se
        recuerdan, ADR-015). Con `abrir`, el diálogo sale solo la primera vez que llega un catálogo."""
        pendientes = self.ctx.con_cambios()
        sin_ver = self.ctx.aviso_por_ver()
        if not pendientes and sin_ver is None:
            self.boton_curriculo.hide()
            return
        self.boton_curriculo.setText("§  Cambios en el currículo" + (f" · {len(pendientes)}" if pendientes else ""))
        self.boton_curriculo.setToolTip("Ha cambiado la normativa del catálogo: qué cambia y qué programaciones tuyas "
                                        "afecta. Cada cambio lo aceptas tú en tu programación.")
        self.boton_curriculo.show()
        if abrir and sin_ver is not None and self.isVisible():
            self.ofrecer_curriculo()

    def ofrecer_curriculo(self) -> None:
        from .modales import DialogoCurriculoNuevo

        pendientes = self.ctx.con_cambios()
        dialogo = DialogoCurriculoNuevo(self.ctx, self.ctx.aviso_por_ver() or self.ctx.novedades_catalogo(),
                                        pendientes, self)
        self.ultimo_dialogo = dialogo
        aceptado = dialogo.exec() == QDialog.DialogCode.Accepted
        self.ctx.marcar_aviso_visto()
        if aceptado and pendientes:
            self.abrir_programacion(pendientes[0]["prog"])
        self.pintar_curriculo()

    def mostrar_al_frente(self) -> None:
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.raise_()
        self.activateWindow()
        self.modulos.buscador.setFocus()

    def version(self) -> str:
        return f"{NOMBRE_APP} {__version__}"
