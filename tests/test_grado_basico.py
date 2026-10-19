"""Grado Básico (F8, ADR-032): catálogo de los cuatro ciclos del centro, documento de sus módulos técnicos y, hasta
que llegue su plantilla, los ámbitos como «pendiente». Textos inventados en los lectores; el resto, del catálogo."""
import pytest

import catalogo
from conftest import programacion_minima
from programaciones import documento, programacion
from test_documento import generar, parrafos, secciones, tablas


# -- catálogo --------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("sigla, propios", [("EE", {"3013", "3014", "3015", "3016"}),
                                            ("IC", {"3015", "3016", "3029", "3030"}),
                                            ("MV", {"3043", "3044", "3045", "3046", "3047"}),
                                            ("SA", {"3001", "3002", "3003", "3004", "3005", "3006"})])
def test_los_cuatro_ciclos_de_gb(cat, sigla, propios):
    c = cat.ciclo(sigla)
    assert c["grado"] == "GB" and c["titulo"]["es"].startswith("Técnico Básico en ") and c["rd"]["anexo"]
    tipos = {m["codigo"]: m["tipo"] for m in c["modulos"]}
    assert {k for k, t in tipos.items() if t == "propio"} == propios
    assert {k for k, t in tipos.items() if t == "ambito"} == {"3161", "3162", "3163", "3164"}
    assert {k for k, t in tipos.items() if t == "tutoria"} == {"TU01CF", "TU02CF"}
    assert tipos["3159p"] == tipos["3159"] == "empleabilidad"
    assert sum(1 for t in tipos.values() if t == "proyecto") == 1
    for curso in (1, 2):   # cada curso, 30 h y 1.000 h con la tutoría (Decreto 95/2026)
        fs = [m for m in c["modulos"] if m["curso"] == curso]
        assert (sum(m["h_sem"] for m in fs), sum(m["h_anuales"] for m in fs)) == (30, 1000)
    ccs = [m for m in c["modulos"] if m["codigo"] in ("3161", "3162")]
    assert all(sum(p["h_anuales"] for p in m["partes"]) == m["h_anuales"] for m in ccs)
    assert {e["uc"] for f in c["correspondencias_ecp"] for e in f["ecp"]} and c["competencias"]


def test_ambitos_con_competencias_especificas(cat):
    for codigo, (ambito, _curso) in catalogo.AMBITOS.items():
        m = cat.modulo(codigo)
        assert m["tipo"] == "ambito" and m["ra"] == [] and len(m["ce"]) == 8 and m["ambito"]["es"] == ambito
        assert all(c["descriptores"] and c["criterios"] for c in m["ce"])
        assert all(x["n"].startswith(f"{c['n']}.") for c in m["ce"] for x in c["criterios"])
    assert [len(c["criterios"]) for c in cat.modulo("3164")["ce"]] == [2, 4, 3, 2, 3, 1, 1, 2]


def test_modulos_comunes_de_gb(cat):
    assert len(cat.modulo("3159")["ra"]) == 9          # Decreto 117/2025, anexo I (la CV añade PRL y derechos)
    assert len(cat.modulo("3160")["ra"]) == 5          # RD 498/2024, anexo I
    assert "q" in cat.modulo("3013")["competencias_modulo"]["EE"], "también las transversales de las orientaciones"


def test_lectores_de_gb_con_textos_inventados():
    lineas = ["   FAMILIA: FICTICIA", "   Ciclo ficticio",
              "   Ámbito                   Materia                         Hrs/sem Hrs/año",
              "                            Lengua ficticia I               1       33",
              "      Comunicación y        Lengua extranjera de iniciación 1       33",
              "                            profesional I",
              "     Ciencias Sociales I     Otra materia I                  2       67"]

    class Doc:
        id = "ficticio"
        def __init__(self, lineas):
            self.lineas = ["ANEXO VI. Modificación del Decreto 117/2025", "ANEXO III-B. Organización del ámbito"] + lineas

        def buscar(self, patron, desde=0):
            import re
            return next(k for k in range(desde, len(self.lineas)) if re.search(patron, self.lineas[k]))
    m = catalogo.materias_ccs(Doc(lineas), "Ciclo ficticio")
    assert [x["nombre"] for x in m[1]] == ["Lengua ficticia I", "Lengua extranjera de iniciación profesional I",
                                          "Otra materia I"]
    assert [x["h_anuales"] for x in m[1]] == [33, 33, 67]


# -- documento de un módulo técnico de GB ----------------------------------------------------------------------------
@pytest.fixture
def docx_gb(cat, curso):
    return generar(programacion_minima(cat, "EE", 2, "3016"), cat, curso)


def test_portada_y_referencias_al_anexo_del_titulo(docx_gb):
    assert ["Ciclo Formativo:", "Grado Básico: / Electricidad y electrónica"] in tablas(docx_gb, "portada")[0].filas
    p2 = " ".join(parrafos(docx_gb, "2"))
    assert "Real Decreto 127/2014, de 28 de febrero, en su anexo II, en su redacción vigente" in p2
    assert "apartado 6 bis del anexo II del Real Decreto 127/2014, añadido por el Real Decreto 498/2024" in p2
    assert "Según el apartado 2.1 del anexo II del" in p2 and "anexo V B)" not in p2
    assert any(t.startswith("De acuerdo con el apartado 2.2 del anexo II del") for t in parrafos(docx_gb, "2.1"))
    assert any("orientaciones pedagógicas del anexo II del" in t for t in parrafos(docx_gb, "3"))


def test_el_documento_de_gb_pasa_las_comprobaciones_de_exportacion(docx_gb):
    """Sin el 2.2 de optativos (por diseño) y con las normas que cita el título del RD 127/2014 enlazadas."""
    from programaciones import exportacion

    assert exportacion.problemas(docx_gb) == []


def test_la_errata_cl3_se_corrige_en_la_ficha_y_el_catalogo_guarda_el_literal(cat):
    """Dudas del catálogo de GB (CarlosFB, 2026-10-19): el literal del BOE en el catálogo, la corrección en la app."""
    for codigo, curso in (("3161", 1), ("3162", 2)):
        assert "CL3" in cat.modulo(codigo)["ce"][3]["descriptores"]
        d = cat.ficha("EE", codigo, curso).descriptores[4]
        assert "CCL3" in d and "CL3" not in d


def test_en_gb_el_decreto_del_curriculo_es_el_117(docx_gb, cat, curso):
    """El 9.1 de la plantilla cita el Decreto 114/2025 (GM y GS); en GB pasa a ser el 117/2025, con su enlace."""
    from programaciones import contenido
    from programaciones.ooxml import R, W

    texto = " ".join(parrafos(docx_gb, "9.1"))
    assert "Decreto 117/2025" in texto and "Decreto 114/2025" not in " ".join(p for s in secciones(docx_gb)
                                                                           for p in parrafos(docx_gb, s))
    d = contenido.documento_xml(docx_gb)
    import zipfile
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(docx_gb)) as z:
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    destinos = {m.group(1): m.group(2) for m in
                __import__("re").finditer(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels)}
    enlaces_117 = [h for h in d.iter(W + "hyperlink")
                   if "Decreto 117/2025" in "".join(t.text or "" for t in h.iter(W + "t"))]
    assert enlaces_117 and all(destinos[h.get(R + "id")] == cat.norma("DOGV-C-2025-32763").enlace for h in enlaces_117)
    # en GS sigue el 114/2025
    gs = generar(programacion_minima(cat, "SEA", 2, "0517"), cat, curso)
    assert "Decreto 114/2025" in " ".join(parrafos(gs, "9.1"))


def test_la_norma_citada_solo_se_enlaza_y_no_va_en_las_listas(cat):
    n = cat.normas["BOE-A-2009-20651"]
    assert n.aplica == "citada" and not n.aplica_a("SA", "GB") and not n.aplica_a("SEA", "GS")


def test_sin_optativos_ni_su_entrada_en_el_indice(docx_gb, cat, curso):
    assert "2.2" not in __import__("test_documento").secciones(docx_gb)
    gs = generar(programacion_minima(cat, "SEA", 2, "0517"), cat, curso)
    indice = lambda d: [t for t in parrafos(d, "indice") if "optativos" in t.lower()]  # noqa: E731
    assert "2.2" in __import__("test_documento").secciones(gs) and not indice(docx_gb)


def test_normativa_de_grado_basico(docx_gb):
    estatal, autonomica = " ".join(parrafos(docx_gb, "1.1")), " ".join(parrafos(docx_gb, "1.2"))
    assert "Real Decreto 217/2022" in estatal and "Real Decreto 498/2024" in estatal
    assert "Real Decreto 499/2024" not in estatal and "Real Decreto 500/2024" not in estatal
    assert "Decreto 117/2025" in autonomica and "Decreto 114/2025" not in autonomica


def test_gb_espera_los_periodos_de_empresa_de_primero_y_tiene_los_de_segundo(cat):
    """2026-2027: la FE de 1.º de GB no está en el calendario del centro y la definitiva espera (V-11); la de 2.º salió
    de la plantilla 3016 del departamento (CarlosFB, 2026-10-19): 35 días a 8 h, del 1 de marzo al 30 de abril."""
    from programaciones import documento, validacion
    curso = cat.curso_escolar("2026-2027")
    p = programacion_minima(cat, "SA", 1, "3001")
    avisos = validacion.validar(p, cat.ficha("SA", "3001", 1),
                                curso_pendiente=documento.pendiente_curso(curso, "SA", 1))
    assert any(a.id == "V-11" and "1.º de Grado Básico" in a.mensaje for a in avisos)
    for sigla, codigo in (("EE", "3016"), ("IC", "3016"), ("MV", "3046"), ("SA", "3002")):
        assert documento.pendiente_curso(curso, sigla, 2) == ""
        periodos = documento.periodos_empresa(curso, cat.ficha(sigla, codigo, 2))
        assert [(x["jornada"], x["dias"], str(x["desde"]), str(x["hasta"])) for x in periodos] == \
            [(8, 35, "2027-03-01", "2027-04-30")]


# -- app ---------------------------------------------------------------------------------------------------------------
def test_lista_sin_tutoria(contexto):
    gb = [m for m in contexto.modulos if m.grado == "GB"]
    assert gb and not any(m.codigo.startswith("TU") for m in gb)
    assert not any(m.pendiente for m in gb if m.codigo in catalogo.AMBITOS or m.codigo == "3016")


@pytest.mark.parametrize("sigla, curso_m, codigo, cita", [
    ("EE", 2, "3160956", "anexo I del Real Decreto 498/2024, de 21 de mayo"),
    ("EE", 2, "3159", "anexo I del Decreto 117/2025, de 5 de agosto"),
    ("SEA", 1, "1709", "anexo V del Decreto 114/2025, de 29 de julio"),     # GS: el mismo arreglo
])
def test_modulos_cuyo_curriculo_no_esta_en_el_titulo(cat, sigla, curso_m, codigo, cita):
    """Los comunes y el Proyecto de GB citan la norma que trae su currículo en los apartados 3 y 11."""
    curso = cat.curso_escolar("2026-2027")
    d = generar(programacion_minima(cat, sigla, curso_m, codigo), cat, curso)
    tres = next(t for t in parrafos(d, "3") if t.startswith("De acuerdo con las previsiones"))
    once = next(t for t in parrafos(d, "11") if t.startswith("Siguiendo"))
    assert cita in tres and f"y el {cita}, que establece el currículo de este módulo" in once
    assert "  " not in tres and "Proyecto intermodular» y mantiene" not in once


# -- ámbitos (0.7.0, ADR-032) -----------------------------------------------------------------------------------------
def programacion_ambito(cat, sigla="EE", curso=2, codigo="3164"):
    """Un ámbito con dos partes inventadas, una unidad por parte y un elemento con CE."""
    p = programacion.nueva(sigla, curso, codigo, "2026-2027", cat.version, "2026-10-17")
    h = cat.ficha(sigla, codigo, curso).horas
    p["profesorado"] = ["Profesora Ficticia Uno"]
    p["partes"] = [{"id": "p1", "nombre": "Parte ficticia A", "horas": h - 60},
                   {"id": "p2", "nombre": "Parte ficticia B", "horas": 60}]
    p["elementos"] = [{"id": "e1", "tipo": "E", "nombre": "Tareas ficticias", "ra": [1, 2, 3, 4]},
                      {"id": "e2", "tipo": "E", "nombre": "Examen ficticio", "ra": [5, 6, 7, 8]}]
    p["unidades"] = [{"id": "u1", "titulo": "Unidad ficticia A", "horas": h - 60, "trimestre": [1, 2],
                      "elemento": "e1", "parte": "p1"},
                     {"id": "u2", "titulo": "Unidad ficticia B", "horas": 60, "trimestre": 3, "elemento": "e2",
                      "parte": "p2"}]
    p["bloques"] = {b: "confirmado" for b in p["bloques"]}
    return p


def test_partes_propuestas(cat):
    from programaciones import propuesta
    ccs = propuesta.partes(cat.ficha("EE", "3162", 2))
    assert [x["nombre"] for x in ccs][0] == "Lengua castellana II" and sum(x["horas"] for x in ccs) == 166
    ca = propuesta.partes(cat.ficha("EE", "3164", 2))
    assert ca == [{"id": "p1", "nombre": "Matemáticas II", "horas": 100}, {"id": "p2", "nombre": "Ciencias II", "horas": 66}]
    us = propuesta.unidades(cat.ficha("EE", "3164", 2), ca)
    assert len(us) == 11 and {u["parte"] for u in us} == {""}, "con dos partes, las reparte el profesor"
    us = propuesta.unidades(cat.ficha("EE", "3162", 2), ccs)
    assert {u["parte"] for u in us} == {""}, "con varias partes, las reparte el profesor"


def test_ciencias_aplicadas_en_matematicas_y_ciencias_por_horas_semanales(cat):
    """ADR-039: 5 h → 3 + 2 (el modelo del departamento: 99 + 66 de 166, que no cuadraba); 4 h → 2 + 2. Siempre suma
    las horas del ámbito."""
    from programaciones import propuesta

    vistos = set()
    for sigla in ("EE", "IC", "MV", "SA"):
        for codigo, curso in (("3163", 1), ("3164", 2)):
            f = cat.ficha(sigla, codigo, curso)
            ps = propuesta.partes(f)
            n = "I" if curso == 1 else "II"
            assert [p["nombre"] for p in ps] == [f"Matemáticas {n}", f"Ciencias {n}"]
            assert sum(p["horas"] for p in ps) == f.horas
            esperado = {(5, 166): (100, 66), (4, 133): (67, 66)}[(f.h_sem, f.horas)]
            assert (ps[0]["horas"], ps[1]["horas"]) == esperado
            vistos.add(f.h_sem)
    assert vistos == {4, 5}, "hay ciclos con el ámbito en 4 h y en 5 h semanales"


def test_avisos_de_las_partes(cat):
    from programaciones import validacion
    ficha = cat.ficha("EE", "3164", 2)
    p = programacion_ambito(cat)
    avisos = validacion.validar(p, ficha)
    assert not validacion.bloquean(avisos), [a.mensaje for a in avisos]
    assert not {"V-04", "V-07", "V-10", "V-13"} & {a.id for a in avisos}
    p["unidades"][1]["parte"] = ""
    p["partes"][0]["horas"] += 1
    mensajes = [a.mensaje for a in validacion.validar(p, ficha) if a.id == "V-14"]
    assert any("sin parte" in m for m in mensajes) and any("Las partes suman 167 h" in m for m in mensajes)
    p["elementos"][1]["ra"] = []
    assert any(a.id == "V-02" and a.mensaje.startswith("CE5") for a in validacion.validar(p, ficha))


def test_herencia_de_un_ambito(cat):
    from programaciones import herencia
    h = herencia.heredar(programacion_ambito(cat), cat, "2027-2028")
    assert [x["nombre"] for x in h.programacion["partes"]] == ["Parte ficticia A", "Parte ficticia B"]


@pytest.fixture
def docx_ambito(cat):
    return generar(programacion_ambito(cat), cat, cat.curso_escolar("2026-2027"))


def test_documento_de_un_ambito(docx_ambito, cat):
    from test_documento import secciones
    sec = secciones(docx_ambito)
    assert ["Ciclo Formativo:", "Grado Básico: / Electricidad y electrónica"] in tablas(docx_ambito, "portada")[0].filas
    assert any(f[0].startswith("Ámbito") for f in tablas(docx_ambito, "portada")[0].filas)
    dos = parrafos(docx_ambito, "2")
    assert any(t.startswith("CE1. Reconocer los motivos") for t in dos)
    assert any(t.startswith("Descriptores del perfil de salida: CCL1, STEM1") for t in dos)
    assert any(t.startswith("4.1 Evaluar los efectos") for t in dos), "criterios oficiales, con su número"
    t3 = tablas(docx_ambito, "3")
    assert len(t3) == 2 and t3[0].filas[1][:3] == ["Tareas ficticias", "Unidad ficticia A", "CE1, CE2, CE3 y CE4"]
    assert [x for x in t3[1].filas[-1] if x][:2] == ["TOTAL", "60"]
    t31 = tablas(docx_ambito, "3.1")
    assert [f[1] for f in t31[1].filas[1:-1]] == ["15", "15", "15", "15"] and t31[1].filas[-1][-1] == "60"
    ocho = " ".join(parrafos(docx_ambito, "8"))
    assert "Insuficiente (IN)" in ocho and "Suficiente (SU)" in ocho and "igual o superior a 5" not in ocho
    assert "9.1" not in sec and "4.1" in sec and "11" in sec and "12" not in sec
    todo = " ".join(" ".join(parrafos(docx_ambito, k)) for k in sec)
    assert "R.A." not in todo and "Formación en Empresa" not in todo and "{{" not in todo


def test_un_ambito_exportado_se_importa_con_sus_partes(cat):
    from programaciones import documento, importar_docx, incrustar
    p = programacion_ambito(cat)
    exportado = incrustar.incrustar(documento.generar(p, cat, cat.curso_escolar("2026-2027")), p)
    assert importar_docx.importar(exportado, cat, "EE 2 - 3164 - Ciencias Aplicadas II.docx") == p


def test_tabla_de_fechas_de_un_ambito_con_las_convocatorias_en_corto(docx_ambito, cat):
    """Las convocatorias, como las evaluaciones de las filas de encima («08/06/2027»; CarlosFB, 2026-10-18)."""
    curso = cat.curso_escolar("2026-2027")
    filas = [f for t in (e for v in secciones(docx_ambito).values() for e in v if e.tipo == "tabla") for f in t.filas]
    fechas = {f[0]: f[1] for f in filas if len(f) > 1 and f[0].startswith("CONVOCATORIA")}
    corta = documento.fecha_corta
    assert fechas["CONVOCATORIA ORDINARIA"] == corta(curso["evaluaciones"]["ordinaria"])
    assert fechas["CONVOCATORIA EXTRAORDINARIA"] == corta(curso["evaluaciones"]["extraordinaria"])
