"""Ventana principal: barra superior, tres zonas (módulos · ficha y bloques · estado y exportar) y menú de la app.

La navegación es la de la maqueta v0 (aprobada el 2026-10-17): «Programaciones · N» abre el listado, «Ajustes» sus
apartados, el chip del curso la carpeta de entrega, y el menú «Abrir…», «Nueva a partir de…», la vista previa, la ayuda
y «Acerca de». Las zonas son de `columnas.py`.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont, QKeySequence
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from .. import NOMBRE_APP, __version__
from . import estilo
from .columnas import ColumnaEstado, ColumnaFicha, ColumnaModulos
from .componentes import AvisoFlotante, boton, etiqueta, separador_vertical

logger = logging.getLogger(__name__)


class VentanaPrincipal(QMainWindow):
    def __init__(self, contexto):
        super().__init__()
        self.ctx = contexto
        self._actualizacion: tuple[str, str, str] | None = None
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
        self.ctx.ajustes_cambiados.connect(self.recargar)
        self.recargar()

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
        self.catalogo = etiqueta(f"Catálogo · comprobado el {self.ctx.catalogo.version.replace('.', '-')}", "ok")
        self.catalogo.setToolTip("Datos oficiales del BOE y del DOGV que lleva la app. La descarga de las "
                                 "actualizaciones del catálogo llega en la fase F5.")
        fila.addWidget(self.catalogo)
        fila.addSpacing(6)
        self.recuento = etiqueta("", "muted")
        fila.addWidget(self.recuento)
        fila.addSpacing(6)
        self.boton_curso = boton(self.ctx.curso_escolar, pequeno=True)
        self.boton_curso.setToolTip("Curso escolar: carpeta de entrega en Ajustes")
        self.boton_curso.clicked.connect(lambda: self.abrir_ajustes("Carpeta de entrega"))
        fila.addWidget(self.boton_curso)
        # Aviso de versión nueva: dorado y bien visible; abre el diálogo de actualizar.
        self.boton_actualizar = boton("", pequeno=True, dorado=True)
        self.boton_actualizar.hide()
        self.boton_actualizar.clicked.connect(self._ofrecer_actualizacion)
        fila.addWidget(self.boton_actualizar)
        self.boton_programaciones = boton("", pequeno=True, primario=True)
        self.boton_programaciones.setToolTip("Tus programaciones: abrir y enviar por correo")
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
        # «Abrir…», la vista previa y exportar se activan cuando hay una programación (siguiente tanda de F4).
        self.accion_abrir = accion(archivo, "Abrir…", lambda: None, QKeySequence.StandardKey.Open, activa=False)
        accion(archivo, "Nueva a partir de…", self.abrir_heredar, "Ctrl+Shift+N")
        archivo.addSeparator()
        self.accion_vista_previa = accion(archivo, "Vista previa", self.abrir_vista_previa,
                                          QKeySequence.StandardKey.Print, activa=False)
        self.accion_exportar = accion(archivo, "Exportar", lambda: None, "Ctrl+E", activa=False)
        archivo.addSeparator()
        accion(archivo, "Programaciones…", self.abrir_programaciones)
        accion(archivo, "Ajustes…", lambda: self.abrir_ajustes(), "Ctrl+,", QAction.MenuRole.PreferencesRole)
        ayuda = barra.addMenu("Ayuda")
        accion(ayuda, "Añadir la carpeta de Teams a OneDrive", self.abrir_ayuda_teams)
        accion(ayuda, "Buscar actualizaciones", lambda: self.buscar_actualizaciones(avisar_si_al_dia=True))
        accion(ayuda, f"Acerca de {NOMBRE_APP}", self.acerca_de, rol=QAction.MenuRole.AboutRole)

    # Datos
    def recargar(self) -> None:
        n = len(self.ctx.programaciones)
        self.recuento.setText(f"{len(self.ctx.modulos)} módulos · {n} programaciones")
        self.boton_programaciones.setText(f"Programaciones · {n}")
        self.estado.recargar()

    # Ventanas
    def abrir_ajustes(self, apartado: str | None = None) -> None:
        from .ajustes import DialogoAjustes

        dialogo = DialogoAjustes(self.ctx, self, apartado)
        dialogo.exec()
        self.ctx.ajustes_cambiados.emit()

    def abrir_programaciones(self) -> None:
        from .programaciones import DialogoProgramaciones

        DialogoProgramaciones(self.ctx, self).exec()

    def abrir_heredar(self) -> None:
        from .programaciones import DialogoHeredar

        DialogoHeredar(self.ctx, self).exec()

    def abrir_vista_previa(self) -> None:
        from .vista_previa import DialogoVistaPrevia

        DialogoVistaPrevia(self).exec()

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

    def mostrar_al_frente(self) -> None:
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.raise_()
        self.activateWindow()
        self.modulos.buscador.setFocus()

    def version(self) -> str:
        return f"{NOMBRE_APP} {__version__}"
