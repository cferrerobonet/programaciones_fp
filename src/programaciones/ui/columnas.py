"""Las tres zonas de la ventana principal (DESIGN.md, «The Three Zones Rule»; maqueta v0, pantallas 01 a 07).

- `ColumnaModulos` (300 px): buscador, chips de grado, «Favoritos» y de ciclo, curso, «Limpiar» y la lista de módulos
  en filas de 58 px con su estado (sin empezar · en curso · exportada) y la estrella de favorito, que se marca con un
  clic, con el clic derecho o con ⌘D sobre la fila elegida.
- `ColumnaFicha` (flexible): «Elige un módulo»; con un módulo, su cabecera, la caja «DEL CURRÍCULO» (solo lectura, con
  su fuente) y, sin programación, «Empezar en blanco» o «Nueva a partir de…»; con programación, la barra de pasos y el
  bloque elegido, con la banda «Heredado… · revisa y confirma».
- `ColumnaEstado` (340 px): «PROGRAMACIONES RECIENTES» sin módulo; con módulo, «ESTADO» (bloques, progreso, horas de
  centro y empresa), los avisos V-xx con «Ir ›» y «VISTA PREVIA»; siempre, abajo, «EXPORTAR» con los chips «Word» y
  «PDF» y el botón grande «Exportar ⌘E».
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QIcon, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QProgressBar,
    QSizePolicy,
    QStackedLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import almacen, calculos, excel_ra, validacion
from ..ajustes import estado_carpeta
from ..catalogo import texto as texto_idioma
from . import estilo
from .bloques import CLASES, CORTOS, ORDEN
from .componentes import EstadoVacio, FlujoLayout, atajo, boton, desplazable, etiqueta, refrescar_estilo
from .listado import sin_tildes

ELIGE_UN_MODULO = ("Elige un módulo", "Búscalo por código o nombre, o fíltralo por grado, ciclo y curso. "
                   "Los datos oficiales ya están dentro.")
GRADOS = {"GB": "G. Básico", "GM": "G. Medio", "GS": "G. Superior"}
SIN_PROGRAMACION = ("Aún no hay programación para {curso}",
                    "Empieza en blanco o hereda la del curso pasado: la tuya o la de otro profesor.")
ESTADO_BLOQUE = {"confirmado": ("Confirmado", "ok"), "heredado": ("Heredado · revisar", "aviso-texto"),
                 "vacio": ("Vacío", "pequeno")}
#: Aviso → paso al que lleva «Ir ›».
IR_A = {"V-15": "unidades", "V-16": "ra_competencias", "V-01": "unidades", "V-02": "unidades", "V-03": "unidades", "V-04": "empresa", "V-05": "profesorado",
        "V-07": "ra_competencias", "V-09": "unidades", "V-10": "empresa", "V-12": "unidades", "V-13": "empresa"}


def _titulo(texto: str, tam: int) -> QLabel:
    t = QLabel(texto)
    t.setFont(estilo.fuente(tam, QFont.Weight.Bold, estilo.TITULAR))
    t.setWordWrap(True)
    return t


def _limpiar(capa) -> None:
    while capa.count():
        item = capa.takeAt(0)
        if item.widget():
            item.widget().hide()  # deleteLater espera al bucle de eventos: hasta entonces seguiría a la vista
            item.widget().deleteLater()
        elif item.layout():
            _limpiar(item.layout())


# ---------------------------------------------------------------------------------------------------------------------
# Módulos
# ---------------------------------------------------------------------------------------------------------------------
class FilaModulo(QWidget):
    """Código en su cuadro dorado, nombre en dos líneas, «2.º SEA · G. Superior», el icono de estado y la
    estrella de favorito (con nombre accesible y su estado, marcada o no)."""

    estrella_pulsada = pyqtSignal(object)  # la entrada del módulo

    def __init__(self, entrada):
        super().__init__()
        self.entrada = entrada
        fila = QHBoxLayout(self)
        fila.setContentsMargins(8, 4, 4, 4)
        fila.setSpacing(8)
        # el Proyecto de GB lleva en el horario un código de siete cifras por ciclo (3160956): en el cuadro, el del RD
        visible = entrada.mostrar
        codigo = QLabel(visible[:4] if len(visible) == 7 and visible.isdigit() else visible)
        codigo.setToolTip(visible)
        codigo.setProperty("rol", "codigo")
        codigo.setFixedSize(46, 46)
        codigo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        codigo.setFont(estilo.fuente(17, QFont.Weight.Bold, estilo.TITULAR))
        codigo.setStyleSheet(f"background:{estilo.T['gold_soft']};border-radius:8px;")
        fila.addWidget(codigo)
        textos = QVBoxLayout()
        textos.setSpacing(0)
        self.nombre = QLabel()
        self.nombre.setFont(estilo.fuente(14, QFont.Weight.Bold))
        self.nombre.setWordWrap(True)
        fm = QFontMetrics(self.nombre.font())
        self.nombre.setText(fm.elidedText(entrada.nombre, Qt.TextElideMode.ElideRight, 2 * 125 - 20))
        self.nombre.setToolTip(entrada.nombre)
        textos.addWidget(self.nombre)
        meta = f"{entrada.curso}.º {entrada.sigla} · {GRADOS.get(entrada.grado, entrada.grado)}"
        if entrada.pendiente:
            meta += " · pendiente"
        self.meta = etiqueta(meta, "pequeno")
        textos.addWidget(self.meta)
        fila.addLayout(textos, 1)
        self.icono = QLabel()
        self.icono.setFixedWidth(18)
        fila.addWidget(self.icono)
        self.estrella = boton("", enlace=True)
        self.estrella.setCheckable(True)
        self.estrella.setFixedSize(26, 26)
        self.estrella.setIconSize(QSize(16, 16))
        self.estrella.setAccessibleName(f"Favorito: {entrada.mostrar} {entrada.nombre}")
        self.estrella.clicked.connect(lambda _=False: self.estrella_pulsada.emit(self.entrada))
        fila.addWidget(self.estrella)
        self.poner_favorito(False)

    def poner_favorito(self, marcado: bool) -> None:
        self.estrella.setChecked(marcado)
        self.estrella.setIcon(QIcon(estilo.icono_estrella(estilo.T["gold"] if marcado else estilo.T["muted"], 16,
                                                          llena=marcado)))
        accion = "Quitar de favoritos" if marcado else "Añadir a favoritos"
        self.estrella.setToolTip(f"{accion} ({atajo('D')})")
        self.estrella.setAccessibleDescription("Favorito: marcado" if marcado else "Favorito: sin marcar")

    def poner_estado(self, estado: str) -> None:
        clave = {"exportada": "exportada", "en_curso": "en_curso", "heredada": "heredado"}.get(estado)
        self.icono.setPixmap(estilo.icono_estado(clave, 15) if clave else QPixmap())
        self.icono.setToolTip({"exportada": "Exportada", "en_curso": "En curso", "heredada": "Heredada · sin revisar"}
                              .get(estado, ""))


class ColumnaModulos(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setFixedWidth(300)
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 10)
        v.setSpacing(10)
        self.buscador = QLineEdit()
        self.buscador.setObjectName("buscador")
        self.buscador.setPlaceholderText("Código o nombre del módulo")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.addAction(estilo.icono_lupa(estilo.T["muted"]), QLineEdit.ActionPosition.LeadingPosition)
        self.buscador.textChanged.connect(self._buscar)
        self.buscador.returnPressed.connect(self.elegir_primero)
        v.addWidget(self.buscador)

        grados = QWidget()
        capa = FlujoLayout(grados, 6)
        self.grupo_grado = QButtonGroup(self)
        self.chips_grado: dict[str, object] = {}
        for clave, texto in (("", "Todos"), *GRADOS.items()):
            b = boton(texto, chip=True)
            b.setCheckable(True)
            self.grupo_grado.addButton(b)
            b.clicked.connect(lambda _=False, k=clave: self.filtrar_grado(k))
            capa.addWidget(b)
            self.chips_grado[clave] = b
        self.chips_grado[""].setChecked(True)
        self.chip_favoritos = boton("Favoritos", chip=True)
        self.chip_favoritos.setCheckable(True)
        self.chip_favoritos.setIcon(QIcon(estilo.icono_estrella(estilo.T["gold"], 14, llena=True)))
        self.chip_favoritos.setToolTip("Solo los módulos marcados con la estrella")
        self.chip_favoritos.setAccessibleName("Solo favoritos")
        self.chip_favoritos.toggled.connect(self.filtrar_favoritos)
        capa.addWidget(self.chip_favoritos)
        v.addWidget(grados)
        self.zona_ciclos = QWidget()
        self.capa_ciclos = FlujoLayout(self.zona_ciclos, 6)
        self.chips_ciclo: dict[str, object] = {}
        for sigla in ctx.ciclos:
            b = boton(sigla, chip=True)
            b.setCheckable(True)
            b.setToolTip(texto_idioma(ctx.catalogo.ciclo(sigla)["nombre"]))
            b.clicked.connect(lambda on, s=sigla: self.filtrar_ciclo(s if on else ""))
            self.capa_ciclos.addWidget(b)
            self.chips_ciclo[sigla] = b
        v.addWidget(self.zona_ciclos)
        fila = QHBoxLayout()
        self.curso = QComboBox()
        for texto, valor in (("Todos los cursos", 0), ("1.º curso", 1), ("2.º curso", 2)):
            self.curso.addItem(texto, valor)
        self.curso.currentIndexChanged.connect(lambda _i: self._aplicar())
        fila.addWidget(self.curso, 1)
        self.limpiar = boton("Limpiar")
        self.limpiar.clicked.connect(self.limpiar_filtros)
        fila.addWidget(self.limpiar)
        v.addLayout(fila)
        self.cuenta = etiqueta("", "pequeno", envolver=True)
        v.addWidget(self.cuenta)
        self.lista = QListWidget()
        self.lista.setObjectName("modulos")
        self.lista.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.filas: list[FilaModulo] = []
        for m in sorted(ctx.modulos, key=lambda e: (e.sigla, e.mostrar, e.curso, e.nombre)):
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 58))
            item.setData(Qt.ItemDataRole.UserRole, m)
            self.lista.addItem(item)
            fila_modulo = FilaModulo(m)
            fila_modulo.estrella_pulsada.connect(self.cambiar_favorito)
            self.lista.setItemWidget(item, fila_modulo)
            self.filas.append(fila_modulo)
        self.lista.currentItemChanged.connect(self._elegida)
        self.lista.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lista.customContextMenuRequested.connect(self._menu)
        self.atajo_favorito = QShortcut(QKeySequence("Ctrl+D"), self.lista)
        self.atajo_favorito.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.atajo_favorito.activated.connect(self.favorito_de_la_elegida)
        self.ultimo_menu: QMenu | None = None
        v.addWidget(self.lista, 1)
        self.grado, self.ciclo = "", ""
        self.solo_favoritos = False
        ctx.programaciones_cambiadas.connect(self.poner_estados)
        ctx.modulo_elegido.connect(self.marcar)
        ctx.favoritos_cambiados.connect(self.poner_favoritos)
        self.poner_estados()
        self.poner_favoritos()

    # Filtros
    def filtrar_grado(self, grado: str) -> None:
        self.grado = grado
        self.chips_grado[grado].setChecked(True)
        if self.ciclo and grado and self.ctx.catalogo.ciclo(self.ciclo)["grado"] != grado:
            self.ciclo = ""
        self._aplicar()

    def filtrar_ciclo(self, sigla: str) -> None:
        self.ciclo = sigla
        self._aplicar()

    def filtrar_favoritos(self, solo: bool) -> None:
        self.solo_favoritos = bool(solo)
        if self.chip_favoritos.isChecked() != self.solo_favoritos:
            self.chip_favoritos.setChecked(self.solo_favoritos)
        self._aplicar()

    def limpiar_filtros(self) -> None:
        self.buscador.clear()
        self.grado, self.ciclo = "", ""
        self.chips_grado[""].setChecked(True)
        self.chip_favoritos.blockSignals(True)
        self.chip_favoritos.setChecked(False)
        self.chip_favoritos.blockSignals(False)
        self.solo_favoritos = False
        self.curso.setCurrentIndex(0)
        self._aplicar()

    # Favoritos
    def cambiar_favorito(self, entrada) -> bool:
        return self.ctx.cambiar_favorito(entrada)

    def favorito_de_la_elegida(self) -> None:
        item = self.lista.currentItem()
        if item is not None and not item.isHidden():
            self.cambiar_favorito(item.data(Qt.ItemDataRole.UserRole))

    def menu_favorito(self, entrada) -> QMenu:
        menu = QMenu(self)
        texto = "Quitar de favoritos" if self.ctx.es_favorito(entrada) else "Añadir a favoritos"
        accion = menu.addAction(texto)
        accion.setShortcut(QKeySequence("Ctrl+D"))
        accion.triggered.connect(lambda _=False: self.cambiar_favorito(entrada))
        self.ultimo_menu = menu
        return menu

    def _menu(self, pos) -> None:
        item = self.lista.itemAt(pos)
        if item is not None:
            self.menu_favorito(item.data(Qt.ItemDataRole.UserRole)).popup(self.lista.viewport().mapToGlobal(pos))

    def poner_favoritos(self) -> None:
        for f in self.filas:
            f.poner_favorito(self.ctx.es_favorito(f.entrada))
        self._aplicar()

    def visibles(self) -> list:
        return [self.lista.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.lista.count())
                if not self.lista.item(i).isHidden()]

    def _buscar(self) -> None:
        self._aplicar()
        texto = self.buscador.text().strip()
        if len(texto) >= 4 and texto.isdigit():
            iguales = [m for m in self.visibles() if texto in (m.codigo, m.mostrar)]
            if len(iguales) == 1:
                self.elegir(iguales[0])

    def _aplicar(self) -> None:
        q = sin_tildes(self.buscador.text()).lower().split()
        curso = self.curso.currentData()
        for sigla, b in self.chips_ciclo.items():
            grado = self.ctx.catalogo.ciclo(sigla)["grado"]
            b.setVisible(not self.grado or grado == self.grado)
            b.setChecked(sigla == self.ciclo)
        self.zona_ciclos.updateGeometry()
        n = 0
        for i in range(self.lista.count()):
            m = self.lista.item(i).data(Qt.ItemDataRole.UserRole)
            texto = sin_tildes(f"{m.mostrar} {m.nombre} {m.sigla}").lower()
            ver = ((not self.grado or m.grado == self.grado) and (not self.ciclo or m.sigla == self.ciclo)
                   and (not curso or m.curso == curso) and all(t in texto for t in q)
                   and (not self.solo_favoritos or self.ctx.es_favorito(m)))
            self.lista.item(i).setHidden(not ver)
            n += ver
        partes = [f"{n} módulos"]
        if self.ciclo:
            partes.append(self.ciclo)
        elif self.grado:
            partes.append(GRADOS[self.grado])
        if self.solo_favoritos:
            partes.append("favoritos" if self.ctx.gestor.valores.favoritos else
                          "ninguno marcado: pulsa la estrella de un módulo")
        self.cuenta.setText(" · ".join(partes))
        self.limpiar.setEnabled(bool(self.buscador.text() or self.grado or self.ciclo or curso or self.solo_favoritos))

    # Elegir
    def elegir_primero(self) -> None:
        visibles = self.visibles()
        if visibles:
            self.elegir(visibles[0])

    def elegir(self, entrada) -> None:
        for i in range(self.lista.count()):
            if self.lista.item(i).data(Qt.ItemDataRole.UserRole) == entrada:
                self.lista.setCurrentRow(i)
                return

    def _elegida(self, actual, _anterior) -> None:
        if actual is not None:
            entrada = actual.data(Qt.ItemDataRole.UserRole)
            if entrada != self.ctx.modulo:
                self.ctx.elegir(entrada)

    def marcar(self, entrada) -> None:
        """El módulo se eligió desde otro sitio (abrir, heredar): se marca sin volver a elegirlo."""
        self.lista.blockSignals(True)
        if entrada is None:
            self.lista.setCurrentRow(-1)
        else:
            for i in range(self.lista.count()):
                if self.lista.item(i).data(Qt.ItemDataRole.UserRole) == entrada:
                    self.lista.setCurrentRow(i)
                    self.lista.scrollToItem(self.lista.item(i))
        self.lista.blockSignals(False)

    def poner_estados(self) -> None:
        for f in self.filas:
            f.poner_estado(self.ctx.estado_modulo(f.entrada))


# ---------------------------------------------------------------------------------------------------------------------
# Ficha
# ---------------------------------------------------------------------------------------------------------------------
class CajaCurriculo(QFrame):
    """«DEL CURRÍCULO»: RA, competencias del módulo y normativa, de solo lectura y con su fuente. Abierta sin
    programación; plegada en una línea mientras se rellenan los bloques. «Ver» abre el detalle."""

    ver = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setProperty("rol", "curriculo")
        self.capa = QVBoxLayout(self)
        self.capa.setContentsMargins(14, 10, 14, 10)
        self.capa.setSpacing(6)

    def poner(self, ctx, plegada: bool) -> None:
        _limpiar(self.capa)
        ficha = ctx.ficha
        cab = QHBoxLayout()
        cab.addWidget(etiqueta("Del currículo", "etiqueta"))
        letras = list(ficha.competencias_modulo)
        n_normas = len(ctx.catalogo.normativa(ficha.sigla, "estatal", ctx.curso_escolar)) + \
            len(ctx.catalogo.normativa(ficha.sigla, "autonomico", ctx.curso_escolar))
        self.fuente = etiqueta(self._fuente(ctx), "pequeno")
        if plegada:
            cab.addWidget(etiqueta(f"<b>{len(ficha.ra)}</b> RA" if ficha.ra else "RA: pendiente"))
            cab.addLayout(self._letras(letras, 5))
            cab.addStretch(1)
            cab.addWidget(etiqueta(f"<b>{n_normas}</b> normas"))
            b = boton("Ver ›", enlace=True)
            b.clicked.connect(self.ver.emit)
            cab.addWidget(b)
            self.capa.addLayout(cab)
            return
        cab.addStretch(1)
        cab.addWidget(self.fuente)
        self.capa.addLayout(cab)
        if not ficha.ra:
            self.capa.addWidget(etiqueta("Resultados de aprendizaje: pendiente. " + "; ".join(ficha.pendientes),
                                         "aviso", envolver=True))
        for ra in ficha.ra[:8]:
            fila = QHBoxLayout()
            n = etiqueta(f"RA{ra['n']}", "ra")
            n.setFixedWidth(42)
            fila.addWidget(n)
            t = etiqueta(QFontMetrics(estilo.fuente(14)).elidedText(ra["texto"], Qt.TextElideMode.ElideRight, 320))
            t.setToolTip("<p>" + ra["texto"] + "</p><ul>" + "".join(f"<li>{c['letra']}) {c['texto']}</li>"
                                                                   for c in ra["criterios"]) + "</ul>")
            fila.addWidget(t, 1)
            self.capa.addLayout(fila)
        if len(ficha.ra) > 8:
            self.capa.addWidget(etiqueta(f"y {len(ficha.ra) - 8} RA más: «Ver»", "pequeno"))
        pie = QHBoxLayout()
        if letras:
            competencias = etiqueta("Competencias")
            competencias.setStyleSheet("font-weight:700;")
            pie.addWidget(competencias)
            pie.addLayout(self._letras(letras, 7))
        pie.addStretch(1)
        pie.addWidget(etiqueta(f"<b>{n_normas}</b> normas"))
        b = boton("Ver", pequeno=True)
        b.clicked.connect(self.ver.emit)
        pie.addWidget(b)
        self.capa.addLayout(pie)

    @staticmethod
    def _letras(letras, maximo: int) -> QHBoxLayout:
        """Las letras de competencia en cuadritos; si no caben, las primeras y «+N» (con todas en la ayuda)."""
        fila = QHBoxLayout()
        fila.setSpacing(2)
        for x in letras[:maximo]:
            letra = etiqueta(x, "letra")
            letra.setFixedSize(17, 20)
            letra.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fila.addWidget(letra)
        if len(letras) > maximo:
            mas = etiqueta(f"+{len(letras) - maximo}", "pequeno")
            mas.setToolTip(", ".join(f"{x})" for x in letras))
            fila.addWidget(mas)
        return fila

    @staticmethod
    def _fuente(ctx) -> str:
        ficha = ctx.ficha
        if not ficha.fuente_ra:
            return "Fuente: pendiente"
        n = ctx.catalogo.norma(ficha.fuente_ra)
        comprobado = str(ctx.catalogo.modulo(ficha.modulo_id)["fuente"].get("comprobado", ""))
        return f"{n.diario} · {n.cita_corta.replace('Real Decreto', 'RD')} · comprobado el {comprobado}"


class Cabecera(QWidget):
    def __init__(self):
        super().__init__()
        fila = QHBoxLayout(self)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(16)
        caja = QFrame()
        caja.setProperty("rol", "codigo")
        caja.setFixedSize(100, 100)
        cv = QVBoxLayout(caja)
        cv.setSpacing(0)
        self.codigo = QLabel()
        self.codigo.setProperty("rol", "codigo")
        self.codigo.setFont(estilo.fuente(36, QFont.Weight.Bold, estilo.TITULAR))
        self.codigo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cv.addWidget(self.codigo)
        self.ciclo_curso = QLabel()
        self.ciclo_curso.setProperty("rol", "codigo")
        self.ciclo_curso.setFont(estilo.etiqueta_fuente(13))
        self.ciclo_curso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cv.addWidget(self.ciclo_curso)
        fila.addWidget(caja, 0, Qt.AlignmentFlag.AlignTop)
        textos = QVBoxLayout()
        textos.setSpacing(6)
        self.nombre = _titulo("", 30)
        textos.addWidget(self.nombre)
        etiquetas = QHBoxLayout()
        etiquetas.setSpacing(6)
        self.tag_grado = etiqueta("", "tag-etapa")
        self.tag_curso = etiqueta("", "tag")
        self.tag_pendiente = etiqueta("pendiente", "aviso")
        for t in (self.tag_grado, self.tag_curso, self.tag_pendiente):
            etiquetas.addWidget(t)
        etiquetas.addStretch(1)
        textos.addLayout(etiquetas)
        self.datos = etiqueta("", "muted")
        textos.addWidget(self.datos)
        fila.addLayout(textos, 1)

    def poner(self, ficha, entrada) -> None:
        self.codigo.setText(ficha.codigo)
        self.ciclo_curso.setText(f"{ficha.sigla} · {ficha.curso}")
        largo = len(ficha.nombre)
        self.nombre.setFont(estilo.fuente(30 if largo <= 28 else 26 if largo <= 48 else 22, QFont.Weight.Bold,
                                          estilo.TITULAR))
        self.nombre.setText(ficha.nombre.upper())
        self.tag_grado.setText(f"{GRADOS.get(ficha.grado, ficha.grado)} · {ficha.sigla}")
        self.tag_curso.setText(f"{ficha.curso}.º curso")
        self.tag_pendiente.setVisible(bool(ficha.pendientes))
        self.tag_pendiente.setToolTip("; ".join(ficha.pendientes))
        self.datos.setText(f"Código <span style='font-family:\"{estilo.MONO}\"'>{ficha.codigo}</span> · "
                           f"{ficha.horas} h · {ficha.h_sem} h/semana")


class ColumnaFicha(QWidget):
    VACIA, FICHA = 0, 1
    pedir_heredar = pyqtSignal()
    pedir_curriculo = pyqtSignal()

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.paso = ORDEN[0]
        self.pila = QStackedLayout(self)
        self.vacio = EstadoVacio(*ELIGE_UN_MODULO, icono=estilo.icono_documento(estilo.T["muted"], 30))
        self.pila.addWidget(self.vacio)

        self.ficha = QWidget()
        v = QVBoxLayout(self.ficha)
        v.setContentsMargins(18, 16, 18, 14)
        v.setSpacing(12)
        self.cabecera = Cabecera()
        v.addWidget(self.cabecera)
        self.curriculo = CajaCurriculo()
        self.curriculo.ver.connect(self.pedir_curriculo.emit)
        v.addWidget(self.curriculo)
        self.zona_pasos = QWidget()
        capa = FlujoLayout(self.zona_pasos, 8)
        self.botones_paso = {}
        for i, paso in enumerate(ORDEN, start=1):
            b = boton(f"{i}  {CORTOS[paso]}", chip=True)
            b.clicked.connect(lambda _=False, p=paso: self.ir(p))
            capa.addWidget(b)
            self.botones_paso[paso] = b
        v.addWidget(self.zona_pasos)

        self.caja = QFrame()
        self.caja.setProperty("rol", "caja")
        cv = QVBoxLayout(self.caja)
        cv.setContentsMargins(1, 1, 1, 10)
        cv.setSpacing(0)
        self.banda = QFrame()
        self.banda.setProperty("rol", "banda")
        bf = QHBoxLayout(self.banda)
        bf.setContentsMargins(18, 10, 14, 10)
        self.texto_banda = etiqueta("", "banda", envolver=True)
        bf.addWidget(self.texto_banda, 1)
        self.boton_confirmar = boton("Confirmar bloque", primario=True)
        self.boton_confirmar.clicked.connect(self.confirmar)
        bf.addWidget(self.boton_confirmar)
        cv.addWidget(self.banda)
        self.pila_bloques = QStackedWidget()
        self.sin_programacion = EstadoVacio(
            f"Aún no hay programación para {ctx.curso_escolar}",
            "Empieza en blanco o hereda la del curso pasado: la tuya o la de otro profesor.")
        self.boton_empezar = self.sin_programacion.con_boton("Empezar en blanco", self.empezar)
        self.boton_heredar = self.sin_programacion.con_boton("Nueva a partir de…", self.pedir_heredar.emit,
                                                             primario=True)
        self.pila_bloques.addWidget(self.sin_programacion)
        self.bloques = {}
        for paso in ORDEN:
            b = CLASES[paso](ctx)
            self.bloques[paso] = b
            self.pila_bloques.addWidget(b)
        cv.addWidget(self.pila_bloques, 1)
        nav = QHBoxLayout()
        nav.setContentsMargins(18, 4, 18, 0)
        nav.addStretch(1)
        self.anterior = boton("‹ Anterior")
        self.anterior.clicked.connect(lambda: self.mover(-1))
        self.siguiente = boton("Siguiente ›")
        self.siguiente.clicked.connect(lambda: self.mover(1))
        nav.addWidget(self.anterior)
        nav.addWidget(self.siguiente)
        self.nav = QWidget()
        self.nav.setLayout(nav)
        cv.addWidget(self.nav)
        self.caja.setMinimumHeight(340)
        v.addWidget(self.caja, 1)
        self.pila.addWidget(desplazable(self.ficha))
        self.pila.setCurrentIndex(self.VACIA)

        ctx.modulo_elegido.connect(self._modulo)
        ctx.programacion_abierta.connect(self._programacion)
        ctx.programacion_cambiada.connect(self._cambiada)

    def _modulo(self, entrada) -> None:
        if entrada is None:
            self.pila.setCurrentIndex(self.VACIA)
            return
        self.cabecera.poner(self.ctx.ficha, entrada)
        self.pila.setCurrentIndex(self.FICHA)

    def _programacion(self, prog) -> None:
        if self.ctx.ficha is None:
            return
        self.curriculo.poner(self.ctx, plegada=prog is not None)
        self.zona_pasos.setVisible(prog is not None)
        self.nav.setVisible(prog is not None)
        if prog is None:
            self.banda.hide()
            titulo, texto = SIN_PROGRAMACION
            self.sin_programacion.poner(titulo.format(curso=self.ctx.curso_escolar), texto)
            self.pila_bloques.setCurrentWidget(self.sin_programacion)
            return
        for b in self.bloques.values():
            b.cargar()
        orden = almacen.pasos(prog)
        heredados = [p for p in orden if almacen.estado_paso(prog, p) == "heredado"]
        self.ir(heredados[0] if heredados else orden[0])

    def _cambiada(self) -> None:
        if self.ctx.prog is None:
            return
        for b in self.bloques.values():
            b.refrescar()
        self._pintar()

    def ir(self, paso: str) -> None:
        if self.ctx.prog is None:
            return
        self.paso = paso
        self.pila_bloques.setCurrentWidget(self.bloques[paso])
        self._pintar()

    def mover(self, delta: int) -> None:
        orden = almacen.pasos(self.ctx.prog)
        i = max(0, min(len(orden) - 1, orden.index(self.paso) + delta))
        self.ir(orden[i])

    def _pintar(self) -> None:
        prog = self.ctx.prog
        orden = almacen.pasos(prog)
        for paso, b in self.botones_paso.items():
            b.setVisible(paso in orden)
            if paso not in orden:
                continue
            e = almacen.estado_paso(prog, paso)
            estado = "actual" if paso == self.paso else e
            i = orden.index(paso) + 1
            b.setText(f"✓  {CORTOS[paso]}" if e == "confirmado" and paso != self.paso else f"{i}  {CORTOS[paso]}")
            b.setProperty("paso", estado)
            refrescar_estilo(b)
        heredado = almacen.estado_paso(prog, self.paso) == "heredado"
        self.banda.setVisible(heredado)
        if heredado:
            origen = prog.get("heredada_de") or {}
            if origen.get("profesor"):
                texto = (f"Heredado de <b>{origen['profesor']}</b> ({origen.get('curso_escolar', '')}) · revisa y "
                         "confirma")
            elif origen:
                texto = f"Heredado de «{origen.get('archivo', 'otra programación')}» · revisa y confirma"
            elif self.paso == "ra_competencias":
                texto = ("Propuesta de la app (hecha con IA, no es un dato oficial): las competencias de cada RA · "
                         "revísalas, cámbialas si hace falta y confirma")
            elif self.paso == "unidades" and self.ctx.ficha.es_ambito:
                texto = ("Propuesta de la app: una unidad por bloque de saberes básicos del ámbito · revisa títulos, "
                         "horas y trimestres, asigna cada unidad a su parte, añade los elementos de evaluación y "
                         "confirma")
            elif self.paso == "unidades":
                texto = ("Propuesta de la app: una unidad por bloque de contenidos básicos del módulo · revisa "
                         "títulos, horas y trimestres, añade los elementos de evaluación y confirma")
            else:
                texto = "Por revisar · comprueba este bloque y confírmalo"
            self.texto_banda.setText(texto)
        self.anterior.setEnabled(self.paso != orden[0])
        self.siguiente.setEnabled(self.paso != orden[-1])

    def confirmar(self) -> None:
        self.ctx.confirmar(self.paso)

    def empezar(self) -> None:
        self.ctx.empezar()


# ---------------------------------------------------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------------------------------------------------
class Cifra(QFrame):
    def __init__(self):
        super().__init__()
        self.setProperty("rol", "dato")
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 6, 10, 8)
        v.setSpacing(0)
        self.valor = QLabel()
        self.valor.setFont(estilo.fuente(32, QFont.Weight.Bold, estilo.TITULAR))
        v.addWidget(self.valor)
        self.texto = etiqueta("", "pequeno")
        v.addWidget(self.texto)

    def poner(self, valor: str, texto: str) -> None:
        self.valor.setText(valor)
        self.texto.setText(texto)


class FilaAviso(QFrame):
    def __init__(self, texto: str, gravedad: str, ir=None):
        super().__init__()
        self.setProperty("rol", "aviso-roja" if gravedad == validacion.ROJA else "aviso-ambar")
        fila = QHBoxLayout(self)
        fila.setContentsMargins(10, 6, 6, 6)
        self.texto = etiqueta(texto, "rojo" if gravedad == validacion.ROJA else "aviso-texto", envolver=True)
        fila.addWidget(self.texto, 1)
        self.ir = None
        if ir is not None:
            self.ir = boton("Ir ›", enlace=True)
            self.ir.clicked.connect(ir)
            fila.addWidget(self.ir, 0, Qt.AlignmentFlag.AlignTop)


def agrupar(avisos: list, heredados_pasos: int | None = None) -> list[tuple[str, str, str]]:
    """(id, gravedad, texto) para la columna «Estado»: los heredados juntos («3 bloques heredados sin confirmar»), las
    rojas antes que las ámbar."""
    out = []
    heredados = [a for a in avisos if a.id == "V-06"]
    if heredados:
        n = heredados_pasos or len(heredados)
        out.append(("V-06", validacion.ROJA, f"{n} {'bloque heredado' if n == 1 else 'bloques heredados'} sin "
                                             "confirmar"))
    out += [(a.id, a.gravedad, a.mensaje) for a in avisos if a.id != "V-06"]
    return sorted(out, key=lambda x: x[1] != validacion.ROJA)


class ColumnaEstado(QWidget):
    MAX_AVISOS = 3
    pedir_vista_previa = pyqtSignal()
    pedir_exportar = pyqtSignal()
    pedir_paso = pyqtSignal(str)
    pedir_cambios = pyqtSignal()
    pedir_programaciones = pyqtSignal()
    pedir_abrir = pyqtSignal(object)

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setFixedWidth(340)
        self.pdf_previo: Path | None = None
        self.paginas_previo = 0
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 14)
        v.setSpacing(10)
        self.pila = QStackedWidget()
        v.addWidget(self.pila, 1)

        # Sin módulo: programaciones recientes
        recientes = QWidget()
        rv = QVBoxLayout(recientes)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(8)
        self.titulo = etiqueta("Programaciones recientes", "etiqueta")
        rv.addWidget(self.titulo)
        self.capa_recientes = QVBoxLayout()
        self.capa_recientes.setSpacing(4)
        rv.addLayout(self.capa_recientes)
        self.recientes = etiqueta("Aún no hay programaciones en este equipo.", "muted", envolver=True)
        rv.addWidget(self.recientes)
        self.ver_todas = boton("Ver todas…")
        self.ver_todas.clicked.connect(self.pedir_programaciones.emit)
        rv.addWidget(self.ver_todas, 0, Qt.AlignmentFlag.AlignLeft)
        rv.addStretch(1)
        self.pila.addWidget(recientes)

        # Con módulo: estado, avisos y vista previa
        estado = QWidget()
        zona = desplazable(estado)
        ev = QVBoxLayout(estado)
        ev.setContentsMargins(0, 0, 4, 0)
        ev.setSpacing(8)
        ev.addWidget(etiqueta("Estado", "etiqueta"))
        self.filas_bloque = {}
        self.widgets_bloque = {}
        for paso in ORDEN:
            fila = QHBoxLayout()
            icono = QLabel()
            icono.setFixedWidth(22)
            fila.addWidget(icono)
            nombre = boton(almacen.PASOS[paso][0], enlace=True)
            nombre.setStyleSheet("font-weight:400;text-align:left;")
            nombre.clicked.connect(lambda _=False, p=paso: self.pedir_paso.emit(p))
            fila.addWidget(nombre, 1)
            estado_txt = etiqueta("", "pequeno")
            fila.addWidget(estado_txt)
            ev.addLayout(fila)
            self.filas_bloque[paso] = (icono, estado_txt)
            self.widgets_bloque[paso] = (icono, nombre, estado_txt)
        fila = QHBoxLayout()
        self.progreso = QProgressBar()
        self.progreso.setRange(0, len(ORDEN))
        self.progreso.setTextVisible(False)
        self.progreso.setFixedHeight(12)
        fila.addWidget(self.progreso, 1)
        self.texto_progreso = etiqueta("", "pequeno")
        fila.addWidget(self.texto_progreso)
        ev.addLayout(fila)
        self.cifras = QWidget()
        cf = QHBoxLayout(self.cifras)
        cf.setContentsMargins(0, 0, 0, 0)
        cf.setSpacing(6)
        self.cifra_centro, self.cifra_empresa, self.cifra_total = Cifra(), Cifra(), Cifra()
        for c in (self.cifra_centro, self.cifra_empresa, self.cifra_total):
            cf.addWidget(c)
        ev.addWidget(self.cifras)
        self.capa_avisos = QVBoxLayout()
        self.capa_avisos.setSpacing(5)
        ev.addLayout(self.capa_avisos)
        self.todo_bien = etiqueta("", "ok", envolver=True)
        ev.addWidget(self.todo_bien)
        ev.addWidget(etiqueta("Vista previa", "etiqueta"))
        fila = QHBoxLayout()
        fila.setSpacing(12)
        self.miniatura = QLabel("Sin\ndatos")
        self.miniatura.setProperty("rol", "miniatura")
        self.miniatura.setFixedSize(106, 150)
        self.miniatura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fila.addWidget(self.miniatura, 0, Qt.AlignmentFlag.AlignTop)
        lado = QVBoxLayout()
        self.texto_previa = etiqueta("", "muted", envolver=True)
        lado.addWidget(self.texto_previa)
        self.boton_previa = boton(f"Vista previa  {atajo('P')}")
        self.boton_previa.clicked.connect(self.pedir_vista_previa.emit)
        lado.addWidget(self.boton_previa, 0, Qt.AlignmentFlag.AlignLeft)
        lado.addStretch(1)
        fila.addLayout(lado, 1)
        ev.addLayout(fila)
        ev.addStretch(1)
        self.pila.addWidget(zona)

        v.addWidget(etiqueta("Exportar", "etiqueta"))
        chips = QWidget()
        fila = FlujoLayout(chips, 6)
        self.chip_word = boton("Word", chip=True)
        self.chip_pdf = boton("PDF", chip=True)
        self.chip_excel = boton("Excel de RA", chip=True)
        self.chip_excel.setToolTip("Para importar los RA y sus criterios en el cuaderno de Educamos")
        self.chips_formato = {"docx": self.chip_word, "pdf": self.chip_pdf, "xlsx": self.chip_excel}
        for f, b in self.chips_formato.items():
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, x=f: self._formato(x))
            fila.addWidget(b)
        v.addWidget(chips)
        self.boton_exportar = boton(f"Exportar  {atajo('E')}", primario=True, grande=True)
        self.boton_exportar.setEnabled(False)
        self.boton_exportar.clicked.connect(self.pedir_exportar.emit)
        v.addWidget(self.boton_exportar)
        self.resumen = etiqueta("Elige un módulo para empezar", "muted")
        self.resumen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.resumen.setWordWrap(True)
        self.resumen.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        v.addWidget(self.resumen)

        ctx.modulo_elegido.connect(lambda _e: self.actualizar())
        ctx.programacion_abierta.connect(self._abierta)
        ctx.programacion_cambiada.connect(self.actualizar)
        ctx.programaciones_cambiadas.connect(self._pintar_recientes)
        self._pintar_recientes()
        self.recargar()

    # Ajustes
    def recargar(self) -> None:
        formatos = self.ctx.gestor.valores.formatos
        for f, b in self.chips_formato.items():
            b.setChecked(f in formatos)
        self.actualizar()

    def _formato(self, f: str) -> None:
        formatos = [x for x, b in self.chips_formato.items() if b.isChecked()]
        if not formatos:  # al menos uno
            self.chips_formato[f].setChecked(True)
            return
        self.ctx.gestor.poner(formatos=formatos)
        self.actualizar()

    # Recientes
    def _pintar_recientes(self) -> None:
        _limpiar(self.capa_recientes)
        filas = self.ctx.recientes()
        self.recientes.setVisible(not filas)
        self.ver_todas.setVisible(bool(filas))
        for f in filas:
            b = boton("", enlace=True)
            b.setStyleSheet("text-align:left;font-weight:400;")
            p = f["prog"]
            nombre = f["programacion"].split(" - ", 2)[-1]
            b.setText(f"{nombre}\n{p['ciclo']} {p['curso']} · {p['modulo']} · {f['estado']}")
            b.setIcon(QIcon(estilo.icono_documento(estilo.T["muted"], 20)))
            b.clicked.connect(lambda _=False, prog=p: self.pedir_abrir.emit(prog))
            self.capa_recientes.addWidget(b)

    # Programación
    def _abierta(self, _prog) -> None:
        self.pdf_previo = None
        self.miniatura.setPixmap(QPixmap())
        self.miniatura.setText("Sin\ndatos")
        self.actualizar()

    def actualizar(self) -> None:
        ctx = self.ctx
        if ctx.modulo is None:
            self.pila.setCurrentIndex(0)
            self.boton_exportar.setEnabled(False)
            self.resumen.setText("Elige un módulo para empezar")
            return
        self.pila.setCurrentIndex(1)
        prog = ctx.prog
        # el Excel de RA no existe para los ámbitos de GB (competencias específicas, no RA)
        con_excel = ctx.ficha is not None and excel_ra.aplica(ctx.ficha)
        self.chip_excel.setEnabled(con_excel)
        self.chip_excel.setToolTip("Para importar los RA y sus criterios en el cuaderno de Educamos" if con_excel else
                                   "Los ámbitos no tienen RA: no hay Excel de RA")
        orden = almacen.pasos(prog)
        for paso, ws in self.widgets_bloque.items():
            for w in ws:
                w.setVisible(paso in orden)
        for paso, (icono, texto) in self.filas_bloque.items():
            e = almacen.estado_paso(prog, paso) if prog else "vacio"
            icono.setPixmap(estilo.icono_estado(e, 16))
            t, rol = ESTADO_BLOQUE[e]
            texto.setText(t)
            texto.setProperty("rol", rol)
            refrescar_estilo(texto)
        n = almacen.confirmados(prog) if prog else 0
        self.progreso.setRange(0, len(orden))
        self.progreso.setValue(n)
        self.texto_progreso.setText(f"{n} de {len(orden)}")
        _limpiar(self.capa_avisos)
        self.cifras.setVisible(prog is not None)
        self.boton_previa.setEnabled(prog is not None)
        if prog is None:
            self.todo_bien.hide()
            self.texto_previa.setText("La vista previa estará disponible cuando empieces la programación.")
            self.boton_exportar.setEnabled(False)
            self.resumen.setText("Empieza la programación para poder exportar")
            return
        H = ctx.ficha.horas
        h_c, h_e = calculos.horas_centro(prog), calculos.horas_empresa(prog)
        pe = calculos.porcentaje_empresa(prog, H)
        self.cifra_centro.poner(f"{h_c} h", f"centro · {100 - pe} %")
        self.cifra_empresa.poner(f"{h_e} h", f"empresa · {pe} %")
        self.cifra_total.poner(f"{H} h", "del módulo")
        avisos = ctx.avisos()
        self.avisos = avisos
        grupos = agrupar(avisos, sum(1 for p in ORDEN if almacen.estado_paso(prog, p) == "heredado"))
        for ident, gravedad, texto in grupos[:self.MAX_AVISOS]:
            self.capa_avisos.addWidget(FilaAviso(texto, gravedad, self._destino(ident)))
        if len(grupos) > self.MAX_AVISOS:
            self.capa_avisos.addWidget(etiqueta(f"y {len(grupos) - self.MAX_AVISOS} avisos más", "pequeno"))
        bloquea = validacion.bloquean(avisos)
        self.todo_bien.setVisible(not bloquea)
        self.todo_bien.setText("✓ Todo cuadra: lista para exportar" if not grupos
                               else "✓ Sin errores: se puede exportar")
        if self.pdf_previo is None:
            self.texto_previa.setText("El documento con la plantilla del centro y la marca «BORRADOR».")
        self.boton_exportar.setEnabled(not bloquea)
        if bloquea:
            ids = {a.id for a in avisos if a.gravedad == validacion.ROJA}
            self.resumen.setText("Confirma los bloques heredados para exportar" if ids == {"V-06"}
                                 else "Corrige los avisos en rojo para exportar")
        else:
            self.resumen.setText(self.texto_destino())

    def texto_destino(self) -> str:
        valor = self.ctx.gestor.carpeta_entrega(self.ctx.prog["curso_escolar"]) if self.ctx.prog else ""
        estado = estado_carpeta(valor)
        if estado == "local":
            return f"Se guardará en: {Path(valor).name or valor}"
        if estado == "enlace":
            return "Se guardará en este equipo y se abrirá la carpeta de Teams"
        return "Al exportar, elegirás dónde se guarda"

    def _destino(self, ident: str):
        if ident == "V-06":
            return lambda: self.pedir_paso.emit(next(p for p in ORDEN if almacen.estado_paso(self.ctx.prog, p)
                                                     == "heredado"))
        if ident == "V-08":
            return self.pedir_cambios.emit
        if ident in IR_A:
            return lambda: self.pedir_paso.emit(IR_A[ident])
        return None

    def poner_previo(self, pdf: Path, paginas: int, imagen: QPixmap | None) -> None:
        self.pdf_previo = pdf
        self.paginas_previo = paginas
        if imagen is not None and not imagen.isNull():
            self.miniatura.setPixmap(imagen.scaled(self.miniatura.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation))
        resto = paginas - 1
        cuantas = "Solo la portada" if resto < 1 else f"Portada y {resto} {'página' if resto == 1 else 'páginas'}"
        self.texto_previa.setText(f"{cuantas}. Con la marca «BORRADOR».")
