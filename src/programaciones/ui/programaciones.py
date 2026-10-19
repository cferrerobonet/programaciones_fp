"""Ventanas «Programaciones» (listado y gestión) y «Nueva a partir de…» (maqueta v0, pantallas 08, 13 y 14).

- El listado usa `TablaPaginada` (patrón de Web Pedidos) con una casilla por fila y la fila de la programación abierta
  resaltada. Con las marcadas: **Abrir** (solo una), **Vista previa**, **Exportar a carpeta…**, **Enviar por correo…**
  (ADR-014) y **Borrar…** (ADR-024), con botones abajo o con clic derecho; se activan según cuántas haya marcadas. El
  trabajo lo hace `gestion.Gestion`.
- «Nueva a partir de…» lee el `.docx` o el `.programacion` del curso pasado (`herencia.leer_origen`), enseña en cifras
  lo que se hereda y los RA que ya no están, y crea la programación del curso escolar actual con los bloques heredados.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QMenu, QMessageBox, QVBoxLayout

from .. import herencia, importar_docx, incrustar, programacion
from . import estilo
from .componentes import ZonaSoltar, boton, etiqueta
from .listado import Columna, TablaPaginada

EXTENSIONES = herencia.EXTENSIONES
#: Acción → (texto, cuántas marcadas hacen falta: «1» solo una, «n» una o más).
ACCIONES = {
    "abrir": ("Abrir", "1"),
    "vista_previa": ("Vista previa", "n"),
    "exportar": ("Exportar a carpeta…", "n"),
    "correo": ("Enviar por correo…", "n"),
    "borrar": ("Borrar…", "n"),
}


def _titulo(texto: str) -> QLabel:
    t = QLabel(texto)
    t.setFont(estilo.fuente(24, QFont.Weight.Bold, estilo.TITULAR))
    return t


def modulo_elegido(ctx) -> importar_docx.Modulo | None:
    """El módulo elegido en la columna «Módulos», o None."""
    m = getattr(ctx, "modulo", None)
    return (m.sigla, m.curso, m.codigo) if m else None


def texto_modulo(cat, modulo) -> str:
    """«0961 Sistemas de medida y regulación (ARI 1.º)»; solo el código si no se sabe de qué ciclo es."""
    sigla, curso, codigo = modulo
    if sigla is None:
        return f"el módulo {codigo}"
    try:
        nombre = cat.nombre_modulo(sigla, codigo)
    except KeyError:
        nombre = ""
    return f"{codigo} {nombre} ({sigla} {curso}.º)".replace("  ", " ")


def preguntar_modulo(padre, texto: str, opciones: dict[str, str]) -> str | None:
    """Pregunta en qué módulo se importa. `opciones`: clave → texto del botón. Devuelve la clave o None (Cancelar)."""
    caja = QMessageBox(padre)
    caja.setWindowTitle("¿De qué módulo es?")
    caja.setIcon(QMessageBox.Icon.Question)
    caja.setText(texto)
    botones = {caja.addButton(t, QMessageBox.ButtonRole.AcceptRole): clave for clave, t in opciones.items()}
    caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
    caja.exec()
    return botones.get(caja.clickedButton())


def leer_origen(padre, ctx, ruta: str | Path) -> herencia.Origen | None:
    """`herencia.leer_origen` con el módulo elegido en la columna «Módulos»: así un Word sin datos de la app no tiene
    que llamarse «SIGLA N - 0xxx - Nombre». Si el documento dice otro módulo, pregunta cuál se usa (None: cancelado).
    Los demás errores llegan a quien llama."""
    try:
        return herencia.leer_origen(ruta, ctx.catalogo, modulo_elegido(ctx))
    except importar_docx.ModuloDistinto as e:
        documento, elegido = e.documento, e.elegido
        opciones = {}
        if documento[0] is not None:
            opciones["documento"] = f"El del documento ({documento[2]})"
        opciones["elegido"] = f"El elegido ({elegido[2]})"
        texto = (f"«{Path(ruta).name}» parece de {texto_modulo(ctx.catalogo, documento)} y en la columna «Módulos» "
                 f"tienes elegido {texto_modulo(ctx.catalogo, elegido)}. ¿En cuál la importas?")
        if documento[0] is None:
            texto += " (Si es del otro, elige antes ese módulo en la columna «Módulos».)"
        respuesta = preguntar_modulo(padre, texto, opciones)
        if respuesta == "documento":
            return herencia.leer_origen(ruta, ctx.catalogo, documento)
        if respuesta == "elegido":
            return herencia.leer_origen(ruta, ctx.catalogo, elegido, comprobar=False)
        return None


class DialogoProgramaciones(QDialog):
    """Programaciones de este equipo (940 × 600): casilla por fila y las acciones sobre las marcadas."""

    COLUMNAS = [
        Columna("Programación", lambda p: p.get("programacion", "")),
        Columna("Curso", lambda p: p.get("curso_escolar", ""), ancho=110),
        Columna("Estado", lambda p: p.get("estado", ""), ancho=170),
        Columna("Exportada", lambda p: p.get("exportada", ""), orden=lambda p: p.get("exportada_iso", ""),
                ancho=150),
    ]

    def __init__(self, ctx, padre=None):
        super().__init__(padre)
        from .gestion import Gestion

        self.ctx = ctx
        self.gestion = getattr(padre, "gestion", None) or Gestion(ctx, self)
        self.elegida: dict | None = None
        self.ultimo_menu: QMenu | None = None
        self.setWindowTitle("Programaciones")
        self.resize(940, 600)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(12)
        capa.addWidget(_titulo("Programaciones"))
        capa.addWidget(etiqueta("Las que has abierto o exportado en este equipo. Marca una o varias para verlas, "
                                "exportarlas, enviarlas por correo o borrarlas (también con clic derecho).", "muted",
                                envolver=True))
        self.tabla = TablaPaginada(self.COLUMNAS, "", lambda p: p.get("id", ""), (3, True),
                                   "Buscar módulo o ciclo", casillas=True)
        actual = None
        if ctx.prog is not None:
            actual = f"{ctx.prog['curso_escolar']}/{ctx.prog['ciclo']}-{ctx.prog['curso']}-{ctx.prog['modulo']}"
        elif ctx.programaciones:
            actual = ctx.recientes(1)[0]["id"]
        self.tabla.poner(ctx.programaciones, resaltar=actual)
        self.tabla.activada.connect(lambda f: self._abrir(f) if f else None)
        self.tabla.marcadas_cambiadas.connect(self._marcadas)
        self.tabla.menu_pedido.connect(self._menu)
        capa.addWidget(self.tabla, 1)
        marcar = QHBoxLayout()
        exportadas = boton("Marcar las exportadas", pequeno=True)
        exportadas.clicked.connect(lambda: self.tabla.marcar(
            [f["id"] for f in ctx.programaciones if f["estado_clave"] == "exportada"]))
        ninguna = boton("Ninguna", pequeno=True)
        ninguna.clicked.connect(lambda: self.tabla.marcar([]))
        marcar.addWidget(exportadas)
        marcar.addWidget(ninguna)
        marcar.addStretch(1)
        self.cuantas = etiqueta("", "pequeno")
        marcar.addWidget(self.cuantas)
        capa.addLayout(marcar)
        botones = QHBoxLayout()
        self.botones = {}
        for clave, (texto, _n) in ACCIONES.items():
            b = boton(texto, peligro=True) if clave == "borrar" else boton(texto, primario=clave == "abrir")
            b.clicked.connect(lambda _=False, c=clave: self.hacer(c))
            botones.addWidget(b)
            self.botones[clave] = b
        botones.addStretch(1)
        cerrar = boton("Cerrar")
        cerrar.clicked.connect(self.reject)
        botones.addWidget(cerrar)
        capa.addLayout(botones)
        # Compatibilidad con la 0.1: «Abrir» y «Enviar…» se llamaban así en las pruebas y en la maqueta.
        self.abrir, self.enviar = self.botones["abrir"], self.botones["correo"]
        ctx.programaciones_cambiadas.connect(self._recargar)
        self._marcadas(0)

    # Acciones
    def marcadas(self) -> list[dict]:
        return [f["prog"] for f in self.tabla.marcadas()]

    def activa(self, accion: str, n: int | None = None) -> bool:
        n = len(self.tabla.marcadas()) if n is None else n
        return n == 1 if ACCIONES[accion][1] == "1" else n >= 1

    def _marcadas(self, n: int) -> None:
        for clave, b in self.botones.items():
            b.setEnabled(self.activa(clave, n))
        self.botones["correo"].setText(f"Enviar {n} por correo…" if n > 1 else "Enviar por correo…")
        self.botones["exportar"].setText(f"Exportar {n} a carpeta…" if n > 1 else "Exportar a carpeta…")
        self.botones["borrar"].setText(f"Borrar {n}…" if n > 1 else "Borrar…")
        self.botones["abrir"].setToolTip("Abre la marcada" if n == 1 else "Marca solo una para abrirla")
        self.cuantas.setText("Ninguna marcada" if not n else f"{n} marcada{'s' if n > 1 else ''}")

    def hacer(self, accion: str) -> None:
        progs = self.marcadas()
        if not self.activa(accion):
            return
        if accion == "abrir":
            self._abrir(self.tabla.marcadas()[0])
        elif accion == "vista_previa":
            self.gestion.vista_previa(progs, self)
        elif accion == "exportar":
            self.gestion.exportar_a_carpeta(progs, self)
        elif accion == "correo":
            self.gestion.enviar(progs, self)
        elif accion == "borrar":
            self.gestion.borrar(progs, self)

    def menu_contextual(self, fila: dict | None) -> QMenu:
        """El de clic derecho: si la fila no estaba marcada, se marca solo ella (como en el Finder)."""
        if fila is not None and fila not in self.tabla.marcadas():
            self.tabla.marcar([self.tabla.id_de(fila)])
        menu = QMenu(self)
        for clave, (texto, _n) in ACCIONES.items():
            if clave == "borrar":
                menu.addSeparator()
            a = menu.addAction(texto)
            a.setEnabled(self.activa(clave))
            a.triggered.connect(lambda _=False, c=clave: self.hacer(c))
        self.ultimo_menu = menu
        return menu

    def _menu(self, fila, punto) -> None:
        self.menu_contextual(fila).popup(punto)

    def _recargar(self) -> None:
        marcadas = [self.tabla.id_de(f) for f in self.tabla.marcadas()]
        self.tabla.poner(self.ctx.programaciones)
        self.tabla.marcar(marcadas)

    def _abrir(self, fila: dict) -> None:
        self.elegida = fila["prog"]
        self.accept()


class DialogoHeredar(QDialog):
    """«Nueva a partir de…»: se suelta el .docx o el .programacion del curso pasado y se ve qué se hereda."""

    def __init__(self, ctx, padre=None):
        super().__init__(padre)
        self.ctx = ctx
        self.archivo: Path | None = None
        self.herencia: herencia.Herencia | None = None
        self.setWindowTitle("Nueva a partir de…")
        self.resize(640, 520)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(12)
        capa.addWidget(_titulo("Nueva a partir de…"))
        capa.addWidget(etiqueta(
            "Elige la programación del curso pasado (la tuya o la de otro profesor). Se heredan tus bloques; lo oficial "
            "y las fechas se ponen al día solos.", "muted", envolver=True))
        self.zona = ZonaSoltar("Arrastra aquí el .docx o el .programacion",
                               "De la carpeta de Teams del curso anterior o de tu OneDrive",
                               "Elegir archivo…", EXTENSIONES, "↥")
        self.zona.boton.clicked.connect(self._elegir)
        self.zona.archivos.connect(lambda rutas: self.poner_archivo(rutas[0]))
        capa.addWidget(self.zona)
        self.tarjeta = QFrame()
        self.tarjeta.setProperty("rol", "caja")
        tv = QVBoxLayout(self.tarjeta)
        tv.setContentsMargins(16, 12, 16, 14)
        tv.setSpacing(8)
        cab = QHBoxLayout()
        icono = QLabel()
        icono.setPixmap(estilo.icono_documento(estilo.T["accent"], 20))
        cab.addWidget(icono, 0, Qt.AlignmentFlag.AlignTop)
        nombres = QVBoxLayout()
        self.nombre = etiqueta("", envolver=True)
        self.nombre.setStyleSheet("font-weight:700;")
        nombres.addWidget(self.nombre)
        self.origen = etiqueta("", "muted", envolver=True)
        nombres.addWidget(self.origen)
        cab.addLayout(nombres, 1)
        tv.addLayout(cab)
        cifras = QHBoxLayout()
        self.cifras = {}
        for clave, texto in (("unidades", "unidades"), ("elementos", "elementos"), ("ra_empresa", "RA a empresa"),
                             ("heredados", "bloques heredados")):
            caja = QFrame()
            caja.setProperty("rol", "dato")
            cv = QVBoxLayout(caja)
            cv.setContentsMargins(10, 6, 10, 6)
            valor = QLabel("0")
            valor.setFont(estilo.fuente(30, QFont.Weight.Bold, estilo.TITULAR))
            cv.addWidget(valor)
            cv.addWidget(etiqueta(texto, "pequeno"))
            cifras.addWidget(caja)
            self.cifras[clave] = valor
        tv.addLayout(cifras)
        self.tarjeta.hide()
        capa.addWidget(self.tarjeta)
        self.resumen = etiqueta("", "aviso", envolver=True)
        self.resumen.hide()
        capa.addWidget(self.resumen)
        capa.addStretch(1)
        botones = QHBoxLayout()
        botones.addStretch(1)
        cancelar = boton("Cancelar")
        cancelar.clicked.connect(self.reject)
        self.heredar = boton("Heredar", primario=True)
        self.heredar.setEnabled(False)
        self.heredar.clicked.connect(self._heredar)
        botones.addWidget(cancelar)
        botones.addWidget(self.heredar)
        capa.addLayout(botones)

    def _elegir(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Programación del curso pasado", str(Path.home()),
                                              "Programaciones (*.docx *.programacion)")
        if ruta:
            self.poner_archivo(ruta)

    def poner_archivo(self, ruta: str | Path, origen: herencia.Origen | None = None) -> None:
        """`origen`: ya leído (desde «Abrir», que ha preguntado el módulo si hacía falta)."""
        self.archivo = Path(ruta)
        self.herencia = None
        self.heredar.setEnabled(False)
        self.tarjeta.hide()
        self.resumen.hide()
        try:
            if origen is None:
                origen = leer_origen(self, self.ctx, self.archivo)
            if origen is None:
                return
            self.herencia = herencia.heredar(origen.programacion, self.ctx.catalogo, self.ctx.curso_escolar,
                                             self.archivo.name)
        except (OSError, KeyError, ValueError, importar_docx.NoEsProgramacion, incrustar.DatosDanados,
                programacion.ProgramacionNoValida) as e:
            self.resumen.setText(f"No se puede heredar de «{self.archivo.name}»: {e}")
            self.resumen.show()
            return
        p = origen.programacion
        self.nombre.setText(self.archivo.name)
        profesor = next((x for x in p.get("profesorado", []) if x.strip()), "")
        partes = [x for x in (profesor, f"curso {p['curso_escolar']}",
                              "exportada por la app" if origen.exportada_por_la_app else "leída de un Word") if x]
        self.origen.setText(" · ".join(partes))
        for clave, valor in self.herencia.resumen.items():
            self.cifras[clave].setText(str(valor))
        self.tarjeta.show()
        avisos = list(self.herencia.avisos)
        if origen.modificado_en_word:
            avisos.insert(0, "Se cambió en Word después de exportarlo: se heredan los datos de la app, no esos cambios")
        nuevo = self.herencia.programacion
        if p["curso_escolar"] != nuevo["curso_escolar"]:
            fechas = "pendientes" if self.ctx.datos_curso is None else "las del curso nuevo"
            avisos.append(f"Las fechas del curso y la resolución de instrucciones salen del curso "
                          f"{nuevo['curso_escolar']} ({fechas})")
        m = self.ctx.modulo
        if m is not None and (m.sigla, m.curso, m.codigo) != (nuevo["ciclo"], nuevo["curso"], nuevo["modulo"]):
            avisos.append(f"Es de otro módulo ({nuevo['ciclo']} {nuevo['curso']} - {nuevo['modulo']}): se abrirá ese")
        avisos.append("Tendrás que revisar y confirmar cada bloque heredado.")
        self.resumen.setText(". ".join(a.rstrip(".") for a in avisos) + ".")
        self.resumen.show()
        self.heredar.setEnabled(True)

    def _heredar(self) -> None:
        nuevo = self.herencia.programacion
        existente = self.ctx.almacen.cargar(nuevo["curso_escolar"], nuevo["ciclo"], nuevo["curso"], nuevo["modulo"])
        if existente is not None:
            r = QMessageBox.question(
                self, "Nueva a partir de…",
                f"Ya tienes una programación de este módulo para {nuevo['curso_escolar']}. ¿La sustituyes por la "
                "heredada? (La anterior queda entre las copias de seguridad de este equipo.)")
            if r != QMessageBox.StandardButton.Yes:
                return
        self.accept()
