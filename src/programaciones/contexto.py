"""Lo que comparte toda la aplicación: ajustes, catálogo, curso escolar y la lista de módulos (como en Partes de salida).

Las pantallas no leen archivos por su cuenta: piden aquí y escuchan las señales.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from .ajustes import GestorAjustes, curso_escolar_de
from .catalogo import Catalogo, texto
from .rutas import carpeta_datos

logger = logging.getLogger(__name__)


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


class Contexto(QObject):
    ajustes_cambiados = pyqtSignal()
    #: Módulo elegido en la columna izquierda (`EntradaModulo`) o None: lo escuchan la ficha y el estado.
    modulo_elegido = pyqtSignal(object)

    def __init__(self, carpeta: Path | None = None, avance=None, catalogo: Catalogo | None = None):
        """`avance(texto, porcentaje)` cuenta cada paso a la pantalla de presentación."""
        super().__init__()
        avance = avance or (lambda _t, _p: None)
        avance("Cargando el catálogo…", 15)
        self.carpeta = Path(carpeta or carpeta_datos())
        self.gestor = GestorAjustes(self.carpeta)
        self.catalogo = catalogo or Catalogo()
        self.curso_escolar = curso_escolar_de()
        avance("Comprobando el currículo…", 55)
        self.modulos = modulos_del_catalogo(self.catalogo)
        self.ciclos = self.catalogo.siglas()
        #: Fechas de evaluación y de empresa del curso (`catalogo/cursos/`); None mientras no estén dadas de alta.
        self.datos_curso = self.catalogo.curso_escolar(self.curso_escolar)
        #: Programaciones del profesor en este equipo (las rellena la pantalla «Programaciones» en la fase F4).
        self.programaciones: list = []
        self.modulo: EntradaModulo | None = None
        logger.info("Catálogo %s: %d ciclos, %d módulos; curso %s", self.catalogo.version, len(self.ciclos),
                    len(self.modulos), self.curso_escolar)

    def elegir(self, entrada: EntradaModulo | None) -> None:
        self.modulo = entrada
        self.modulo_elegido.emit(entrada)
