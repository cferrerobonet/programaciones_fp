"""Importar una programación con la plantilla actual retocada a mano en Word (sin los datos de la app dentro): subtítulos
sin número, cabeceras de la tabla 4.1 con otra redacción, listas de RA abreviadas, celdas de elemento vacías con su
propio peso, filas vacías y párrafos de entrada de los bloques sustituibles reescritos. Cada variante se hace sobre un
documento generado con datos ficticios."""
import io
import zipfile

import pytest
from lxml import etree

from programaciones import calculos, documento, exportacion, importar_docx, incrustar, ooxml, validacion
from programaciones.ooxml import W, es_titulo, normal, texto

NOMBRE = "SEA 2 - 0517 - Procesos en instalaciones de infraestructuras comunes de telecomunicaciones.docx"


# --- Retoques del documento generado, como los haría un profesor en Word ----------------------------------------------
def retocar(docx: bytes, cambio) -> bytes:
    """Aplica `cambio(cuerpo)` al document.xml y devuelve el .docx."""
    entrada, salida = zipfile.ZipFile(io.BytesIO(docx)), io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for i in entrada.infolist():
            datos = entrada.read(i.filename)
            if i.filename == "word/document.xml":
                raiz = etree.fromstring(datos)
                cambio(raiz.find(W + "body"))
                datos = etree.tostring(raiz, xml_declaration=True, encoding="UTF-8", standalone=True)
            z.writestr(i, datos)
    return salida.getvalue()


def escribir(p, nuevo: str) -> None:
    """Deja el párrafo con un solo texto (sin enlaces ni campos)."""
    for hijo in [h for h in p if h.tag != W + "pPr"]:
        p.remove(hijo)
    r = etree.SubElement(p, W + "r")
    t = etree.SubElement(r, W + "t")
    t.text = nuevo
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def parrafo(cuerpo, inicio: str, titulo: bool = False):
    return next(p for p in cuerpo.iter(W + "p")
                if normal(texto(p)).startswith(inicio) and (es_titulo(p) if titulo else not es_titulo(p)))


def tabla(cuerpo, inicio: str):
    return next(t for t in cuerpo.iter(W + "tbl") if normal(texto(t.find(W + "tr"))).casefold().startswith(inicio))


def celda(tr, i: int):
    return tr.findall(W + "tc")[i]


def poner_celda(tc, *parrafos: str) -> None:
    """La celda con estos párrafos y sin combinación vertical (una celda vacía si no hay párrafos)."""
    pr = tc.find(W + "tcPr")
    if pr is not None and pr.find(W + "vMerge") is not None:
        pr.remove(pr.find(W + "vMerge"))
    ps = tc.findall(W + "p")
    for p in ps[1:]:
        tc.remove(p)
    escribir(ps[0], parrafos[0] if parrafos else "")
    for t in parrafos[1:]:
        nuevo = etree.SubElement(tc, W + "p")
        escribir(nuevo, t)


@pytest.fixture
def generado(prog, cat, curso):
    return documento.generar(prog, cat, curso)


def importar(docx, cat):
    return importar_docx.importar(docx, cat, NOMBRE)


# --- Exportada por la app y sin sus datos dentro (Word o SharePoint los pierden) -------------------------------------
def sin_datos_de_la_app(docx: bytes) -> bytes:
    pq = ooxml.Paquete.desde_docx(docx)
    for item in incrustar._partes_propias(pq):
        incrustar.quitar_parte(pq, item)
    docx = pq.a_bytes()
    assert incrustar.leer(docx) is None
    return docx


def sin_ids(prog):
    el = {e["id"]: e for e in prog["elementos"]}
    return [(u, {k: v for k, v in el[u.pop("elemento")].items() if k != "id"})
            for u in ({k: v for k, v in x.items() if k != "id"} for x in prog["unidades"])]


def test_exportada_por_la_app_sin_sus_datos_se_lee_igual(prog, cat, curso, tmp_path):
    """Fija lo que la lectura del texto saca de un .docx exportado por la app al que se le ha perdido la parte con
    los datos: lo mismo que se exportó, salvo los identificadores, el estado de los bloques (heredados) y la
    modalidad, que se lee de la tabla 4.1."""
    prog["textos_propios"] = {"instrumentos": [{"texto": "Entrega de las tareas ficticias.", "nivel": 0}],
                              "calificacion": [{"texto": "La calificación ficticia sale de las tareas."}]}
    prog["elementos"][0]["peso_ajustado"] = {"valor": 2.15}
    prog["elementos"][2]["peso_ajustado"] = {"valor": 4.2, "texto": "1,4 % / x práctica"}
    prog["elementos"][2]["detalle"] = ["(7h)", "MEMORIA ficticia"]
    prog["columna_pct_curso"] = True
    prog["unidades"][0]["descripcion"] = ["Descripción ficticia de la unidad."]
    prog["unidades"][1]["trimestre"] = [1, 2]
    prog["contenidos"] = [{"texto": "Contenido ficticio uno."}, {"texto": "Subcontenido ficticio.", "nivel": 1}]
    prog["actividades"] = [{"texto": "Visita ficticia a una empresa inventada."}]
    prog["notas_tabla41"] = [{"texto": "Nota ficticia de la 4.1."}]
    prog["metodologia_final"] = [{"texto": "Cierre ficticio de la metodología."}]
    res = exportacion.exportar(prog, cat, curso, tmp_path, ["docx"], documento.Opciones())
    exportado = res.archivos[0].read_bytes()
    assert importar_docx.importar(exportado, cat, res.archivos[0].name) == prog   # con los datos: tal cual
    imp = importar_docx.importar(sin_datos_de_la_app(exportado), cat, res.archivos[0].name)
    assert sin_ids(imp) == sin_ids(prog)
    for clave in ("profesorado", "curso_escolar", "empresa", "centro_ajustado", "ra_competencias", "contenidos",
                  "notas_tabla4", "notas_tabla41", "metodologia", "metodologia_final", "recursos", "espacios",
                  "actividades", "textos_propios", "columna_pct_curso"):
        assert imp[clave] == prog[clave], clave
    ras = cat.ficha("SEA", "0517", 2).numeros_ra
    assert imp["modalidad"] == {str(f.ra): f.modalidad for f in calculos.tabla41(prog, ras)}
    assert set(imp["bloques"].values()) == {"heredado"}
    assert "ra_documento" not in imp and "sustituyen_salida" not in imp   # los RA y la salida, los de la plantilla


# --- Subtítulos sin número ---------------------------------------------------------------------------------------------
def test_subtitulos_sin_numero_van_a_su_apartado(prog, cat, curso):
    """Con «5.1.-», «11.1.-» y «11.2.-» borrados de sus títulos, la metodología y los textos propios se perdían: sus
    párrafos caían en un apartado «Principios generales…» que no se lee."""
    prog["metodologia_final"] = [{"texto": "Cierre ficticio de la metodología."}]
    prog["textos_propios"] = {"instrumentos": [{"texto": "Instrumento ficticio único.", "nivel": 0}],
                              "elementos": [{"texto": "Exámenes ficticios (E).", "nivel": 0}]}
    docx = documento.generar(prog, cat, curso)

    def sin_numeros(cuerpo):
        escribir(parrafo(cuerpo, "5.1", titulo=True), "Principios generales y pedagógicos")
        escribir(parrafo(cuerpo, "11.1", titulo=True), "Instrumentos y procedimiento de evaluación:")
        escribir(parrafo(cuerpo, "11.2", titulo=True), "ELEMENTOS DE EVALUACIÓN")

    imp = importar(retocar(docx, sin_numeros), cat)
    assert imp["metodologia"] == prog["metodologia"]
    assert imp["metodologia_final"] == prog["metodologia_final"]
    assert imp["textos_propios"] == prog["textos_propios"]


# --- Tabla 4.1 ---------------------------------------------------------------------------------------------------------
def test_cabeceras_horas_de_empresa_y_horas_en_el_centro(prog, cat, generado):
    """«Horas de / empresa» (en dos líneas) no se reconocía: las horas de empresa se perdían (empresa 0 h y V-13 en
    todos los RA mixtos)."""
    def cabeceras(cuerpo):
        cab = next(t for t in cuerpo.iter(W + "tbl") if "Modalidad" in texto(t.find(W + "tr"))).find(W + "tr")
        nombres = [normal(texto(tc)) for tc in cab.findall(W + "tc")]
        poner_celda(celda(cab, nombres.index("Horas Centro")), "Horas en el centro")
        poner_celda(celda(cab, nombres.index("Horas Empresa")), "Horas de", "empresa")

    imp = importar(retocar(generado, cabeceras), cat)
    assert imp["empresa"] == prog["empresa"]
    assert imp["centro_ajustado"] == prog["centro_ajustado"]


# --- Tabla 4 -----------------------------------------------------------------------------------------------------------
def _filas_del_examen_1(cuerpo):
    """Las dos filas de «EXAMEN 1» (la segunda, combinada con la primera en elemento, peso y RA)."""
    t4 = tabla(cuerpo, "unidad")
    filas = [tr for tr in t4.findall(W + "tr") if "Unidad ficticia 2" in texto(tr) or "Unidad ficticia 3" in texto(tr)]
    return t4, filas


def test_celda_de_elemento_vacia_con_su_propio_peso_es_otro_elemento(cat, generado):
    """Una celda de elemento vacía (sin combinar) con su propio peso y sus RA era «el elemento de arriba»: su peso se
    perdía y los pesos dejaban de sumar."""
    def vaciar(cuerpo):
        _t4, (_primera, segunda) = _filas_del_examen_1(cuerpo)
        poner_celda(celda(segunda, 3))
        poner_celda(celda(segunda, 4), "9 %")
        poner_celda(celda(segunda, 5), "RA1")

    imp = importar(retocar(generado, vaciar), cat)
    u2, u3 = imp["unidades"][1], imp["unidades"][2]
    assert u2["elemento"] != u3["elemento"]
    nuevo = next(e for e in imp["elementos"] if e["id"] == u3["elemento"])
    assert (nuevo["nombre"], nuevo["ra"], nuevo["peso_ajustado"]) == ("", [1], {"valor": 9.0})


def test_celda_de_elemento_vacia_sin_peso_propio_sigue_siendo_el_de_arriba(prog, cat, generado):
    def vaciar(cuerpo):
        _t4, (_primera, segunda) = _filas_del_examen_1(cuerpo)
        for i in (3, 4, 5):
            poner_celda(celda(segunda, i))

    imp = importar(retocar(generado, vaciar), cat)
    assert imp["unidades"][1]["elemento"] == imp["unidades"][2]["elemento"]
    assert len(imp["elementos"]) == len(prog["elementos"])


def test_fila_vacia_de_la_tabla_4_no_es_una_unidad(prog, cat, generado):
    def fila_vacia(cuerpo):
        t4, (primera, _segunda) = _filas_del_examen_1(cuerpo)
        import copy
        vacia = copy.deepcopy(primera)
        for tc in vacia.findall(W + "tc"):
            poner_celda(tc)
        t4.findall(W + "tr")[-1].addnext(vacia)   # al final, tras las filas de totales

    imp = importar(retocar(generado, fila_vacia), cat)
    assert len(imp["unidades"]) == len(prog["unidades"])


def test_columna_de_ra_titulada_resultados_de_aprendizaje(prog, cat, generado):
    """Con la columna de RA de la tabla 4 titulada «Resultados de Aprendizaje», ningún elemento tenía RA (V-03)."""
    def cabecera(cuerpo):
        cab = tabla(cuerpo, "unidad").find(W + "tr")
        poner_celda(celda(cab, 5), "Resultados de Aprendizaje (RA)")

    imp = importar(retocar(generado, cabecera), cat)
    assert [e["ra"] for e in imp["elementos"]] == [e["ra"] for e in prog["elementos"]]


def test_nombre_con_varias_horas_entre_parentesis_no_se_parte(cat, generado):
    def nombre(cuerpo):
        _t4, (primera, _segunda) = _filas_del_examen_1(cuerpo)
        poner_celda(celda(primera, 3), "PR 1(3h), PR 2 (4h)", "EXAMEN ficticio (2h)")

    imp = importar(retocar(generado, nombre), cat)
    el = next(e for e in imp["elementos"] if e["id"] == imp["unidades"][1]["elemento"])
    assert (el["nombre"], el["tipo"], el["detalle"]) == ("PR 1(3h), PR 2 (4h)", "P", ["EXAMEN ficticio (2h)"])


@pytest.mark.parametrize("texto_ra, ras", [
    ("RA 3 y 6", [3, 6]), ("RA1, 4, y 6", [1, 4, 6]), ("R2, 3 y 6", [2, 3, 6]), ("RA 2y 4", [2, 4]),
    ("R3 y RA 4", [3, 4]), ("R.A 4", [4]), ("RA2-RA4", [2, 3, 4]), ("RA2 -> 5", [2, 3, 4, 5]),
    ("RA1 a RA3", [1, 2, 3]), ("RA1 - 20 %", [1]), ("Prác. 4 y 5", []), ("Real Decreto 999/2099", []),
])
def test_listas_de_ra_escritas_a_mano(texto_ra, ras):
    """Antes solo se leía el número pegado a «RA»: «RA 3 y 6» daba [3] y el RA6 quedaba sin evaluar (V-02)."""
    assert importar_docx._ras(texto_ra) == ras


@pytest.mark.parametrize("nombre, tipo", [
    ("Exám. 2", "E"), ("Exam 1", "E"), ("Prác.4, 5 y 6", "P"), ("PR 1(3h)", "P"), ("PR-AB2", "P"), ("Pr1", "P"),
    ("PRUEBA 1", "T"), ("Proyecto ficticio", "T"), ("PRESENTACIÓN", "T"), ("EXAMEN 3", "E"), ("PRÁCTICA 2", "P"),
])
def test_tipo_de_elemento_abreviado(nombre, tipo):
    assert importar_docx._tipo(nombre) == tipo


# --- Bloques sustituibles con su entrada o su salida reescritas ------------------------------------------------------
def test_bloques_sustituibles_con_la_entrada_y_la_salida_reescritas(cat, generado):
    """La entrada del bloque de asistencia reescrita («La asistencia deberá alcanzar…»), la salida con su texto en el
    mismo párrafo y una viñeta a mano («• Visitas y actividades complementarias: …») y, en el 9, sin el párrafo de
    salida: los bloques del profesor no se leían."""
    def reescribir(cuerpo):
        escribir(parrafo(cuerpo, "Prácticas (P):"), "Prácticas (P): actividades ficticias de taller.")
        escribir(parrafo(cuerpo, "La asistencia deberá ser"), "La asistencia deberá alcanzar como mínimo el 85 % ficticio.")
        escribir(parrafo(cuerpo, "No se repetirá ninguna prueba"), "No se repetirá ninguna prueba ficticia.")
        visitas = parrafo(cuerpo, "Visitas y actividades complementarias")
        texto_visitas = visitas.getnext()
        escribir(visitas, "• Visitas y actividades complementarias: asistencia ficticia obligatoria.")
        cuerpo.remove(texto_visitas)
        salida_9 = parrafo(cuerpo, "La calificación del módulo es la suma ponderada")
        escribir(salida_9.getprevious(), "Calificación ficticia por resultados de aprendizaje.")
        cuerpo.remove(salida_9)

    imp = importar(retocar(generado, reescribir), cat)
    propios = imp["textos_propios"]
    # el documento no lleva «La calificación del módulo es la suma ponderada…»: el texto del profesor la sustituye.
    # Las salidas de los otros bloques sí están (reescritas): no cuentan
    assert imp["sustituyen_salida"] == ["calificacion"]
    assert propios["calificacion"] == [{"texto": "Calificación ficticia por resultados de aprendizaje."}]
    assert [p["texto"] for p in propios["elementos"]][1] == "Prácticas (P): actividades ficticias de taller."
    assert len(propios["elementos"]) == 3
    asistencia = [p["texto"] for p in propios["asistencia_y_pruebas"]]
    assert "No se repetirá ninguna prueba ficticia." in asistencia
    assert not any(t.startswith(("La asistencia", "•", "Visitas")) for t in asistencia)
    modelo = importar_docx.plantilla()["sustituibles"]["asistencia_y_pruebas"]["bloque"][False]
    assert len(asistencia) == len(modelo)


def test_bloques_de_la_plantilla_tal_cual_no_son_textos_propios(cat, generado):
    assert importar(generado, cat)["textos_propios"] == {}


# --- Avisos ------------------------------------------------------------------------------------------------------------
def test_v04_dice_por_que_un_ra_no_cuadra(prog, cat):
    """V-04 con límites «0-0 h» o «32-32 h» no se entendía: lo dice con palabras."""
    ficha = cat.ficha("SEA", "0517", 2)
    p = dict(prog, centro_ajustado={"5": 4})   # el RA5 no está en ningún elemento: solo en empresa
    mensajes = [a.mensaje for a in validacion.validar(p, ficha) if a.id == "V-04"]
    assert "RA5: 4 h de centro y no está en ningún elemento con horas de la tabla 4" in mensajes
    p = dict(prog, elementos=[dict(e, ra=[5]) if e["id"] == "e0" else e for e in prog["elementos"]],
             centro_ajustado={"5": 6})
    mensajes = [a.mensaje for a in validacion.validar(p, ficha) if a.id == "V-04"]
    assert "RA5: 6 h de centro; sus elementos de la tabla 4 le dan 4 h" in mensajes


def test_enunciados_de_ra_del_documento_distintos_del_curriculo(cat, generado):
    """Un enunciado de RA de la tabla 4.1 reescrito se guarda (V-16) con el texto del documento; los iguales, no."""
    def reescribir(cuerpo):
        t41 = next(t for t in cuerpo.iter(W + "tbl") if "Modalidad" in texto(t.find(W + "tr")))
        fila = next(tr for tr in t41.findall(W + "tr")[1:] if normal(texto(celda(tr, 0))).startswith("R.A.2"))
        poner_celda(celda(fila, 0), "R.A.2. Enunciado ficticio reescrito a mano.")

    imp = importar(retocar(generado, reescribir), cat)
    assert imp["ra_documento"] == {"2": "Enunciado ficticio reescrito a mano."}
    avisos = validacion.validar(imp, cat.ficha("SEA", "0517", 2))
    assert [a.id for a in avisos if a.gravedad == validacion.AMBAR].count("V-16") == 1


def _hay(docx: bytes, inicio: str) -> bool:
    cuerpo = etree.fromstring(zipfile.ZipFile(io.BytesIO(docx)).read("word/document.xml")).find(W + "body")
    return any(normal(texto(p)).startswith(inicio) for p in cuerpo.iter(W + "p"))


def test_texto_propio_que_sustituye_la_salida_del_bloque_no_la_duplica(prog, cat, curso):
    """Con `sustituyen_salida`, el párrafo fijo que sigue al bloque no sale: el texto del profesor ya lo dice. Sin la
    clave (todas las programaciones de antes) o sin texto propio del bloque, sale como siempre."""
    salida = "La calificación del módulo es la suma ponderada"
    assert _hay(documento.generar(prog, cat, curso), salida)
    prog["sustituyen_salida"] = ["calificacion"]
    assert _hay(documento.generar(prog, cat, curso), salida)   # sin texto propio, no cuenta
    prog["textos_propios"] = {"calificacion": [{"texto": "Calificación ficticia: media de los RA, aprobado con 5."}]}
    docx = documento.generar(prog, cat, curso)
    assert not _hay(docx, salida) and _hay(docx, "Calificación ficticia: media de los RA")
    assert _hay(docx, "Los Resultados de Aprendizaje que no hayan sido superados")   # lo siguiente, sí
    del prog["sustituyen_salida"]
    assert _hay(documento.generar(prog, cat, curso), salida)
