"""Editor de los párrafos del profesor como en Word (ADR-045): negrita y viñetas, pegar desde Word y copiar a Word.
Lo guardado no cambia: `{texto, nivel}` con `**negrita**`."""
import pytest
from PyQt6.QtCore import QMimeData, Qt
from PyQt6.QtGui import QTextCursor

from programaciones.ui.editor import EditorParrafos, parrafos_de_html, parrafos_de_texto

pytestmark = pytest.mark.ui

PARRAFOS = [{"texto": "Párrafo ficticio con **negrita** en medio."}, {"texto": "Viñeta ficticia", "nivel": 0},
            {"texto": "Anidada con **dos** **trozos**", "nivel": 1}, {"texto": "Más anidada", "nivel": 2},
            {"texto": "Otra del primer nivel", "nivel": 0}, {"texto": "**Párrafo entero en negrita**"}]

#: Lo que pone Word en el portapapeles (inventado, con su forma): viñetas como párrafos «mso-list» con el «·» dibujado
#: dentro de un bloque condicional, negrita con <b> y letra, color y cursiva que el documento no lleva.
HTML_WORD = """<html xmlns:o="urn:schemas-microsoft-com:office:office"><body lang=ES>
<p class=MsoNormal><b>Negrita ficticia</b> y texto con <span style='color:red;font-family:"Comic Sans MS"'>color</span>
y <i>cursiva</i>.</p>
<p class=MsoListParagraphCxSpFirst style='margin-left:36.0pt;text-indent:-18.0pt;mso-list:l0 level1 lfo1'><![if !supportLists]><span style='font-family:Symbol'><span style='mso-list:Ignore'>·<span style='font:7.0pt "Times New Roman"'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </span></span></span><![endif]>Viñeta ficticia de Word</p>
<p class=MsoListParagraphCxSpLast style='margin-left:72.0pt;text-indent:-18.0pt;mso-list:l0 level2 lfo1'><!--[if !supportLists]--><span style='font-family:"Courier New"'><span style='mso-list:Ignore'>o<span style='font:7.0pt "Times New Roman"'>&nbsp;&nbsp; </span></span></span><!--[endif]-->Anidada <b>ficticia</b></p>
<p class=MsoNormal>&nbsp;</p>
</body></html>"""


@pytest.fixture
def editor(qtbot):
    e = EditorParrafos("Marcador ficticio")
    qtbot.addWidget(e)
    e.show()
    return e


def test_ida_y_vuelta_sin_perder_nada(editor):
    editor.poner(PARRAFOS)
    assert editor.parrafos() == PARRAFOS
    assert "**" not in editor.toPlainText(), "la negrita se ve como negrita, sin asteriscos"


def test_pegar_desde_word_conserva_negrita_y_vinetas_y_nada_mas():
    assert parrafos_de_html(HTML_WORD) == [
        {"texto": "**Negrita ficticia** y texto con color y cursiva."},
        {"texto": "Viñeta ficticia de Word", "nivel": 0},
        {"texto": "Anidada **ficticia**", "nivel": 1}]


def test_pegar_listas_html_y_texto(editor):
    html = "<ul><li>Uno ficticio</li><li>Dos<ul><li>Dos y medio</li></ul></li></ul><p><strong>Fin</strong></p>"
    assert parrafos_de_html(html) == [{"texto": "Uno ficticio", "nivel": 0}, {"texto": "Dos", "nivel": 0},
                                      {"texto": "Dos y medio", "nivel": 1}, {"texto": "**Fin**"}]
    assert parrafos_de_texto("Texto\n- Viñeta\n  - Anidada\n• Otra\n\n") == [
        {"texto": "Texto"}, {"texto": "Viñeta", "nivel": 0}, {"texto": "Anidada", "nivel": 1},
        {"texto": "Otra", "nivel": 0}]
    datos = QMimeData()
    datos.setHtml(HTML_WORD)
    editor.texto.insertFromMimeData(datos)
    assert editor.parrafos()[1:] == [{"texto": "Viñeta ficticia de Word", "nivel": 0},
                                     {"texto": "Anidada **ficticia**", "nivel": 1}]


def test_teclado_como_en_word(qtbot, editor):
    editor.texto.setFocus()
    qtbot.keyClicks(editor.texto, "Primero")
    qtbot.keyClick(editor.texto, Qt.Key.Key_Return)
    qtbot.keyClicks(editor.texto, "- Vineta tecleada")
    assert editor.parrafos() == [{"texto": "Primero"}, {"texto": "Vineta tecleada", "nivel": 0}]
    qtbot.keyClick(editor.texto, Qt.Key.Key_Return)
    qtbot.keyClick(editor.texto, Qt.Key.Key_Tab)
    qtbot.keyClicks(editor.texto, "Anidada")
    assert editor.parrafos()[-1] == {"texto": "Anidada", "nivel": 1}
    qtbot.keyClick(editor.texto, Qt.Key.Key_Tab, Qt.KeyboardModifier.ShiftModifier)
    assert editor.parrafos()[-1] == {"texto": "Anidada", "nivel": 0}
    qtbot.keyClick(editor.texto, Qt.Key.Key_Return)
    qtbot.keyClick(editor.texto, Qt.Key.Key_Return)   # Intro en una viñeta vacía: fuera de la lista
    qtbot.keyClicks(editor.texto, "Normal")
    assert editor.parrafos()[-1] == {"texto": "Normal"}


def test_negrita_y_vinetas_desde_la_barra(editor):
    editor.poner([{"texto": "Texto ficticio"}])
    editor.texto.setFocus()
    c = editor.texto.textCursor()
    c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
    c.movePosition(QTextCursor.MoveOperation.EndOfWord, QTextCursor.MoveMode.KeepAnchor)
    editor.texto.setTextCursor(c)
    editor.b_negrita.click()
    editor.b_vinetas.click()
    assert editor.parrafos() == [{"texto": "**Texto** ficticio", "nivel": 0}]
    assert editor.b_negrita.isChecked() and editor.b_vinetas.isChecked() and editor.b_mas.isEnabled()
    editor.b_mas.click()
    assert editor.parrafos() == [{"texto": "**Texto** ficticio", "nivel": 1}]


def test_copiar_da_html_limpio_para_word(editor):
    editor.poner(PARRAFOS[:3])
    editor.texto.selectAll()
    datos = editor.texto.createMimeDataFromSelection()
    assert "<b>negrita</b>" in datos.html() and "<ul><li>Viñeta ficticia<ul><li>" in datos.html().replace("</li><ul>", "<ul>")
    assert "font-family" not in datos.html()
    assert datos.text().splitlines()[1] == "• Viñeta ficticia"


def test_escrito_como_antes_y_aviso_de_cambio(qtbot, editor):
    """Los chips y lo escrito con «- » y `**…**` siguen valiendo: se ven como viñeta y negrita."""
    with qtbot.waitSignal(editor.cambiado) as senal:
        editor.setPlainText("Con el **cuaderno ficticio**.\n- Viñeta ficticia")
    assert senal.args[0] == [{"texto": "Con el **cuaderno ficticio**."}, {"texto": "Viñeta ficticia", "nivel": 0}]
