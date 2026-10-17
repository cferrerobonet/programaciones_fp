"""Ventana «Enviar por correo» (DESIGN.md, «Ventanas modales»; ADR-014).

Destinatarios (chips con los habituales de Ajustes → Correo y un campo para otros), «Word» y «PDF» (por defecto, los de
Ajustes → Exportación), los adjuntos con su tamaño o «se exporta antes», el total con el aviso si pasa de 20 MB, el
asunto y el mensaje ya escritos con la plantilla de Ajustes, y «Cancelar» / «Crear correo». El correo lo abre
`gestion.Gestion.enviar` en el programa de correo del profesor: la app no envía nada.
"""

from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget

from .. import correo
from . import estilo
from .componentes import FlujoLayout, boton, desplazable, etiqueta, refrescar_estilo
from .gestion import chips_formato

ESTADOS = {
    "listo": ("pequeno", ""),
    "cambiada": ("aviso-texto", "exportado antes de tus últimos cambios"),
    "exportar": ("pequeno", "se exporta antes de crear el correo"),
    "bloqueada": ("rojo", "no se puede adjuntar: tiene avisos en rojo"),
}


class DialogoCorreo(QDialog):
    def __init__(self, gestion, progs: list[dict], padre=None):
        super().__init__(padre)
        self.gestion = gestion
        self.ctx = gestion.ctx
        self.progs = progs
        self.plan = []
        self._escrito = {"asunto": False, "cuerpo": False}
        v = self.ctx.gestor.valores
        self.setWindowTitle("Enviar por correo")
        self.resize(720, 680)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(26, 22, 26, 20)
        capa.setSpacing(10)
        titulo = QLabel("Enviar por correo")
        titulo.setFont(estilo.fuente(24, QFont.Weight.Bold, estilo.TITULAR))
        capa.addWidget(titulo)
        capa.addWidget(etiqueta(correo.que_se_abre(v.cliente_correo), "muted", envolver=True))

        capa.addWidget(etiqueta("Para", "etiqueta"))
        zona = QWidget()
        flujo = FlujoLayout(zona, 6)
        self.chips_para = {}
        for d in v.destinatarios:
            b = boton(d, chip=True)
            b.setCheckable(True)
            b.setAccessibleName(f"Destinatario {d}")
            b.clicked.connect(self._pintar_para)
            flujo.addWidget(b)
            self.chips_para[d] = b
        if self.chips_para:
            capa.addWidget(zona)
        else:
            capa.addWidget(etiqueta("Sin destinatarios habituales: añádelos en Ajustes → Correo o escríbelos aquí.",
                                    "pequeno", envolver=True))
        self.otros = QLineEdit()
        self.otros.setPlaceholderText("Otros destinatarios, separados por comas")
        self.otros.setAccessibleName("Otros destinatarios")
        self.otros.textChanged.connect(self._pintar_para)
        capa.addWidget(self.otros)
        self.estado_para = etiqueta("", "pequeno", envolver=True)
        capa.addWidget(self.estado_para)

        capa.addWidget(etiqueta("Adjuntos", "etiqueta"))
        zona_formatos, self.chips = chips_formato(v.formatos, self.refrescar)
        capa.addWidget(zona_formatos)
        contenido = QWidget()
        self.capa_adjuntos = QVBoxLayout(contenido)
        self.capa_adjuntos.setContentsMargins(0, 0, 0, 0)
        self.capa_adjuntos.setSpacing(3)
        lista = desplazable(contenido)
        lista.setMinimumHeight(120)
        capa.addWidget(lista, 1)
        self.total = etiqueta("", "pequeno", envolver=True)
        capa.addWidget(self.total)
        self.reexportar = QCheckBox("Exportar de nuevo las que han cambiado después de exportarlas (se sustituyen "
                                    "esos archivos)")
        self.reexportar.toggled.connect(self.refrescar)
        capa.addWidget(self.reexportar)

        capa.addWidget(etiqueta("Asunto", "etiqueta"))
        self.asunto = QLineEdit()
        self.asunto.setAccessibleName("Asunto")
        self.asunto.textEdited.connect(lambda _t: self._escrito.__setitem__("asunto", True))
        capa.addWidget(self.asunto)
        capa.addWidget(etiqueta("Mensaje", "etiqueta"))
        self.cuerpo = QPlainTextEdit()
        self.cuerpo.setAccessibleName("Mensaje")
        self.cuerpo.setFixedHeight(130)
        capa.addWidget(self.cuerpo)

        botones = QHBoxLayout()
        botones.addStretch(1)
        cancelar = boton("Cancelar")
        cancelar.clicked.connect(self.reject)
        self.crear = boton("Crear correo", primario=True)
        self.crear.clicked.connect(self.accept)
        botones.addWidget(cancelar)
        botones.addWidget(self.crear)
        capa.addLayout(botones)
        self.refrescar()
        self.cuerpo.textChanged.connect(self._cuerpo_escrito)

    def _cuerpo_escrito(self) -> None:
        if self.cuerpo.hasFocus():
            self._escrito["cuerpo"] = True

    def formatos(self) -> list[str]:
        return [f for f, b in self.chips.items() if b.isChecked()]

    def para(self) -> list[str]:
        otros, _malos = correo.separar(self.otros.text())
        marcados = [d for d, b in self.chips_para.items() if b.isChecked()]
        return list(dict.fromkeys(marcados + otros))

    def _pintar_para(self) -> None:
        _validos, malos = correo.separar(self.otros.text())
        if malos:
            self.estado_para.setProperty("rol", "aviso-texto")
            self.estado_para.setText(f"No parece un correo: {', '.join(malos)}.")
        elif not self.para():
            self.estado_para.setProperty("rol", "pequeno")
            self.estado_para.setText("Sin destinatarios: podrás escribirlos en el correo.")
        else:
            self.estado_para.setProperty("rol", "pequeno")
            self.estado_para.setText(f"Para: {', '.join(self.para())}")
        refrescar_estilo(self.estado_para)
        self._activar()

    def refrescar(self) -> None:
        """Adjuntos, total y, si el profesor no los ha cambiado, asunto y mensaje."""
        self.plan = self.gestion.adjuntos(self.progs, self.formatos(), self.reexportar.isChecked())
        while self.capa_adjuntos.count():
            w = self.capa_adjuntos.takeAt(0).widget()
            if w:
                w.hide()
                w.deleteLater()
        self.filas: list[QLabel] = []
        conocidos = 0
        for a in self.plan:
            rol, texto = ESTADOS[a.estado]
            if a.estado in ("listo", "cambiada"):
                tam = correo.texto_tamano(a.ruta.stat().st_size)
                conocidos += a.ruta.stat().st_size
                texto = f"{tam} · {texto}" if texto else tam
            e = etiqueta(f"{a.ruta.name} · {texto}", rol, envolver=True)
            e.setStyleSheet("font-size:13px;font-weight:400;")  # el color, del rol; el tamaño, igual en todas
            e.setToolTip(str(a.ruta))
            self.filas.append(e)
            self.capa_adjuntos.addWidget(e)
        self.capa_adjuntos.addStretch(1)
        cambiadas = any(a.estado == "cambiada" for a in self.plan)
        self.reexportar.setVisible(cambiadas or self.reexportar.isChecked())
        n = sum(1 for a in self.plan if a.se_adjunta)
        por_exportar = sum(1 for a in self.plan if a.estado == "exportar")
        partes = [f"{n} {'adjunto' if n == 1 else 'adjuntos'}", correo.texto_tamano(conocidos)]
        if por_exportar:
            partes.append(f"más {por_exportar} que se exporta{'n' if por_exportar > 1 else ''} antes")
        if correo.supera_limite(conocidos):
            self.total.setProperty("rol", "aviso-texto")
            partes.append(f"pasa de {correo.LIMITE_MB} MB: puede que el correo no salga; envía menos o solo el PDF")
        else:
            self.total.setProperty("rol", "pequeno")
        self.total.setText(" · ".join(partes))
        refrescar_estilo(self.total)
        asunto, cuerpo = self.gestion.borrador(self.progs, self.plan)
        if not self._escrito["asunto"]:
            self.asunto.setText(asunto)
        if not self._escrito["cuerpo"]:
            self.cuerpo.blockSignals(True)
            self.cuerpo.setPlainText(cuerpo)
            self.cuerpo.blockSignals(False)
        self._pintar_para()

    def supera_limite(self) -> bool:
        return correo.supera_limite(sum(a.ruta.stat().st_size for a in self.plan if a.estado in ("listo", "cambiada")))

    def _activar(self) -> None:
        _validos, malos = correo.separar(self.otros.text())
        self.crear.setEnabled(any(a.se_adjunta for a in self.plan) and not malos)
