"""Lo que se hace con una o varias programaciones, desde la ventana principal o desde «Programaciones»: vista previa,
exportar a una carpeta, enviar por correo (ADR-014) y borrar (ADR-024).

El trabajo largo va en una `Tarea` (RNF-03) con la ventana «Exportando», que se puede cancelar. Nada se sustituye sin
preguntar (DESIGN.md, «Don'ts») y borrar nunca toca lo exportado: el archivo de trabajo va a la papelera del sistema.
"""

from __future__ import annotations

import copy
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QFile, QObject, QStandardPaths
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from .. import almacen, correo, exportacion, validacion
from ..rutas import carpeta_datos
from . import estilo
from .componentes import FlujoLayout, Tarea, boton, desplazable, etiqueta

NOMBRE_FORMATO = {"docx": "Word", "pdf": "PDF"}


class Cancelada(Exception):
    """El profesor ha pulsado «Cancelar» en la ventana «Exportando»."""


def papelera(ruta: Path) -> bool:
    """Mueve un archivo o una carpeta a la papelera del sistema (las pruebas la sustituyen)."""
    ok, _destino = QFile.moveToTrash(str(ruta))
    return bool(ok)


def documentos() -> Path:
    ruta = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    return Path(ruta or Path.home())


def _titulo(texto: str) -> QLabel:
    t = QLabel(texto)
    t.setFont(estilo.fuente(24, QFont.Weight.Bold, estilo.TITULAR))
    t.setWordWrap(True)
    return t


def chips_formato(formatos: list[str], al_cambiar) -> tuple[QWidget, dict]:
    """Chips «Word» y «PDF» (al menos uno marcado), como los de «Exportar»."""
    zona = QWidget()
    capa = FlujoLayout(zona, 6)
    chips = {}

    def tocado(f: str) -> None:
        if not any(b.isChecked() for b in chips.values()):
            chips[f].setChecked(True)
            return
        al_cambiar()

    for f, texto in NOMBRE_FORMATO.items():
        b = boton(texto, chip=True)
        b.setCheckable(True)
        b.setChecked(f in formatos)
        b.setAccessibleName(f"Adjuntar o exportar en {texto}")
        b.clicked.connect(lambda _=False, f=f: tocado(f))
        capa.addWidget(b)
        chips[f] = b
    return zona, chips


@dataclass
class Adjunto:
    prog: dict
    formato: str
    ruta: Path
    estado: str   # «listo», «cambiada» (exportado antes de los últimos cambios), «exportar» o «bloqueada»

    @property
    def se_adjunta(self) -> bool:
        return self.estado != "bloqueada"


class Gestion(QObject):
    def __init__(self, ctx, ventana: QWidget | None = None):
        super().__init__(ventana)
        self.ctx = ctx
        self.ventana = ventana
        self.tareas: list[Tarea] = []
        self.temporales: list[Path] = []
        self.ultimo_dialogo = None
        self.ultimo_visor = None

    # -- Utilidades --------------------------------------------------------------------------------------------------
    def lanzar(self, trabajo, dialogo, al_terminar) -> Tarea:
        def con_cancelar(avance):
            def paso(i, n, texto):
                if dialogo.cancelado:
                    raise Cancelada()
                avance(i, n, texto)
            return trabajo(paso)

        tarea = Tarea(con_cancelar)
        tarea.progreso.connect(dialogo.avance)
        tarea.terminado.connect(al_terminar)
        tarea.fallo.connect(lambda m: dialogo.reject() if dialogo.cancelado else dialogo.fallar(m))
        tarea.finished.connect(lambda: self.tareas.remove(tarea) if tarea in self.tareas else None)
        self.tareas.append(tarea)
        tarea.start()
        return tarea

    def esperar(self, ms: int = 5000) -> None:
        for t in list(self.tareas):
            t.wait(ms)

    def limpiar(self) -> None:
        for carpeta in self.temporales:
            shutil.rmtree(carpeta, ignore_errors=True)

    def nombre(self, prog: dict) -> str:
        """Nombre normalizado del archivo, sin extensión («SEA 2 - 0517 - Procesos…»)."""
        return exportacion.destinos(prog, self.ctx.catalogo, Path("."), ["docx"])[0].stem

    def bloquea(self, prog: dict) -> bool:
        return validacion.bloquean(self.ctx.avisos_de(prog))

    def carpeta_habitual(self, prog: dict) -> Path:
        curso = prog["curso_escolar"]
        return exportacion.carpeta_habitual(self.ctx.gestor.carpeta_entrega(curso), curso, documentos())

    def _motor(self) -> str:
        return self.ctx.gestor.valores.programa_pdf

    # -- Vista previa ------------------------------------------------------------------------------------------------
    def vista_previa(self, progs: list[dict], padre=None, al_terminar=None) -> None:
        """PDF con la marca «BORRADOR» de cada una; con varias, el visor deja elegir cuál se ve."""
        from .modales import DialogoExportando
        from .vista_previa import DialogoVistaPrevia

        progs = [copy.deepcopy(self.ctx.al_dia(p)) for p in progs]
        if not progs:
            return
        carpeta = Path(tempfile.mkdtemp(prefix="programaciones-vista-"))
        self.temporales.append(carpeta)
        motor = self._motor()
        nombres = [self.nombre(p) for p in progs]
        if len(progs) == 1:
            pasos = ["Rellenando la plantilla", f"Convirtiendo a PDF con {exportacion.texto_motor(motor)}"]
            detalle = nombres[0]
        else:
            pasos = nombres
            detalle = f"{len(progs)} programaciones, convertidas a PDF con {exportacion.texto_motor(motor)}"
        dialogo = DialogoExportando("Preparando la vista previa", detalle, pasos, padre)
        self.ultimo_dialogo = dialogo
        cat, opciones = self.ctx.catalogo, self.ctx.opciones_documento()
        cursos = [self.ctx.datos_curso_de(p) for p in progs]

        def trabajo(avance):
            if len(progs) == 1:
                return [(nombres[0], exportacion.vista_previa(progs[0], cat, cursos[0], opciones, carpeta, motor,
                                                              avance))]
            rutas = []
            for i, p in enumerate(progs):
                avance(i, len(progs), nombres[i])
                destino = carpeta / str(i)
                rutas.append((nombres[i], exportacion.vista_previa(p, cat, cursos[i], opciones, destino, motor)))
            avance(len(progs), len(progs), "Hecho")
            return rutas

        def listo(rutas):
            dialogo.accept()
            if al_terminar:
                al_terminar(rutas)
            visor = DialogoVistaPrevia(padre)
            self.ultimo_visor = visor
            visor.abrir_varias(rutas)
            visor.exec()

        self.lanzar(trabajo, dialogo, listo)
        dialogo.exec()

    # -- Exportar a una carpeta --------------------------------------------------------------------------------------
    def exportar_a_carpeta(self, progs: list[dict], padre=None) -> None:
        from .modales import DialogoExportando

        progs = [self.ctx.al_dia(p) for p in progs]
        if not progs:
            return
        eleccion = DialogoExportarCarpeta(self, progs, padre)
        self.ultimo_dialogo = eleccion
        if eleccion.exec() != QDialog.DialogCode.Accepted:
            return
        carpeta, formatos = eleccion.carpeta, eleccion.formatos()
        plan = []   # (programación, formatos que se escriben)
        existentes = []
        for p in eleccion.exportables():
            destinos = exportacion.destinos(p, self.ctx.catalogo, carpeta, formatos)
            existentes += [d for d in destinos if d.exists()]
            plan.append((p, formatos))
        saltadas = []
        if existentes:
            r = QMessageBox.question(
                padre, "Exportar a una carpeta",
                "Ya existe en la carpeta:\n" + "\n".join(d.name for d in existentes) + "\n\n¿Lo sustituyes? «Sí»: se "
                "sustituye. «No»: se exportan solo los que faltan.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel)
            if r == QMessageBox.StandardButton.Cancel:
                return
            if r == QMessageBox.StandardButton.No:
                nuevo = []
                for p, fmts in plan:
                    quedan = [f for f, d in zip(fmts, exportacion.destinos(p, self.ctx.catalogo, carpeta, fmts),
                                                strict=True) if not d.exists()]
                    if quedan:
                        nuevo.append((p, quedan))
                    else:
                        saltadas.append(self.nombre(p))
                plan = nuevo
        avisos = [f"No se exporta {self.nombre(p)}: tiene avisos en rojo (ábrela para corregirlos)."
                  for p in eleccion.bloqueadas()]
        avisos += [f"Ya estaba y no se sustituye: {n}." for n in saltadas]
        if not plan:
            QMessageBox.information(padre, "Exportar a una carpeta", "\n".join(avisos) or "Nada que exportar.")
            return
        datos = [(copy.deepcopy(p), fmts, self.ctx.datos_curso_de(p)) for p, fmts in plan]
        cat, opciones, motor = self.ctx.catalogo, self.ctx.opciones_documento(), self._motor()
        dialogo = DialogoExportando("Exportando", f"{len(plan)} programaciones en {carpeta}" if len(plan) > 1
                                    else self.nombre(plan[0][0]), [self.nombre(p) for p, _f in plan], padre)
        self.ultimo_dialogo = dialogo

        def trabajo(avance):
            hechos = []
            for i, (p, fmts, curso) in enumerate(datos):
                avance(i, len(datos), self.nombre(p))
                hechos.append(exportacion.exportar(p, cat, curso, carpeta, fmts, opciones, motor))
            avance(len(datos), len(datos), "Hecho")
            return hechos

        def listo(hechos):
            archivos = []
            for (p, _f), res in zip(plan, hechos, strict=True):
                self.ctx.exportada(res.archivos, p)
                archivos += res.archivos
                if res.error_pdf:
                    avisos.append(f"El PDF de {self.nombre(p)} no se ha podido hacer ({res.error_pdf}).")
            dialogo.terminar("Exportadas" if len(plan) > 1 else "Exportada", archivos, "\n".join(avisos))

        self.lanzar(trabajo, dialogo, listo)
        dialogo.exec()

    # -- Correo ------------------------------------------------------------------------------------------------------
    def adjuntos(self, progs: list[dict], formatos: list[str], reexportar: bool = False) -> list[Adjunto]:
        """Lo que se adjunta de cada programación: el archivo exportado en su carpeta habitual o, si falta, el que se
        exportará antes con el nombre normalizado. Las que tienen avisos en rojo no se pueden exportar."""
        out = []
        for p in progs:
            p = self.ctx.al_dia(p)
            carpeta = self.carpeta_habitual(p)
            bloquea = None
            al_dia = almacen.estado(p) == "exportada"
            for f, ruta in zip([x for x in ("docx", "pdf") if x in formatos],
                               exportacion.destinos(p, self.ctx.catalogo, carpeta, formatos), strict=True):
                if ruta.is_file() and (al_dia or not reexportar):
                    estado = "listo" if al_dia else "cambiada"
                else:
                    bloquea = self.bloquea(p) if bloquea is None else bloquea
                    estado = "bloqueada" if bloquea else "exportar"
                out.append(Adjunto(p, f, ruta, estado))
        return out

    def borrador(self, progs: list[dict], adjuntos: list[Adjunto]) -> tuple[str, str]:
        """Asunto y cuerpo con las plantillas de Ajustes; solo cuentan las que llevan algún adjunto."""
        v = self.ctx.gestor.valores
        con_adjunto = {almacen.identificador(a.prog) for a in adjuntos if a.se_adjunta}
        progs = [p for p in progs if almacen.identificador(p) in con_adjunto] or progs
        c = correo.campos([self.ctx.nombre_modulo(p) for p in progs], [p["curso_escolar"] for p in progs],
                          [a.ruta for a in adjuntos if a.se_adjunta], v.nombre_profesor)
        return correo.asunto_y_cuerpo(c, v.asunto_una, v.asunto_varias, v.cuerpo_correo)

    def enviar(self, progs: list[dict], padre=None) -> None:
        from .correo import DialogoCorreo
        from .modales import DialogoExportando

        progs = [self.ctx.al_dia(p) for p in progs]
        if not progs:
            return
        eleccion = DialogoCorreo(self, progs, padre)
        self.ultimo_dialogo = eleccion
        if eleccion.exec() != QDialog.DialogCode.Accepted:
            return
        adjuntos = [a for a in eleccion.plan if a.se_adjunta]
        por_exportar: dict[str, tuple[dict, list[str], Path]] = {}
        for a in adjuntos:
            if a.estado == "exportar":
                clave = f"{a.prog['curso_escolar']}/{almacen.identificador(a.prog)}"
                por_exportar.setdefault(clave, (a.prog, [], a.ruta.parent))[1].append(a.formato)
        tareas = [(copy.deepcopy(p), fmts, carpeta, self.ctx.datos_curso_de(p))
                  for p, fmts, carpeta in por_exportar.values()]
        cliente = self.ctx.gestor.valores.cliente_correo
        b = correo.Borrador(eleccion.para(), eleccion.asunto.text().strip(), eleccion.cuerpo.toPlainText(),
                            [a.ruta for a in adjuntos])
        cat, opciones, motor = self.ctx.catalogo, self.ctx.opciones_documento(), self._motor()
        pasos = [f"Exportando {self.nombre(p)}" for p, *_ in tareas] + [f"Abriendo el correo en "
                                                                         f"{correo.NOMBRES[correo.metodos(cliente)[0]]}"]
        dialogo = DialogoExportando("Preparando el correo", b.asunto, pasos, padre)
        self.ultimo_dialogo = dialogo

        def trabajo(avance):
            hechos = []
            for i, (p, fmts, carpeta, curso) in enumerate(tareas):
                avance(i, len(pasos), pasos[i])
                hechos.append((p, exportacion.exportar(p, cat, curso, carpeta, fmts, opciones, motor)))
            avance(len(tareas), len(pasos), pasos[-1])
            faltan = [r for r in b.adjuntos if not Path(r).is_file()]  # un PDF que no se ha podido hacer
            if faltan:
                b.adjuntos = [r for r in b.adjuntos if r not in faltan]
                b.cuerpo = correo.sin_los_que_faltan(b.cuerpo, faltan)
            if not b.adjuntos:      # sin nada que adjuntar, no se abre un correo vacío
                return hechos, None
            return hechos, correo.abrir_borrador(b, cliente, carpeta_datos() / "correo")

        def listo(resultado):
            hechos, r = resultado
            avisos = [r.texto if r else "No se ha creado el correo: no se ha podido hacer ningún archivo para "
                                        "adjuntar."]
            for p, res in hechos:
                self.ctx.exportada(res.archivos, p)
                if res.error_pdf:
                    avisos.append(f"El PDF de {self.nombre(p)} no se ha podido hacer ({res.error_pdf}): no va "
                                  "adjunto.")
            total = correo.tamano(b.adjuntos)
            if correo.supera_limite(total):
                avisos.append(f"Los adjuntos suman {correo.texto_tamano(total)}: más de {correo.LIMITE_MB} MB, puede "
                              "que el correo no salga.")
            titulo = "Correo sin crear" if r is None else "Correo nuevo abierto" if r.manual else "Correo creado"
            dialogo.terminar(titulo, b.adjuntos, "\n".join(avisos))

        self.lanzar(trabajo, dialogo, listo)
        dialogo.exec()

    # -- Borrar ------------------------------------------------------------------------------------------------------
    def borrar(self, progs: list[dict], padre=None) -> list[dict]:
        """Pregunta diciendo qué se borra y quita las programaciones de este equipo (a la papelera, ADR-024)."""
        if not progs:
            return []
        lista = "\n".join(f"• {self.nombre(p)} ({p['curso_escolar']})" for p in progs)
        texto = (f"Se quitan de la lista de este equipo y su archivo de trabajo, con sus copias de autoguardado, va a "
                 f"la papelera (de allí lo puedes recuperar):\n\n{lista}\n\nNo se borra nada de lo exportado: los Word "
                 "y los PDF y la carpeta de Teams se quedan como están.")
        r = QMessageBox.question(padre, "Borrar", texto,
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                 QMessageBox.StandardButton.No)
        if r != QMessageBox.StandardButton.Yes:
            return []
        quitadas, errores = self.ctx.quitar(progs, papelera)
        if errores:
            QMessageBox.warning(padre, "Borrar", "No se ha podido borrar todo:\n" + "\n".join(errores))
        return quitadas


# ---------------------------------------------------------------------------------------------------------------------
# Exportar a una carpeta
# ---------------------------------------------------------------------------------------------------------------------
class DialogoExportarCarpeta(QDialog):
    """Carpeta y formatos; la lista dice qué ya existe (se preguntará) y qué no se puede exportar."""

    def __init__(self, gestion: Gestion, progs: list[dict], padre=None):
        super().__init__(padre)
        self.gestion = gestion
        self.ctx = gestion.ctx
        self.progs = progs
        self._bloqueadas = [p for p in progs if gestion.bloquea(p)]
        self.setWindowTitle("Exportar a una carpeta")
        self.resize(660, 500)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(12)
        capa.addWidget(_titulo("Exportar a una carpeta"))
        capa.addWidget(etiqueta("Se exportan con el nombre de siempre. Si alguno ya está en la carpeta, la app te "
                                "pregunta antes de sustituirlo.", "muted", envolver=True))
        capa.addWidget(etiqueta("Carpeta", "etiqueta"))
        fila = QHBoxLayout()
        self.campo = QLineEdit()
        self.campo.setReadOnly(True)
        self.campo.setAccessibleName("Carpeta de destino")
        fila.addWidget(self.campo, 1)
        elegir = boton("Elegir…", pequeno=True)
        elegir.clicked.connect(self._elegir)
        fila.addWidget(elegir)
        capa.addLayout(fila)
        capa.addWidget(etiqueta("Formatos", "etiqueta"))
        zona, self.chips = chips_formato(self.ctx.gestor.valores.formatos, self._pintar)
        capa.addWidget(zona)
        capa.addWidget(etiqueta("Programaciones", "etiqueta"))
        contenido = QWidget()
        self.capa_lista = QVBoxLayout(contenido)
        self.capa_lista.setContentsMargins(0, 0, 0, 0)
        self.capa_lista.setSpacing(4)
        caja = desplazable(contenido)
        caja.setFrameShape(QFrame.Shape.NoFrame)
        capa.addWidget(caja, 1)
        botones = QHBoxLayout()
        botones.addStretch(1)
        cancelar = boton("Cancelar")
        cancelar.clicked.connect(self.reject)
        self.boton = boton("Exportar", primario=True)
        self.boton.clicked.connect(self.accept)
        botones.addWidget(cancelar)
        botones.addWidget(self.boton)
        capa.addLayout(botones)
        self.carpeta = gestion.carpeta_habitual(progs[0])
        self.poner_carpeta(self.carpeta)

    def formatos(self) -> list[str]:
        return [f for f, b in self.chips.items() if b.isChecked()]

    def bloqueadas(self) -> list[dict]:
        return list(self._bloqueadas)

    def exportables(self) -> list[dict]:
        return [p for p in self.progs if p not in self._bloqueadas]

    def poner_carpeta(self, carpeta: str | Path) -> None:
        self.carpeta = Path(carpeta)
        self.campo.setText(str(self.carpeta))
        self._pintar()

    def _elegir(self) -> None:
        ruta = QFileDialog.getExistingDirectory(self, "¿Dónde se exportan?", str(self.carpeta if self.carpeta.is_dir()
                                                                                 else Path.home()))
        if ruta:
            self.poner_carpeta(ruta)

    def _pintar(self) -> None:
        while self.capa_lista.count():
            w = self.capa_lista.takeAt(0).widget()
            if w:
                w.hide()
                w.deleteLater()
        self.filas: dict[str, QLabel] = {}
        for p in self.progs:
            nombre = self.gestion.nombre(p)
            if p in self._bloqueadas:
                rol, estado = "rojo", "tiene avisos en rojo: no se exporta (ábrela para corregirlos)"
            elif any(d.exists() for d in exportacion.destinos(p, self.ctx.catalogo, self.carpeta, self.formatos())):
                rol, estado = "aviso-texto", "ya está en la carpeta: se te preguntará"
            else:
                rol, estado = "pequeno", "se exporta"
            e = etiqueta(f"{nombre} · {estado}", rol, envolver=True)
            e.setStyleSheet("font-size:13px;font-weight:400;")  # el color, del rol; el tamaño, igual en todas
            self.filas[nombre] = e
            self.capa_lista.addWidget(e)
        self.capa_lista.addStretch(1)
        self.boton.setEnabled(bool(self.exportables()))
