"""Catálogo: lectores del BOE y del DOGV, comprobación y comparación con una programación.

Los textos de ejemplo son ficticios: imitan la forma del BOE y del DOGV (también sus erratas), no su contenido.
"""
import copy
import zipfile

import pytest
import yaml

import catalogo
from catalogo import (
    anexo_vb,
    aplicar_correcciones,
    comparar,
    competencias_titulo,
    comprobar,
    con_letras,
    escribir_yaml,
    horario,
    leer_ra,
    leer_yaml,
    modulos_boe,
    titulo_dogv,
    trocear,
)

HUELLA = "sha256:" + "1" * 64


# ---------------------------------------------------------------------------------------------------------------------
# El catálogo del repositorio
# ---------------------------------------------------------------------------------------------------------------------
def test_catalogo_del_repositorio_limpio():
    """Criterio de cierre de F1: `catalogo.py comprobar` sin errores."""
    assert comprobar() == []


def test_once_ciclos_con_sus_cursos():
    for sigla in catalogo.CICLOS:
        c = leer_yaml(catalogo.CATALOGO / "ciclos" / f"{sigla}.yaml")
        assert {m["curso"] for m in c["modulos"]} == {1, 2}
        assert c["grado"] == catalogo.CICLOS[sigla]["grado"]


def test_ningun_dato_sin_fuente():
    fuentes = {f["id"] for f in leer_yaml(catalogo.CATALOGO / "fuentes.yaml")["fuentes"]}
    for p in (catalogo.CATALOGO / "modulos").glob("*.yaml"):
        assert leer_yaml(p)["fuente"]["norma"] in fuentes, p.name


def test_codigos_entre_comillas_en_el_yaml():
    """Un código con cero delante («0518») tiene que leerse como texto también con un lector YAML 1.2."""
    for p in (catalogo.CATALOGO / "ciclos").glob("*.yaml"):
        texto = p.read_text(encoding="utf-8")
        assert "codigo: 0" not in texto and "- 0" not in texto.replace("- '0", ""), p.name


# ---------------------------------------------------------------------------------------------------------------------
# Lector del BOE
# ---------------------------------------------------------------------------------------------------------------------
def p(texto, clase=""):
    return {"tipo": "p", "clase": clase, "texto": texto}


def test_leer_ra_formato_actual():
    ra = leer_ra([
        "Resultados de aprendizaje y criterios de evaluación.",
        "1. Monta instalaciones ficticias, aplicando técnicas de prueba.",
        "Criterios de evaluación:",
        "a) Se ha preparado el material de prueba.",
        "b) Se han montado los elementos de prueba.",
        "2. Verifica instalaciones ficticias.",
        "Criterios de evaluación:",
        "a) Se han medido los parámetros de prueba.",
        "Duración: 100 horas.",
        "1. Esto ya no es un RA.",
    ])
    assert [r["n"] for r in ra] == [1, 2]
    assert [c["letra"] for c in ra[0]["criterios"]] == ["a", "b"]
    assert ra[1]["criterios"][0]["texto"] == "Se han medido los parámetros de prueba."


def test_leer_ra_parrafos_juntos_como_en_los_boe_de_2008():
    ra = leer_ra([
        "Resultados de aprendizaje y criterios de evaluación. 1. Identifica elementos ficticios. Criterios de "
        "evaluación: a) Se ha analizado la norma ficticia.",
        "b) Se han identificado las zonas de prueba. c) Se han descrito los tipos de prueba sin punto final "
        "d) Se ha determinado la función de prueba.",
        "2. Configura pequeñas instalaciones ficticias. Criterios de evaluación:",
        "a) Se han identificado las especificaciones de prueba.",
    ])
    assert [len(r["criterios"]) for r in ra] == [4, 1]
    assert ra[0]["criterios"][2]["texto"] == "Se han descrito los tipos de prueba sin punto final"


def test_leer_ra_criterios_sin_letra_o_con_guion():
    ra = leer_ra([
        "1. Planifica un trabajo ficticio.", "Criterios de evaluación:",
        "Se han secuenciado las tareas de prueba.", "− Se han determinado los recursos de prueba.",
    ])
    assert [(c["letra"], c["texto"]) for c in ra[0]["criterios"]] == [
        ("a", "Se han secuenciado las tareas de prueba."), ("b", "Se han determinado los recursos de prueba.")]


def test_leer_ra_erratas_de_numeracion():
    """Un número repetido, una letra fuera de sitio o un RA sin punto: la posición manda y lo impreso se guarda."""
    ra = leer_ra([
        "1. Monta algo ficticio.", "a) Se ha montado.", "b) Se ha probado.", "ñ) Se ha revisado.",
        "2. Repara algo ficticio.", "a) Se ha reparado.",
        "2. Diagnostica algo ficticio.", "a) Se ha diagnosticado.",
        "4 Mantiene algo ficticio.", "a) Se ha mantenido.", "c) Se ha limpiado.",
    ])
    assert [r["n"] for r in ra] == [1, 2, 3, 4]
    assert ra[2]["n_boe"] == 2 and "n_boe" not in ra[1]
    assert ra[0]["criterios"][2] == {"letra": "c", "letra_boe": "ñ", "texto": "Se ha revisado."}
    assert ra[3]["criterios"][1] == {"letra": "b", "letra_boe": "c", "texto": "Se ha limpiado."}


def test_un_numero_que_no_es_ra_se_queda_en_el_texto():
    ra = leer_ra(["1. Calcula algo ficticio.", "a) Se ha calculado según la norma", "7. de la tabla ficticia."])
    assert len(ra) == 1
    assert ra[0]["criterios"][0]["texto"] == "Se ha calculado según la norma 7. de la tabla ficticia."


def test_trocear():
    assert trocear("1. Uno ficticio. Criterios de evaluación: a) Se ha hecho. b) Se ha probado.") == [
        "1. Uno ficticio.", "a) Se ha hecho.", "b) Se ha probado."]


def test_modulos_boe_nombre_codigo_y_competencias():
    elems = [
        p("Módulo Profesional: Módulo ficticio uno. Código: 0991"),
        p("Resultados de aprendizaje y criterios de evaluación."),
        p("1. Hace algo ficticio."), p("a) Se ha hecho."),
        p("Orientaciones pedagógicas."),
        p("La formación del módulo contribuye a alcanzar los objetivos generales a) y b) del ciclo formativo y las "
          "competencias b), d) y ñ) del título."),
        p("Módulo Profesional: Módulo ficticio dos."), p("Equivalencia en créditos ECTS: 5"), p("Código: 0992."),
        p("1. Hace otra cosa ficticia."), p("a) Se ha hecho otra cosa."),
        p("La formación del módulo contribuye a alcanzar el objetivo general n) del ciclo formativo y la competencia n) del título."),
        p("Módulo Profesional: Módulo ficticio tres."), p("Código: 0993"),
        p("1. Integra lo ficticio."), p("a) Se ha integrado."),
        p("La formación del módulo contribuye a alcanzar todos los objetivos generales del ciclo formativo y todas las competencias del título."),
        p("ANEXO II", "anexo_num"),
    ]
    m = modulos_boe(elems)
    assert m["0991"]["nombre"] == "Módulo ficticio uno" and m["0991"]["competencias"] == ["b", "d", "ñ"]
    assert m["0992"]["nombre"] == "Módulo ficticio dos" and m["0992"]["competencias"] == ["n"]
    assert m["0993"]["competencias"] == ["todas"]
    assert m["0991"]["huella"] != m["0992"]["huella"]


def test_competencias_con_letras_y_con_numeros():
    letras = [p("Artículo 5. Competencias profesionales, personales y sociales."),
              p("Las competencias de este título son las que se relacionan a continuación: a) Montar algo ficticio."),
              p("b) Revisar algo ficticio. c) Mantener algo ficticio."), p("Artículo 6. Relación de cualificaciones.")]
    assert [x["letra"] for x in competencias_titulo(letras)] == ["a", "b", "c"]
    numeros = [p("Artículo 5. Competencias profesionales, personales y sociales."), p("Las competencias:"),
               p("1. Tramitar algo ficticio."), p("2. Archivar algo ficticio."), p("Artículo 6. Relación.")]
    assert [x["letra"] for x in competencias_titulo(numeros)] == ["1", "2"]


def test_modulo_de_proyecto_con_la_totalidad_de_las_competencias():
    elems = [p("Módulo Profesional: Proyecto ficticio. Código: 0994"), p("1. Diseña algo ficticio."),
             p("a) Se ha diseñado."), p("Orientaciones pedagógicas."),
             p("Este módulo complementa la formación de otros módulos.La formación del módulo se relaciona con la "
               "totalidad de los objetivos generales del ciclo y las competencias profesionales, personales y sociales "
               "del título."), p("ANEXO II", "anexo_num")]
    assert modulos_boe(elems)["0994"]["competencias"] == ["todas"]


def test_competencias_numeradas_pasan_a_letras_con_la_enye():
    numeradas = [{"letra": str(n), "texto": f"Competencia ficticia {n}."} for n in range(1, 17)]
    letras = con_letras(numeradas)
    assert [c["letra"] for c in letras][13:16] == ["n", "ñ", "o"]
    assert letras[0] == {"letra": "a", "numero_boe": 1, "texto": "Competencia ficticia 1."}
    assert con_letras([{"letra": "a", "texto": "x"}]) == [{"letra": "a", "texto": "x"}]


def test_titulo_dogv_con_y_sin_codigo_de_insercion():
    antigua = ("Núm. 1 / 01.01.2019 ORDRE 1/2019, de prova. [2019/1] Conselleria ficticia ORDEN 1/2019, de 2 de enero, "
               "de la Conselleria ficticia, por la cual se regula algo ficticio. [2019/1] ÍNDEX ÍNDICE Preámbulo")
    assert titulo_dogv(antigua) == "ORDEN 1/2019, de 2 de enero, de la Conselleria ficticia, por la cual se regula algo ficticio."
    assert titulo_dogv("DECRETO 1/2026, de 2 de enero, del Consell, ficticio. Preámbulo") == \
        "DECRETO 1/2026, de 2 de enero, del Consell, ficticio."


def test_correcciones_de_erratas_guardan_literal_y_corregido():
    modulos = {"0991": {"ra": _ra()}}
    aplicar_correcciones(modulos, {("0991", 1, "b"): ("hecho 1", "hecho uno", "Errata ficticia de prueba"),
                                   ("0991", 2, None): ("algo", "alguna cosa", "Errata ficticia de prueba")})
    crit = modulos["0991"]["ra"][0]["criterios"][1]
    assert crit["texto"]["es"] == "Se ha hecho 1." and crit["corregido"]["es"] == "Se ha hecho uno."
    assert modulos["0991"]["ra"][1]["corregido"]["es"] == "Hace alguna cosa ficticio 2."


@pytest.mark.parametrize("clave, fragmento", [(("0991", 1, "b"), "no está"), (("0999", 1, "a"), "hecho"),
                                               (("0991", 1, "z"), "hecho")])
def test_correccion_que_no_casa_para_la_construccion(clave, fragmento):
    with pytest.raises(SystemExit):
        aplicar_correcciones({"0991": {"ra": _ra()}}, {clave: (fragmento, "x", "Errata ficticia de prueba")})


def test_correccion_de_un_texto_del_ciclo():
    corr = {("ZZ", "competencia_general"): ("ficticia.Consiste", "ficticia. Consiste", "Errata ficticia de prueba")}
    assert catalogo.corregir_ciclo("ZZ", "competencia_general", "Es ficticia.Consiste en algo.", corr) == {
        "competencia_general_corregida": {"es": "Es ficticia. Consiste en algo."},
        "competencia_general_correccion": "Errata ficticia de prueba"}
    assert catalogo.corregir_ciclo("YY", "competencia_general", "Otro texto.", corr) == {}
    with pytest.raises(SystemExit):
        catalogo.corregir_ciclo("ZZ", "competencia_general", "Sin la errata.", corr)


def test_proyecto_intermodular_de_gm_del_anexo_ii_del_rd_499():
    """Los RA del 1713 (antes «pendiente»): anexo II del RD 499/2024, uno para los cinco ciclos de GM; el RA5 repite la
    letra a) en el BOE y se guarda su letra impresa."""
    from programaciones.catalogo import Catalogo

    cat = Catalogo()
    m = cat.modulo("1713")
    assert m["fuente"]["norma"] == "BOE-A-2024-10684" and m["fuente"]["bloque"] == "Anexo II, módulo 1713"
    assert [len(r["criterios"]) for r in m["ra"]] == [9, 11, 9, 6, 4]
    assert [(c["letra"], c.get("letra_boe")) for c in m["ra"][4]["criterios"]] == [
        ("a", None), ("b", "a"), ("c", "b"), ("d", "c")]
    for sigla in ("GA", "IT", "IEA", "CAR", "EMV"):
        pr = next(x for x in cat.ciclo(sigla)["modulos"] if x["tipo"] == "proyecto")
        assert pr["modulo"] == "1713" and "pendiente" not in pr
        assert set(m["competencias_modulo"][sigla]) == {c["letra"] for c in cat.ciclo(sigla)["competencias"]}


def test_erratas_del_catalogo_del_repositorio():
    """Las cuatro erratas que corrigen las programaciones, la del enunciado del RA4 de 0959 y la UC0626_3 de EMV (solo
    posición y código)."""
    for (ident, n, letra), (_viejo, _nuevo, _motivo) in catalogo.CORRECCIONES.items():
        ra = next(r for r in leer_yaml(catalogo.CATALOGO / "modulos" / f"{ident}.yaml")["ra"] if r["n"] == n)
        elem = ra if letra is None else next(c for c in ra["criterios"] if c["letra"] == letra)
        assert elem["corregido"]["es"] != elem["texto"]["es"] and elem["correccion"]
    sea = leer_yaml(catalogo.CATALOGO / "ciclos" / "SEA.yaml")
    assert "(REBT). También" in sea["competencia_general_corregida"]["es"]
    assert "(REBT).También" in sea["competencia_general"]["es"]
    emv = leer_yaml(catalogo.CATALOGO / "ciclos" / "EMV.yaml")
    ecp = [e for c in emv["correspondencias_ecp"] for e in c["ecp"] if e.get("uc_boe")]
    assert [(e["codigo"], e["uc"], e["uc_boe"]) for e in ecp] == [("ECP0626_2", "UC0626_2", "UC0626_3")]


def test_ga_e_it_con_letras():
    for sigla in ("GA", "IT"):
        c = leer_yaml(catalogo.CATALOGO / "ciclos" / f"{sigla}.yaml")
        assert c["competencias"][0]["letra"] == "a" and c["competencias"][0]["numero_boe"] == 1
        assert "pendiente_competencias" not in c


def test_anexo_vb_tabla_con_titulo_dentro():
    elems = [{"tipo": "tabla", "clase": "", "texto": "Anexo V.B) Correspondencia…", "filas": [
        ["Anexo V.B) Correspondencia de los módulos profesionales con las unidades de competencia"],
        ["Módulos profesionales superados", "Unidades de competencia acreditables"],
        ["0991. Módulo ficticio uno. 0992. Módulo ficticio dos.",
         "UC0001_2: Montar algo ficticio. UC0002_2 Mantener algo ficticio."],
    ]}]
    assert anexo_vb(elems) == [{"modulos": ["0991", "0992"],
                                "uc": [("0001_2", "Montar algo ficticio."), ("0002_2", "Mantener algo ficticio.")]}]


# ---------------------------------------------------------------------------------------------------------------------
# Lector del DOGV (horario del Decreto 95/2026)
# ---------------------------------------------------------------------------------------------------------------------
class DogvFicticio(catalogo.Dogv):
    def __init__(self, lineas):
        self.id, self.lineas = "DOGV-C-2000-1", lineas


HORARIO = """
              ANEXO IV. Modificación de los anexos I y II del Decreto 114/2025, de 29 de julio, del
                                     ANEXO I. Secuenciación y horario GM
                                    ANEXO II. Secuenciación y horario GS
                 Ciclo ficticio
                 1º       0179       Inglés profesional GS                                                 2      67
                          0991       Módulo ficticio uno                                                  25     833
                                     Módulo ficticio con un nombre tan largo que no cabe en una
                          0992p                                                                            3     100
                                     sola línea
               Total 1º                                                                                    30   1.000
                 2º       0993       Módulo ficticio tres                                                 26     866
                          CVOPS999   Módulo optativo                                                       3     100
                          1665999    Digitalización aplicada al sistema productivo GS                       1      34
               Total 2º                                                                                    30   1.000
                   Total ciclo                                                                             60   2.000
              ANEXO V. Incorporación de un nuevo anexo XII
""".splitlines()


def test_horario_con_nombres_partidos():
    h = horario(DogvFicticio(HORARIO), "Ciclo ficticio", "GS")
    assert [(f["codigo"], f["curso"], f["h_sem"], f["h_anuales"]) for f in h["filas"]] == [
        ("0179", 1, 2, 67), ("0991", 1, 25, 833), ("0992p", 1, 3, 100),
        ("0993", 2, 26, 866), ("CVOPS999", 2, 3, 100), ("1665999", 2, 1, 34)]
    assert h["filas"][2]["nombre"] == "Módulo ficticio con un nombre tan largo que no cabe en una sola línea"
    assert h["totales"] == {1: (30, 1000), 2: (30, 1000)}


def test_tipo_y_archivo_de_cada_codigo():
    assert catalogo.tipo_de("1665031", "") == "digitalizacion" and catalogo.base_de("1665031", "digitalizacion") == "1665"
    assert catalogo.tipo_de("1708031", "") == "sostenibilidad"
    assert catalogo.tipo_de("0526p", "Proyecto intermodular de algo") == "proyecto"
    assert catalogo.base_de("0526p", "proyecto") == "0526"
    assert catalogo.tipo_de("CVOPS031", "Módulo optativo") == "optativo" and catalogo.base_de("CVOPS031", "optativo") is None
    assert catalogo.tipo_de("CV0015", "") == "autonomico"
    assert catalogo.tipo_de("1713472", "Proyecto intermodular") == "proyecto"


def test_yaml_codigos_y_fechas_como_texto(tmp_path):
    datos = {"codigo": "0518", "otro": "1665031", "fecha": "2026-10-17", "texto": "Algo ficticio", "n": 3}
    escribir_yaml(tmp_path / "x.yaml", datos)
    texto = (tmp_path / "x.yaml").read_text(encoding="utf-8")
    assert "codigo: '0518'" in texto and "fecha: '2026-10-17'" in texto
    assert yaml.safe_load(texto) == datos


# ---------------------------------------------------------------------------------------------------------------------
# Comprobación sobre un catálogo ficticio
# ---------------------------------------------------------------------------------------------------------------------
def _ra(n_ra=2, n_ce=2):
    return [{"n": i + 1, "texto": {"es": f"Hace algo ficticio {i + 1}."},
             "criterios": [{"letra": "abcdefgh"[k], "texto": {"es": f"Se ha hecho {k}."}} for k in range(n_ce)]}
            for i in range(n_ra)]


def _fuente():
    return {"norma": "BOE-A-2000-1", "bloque": "Anexo I", "version": "2000-01-01", "huella": HUELLA, "comprobado": "2026-10-17"}


def catalogo_ficticio(tmp_path):
    raiz = tmp_path / "catalogo"
    t = {"es": "Ficticio"}
    escribir_yaml(raiz / "fuentes.yaml", {"formato": "catalogo/4", "fuentes": [
        {"id": "BOE-A-2000-1", "tipo": "boe", "titulo": t, "url": "https://example.com/x", "enlace": "https://example.com/y",
         "publicado": "2000-01-01", "huella": HUELLA, "consultado": "2026-10-17"}]})
    for codigo in ("0991", "0992"):
        escribir_yaml(raiz / "modulos" / f"{codigo}.yaml", {
            "formato": "catalogo/4", "id": codigo, "codigo": codigo, "nombre": t, "tipo": "propio",
            "competencias_modulo": {"ZZ": ["a"]}, "ra": _ra(), "fuente": _fuente()})
    mod = {"nombre": t, "tipo": "propio"}
    escribir_yaml(raiz / "ciclos" / "ZZ.yaml", {
        "formato": "catalogo/4", "sigla": "ZZ", "grado": "GS", "familia": t, "nombre": t, "titulo": t,
        "rd": {"id": "BOE-A-2000-1", "nombre": t, "enlace": "https://example.com/y", "modificado_por": [],
               "correcciones": [], "posteriores": []},
        "competencia_general": t, "competencias": [{"letra": "a", "texto": t}, {"letra": "b", "texto": t}],
        "correspondencias_ecp": [{"modulos": ["0991"], "fuente": "BOE-A-2000-1",
                                  "ecp": [{"codigo": "ECP0001_3", "texto": t, "uc": "UC0001_3"}]}],
        "modulos": [{**mod, "codigo": "0991", "modulo": "0991", "curso": 1, "h_sem": 30, "h_anuales": 1000},
                    {**mod, "codigo": "0992", "modulo": "0992", "curso": 2, "h_sem": 27, "h_anuales": 900},
                    {**mod, "codigo": "1713999", "modulo": None, "curso": 2, "h_sem": 3, "h_anuales": 100,
                     "tipo": "proyecto", "pendiente": "Sin fuente de los RA (ficticio)"}],
        "optativos_ofertados": [], "proyecto": "1713999", "fuentes": {"titulo": "BOE-A-2000-1"},
        "comprobado": "2026-10-17"})
    escribir_yaml(raiz / "normativa.yaml", {"formato": "catalogo/4", "comprobado": "2026-10-17", "normas": [
        {"id": "BOE-A-2000-1", "ambito": "estatal", "titulo": t, "fecha": "2000-01-01", "diario": "BOE",
         "enlace": "https://example.com/y", "aplica": ["ZZ"]}]})
    catalogo.actualizar_version(raiz, "2026-10-17")
    return raiz


def test_catalogo_ficticio_limpio(tmp_path):
    assert comprobar(catalogo_ficticio(tmp_path), siglas={"ZZ"}) == []


def _cambiar(raiz, archivo, f):
    d = leer_yaml(raiz / archivo)
    f(d)
    escribir_yaml(raiz / archivo, d)


@pytest.mark.parametrize("archivo, cambio, mensaje", [
    ("ciclos/ZZ.yaml", lambda c: c["modulos"][1].update(h_sem=26), "h/semana"),
    ("ciclos/ZZ.yaml", lambda c: c["modulos"][1].update(h_anuales=899), "h/año"),
    ("ciclos/ZZ.yaml", lambda c: c["modulos"][1].update(modulo="0993"), "no existe"),
    ("ciclos/ZZ.yaml", lambda c: c["modulos"][2].pop("pendiente"), "sin RA y sin motivo"),
    ("ciclos/ZZ.yaml", lambda c: c["correspondencias_ecp"][0].update(modulos=["0555"]), "no es del ciclo"),
    ("ciclos/ZZ.yaml", lambda c: c.update(competencias=[{"letra": "b", "texto": {"es": "x"}}]), "competencias"),
    ("modulos/0991.yaml", lambda m: m["ra"][1].update(n=3), "RA no numerados"),
    ("modulos/0991.yaml", lambda m: m["ra"][0]["criterios"][1].update(letra="c"), "fuera de orden"),
    ("modulos/0991.yaml", lambda m: m["fuente"].update(norma="BOE-A-2000-2"), "no está en fuentes.yaml"),
    ("modulos/0991.yaml", lambda m: m.update(id="0992"), "no casan"),
    ("ciclos/ZZ.yaml", lambda c: c.update(competencia_general_corregida=c["competencia_general"],
                                          competencia_general_correccion="Errata ficticia de prueba"),
     "corregida igual"),
    ("modulos/0991.yaml", lambda m: m["ra"][0]["criterios"][0].update(
        corregido={"es": "Se ha hecho 0."}, correccion="Errata ficticia de prueba"), "igual al texto literal"),
    ("normativa.yaml", lambda n: n["normas"].append({**copy.deepcopy(n["normas"][0]), "fecha": "1999-01-01"}), "fecha creciente"),
])
def test_comprobar_detecta_errores(tmp_path, archivo, cambio, mensaje):
    raiz = catalogo_ficticio(tmp_path)
    _cambiar(raiz, archivo, cambio)
    errores = comprobar(raiz, siglas={"ZZ"})
    assert any(mensaje in e for e in errores), errores


def test_comprobar_detecta_modulo_sin_usar_y_ciclo_que_falta(tmp_path):
    raiz = catalogo_ficticio(tmp_path)
    escribir_yaml(raiz / "modulos" / "0994.yaml", {**leer_yaml(raiz / "modulos" / "0991.yaml"), "id": "0994", "codigo": "0994"})
    errores = comprobar(raiz)
    assert any("0994.yaml: ningún ciclo" in e for e in errores)
    assert any(e.startswith("ciclos: faltan") for e in errores)


# ---------------------------------------------------------------------------------------------------------------------
# Comparación con una programación (.docx ficticio creado en la prueba)
# ---------------------------------------------------------------------------------------------------------------------
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def docx_ficticio(ruta, parrafos):
    cuerpo = "".join(f'<w:p><w:pPr><w:pStyle w:val="{e}"/></w:pPr><w:r><w:t>{t}</w:t></w:r></w:p>' for e, t in parrafos)
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("word/document.xml", f'<?xml version="1.0"?><w:document {W}><w:body>{cuerpo}</w:body></w:document>')


def programacion(tmp_path, criterio_b="Se ha hecho 1."):
    ruta = tmp_path / "ZZ 1 - 0991 - Módulo ficticio.docx"
    docx_ficticio(ruta, [
        ("TDC2", "11. CRITERIOS Y PROCEDIMIENTOS PARA LA EVALUACIÓN13"),
        ("Ttulo2", "11. CRITERIOS Y PROCEDIMIENTOS PARA LA EVALUACIÓN"),
        ("", "Siguiendo el real decreto ficticio, los resultados de aprendizaje son los siguientes:"),
        ("", "R.A.1. Hace algo ficticio 1."), ("", "Criterios de evaluación:"),
        ("Prrafodelista", "Se ha hecho 0."), ("Prrafodelista", criterio_b),
        ("", "R.A.2. Hace algo ficticio 2."), ("", "Criterios de evaluación."),
        ("Prrafodelista", "Se ha hecho 0."), ("Prrafodelista", "Se ha hecho 1."),
        ("Ttulo3", "11.1.- Instrumentos y procedimiento de evaluación"),
        ("", "R.A.9. Esto ya no cuenta."),
    ])
    return ruta


def test_comparar_identicos(tmp_path):
    raiz = catalogo_ficticio(tmp_path)
    assert comparar(programacion(tmp_path), raiz) == []


def test_comparar_detecta_un_criterio_distinto(tmp_path):
    raiz = catalogo_ficticio(tmp_path)
    dif = comparar(programacion(tmp_path, "Se ha hecho otra cosa."), raiz)
    assert [(d["codigo"], d["ra"], d["letra"], d["tipo"]) for d in dif] == [("0991", 1, "b", "criterio")]


def test_comparar_detecta_un_ra_de_menos(tmp_path):
    raiz = catalogo_ficticio(tmp_path)
    _cambiar(raiz, "modulos/0991.yaml", lambda m: m.update(ra=m["ra"][:1]))
    assert comparar(programacion(tmp_path), raiz)[0]["tipo"] == "número de RA"


# -- contenidos básicos (apartado 4 de una programación nueva; textos inventados con la forma de cada BOE) ------------
def _p(*textos, clase=""):
    return [{"texto": t, "clase": clase} for t in textos]


def test_contenidos_con_guiones():
    ps = _p("Duración: 99 horas.", "Contenidos básicos:", "Bloque ficticio uno:", "− Punto a.", "− Punto b",
            "que sigue en otra línea.", "Bloque ficticio (c.a.) dos:", "– Punto c.", "Orientaciones pedagógicas.")
    c, motivo = catalogo.leer_contenidos(ps, 2)
    assert motivo is None and [b["titulo"] for b in c] == ["Bloque ficticio uno", "Bloque ficticio (c.a.) dos"]
    assert c[0]["puntos"] == ["Punto a.", "Punto b que sigue en otra línea."]


def test_contenidos_sin_guiones_y_titulo_que_no_lo_es():
    ps = _p("Contenidos básicos:", "Bloque uno:", "Punto suelto.", "Funcionamiento de los siguientes sistemas:",
            "Bloque dos:", "Otro punto.")
    c, _ = catalogo.leer_contenidos(ps, 2)
    assert [b["titulo"] for b in c] == ["Bloque uno", "Bloque dos"] and len(c[0]["puntos"]) == 2


def test_contenidos_de_2008_con_titulo_pegado():
    ps = [{"texto": "Duración: 99 horas. Contenidos básicos:", "clase": "ATEXTO_BLANCO_6"},
          {"texto": "Bloque uno: primer punto.", "clase": "ATEXTO_BLANCO_4"},
          {"texto": "Más texto del bloque.", "clase": "ATEXTO_NORMAL"},
          {"texto": "Bloque dos:", "clase": "ATEXTO_BLANCO_6"},
          {"texto": "Punto del dos.", "clase": "ATEXTO_BLANCO_4"}]
    c, _ = catalogo.leer_contenidos(ps, 2)
    assert [b["titulo"] for b in c] == ["Bloque uno", "Bloque dos"] and c[0]["puntos"][0] == "primer punto."


@pytest.mark.parametrize("ps, n_ra", [
    (_p("Contenidos básicos:", "Bloque uno:", "− a", "Bloque dos:", "− b"), 5),          # bloques muy lejos de los RA
    (_p("Contenidos básicos:", "Texto suelto.", "Bloque:", "− a"), 1),                   # texto antes de un bloque
    (_p("Contenidos básicos:", "Bloque:", "− a", "Bloque:", "− b"), 2),                  # títulos repetidos
])
def test_contenidos_dudosos_quedan_pendientes(ps, n_ra):
    assert catalogo.leer_contenidos(ps, n_ra) == (None, catalogo.PENDIENTE_CONTENIDOS)


def test_sin_contenidos_basicos_no_hay_nada():
    assert catalogo.leer_contenidos(_p("Duración: 40 horas.", "Orientaciones pedagógicas."), 3) == (None, None)


def test_contenidos_del_dogv():
    lineas = ["  1. Bloque uno:", "  - Punto a que se parte", "    en dos líneas.", "  a) Punto con letra.",
              "  Título de grupo", "  2. Bloque dos:", "  2.1. Subbloque como punto:", "  - Punto b."]
    c, motivo = catalogo.contenidos_dogv(lineas, 2)
    assert motivo is None and [b["titulo"] for b in c] == ["Bloque uno", "Bloque dos"]
    assert c[0]["puntos"] == ["Punto a que se parte en dos líneas.", "Punto con letra."]
    assert c[1]["puntos"] == ["Subbloque como punto:", "Punto b."]
    assert catalogo.contenidos_dogv(["  7.1. Sin su bloque:", "  - x"], 1)[1] == catalogo.PENDIENTE_CONTENIDOS


# -- propuesta de IA de las competencias de cada RA ------------------------------------------------------------------
def _modulo_ficticio():
    return {"ra": [{"n": 1, "texto": {"es": "RA uno ficticio."}}, {"n": 2, "texto": {"es": "RA dos ficticio."}}],
            "competencias_modulo": {"XX": ["a", "b", "c"]}, "fuente": {"norma": "BOE-A-0000-0"}}


def _ciclos_ficticios():
    return {"XX": {"sigla": "XX", "competencias": [{"letra": x} for x in "abcd"], "modulos": [{"modulo": "9999"}]}}


def test_propuesta_valida_entra_en_el_modulo(tmp_path):
    m = _modulo_ficticio()
    origen = tmp_path / "p.yaml"
    origen.write_text(yaml.safe_dump({"XX": {"9999": {"huella_ra": catalogo.huella_ra(m),
                                                      "ra": {"1": ["c", "a"], "2": ["b"]}}}}))
    modulos = {"9999": m}
    assert catalogo.anadir_propuestas(modulos, _ciclos_ficticios(), origen) == []
    assert m["propuesta_ra_competencias"] == {"XX": {"1": ["a", "c"], "2": ["b"]}}
    assert list(m)[-1] == "fuente"


@pytest.mark.parametrize("cambio, aviso", [
    ({"huella_ra": "otra"}, "sus RA han cambiado"),
    ({"ra": {"1": ["a"]}}, "incompleta"),                       # falta el RA2
    ({"ra": {"1": ["a"], "2": ["d"]}}, "letras que el módulo no tiene"),
    ({"ra": {"1": ["a"], "2": []}}, "incompleta"),
])
def test_propuesta_que_no_vale_queda_fuera(tmp_path, cambio, aviso):
    m = _modulo_ficticio()
    p = {"huella_ra": catalogo.huella_ra(m), "ra": {"1": ["a"], "2": ["b"]}, **cambio}
    origen = tmp_path / "p.yaml"
    origen.write_text(yaml.safe_dump({"XX": {"9999": p}}))
    avisos = catalogo.anadir_propuestas({"9999": m}, _ciclos_ficticios(), origen)
    assert "propuesta_ra_competencias" not in m and aviso in avisos[0]


def test_optativos_de_adm_y_aut_y_peritacion_sin_erratas(cat):
    """CarlosFB, 2026-10-21: en 2.º de ADM solo inglés (como SEA, STI y ARI); en 2.º de AUT, inglés y Peritación
    de daños y realización de presupuestos (anexo X-XXVI del Decreto 114/2025, con el código de la casilla de optativo
    de AUT, CVOPS192). CAR y EMV siguen con el inglés de GM. Peritación trae los 17 RA del decreto, sin la errata
    «-ónón» del PDF del DOGV."""
    ofertados = {s: [(o["codigo"], o["modulo"]) for o in cat.ciclo(s)["optativos_ofertados"]]
                 for s in ("ADM", "AUT", "CAR", "EMV")}
    # el inglés oral de GS, con el código de la casilla de optativo de su ciclo (CarlosFB, 2026-10-21; ADR-043)
    assert ofertados["ADM"] == [("CVOPS001", "OPT-INGLES-ORAL")]
    assert ofertados["AUT"] == [("CVOPS192", "OPT-INGLES-ORAL"), ("CVOPS192", "OPT-TMV-PERITACION")]
    assert ofertados["CAR"] == ofertados["EMV"] == [("ANEXO X-I", "OPT-INGLES-ORAL")]
    assert not any(m.get("pendiente") for s in ("ADM", "AUT") for m in cat.ciclo(s)["modulos"] if m["tipo"] == "optativo")
    peritacion = cat.modulo("OPT-TMV-PERITACION")
    assert peritacion["nombre"]["es"] == "Peritación de daños y realización de presupuestos"
    assert [r["n"] for r in peritacion["ra"]] == list(range(1, 18))
    textos = [r["texto"]["es"] for r in peritacion["ra"]] + \
        [c["texto"]["es"] for r in peritacion["ra"] for c in r["criterios"]]
    assert not any("ónón" in t for t in textos) and any("reparación" in t for t in textos)
