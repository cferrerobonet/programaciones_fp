"""Ventanas que se abren desde la barra y el menú: «Programaciones» (listado y envío) y «Nueva a partir de…».

Esqueleto de la fase F4, con el diseño de DESIGN.md («Ventanas modales»): título, contenido vacío y botones. El
listado usa `TablaPaginada` (patrón de Web Pedidos); el envío por correo espera a ADR-014.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QLabel, QVBoxLayout

from . import estilo
from .componentes import ZonaSoltar, boton, etiqueta
from .listado import Columna, TablaPaginada

EXTENSIONES = (".docx", ".programacion")


def _titulo(texto: str) -> QLabel:
    t = QLabel(texto)
    t.setFont(estilo.fuente(24, QFont.Weight.Bold, estilo.TITULAR))
    return t


class DialogoProgramaciones(QDialog):
    """Programaciones de este equipo (940 × 600): casilla por fila, «Abrir» y «Enviar N por correo…»."""

    COLUMNAS = [
        Columna("Módulo", lambda p: p.get("modulo", "")),
        Columna("Ciclo y curso", lambda p: p.get("ciclo_curso", ""), ancho=130),
        Columna("Curso escolar", lambda p: p.get("curso_escolar", ""), ancho=120),
        Columna("Estado", lambda p: p.get("estado", ""), ancho=120),
        Columna("Última exportación", lambda p: p.get("exportada", ""), ancho=150),
    ]

    def __init__(self, ctx, padre=None):
        super().__init__(padre)
        self.ctx = ctx
        self.setWindowTitle("Programaciones")
        self.resize(940, 600)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(12)
        capa.addWidget(_titulo("Programaciones"))
        capa.addWidget(etiqueta("Las que has empezado o exportado en este equipo. Marca una o varias para enviarlas.",
                                "muted", envolver=True))
        self.tabla = TablaPaginada(self.COLUMNAS, "programaciones", lambda p: p.get("id", ""), (4, True),
                                   "Buscar por módulo, ciclo o curso")
        self.tabla.poner(ctx.programaciones)
        capa.addWidget(self.tabla, 1)
        botones = QHBoxLayout()
        self.aviso_correo = etiqueta("Envío por correo: pendiente de decidir cómo se envía (ADR-014).", "pequeno")
        botones.addWidget(self.aviso_correo)
        botones.addStretch(1)
        cerrar = boton("Cerrar")
        cerrar.clicked.connect(self.reject)
        self.enviar = boton("Enviar por correo…")
        self.enviar.setEnabled(False)
        self.abrir = boton("Abrir", primario=True)
        self.abrir.setEnabled(False)
        for b in (cerrar, self.enviar, self.abrir):
            botones.addWidget(b)
        capa.addLayout(botones)


class DialogoHeredar(QDialog):
    """«Nueva a partir de…»: se suelta el .docx o el .programacion del curso pasado y se ve qué se hereda."""

    def __init__(self, ctx, padre=None):
        super().__init__(padre)
        self.ctx = ctx
        self.archivo: Path | None = None
        self.setWindowTitle("Nueva a partir de…")
        self.resize(600, 340)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(12)
        capa.addWidget(_titulo("Nueva a partir de…"))
        capa.addWidget(etiqueta(
            "Parte de la programación del curso pasado, tuya o de otro profesor. Lo tuyo llega como «heredado» y lo "
            "revisas bloque a bloque; lo oficial y las fechas se actualizan.", "muted", envolver=True))
        self.zona = ZonaSoltar("Programación del curso pasado",
                               "Arrastra aquí el Word que exportó la app o su archivo .programacion.",
                               "Elegir…", EXTENSIONES, "↥")
        self.zona.boton.clicked.connect(self._elegir)
        self.zona.archivos.connect(lambda rutas: self.poner_archivo(rutas[0]))
        capa.addWidget(self.zona)
        self.resumen = etiqueta("", "muted", envolver=True)
        capa.addWidget(self.resumen)
        capa.addStretch(1)
        botones = QHBoxLayout()
        botones.addStretch(1)
        cancelar = boton("Cancelar")
        cancelar.clicked.connect(self.reject)
        self.heredar = boton("Heredar", primario=True)
        self.heredar.setEnabled(False)
        botones.addWidget(cancelar)
        botones.addWidget(self.heredar)
        capa.addLayout(botones)

    def _elegir(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Programación del curso pasado", str(Path.home()),
                                              "Programaciones (*.docx *.programacion)")
        if ruta:
            self.poner_archivo(ruta)

    def poner_archivo(self, ruta: str | Path) -> None:
        self.archivo = Path(ruta)
        self.resumen.setText(f"Elegido: {self.archivo.name}")
