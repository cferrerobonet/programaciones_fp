"""Flujo completo de la interfaz con pytest-qt, sin pantalla y con datos ficticios: elegir el módulo, rellenar los cinco
bloques, ver los avisos, vista previa, exportar Word y PDF, volver a abrirlo, heredar, cambios de currículo, listado y
primer arranque. Word no se toca nunca: el PDF se simula (salvo una prueba con LibreOffice, si está)."""
import copy
import shutil
import zipfile
from io import BytesIO

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QMessageBox

from programaciones import calculos, documento, incrustar, pdf, validacion
from programaciones.ui import estilo
from programaciones.ui.columnas import FilaAviso, agrupar
from programaciones.ui.modales import DialogoModificadoWord

pytestmark = pytest.mark.ui
NOMBRE = "SEA 2 - 0517 - Procesos en instalaciones de infraestructuras comunes de telecomunicaciones"


@pytest.fixture
def ctx(contexto, curso):
    contexto.datos_curso = curso  # curso escolar ficticio: con él, la definitiva se puede exportar
    contexto.gestor.poner(nombre_profesor="Profesora Ficticia Uno", programa_pdf="libreoffice")
    return contexto


@pytest.fixture
def ventana(qtbot, ctx):
    from programaciones.ui.ventana import VentanaPrincipal

    v = VentanaPrincipal(ctx)
    qtbot.addWidget(v)
    v.show()
    return v


@pytest.fixture
def modales(monkeypatch):
    """`exec()` de los diálogos no bloquea: guarda el diálogo y vuelve al momento («Cancelar»)."""
    abiertos = []

    def exec_(self):
        abiertos.append(self)
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(QDialog, "exec", exec_)
    return abiertos


def elegir_0517(qtbot, ventana):
    qtbot.keyClicks(ventana.modulos.buscador, "0517")
    return ventana.ctx.modulo


def rellenar(qtbot, ventana, ctx):
    """Los cinco bloques, como los rellenaría el profesor (todo inventado). 0517: 166 h, RA1 a RA6."""
    ficha = ventana.ficha
    ficha.ir("profesorado")
    b = ficha.bloques["profesorado"]
    qtbot.keyClicks(b.nuevo, "Profesor Ficticio Dos")
    qtbot.keyClick(b.nuevo, Qt.Key.Key_Return)

    ficha.ir("unidades")
    u = ficha.bloques["unidades"]
    while ctx.prog["unidades"]:          # fuera la propuesta de la app: el profesor pone las suyas
        u.quitar("unidades", 0)
    u.ver(1)
    u.anadir_elemento()
    u.anadir_elemento()
    for r, (nombre, tipo, ras) in enumerate((("EXAMEN FICTICIO", "E", [1, 2]), ("PRÁCTICA FICTICIA", "P", [3, 4, 6]))):
        u.elementos.item(r, u.E_NOMBRE).setText(nombre)
        u.elementos.item(r, u.E_TIPO).setData(Qt.ItemDataRole.UserRole, tipo)
        u.elegir_ra(r, ras)
    u.ver(0)
    for _ in range(3):
        u.anadir_unidad()
    ids = [e["id"] for e in ctx.prog["elementos"]]
    for r, (titulo, horas, trim, el) in enumerate((("UD01. Unidad ficticia", 30, 1, ids[0]),
                                                    ("UD02. Otra unidad ficticia", 20, 2, ids[0]),
                                                    ("Práctica 1: Montaje ficticio", 53, [2, 3], ids[1]))):
        u.unidades.item(r, u.U_TITULO).setText(titulo)
        u.unidades.item(r, u.U_HORAS).setText(str(horas))
        u.unidades.item(r, u.U_TRIM).setData(Qt.ItemDataRole.UserRole, trim)
        u.unidades.item(r, u.U_ELEM).setData(Qt.ItemDataRole.UserRole, el)

    ficha.ir("empresa")
    e = ficha.bloques["empresa"]
    for n, h in ((2, 12), (3, 13), (4, 13), (5, 13), (6, 12)):
        e.poner_modalidad(n, "Empresa" if n == 5 else "Mixto")
        e.poner_empresa(n, h)

    ficha.ir("ra_competencias")
    c = ficha.bloques["ra_competencias"]
    for n in range(1, 7):
        c.marcar(n, c.letras[n % len(c.letras)])

    ficha.ir("metodologia")
    m = ficha.bloques["metodologia"]
    m.chips_recursos.botones["Teams"].click()
    m.metodologia.setPlainText("Párrafo ficticio de metodología con el **cuaderno ficticio**.\n- Viñeta ficticia")


def test_elegir_el_modulo_tecleando_el_codigo_y_con_filtros(qtbot, ventana, ctx):
    col = ventana.modulos
    col.filtrar_grado("GM")
    assert all(m.grado == "GM" for m in col.visibles())
    assert not col.chips_ciclo["SEA"].isVisible() and col.limpiar.isEnabled()
    col.limpiar_filtros()
    col.filtrar_ciclo("SEA")
    col.curso.setCurrentIndex(2)
    assert {(m.sigla, m.curso) for m in col.visibles()} == {("SEA", 2)}
    assert col.cuenta.text().endswith("· SEA")
    col.limpiar_filtros()
    assert len(col.visibles()) == len(ctx.modulos)
    m = elegir_0517(qtbot, ventana)
    assert (m.sigla, m.curso, m.codigo) == ("SEA", 2, "0517")
    assert ventana.ficha.pila.currentIndex() == ventana.ficha.FICHA
    assert ventana.ficha.cabecera.codigo.text() == "0517"
    assert ventana.ficha.pila_bloques.currentWidget() is ventana.ficha.sin_programacion
    assert ventana.estado.resumen.text() == "Empieza la programación para poder exportar"
    assert not ventana.estado.boton_exportar.isEnabled()


def test_lo_oficial_es_de_solo_lectura_y_con_su_fuente(qtbot, ventana, ctx, modales):
    from programaciones.ui.modales import html_curriculo

    elegir_0517(qtbot, ventana)
    assert "BOE" in ventana.ficha.curriculo.fuente.text() and "comprobado el" in ventana.ficha.curriculo.fuente.text()
    ventana.ver_curriculo()
    assert modales[-1].windowTitle() == "Del currículo" and modales[-1].texto.isReadOnly()
    detalle = html_curriculo(ctx)
    assert all(f"RA{n}." in detalle for n in range(1, 7)) and "boe.es" in detalle


def test_flujo_completo_rellenar_validar_exportar_y_volver_a_abrir(qtbot, ventana, ctx, tmp_path, modales,
                                                                   pdf_falso, monkeypatch):
    carpeta = tmp_path / "Teams 2026-2027"
    carpeta.mkdir()
    ctx.gestor.poner_carpeta_entrega(ctx.curso_escolar, str(carpeta))
    elegir_0517(qtbot, ventana)
    qtbot.mouseClick(ventana.ficha.boton_empezar, Qt.MouseButton.LeftButton)
    prog = ctx.prog
    assert prog["profesorado"] == ["Profesora Ficticia Uno"], "el nombre sale de Ajustes"
    # Apartado 4 propuesto desde los contenidos básicos de 0517 (CarlosFB, 2026-10-17): una unidad por bloque, las
    # 166 h repartidas, por trimestres y sin elementos de evaluación; se abre ese paso, «por revisar»
    bloques = ctx.ficha.contenidos
    assert [u["titulo"] for u in prog["unidades"]] == [f"UD{k:02d}. {b['titulo']}" for k, b in enumerate(bloques, 1)]
    assert sum(u["horas"] for u in prog["unidades"]) == 166 and {u["elemento"] for u in prog["unidades"]} == {""}
    trimestres = [u["trimestre"] for u in prog["unidades"]]
    assert trimestres == sorted(trimestres) and trimestres[0] == 1 and trimestres[-1] == 3
    assert prog["bloques"]["unidades"] == "heredado"
    assert ventana.ficha.pila_bloques.currentWidget() is ventana.ficha.bloques["unidades"]
    assert "contenidos básicos" in ventana.ficha.texto_banda.text()
    assert not ventana.estado.boton_exportar.isEnabled()

    rellenar(qtbot, ventana, ctx)
    assert prog["profesorado"] == ["Profesora Ficticia Uno", "Profesor Ficticio Dos"]
    assert [u["horas"] for u in prog["unidades"]] == [30, 20, 53] and prog["unidades"][2]["trimestre"] == [2, 3]
    assert prog["empresa"] == {"2": 12, "3": 13, "4": 13, "5": 13, "6": 12}
    assert prog["recursos"] == [{"texto": "Teams", "nivel": 0}]
    assert prog["metodologia"][1] == {"texto": "Viñeta ficticia", "nivel": 0}
    assert set(prog["bloques"].values()) >= {"confirmado"}

    # Lo calculado, en gris: pesos, reparto por RA, modalidad y cifras del estado
    u = ventana.ficha.bloques["unidades"]
    assert u.elementos.item(0, u.E_PESO).text() == "30,1 %"   # 50 / 166
    e = ventana.ficha.bloques["empresa"]
    assert e.tabla.item(2, e.C_MODALIDAD).text() == "Mixto" and e.tabla.item(4, e.C_MODALIDAD).text() == "Empresa"
    assert "reparto 17,67" in e.tabla.item(2, e.C_CENTRO).toolTip()
    assert e.tabla.item(4, e.C_CENTRO).text() == "—" and e.tabla.item(0, e.C_EMPRESA).text() == "—"
    assert (e.tabla.item(2, e.C_PCT_CENTRO).text(), e.tabla.item(2, e.C_PCT_EMPRESA).text()) == ("57 %", "43 %")   # 17 + 13
    assert e.tabla.item(4, e.C_PCT_CENTRO).text() == "—"
    assert ventana.estado.cifra_centro.valor.text() == "103 h" and ventana.estado.cifra_empresa.texto.text() == \
        "empresa · 38 %"
    assert ventana.estado.texto_progreso.text() == "5 de 5"
    avisos = ctx.avisos()
    assert not validacion.bloquean(avisos), avisos
    assert ventana.estado.boton_exportar.isEnabled() and ventana.accion_exportar.isEnabled()
    assert ventana.estado.resumen.text() == f"Se guardará en: {carpeta.name}"

    # Horas de centro: ajuste dentro de los límites y fuera de ellos (V-04)
    e.poner_centro(3, 20)
    assert prog["centro_ajustado"] == {"3": 20}
    assert "V-04" in {a.id for a in ctx.avisos()} and not ventana.estado.boton_exportar.isEnabled()
    assert any(f == "V-04" for f, _g, _t in agrupar(ctx.avisos()))
    e.volver_a_la_propuesta()
    assert prog["centro_ajustado"] == {} and ventana.estado.boton_exportar.isEnabled()

    # Modalidad (ADR-030): Centro quita la empresa; Empresa deja el centro a 0; Mixto vuelve a la propuesta
    e.poner_modalidad(2, "Centro")
    assert "2" not in prog["empresa"] and e.tabla.item(1, e.C_EMPRESA).text() == "—"
    e.poner_modalidad(2, "Empresa")
    assert prog["empresa"]["2"] == 0 and prog["centro_ajustado"] == {"2": 0}
    assert e.tabla.item(1, e.C_CENTRO).text() == "—" and "V-10" in {a.id for a in ctx.avisos()}
    e.poner_empresa(2, 12)
    e.poner_modalidad(2, "Mixto")
    assert prog["centro_ajustado"] == {} and prog["empresa"]["2"] == 12 and prog["modalidad"]["2"] == "Mixto"
    fila = calculos.tabla41(prog, ctx.ficha.numeros_ra)[1]   # la regla de los %, en test_calculos.py
    assert fila.empresa == 12 and e.tabla.item(1, e.C_PCT_EMPRESA).text() == f"{fila.porcentajes[1]} %"
    assert not validacion.bloquean(ctx.avisos())

    # Pesos a mano: tienen que sumar el % de centro (V-12)
    u.elementos.item(0, u.E_AJUSTE).setText("30")
    u.elementos.item(1, u.E_AJUSTE).setText("40 | 40 % entre todas")
    assert prog["elementos"][1]["peso_ajustado"] == {"valor": 40, "texto": "40 % entre todas"}
    assert "V-12" in {a.id for a in ctx.avisos()}
    u.elementos.item(1, u.E_AJUSTE).setText("32")
    assert "V-12" not in {a.id for a in ctx.avisos()}
    u.elementos.item(0, u.E_AJUSTE).setText("")
    u.elementos.item(1, u.E_AJUSTE).setText("")
    assert not any(el.get("peso_ajustado") for el in prog["elementos"])

    # Exportar Word y PDF con el nombre normalizado
    ventana.exportar()
    dialogo = modales[-1]
    assert dialogo.windowTitle() == "Exportando"
    qtbot.waitUntil(lambda: dialogo._terminado, timeout=60000)
    assert dialogo.titulo.text() == "Exportada" and not dialogo.boton_carpeta.isHidden()
    docx, pdf_ = carpeta / f"{NOMBRE}.docx", carpeta / f"{NOMBRE}.pdf"
    assert docx.is_file() and pdf_.is_file() and pdf_falso[-1][1] == "libreoffice"
    assert [p.name for p in dialogo.archivos] == [docx.name, pdf_.name]
    assert prog["historial"][-1]["accion"].startswith("exportada")
    assert ctx.estado_modulo(ctx.modulo) == "exportada"
    assert ventana.boton_programaciones.text() == "Programaciones · 1"

    # Sin sobrescribir sin preguntar
    preguntas = []
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: preguntas.append(a[2]) or QMessageBox.StandardButton.No)
    antes = docx.stat().st_mtime_ns
    n = len(modales)
    ventana.exportar()
    assert preguntas and docx.name in preguntas[0] and len(modales) == n and docx.stat().st_mtime_ns == antes

    # Volver a abrirlo: el Word lleva dentro todos los datos
    exportada = copy.deepcopy(prog)
    ventana.modulos.elegir(ctx.entrada("SEA", 2, "0518"))
    assert ctx.prog is None
    ventana.abrir_archivo(docx)
    datos = incrustar.leer(docx.read_bytes()).programacion
    assert ctx.prog == datos and ctx.modulo.codigo == "0517"
    assert {k: v for k, v in datos.items() if k != "historial"} == \
        {k: v for k, v in exportada.items() if k != "historial"}
    assert not any(isinstance(d, DialogoModificadoWord) for d in modales)

    # Tocado en Word después de exportar: se avisa
    tocado = tmp_path / "tocado.docx"
    with zipfile.ZipFile(docx) as z, zipfile.ZipFile(tocado, "w") as w:
        for n in z.namelist():
            datos_parte = z.read(n)
            if n == "word/document.xml":
                datos_parte = datos_parte.replace(b"</w:body>", b"<w:p><w:r><w:t>Cambio en Word</w:t></w:r></w:p></w:body>")
            w.writestr(n, datos_parte)
    ventana.abrir_archivo(tocado)
    assert modales[-1].windowTitle() == "Abierto con cambios de Word"


@pytest.mark.skipif(pdf.soffice() is None, reason="sin LibreOffice en este equipo")
def test_exportar_con_libreoffice_de_verdad(qtbot, ventana, ctx, prog, tmp_path, modales):
    ctx.gestor.poner_carpeta_entrega(ctx.curso_escolar, str(tmp_path))
    prog["curso_escolar"] = ctx.curso_escolar
    prog["bloques"] = {b: "confirmado" for b in prog["bloques"]}
    ventana.abrir_programacion(prog)
    ventana.exportar()
    qtbot.waitUntil(lambda: modales[-1]._terminado, timeout=240000)
    assert not modales[-1].error.isVisible(), modales[-1].error.text()
    assert (tmp_path / f"{NOMBRE}.pdf").read_bytes().startswith(b"%PDF")


def test_vista_previa_y_miniatura(qtbot, ventana, ctx, prog, modales, pdf_falso):
    from programaciones.ui.vista_previa import DialogoVistaPrevia

    prog["curso_escolar"] = ctx.curso_escolar
    ventana.abrir_programacion(prog)
    assert ventana.accion_vista_previa.isEnabled()
    ventana.abrir_vista_previa()
    qtbot.waitUntil(lambda: any(isinstance(d, DialogoVistaPrevia) for d in modales), timeout=60000)
    visor = next(d for d in modales if isinstance(d, DialogoVistaPrevia))
    assert visor.pila.currentWidget() is visor.visor and visor.documento.pageCount() == 1
    assert not ventana.estado.miniatura.pixmap().isNull()
    assert "BORRADOR" in ventana.estado.texto_previa.text()
    docx = pdf_falso[-1][2]
    with zipfile.ZipFile(BytesIO(docx)) as z:
        assert b"BORRADOR" in b"".join(z.read(n) for n in z.namelist() if n.startswith("word/header"))


def test_sin_curso_escolar_la_vista_previa_va_y_la_definitiva_no(qtbot, ventana, ctx, prog, modales, pdf_falso):
    ctx.datos_curso = None
    prog["curso_escolar"] = ctx.curso_escolar
    prog["bloques"] = {b: "confirmado" for b in prog["bloques"]}
    ventana.abrir_programacion(prog)
    assert [a.id for a in ctx.avisos() if a.gravedad == validacion.ROJA] == ["V-11"]
    assert not ventana.estado.boton_exportar.isEnabled()
    assert any("pendiente" in w.texto.text() or "fechas" in w.texto.text()
               for w in ventana.estado.findChildren(FilaAviso))
    ventana.abrir_vista_previa()
    qtbot.waitUntil(lambda: bool(pdf_falso), timeout=60000)


def test_heredar_de_un_docx_del_curso_pasado(qtbot, ventana, ctx, prog, cat, curso, tmp_path, modales):
    from programaciones.ui.programaciones import DialogoHeredar

    prog["curso_escolar"] = "2025-2026"
    prog["bloques"] = {b: "confirmado" for b in prog["bloques"]}
    anterior = tmp_path / f"{NOMBRE}.docx"
    anterior.write_bytes(incrustar.incrustar(documento.generar(prog, cat, curso), prog))
    d = DialogoHeredar(ctx, ventana)
    qtbot.addWidget(d)
    d.zona.archivos.emit([str(anterior)])
    assert d.heredar.isEnabled() and d.cifras["unidades"].text() == "15" and d.cifras["ra_empresa"].text() == "5"
    assert d.origen.text() == "Profesora Ficticia Uno · curso 2025-2026 · exportada por la app"
    assert "revisar y confirmar" in d.resumen.text()
    d._heredar()
    assert d.result() == QDialog.DialogCode.Accepted
    ventana.heredada(d.herencia)
    nuevo = ctx.prog
    assert nuevo["curso_escolar"] == ctx.curso_escolar and nuevo["heredada_de"]["curso_escolar"] == "2025-2026"
    assert ventana.ficha.banda.isVisible() and "Profesora Ficticia Uno" in ventana.ficha.texto_banda.text()
    assert ventana.estado.resumen.text() == "Confirma los bloques heredados para exportar"
    for paso in ("profesorado", "unidades", "empresa", "ra_competencias", "metodologia"):
        ventana.ficha.ir(paso)
        if ventana.ficha.banda.isVisible():
            qtbot.mouseClick(ventana.ficha.boton_confirmar, Qt.MouseButton.LeftButton)
    assert ventana.estado.boton_exportar.isEnabled() and ventana.estado.texto_progreso.text() == "5 de 5"


def test_heredar_un_word_sin_renombrar_con_el_modulo_elegido(qtbot, ctx, prog, cat, curso, tmp_path, monkeypatch):
    """Un Word sin datos de la app y con cualquier nombre: vale el módulo elegido en la columna «Módulos»."""
    from programaciones.ui import programaciones as ui_prog

    monkeypatch.setattr(ui_prog, "preguntar_modulo", lambda *_a: pytest.fail("no debe preguntar"))
    ctx.elegir(ctx.entrada("SEA", 2, "0517"))
    word = tmp_path / "Programación del curso pasado.docx"
    word.write_bytes(documento.generar(prog, cat, curso))
    d = ui_prog.DialogoHeredar(ctx)
    qtbot.addWidget(d)
    d.poner_archivo(word)
    assert d.heredar.isEnabled() and d.herencia.programacion["modulo"] == "0517"


@pytest.mark.parametrize("respuesta, modulo", [("documento", "0517"), ("elegido", "0519"), (None, None)])
def test_heredar_un_word_de_otro_modulo_que_el_elegido_pregunta(qtbot, ctx, prog, cat, curso, tmp_path, monkeypatch,
                                                                 respuesta, modulo):
    from programaciones.ui import programaciones as ui_prog

    preguntas = []
    monkeypatch.setattr(ui_prog, "preguntar_modulo",
                        lambda _padre, texto, opciones: preguntas.append((texto, opciones)) or respuesta)
    ctx.elegir(ctx.entrada("SEA", 1, "0519"))
    word = tmp_path / f"{NOMBRE}.docx"
    word.write_bytes(documento.generar(prog, cat, curso))
    d = ui_prog.DialogoHeredar(ctx)
    qtbot.addWidget(d)
    d.poner_archivo(word)
    texto, opciones = preguntas[0]
    assert "0517" in texto and "0519" in texto and set(opciones) == {"documento", "elegido"}
    if modulo is None:   # Cancelar: no se hereda nada ni se avisa de un error
        assert d.herencia is None and not d.heredar.isEnabled() and d.resumen.isHidden()
    else:
        assert d.heredar.isEnabled() and d.herencia.programacion["modulo"] == modulo


def test_heredar_de_un_archivo_que_no_vale(qtbot, ctx, tmp_path):
    from programaciones.ui.programaciones import DialogoHeredar

    malo = tmp_path / "SEA 2 - 0517 - Nada.docx"
    malo.write_bytes(b"no es un docx")
    d = DialogoHeredar(ctx)
    qtbot.addWidget(d)
    d.poner_archivo(malo)
    assert not d.heredar.isEnabled() and "No se puede heredar" in d.resumen.text()


def test_cambios_de_curriculo_hasta_que_el_profesor_los_acepta(qtbot, ventana, ctx, prog, tmp_path, modales):
    from programaciones.catalogo import Catalogo

    copia = tmp_path / "catalogo-anterior"
    shutil.copytree(ctx.catalogo.carpeta, copia)
    ruta = copia / "modulos" / "0517.yaml"
    texto = ruta.read_text(encoding="utf-8")
    assert "es: Instala infraestructuras" in texto
    ruta.write_text(texto.replace("es: Instala infraestructuras", "es: Instala (enunciado anterior ficticio) "
                                  "infraestructuras", 1), encoding="utf-8")
    anterior = Catalogo(copia)
    anterior.version = "2026.01.01"   # el catálogo con el que se hizo la programación
    ctx.catalogos[anterior.version] = anterior
    prog["catalogo"] = anterior.version
    prog["curso_escolar"] = ctx.curso_escolar
    prog["bloques"] = {b: "confirmado" for b in prog["bloques"]}
    ventana.abrir_programacion(prog)
    cambios = ctx.cambios_de_curriculo()
    assert cambios == ["RA3 de 0517: enunciado nuevo"]
    dialogo = modales[-1]
    assert dialogo.windowTitle() == "Cambios en el currículo" and "RA3" in dialogo.notas.toPlainText()
    assert "Te afecta en" in dialogo.notas.toPlainText()
    assert "V-08" in {a.id for a in ctx.avisos()} and ventana.catalogo.text() == "Cambios en el currículo"
    assert ctx.prog["catalogo"] == "2026.01.01", "hasta aceptar, sigue con su versión"
    ventana.aceptar_cambios()
    assert ctx.prog["catalogo"] == ctx.catalogo.version and not ctx.cambios_de_curriculo()
    assert ctx.prog["bloques"]["unidades"] == "heredado", "los bloques que usan el RA quedan por revisar"
    assert "V-08" not in {a.id for a in ctx.avisos()}


def test_listado_de_programaciones_con_el_patron_de_los_listados(qtbot, ctx, prog):
    from programaciones import almacen
    from programaciones.ui.programaciones import DialogoProgramaciones

    modulos = [m for m in ctx.modulos if m.sigla == "SEA"][:12]
    for i, m in enumerate(modulos):
        p = copy.deepcopy(prog)
        p.update(ciclo=m.sigla, curso=m.curso, modulo=m.codigo, curso_escolar=ctx.curso_escolar)
        if i % 3 == 0:
            almacen.anotar(p, "exportada: ficticia.docx")
        ctx.almacen.guardar(p)
    ctx.recargar_programaciones()
    d = DialogoProgramaciones(ctx)
    qtbot.addWidget(d)
    t = d.tabla
    assert t.pagina == 2, "se abre en la página de la fila resaltada (la última guardada)"
    t._ir(1)
    assert t.total == 12 and t.tabla.rowCount() == 10 and t.recuento.text() == "Mostrando 1–10 de 12"
    botones = [t._capa_paginas.itemAt(i).widget() for i in range(t._capa_paginas.count())]
    assert [b.text() for b in botones] == ["«", "‹", "1", "2", "›", "»"]
    assert not botones[0].isEnabled() and not botones[1].isEnabled() and botones[-1].isEnabled()
    t.por_pagina.setCurrentIndex(0)
    assert t.tabla.rowCount() == 5 and t.recuento.text() == "Mostrando 1–5 de 12"
    qtbot.keyClicks(t.buscador, "0520")
    assert t.total == 1 and t.limpiar.isEnabled()
    botones = [t._capa_paginas.itemAt(i).widget() for i in range(t._capa_paginas.count())]
    assert botones and not botones[0].isEnabled() and not botones[-1].isEnabled(), "una página: extremos desactivados"
    t.limpiar_filtros()
    assert t.total == 12
    t._ordenar_por(1)  # cabecera «Programación»
    primero = t.seleccionada()
    assert t.tabla.item(0, 1).text() <= t.tabla.item(1, 1).text() and primero is None
    d.tabla.marcar([f["id"] for f in ctx.programaciones if f["estado_clave"] == "exportada"])
    assert d.enviar.text() == "Enviar 4 por correo…" and d.enviar.isEnabled() and not d.abrir.isEnabled()


def test_pie_de_los_listados_con_cinco_numeros_tambien_al_final():
    from programaciones.ui.listado import ventana_paginas

    assert ventana_paginas(1, 12) == [1, 2, 3, 4, 5]
    assert ventana_paginas(6, 12) == [4, 5, 6, 7, 8]
    assert ventana_paginas(12, 12) == [8, 9, 10, 11, 12], "en la última página enseñaba solo tres"
    assert ventana_paginas(11, 12) == [8, 9, 10, 11, 12]
    assert ventana_paginas(3, 3) == [1, 2, 3]
    assert ventana_paginas(1, 1) == [1]


def test_la_fila_nueva_sale_resaltada(qtbot, ctx, prog):
    from programaciones.ui.programaciones import DialogoProgramaciones

    prog["curso_escolar"] = ctx.curso_escolar
    ctx.abrir(prog)
    d = DialogoProgramaciones(ctx)
    qtbot.addWidget(d)
    item = d.tabla.tabla.item(0, 1)
    assert item.font().bold() and item.background().color().name() == estilo.T["accent_soft"]


def test_primer_arranque_pide_nombre_y_carpeta(qtbot, contexto, tmp_path):
    from programaciones.ui.modales import DialogoBienvenida

    assert DialogoBienvenida.hace_falta(contexto)
    d = DialogoBienvenida(contexto)
    qtbot.addWidget(d)
    d.nombre.setText("Profesora Ficticia Tres")
    d.carpeta.setText(str(tmp_path))
    assert "encontrada" in d.estado.text()
    d._guardar()
    assert contexto.gestor.valores.nombre_profesor == "Profesora Ficticia Tres"
    assert contexto.gestor.carpeta_entrega(contexto.curso_escolar) == str(tmp_path)
    assert not DialogoBienvenida.hace_falta(contexto)


def test_ordenar_y_quitar_filas_con_el_teclado(qtbot, ventana, ctx, prog):
    prog["curso_escolar"] = ctx.curso_escolar
    ventana.abrir_programacion(prog)
    ventana.ficha.ir("unidades")
    u = ventana.ficha.bloques["unidades"]
    primera = prog["unidades"][0]["titulo"]
    u.unidades.setCurrentCell(0, u.U_RA)
    qtbot.keyClick(u.unidades, Qt.Key.Key_Down, Qt.KeyboardModifier.AltModifier)
    assert ctx.prog["unidades"][1]["titulo"] == primera
    u.mover("unidades", 1, 0)
    assert ctx.prog["unidades"][0]["titulo"] == primera
    u.unidades.setCurrentCell(0, u.U_RA)
    qtbot.keyClick(u.unidades, Qt.Key.Key_Delete)
    assert len(ctx.prog["unidades"]) == 14 and ctx.prog["unidades"][0]["titulo"] != primera


def test_guardar_y_autoguardado(qtbot, ventana, ctx, prog):
    prog["curso_escolar"] = ctx.curso_escolar
    ventana.abrir_programacion(prog)
    ruta = ctx.almacen.ruta(prog)
    assert ruta.is_file()
    ventana.ficha.bloques["metodologia"].actividades.setPlainText("Visita ficticia.")
    qtbot.waitUntil(lambda: "Visita ficticia." in ruta.read_text(encoding="utf-8"), timeout=5000)
    ventana.guardar()
    assert ventana.aviso.isVisible() and ventana.aviso.text() == "Guardada en este equipo"


def test_parrafos_del_profesor_como_texto():
    from programaciones.ui.bloques import a_texto, de_texto, leer_peso_ajustado, texto_peso_ajustado

    ps = [{"texto": "Párrafo con **negrita**."}, {"texto": "Viñeta", "nivel": 0}, {"texto": "Anidada", "nivel": 1},
          {"texto": "Más anidada", "nivel": 2}]
    assert de_texto(a_texto(ps)) == ps
    assert de_texto("\n\n- \nTexto\n") == [{"texto": "Texto"}]
    assert leer_peso_ajustado("") is None and leer_peso_ajustado("20,5 %") == {"valor": 20.5}
    assert leer_peso_ajustado("20 | 1,25 % / x práctica") == {"valor": 20, "texto": "1,25 % / x práctica"}
    assert texto_peso_ajustado({"valor": 20, "texto": "1,25 % / x práctica"}) == "20 | 1,25 % / x práctica"
    for malo in ("veinte", "120"):
        with pytest.raises(ValueError):
            leer_peso_ajustado(malo)


@pytest.mark.parametrize("sigla, modulo", [("IEA", "0232"), ("SEA", "0519")])
def test_definitiva_de_1_de_gm_y_gs_con_el_curso_2026_2027(qtbot, contexto, cat, tmp_path, modales, pdf_falso, sigla,
                                                           modulo):
    """Con `catalogo/cursos/2026-2027.yaml` no hay «pendiente» de fechas: «Exportar» se activa y sale la definitiva."""
    from conftest import programacion_minima
    from programaciones.ui.ventana import VentanaPrincipal

    contexto.curso_escolar = "2026-2027"
    contexto.datos_curso = cat.curso_escolar("2026-2027")
    contexto.gestor.poner(programa_pdf="libreoffice")
    contexto.gestor.poner_carpeta_entrega("2026-2027", str(tmp_path))
    v = VentanaPrincipal(contexto)
    qtbot.addWidget(v)
    v.show()
    v.abrir_programacion(programacion_minima(cat, sigla, 1, modulo))
    assert contexto.curso_pendiente(contexto.prog) == ""
    assert "V-11" not in {a.id for a in contexto.avisos()}
    assert v.estado.boton_exportar.isEnabled()
    v.exportar()
    qtbot.waitUntil(lambda: modales[-1]._terminado, timeout=60000)
    assert [p.suffix for p in modales[-1].archivos] == [".docx", ".pdf"]
    assert all(p.parent == tmp_path and p.name.startswith(f"{sigla} 1 - {modulo} - ") for p in modales[-1].archivos)


def test_proponer_correccion_de_competencias_con_ia(qtbot, ventana, ctx, monkeypatch):
    """CarlosFB, 2026-10-17: si las competencias de cada RA no casan con la propuesta, un botón la enseña y el
    profesor decide; con «Mantener las mías» no cambia nada y con «Aplicar la propuesta» queda la de la app."""
    import dataclasses

    from programaciones.ui import modales as m

    elegir_0517(qtbot, ventana)
    ctx.ficha = dataclasses.replace(ctx.ficha, propuesta_competencias={n: ["a"] for n in ctx.ficha.numeros_ra})
    qtbot.mouseClick(ventana.ficha.boton_empezar, Qt.MouseButton.LeftButton)
    prog = ctx.prog
    assert prog["ra_competencias"] == {str(n): ["a"] for n in ctx.ficha.numeros_ra}, "nueva: con la propuesta"
    assert prog["bloques"]["ra_competencias"] == "heredado"
    ventana.ficha.ir("ra_competencias")
    c = ventana.ficha.bloques["ra_competencias"]
    assert c.corregir.isHidden(), "coincide con la propuesta: sin botón"
    assert "IA" in ventana.ficha.texto_banda.text()

    c.marcar(1, c.letras[1])                      # el profesor cambia el RA1
    assert not c.corregir.isHidden()
    respuestas = iter([QDialog.DialogCode.Rejected, QDialog.DialogCode.Accepted])
    monkeypatch.setattr(m.DialogoPropuestaCompetencias, "exec", lambda self: next(respuestas))
    c.proponer_correccion()
    assert "RA1" in c.ultimo_dialogo.texto.text() and "RA2" not in c.ultimo_dialogo.texto.text()
    assert sorted(prog["ra_competencias"]["1"]) == sorted(["a", c.letras[1]]), "«Mantener las mías»"
    c.proponer_correccion()
    assert prog["ra_competencias"]["1"] == ["a"] and c.corregir.isHidden(), "«Aplicar la propuesta»"


def test_flujo_de_un_ambito_de_grado_basico(qtbot, ventana, ctx):
    """ADR-032: un ámbito tiene tres pasos, sus CE en lugar de RA y sus partes; cada unidad va a una parte."""
    ctx.curso_escolar = "2026-2027"
    ctx.datos_curso = ctx.catalogo.curso_escolar("2026-2027")
    ambito = next(m for m in ctx.modulos if m.sigla == "EE" and m.codigo == "3164")
    ctx.elegir(ambito)
    ficha = ventana.ficha
    qtbot.mouseClick(ficha.boton_empezar, Qt.MouseButton.LeftButton)
    prog = ctx.prog
    # ADR-039: Ciencias Aplicadas se propone en Matemáticas y Ciencias, por horas semanales (5 h → 3 + 2)
    assert prog["partes"] == [{"id": "p1", "nombre": "Matemáticas II", "horas": 100},
                              {"id": "p2", "nombre": "Ciencias II", "horas": 66}]
    assert {u["parte"] for u in prog["unidades"]} == {""}, "con dos partes, las unidades las reparte el profesor"
    visibles = [p for p, b in ficha.botones_paso.items() if not b.isHidden()]
    assert visibles == ["profesorado", "unidades", "metodologia"]
    assert ventana.estado.texto_progreso.text().endswith("de 3")
    u = ficha.bloques["unidades"]
    ficha.ir("unidades")
    assert u.unidades.horizontalHeaderItem(u.U_RA).text() == "CE"
    assert u.unidades.horizontalHeaderItem(u.U_PESO).text() == "Parte" and not u.chip_partes.isHidden()
    assert u.elementos.isColumnHidden(u.E_PESO)
    # el profesor puede cambiar las partes propuestas
    u.ver(3)
    u.partes.item(0, 1).setText("Matemáticas ficticias")
    u.partes.item(0, 2).setText("90")
    u.anadir_parte()
    assert prog["partes"][2]["horas"] == 10, "la parte nueva se lleva las horas que faltan"
    u.partes.item(1, 1).setText("Ciencias ficticias")
    assert [x["nombre"] for x in prog["partes"]][:2] == ["Matemáticas ficticias", "Ciencias ficticias"]
    # una unidad a la segunda parte, desde la tabla de unidades
    u.ver(0)
    u.unidades.item(0, u.U_PESO).setData(Qt.ItemDataRole.UserRole, prog["partes"][1]["id"])
    assert prog["unidades"][0]["parte"] == prog["partes"][1]["id"]
    assert any(a.id == "V-14" for a in ctx.avisos()), "las horas de cada parte ya no cuadran"
    # en el elemento, «CE» en lugar de «RA»
    u.anadir_elemento()
    u.elegir_ra(0, [1, 2])
    assert u.elementos.item(0, u.E_RA).text() == "CE1 y CE2"
