"""Documento generado: plantilla rellena, reglas de la guía programacion-didactica y retoques (sin datos reales)."""
import io
import re
import zipfile

import pytest
from lxml import etree

from conftest import programacion_ficticia
from programaciones import contenido, documento, programacion
from programaciones.documento import Enlace, Opciones
from programaciones.ooxml import R, W, texto


def generar(prog, cat, curso, **kw):
    return documento.generar(prog, cat, curso, Opciones(**kw))


def secciones(docx):
    return contenido.secciones(contenido.leer(docx))


def parrafos(docx, seccion):
    return [e.texto for e in secciones(docx).get(seccion, []) if e.tipo == "p"]


def tablas(docx, seccion):
    return [e for e in secciones(docx).get(seccion, []) if e.tipo == "tabla"]


def xml(docx, parte="word/document.xml"):
    return etree.fromstring(zipfile.ZipFile(io.BytesIO(docx)).read(parte))


@pytest.fixture
def docx(prog, cat, curso):
    return generar(prog, cat, curso)


def test_cumple_las_comprobaciones_de_la_skill(docx):
    plantilla = documento.cargar_plantilla().a_bytes()
    v = contenido.verificar(docx, contenido.titulos(plantilla))
    assert v["titulos_iguales"] and v["campo_toc"] == 1 and v["update_fields"]
    assert v["citas_sin_enlace"] == [] and not v["termino_vetado"]


def test_paquete_completo_y_sin_marcas(docx):
    z = zipfile.ZipFile(io.BytesIO(docx))
    assert {"[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/_rels/document.xml.rels"} <= set(z.namelist())
    for n in z.namelist():
        if n.endswith(".xml"):
            assert "{{" not in z.read(n).decode("utf-8"), n


def test_portada(docx, prog, cat, curso):
    filas = [f for t in tablas(docx, "portada") for f in t.filas]
    assert ["Módulo profesional:", "0517 – Procesos en instalaciones de infraestructuras comunes de "
            "telecomunicaciones"] in filas
    assert ["Nº Horas del módulo:", "166"] in filas and ["Profesor:", "Profesora Ficticia Uno"] in filas
    prog["profesorado"].append("Profesor Ficticio Dos")
    otro = generar(prog, cat, curso)
    filas = [f for t in tablas(otro, "portada") for f in t.filas]
    assert ["Profesores:", "Profesora Ficticia Uno / Profesor Ficticio Dos"] in filas
    assert any("el profesorado del módulo" in p for p in parrafos(otro, "9"))


def test_normativa_estatal_por_fecha_con_el_real_decreto_del_titulo(docx, cat):
    d = xml(docx)
    rels = {r.get("Id"): r.get("Target") for r in etree.fromstring(
        zipfile.ZipFile(io.BytesIO(docx)).read("word/_rels/document.xml.rels"))}
    body = d.find(W + "body")
    en = False
    fechas, textos = [], []
    for e in body:
        t = texto(e)
        if t.startswith("1.1."):
            en = True
            continue
        if t.startswith("1.2."):
            break
        if en and t.strip():
            textos.append(t)
            h = e.find(f".//{W}hyperlink")
            m = re.search(r"BOE-A-\d{4}-\d+", rels[h.get(R + "id")])
            fechas.append(cat.norma(m.group(0)).fecha)
    assert fechas == sorted(fechas)
    assert textos[0].startswith("Real Decreto 1127/2010, de 10 de septiembre, por el que se establece el título")
    assert any(t.startswith("Real Decreto 401/2023") for t in textos)
    assert not any("499/2024" in t for t in textos)


def test_normativa_autonomica_con_el_decreto_95_2026_y_la_resolucion_del_curso(prog, cat, curso):
    prog["curso_escolar"] = "2026-2027"
    d = generar(prog, cat, curso)
    ps = parrafos(d, "1.2")
    assert any(p.startswith("Decreto 95/2026, de 19 de junio") for p in ps)    # CarlosFB, 2026-10-17
    assert ps[-1].startswith("RESOLUCIÓN de 16 de julio de 2026")
    assert parrafos(generar(programacion_ficticia(), cat, curso), "1.2")[-1].startswith("Decreto 95/2026")


def test_tabla_4_pesos_ra_combinaciones_y_totales(docx):
    t = tablas(docx, "4")[0]
    filas = t.filas
    assert filas[2][3:] == ["EXAMEN 1 / (24h)", "14,5 %", "RA1 y RA2"]
    assert filas[3][3:] == filas[2][3:]                        # la segunda unidad del EXAMEN 1, combinada
    assert ["HORAS CENTRO", "103", "62 %", ""] in filas
    assert ["HORAS DE EMPRESA", "63", "38 %", "RA2 → RA6"] in filas
    tcs = t.xml.findall(W + "tr")[2].findall(W + "tc")
    assert tcs[3].find(f"{W}tcPr/{W}vMerge").get(W + "val") == "restart"
    assert t.xml.findall(W + "tr")[3].findall(W + "tc")[3].find(f"{W}tcPr/{W}vMerge").get(W + "val") is None


CABECERA_41 = ["Resultado de aprendizaje", "Modalidad", "Horas Centro", "Horas Empresa", "% Horas Centro",
               "% Horas Empresa"]


def test_tabla_41_cuadrada_con_el_ajuste_del_profesor(docx):
    """Formato de CarlosFB (2026-10-17, ADR-025): horas de centro y de empresa (o «-») y % solo en los mixtos."""
    filas = tablas(docx, "4.1")[0].filas
    assert filas[0] == CABECERA_41
    por_ra = {f[0][:6]: f[1:] for f in filas if f[0].startswith("R.A.")}
    assert por_ra["R.A.1."] == ["Centro", "34", "-", "-", "-"]
    assert por_ra["R.A.3."] == ["Mixto", "8", "13", "38 %", "62 %"]   # 8 de centro (ajuste) + 13 de empresa
    assert por_ra["R.A.5."] == ["Empresa", "-", "13", "-", "-"]
    assert filas[-1] == ["TOTAL", "103", "63", ""]


def celdas_41(docx):
    t = next(t for t in xml(docx).iter(W + "tbl")
             if [texto(tc) for tc in t.find(W + "tr").findall(W + "tc")][:2] == ["Resultado de aprendizaje", "Modalidad"])
    return t, t.findall(W + "tr")


def test_tabla_41_formato(docx):
    t, filas = celdas_41(docx)
    cab = filas[0].findall(W + "tc")
    assert all(tc.find(f"{W}tcPr/{W}shd").get(W + "fill") == "F2F2F2" for tc in cab), "cabecera sobre gris claro"
    assert all(r.find(f"{W}rPr/{W}b") is not None for tc in cab for r in tc.iter(W + "r"))
    assert len(cab[2].findall(f".//{W}br")) == 1 and texto(cab[2]) == "Horas Centro", "dos líneas"
    ra = filas[1].findall(W + "tc")
    codigo, enunciado = [r for r in ra[0].iter(W + "r") if texto(r).strip()][:2]
    assert texto(codigo) == "R.A.1." and codigo.find(f"{W}rPr/{W}u") is not None and \
        codigo.find(f"{W}rPr/{W}b") is not None
    assert ra[0].find(f"{W}p/{W}pPr/{W}jc").get(W + "val") == "both", "enunciado justificado"
    assert all(tc.find(f"{W}p/{W}pPr/{W}jc").get(W + "val") == "center" for tc in ra[1:])
    assert all(r.find(f"{W}rPr/{W}b") is not None for tc in ra[4:] for r in tc.iter(W + "r")), "% en negrita"
    assert filas[1].find(f"{W}trPr/{W}cantSplit") is not None
    total = filas[-1].findall(W + "tc")
    assert [tc.find(f"{W}tcPr/{W}gridSpan").get(W + "val") if tc.find(f"{W}tcPr/{W}gridSpan") is not None else "1"
            for tc in total] == ["2", "1", "1", "2"], "TOTAL en RA y Modalidad; los dos % combinados"
    assert total[0].find(f"{W}p/{W}pPr/{W}jc").get(W + "val") == "right"
    assert all(r.find(f"{W}rPr/{W}b") is not None for tc in total[:3] for r in tc.iter(W + "r"))
    assert all(tc.find(f"{W}tcPr/{W}shd").get(W + "fill") == "D9D9D9" for tc in total), "fila TOTAL sobre gris"
    anchos = [int(g.get(W + "w")) for g in t.find(W + "tblGrid")]
    assert len(anchos) == 6 and sum(anchos) == 8896


def test_sin_empresa_sin_filas_de_centro_y_empresa(prog, cat, curso):
    """El Proyecto (sin empresa): fuera las filas de centro y empresa de la tabla 4; la 4.1 sigue con sus seis
    columnas y «-» en lo de empresa (ADR-025)."""
    prog["empresa"] = {}
    prog["unidades"][0]["horas"] += 63
    d = generar(prog, cat, curso)
    assert not any(f[0].startswith("HORAS") for f in tablas(d, "4")[0].filas)
    filas = tablas(d, "4.1")[0].filas
    assert filas[0] == CABECERA_41
    assert all(f[1] in ("Centro", "-") and f[3:] == ["-", "-", "-"] for f in filas[1:-1])  # RA5: solo era de empresa
    assert filas[-1][0] == "TOTAL" and filas[-1][2:] == ["-", ""]


def test_criterios_de_cada_ra_con_su_numeracion(docx):
    nums = []
    for e in secciones(docx)["11"]:
        if e.tipo == "p" and e.texto.startswith("Se ha"):
            nums.append(e.xml.find(f"{W}pPr/{W}numPr/{W}numId").get(W + "val"))
    assert len(set(nums)) == 6                                  # una lista por RA: cada una empieza en a)


def test_ra_y_criterios_corregidos_del_catalogo(docx):
    ps = parrafos(docx, "11")
    assert any(p.startswith("R.A.1. Caracteriza instalaciones") for p in ps)
    assert any("(ICT)" in p for p in ps) and not any("(ITC)" in p for p in ps)


def test_parrafos_del_profesor_con_negrita_y_enlaces(docx):
    p = next(e.xml for e in secciones(docx)["5.1"] if e.texto.startswith("Párrafo ficticio de metodología"))
    negritas = [texto(r) for r in p.iter(W + "r") if r.find(f"{W}rPr/{W}b") is not None]
    assert negritas == ["cuaderno ficticio"]
    assert [texto(h) for h in p.iter(W + "hyperlink")] == ["Real Decreto 1127/2010, de 10 de septiembre"]
    assert "**" not in contenido.texto_cuerpo(docx)


def test_vinetas_del_profesor(docx):
    rec = [e for e in secciones(docx)["6"] if e.tipo == "p"]
    assert [(e.texto, e.nivel) for e in rec[:2]] == [("Recurso ficticio uno.", 0), ("Subrecurso ficticio.", 1)]


def test_textos_propios_sustituyen_el_bloque_de_la_plantilla(prog, cat, curso):
    prog["textos_propios"] = {"instrumentos": [{"texto": "Entrega de las tareas ficticias.", "nivel": 0}]}
    d = generar(prog, cat, curso)
    ps = parrafos(d, "11.1")
    assert ps[-1] == "Entrega de las tareas ficticias."
    assert not any(p.startswith("Pruebas y test de conocimientos") for p in ps)


def test_fechas_del_curso_y_formacion_en_empresa(docx):
    ps = parrafos(docx, "9")
    assert "Evaluación inicial: 30/09/2030" in ps
    assert ("La convocatoria ordinaria finalizará el 10 de junio de 2031 y la convocatoria extraordinaria finalizará el "
            "24 de junio de 2031." in ps)   # fechas de fin, como las evaluaciones (ADR-033)
    assert parrafos(docx, "9.1")[2:] == [
        "Alumnos que realicen 8h/día (en total 43 días de formación): desde el 3 de marzo al 30 de mayo de 2031",
        "Alumnos que realicen 7h/día (en total 49 días de formación): desde el 26 de febrero al 5 de junio de 2031"]


def test_titulos_que_no_se_quedan_solos(docx):
    for p in xml(docx).iter(W + "p"):
        st = p.find(f"{W}pPr/{W}pStyle")
        if st is not None and st.get(W + "val") in ("Ttulo2", "Ttulo3"):
            assert p.find(f"{W}pPr/{W}keepNext") is not None


def test_vista_previa_con_marca_borrador(prog, cat, curso):
    d = generar(prog, cat, curso, borrador=True)
    z = zipfile.ZipFile(io.BytesIO(d))
    cabeceras = [n for n in z.namelist() if re.fullmatch(r"word/header\d+\.xml", n)]
    con_marca = [n for n in cabeceras if b'string="BORRADOR"' in z.read(n)]
    assert con_marca and len(con_marca) < len(cabeceras)        # la portada (encabezado vacío), sin marca
    assert not any(b"BORRADOR" in zipfile.ZipFile(io.BytesIO(generar(prog, cat, curso))).read(n) for n in cabeceras)


def test_correo_del_pie_solo_si_se_da(prog, cat, curso):
    sin = zipfile.ZipFile(io.BytesIO(generar(prog, cat, curso))).read("word/footer2.xml")
    con = zipfile.ZipFile(io.BytesIO(generar(prog, cat, curso, correo_pie="departamento@example.com"))).read(
        "word/footer2.xml")
    assert b"@" not in sin and b"departamento@example.com" in con


def test_proyecto_con_la_totalidad_de_las_competencias(cat, curso):
    p = programacion.nueva("SEA", 2, "0526", "2030-2031", cat.version, "2026-10-06")
    d = generar(p, cat, curso)
    assert any("contribuye al desarrollo de la totalidad de las competencias profesionales, personales y sociales "
               "del título, de la a) a la r)" in t for t in parrafos(d, "3"))
    assert any("que da al módulo la denominación de «Proyecto intermodular»" in t for t in parrafos(d, "11"))


def test_ciclo_de_grado_medio_con_letras(cat, curso):
    codigo = next(m["codigo"] for m in cat.ciclo("GA")["modulos"] if m["tipo"] == "propio")
    p = programacion.nueva("GA", cat.ficha("GA", codigo).curso, codigo, "2030-2031", cat.version, "2026-10-06")
    d = generar(p, cat, curso)
    assert ["Ciclo Formativo:", "Grado Medio: / Gestión administrativa"] in tablas(d, "portada")[0].filas
    assert parrafos(d, "2.1")[1].startswith("a) ")                # GA: la competencia 1 es la a)
    assert any("Real Decreto 499/2024" in t for t in parrafos(d, "1.1"))
    assert not any("500/2024" in t for t in parrafos(d, "1.1"))


def test_enlazar_solo_las_normas_del_catalogo(cat):
    segs = documento.enlazar("Según el RD 1127/2010 y la Orden 99/1999, de prueba.", cat)
    assert segs[0] == "Según el " and isinstance(segs[1], Enlace) and segs[1].texto == "RD 1127/2010"
    assert segs[2] == " y la Orden 99/1999, de prueba."


def test_nombre_del_archivo(cat):
    assert documento.nombre_archivo(cat.ficha("ARI", "0959")) == \
        "ARI 1 - 0959 - Sistemas eléctricos, neumáticos e hidráulicos.docx"


@pytest.mark.parametrize("titulo, partes", [
    ("UD00. PRL ficticia", ("UD00.", " PRL ficticia")), ("Práctica 1: Montaje ficticio", ("Práctica 1:", " Montaje ficticio")),
    ("UT03.- Unidad ficticia", ("UT03.-", " Unidad ficticia")), ("Práctica sin código", ("", "Práctica sin código")),
])
def test_codigo_de_la_unidad_en_negrita(titulo, partes):
    assert documento.partir_titulo(titulo) == partes


def test_sin_identificadores_repetidos(docx):
    """Word da el documento por dañado con marcadores o párrafos con el mismo id (los copia la plantilla)."""
    d = xml(docx)
    ids = [b.get(W + "id") for b in d.iter(W + "bookmarkStart")]
    assert len(ids) == len(set(ids))
    para = [p.get("{http://schemas.microsoft.com/office/word/2010/wordml}paraId") for p in d.iter(W + "p")]
    para = [x for x in para if x]
    assert len(para) == len(set(para))


def test_pesos_ajustados_y_columna_del_curso(prog, cat, curso):
    prog["elementos"][0]["peso_ajustado"] = {"valor": 2.15}
    prog["elementos"][2]["peso_ajustado"] = {"valor": 4.2, "texto": "1,4 % / x práctica"}
    prog["columna_pct_curso"] = True
    d = generar(prog, cat, curso)
    filas = tablas(d, "4")[0].filas
    assert filas[1][4] == "2,15 %" and "1,4 % / x práctica" in [f[4] for f in filas if len(f) > 4]
    t41 = tablas(d, "4.1")[0].filas
    assert t41[0] == [*CABECERA_41, "% del curso (aprox.)"], "al final, sin romper la tabla"
    assert t41[1][-1] == "20,5 %" and t41[-1] == ["TOTAL", "103", "63", "", "100 %"]   # RA1: 34 h de 166
    t, filas = celdas_41(d)
    anchos = [int(g.get(W + "w")) for g in t.find(W + "tblGrid")]
    assert len(anchos) == 7 and sum(anchos) == 8896, "el ancho sale de la columna del RA"
    assert all(int(tr.findall(W + "tc")[0].find(f"{W}tcPr/{W}tcW").get(W + "w")) in (anchos[0], anchos[0] + anchos[1])
               for tr in filas)
    assert filas[1].findall(W + "tc")[-1].find(f".//{W}sz").get(W + "val") == "16", "letra más pequeña"


def test_variante_de_proyecto_de_la_plantilla(cat, curso):
    p = programacion.nueva("SEA", 2, "0526", "2030-2031", cat.version, "2026-10-06")
    p["elementos"] = [{"id": f"e{k}", "tipo": "T", "nombre": f"TAREA {k}", "ra": [2]} for k in range(1, 4)]
    p["unidades"] = [{"id": f"u{k}", "titulo": f"T0{k}. Tarea ficticia", "horas": 30 + k, "trimestre": 2,
                      "elemento": f"e{k}"} for k in range(1, 4)]
    d = generar(p, cat, curso)
    assert tablas(d, "4")[0].filas[0][0] == "TAREA (Item del proyecto)" and len(tablas(d, "4")) == 1
    assert any("tareas del proyecto (T01 a T03)" in t for t in parrafos(d, "11.1"))
    assert not any(t.startswith("Exámenes (E)") for t in parrafos(d, "11.2"))
    assert any("no se realizan exámenes ni prácticas de taller" in t for t in parrafos(d, "9"))
    otro = generar(programacion_ficticia(), cat, curso)
    assert tablas(otro, "4")[0].filas[0][0] == "UNIDAD DIDÁCTICA"
    assert any(t.startswith("Exámenes (E)") for t in parrafos(otro, "11.2"))


# Tipografía: nada en Times New Roman (CarlosFB, 2026-10-17)
PARTES_CON_TEXTO = r"word/(document|header\d+|footer\d+)\.xml"


def fuentes_de_la_plantilla():
    """Las fuentes con las que se ve el texto de la plantilla (cuerpo, encabezados y pies)."""
    from programaciones import ooxml
    pq = documento.cargar_plantilla()
    return {f for n in pq.partes if re.fullmatch(PARTES_CON_TEXTO, n) for f, _r, _t in ooxml.fuentes_de_texto(pq, n)}


@pytest.mark.parametrize("sigla, curso_m, modulo", [("SEA", 2, "0517"), ("SEA", 2, "0526"), ("CAR", 1, "0156")])
def test_ningun_texto_en_times_new_roman(cat, curso, sigla, curso_m, modulo):
    """Normal, Proyecto y GM, con un elemento de todos los RA («RA1 → RA6» en la tabla 4): cada run del documento y
    de los encabezados y pies resuelve (rFonts, estilo de carácter, de párrafo y docDefaults, en las ranuras ascii,
    hAnsi y eastAsia) a una fuente del texto de la plantilla, nunca a Times New Roman."""
    from conftest import programacion_minima
    from programaciones import ooxml
    permitidas = fuentes_de_la_plantilla()
    assert "Times New Roman" not in permitidas and "Calibri" in permitidas
    p = programacion_minima(cat, sigla, curso_m, modulo, "2030-2031")
    p["columna_pct_curso"] = True
    pq = ooxml.Paquete.desde_docx(documento.generar(p, cat, curso))
    if modulo == "0517":
        assert "→" in texto(pq.xml("word/document.xml")), "el caso de CarlosFB: «RA1 → RA6» en la tabla 4"
    for parte in [n for n in pq.partes if re.fullmatch(PARTES_CON_TEXTO, n)]:
        malas = [(f, r, t[:40]) for f, r, t in ooxml.fuentes_de_texto(pq, parte) if f not in permitidas]
        assert not malas, f"{parte}: {malas[:5]}"


def test_textos_del_profesor_y_propios_sin_times_new_roman(prog, cat, curso):
    """Metodología, recursos, espacios, notas y textos propios: la fuente de la plantilla."""
    from programaciones import ooxml
    prog["textos_propios"] = {"instrumentos": [{"texto": "Entrega de las tareas ficticias → rúbrica.", "nivel": 0}],
                              "calificacion": [{"texto": "La calificación ficticia sale de las tareas."}]}
    prog["actividades"] = [{"texto": "Visita ficticia a una obra · 2.º trimestre."}]
    pq = ooxml.Paquete.desde_docx(documento.generar(prog, cat, curso))
    permitidas = fuentes_de_la_plantilla()
    malas = [(f, r, t[:40]) for f, r, t in ooxml.fuentes_de_texto(pq) if f not in permitidas]
    assert not malas, malas[:5]
