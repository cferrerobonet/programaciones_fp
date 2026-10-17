"""Lo que comparte toda la aplicación: ajustes, catálogo, curso escolar, la lista de módulos y la programación abierta
(como en Partes de salida).

Las pantallas no leen archivos por su cuenta: piden aquí y escuchan las señales. Cada cambio del profesor pasa por
`cambiar` (marca el paso como confirmado y guarda solo, RNF-05); lo calculado se recalcula siempre con `calculos`.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from . import almacen, documento, programacion, validacion
from .ajustes import GestorAjustes, curso_escolar_de
from .catalogo import Catalogo, Ficha, texto
from .rutas import carpeta_datos

logger = logging.getLogger(__name__)
ESPERA_GUARDADO = 1500   # ms tras el último cambio


@dataclass(frozen=True)
class EntradaModulo:
    """Una fila del horario de un ciclo: lo que la columna «Módulos» enseña y filtra."""

    sigla: str
    grado: str            # «GM» o «GS»
    curso: int            # 1 o 2
    codigo: str           # «0517»; el Proyecto de 1.º, «0526» con curso 1
    codigo_horario: str   # tal cual en el catálogo: «0526p»
    nombre: str           # el del Decreto 95/2026
    horas: int
    h_sem: int
    pendiente: str = ""   # dato que falta en la fuente (Proyecto intermodular de GM…): se enseña como «pendiente»

    @property
    def clave(self) -> str:
        return f"{self.sigla}-{self.curso}-{self.codigo}"


def modulos_del_catalogo(cat: Catalogo) -> list[EntradaModulo]:
    """Todas las filas de todos los ciclos, por ciclo, curso y código."""
    out = []
    for sigla in cat.siglas():
        ciclo = cat.ciclo(sigla)
        for m in ciclo["modulos"]:
            out.append(EntradaModulo(
                sigla=sigla, grado=ciclo["grado"], curso=m["curso"], codigo=m["codigo"].rstrip("p"),
                codigo_horario=m["codigo"], nombre=texto(m["nombre"]), horas=m["h_anuales"], h_sem=m["h_sem"],
                pendiente=m.get("pendiente") or "",
            ))
    return sorted(out, key=lambda e: (e.sigla, e.curso, e.codigo))


def fecha_corta(iso: str) -> str:
    """«2026-10-14T10:42» → «14/10/2026 10:42»."""
    if not iso:
        return "—"
    d = dt.datetime.fromisoformat(iso)
    return d.strftime("%d/%m/%Y %H:%M")


class Contexto(QObject):
    ajustes_cambiados = pyqtSignal()
    #: Módulo elegido en la columna izquierda (`EntradaModulo`) o None: lo escuchan la ficha y el estado.
    modulo_elegido = pyqtSignal(object)
    #: Programación abierta (dict) o None: cambia la ficha entre «Aún no hay programación» y los pasos.
    programacion_abierta = pyqtSignal(object)
    #: Un dato o el estado de un bloque de la programación abierta: el estado y los avisos se recalculan.
    programacion_cambiada = pyqtSignal()
    #: El listado de programaciones de este equipo (guardar, exportar, heredar).
    programaciones_cambiadas = pyqtSignal()

    def __init__(self, carpeta: Path | None = None, avance=None, catalogo: Catalogo | None = None):
        """`avance(texto, porcentaje)` cuenta cada paso a la pantalla de presentación."""
        super().__init__()
        avance = avance or (lambda _t, _p: None)
        avance("Cargando el catálogo…", 15)
        self.carpeta = Path(carpeta or carpeta_datos())
        self.gestor = GestorAjustes(self.carpeta)
        self.catalogo = catalogo or Catalogo()
        #: Catálogos que la app conoce, por versión: el de ahora y, con F5, los anteriores descargados. Sirven para
        #: enseñar los cambios de currículo de una programación hecha con otra versión (ADR-015).
        self.catalogos: dict[str, Catalogo] = {self.catalogo.version: self.catalogo}
        self.curso_escolar = curso_escolar_de()
        avance("Comprobando el currículo…", 55)
        self.modulos = modulos_del_catalogo(self.catalogo)
        self.ciclos = self.catalogo.siglas()
        #: Fechas de evaluación y de empresa del curso (`catalogo/cursos/`); None mientras no estén dadas de alta.
        self.datos_curso = self.catalogo.curso_escolar(self.curso_escolar)
        self.almacen = almacen.Almacen(self.carpeta)
        self.guardadas: list[almacen.Guardada] = []
        #: Filas del listado «Programaciones» (dicts para `TablaPaginada`).
        self.programaciones: list[dict] = []
        self.modulo: EntradaModulo | None = None
        self.ficha: Ficha | None = None
        self.prog: dict | None = None
        self._guardar_luego = QTimer(self, singleShot=True, interval=ESPERA_GUARDADO, timeout=self.guardar)
        self.recargar_programaciones()
        logger.info("Catálogo %s: %d ciclos, %d módulos; curso %s", self.catalogo.version, len(self.ciclos),
                    len(self.modulos), self.curso_escolar)

    # -- módulo y programación ---------------------------------------------------------------------------------------
    def entrada(self, sigla: str, curso: int, codigo: str) -> EntradaModulo | None:
        return next((m for m in self.modulos if (m.sigla, m.curso, m.codigo) == (sigla, curso, codigo)), None)

    def elegir(self, entrada: EntradaModulo | None) -> None:
        """Elige un módulo y abre su programación de este curso escolar, si la hay en este equipo."""
        self._guardar_pendiente()
        self.modulo = entrada
        self.ficha = self.catalogo.ficha(entrada.sigla, entrada.codigo, entrada.curso) if entrada else None
        self.prog = self.almacen.cargar(self.curso_escolar, entrada.sigla, entrada.curso, entrada.codigo) \
            if entrada else None
        self.modulo_elegido.emit(entrada)
        self.programacion_abierta.emit(self.prog)

    def empezar(self) -> dict:
        """Programación en blanco del módulo elegido. El profesorado sale de Ajustes (lo escribió el profesor)."""
        m = self.modulo
        prog = programacion.nueva(m.sigla, m.curso, m.codigo, self.curso_escolar, self.catalogo.version,
                                  documento.metadatos_plantilla()["version"])
        nombre = self.gestor.valores.nombre_profesor.strip()
        if nombre:
            prog["profesorado"] = [nombre]
            prog["bloques"]["profesorado"] = "confirmado"
        almacen.anotar(prog, "creada")
        return self.abrir(prog)

    def abrir(self, prog: dict) -> dict:
        """Abre una programación (heredada, importada o de un archivo): elige su módulo y la guarda en este equipo."""
        self._guardar_pendiente()
        prog = programacion.validar(prog)
        entrada = self.entrada(prog["ciclo"], prog["curso"], prog["modulo"])
        if entrada is None:
            raise programacion.ProgramacionNoValida(
                f"{prog['ciclo']} {prog['curso']} - {prog['modulo']} no es un módulo del catálogo")
        if entrada != self.modulo:
            self.modulo = entrada
            self.ficha = self.catalogo.ficha(entrada.sigla, entrada.codigo, entrada.curso)
            self.modulo_elegido.emit(entrada)
        self.prog = prog
        self.guardar()
        self.programacion_abierta.emit(prog)
        return prog

    def cambiar(self, paso: str | None, cambio) -> None:
        """Aplica `cambio(prog)`; el paso queda confirmado (cambiar un bloque heredado también lo revisa: HU-09)."""
        if self.prog is None:
            return
        cambio(self.prog)
        if paso:
            for b in almacen.PASOS[paso][1]:
                self.prog["bloques"][b] = "confirmado"
        almacen.marcar_cambio(self.prog)
        self._guardar_luego.start()
        self.programacion_cambiada.emit()

    def confirmar(self, paso: str) -> None:
        self.cambiar(paso, lambda _p: None)

    # -- cálculo y validación ----------------------------------------------------------------------------------------
    def datos_curso_de(self, prog: dict) -> dict | None:
        if prog["curso_escolar"] == self.curso_escolar:
            return self.datos_curso
        return self.catalogo.curso_escolar(prog["curso_escolar"])

    def curso_pendiente(self, prog: dict) -> str:
        if self.datos_curso_de(prog) is not None:
            return ""
        return f"fechas de evaluación y de formación en empresa del curso {prog['curso_escolar']}"

    def cambios_de_curriculo(self) -> list[str]:
        """Cambios de RA y criterios entre el catálogo de la programación y el de ahora (ADR-015). Sin el catálogo
        anterior en este equipo (llega con F5), no hay con qué comparar."""
        if self.prog is None or self.prog["catalogo"] == self.catalogo.version:
            return []
        anterior = self.catalogos.get(self.prog["catalogo"])
        if anterior is None:
            return []
        return anterior.diferencias(self.catalogo, self.prog["ciclo"], self.prog["modulo"])

    def aceptar_cambios(self) -> list[str]:
        """El profesor acepta el currículo nuevo: la programación pasa a la versión de ahora y los bloques que usan los
        RA cambiados quedan por revisar. Devuelve los pasos afectados."""
        cambios = self.cambios_de_curriculo()
        ras = {int(c.split()[0][2:]) for c in cambios if c.startswith("RA")}
        prog = self.prog
        afectados = []
        if any(set(e.get("ra", [])) & ras for e in prog["elementos"]):
            afectados.append("unidades")
        if any(int(k) in ras for k in prog.get("empresa", {})):
            afectados.append("empresa")
        if any(int(k) in ras for k in prog.get("ra_competencias", {})):
            afectados.append("ra_competencias")
        quedan = set(self.ficha.numeros_ra)
        for e in prog["elementos"]:
            e["ra"] = [r for r in e["ra"] if r in quedan]
        for clave in ("empresa", "centro_ajustado", "ra_competencias"):
            prog[clave] = {k: v for k, v in prog.get(clave, {}).items() if int(k) in quedan}
        prog["catalogo"] = self.catalogo.version
        for paso in afectados:
            for b in almacen.PASOS[paso][1]:
                if prog["bloques"].get(b) == "confirmado":
                    prog["bloques"][b] = "heredado"
        almacen.anotar(prog, f"cambios del currículo aceptados ({self.catalogo.version})")
        self.guardar()
        self.programacion_cambiada.emit()
        return afectados

    def avisos(self) -> list[validacion.Aviso]:
        if self.prog is None or self.ficha is None:
            return []
        return validacion.validar(self.prog, self.ficha, self.cambios_de_curriculo(), self.curso_pendiente(self.prog))

    def opciones_documento(self) -> documento.Opciones:
        return documento.Opciones(correo_pie=self.gestor.valores.correo_pie)

    # -- guardar y listado -------------------------------------------------------------------------------------------
    def guardar(self) -> None:
        self._guardar_luego.stop()
        if self.prog is None:
            return
        try:
            self.almacen.guardar(self.prog)
        except (OSError, programacion.ProgramacionNoValida):
            logger.exception("No se ha podido guardar la programación")
            return
        self.recargar_programaciones()

    def _guardar_pendiente(self) -> None:
        if self._guardar_luego.isActive():
            self.guardar()

    def exportada(self, archivos: list[Path]) -> None:
        if self.prog is None:
            return
        almacen.anotar(self.prog, "exportada: " + ", ".join(p.name for p in archivos))
        self.guardar()
        self.programacion_cambiada.emit()

    def recargar_programaciones(self) -> None:
        self.guardadas = self.almacen.todas()
        filas = []
        for g in self.guardadas:
            p = g.programacion
            try:
                ficha = self.catalogo.ficha(p["ciclo"], p["modulo"], p["curso"])
                nombre = documento.nombre_archivo(ficha, "x")[:-2]
            except KeyError:
                nombre = f"{p['ciclo']} {p['curso']} - {p['modulo']}"
            filas.append({"id": g.id, "programacion": nombre, "curso_escolar": p["curso_escolar"],
                          "estado": almacen.texto_estado(p), "estado_clave": almacen.estado(p),
                          "exportada_iso": almacen.ultima_exportacion(p),
                          "exportada": fecha_corta(almacen.ultima_exportacion(p)),
                          "modificada": g.ruta.stat().st_mtime, "ruta": str(g.ruta), "prog": p})
        self.programaciones = filas
        self.programaciones_cambiadas.emit()

    def estado_modulo(self, entrada: EntradaModulo) -> str:
        """«exportada», «en_curso», «heredada» o «» (sin programación este curso escolar)."""
        ident = f"{self.curso_escolar}/{entrada.clave}"
        fila = next((f for f in self.programaciones if f["id"] == ident), None)
        return fila["estado_clave"] if fila else ""

    def recientes(self, n: int = 4) -> list[dict]:
        return sorted(self.programaciones, key=lambda f: -f["modificada"])[:n]
