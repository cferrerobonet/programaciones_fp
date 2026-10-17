"""Ventana de novedades y actualización de la app: copia de `ui/dialogos.py` de Partes de salida (ADR-010).

`DialogoNovedades` es el mismo diálogo con el círculo dorado; `DialogoActualizacion` lo usa con «↑» y las notas del
release (la entrada del `CHANGELOG.md`), y las ventanas «Cambios en el currículo» (ADR-015, F5: `modales.py`), con «§».
`buscar_catalogo` comprueba el catálogo publicado en segundo plano, como `buscar_actualizaciones` la versión de la app.
"""

from __future__ import annotations

import logging
import platform
import tempfile
import webbrowser
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QTextBrowser,
    QVBoxLayout,
)

from .. import NOMBRE_APP, __version__
from ..actualizaciones import PAGINA_DE_RELEASES, abrir_instalador, comprobar, descargar_verificado, instalar_macos
from . import estilo
from .componentes import boton, etiqueta

logger = logging.getLogger(__name__)


class _Puente(QObject):
    """Lleva la respuesta de GitHub del hilo de comprobación a la interfaz."""

    respuesta = pyqtSignal(str, str, str)
    resultado = pyqtSignal(object)


_puentes: list[_Puente] = []


def buscar_catalogo(ctx, forzar: bool = False, al_terminar=None) -> None:
    """Catálogo publicado (F5) en segundo plano: como mucho una vez al día salvo con `forzar` («Comprobar ahora»). Si
    llega uno nuevo y verificado, la app pasa a él (`Contexto.cambiar_catalogo`) y `al_terminar(resultado)` lo cuenta."""
    from threading import Thread

    from .. import catalogo_remoto

    puente = _Puente()
    _puentes.append(puente)
    carpeta, actual, faltan = ctx.carpeta, ctx.catalogo.version, ctx.versiones_que_faltan()

    def recibir(res):
        _puentes.remove(puente)
        if res.nuevas:
            ctx.cambiar_catalogo()
        if al_terminar:
            al_terminar(res)

    puente.resultado.connect(recibir)

    def hilo():
        puente.resultado.emit(catalogo_remoto.comprobar(carpeta, actual, faltan, forzar))

    Thread(target=hilo, daemon=True).start()


def buscar_actualizaciones(padre, avisar_si_al_dia: bool = False, al_encontrar=None) -> None:
    """Pregunta a GitHub en segundo plano.

    Si hay versión nueva, llama a `al_encontrar(version, url, notas)` (la ventana principal enseña su botón dorado) o,
    sin él, abre directamente el diálogo.
    """
    puente = _Puente()
    _puentes.append(puente)

    def recibir(version: str, url: str, notas: str):
        _puentes.remove(puente)
        if version:
            (al_encontrar or (lambda v, u, n: ofrecer(padre, v, u, n)))(version, url, notas)
        elif avisar_si_al_dia:
            if notas:
                QMessageBox.information(padre, "Actualizaciones", f"No se ha podido comprobar:\n{notas}")
            else:
                QMessageBox.information(padre, "Actualizaciones", f"Tienes la última versión ({__version__}).")

    puente.respuesta.connect(recibir)
    comprobar(__version__, puente.respuesta.emit, siempre=avisar_si_al_dia)


class DialogoNovedades(QDialog):
    """Círculo dorado con un símbolo, título condensado, explicación, novedades en Markdown y dos botones."""

    def __init__(self, simbolo: str, titulo: str, explicacion: str, notas: str, aceptar: str,
                 titulo_ventana: str, padre=None):
        super().__init__(padre)
        self.setWindowTitle(titulo_ventana)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.resize(520, 420 if notas else 240)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(12)
        cabecera = QHBoxLayout()
        cabecera.setSpacing(14)
        circulo = QLabel(simbolo)
        circulo.setFixedSize(46, 46)
        circulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circulo.setStyleSheet(
            f"background:{estilo.T['gold']};color:#ffffff;border-radius:23px;font-size:24px;font-weight:700;"
        )
        cabecera.addWidget(circulo)
        self.titulo = QLabel(titulo)
        self.titulo.setFont(estilo.fuente(24, QFont.Weight.Bold, estilo.TITULAR))
        self.titulo.setWordWrap(True)
        cabecera.addWidget(self.titulo, 1)
        capa.addLayout(cabecera)
        capa.addWidget(etiqueta(explicacion, "muted", envolver=True))
        if notas:
            capa.addWidget(etiqueta("Novedades", "etiqueta"))
            self.notas = QTextBrowser()
            self.notas.setOpenExternalLinks(True)
            self.notas.setMarkdown(notas)
            capa.addWidget(self.notas, 1)
        else:
            capa.addStretch(1)
        botones = QHBoxLayout()
        botones.addStretch(1)
        luego = boton("Más tarde")
        self.aceptar = boton(aceptar, primario=True)
        self.aceptar.setDefault(True)
        luego.clicked.connect(self.reject)
        self.aceptar.clicked.connect(self.accept)
        botones.addWidget(luego)
        botones.addWidget(self.aceptar)
        capa.addLayout(botones)


class DialogoActualizacion(DialogoNovedades):
    """Aviso de versión nueva, por encima de la app: actualizar es la opción destacada."""

    def __init__(self, version: str, notas: str, padre=None):
        super().__init__(
            "↑", f"Hay una versión nueva: {version}",
            f"Tienes la {__version__}. Se descarga, se cierra la app y se abre el instalador; "
            "tus programaciones y los ajustes se conservan.",
            notas, "Actualizar ahora", "Actualización disponible", padre,
        )


def ofrecer(padre, version: str, url: str, notas: str) -> None:
    dialogo = DialogoActualizacion(version, notas, padre)
    dialogo.raise_()
    dialogo.activateWindow()
    if dialogo.exec() != QDialog.DialogCode.Accepted:
        return
    if not url:
        webbrowser.open(PAGINA_DE_RELEASES)
        return
    _descargar(padre, url, version)


class _Descargador(QThread):
    avance = pyqtSignal(int)
    listo = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url: str, destino: Path):
        super().__init__()
        self._url = url
        self._destino = destino

    def run(self):
        # Solo se abre si el sha256 coincide con el digest del asset en la API de releases.
        try:
            ruta = descargar_verificado(self._url, self._destino, self.avance.emit)
        except ValueError:
            self.error.emit("La dirección de descarga no es de confianza; se cancela.")
            return
        except Exception as e:  # noqa: BLE001
            self.error.emit(f"{e}\n\nSe puede descargar a mano desde {PAGINA_DE_RELEASES}")
            return
        self.listo.emit(str(ruta))


def _descargar(padre, url: str, version: str) -> None:
    destino = Path(tempfile.mkdtemp(prefix="programaciones-actualizacion-")) / url.rsplit("/", 1)[-1]
    progreso = QProgressDialog(f"Descargando {NOMBRE_APP} {version}…", "Cancelar", 0, 100, padre)
    progreso.setWindowTitle("Actualización")
    progreso.setMinimumDuration(0)
    hilo = _Descargador(url, destino)
    progreso._hilo = hilo
    hilo.avance.connect(progreso.setValue)
    progreso.canceled.connect(hilo.terminate)

    def instalar(ruta):
        progreso.close()
        if platform.system() == "Darwin":
            # Se sustituye la app en su carpeta (ADR-029); si no se puede, se abre el DMG y se dice dónde arrastrarla.
            r = instalar_macos(ruta)
            if r.modo == "reserva":
                QMessageBox.information(padre, "Actualización", r.mensaje)
        else:
            abrir_instalador(ruta)   # Windows: el instalador ya instala en la carpeta de la versión anterior (AppId)
        QApplication.instance().quit()

    hilo.listo.connect(instalar)
    hilo.error.connect(lambda e: (progreso.close(), QMessageBox.critical(padre, "Error de descarga", e)))
    hilo.start()
