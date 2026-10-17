"""Los cinco bloques del profesor (DESIGN.md, «Bloques del profesor»; maqueta v0, pantallas 03 a 07).

Cada bloque enseña solo lo que únicamente sabe el profesor (The Only-What-He-Knows Rule): ningún texto fijo de la
plantilla. Lo calculado (pesos, reparto de horas por RA, modalidad, totales) sale de `calculos` y se ve en gris. Cada
cambio pasa por `Contexto.cambiar`, que confirma el paso y guarda solo.

Los párrafos del profesor se escriben como texto: una línea por párrafo, «- » delante para una viñeta (dos espacios más
por cada nivel) y `**negrita**` (`a_texto` y `de_texto`, docs/MODELO_DE_DATOS.md §2).
"""

from __future__ import annotations

import re
import uuid
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .. import calculos
from ..almacen import PASOS
from . import estilo
from .componentes import DelegadoFila, FlujoLayout, boton, desplazable, etiqueta

ORDEN = list(PASOS)
CORTOS = {"profesorado": "Profesorado", "unidades": "Unidades", "empresa": "Empresa", "ra_competencias": "Competencias",
          "metodologia": "Metodología"}
TRIMESTRES = [("1", 1), ("2", 2), ("3", 3), ("1 y 2", [1, 2]), ("2 y 3", [2, 3]), ("1, 2 y 3", [1, 2, 3])]
TIPOS = [("Examen", "E"), ("Práctica", "P"), ("Trabajo", "T")]
MAX_METODOLOGIA = 600   # caracteres del texto libre de metodología propia (DESIGN.md)
RECURSOS_HABITUALES = ("Cuaderno de apuntes", "Libro de texto", "Teams", "Educamos", "Office 365", "CYPE")
ESPACIOS_HABITUALES = ("Aula", "Aula de informática", "Taller")
TEXTOS_PROPIOS = {
    "calificacion": "Calificación (apartado 9)",
    "instrumentos": "Instrumentos de evaluación (11.1)",
    "elementos": "Elementos de evaluación (11.2)",
    "asistencia_y_pruebas": "Asistencia, repetición de pruebas y conductas (11.2)",
}


# ---------------------------------------------------------------------------------------------------------------------
# Párrafos del profesor como texto
# ---------------------------------------------------------------------------------------------------------------------
RE_VINETA = re.compile(r"^( *)- (.*)$")


def a_texto(parrafos) -> str:
    lineas = []
    for p in parrafos or []:
        nivel = p.get("nivel")
        lineas.append(p["texto"] if nivel is None else "  " * nivel + "- " + p["texto"])
    return "\n".join(lineas)


def de_texto(texto: str) -> list[dict]:
    out = []
    for linea in texto.splitlines():
        if not linea.strip():
            continue
        m = RE_VINETA.match(linea)
        if m and m.group(2).strip():
            out.append({"texto": m.group(2).strip(), "nivel": min(2, len(m.group(1)) // 2)})
        elif not m:
            out.append({"texto": linea.strip()})
    return out


def texto_trimestre(t) -> str:
    return next((txt for txt, v in TRIMESTRES if v == t), str(t))


def texto_peso_ajustado(ajuste: dict | None) -> str:
    if not ajuste:
        return ""
    valor = f"{Decimal(str(ajuste['valor'])).normalize():f}".replace(".", ",")
    return f"{valor} | {ajuste['texto']}" if ajuste.get("texto") else valor


def leer_peso_ajustado(texto: str) -> dict | None:
    """«20» o «20,5» → {valor}; «20 | 1,25 % / x práctica» → {valor, texto}; vacío → None (el calculado).
    Lanza ValueError si el número no vale."""
    texto = texto.strip()
    if not texto:
        return None
    numero, _, como = texto.partition("|")
    try:
        valor = Decimal(numero.strip().rstrip("%").strip().replace(",", "."))
    except InvalidOperation as e:
        raise ValueError(f"«{numero.strip()}» no es un porcentaje") from e
    if not 0 <= valor <= 100:
        raise ValueError("El peso va de 0 a 100")
    out: dict = {"valor": int(valor) if valor == valor.to_integral_value() else float(valor)}
    if como.strip():
        out["texto"] = como.strip()
    return out


def nuevo_id(prefijo: str, existentes) -> str:
    while True:
        ident = f"{prefijo}{uuid.uuid4().hex[:6]}"
        if ident not in existentes:
            return ident


def fraccion(v: Fraction) -> str:
    """7,33 · 34 (las horas exactas del reparto, como en la maqueta)."""
    if v.denominator == 1:
        return str(v.numerator)
    return f"{float(v):.2f}".rstrip("0").rstrip(".").replace(".", ",")


class EditorParrafos(QPlainTextEdit):
    """Párrafos del profesor: una línea por párrafo, «- » para viñetas y `**negrita**`."""

    cambiado = pyqtSignal(list)

    def __init__(self, marcador: str, alto: int = 84):
        super().__init__()
        self.setPlaceholderText(marcador)
        self.setToolTip("Una línea por párrafo. «- » delante para una viñeta (dos espacios más por nivel). "
                        "**así** para negrita. Las normas del catálogo que cites salen con su enlace.")
        self.setMinimumHeight(alto)
        self.setTabChangesFocus(True)
        self.textChanged.connect(lambda: self.cambiado.emit(self.parrafos()))

    def poner(self, parrafos) -> None:
        self.blockSignals(True)
        self.setPlainText(a_texto(parrafos))
        self.blockSignals(False)

    def parrafos(self) -> list[dict]:
        return de_texto(self.toPlainText())


class DelegadoEntero(DelegadoFila):
    def __init__(self, maximo: int = 2000, padre=None):
        super().__init__(padre)
        self._maximo = maximo

    def createEditor(self, padre, _opcion, _indice):  # noqa: N802
        e = QSpinBox(padre)
        e.setRange(0, self._maximo)
        e.setFrame(False)
        return e

    def setEditorData(self, editor, indice):  # noqa: N802
        try:
            editor.setValue(int(str(indice.data()).split()[0]))
        except (ValueError, IndexError):
            editor.setValue(0)

    def setModelData(self, editor, modelo, indice):  # noqa: N802
        editor.interpretText()
        modelo.setData(indice, str(editor.value()))


class DelegadoOpciones(DelegadoFila):
    """Desplegable: `opciones()` → [(texto, valor)]; el valor elegido va en UserRole."""

    def __init__(self, opciones, padre=None):
        super().__init__(padre)
        self._opciones = opciones

    def createEditor(self, padre, _opcion, _indice):  # noqa: N802
        c = QComboBox(padre)
        for texto, valor in self._opciones():
            c.addItem(texto, valor)
        return c

    def setEditorData(self, editor, indice):  # noqa: N802
        actual = indice.data(Qt.ItemDataRole.UserRole)
        for i in range(editor.count()):
            if editor.itemData(i) == actual:
                editor.setCurrentIndex(i)

    def setModelData(self, editor, modelo, indice):  # noqa: N802
        modelo.setData(indice, editor.currentData(), Qt.ItemDataRole.UserRole)
        modelo.setData(indice, editor.currentText())


class TablaOrdenable(QTableWidget):
    """Tabla de filas de 30 px que se ordenan arrastrando (la fila entera, por su asa «⋮⋮») o con Alt+↑/↓; Supr o el
    menú contextual quitan la fila."""

    movida = pyqtSignal(int, int)
    quitada = pyqtSignal(int)

    def __init__(self, cabeceras: list[str]):
        super().__init__(0, len(cabeceras))
        self.setHorizontalHeaderLabels(cabeceras)
        self.verticalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(30)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed
                             | QAbstractItemView.EditTrigger.AnyKeyPressed
                             | QAbstractItemView.EditTrigger.SelectedClicked)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDropIndicatorShown(True)
        self.setItemDelegate(DelegadoFila(self))

    def dropEvent(self, e):  # noqa: N802
        origen = self.currentRow()
        destino = self.rowAt(round(e.position().y()))
        if destino < 0:
            destino = self.rowCount() - 1
        e.setDropAction(Qt.DropAction.IgnoreAction)
        e.accept()
        if origen >= 0 and destino != origen:
            self.movida.emit(origen, destino)

    def keyPressEvent(self, e):  # noqa: N802
        r = self.currentRow()
        editando = self.state() == QAbstractItemView.State.EditingState
        if r >= 0 and not editando and e.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.quitada.emit(r)
            return
        if r >= 0 and e.modifiers() & Qt.KeyboardModifier.AltModifier and e.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            destino = r - 1 if e.key() == Qt.Key.Key_Up else r + 1
            if 0 <= destino < self.rowCount():
                self.movida.emit(r, destino)
            return
        super().keyPressEvent(e)

    def contextMenuEvent(self, e):  # noqa: N802
        r = self.rowAt(e.pos().y())
        if r < 0:
            return
        menu = QMenu(self)
        subir = menu.addAction("Subir")
        subir.setEnabled(r > 0)
        bajar = menu.addAction("Bajar")
        bajar.setEnabled(r < self.rowCount() - 1)
        menu.addSeparator()
        quitar = menu.addAction("Quitar esta fila")
        elegida = menu.exec(e.globalPos())
        if elegida is subir:
            self.movida.emit(r, r - 1)
        elif elegida is bajar:
            self.movida.emit(r, r + 1)
        elif elegida is quitar:
            self.quitada.emit(r)


def _item(texto: str = "", editable: bool = False, gris: bool = False, mono: bool = False,
          alinear=Qt.AlignmentFlag.AlignLeft) -> QTableWidgetItem:
    it = QTableWidgetItem(texto)
    banderas = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled
    if editable:
        banderas |= Qt.ItemFlag.ItemIsEditable
    it.setFlags(banderas)
    if gris:
        it.setForeground(QBrush(QColor(estilo.T["muted"])))
    if mono:
        it.setFont(estilo.fuente(13, QFont.Weight.Normal, estilo.MONO))
    it.setTextAlignment(alinear | Qt.AlignmentFlag.AlignVCenter)
    return it


def _quitar_boton(accion) -> QPushButton:
    b = boton("×", enlace=True)
    b.setToolTip("Quitar")
    b.clicked.connect(accion)
    return b


def _columnas(tabla: QTableWidget, anchos: list[int]) -> None:
    cab = tabla.horizontalHeader()
    for i, ancho in enumerate(anchos):
        if ancho:
            cab.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            tabla.setColumnWidth(i, ancho)
        else:
            cab.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)


# ---------------------------------------------------------------------------------------------------------------------
# Bloques
# ---------------------------------------------------------------------------------------------------------------------
class Bloque(QWidget):
    paso = ""

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self._cargando = False

    @property
    def prog(self) -> dict:
        return self.ctx.prog

    def cambiar(self, cambio) -> None:
        if not self._cargando:
            self.ctx.cambiar(self.paso, cambio)

    def cargar(self) -> None:
        """Rehace el bloque con la programación abierta."""

    def refrescar(self) -> None:
        """Vuelve a poner lo calculado (tras un cambio en otro bloque)."""


class BloqueProfesorado(Bloque):
    paso = "profesorado"

    def __init__(self, ctx):
        super().__init__(ctx)
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 8)
        v.setSpacing(10)
        v.addWidget(etiqueta("Profesorado del módulo", "etiqueta"))
        self.filas = QVBoxLayout()
        self.filas.setSpacing(8)
        v.addLayout(self.filas)
        fila = QHBoxLayout()
        self.nuevo = QLineEdit()
        self.nuevo.setPlaceholderText("Añadir otro profesor o profesora…")
        self.nuevo.returnPressed.connect(self.anadir)
        fila.addWidget(self.nuevo, 1)
        anadir = boton("Añadir", pequeno=True)
        anadir.clicked.connect(self.anadir)
        fila.addWidget(anadir)
        v.addLayout(fila)
        v.addWidget(etiqueta("Aparece en la portada. El primero se rellena con tu nombre de Ajustes. Si el módulo es "
                             "compartido, añade al resto.", "muted", envolver=True))
        v.addStretch(1)
        self.campos: list[QLineEdit] = []

    def cargar(self) -> None:
        while self.filas.count():
            item = self.filas.takeAt(0)
            if item.layout():
                while item.layout().count():
                    w = item.layout().takeAt(0).widget()
                    if w:
                        w.deleteLater()
        self.campos = []
        for i, nombre in enumerate(self.prog.get("profesorado", [])):
            fila = QHBoxLayout()
            campo = QLineEdit(nombre)
            campo.editingFinished.connect(self._guardar)
            fila.addWidget(campo, 1)
            fila.addWidget(_quitar_boton(lambda _=False, k=i: self.quitar(k)))
            self.filas.addLayout(fila)
            self.campos.append(campo)

    def _guardar(self) -> None:
        nombres = [c.text().strip() for c in self.campos if c.text().strip()]
        if nombres != self.prog.get("profesorado"):
            self.cambiar(lambda p: p.__setitem__("profesorado", nombres))

    def anadir(self) -> None:
        nombre = self.nuevo.text().strip()
        if not nombre:
            return
        self.nuevo.clear()
        self.cambiar(lambda p: p["profesorado"].append(nombre))
        self.cargar()

    def quitar(self, i: int) -> None:
        self.cambiar(lambda p: p["profesorado"].pop(i))
        self.cargar()


class BloqueUnidades(Bloque):
    """Unidades y prácticas con horas, trimestre y elemento; elementos de evaluación con sus RA y su peso."""

    paso = "unidades"
    U_TITULO, U_HORAS, U_TRIM, U_ELEM, U_RA, U_PESO = 1, 2, 3, 4, 5, 6
    E_TIPO, E_NOMBRE, E_RA, E_HORAS, E_PESO, E_AJUSTE = 1, 2, 3, 4, 5, 6

    def __init__(self, ctx):
        super().__init__(ctx)
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 12, 14, 6)
        v.setSpacing(8)
        fila = QHBoxLayout()
        self.chip_unidades = boton("", chip=True)
        self.chip_elementos = boton("", chip=True)
        self.chip_notas = boton("Notas", chip=True)
        self.chips = [self.chip_unidades, self.chip_elementos, self.chip_notas]
        for i, c in enumerate(self.chips):
            c.setCheckable(True)
            c.clicked.connect(lambda _=False, k=i: self.ver(k))
            fila.addWidget(c)
        fila.addStretch(1)
        self.mas = boton("+ Unidad", pequeno=True)
        self.mas.clicked.connect(self._mas)
        fila.addWidget(self.mas)
        v.addLayout(fila)
        self.pila = QStackedWidget()
        v.addWidget(self.pila, 1)

        self.unidades = TablaOrdenable(["", "Unidad o práctica", "h", "Tr.", "Elemento", "RA", "Peso"])
        _columnas(self.unidades, [14, 0, 32, 40, 84, 42, 52])
        self.unidades.quitada.connect(lambda r: self.quitar("unidades", r))
        self.unidades.setItemDelegateForColumn(self.U_HORAS, DelegadoEntero(padre=self.unidades))
        self.unidades.setItemDelegateForColumn(self.U_TRIM, DelegadoOpciones(lambda: TRIMESTRES, self.unidades))
        self.unidades.setItemDelegateForColumn(self.U_ELEM, DelegadoOpciones(self._opciones_elemento, self.unidades))
        self.unidades.itemChanged.connect(self._unidad_cambiada)
        self.unidades.movida.connect(lambda a, b: self.mover("unidades", a, b))
        self.pila.addWidget(self.unidades)

        self.elementos = TablaOrdenable(["", "Tipo", "Elemento", "RA", "h", "Peso", "A mano"])
        _columnas(self.elementos, [14, 64, 0, 64, 30, 52, 60])
        self.elementos.quitada.connect(lambda r: self.quitar("elementos", r))
        self.elementos.setItemDelegateForColumn(self.E_TIPO, DelegadoOpciones(lambda: TIPOS, self.elementos))
        self.elementos.itemChanged.connect(self._elemento_cambiado)
        self.elementos.cellClicked.connect(self._clic_elemento)
        self.elementos.movida.connect(lambda a, b: self.mover("elementos", a, b))
        self.elementos.horizontalHeaderItem(self.E_AJUSTE).setToolTip(
            "Peso que fijas tú, en % del módulo («20» o «20,5»). Si lo escribes de otra forma en el documento: "
            "«20 | 1,25 % / x práctica». Vacío: el calculado. Con pesos a mano, tienen que sumar el % de centro.")
        self.pila.addWidget(self.elementos)

        notas = QWidget()
        nv = QVBoxLayout(notas)
        nv.setContentsMargins(0, 4, 0, 0)
        nv.addWidget(etiqueta("Notas bajo la tabla 4", "etiqueta"))
        self.notas = EditorParrafos("Opcional: lo que quieras aclarar bajo la tabla de secuenciación.")
        self.notas.cambiado.connect(lambda ps: self.cambiar(lambda p: p.__setitem__("notas_tabla4", ps)))
        nv.addWidget(self.notas)
        self.titulo_contenidos = etiqueta("Contenidos propios del módulo", "etiqueta")
        nv.addWidget(self.titulo_contenidos)
        self.contenidos = EditorParrafos("El módulo no tiene contenidos básicos en el currículo: escribe los suyos.")
        self.contenidos.cambiado.connect(lambda ps: self.cambiar(lambda p: p.__setitem__("contenidos", ps)))
        nv.addWidget(self.contenidos)
        nv.addStretch(1)
        self.pila.addWidget(notas)

        self.pie = etiqueta("", "pequeno", envolver=True)
        v.addWidget(self.pie)
        self.ver(0)

    # Vista
    def ver(self, k: int) -> None:
        self.pila.setCurrentIndex(k)
        for i, c in enumerate(self.chips):
            c.setChecked(i == k)
        self.mas.setVisible(k < 2)
        self.mas.setText("+ Unidad" if k == 0 else "+ Elemento")

    def _opciones_elemento(self):
        return [("—", "")] + [(e.get("nombre") or "(sin nombre)", e["id"]) for e in self.prog.get("elementos", [])]

    def cargar(self) -> None:
        self._cargando = True
        p = self.prog
        H = self.ctx.ficha.horas
        self.unidades.setRowCount(0)
        nombres = {e["id"]: e.get("nombre") or "(sin nombre)" for e in p["elementos"]}
        for r, u in enumerate(p["unidades"]):
            self.unidades.insertRow(r)
            self.unidades.setItem(r, 0, _item("⋮⋮", gris=True))
            self.unidades.setItem(r, self.U_TITULO, _item(u.get("titulo", ""), editable=True))
            self.unidades.setItem(r, self.U_HORAS, _item(str(u.get("horas", 0)), editable=True, mono=True,
                                                         alinear=Qt.AlignmentFlag.AlignRight))
            trim = _item(texto_trimestre(u.get("trimestre")), editable=True)
            trim.setData(Qt.ItemDataRole.UserRole, u.get("trimestre"))
            self.unidades.setItem(r, self.U_TRIM, trim)
            el = _item(nombres.get(u.get("elemento"), "—"), editable=True)
            el.setData(Qt.ItemDataRole.UserRole, u.get("elemento", ""))
            self.unidades.setItem(r, self.U_ELEM, el)
            self.unidades.setItem(r, self.U_RA, _item("", gris=True))
            self.unidades.setItem(r, self.U_PESO, _item("", gris=True, alinear=Qt.AlignmentFlag.AlignRight))
        self.elementos.setRowCount(0)
        for r, e in enumerate(p["elementos"]):
            self.elementos.insertRow(r)
            self.elementos.setItem(r, 0, _item("⋮⋮", gris=True))
            tipo = _item(dict((v, t) for t, v in TIPOS).get(e.get("tipo"), ""), editable=True)
            tipo.setData(Qt.ItemDataRole.UserRole, e.get("tipo"))
            self.elementos.setItem(r, self.E_TIPO, tipo)
            self.elementos.setItem(r, self.E_NOMBRE, _item(e.get("nombre", ""), editable=True))
            ra = _item(calculos.lista_ra(e.get("ra", [])) or "Elegir…")
            ra.setToolTip("Pulsa para elegir los RA de este elemento")
            self.elementos.setItem(r, self.E_RA, ra)
            self.elementos.setItem(r, self.E_HORAS, _item("", gris=True, mono=True, alinear=Qt.AlignmentFlag.AlignRight))
            self.elementos.setItem(r, self.E_PESO, _item("", gris=True, alinear=Qt.AlignmentFlag.AlignRight))
            self.elementos.setItem(r, self.E_AJUSTE, _item(texto_peso_ajustado(e.get("peso_ajustado")), editable=True))
        self.notas.poner(p.get("notas_tabla4"))
        proyecto = self.ctx.ficha.tipo == "proyecto" or bool(p.get("contenidos"))
        self.contenidos.poner(p.get("contenidos"))
        self.titulo_contenidos.setVisible(proyecto)
        self.contenidos.setVisible(proyecto)
        self.pie.setText(f"Arrastra para ordenar (Supr quita la fila). El peso se calcula solo: horas del elemento ÷ {H} h; lo puedes fijar "
                         "a mano en «Elementos de evaluación».")
        self._cargando = False
        self.refrescar()

    def refrescar(self) -> None:
        p = self.prog
        if p is None:
            return
        H = self.ctx.ficha.horas
        h_el = calculos.horas_elementos(p)
        elementos = {e["id"]: e for e in p["elementos"]}
        self._cargando = True
        for r, u in enumerate(p["unidades"]):
            e = elementos.get(u.get("elemento"))
            if self.unidades.item(r, self.U_RA) is None:
                continue
            self.unidades.item(r, self.U_RA).setText(" · ".join(str(x) for x in e.get("ra", [])) if e else "")
            peso = calculos.peso_efectivo(e, h_el.get(e["id"], 0), H) if e else None
            self.unidades.item(r, self.U_PESO).setText(calculos.formato_peso(peso) if peso is not None else "")
        for r, e in enumerate(p["elementos"]):
            if self.elementos.item(r, self.E_HORAS) is None:
                continue
            self.elementos.item(r, self.E_HORAS).setText(str(h_el.get(e["id"], 0)))
            self.elementos.item(r, self.E_PESO).setText(calculos.formato_peso(calculos.peso(h_el.get(e["id"], 0), H)))
        self.chip_unidades.setText(f"Unidades · {len(p['unidades'])}")
        self.chip_elementos.setText(f"Elementos · {len(p['elementos'])}")
        self._cargando = False

    # Cambios
    def _unidad_cambiada(self, item: QTableWidgetItem) -> None:
        if self._cargando:
            return
        r, c = item.row(), item.column()
        if c == self.U_TITULO:
            valor, campo = item.text(), "titulo"
        elif c == self.U_HORAS:
            try:
                valor, campo = max(0, int(item.text())), "horas"
            except ValueError:
                self.cargar()
                return
        elif c == self.U_TRIM:
            valor, campo = item.data(Qt.ItemDataRole.UserRole), "trimestre"
        elif c == self.U_ELEM:
            valor, campo = item.data(Qt.ItemDataRole.UserRole) or "", "elemento"
        else:
            return
        self.cambiar(lambda p: p["unidades"][r].__setitem__(campo, valor))
        self.refrescar()

    def _elemento_cambiado(self, item: QTableWidgetItem) -> None:
        if self._cargando:
            return
        r, c = item.row(), item.column()
        if c == self.E_TIPO:
            tipo = item.data(Qt.ItemDataRole.UserRole)
            self.cambiar(lambda p: p["elementos"][r].__setitem__("tipo", tipo))
        elif c == self.E_NOMBRE:
            nombre = item.text().strip()
            self.cambiar(lambda p: p["elementos"][r].__setitem__("nombre", nombre))
            self.cargar()
            self.ver(1)
            return
        elif c == self.E_AJUSTE:
            try:
                ajuste = leer_peso_ajustado(item.text())
            except ValueError as e:
                item.setToolTip(str(e))
                self.cargar()
                self.ver(1)
                return

            def poner(p):
                if ajuste is None:
                    p["elementos"][r].pop("peso_ajustado", None)
                else:
                    p["elementos"][r]["peso_ajustado"] = ajuste
            self.cambiar(poner)
        self.refrescar()

    def _clic_elemento(self, r: int, c: int) -> None:
        if c == self.E_RA:
            self.elegir_ra(r)

    def elegir_ra(self, r: int, ras: list[int] | None = None) -> None:
        """Menú con los RA del módulo; `ras` los pone directamente (pruebas y teclado)."""
        if ras is None:
            actuales = set(self.prog["elementos"][r].get("ra", []))
            menu = QMenu(self)
            acciones = []
            for n in self.ctx.ficha.numeros_ra:
                a = QAction(f"RA{n}", menu, checkable=True, checked=n in actuales)
                menu.addAction(a)
                acciones.append((n, a))
            rect = self.elementos.visualItemRect(self.elementos.item(r, self.E_RA))
            menu.exec(self.elementos.viewport().mapToGlobal(rect.bottomLeft()))
            ras = [n for n, a in acciones if a.isChecked()]
        valores = sorted(ras)
        self.cambiar(lambda p: p["elementos"][r].__setitem__("ra", valores))
        self.elementos.item(r, self.E_RA).setText(calculos.lista_ra(valores) or "Elegir…")
        self.refrescar()

    def _mas(self) -> None:
        if self.pila.currentIndex() == 0:
            self.anadir_unidad()
        else:
            self.anadir_elemento()

    def anadir_unidad(self) -> None:
        p = self.prog
        ultimo = p["unidades"][-1] if p["unidades"] else None
        u = {"id": nuevo_id("u", {x["id"] for x in p["unidades"]}), "titulo": "", "horas": 0,
             "trimestre": ultimo["trimestre"] if ultimo else 1, "elemento": ultimo["elemento"] if ultimo else ""}
        self.cambiar(lambda q: q["unidades"].append(u))
        self.cargar()
        self.ver(0)
        self.unidades.setCurrentCell(len(p["unidades"]) - 1, self.U_TITULO)

    def anadir_elemento(self) -> None:
        p = self.prog
        e = {"id": nuevo_id("e", {x["id"] for x in p["elementos"]}), "tipo": "E", "nombre": "", "ra": []}
        self.cambiar(lambda q: q["elementos"].append(e))
        self.cargar()
        self.ver(1)
        self.elementos.setCurrentCell(len(p["elementos"]) - 1, self.E_NOMBRE)

    def quitar(self, lista: str, r: int) -> None:
        def quitar(p):
            quitado = p[lista].pop(r)
            if lista == "elementos":
                for u in p["unidades"]:
                    if u.get("elemento") == quitado["id"]:
                        u["elemento"] = ""
        self.cambiar(quitar)
        self.cargar()
        self.ver(0 if lista == "unidades" else 1)

    def mover(self, lista: str, origen: int, destino: int) -> None:
        def mover(p):
            fila = p[lista].pop(origen)
            p[lista].insert(destino, fila)
        self.cambiar(mover)
        self.cargar()
        self.ver(0 if lista == "unidades" else 1)


class BloqueEmpresa(Bloque):
    """Una fila por RA: horas de centro (propuesta y ajuste), si va a empresa y cuántas horas, total y modalidad."""

    paso = "empresa"
    C_RA, C_CENTRO, C_PROP, C_VA, C_EMPRESA, C_TOTAL, C_MODALIDAD = range(7)

    def __init__(self, ctx):
        super().__init__(ctx)
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 12, 14, 6)
        v.setSpacing(8)
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["RA", "Centro", "Prop.", "", "Empresa", "Total", "Modalidad"])
        self.tabla.verticalHeader().hide()
        self.tabla.verticalHeader().setDefaultSectionSize(32)
        self.tabla.setShowGrid(False)
        self.tabla.setItemDelegate(DelegadoFila(self.tabla))
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        _columnas(self.tabla, [0, 50, 46, 26, 56, 40, 76])
        self.tabla.horizontalHeaderItem(self.C_PROP).setToolTip(
            "Reparto a partes iguales de las horas de cada elemento entre sus RA. La app propone el entero más cercano; "
            "tú lo puedes ajustar dentro de sus límites.")
        self.tabla.setItemDelegateForColumn(self.C_CENTRO, DelegadoEntero(padre=self.tabla))
        self.tabla.setItemDelegateForColumn(self.C_EMPRESA, DelegadoEntero(padre=self.tabla))
        self.tabla.itemChanged.connect(self._cambiada)
        v.addWidget(self.tabla, 1)
        self.info = etiqueta("", "info", envolver=True)
        v.addWidget(self.info)
        self.propuesta = boton("Volver a la propuesta", pequeno=True)
        self.propuesta.setToolTip("Quita tus ajustes de horas de centro y deja la propuesta de la app")
        self.propuesta.clicked.connect(self.volver_a_la_propuesta)
        v.addWidget(self.propuesta, 0, Qt.AlignmentFlag.AlignLeft)
        self.pct_curso = QCheckBox("Columna «% del curso (aprox.)» en la tabla 4.1")
        self.pct_curso.toggled.connect(lambda on: self.cambiar(lambda p: p.__setitem__("columna_pct_curso", on)))
        v.addWidget(self.pct_curso)
        v.addWidget(etiqueta("Notas bajo la tabla 4.1", "etiqueta"))
        self.notas = EditorParrafos("Opcional: lo que quieras aclarar bajo la tabla de ponderación.", alto=56)
        self.notas.cambiado.connect(lambda ps: self.cambiar(lambda p: p.__setitem__("notas_tabla41", ps)))
        v.addWidget(self.notas)

    def cargar(self) -> None:
        self._cargando = True
        ficha = self.ctx.ficha
        self.tabla.setRowCount(len(ficha.ra) + 1)
        for r, ra in enumerate(ficha.ra):
            it = _item(f"RA{ra['n']}  {ra['texto']}")
            it.setToolTip(ra["texto"])
            it.setForeground(QBrush(QColor(estilo.T["fg"])))
            self.tabla.setItem(r, self.C_RA, it)
            self.tabla.setItem(r, self.C_CENTRO, _item("", editable=True, mono=True, alinear=Qt.AlignmentFlag.AlignRight))
            self.tabla.setItem(r, self.C_PROP, _item("", gris=True, mono=True, alinear=Qt.AlignmentFlag.AlignRight))
            va = _item()
            va.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            va.setToolTip("Va a empresa")
            self.tabla.setItem(r, self.C_VA, va)
            self.tabla.setItem(r, self.C_EMPRESA, _item("", editable=True, mono=True, alinear=Qt.AlignmentFlag.AlignRight))
            self.tabla.setItem(r, self.C_TOTAL, _item("", mono=True, alinear=Qt.AlignmentFlag.AlignRight))
            self.tabla.setCellWidget(r, self.C_MODALIDAD, etiqueta("", "modalidad"))
        t = len(ficha.ra)
        for c in range(7):
            self.tabla.setItem(t, c, _item("Total" if c == 0 else "", mono=c > 0, alinear=Qt.AlignmentFlag.AlignRight
                                           if c else Qt.AlignmentFlag.AlignLeft))
            self.tabla.item(t, c).setFont(estilo.fuente(14, QFont.Weight.Bold, estilo.MONO if c else estilo.CUERPO))
        self.tabla.removeCellWidget(t, self.C_MODALIDAD)
        self.pct_curso.setChecked(bool(self.prog.get("columna_pct_curso")))
        self.notas.poner(self.prog.get("notas_tabla41"))
        self._cargando = False
        self.refrescar()

    def refrescar(self) -> None:
        p = self.prog
        if p is None or self.tabla.rowCount() != len(self.ctx.ficha.ra) + 1:
            return
        ras = self.ctx.ficha.numeros_ra
        exacto = calculos.reparto(p, ras)
        prop = calculos.propuesta_centro(p, ras)
        lim = calculos.limites(p, ras)
        ajuste = {int(k): v for k, v in (p.get("centro_ajustado") or {}).items()}
        empresa = {int(k): v for k, v in (p.get("empresa") or {}).items()}
        filas = calculos.tabla41(p, ras)
        self._cargando = True
        for r, fila in enumerate(filas):
            n = fila.ra
            centro = self.tabla.item(r, self.C_CENTRO)
            centro.setText(str(fila.centro))
            ajustado = n in ajuste and ajuste[n] != prop[n]
            centro.setBackground(QBrush(QColor(estilo.T["gold_soft"])) if ajustado else QBrush())
            centro.setToolTip(f"Ajustado por ti (propuesta: {prop[n]} h)" if ajustado else "Propuesta de la app")
            pr = self.tabla.item(r, self.C_PROP)
            pr.setText(fraccion(exacto[n]))
            pr.setToolTip(f"Propuesta: {prop[n]} h · límites {lim[n][0]}–{lim[n][1]} h")
            self.tabla.item(r, self.C_VA).setCheckState(Qt.CheckState.Checked if n in empresa
                                                        else Qt.CheckState.Unchecked)
            emp = self.tabla.item(r, self.C_EMPRESA)
            emp.setText(str(empresa[n]) if n in empresa else "—")
            banderas = emp.flags()
            emp.setFlags(banderas | Qt.ItemFlag.ItemIsEditable if n in empresa
                         else banderas & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla.item(r, self.C_TOTAL).setText(str(fila.total))
            mod = self.tabla.cellWidget(r, self.C_MODALIDAD)
            mod.setText(fila.modalidad)
            mod.setProperty("tipo", fila.modalidad)
            mod.style().unpolish(mod)
            mod.style().polish(mod)
        t = len(filas)
        self.tabla.item(t, self.C_CENTRO).setText(str(sum(f.centro for f in filas)))
        self.tabla.item(t, self.C_EMPRESA).setText(str(sum(f.empresa for f in filas)))
        self.tabla.item(t, self.C_TOTAL).setText(str(sum(f.total for f in filas)))
        ajustados = [n for n in ras if n in ajuste and ajuste[n] != prop[n]]
        h_c = calculos.horas_centro(p)
        texto = ("La app propone las horas de centro de cada RA a partes iguales entre los RA de cada elemento "
                 "(«Prop.»). ")
        if ajustados:
            nombres = calculos.lista_ra(ajustados)
            texto += (f"{nombres} {'lo has' if len(ajustados) == 1 else 'los has'} ajustado tú; cada RA tiene que "
                      f"quedar dentro de sus límites y la suma, en las {h_c} h de centro.")
        else:
            texto += f"Puedes ajustar cada una dentro de sus límites; la suma tiene que seguir en las {h_c} h de centro."
        self.info.setText(texto)
        self.propuesta.setEnabled(bool(ajuste))
        self._cargando = False

    def _cambiada(self, item: QTableWidgetItem) -> None:
        if self._cargando or item.row() >= len(self.ctx.ficha.ra):
            return
        n = self.ctx.ficha.ra[item.row()]["n"]
        clave = str(n)
        c = item.column()
        if c == self.C_CENTRO:
            try:
                valor = max(0, int(item.text()))
            except ValueError:
                self.refrescar()
                return
            prop = calculos.propuesta_centro(self.prog, self.ctx.ficha.numeros_ra)[n]

            def centro(p):
                ajuste = p.setdefault("centro_ajustado", {})
                if valor == prop:
                    ajuste.pop(clave, None)
                else:
                    ajuste[clave] = valor
            self.cambiar(centro)
        elif c == self.C_VA:
            va = item.checkState() == Qt.CheckState.Checked

            def empresa(p):
                if va:
                    p["empresa"].setdefault(clave, 0)
                else:
                    p["empresa"].pop(clave, None)
            self.cambiar(empresa)
        elif c == self.C_EMPRESA:
            try:
                valor = max(0, int(item.text()))
            except ValueError:
                self.refrescar()
                return
            self.cambiar(lambda p: p["empresa"].__setitem__(clave, valor))
        self.refrescar()

    def poner_centro(self, n: int, horas: int) -> None:
        self.tabla.item(self.ctx.ficha.numeros_ra.index(n), self.C_CENTRO).setText(str(horas))

    def poner_empresa(self, n: int, horas: int | None) -> None:
        r = self.ctx.ficha.numeros_ra.index(n)
        self.tabla.item(r, self.C_VA).setCheckState(Qt.CheckState.Unchecked if horas is None else Qt.CheckState.Checked)
        if horas is not None:
            self.tabla.item(r, self.C_EMPRESA).setText(str(horas))

    def volver_a_la_propuesta(self) -> None:
        self.cambiar(lambda p: p.__setitem__("centro_ajustado", {}))
        self.refrescar()


class BloqueCompetencias(Bloque):
    """Rejilla RA × letras de competencia del módulo (las del anexo I; en los comunes, las del título)."""

    paso = "ra_competencias"

    def __init__(self, ctx):
        super().__init__(ctx)
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 12, 14, 6)
        v.setSpacing(8)
        v.addWidget(etiqueta("Marca a qué competencias del título contribuye cada RA. Solo aparecen las letras del "
                             "módulo (orientaciones pedagógicas del anexo I).", "muted", envolver=True))
        self.tabla = QTableWidget(0, 0)
        self.tabla.verticalHeader().hide()
        self.tabla.verticalHeader().setDefaultSectionSize(32)
        self.tabla.setShowGrid(False)
        self.tabla.setItemDelegate(DelegadoFila(self.tabla))
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabla.itemChanged.connect(self._cambiada)
        v.addWidget(self.tabla, 1)
        self.estado = etiqueta("", "ok", envolver=True)
        v.addWidget(self.estado)
        self.letras: list[str] = []

    def _letras(self) -> list[str]:
        ficha = self.ctx.ficha
        if ficha.competencias_modulo:
            return list(ficha.competencias_modulo)
        return [c["letra"] for c in self.ctx.catalogo.ciclo(ficha.sigla)["competencias"]]

    def cargar(self) -> None:
        self._cargando = True
        ficha = self.ctx.ficha
        self.letras = self._letras()
        rc = self.prog.get("ra_competencias") or {}
        self.tabla.setColumnCount(len(self.letras) + 1)
        self.tabla.setHorizontalHeaderLabels(["RA"] + [f"{x})" for x in self.letras])
        _columnas(self.tabla, [0] + [30] * len(self.letras))
        self.tabla.setRowCount(len(ficha.ra))
        for r, ra in enumerate(ficha.ra):
            it = _item(f"RA{ra['n']}  {ra['texto']}")
            it.setToolTip(ra["texto"])
            self.tabla.setItem(r, 0, it)
            marcadas = set(rc.get(str(ra["n"]), []))
            for c, letra in enumerate(self.letras, start=1):
                casilla = QTableWidgetItem()
                casilla.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                casilla.setCheckState(Qt.CheckState.Checked if letra in marcadas else Qt.CheckState.Unchecked)
                casilla.setToolTip(f"RA{ra['n']} · competencia {letra})")
                self.tabla.setItem(r, c, casilla)
        self._cargando = False
        self.refrescar()

    def refrescar(self) -> None:
        if self.prog is None:
            return
        rc = self.prog.get("ra_competencias") or {}
        sin = [n for n in self.ctx.ficha.numeros_ra if not rc.get(str(n))]
        usadas = {x for v in rc.values() for x in v}
        libres = [x for x in self.letras if x not in usadas]
        if sin:
            self.estado.setProperty("rol", "aviso-texto")
            self.estado.setText(f"{calculos.lista_ra(sin)} sin competencias: marca al menos una por RA")
        else:
            self.estado.setProperty("rol", "ok")
            self.estado.setText("✓ Cada RA tiene al menos una competencia" + (
                " y todas las letras del módulo están cubiertas" if not libres
                else f"; sin usar: {', '.join(x + ')' for x in libres)}"))
        self.estado.style().unpolish(self.estado)
        self.estado.style().polish(self.estado)

    def _cambiada(self, item: QTableWidgetItem) -> None:
        if self._cargando or item.column() == 0:
            return
        n = self.ctx.ficha.ra[item.row()]["n"]
        letra = self.letras[item.column() - 1]
        marcar = item.checkState() == Qt.CheckState.Checked
        orden = self.letras

        def poner(p):
            actuales = set(p["ra_competencias"].get(str(n), []))
            (actuales.add if marcar else actuales.discard)(letra)
            if actuales:
                p["ra_competencias"][str(n)] = sorted(actuales, key=lambda x: orden.index(x) if x in orden else 99)
            else:
                p["ra_competencias"].pop(str(n), None)
        self.cambiar(poner)
        self.refrescar()

    def marcar(self, n: int, letra: str, si: bool = True) -> None:
        self.tabla.item(self.ctx.ficha.numeros_ra.index(n), self.letras.index(letra) + 1).setCheckState(
            Qt.CheckState.Checked if si else Qt.CheckState.Unchecked)


class _Chips(QWidget):
    """Opciones habituales en chips que ponen o quitan su línea («- Teams») en un editor de párrafos."""

    def __init__(self, opciones, editor: EditorParrafos):
        super().__init__()
        self.editor = editor
        self.capa = FlujoLayout(self, 6)
        self.botones: dict[str, QPushButton] = {}
        for o in opciones:
            b = boton(o, chip=True)
            b.setCheckable(True)
            b.clicked.connect(lambda on, t=o: self.poner(t, on))
            self.capa.addWidget(b)
            self.botones[o] = b
        mas = boton("+ Añadir", chip=True)
        mas.clicked.connect(self._mas)
        self.capa.addWidget(mas)

    def actualizar(self) -> None:
        textos = {p["texto"] for p in self.editor.parrafos()}
        for t, b in self.botones.items():
            b.setChecked(t in textos)

    def poner(self, texto: str, si: bool) -> None:
        ps = [p for p in self.editor.parrafos() if p["texto"] != texto]
        if si:
            ps.append({"texto": texto, "nivel": 0})
        self.editor.setPlainText(a_texto(ps))

    def _mas(self) -> None:
        texto, ok = QInputDialog.getText(self, "Añadir", "Nombre:")
        if ok and texto.strip():
            self.poner(texto.strip(), True)


class BloqueMetodologia(Bloque):
    """Material y recursos, espacios, metodología propia, actividades y, si hace falta, textos propios."""

    paso = "metodologia"

    def __init__(self, ctx):
        super().__init__(ctx)
        fuera = QVBoxLayout(self)
        fuera.setContentsMargins(0, 0, 0, 0)
        dentro = QWidget()
        fuera.addWidget(desplazable(dentro))
        v = QVBoxLayout(dentro)
        v.setContentsMargins(20, 14, 20, 10)
        v.setSpacing(8)

        v.addWidget(etiqueta("Material y recursos", "etiqueta"))
        self.recursos = EditorParrafos("El material del módulo: cuaderno o libro, plataformas, software…")
        self.chips_recursos = _Chips(RECURSOS_HABITUALES, self.recursos)
        v.addWidget(self.chips_recursos)
        v.addWidget(self.recursos)
        self.recursos.cambiado.connect(lambda ps: self._lista("recursos", ps, self.chips_recursos))

        v.addWidget(etiqueta("Espacios", "etiqueta"))
        self.espacios = EditorParrafos("Aulas y talleres del módulo.", alto=60)
        self.chips_espacios = _Chips(ESPACIOS_HABITUALES, self.espacios)
        v.addWidget(self.chips_espacios)
        v.addWidget(self.espacios)
        self.espacios.cambiado.connect(lambda ps: self._lista("espacios", ps, self.chips_espacios))

        v.addWidget(etiqueta("Metodología propia del módulo", "etiqueta"))
        self.metodologia = EditorParrafos("Cómo desarrollas las unidades: teoría, práctica, material, entregas…")
        self.metodologia.cambiado.connect(self._metodologia)
        v.addWidget(self.metodologia)
        self.cuenta = etiqueta("", "pequeno")
        v.addWidget(self.cuenta)
        v.addWidget(etiqueta("Para terminar la metodología (opcional)", "etiqueta"))
        self.final = EditorParrafos("«Finalmente, …»: lo que va al final del apartado.", alto=56)
        self.final.cambiado.connect(lambda ps: self.cambiar(lambda p: p.__setitem__("metodologia_final", ps)))
        v.addWidget(self.final)
        v.addWidget(etiqueta("Actividades complementarias (opcional)", "etiqueta"))
        self.actividades = EditorParrafos("Visitas o actividades propias del módulo.", alto=56)
        self.actividades.cambiado.connect(lambda ps: self.cambiar(lambda p: p.__setitem__("actividades", ps)))
        v.addWidget(self.actividades)

        v.addWidget(etiqueta("Textos propios (opcional)", "etiqueta"))
        v.addWidget(etiqueta("Si un bloque fijo de la plantilla no vale para tu módulo, márcalo y escribe el tuyo: "
                             "sustituye al de la plantilla.", "pequeno", envolver=True))
        self.propios: dict[str, tuple[QCheckBox, EditorParrafos]] = {}
        self._guardados: dict[str, list] = {}
        for clave, nombre in TEXTOS_PROPIOS.items():
            casilla = QCheckBox(f"Usar un texto propio: {nombre}")
            editor = EditorParrafos(f"Tu texto para «{nombre}».", alto=60)
            casilla.toggled.connect(lambda on, k=clave: self._propio(k, on))
            editor.cambiado.connect(lambda ps, k=clave: self._texto_propio(k, ps))
            v.addWidget(casilla)
            v.addWidget(editor)
            self.propios[clave] = (casilla, editor)
        v.addStretch(1)

    def cargar(self) -> None:
        self._cargando = True
        p = self.prog
        self.recursos.poner(p.get("recursos"))
        self.espacios.poner(p.get("espacios"))
        self.metodologia.poner(p.get("metodologia"))
        self.final.poner(p.get("metodologia_final"))
        self.actividades.poner(p.get("actividades"))
        propios = p.get("textos_propios") or {}
        for clave, (casilla, editor) in self.propios.items():
            casilla.setChecked(clave in propios)
            editor.poner(propios.get(clave))
            editor.setVisible(clave in propios)
        self.chips_recursos.actualizar()
        self.chips_espacios.actualizar()
        self._contar()
        self._cargando = False

    def _lista(self, clave: str, ps: list, chips: _Chips) -> None:
        chips.actualizar()
        self.cambiar(lambda p: p.__setitem__(clave, ps))

    def _metodologia(self, ps: list) -> None:
        self._contar()
        self.cambiar(lambda p: p.__setitem__("metodologia", ps))

    def _contar(self) -> None:
        n = len(self.metodologia.toPlainText())
        self.cuenta.setText(f"{n} de {MAX_METODOLOGIA} caracteres" + (" · más largo de lo previsto: resúmelo si "
                                                                      "puedes" if n > MAX_METODOLOGIA else ""))
        self.cuenta.setProperty("rol", "aviso-texto" if n > MAX_METODOLOGIA else "pequeno")
        self.cuenta.style().unpolish(self.cuenta)
        self.cuenta.style().polish(self.cuenta)

    def _propio(self, clave: str, si: bool) -> None:
        casilla, editor = self.propios[clave]
        editor.setVisible(si)
        if self._cargando:
            return
        if si:
            ps = self._guardados.get(clave) or editor.parrafos()
            editor.poner(ps)
            self.cambiar(lambda p: p.setdefault("textos_propios", {}).__setitem__(clave, ps))
        else:
            self._guardados[clave] = editor.parrafos()
            self.cambiar(lambda p: (p.get("textos_propios") or {}).pop(clave, None))

    def _texto_propio(self, clave: str, ps: list) -> None:
        if self.propios[clave][0].isChecked():
            self.cambiar(lambda p: p.setdefault("textos_propios", {}).__setitem__(clave, ps))


CLASES = {"profesorado": BloqueProfesorado, "unidades": BloqueUnidades, "empresa": BloqueEmpresa,
          "ra_competencias": BloqueCompetencias, "metodologia": BloqueMetodologia}
