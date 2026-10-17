"""Ayudas de la app (copia de `ui/ayuda.py` de Partes de salida): pasos numerados, aviso y notas.

Los textos están aquí, juntos, para cambiarlos sin tocar la ventana de Ajustes. Las capturas de cada paso
(`imagenes`) se añaden cuando las haya, como en Partes de salida.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ..rutas import recursos
from . import estilo
from .componentes import boton, etiqueta


@dataclass
class Ayuda:
    titulo: str
    pasos: list[str]
    aviso: str = ""
    titulo_aviso: str = "Importante."
    notas: list[str] = field(default_factory=list)
    #: Captura (archivo en `recursos/`, ancho en px) que se enseña debajo de un paso (1, 2…).
    imagenes: dict[int, tuple[str, int]] = field(default_factory=dict)


AYUDA_TEAMS = Ayuda(
    titulo="Añadir la carpeta de Teams a OneDrive",
    pasos=[
        "<b>Abre la carpeta del curso en Teams.</b> En el canal del departamento, pestaña <b>Archivos</b>, la carpeta "
        "de las programaciones del curso.",
        "<b>«Agregar acceso directo a Mis archivos»</b>, en el menú de la carpeta. Solo hace falta una vez por curso.",
        "<b>Elígela en Ajustes → Curso escolar.</b> Aparece dentro de tu OneDrive. Al exportar, la app guarda ahí "
        "y Teams lo sube solo.",
    ],
    notas=[
        "Si no la tienes en OneDrive, puedes pegar el enlace de la carpeta de Teams: la app exporta en este equipo y "
        "abre la carpeta en el navegador para que subas los archivos.",
    ],
)


class DialogoAyuda(QDialog):
    def __init__(self, ayuda: Ayuda, padre=None):
        super().__init__(padre)
        self.setWindowTitle("Ayuda")
        self.setMinimumWidth(620)
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)
        desplazar = QScrollArea()
        desplazar.setWidgetResizable(True)
        desplazar.setFrameShape(QFrame.Shape.NoFrame)
        desplazar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        contenido = QWidget()
        desplazar.setWidget(contenido)
        exterior.addWidget(desplazar, 1)
        capa = QVBoxLayout(contenido)
        capa.setContentsMargins(26, 22, 26, 8)
        capa.setSpacing(14)
        titulo = QLabel(ayuda.titulo)
        titulo.setFont(estilo.fuente(24, QFont.Weight.Bold, estilo.TITULAR))
        capa.addWidget(titulo)

        pasos = QGridLayout()
        pasos.setHorizontalSpacing(12)
        pasos.setVerticalSpacing(10)
        fila = 0
        for i, texto in enumerate(ayuda.pasos, start=1):
            fila += 1
            numero = QLabel(str(i))
            numero.setFixedSize(26, 26)
            numero.setAlignment(Qt.AlignmentFlag.AlignCenter)
            numero.setStyleSheet(
                f"background:{estilo.T['accent']};color:{estilo.T['accent_ink']};border-radius:13px;font-weight:700;"
            )
            pasos.addWidget(numero, fila, 0, Qt.AlignmentFlag.AlignTop)
            linea = QLabel(texto)
            linea.setWordWrap(True)
            linea.setTextFormat(Qt.TextFormat.RichText)
            pasos.addWidget(linea, fila, 1)
            if i in ayuda.imagenes:
                fila += 1
                pasos.addWidget(self._captura(*ayuda.imagenes[i]), fila, 1, Qt.AlignmentFlag.AlignLeft)
        pasos.setColumnStretch(1, 1)
        capa.addLayout(pasos)

        if ayuda.aviso:
            caja = QFrame()
            caja.setStyleSheet(f"QFrame {{ background:{estilo.T['warn_soft']}; border-radius:9px; }}")
            fila = QHBoxLayout(caja)
            fila.setContentsMargins(14, 12, 14, 12)
            texto = QLabel(f"<b>{ayuda.titulo_aviso}</b> {ayuda.aviso}")
            texto.setWordWrap(True)
            texto.setStyleSheet(f"color:{estilo.T['warn']};")
            fila.addWidget(texto)
            capa.addWidget(caja)
        if ayuda.notas:
            n = etiqueta("<br>".join(f"• {nota}" for nota in ayuda.notas), "muted", envolver=True)
            n.setTextFormat(Qt.TextFormat.RichText)
            capa.addWidget(n)

        capa.addStretch(1)
        botones = QHBoxLayout()
        botones.setContentsMargins(26, 8, 26, 18)
        botones.addStretch(1)
        entendido = boton("Entendido", primario=True)
        entendido.setDefault(True)
        entendido.clicked.connect(self.accept)
        botones.addWidget(entendido)
        exterior.addLayout(botones)
        self.resize(660, min(760, contenido.sizeHint().height() + 70))

    @staticmethod
    def _captura(nombre: str, ancho: int) -> QLabel:
        """Captura con borde fino, al ancho indicado."""
        imagen = QLabel()
        pm = QPixmap(str(recursos() / nombre))
        dpr = 2.0
        if not pm.isNull():
            pm = pm.scaledToWidth(int(ancho * dpr), Qt.TransformationMode.SmoothTransformation)
            pm.setDevicePixelRatio(dpr)
        imagen.setPixmap(pm)
        imagen.setStyleSheet(f"border: 1px solid {estilo.T['line']}; border-radius: 6px; padding: 2px; background: #ffffff;")
        imagen.setAlignment(Qt.AlignmentFlag.AlignLeft)
        return imagen
