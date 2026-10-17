"""Ventanas modales propias de Programaciones (DESIGN.md, «Ventanas modales»; maqueta v0, pantallas 09, 11 y 20), con
el formato de las de Partes de salida: márgenes 26/22 px, título condensado y botones abajo a la derecha.

- `DialogoCambios`: «Ha cambiado el currículo de este módulo» (el diálogo de novedades con «§», ADR-015).
- `DialogoExportando`: pasos con su marca, barra de progreso y, al terminar, «Exportada en …» con «Mostrar en la
  carpeta». También sirve para preparar la vista previa.
- `DialogoAviso`: círculo con un símbolo, título y texto («Modificado en Word»).
- `DialogoBienvenida`: lo único que la app pregunta al empezar un curso escolar: el nombre y la carpeta (HU-11).
- `DialogoCurriculo`: todo lo oficial del módulo, de solo lectura y con su fuente («Ver» de «DEL CURRÍCULO»).
"""

from __future__ import annotations

import html
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QTextBrowser,
    QVBoxLayout,
)

from ..ajustes import estado_carpeta
from . import estilo
from .componentes import boton, etiqueta
from .dialogos import DialogoNovedades


def _titulo(texto: str, tam: int = 26) -> QLabel:
    t = QLabel(texto)
    t.setFont(estilo.fuente(tam, QFont.Weight.Bold, estilo.TITULAR))
    t.setWordWrap(True)
    return t


def _circulo(simbolo: str, token: str) -> QLabel:
    c = QLabel(simbolo)
    c.setFixedSize(46, 46)
    c.setAlignment(Qt.AlignmentFlag.AlignCenter)
    c.setStyleSheet(f"background:{estilo.T[token]};color:#ffffff;border-radius:23px;font-size:24px;font-weight:700;")
    return c


def mostrar_en_carpeta(ruta: Path) -> None:
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(ruta).parent if Path(ruta).is_file() else ruta)))


# ---------------------------------------------------------------------------------------------------------------------
# Cambios en el currículo
# ---------------------------------------------------------------------------------------------------------------------
def texto_cambios(cambios: list[str], prog: dict) -> str:
    """Markdown de la ventana: qué cambia y qué bloques del profesor usan los RA afectados."""
    lineas = ["### Resultados de aprendizaje", ""]
    lineas += [f"- **{c.split(':', 1)[0].split()[0]}**: {c.split(':', 1)[1].strip()}" if ":" in c else f"- {c}"
               for c in cambios]
    ras = sorted({int(c.split()[0][2:]) for c in cambios if c.startswith("RA")})
    afecta = []
    for r in ras:
        elementos = [e.get("nombre") or e["id"] for e in prog.get("elementos", []) if r in e.get("ra", [])]
        if elementos:
            afecta.append(f"- **Unidades y evaluación**: {', '.join(elementos)} usan el RA{r}.")
        if str(r) in (prog.get("empresa") or {}):
            afecta.append(f"- **Empresa por RA**: el RA{r} va a empresa.")
        if str(r) in (prog.get("ra_competencias") or {}):
            afecta.append(f"- **RA y competencias**: el RA{r} tiene competencias marcadas.")
    if afecta:
        lineas += ["", "### Te afecta en", "", *afecta]
    return "\n".join(lineas)


class DialogoCambios(DialogoNovedades):
    def __init__(self, ctx, cambios: list[str], padre=None):
        ficha = ctx.ficha
        norma = ctx.catalogo.norma(ficha.fuente_ra).cita if ficha.fuente_ra else "el catálogo"
        super().__init__(
            "§", "Ha cambiado el currículo de este módulo",
            f"{ficha.codigo} · {norma}. Tu programación sigue con la versión anterior hasta que aceptes.",
            texto_cambios(cambios, ctx.prog), "Aceptar cambios", "Cambios en el currículo", padre)


# ---------------------------------------------------------------------------------------------------------------------
# Exportando
# ---------------------------------------------------------------------------------------------------------------------
class DialogoExportando(QDialog):
    """Pasos («Rellenando la plantilla» → «Comprobando el documento» → «Convirtiendo a PDF con Word…»), barra y, al
    terminar, los archivos con «Mostrar en la carpeta»."""

    def __init__(self, titulo: str, nombre: str, pasos: list[str], padre=None):
        super().__init__(padre)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.resize(480, 280)
        self.cancelado = False
        self.archivos: list[Path] = []
        self.enlace = ""
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(10)
        self.titulo = _titulo(titulo)
        capa.addWidget(self.titulo)
        self.filas = []
        for texto in pasos:
            fila = QHBoxLayout()
            icono = QLabel()
            icono.setFixedWidth(22)
            icono.setPixmap(estilo.icono_estado("vacio", 15))
            fila.addWidget(icono)
            t = etiqueta(texto)
            fila.addWidget(t, 1)
            capa.addLayout(fila)
            self.filas.append((icono, t))
        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        self.barra.setRange(0, len(pasos))
        capa.addWidget(self.barra)
        self.detalle = etiqueta(nombre, "muted", envolver=True)
        self.detalle.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        capa.addWidget(self.detalle)
        self.error = etiqueta("", "aviso", envolver=True)
        self.error.hide()
        capa.addWidget(self.error)
        capa.addStretch(1)
        botones = QHBoxLayout()
        botones.addStretch(1)
        self.boton_carpeta = boton("Mostrar en la carpeta")
        self.boton_carpeta.clicked.connect(lambda: mostrar_en_carpeta(self.archivos[0]) if self.archivos else None)
        self.boton_carpeta.hide()
        self.boton_teams = boton("Abrir la carpeta de Teams")
        self.boton_teams.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.enlace)))
        self.boton_teams.hide()
        self.boton = boton("Cancelar")
        self.boton.clicked.connect(self._boton)
        for b in (self.boton_carpeta, self.boton_teams, self.boton):
            botones.addWidget(b)
        capa.addLayout(botones)
        self._terminado = False

    def avance(self, paso: int, total: int, texto: str) -> None:
        self.barra.setMaximum(total)
        self.barra.setValue(paso)
        for i, (icono, t) in enumerate(self.filas):
            if i < paso:
                icono.setPixmap(estilo.icono_estado("confirmado", 15))
                t.setStyleSheet("")
            elif i == paso:
                icono.setPixmap(estilo.icono_estado("en_curso", 15))
                t.setText(texto + "…" if i == paso and paso < total else t.text())
                t.setStyleSheet("font-weight:700;")

    def terminar(self, titulo: str, archivos: list[Path], aviso: str = "", enlace: str = "") -> None:
        self._terminado = True
        self.archivos = list(archivos)
        self.enlace = enlace
        self.barra.setValue(self.barra.maximum())
        for icono, t in self.filas:
            icono.setPixmap(estilo.icono_estado("confirmado", 15))
            t.setStyleSheet("")
        self.titulo.setText(titulo)
        if archivos:
            carpeta = Path(archivos[0]).parent
            self.detalle.setText(f"En {carpeta}:\n" + "\n".join(Path(a).name for a in archivos))
        if aviso:
            self.error.setText(aviso)
            self.error.show()
        self.boton_carpeta.setVisible(bool(archivos))
        self.boton_teams.setVisible(bool(enlace))
        self.boton.setText("Cerrar")
        self.boton.setProperty("primario", True)
        self.boton.style().unpolish(self.boton)
        self.boton.style().polish(self.boton)

    def fallar(self, mensaje: str) -> None:
        self._terminado = True
        self.titulo.setText("No se ha podido terminar")
        self.error.setText(mensaje)
        self.error.show()
        self.boton.setText("Cerrar")

    def _boton(self) -> None:
        if self._terminado:
            self.accept()
            return
        self.cancelado = True
        self.boton.setEnabled(False)
        self.boton.setText("Cancelando…")


# ---------------------------------------------------------------------------------------------------------------------
# Avisos
# ---------------------------------------------------------------------------------------------------------------------
class DialogoAviso(QDialog):
    def __init__(self, simbolo: str, token: str, titulo: str, texto: str, aceptar: str = "Entendido",
                 otro: str = "", titulo_ventana: str = "", padre=None):
        super().__init__(padre)
        self.setWindowTitle(titulo_ventana or titulo)
        self.setModal(True)
        self.resize(480, 240)
        self.otro = None
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(14)
        cab = QHBoxLayout()
        cab.setSpacing(14)
        cab.addWidget(_circulo(simbolo, token))
        self.titulo = _titulo(titulo, 24)
        cab.addWidget(self.titulo, 1)
        capa.addLayout(cab)
        self.texto = etiqueta(texto, envolver=True)
        self.texto.setTextFormat(Qt.TextFormat.RichText)
        capa.addWidget(self.texto)
        capa.addStretch(1)
        botones = QHBoxLayout()
        botones.addStretch(1)
        if otro:
            self.otro = boton(otro)
            botones.addWidget(self.otro)
        self.aceptar = boton(aceptar, primario=True)
        self.aceptar.setDefault(True)
        self.aceptar.clicked.connect(self.accept)
        botones.addWidget(self.aceptar)
        capa.addLayout(botones)


class DialogoModificadoWord(DialogoAviso):
    def __init__(self, ruta: Path, padre=None):
        super().__init__("!", "warn", "Modificado en Word",
                         "Este documento se cambió en Word después de exportarlo. Se recuperan los datos de la app; "
                         "<b>los cambios hechos en Word no</b>.", "Entendido", "Ver el archivo",
                         "Abierto con cambios de Word", padre)
        self.otro.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(ruta))))


# ---------------------------------------------------------------------------------------------------------------------
# Primer arranque de cada curso escolar
# ---------------------------------------------------------------------------------------------------------------------
class DialogoBienvenida(QDialog):
    """Nombre del profesor y carpeta de entrega del curso escolar (HU-11). Se puede dejar para más tarde."""

    def __init__(self, ctx, padre=None):
        super().__init__(padre)
        self.ctx = ctx
        self.setWindowTitle("Antes de empezar")
        self.setModal(True)
        self.resize(560, 330)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(10)
        capa.addWidget(_titulo(f"Curso {ctx.curso_escolar}: antes de empezar"))
        capa.addWidget(etiqueta("Solo dos cosas. Puedes cambiarlas cuando quieras en Ajustes.", "muted",
                                envolver=True))
        capa.addWidget(etiqueta("Tu nombre", "etiqueta"))
        self.nombre = QLineEdit(ctx.gestor.valores.nombre_profesor)
        self.nombre.setPlaceholderText("Como saldrá en la portada de tus programaciones")
        capa.addWidget(self.nombre)
        capa.addWidget(etiqueta(f"Carpeta de entrega del curso {ctx.curso_escolar}", "etiqueta"))
        fila = QHBoxLayout()
        self.carpeta = QLineEdit(ctx.gestor.carpeta_entrega(ctx.curso_escolar))
        self.carpeta.setPlaceholderText("La de Teams sincronizada con OneDrive, o su enlace")
        self.carpeta.textChanged.connect(self._pintar)
        fila.addWidget(self.carpeta, 1)
        elegir = boton("Elegir…", pequeno=True)
        elegir.clicked.connect(self._elegir)
        fila.addWidget(elegir)
        ayuda = boton("?", pequeno=True)
        ayuda.setToolTip("Añadir la carpeta de Teams a OneDrive")
        ayuda.clicked.connect(self._ayuda)
        fila.addWidget(ayuda)
        capa.addLayout(fila)
        self.estado = etiqueta("", "pequeno", envolver=True)
        capa.addWidget(self.estado)
        capa.addStretch(1)
        botones = QHBoxLayout()
        botones.addStretch(1)
        luego = boton("Más tarde")
        luego.clicked.connect(self.reject)
        self.guardar = boton("Guardar", primario=True)
        self.guardar.setDefault(True)
        self.guardar.clicked.connect(self._guardar)
        botones.addWidget(luego)
        botones.addWidget(self.guardar)
        capa.addLayout(botones)
        self._pintar()

    @staticmethod
    def hace_falta(ctx) -> bool:
        return not ctx.gestor.valores.nombre_profesor.strip() or not ctx.gestor.carpeta_entrega(ctx.curso_escolar)

    def _pintar(self) -> None:
        textos = {"vacia": "Sin carpeta: al exportar, la app preguntará dónde guardar.",
                  "local": "Carpeta encontrada en este equipo.",
                  "enlace": "Enlace de Teams: se exporta en este equipo y se abre la carpeta para subirlos.",
                  "no_encontrada": "No se encuentra esta carpeta en este equipo."}
        self.estado.setText(textos[estado_carpeta(self.carpeta.text())])

    def _elegir(self) -> None:
        ruta = QFileDialog.getExistingDirectory(self, "Carpeta de entrega", self.carpeta.text() or str(Path.home()))
        if ruta:
            self.carpeta.setText(ruta)

    def _ayuda(self) -> None:
        from .ayuda import AYUDA_TEAMS, DialogoAyuda

        DialogoAyuda(AYUDA_TEAMS, self).exec()

    def _guardar(self) -> None:
        self.ctx.gestor.poner(nombre_profesor=self.nombre.text().strip())
        self.ctx.gestor.poner_carpeta_entrega(self.ctx.curso_escolar, self.carpeta.text())
        self.ctx.ajustes_cambiados.emit()
        self.accept()


# ---------------------------------------------------------------------------------------------------------------------
# Del currículo
# ---------------------------------------------------------------------------------------------------------------------
def html_curriculo(ctx) -> str:
    ficha = ctx.ficha
    cat = ctx.catalogo
    e = html.escape
    partes = [f"<h2>{e(ficha.codigo)} · {e(ficha.nombre)}</h2>",
              f"<p>{e(ficha.ciclo_nombre)} ({ficha.sigla}) · {ficha.curso}.º curso · {ficha.horas} h · "
              f"{ficha.h_sem} h/semana</p>"]
    if ficha.fuente_ra:
        n = cat.norma(ficha.fuente_ra)
        comprobado = cat.modulo(ficha.modulo_id)["fuente"].get("comprobado", "")
        partes.append(f"<p><i>Fuente: <a href='{e(n.enlace)}'>{e(n.cita)}</a> ({n.diario}) · comprobado el "
                      f"{comprobado}</i></p>")
    if ficha.pendientes:
        partes.append("<p><b>Pendiente:</b> " + e("; ".join(ficha.pendientes)) + "</p>")
    partes.append("<h3>Resultados de aprendizaje y criterios de evaluación</h3>")
    for ra in ficha.ra:
        partes.append(f"<p><b>RA{ra['n']}.</b> {e(ra['texto'])}</p><ul>"
                      + "".join(f"<li>{c['letra']}) {e(c['texto'])}</li>" for c in ra["criterios"]) + "</ul>")
    competencias = {c["letra"]: c["texto"]["es"] for c in cat.ciclo(ficha.sigla)["competencias"]}
    if ficha.competencias_modulo:
        partes.append("<h3>Competencias del título a las que contribuye</h3><ul>"
                      + "".join(f"<li>{x}) {e(competencias.get(x, ''))}</li>" for x in ficha.competencias_modulo)
                      + "</ul>")
    partes.append("<h3>Normativa</h3><ul>")
    for ambito in ("estatal", "autonomico"):
        for n in cat.normativa(ficha.sigla, ambito, ctx.curso_escolar):
            partes.append(f"<li><a href='{e(n.enlace)}'>{e(n.titulo)}</a></li>")
    partes.append("</ul>")
    return "".join(partes)


class DialogoCurriculo(QDialog):
    def __init__(self, ctx, padre=None):
        super().__init__(padre)
        self.setWindowTitle("Del currículo")
        self.resize(760, 620)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(10)
        capa.addWidget(_titulo("Del currículo", 24))
        capa.addWidget(etiqueta("Datos oficiales del módulo, de solo lectura: salen así en el documento.", "muted"))
        self.texto = QTextBrowser()
        self.texto.setOpenExternalLinks(True)
        self.texto.setHtml(html_curriculo(ctx))
        capa.addWidget(self.texto, 1)
        botones = QHBoxLayout()
        botones.addStretch(1)
        cerrar = boton("Cerrar", primario=True)
        cerrar.clicked.connect(self.accept)
        botones.addWidget(cerrar)
        capa.addLayout(botones)
