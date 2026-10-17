"""Las tres zonas de la ventana principal (DESIGN.md, «The Three Zones Rule»): esqueleto de la fase F4.

- `ColumnaModulos` (300 px): buscador, chips de grado, ciclo y curso, «Limpiar» y la lista de módulos en filas de 58 px.
- `ColumnaFicha` (flexible): estado vacío «Elige un módulo»; con un módulo, su ficha, la caja «DEL CURRÍCULO», la barra
  de pasos y el bloque elegido.
- `ColumnaEstado` (340 px): «PROGRAMACIONES RECIENTES» sin módulo; con módulo, «ESTADO», avisos y «VISTA PREVIA»;
  siempre, abajo, «EXPORTAR» con los chips «Word» y «PDF» y el botón grande «Exportar ⌘E».

Hoy cada zona tiene su título y su estado vacío; las pantallas de la maqueta se rellenan sobre estas clases.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLineEdit, QStackedLayout, QVBoxLayout, QWidget

from . import estilo
from .componentes import EstadoVacio, FlujoLayout, atajo, boton, etiqueta

ELIGE_UN_MODULO = ("Elige un módulo", "Búscalo por código o nombre, o fíltralo por grado, ciclo y curso. "
                   "Los datos oficiales ya están dentro.")


class ColumnaModulos(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setFixedWidth(300)
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 10)
        v.setSpacing(12)
        self.buscador = QLineEdit()
        self.buscador.setObjectName("buscador")
        self.buscador.setPlaceholderText("Código o nombre del módulo")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.addAction(estilo.icono_lupa(estilo.T["muted"]), QLineEdit.ActionPosition.LeadingPosition)
        v.addWidget(self.buscador)
        self.cuenta = etiqueta(f"{len(ctx.modulos)} módulos · {len(ctx.ciclos)} ciclos", "pequeno")
        v.addWidget(self.cuenta)
        self.lista = QWidget()  # la lista de módulos (QListView con su delegado) sustituye a este hueco
        v.addWidget(self.lista, 1)


class ColumnaFicha(QWidget):
    VACIA, FICHA = 0, 1

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.pila = QStackedLayout(self)
        self.vacio = EstadoVacio(*ELIGE_UN_MODULO, icono=estilo.icono_documento(estilo.T["muted"], 30))
        self.pila.addWidget(self.vacio)
        self.ficha = QWidget()  # cabecera, «DEL CURRÍCULO», pasos y bloque
        self.pila.addWidget(self.ficha)
        self.pila.setCurrentIndex(self.VACIA)


class ColumnaEstado(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setFixedWidth(340)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 14)
        v.setSpacing(10)
        self.titulo = etiqueta("Programaciones recientes", "etiqueta")
        v.addWidget(self.titulo)
        self.recientes = etiqueta("Aún no hay programaciones en este equipo.", "muted", envolver=True)
        v.addWidget(self.recientes)
        v.addStretch(1)
        v.addWidget(etiqueta("Exportar", "etiqueta"))
        chips = QWidget()
        fila = FlujoLayout(chips, 6)
        self.chip_word = boton("Word", chip=True)
        self.chip_pdf = boton("PDF", chip=True)
        for b in (self.chip_word, self.chip_pdf):
            b.setCheckable(True)
            fila.addWidget(b)
        v.addWidget(chips)
        self.boton_exportar = boton(f"Exportar  {atajo('E')}", primario=True, grande=True)
        self.boton_exportar.setEnabled(False)
        v.addWidget(self.boton_exportar)
        self.resumen = etiqueta("Elige un módulo para empezar", "muted")
        self.resumen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.resumen.setWordWrap(True)
        v.addWidget(self.resumen)
        self.recargar()

    def recargar(self) -> None:
        formatos = self.ctx.gestor.valores.formatos
        self.chip_word.setChecked("docx" in formatos)
        self.chip_pdf.setChecked("pdf" in formatos)
