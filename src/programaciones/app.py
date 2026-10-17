"""Arranque: una sola instancia, presentación con la carga real y ventana principal (como Partes de salida, sin icono en
la bandeja ni arranque con la sesión: TRD §2).

Prueba de arranque de la CI (`compilar.yml`): con `PROGRAMACIONES_PRUEBA_DE_ARRANQUE=ventana`, la app abre la ventana,
comprueba los datos que lleva dentro (catálogo, esquemas, plantilla y tipografías) y QtPdf, escribe una marca por cada
cosa en el registro y sale. Si algo falla, sale con código 1 y sin la marca de la ventana.
"""

from __future__ import annotations

import getpass
import logging
import os
import sys

from PyQt6.QtCore import QEvent, QObject, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication, QMessageBox

from . import NOMBRE_APP, __version__
from .rutas import recursos
from .sistema import configurar_registro

logger = logging.getLogger(__name__)
SERVIDOR = f"programaciones-{getpass.getuser()}"
#: Prueba de humo del ejecutable congelado (CI de macOS y Windows): llega a la ventana, comprueba y sale.
VARIABLE_PRUEBA = "PROGRAMACIONES_PRUEBA_DE_ARRANQUE"
MARCA_PRUEBA = "PRUEBA DE ARRANQUE: ventana principal a la vista"


def _ya_abierta() -> bool:
    """Si hay otra abierta, le pide que se muestre y devuelve True."""
    s = QLocalSocket()
    s.connectToServer(SERVIDOR)
    if s.waitForConnected(400):
        s.write(b"mostrar")
        s.flush()
        s.waitForBytesWritten(400)
        s.disconnectFromServer()
        return True
    return False


class _Reactivar(QObject):
    """En macOS, pulsar el icono del Dock con la ventana minimizada la vuelve a mostrar."""

    def __init__(self, ventana):
        super().__init__()
        self._ventana = ventana

    def eventFilter(self, objeto, evento):  # noqa: N802
        if evento.type() == QEvent.Type.ApplicationActivate and self._ventana.isMinimized():
            self._ventana.mostrar_al_frente()
        return False


def icono_app() -> QIcon:
    """El icono de la app (no el logo de EPLA, que solo va dentro del documento)."""
    ruta = recursos() / "icono.png"
    return QIcon(str(ruta)) if ruta.exists() else QIcon()


def prueba_de_arranque(ventana) -> bool:
    """Lo que la CI comprueba en la app compilada, con una marca en el registro por cada pieza."""
    from .diagnostico import MARCA_DATOS, comprobar_datos
    from .ui.vista_previa import MARCA_QTPDF, comprobar_qtpdf

    if not ventana.isVisible():
        logger.error("PRUEBA DE ARRANQUE: fallo: la ventana principal no está a la vista")
        return False
    try:
        for linea in comprobar_datos(ventana.ctx.catalogo):
            logger.info("%s: %s", MARCA_DATOS, linea)
        logger.info("%s: %s", MARCA_QTPDF, comprobar_qtpdf())
    except Exception:  # noqa: BLE001 - la prueba informa y falla, no se cuelga
        logger.exception("PRUEBA DE ARRANQUE: fallo")
        return False
    logger.info(MARCA_PRUEBA)
    return True


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    prueba = os.environ.get(VARIABLE_PRUEBA)
    ruta_log = configurar_registro()
    logger.info("Arranca %s %s (%s)", NOMBRE_APP, __version__, sys.platform)
    app = QApplication(argv)
    app.setApplicationName(NOMBRE_APP)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("EPLA")
    app.setWindowIcon(icono_app())

    if not prueba and _ya_abierta():
        logger.info("Ya había una instancia abierta; se le pide que se muestre")
        return 0
    QLocalServer.removeServer(SERVIDOR)
    servidor = QLocalServer()
    servidor.listen(SERVIDOR)

    from .ui import estilo

    estilo.cargar_fuentes()
    estilo.aplicar(app)

    from .contexto import Contexto
    from .ui.presentacion import Presentacion
    from .ui.ventana import VentanaPrincipal

    presentacion = Presentacion()
    presentacion.show()
    presentacion.paso("Cargando el catálogo…", 3)
    try:
        ctx = Contexto(avance=presentacion.paso)
    except Exception as e:  # noqa: BLE001
        logger.exception("No se pudo preparar la aplicación")
        presentacion.close()
        if prueba:
            return 1
        QMessageBox.critical(None, NOMBRE_APP, f"No se puede abrir la aplicación:\n{e}\n\nRegistro: {ruta_log}")
        return 1
    presentacion.paso("Preparando la ventana…", 86)
    ventana = VentanaPrincipal(ctx)
    app.ventana = ventana

    def conexion():
        s = servidor.nextPendingConnection()
        if s is not None:
            s.readyRead.connect(ventana.mostrar_al_frente)

    servidor.newConnection.connect(conexion)
    reactivar = _Reactivar(ventana)
    app.installEventFilter(reactivar)
    presentacion.terminar(ventana.mostrar_al_frente)

    if prueba:
        def fin_de_prueba():
            app.exit(0 if prueba_de_arranque(ventana) else 1)

        QTimer.singleShot(3000, fin_de_prueba)
    else:
        QTimer.singleShot(1200, ventana.primer_arranque)   # nombre y carpeta del curso escolar (HU-11)
        QTimer.singleShot(4000, ventana.buscar_actualizaciones)
    codigo = app.exec()
    logger.info("Cierre (%s)", codigo)
    return codigo
