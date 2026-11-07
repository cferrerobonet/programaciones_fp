"""Editor de los párrafos del profesor como en Word (ADR-045): negrita y viñetas de tres niveles, que es lo que el
documento sabe escribir. Lo guardado no cambia: una lista de párrafos `{texto, nivel}` con `**…**` para la negrita
(docs/MODELO_DE_DATOS.md §2).

- Barra pequeña: Negrita, Viñetas, Menos y Más sangría; y los atajos de Word: ⌘B (Ctrl+B), Tab y Mayús+Tab en una
  viñeta, Intro en una viñeta vacía para salir de la lista y «- » al principio de un párrafo para empezar una.
- Al pegar desde Word (o desde cualquier sitio) se quedan la negrita y las viñetas; el resto (letra, tamaño, color,
  cursiva…) se descarta, porque el documento no lo llevaría. Al copiar, sale HTML limpio con negrita y viñetas.
"""

from __future__ import annotations

import html
import re

from PyQt6.QtCore import QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import (
    QFont,
    QKeySequence,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextDocumentFragment,
    QTextListFormat,
)
from PyQt6.QtWidgets import QHBoxLayout, QTextEdit, QVBoxLayout, QWidget

from .componentes import atajo, boton

NIVELES = 3                     # viñeta, anidada y más anidada (`nivel` 0, 1 y 2)
ESTILOS = (QTextListFormat.Style.ListDisc, QTextListFormat.Style.ListCircle, QTextListFormat.Style.ListSquare)
#: Marca invisible con el nivel de una viñeta de Word («mso-list: l0 level2»), que el HTML de Qt no conserva
MARCA = "⁣"
RE_MSO_PARRAFO = re.compile(r"(<p\b[^>]*mso-list:\s*l\d+\s+level(\d)[^>]*>)", re.I)
RE_MSO_VINETA = re.compile(r"<!(?:--)?\[if !supportLists\](?:--)?>.*?<!(?:--)?\[endif\](?:--)?>", re.I | re.S)
RE_VINETA_ESCRITA = re.compile(r"^[•·▪◦‣]\s+")
RE_VINETA_TEXTO = re.compile(r"^( *)[-•·*]\s+(.*)$")


# ---------------------------------------------------------------------------------------------------------------------
# Párrafos ↔ documento de Qt
# ---------------------------------------------------------------------------------------------------------------------
def _negrita(fmt: QTextCharFormat) -> bool:
    return fmt.fontWeight() >= QFont.Weight.DemiBold


def _limpio(t: str) -> str:
    return re.sub(r"[ \t   ]+", " ", t)


def _texto_de_bloque(bloque) -> str:
    """El texto del bloque con «**…**» en lo que va en negrita (los trozos seguidos en negrita, juntos)."""
    trozos: list[tuple[str, bool]] = []
    it = bloque.begin()
    while not it.atEnd():
        f = it.fragment()
        if f.isValid():
            t = _limpio(f.text().replace("￼", ""))
            b = _negrita(f.charFormat()) and bool(t.strip())
            if trozos and trozos[-1][1] == b:
                trozos[-1] = (trozos[-1][0] + t, b)
            elif t:
                trozos.append((t, b))
        it += 1
    out = ""
    for t, b in trozos:
        if b:
            antes, medio, despues = re.match(r"^(\s*)(.*?)(\s*)$", t, re.S).groups()
            out += f"{antes}**{medio}**{despues}"
        else:
            out += t
    return re.sub(r" {2,}", " ", out).strip()


def parrafos_de_documento(doc: QTextDocument, pegado: bool = False) -> list[dict]:
    """Los párrafos `{texto, nivel}` del documento. `pegado`: también las viñetas de Word (la marca de su nivel) y las
    que llegan escritas («• texto»)."""
    out = []
    bloque = doc.begin()
    while bloque.isValid():
        texto = _texto_de_bloque(bloque)
        nivel = None
        lista = bloque.textList()
        if lista is not None:
            nivel = min(NIVELES - 1, max(0, lista.format().indent() - 1))
        if pegado:
            m = re.match(rf"^(?:\*\*)?{MARCA}(\d){MARCA}(?:\*\*)?\s*", texto)
            if m:
                nivel = min(NIVELES - 1, max(0, int(m.group(1)) - 1))
                texto = texto[m.end():].strip()
            elif nivel is None and RE_VINETA_ESCRITA.match(texto):
                nivel = 0
                texto = RE_VINETA_ESCRITA.sub("", texto)
        texto = texto.replace(MARCA, "").strip()
        if texto.replace("*", "").strip():
            out.append({"texto": texto} if nivel is None else {"texto": texto, "nivel": nivel})
        bloque = bloque.next()
    return out


def html_de_word(h: str) -> str:
    """El HTML que pone Word en el portapapeles, con el nivel de cada viñeta como marca y sin su «·» dibujado."""
    h = RE_MSO_PARRAFO.sub(lambda m: f"{m.group(1)}{MARCA}{m.group(2)}{MARCA}", h)
    return RE_MSO_VINETA.sub("", h)


def parrafos_de_html(h: str) -> list[dict]:
    doc = QTextDocument()
    doc.setHtml(html_de_word(h))
    return parrafos_de_documento(doc, pegado=True)


def parrafos_de_texto(t: str) -> list[dict]:
    """Texto sin formato (también lo escrito como antes: «- » viñeta, dos espacios más por nivel, `**negrita**`)."""
    out = []
    for linea in t.replace("\r\n", "\n").split("\n"):
        if not linea.strip():
            continue
        m = RE_VINETA_TEXTO.match(linea.replace("\t", "  "))
        if m and m.group(2).strip():
            out.append({"texto": _limpio(m.group(2)).strip(), "nivel": min(NIVELES - 1, len(m.group(1)) // 2)})
        elif not m:
            out.append({"texto": _limpio(linea).strip()})
    return out


def _formato_lista(nivel: int) -> QTextListFormat:
    f = QTextListFormat()
    f.setStyle(ESTILOS[nivel])
    f.setIndent(nivel + 1)
    return f


def _escribir(cursor: QTextCursor, texto: str) -> None:
    normal, negrita = QTextCharFormat(), QTextCharFormat()
    normal.setFontWeight(QFont.Weight.Normal)
    negrita.setFontWeight(QFont.Weight.Bold)
    for k, trozo in enumerate(texto.split("**")):
        if trozo:
            cursor.insertText(trozo, negrita if k % 2 else normal)


def poner_parrafos(doc: QTextDocument, parrafos) -> None:
    """El documento con estos párrafos: la negrita como negrita y cada viñeta en su lista y nivel."""
    doc.clear()
    cursor = QTextCursor(doc)
    listas: dict[int, object] = {}
    for i, p in enumerate(parrafos or []):
        if i:
            cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
        nivel = p.get("nivel")
        if nivel is None:
            listas = {}
        else:
            nivel = min(NIVELES - 1, max(0, int(nivel)))
            listas = {k: v for k, v in listas.items() if k <= nivel}
            if nivel in listas:
                listas[nivel].add(cursor.block())
            else:
                listas[nivel] = cursor.createList(_formato_lista(nivel))
        _escribir(cursor, p.get("texto", ""))


def html_de_parrafos(parrafos) -> str:
    """HTML limpio para el portapapeles (Word lo pega con su negrita y sus viñetas)."""
    out, abiertas = [], 0
    for p in parrafos:
        nivel = p.get("nivel")
        quiero = 0 if nivel is None else nivel + 1
        while abiertas < quiero:
            out.append("<ul>")
            abiertas += 1
        while abiertas > quiero:
            out.append("</ul>")
            abiertas -= 1
        partes = "".join(f"<b>{html.escape(t)}</b>" if k % 2 else html.escape(t)
                         for k, t in enumerate(p["texto"].split("**")) if t)
        out.append(f"<li>{partes}</li>" if quiero else f"<p>{partes}</p>")
    out += ["</ul>"] * abiertas
    return "<html><body>" + "".join(out) + "</body></html>"


def texto_de_parrafos(parrafos) -> str:
    return "\n".join(("\t" * p["nivel"] + "• " if p.get("nivel") is not None else "") + p["texto"].replace("**", "")
                     for p in parrafos)


# ---------------------------------------------------------------------------------------------------------------------
# El editor
# ---------------------------------------------------------------------------------------------------------------------
class _Texto(QTextEdit):
    """El cuadro de texto: lo que se pega se queda en negrita y viñetas; Tab sangra dentro de una viñeta."""

    foco = pyqtSignal()   # entra o sale el cursor: la barra enseña el estado solo del cuadro en el que se escribe

    def __init__(self):
        super().__init__()
        self.setObjectName("parrafos")
        self.setAcceptRichText(True)
        self.setTabChangesFocus(True)
        self.document().setDocumentMargin(2)

    def focusInEvent(self, e) -> None:  # noqa: N802
        super().focusInEvent(e)
        self.foco.emit()

    def focusOutEvent(self, e) -> None:  # noqa: N802
        super().focusOutEvent(e)
        self.foco.emit()

    # -- pegar y copiar ------------------------------------------------------------------------------------------------
    def insertFromMimeData(self, origen: QMimeData) -> None:  # noqa: N802
        if origen.hasHtml():
            ps = parrafos_de_html(origen.html())
        elif origen.hasText():
            ps = parrafos_de_texto(origen.text())
        else:
            return
        self.insertar(ps)

    def insertar(self, parrafos) -> None:
        if not parrafos:
            return
        cursor = self.textCursor()
        if len(parrafos) == 1 and parrafos[0].get("nivel") is None:   # un trozo de texto: dentro del párrafo
            _escribir(cursor, parrafos[0]["texto"])
        else:
            temp = QTextDocument()
            poner_parrafos(temp, parrafos)
            cursor.insertFragment(QTextDocumentFragment(temp))
        self.setTextCursor(cursor)

    def createMimeDataFromSelection(self) -> QMimeData:  # noqa: N802
        temp = QTextDocument()
        QTextCursor(temp).insertFragment(self.textCursor().selection())
        ps = parrafos_de_documento(temp)
        datos = QMimeData()
        datos.setHtml(html_de_parrafos(ps))
        datos.setText(texto_de_parrafos(ps))
        return datos

    # -- teclado como en Word ------------------------------------------------------------------------------------------
    def keyPressEvent(self, e) -> None:  # noqa: N802
        cursor = self.textCursor()
        lista = cursor.currentList()
        if e.matches(QKeySequence.StandardKey.Bold):
            self.negrita()
            return
        if e.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab) and lista is not None:
            self.sangrar(-1 if e.key() == Qt.Key.Key_Backtab or e.modifiers() & Qt.KeyboardModifier.ShiftModifier
                         else 1)
            return
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and lista is not None and not cursor.block().text():
            self.quitar_vineta()   # Intro en una viñeta vacía: fuera de la lista
            return
        if e.key() == Qt.Key.Key_Backspace and lista is not None and cursor.atBlockStart() and not cursor.hasSelection():
            self.quitar_vineta()
            return
        super().keyPressEvent(e)
        if e.text() == " " and lista is None:
            antes = self.textCursor().block().text()[:self.textCursor().positionInBlock()]
            if antes in ("- ", "* ", "• "):   # «- » al principio: empieza una viñeta, como en Word
                c = self.textCursor()
                c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                c.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor, 2)
                c.removeSelectedText()
                self.poner_vineta(True)

    # -- órdenes de la barra -------------------------------------------------------------------------------------------
    def negrita(self) -> None:
        f = QTextCharFormat()
        f.setFontWeight(QFont.Weight.Normal if _negrita(self.currentCharFormat()) else QFont.Weight.Bold)
        self.mergeCurrentCharFormat(f)

    def poner_vineta(self, si: bool) -> None:
        cursor = self.textCursor()
        if si and cursor.currentList() is None:
            cursor.createList(_formato_lista(0))
        elif not si and cursor.currentList() is not None:
            self.quitar_vineta()

    def quitar_vineta(self) -> None:
        cursor = self.textCursor()
        bloque = cursor.block()
        lista = cursor.currentList()
        if lista is not None:
            lista.remove(bloque)
        fmt = cursor.blockFormat()
        fmt.setIndent(0)
        cursor.setBlockFormat(fmt)

    def sangrar(self, paso: int) -> None:
        cursor = self.textCursor()
        lista = cursor.currentList()
        if lista is None:
            return
        nivel = min(NIVELES - 1, max(0, lista.format().indent() - 1 + paso))
        cursor.beginEditBlock()
        lista.remove(cursor.block())
        fmt = cursor.blockFormat()
        fmt.setIndent(0)
        cursor.setBlockFormat(fmt)
        # se une a la lista de ese nivel de justo encima, si la hay; si no, empieza una
        anterior = cursor.block().previous()
        vecina = anterior.textList() if anterior.isValid() else None
        while anterior.isValid() and vecina is not None and vecina.format().indent() - 1 > nivel:
            anterior = anterior.previous()
            vecina = anterior.textList() if anterior.isValid() else None
        if vecina is not None and vecina.format().indent() - 1 == nivel:
            vecina.add(cursor.block())
        else:
            cursor.createList(_formato_lista(nivel))
        cursor.endEditBlock()


class EditorParrafos(QWidget):
    """Párrafos del profesor como en Word: negrita y viñetas, con su barra pequeña encima."""

    cambiado = pyqtSignal(list)

    def __init__(self, marcador: str, alto: int = 84):
        super().__init__()
        capa = QVBoxLayout(self)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(4)
        barra = QHBoxLayout()
        barra.setSpacing(4)
        self.texto = _Texto()
        self.texto.setPlaceholderText(marcador)
        self.texto.setMinimumHeight(alto)
        self.texto.setToolTip("Escribe como en Word: negrita y viñetas. Lo que pegues de Word conserva la negrita y "
                              "las viñetas. Las normas del catálogo que cites salen con su enlace.")
        self.b_negrita = boton("N", chip=True)
        self.b_negrita.setToolTip(f"Negrita ({atajo('B')})")
        self.b_vinetas = boton("• Viñetas", chip=True)
        self.b_vinetas.setToolTip("Viñetas (o escribe «- » al principio del párrafo)")
        self.b_menos = boton("⇤", chip=True)
        self.b_menos.setToolTip("Menos sangría (Mayús+Tab)")
        self.b_mas = boton("⇥", chip=True)
        self.b_mas.setToolTip("Más sangría (Tab)")
        for b in (self.b_negrita, self.b_vinetas):
            b.setCheckable(True)
        f = self.b_negrita.font()
        f.setBold(True)
        self.b_negrita.setFont(f)
        for b in (self.b_negrita, self.b_vinetas, self.b_menos, self.b_mas):
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)   # el cursor sigue en el texto
            barra.addWidget(b)
        barra.addStretch(1)
        capa.addLayout(barra)
        capa.addWidget(self.texto)
        self.b_negrita.clicked.connect(lambda: self.texto.negrita())
        self.b_vinetas.clicked.connect(lambda si: self.texto.poner_vineta(si))
        self.b_menos.clicked.connect(lambda: self.texto.sangrar(-1))
        self.b_mas.clicked.connect(lambda: self.texto.sangrar(1))
        self.texto.cursorPositionChanged.connect(self._estado)
        self.texto.foco.connect(self._estado)
        self.texto.currentCharFormatChanged.connect(lambda _f: self._estado())
        self.texto.textChanged.connect(lambda: self.cambiado.emit(self.parrafos()))
        self.texto.textChanged.connect(self._estado)   # viñeta puesta o quitada sin mover el cursor
        self._estado()

    def _estado(self) -> None:
        c = self.texto.textCursor()
        activo = self.texto.hasFocus()
        en_lista = activo and c.currentList() is not None
        self.b_negrita.setChecked(activo and _negrita(self.texto.currentCharFormat()))
        self.b_vinetas.setChecked(en_lista)
        self.b_menos.setEnabled(en_lista)
        self.b_mas.setEnabled(en_lista)

    def poner(self, parrafos) -> None:
        self.texto.blockSignals(True)
        poner_parrafos(self.texto.document(), parrafos)
        self.texto.blockSignals(False)
        self._estado()

    def parrafos(self) -> list[dict]:
        return parrafos_de_documento(self.texto.document())

    def setPlainText(self, texto: str) -> None:  # noqa: N802
        """Los párrafos escritos como texto (`- ` viñeta, `**negrita**`), como si los tecleara el profesor."""
        self.poner(parrafos_de_texto(texto))
        self.cambiado.emit(self.parrafos())

    def toPlainText(self) -> str:  # noqa: N802
        return self.texto.toPlainText()
