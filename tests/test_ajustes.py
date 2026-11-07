"""Ajustes de este equipo: valores por defecto vacíos, guardado, archivos tocados a mano y curso escolar."""

import json
from datetime import date

import pytest

from programaciones.ajustes import Ajustes, GestorAjustes, correo_valido, curso_escolar_de, estado_carpeta


def test_por_defecto_vacios(datos):
    g = GestorAjustes(datos)
    assert g.valores == Ajustes()
    assert g.valores.formatos == ["docx", "pdf"] and g.valores.programa_pdf == "auto" and g.valores.idioma == "es"


def test_se_guardan_y_se_recuperan(datos):
    g = GestorAjustes(datos)
    g.poner(nombre_profesor="Profesora Ficticia", correo_pie="departamento@example.com")
    prog = {"curso_escolar": "2030-2031", "ciclo": "SEA", "curso": 2, "modulo": "0999"}
    g.poner_carpeta_de(prog, "/ruta/ficticia")
    otra = GestorAjustes(datos)
    assert otra.valores.nombre_profesor == "Profesora Ficticia"
    assert otra.valores.correo_pie == "departamento@example.com"
    assert otra.carpeta_de(prog) == "/ruta/ficticia"


def test_carpeta_vacia_se_quita(datos):
    g = GestorAjustes(datos)
    prog = {"curso_escolar": "2030-2031", "ciclo": "SEA", "curso": 2, "modulo": "0999"}
    g.poner_carpeta_de(prog, "/ruta/ficticia")
    g.poner_carpeta_de(prog, "  ")
    assert g.carpeta_de(prog) == "" and g.valores.carpetas_programacion == {}


def test_la_carpeta_de_antes_es_la_sugerida(datos, tmp_path):
    """ADR-051: la carpeta de exportación de Ajustes (0.17 a 0.19) o, sin ella, la de entrega de este equipo del curso
    más reciente (hasta la 0.17; no un enlace) es donde se abre el diálogo de la primera exportación. No decide sola
    dónde se exporta."""
    g = GestorAjustes(datos)
    vieja, nueva, ajustes = tmp_path / "vieja", tmp_path / "nueva", tmp_path / "ajustes"
    for c in (vieja, nueva, ajustes):
        c.mkdir()
    g.poner(carpetas_entrega={"2029-2030": str(vieja), "2030-2031": str(nueva),
                              "2031-2032": "https://example.com/sites/departamento/Programaciones"})
    assert GestorAjustes(datos).carpeta_sugerida() == str(nueva)
    g.poner(carpeta_exportacion=str(ajustes))
    assert GestorAjustes(datos).carpeta_sugerida() == str(ajustes)
    assert g.destino({"curso_escolar": "2030-2031", "ciclo": "SEA", "curso": 2, "modulo": "0999"}) == ""


def test_ajuste_desconocido_no_se_acepta(datos):
    with pytest.raises(AttributeError):
        GestorAjustes(datos).poner(ajuste_inventado="x")


def test_archivo_tocado_a_mano_no_tumba_la_app(datos):
    (datos / "ajustes.json").write_text(json.dumps({
        "nombre_profesor": 7, "formatos": ["pdf", "odt"], "programa_pdf": "otro", "idioma": "fr",
        "correo_pie": "departamento@example.com", "desconocido": True,
    }), encoding="utf-8")
    v = GestorAjustes(datos).valores
    assert v.nombre_profesor == "" and v.formatos == ["pdf"] and v.programa_pdf == "auto" and v.idioma == "es"
    assert v.correo_pie == "departamento@example.com"
    (datos / "ajustes.json").write_text("{roto", encoding="utf-8")
    assert GestorAjustes(datos).valores == Ajustes()


@pytest.mark.parametrize("dia, curso", [
    (date(2026, 9, 1), "2026-2027"), (date(2027, 8, 31), "2026-2027"), (date(2026, 10, 17), "2026-2027"),
    (date(2027, 6, 30), "2026-2027"), (date(2027, 9, 1), "2027-2028"),
])
def test_curso_escolar(dia, curso):
    assert curso_escolar_de(dia) == curso


def test_correo_valido():
    assert correo_valido("departamento@example.com")
    assert not correo_valido("departamento") and not correo_valido("a@b") and not correo_valido("a b@example.com")


def test_estado_carpeta(tmp_path):
    assert estado_carpeta("") == "vacia"
    assert estado_carpeta(str(tmp_path)) == "local"
    assert estado_carpeta(str(tmp_path / "no-existe")) == "no_encontrada"
    assert estado_carpeta("https://example.com/sites/departamento/Documentos") == "enlace"


def test_correo_y_favoritos_por_defecto_y_tocados_a_mano(datos):
    v = GestorAjustes(datos).valores
    assert v.destinatarios == [] and v.cliente_correo == "auto" and v.favoritos == []
    assert "{modulo}" in v.asunto_una and "{archivos}" in v.cuerpo_correo
    (datos / "ajustes.json").write_text(json.dumps({
        "destinatarios": ["jefatura@example.com", " ", "jefatura@example.com", 3], "cliente_correo": "telegrama",
        "favoritos": ["SEA-2-0991", "SEA-2-0991"],
    }), encoding="utf-8")
    v = GestorAjustes(datos).valores
    assert v.destinatarios == ["jefatura@example.com", "3"] and v.cliente_correo == "auto"
    assert v.favoritos == ["SEA-2-0991"]


def test_favoritos_se_marcan_y_se_guardan(datos):
    g = GestorAjustes(datos)
    assert g.cambiar_favorito("SEA-2-0991") and g.es_favorito("SEA-2-0991")
    assert GestorAjustes(datos).valores.favoritos == ["SEA-2-0991"], "se guardan en este equipo"
    assert not g.cambiar_favorito("SEA-2-0991") and not GestorAjustes(datos).es_favorito("SEA-2-0991")
