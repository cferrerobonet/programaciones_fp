"""Ventana de Ajustes (como en Partes de salida): menú lateral y apartados; cada cambio se guarda al momento.

Apartados de la maqueta: Profesor · Carpeta de entrega · Exportación · Correo · Catálogo · Acerca de. Lo que depende de
algo sin decidir (cómo se envía el correo, ADR-014; catálogo remoto, F5; fechas del curso) sale como «pendiente».
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __version__, pdf
from ..ajustes import FORMATOS, IDIOMAS, PROGRAMAS_PDF, correo_valido, estado_carpeta
from ..rutas import carpeta_datos
from . import estilo
from .ayuda import AYUDA_TEAMS, DialogoAyuda
from .componentes import boton, etiqueta, refrescar_estilo

logger = logging.getLogger(__name__)

APARTADOS = ["Profesor", "Carpeta de entrega", "Exportación", "Correo", "Catálogo", "Acerca de"]
NOMBRE_FORMATO = {"docx": "Word", "pdf": "PDF"}
ESTADO_CARPETA = {
    "vacia": ("aviso-texto", "Sin carpeta: al exportar, la app preguntará dónde guardar."),
    "local": ("ok", "Carpeta encontrada en este equipo. Al exportar, los archivos se guardan aquí."),
    "enlace": ("ok", "Enlace de Teams: se exporta en este equipo y se abre la carpeta en el navegador para subirlos."),
    "no_encontrada": ("aviso-texto", "No se encuentra esta carpeta en este equipo."),
}


class Apartado(QScrollArea):
    """Página de Ajustes: título y, debajo, filas «etiqueta | control» o bloques sueltos."""

    def __init__(self, titulo: str):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        contenido = QWidget()
        contenido.setObjectName("pagina")
        self.setWidget(contenido)
        self.capa = QVBoxLayout(contenido)
        self.capa.setContentsMargins(22, 18, 22, 18)
        self.capa.setSpacing(16)
        t = QLabel(titulo)
        t.setFont(estilo.fuente(23, QFont.Weight.Bold, estilo.TITULAR))
        self.capa.addWidget(t)
        self.rejilla: QGridLayout | None = None
        self._fila = 0

    def poner(self, elemento) -> None:
        """Bloque a todo el ancho (botones, avisos…)."""
        self.rejilla = None
        if isinstance(elemento, QWidget):
            self.capa.addWidget(elemento)
        else:
            self.capa.addLayout(elemento)

    def _rejilla(self) -> QGridLayout:
        if self.rejilla is None:
            self.rejilla = QGridLayout()
            self.rejilla.setHorizontalSpacing(18)
            self.rejilla.setVerticalSpacing(12)
            self.rejilla.setColumnMinimumWidth(0, 190)
            self.rejilla.setColumnStretch(1, 1)
            self.capa.addLayout(self.rejilla)
            self._fila = 0
        return self.rejilla

    def campo(self, texto: str, control, ayuda: str = "") -> QLabel | None:
        rejilla = self._rejilla()
        e = QLabel(texto)
        e.setStyleSheet("font-weight:600;")
        arriba = isinstance(control, (QPlainTextEdit, QWidget)) and not isinstance(control, (QLineEdit, QCheckBox, QComboBox))
        rejilla.addWidget(e, self._fila, 0, Qt.AlignmentFlag.AlignTop if arriba else Qt.AlignmentFlag.AlignVCenter)
        if isinstance(control, QWidget):
            rejilla.addWidget(control, self._fila, 1)
        else:
            rejilla.addLayout(control, self._fila, 1)
        self._fila += 1
        if ayuda:
            nota = etiqueta(ayuda, "pequeno", envolver=True)
            rejilla.addWidget(nota, self._fila, 1)
            self._fila += 1
            return nota
        return None

    def fin(self) -> None:
        self.capa.addStretch(1)


def _fila(*widgets, estirar: bool = True) -> QHBoxLayout:
    f = QHBoxLayout()
    f.setSpacing(10)
    for w in widgets:
        f.addWidget(w)
    if estirar:
        f.addStretch(1)
    return f


def _rol(e: QLabel, rol: str, texto: str) -> None:
    e.setProperty("rol", rol)
    e.setText(texto)
    refrescar_estilo(e)


class DialogoAjustes(QDialog):
    def __init__(self, contexto, padre=None, apartado: str | None = None):
        super().__init__(padre)
        self.ctx = contexto
        self.g = contexto.gestor
        self.setWindowTitle("Ajustes")
        self.resize(980, 640)
        capa = QHBoxLayout(self)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(0)
        self.nav = QListWidget()
        self.nav.setObjectName("navegacion")
        self.nav.setFixedWidth(220)
        self.nav.setFont(estilo.fuente(14, QFont.Weight.DemiBold))
        for nombre in APARTADOS:
            item = QListWidgetItem(nombre)
            item.setSizeHint(QSize(0, 38))
            self.nav.addItem(item)
        capa.addWidget(self.nav)
        self.pila = QStackedWidget()
        self.pila.setStyleSheet(f"QStackedWidget, QWidget#pagina {{ background: {estilo.T['surface']}; }}")
        capa.addWidget(self.pila, 1)
        for crear in (self._profesor, self._carpeta, self._exportacion, self._correo, self._catalogo, self._acerca):
            self.pila.addWidget(crear())
        self.nav.currentRowChanged.connect(self.pila.setCurrentIndex)
        self.nav.setCurrentRow(APARTADOS.index(apartado) if apartado in APARTADOS else 0)

    def ir(self, apartado: str) -> None:
        self.nav.setCurrentRow(APARTADOS.index(apartado))

    # Utilidades de enlace
    def _texto(self, clave: str, marcador: str = "") -> QLineEdit:
        campo = QLineEdit(str(getattr(self.g.valores, clave)))
        campo.setPlaceholderText(marcador)
        campo.editingFinished.connect(lambda: self.g.poner(**{clave: campo.text().strip()}))
        return campo

    # Apartados
    def _profesor(self) -> QWidget:
        ap = Apartado("Profesor")
        self.nombre = self._texto("nombre_profesor", "Tu nombre y apellidos")
        ap.campo("Nombre en la portada", self.nombre,
                 "Tal como quieres que salga en la portada. Se propone en cada programación nueva; en las compartidas "
                 "se añade al resto del profesorado.")
        ap.fin()
        return ap

    def _carpeta(self) -> QWidget:
        ap = Apartado("Carpeta de entrega")
        curso = self.ctx.curso_escolar
        self.carpeta = QLineEdit(self.g.carpeta_entrega(curso))
        self.carpeta.setPlaceholderText("Elige la carpeta o pega el enlace de Teams")
        self.carpeta.editingFinished.connect(lambda: self.poner_carpeta(self.carpeta.text()))
        cambiar = boton("Cambiar…", pequeno=True)
        cambiar.clicked.connect(self._elegir_carpeta)
        self.abrir_carpeta = boton("Abrir", pequeno=True)
        self.abrir_carpeta.clicked.connect(self._abrir_carpeta)
        fila = _fila(self.carpeta, cambiar, self.abrir_carpeta, estirar=False)
        fila.setStretch(0, 1)
        self.estado_carpeta = ap.campo(f"Curso {curso}", fila, " ")
        self.estado_carpeta.setWordWrap(True)
        ap.campo("", etiqueta("La carpeta es la misma para todo el profesorado y cambia cada curso.", "pequeno",
                              envolver=True))
        for otro, ruta in sorted(self.g.valores.carpetas_entrega.items(), reverse=True):
            if otro == curso:
                continue
            anterior = QLineEdit(ruta)
            anterior.setReadOnly(True)
            ap.campo(f"Curso {otro}", anterior, "Se guarda para heredar las programaciones de ese curso.")
        ayuda = boton("¿Cómo añado la carpeta de Teams a OneDrive?", pequeno=True)
        ayuda.clicked.connect(lambda: DialogoAyuda(AYUDA_TEAMS, self).exec())
        ap.campo("", _fila(ayuda))
        ap.fin()
        self._pintar_carpeta()
        return ap

    def poner_carpeta(self, valor: str) -> None:
        self.g.poner_carpeta_entrega(self.ctx.curso_escolar, valor)
        if self.carpeta.text() != valor.strip():
            self.carpeta.setText(valor.strip())
        self._pintar_carpeta()

    def _pintar_carpeta(self) -> None:
        estado = estado_carpeta(self.carpeta.text())
        _rol(self.estado_carpeta, *ESTADO_CARPETA[estado])
        self.abrir_carpeta.setEnabled(estado in ("local", "enlace"))

    def _elegir_carpeta(self) -> None:
        actual = self.carpeta.text()
        inicio = actual if estado_carpeta(actual) == "local" else str(Path.home())
        ruta = QFileDialog.getExistingDirectory(self, f"Carpeta de entrega {self.ctx.curso_escolar}", inicio)
        if ruta:
            self.poner_carpeta(ruta)

    def _abrir_carpeta(self) -> None:
        valor = self.carpeta.text().strip()
        url = QUrl(valor) if estado_carpeta(valor) == "enlace" else QUrl.fromLocalFile(valor)
        QDesktopServices.openUrl(url)

    def _exportacion(self) -> QWidget:
        ap = Apartado("Exportación")
        self.formatos: dict[str, QPushButton] = {}
        chips = []
        for f in FORMATOS:
            b = boton(NOMBRE_FORMATO[f], chip=True)
            b.setCheckable(True)
            b.setChecked(f in self.g.valores.formatos)
            b.toggled.connect(lambda _v, f=f: self._formato(f))
            self.formatos[f] = b
            chips.append(b)
        ap.campo("Formatos", _fila(*chips), "Los que se marcan por defecto al exportar.")
        self.programa = QComboBox()
        for clave, texto in PROGRAMAS_PDF.items():
            self.programa.addItem(texto, clave)
        self.programa.setCurrentIndex(max(0, self.programa.findData(self.g.valores.programa_pdf)))
        self.programa.currentIndexChanged.connect(lambda: self.g.poner(programa_pdf=self.programa.currentData()))
        motores = pdf.motores()
        if motores:
            nombres = " y ".join(PROGRAMAS_PDF[m] for m in motores)
            estado = ("ok", f"En este equipo: {nombres}.")
        else:
            estado = ("aviso-texto", "Sin Word ni LibreOffice en este equipo: se exporta solo en Word y se avisa.")
        self.estado_pdf = ap.campo("Programa para el PDF", self.programa, " ")
        _rol(self.estado_pdf, *estado)
        idiomas = QButtonGroup(self)
        botones = []
        for clave, texto in IDIOMAS.items():
            b = boton(texto, chip=True)
            b.setCheckable(True)
            b.setChecked(clave == "es")
            b.setEnabled(clave == "es")
            idiomas.addButton(b)
            botones.append(b)
        ap.campo("Idioma del documento", _fila(*botones),
                 "Valenciano e inglés llegarán en una versión futura. La app siempre está en castellano.")
        self.correo_pie = QLineEdit(self.g.valores.correo_pie)
        self.correo_pie.setPlaceholderText("El correo del departamento")
        self.correo_pie.editingFinished.connect(lambda: self.poner_correo_pie(self.correo_pie.text()))
        self.estado_correo_pie = ap.campo("Correo del pie", self.correo_pie, " ")
        self.estado_correo_pie.setWordWrap(True)
        self._pintar_correo_pie(self.g.valores.correo_pie)
        ap.fin()
        return ap

    def _formato(self, f: str) -> None:
        marcados = [x for x, b in self.formatos.items() if b.isChecked()]
        if not marcados:  # al menos uno: sin formato no hay nada que exportar
            self.formatos[f].blockSignals(True)
            self.formatos[f].setChecked(True)
            self.formatos[f].blockSignals(False)
            return
        self.g.poner(formatos=marcados)

    def poner_correo_pie(self, valor: str) -> bool:
        valor = valor.strip()
        valido = not valor or correo_valido(valor)
        if valido:
            self.g.poner(correo_pie=valor)
        self._pintar_correo_pie(valor)
        return valido

    def _pintar_correo_pie(self, valor: str) -> None:
        if not valor:
            _rol(self.estado_correo_pie, "pequeno", "Sale en el pie de cada página del documento. Vacío: el pie va sin "
                                                    "correo.")
        elif correo_valido(valor):
            _rol(self.estado_correo_pie, "pequeno", "Sale en el pie de cada página del documento.")
        else:
            _rol(self.estado_correo_pie, "aviso-texto", "No parece un correo: no se guarda.")

    def _correo(self) -> QWidget:
        ap = Apartado("Correo")
        aviso = etiqueta(
            "Pendiente de decidir cómo se envían las programaciones por correo: un borrador en tu Outlook o Mail, el "
            "buzón de las apps o tu propia cuenta (ADR-014). Hasta entonces, la app no envía correo.", "aviso",
            envolver=True)
        ap.poner(aviso)
        ap.fin()
        return ap

    def _catalogo(self) -> QWidget:
        ap = Apartado("Catálogo")
        cat = self.ctx.catalogo
        version = etiqueta(cat.version, "mono")
        ap.campo("Versión", version)
        ap.campo("Contenido", etiqueta(f"{len(self.ctx.ciclos)} ciclos · {len(self.ctx.modulos)} módulos · normativa "
                                       "de FP", envolver=True))
        if self.ctx.datos_curso is None:
            curso = etiqueta(f"{self.ctx.curso_escolar}: pendiente. Faltan las fechas de evaluación y de formación en "
                             "empresa del curso.", "aviso-texto", envolver=True)
        else:
            curso = etiqueta(f"{self.ctx.curso_escolar}: fechas de evaluación y de empresa dadas de alta.", "ok")
        ap.campo("Curso escolar", curso)
        cambios = self.ctx.cambios_de_curriculo()
        if self.ctx.prog is None:
            texto_cambios = etiqueta("Se ven al abrir cada programación.", "pequeno", envolver=True)
        elif cambios:
            texto_cambios = etiqueta(f"{len(cambios)} · en {self.ctx.prog['modulo']}: se revisan y se aceptan en la "
                                     "programación abierta («Cambios en el currículo»).", "aviso-texto", envolver=True)
        else:
            texto_cambios = etiqueta(f"Ninguno en {self.ctx.prog['modulo']}.", "ok")
        self.cambios_por_aceptar = texto_cambios
        ap.campo("Cambios por aceptar", texto_cambios)
        ap.campo("Actualización", etiqueta("Pendiente: la descarga del catálogo publicado, con su firma, llega en la "
                                           "fase F5.", "pequeno", envolver=True),
                 "El catálogo se actualiza solo desde el BOE y el DOGV. Cada cambio lo aceptas tú en tu programación: "
                 "la app nunca lo aplica por su cuenta.")
        ap.fin()
        return ap

    def _acerca(self) -> QWidget:
        ap = Apartado("Acerca de")
        buscar = boton("Buscar actualizaciones", pequeno=True)
        buscar.clicked.connect(self._buscar_actualizaciones)
        acerca = boton("Acerca de…", pequeno=True)
        acerca.clicked.connect(self._acerca_de)
        ap.campo("Versión", _fila(etiqueta(__version__, "mono"), buscar, acerca))
        ruta = etiqueta(str(carpeta_datos()), "pequeno", envolver=True)
        ruta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        ap.campo("Carpeta de datos", ruta, "Ajustes y registro de este equipo. Tus programaciones viajan dentro del "
                                           "Word que exportas.")
        ap.fin()
        return ap

    def _acerca_de(self) -> None:
        from .presentacion import acerca_de

        self._ventana_acerca = acerca_de(self)

    def _buscar_actualizaciones(self) -> None:
        from .dialogos import buscar_actualizaciones

        buscar_actualizaciones(self, avisar_si_al_dia=True)
