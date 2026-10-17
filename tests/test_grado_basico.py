"""Grado Básico (F8, ADR-032): catálogo de los cuatro ciclos del centro, documento de sus módulos técnicos y, hasta
que llegue su plantilla, los ámbitos como «pendiente». Textos inventados en los lectores; el resto, del catálogo."""
import pytest

import catalogo
from conftest import programacion_minima
from programaciones import programacion
from test_documento import generar, parrafos, tablas


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


def test_gb_espera_los_periodos_de_empresa(cat):
    """2026-2027: la FE de GB no está en el calendario del centro; la definitiva espera (V-11)."""
    from programaciones import documento, validacion
    curso = cat.curso_escolar("2026-2027")
    p = programacion_minima(cat, "EE", 2, "3016")
    avisos = validacion.validar(p, cat.ficha("EE", "3016", 2),
                                curso_pendiente=documento.pendiente_curso(curso, "EE", 2))
    assert any(a.id == "V-11" and "Grado Básico" in a.mensaje for a in avisos)


# -- app ---------------------------------------------------------------------------------------------------------------
def test_lista_sin_tutoria_y_ambitos_pendientes(contexto):
    gb = [m for m in contexto.modulos if m.grado == "GB"]
    assert gb and not any(m.codigo.startswith("TU") for m in gb)
    assert all(m.pendiente for m in gb if m.codigo in catalogo.AMBITOS)
    assert not any(m.pendiente for m in gb if m.codigo == "3016")


def test_un_ambito_no_se_abre_hasta_su_plantilla(contexto, cat):
    p = programacion.nueva("EE", 2, "3164", "2026-2027", cat.version, "2026-10-06")
    with pytest.raises(programacion.ProgramacionNoValida, match="próxima versión"):
        contexto.abrir(p)


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
