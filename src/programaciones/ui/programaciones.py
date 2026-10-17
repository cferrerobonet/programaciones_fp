"""Ventanas «Programaciones» (listado y envío) y «Nueva a partir de…» (maqueta v0, pantallas 08, 13 y 14).

- El listado usa `TablaPaginada` (patrón de Web Pedidos) con una casilla por fila, la fila de la programación abierta
  resaltada, «Abrir», «Marcar las exportadas» y «Ninguna». **Enviar por correo** espera a ADR-014 (sin datos de
  CarlosFB): el botón sale desactivado y dice «pendiente».
- «Nueva a partir de…» lee el `.docx` o el `.programacion` del curso pasado (`herencia.leer_origen`), enseña en cifras
  lo que se hereda y los RA que ya no están, y crea la programación del curso escolar actual con los bloques heredados.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QVBoxLayout

from .. import herencia, importar_docx, incrustar, programacion
from . import estilo
from .componentes import ZonaSoltar, boton, etiqueta
from .listado import Columna, TablaPaginada

EXTENSIONES = herencia.EXTENSIONES


def _titulo(texto: str) -> QLabel:
    t = QLabel(texto)
    t.setFont(estilo.fuente(24, QFont.Weight.Bold, estilo.TITULAR))
    return t


class DialogoProgramaciones(QDialog):
    """Programaciones de este equipo (940 × 600): casilla por fila, «Abrir» y «Enviar N por correo…»."""

    COLUMNAS = [
        Columna("Programación", lambda p: p.get("programacion", "")),
        Columna("Curso", lambda p: p.get("curso_escolar", ""), ancho=110),
        Columna("Estado", lambda p: p.get("estado", ""), ancho=170),
        Columna("Exportada", lambda p: p.get("exportada", ""), orden=lambda p: p.get("exportada_iso", ""),
                ancho=150),
    ]

    def __init__(self, ctx, padre=None):
        super().__init__(padre)
        self.ctx = ctx
        self.elegida: dict | None = None
        self.setWindowTitle("Programaciones")
        self.resize(940, 600)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(12)
        capa.addWidget(_titulo("Programaciones"))
        capa.addWidget(etiqueta("Las que has abierto o exportado en este equipo. Marca una o varias para enviarlas por "
                                "correo.", "muted", envolver=True))
        self.tabla = TablaPaginada(self.COLUMNAS, "", lambda p: p.get("id", ""), (3, True),
                                   "Buscar módulo o ciclo", casillas=True)
        actual = None
        if ctx.prog is not None:
            actual = f"{ctx.prog['curso_escolar']}/{ctx.prog['ciclo']}-{ctx.prog['curso']}-{ctx.prog['modulo']}"
        elif ctx.programaciones:
            actual = ctx.recientes(1)[0]["id"]
        self.tabla.poner(ctx.programaciones, resaltar=actual)
        self.tabla.elegida.connect(lambda f: self.abrir.setEnabled(f is not None))
        self.tabla.activada.connect(lambda f: self._abrir() if f else None)
        self.tabla.marcadas_cambiadas.connect(self._marcadas)
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
        capa.addLayout(marcar)
        self.enviar = boton("", primario=True, grande=True)
        self.enviar.setEnabled(False)
        self.enviar.setToolTip("Pendiente de decidir cómo se envía el correo (ADR-014)")
        capa.addWidget(self.enviar)
        botones = QHBoxLayout()
        self.aviso_correo = etiqueta("Envío por correo: pendiente de decidir cómo se envía (ADR-014).", "pequeno")
        botones.addWidget(self.aviso_correo)
        botones.addStretch(1)
        self.abrir = boton("Abrir")
        self.abrir.setEnabled(False)
        self.abrir.clicked.connect(self._abrir)
        cerrar = boton("Cerrar")
        cerrar.clicked.connect(self.reject)
        botones.addWidget(self.abrir)
        botones.addWidget(cerrar)
        capa.addLayout(botones)
        self._marcadas(0)

    def _marcadas(self, n: int) -> None:
        self.enviar.setText(f"Enviar {n} por correo… (pendiente)" if n else "Enviar por correo… (pendiente)")

    def _abrir(self) -> None:
        fila = self.tabla.seleccionada()
        if fila is None:
            return
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

    def poner_archivo(self, ruta: str | Path) -> None:
        self.archivo = Path(ruta)
        self.herencia = None
        self.heredar.setEnabled(False)
        self.tarjeta.hide()
        try:
            origen = herencia.leer_origen(self.archivo, self.ctx.catalogo)
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
