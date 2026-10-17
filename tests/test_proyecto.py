"""Invariantes del proyecto: versión, empaquetado, instaladores y lo que no puede entrar en el repositorio."""

import re
import tomllib
from pathlib import Path

import programaciones

RAIZ = Path(__file__).resolve().parents[1]
PALABRA = "C" + "laude"  # la palabra prohibida de la bóveda, sin escribirla aquí
TEXTO = {".py", ".md", ".toml", ".txt", ".yml", ".yaml", ".json", ".sh", ".ps1", ".iss", ".spec", ".xml", ""}


def leer(ruta: str) -> str:
    return (RAIZ / ruta).read_text(encoding="utf-8-sig")


def test_version_coherente():
    pyproject = tomllib.loads(leer("pyproject.toml"))
    assert pyproject["project"]["version"] == programaciones.__version__


def test_changelog_tiene_la_version_o_esta_sin_publicar():
    changelog = leer("CHANGELOG.md")
    assert f"## [{programaciones.__version__}]" in changelog or "## [Sin publicar]" in changelog


def test_spec_empaqueta_plantilla_catalogo_esquemas_y_qtpdf():
    spec = leer("Programaciones.spec")
    for dato in ('"src/programaciones/recursos"', '"src/programaciones/esquemas"', '"catalogo/ciclos"',
                 '"catalogo/modulos"', '"catalogo/normativa.yaml"'):
        assert dato in spec, dato
    assert '"PyQt6.QtPdf"' in spec and '"PyQt6.QtPdfWidgets"' in spec
    assert 'NOMBRE = "Programaciones"' in spec
    assert "upx=False" in spec


def test_el_catalogo_empaquetado_es_el_que_lee_la_app_congelada(monkeypatch, tmp_path):
    """El spec deja el catálogo en `_MEIPASS/catalogo`: el lector tiene que buscarlo ahí."""
    import sys

    from programaciones import catalogo

    monkeypatch.delenv("PROGRAMACIONES_CATALOGO", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert catalogo.carpeta_por_defecto() == tmp_path / "catalogo"
    assert "(\"catalogo/ciclos\", \"catalogo/ciclos\")" in leer("Programaciones.spec")


def test_recursos_con_nombres_ascii():
    """Un nombre con acento dentro del .app rompe su firma (lección de Guardias)."""
    raros = [str(f) for f in (RAIZ / "src" / "programaciones").rglob("*") if not f.name.isascii()]
    assert not raros


def test_nombres_de_instaladores_coinciden_con_el_actualizador():
    from programaciones.actualizaciones import INSTALADOR_POR_SISTEMA, REPO

    assert REPO == "cferrerobonet/programaciones_fp"
    flujo = leer(".github/workflows/compilar.yml")
    dmg = leer("scripts/build/build_dmg.sh")
    iss = leer("installer_windows.iss")
    assert INSTALADOR_POR_SISTEMA["Darwin"].replace("{v}", "${VERSION}") in dmg
    assert INSTALADOR_POR_SISTEMA["Windows"] == "Programaciones-{v}-Windows-Setup.exe"
    assert "OutputBaseFilename=Programaciones-{#MyAppVersion}-Windows-Setup" in iss
    assert "Programaciones-${{ steps.version.outputs.numero }}-Windows-Portable.zip" in flujo


def test_instalador_de_windows_con_appid_propio_y_nombre_visible():
    iss = leer("installer_windows.iss")
    appid = re.search(r"^AppId=\{\{([0-9A-F-]{36})\}", iss, re.M)
    assert appid, "AppId fijo con forma de GUID"
    partes = leer_partes_de_salida("installer_windows.iss")
    if partes:
        assert appid.group(1) not in partes, "el AppId no puede ser el de Partes de salida"
    assert '#define MyAppName "Programaciones"' in iss
    visibles = re.findall(r'(?:AppName|DefaultGroupName|Name: "\{group\}\\)([^"\n]*)', iss)
    assert all("_" not in v for v in visibles)


def leer_partes_de_salida(ruta: str) -> str:
    otra = RAIZ.parents[1] / "PARTES DE SALIDA (python)" / "PARTES DE SALIDA - CÓDIGO FUENTE" / ruta
    return otra.read_text(encoding="utf-8") if otra.exists() else ""


def test_la_ci_comprueba_datos_qtpdf_y_arranque_en_las_dos_plataformas():
    from programaciones.app import MARCA_PRUEBA
    from programaciones.diagnostico import MARCA_DATOS
    from programaciones.ui.vista_previa import MARCA_QTPDF

    flujo = leer(".github/workflows/compilar.yml")
    windows = leer("scripts/prueba_arranque_windows.ps1")
    for marca in (MARCA_PRUEBA, MARCA_DATOS, MARCA_QTPDF):
        assert marca in flujo and marca in windows, marca
    assert flujo.count("scripts/comprobar_paquete.sh") == 2
    assert "workflow_dispatch" in flujo


def test_icono_de_la_ventana_es_el_de_la_app():
    from programaciones.app import icono_app
    from programaciones.rutas import recursos

    assert (recursos() / "icono.png").exists()
    assert "icono.png" in leer("src/programaciones/app.py")
    assert icono_app  # QIcon del icono de la app, no del logo del centro
    assert 'ICONO = "imagenes/icono.icns" if ES_MACOS else "imagenes/icono.ico"' in leer("Programaciones.spec")
    assert (RAIZ / "imagenes" / "icono.ico").exists()


def test_build_windows_lleva_bom():
    """Windows PowerShell 5.1 lee sin BOM como ANSI y rompe los acentos."""
    assert (RAIZ / "scripts" / "build_windows.ps1").read_bytes().startswith(b"\xef\xbb\xbf")


def test_ajustes_sin_datos_de_correo_por_defecto():
    """ADR-016 y ADR-018 (11): ningún correo ni servidor escrito en el repositorio."""
    from programaciones.ajustes import Ajustes

    a = Ajustes()
    assert a.correo_pie == "" and a.nombre_profesor == "" and a.carpetas_entrega == {}


def test_sin_palabra_prohibida():
    patron = re.compile(rf"\b{PALABRA}\b")
    culpables = []
    for f in RAIZ.rglob("*"):
        partes = f.relative_to(RAIZ).parts
        if not f.is_file() or partes[0] in (".git", ".ruff_cache", "build", "dist", "test-results") or "__pycache__" in partes:
            continue
        if f.suffix.lower() not in TEXTO:
            continue
        if patron.search(f.read_text(encoding="utf-8", errors="ignore")):
            culpables.append(str(f.relative_to(RAIZ)))
    assert not culpables, f"Palabra prohibida en: {culpables}"
