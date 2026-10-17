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
                 '"catalogo/modulos"', '"catalogo/normativa.yaml"', '"catalogo/version.yaml"'):
        assert dato in spec, dato
    assert "vigia.yaml" not in spec.split("datas = [")[1].split("]")[0].replace("vigia.yaml no va", "")
    assert '"PyQt6.QtPdf"' in spec and '"PyQt6.QtPdfWidgets"' in spec and '"cryptography"' in spec
    assert re.search(r"^cryptography==", leer("requirements.txt"), re.M), "la app verifica la firma del catálogo"
    paquete = leer("scripts/comprobar_paquete.sh")
    assert "catalogo/version.yaml" in paquete and "recursos/clave_catalogo.txt" in paquete
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


def test_el_dmg_no_lleva_leeme():
    """CarlosFB (2026-10-17): sin «LÉEME - si dice que está dañada.txt» en el DMG; los pasos, en docs/OPERACIONES.md."""
    script = (Path(__file__).resolve().parents[1] / "scripts" / "build" / "build_dmg.sh").read_text(encoding="utf-8")
    assert not re.search(r'cat\s*>\s*"\$TMP/[^"]*\.txt"', script) and "AVISO" not in script
    operaciones = (Path(__file__).resolve().parents[1] / "docs" / "OPERACIONES.md").read_text(encoding="utf-8")
    assert "com.apple.quarantine" in operaciones


def test_flujos_del_vigia_y_del_catalogo():
    """vigia.yml cada semana y a mano; catalogo.yml al cambiar el catálogo en main, con el secreto solo en el paso que
    firma (ADR-027 y ADR-028)."""
    vigia = leer(".github/workflows/vigia.yml")
    assert "schedule:" in vigia and "workflow_dispatch:" in vigia and "simulacro" in vigia
    assert "scripts/vigia.py revisar" in vigia and "scripts/vigia.py pr" in vigia and "secrets." not in vigia
    cat = leer(".github/workflows/catalogo.yml")
    assert cat.count("secrets.CATALOGO_CLAVE") == 1
    firmar = cat.split("- name: Firmar")[1].split("- name:")[0]
    assert "secrets.CATALOGO_CLAVE" in firmar and "scripts/catalogo.py publicar" in firmar
    assert "scripts/catalogo.py verificar" in cat and "catalogo-publicado" in cat and '"!catalogo/vigia.yaml"' in cat


def test_sin_clave_privada_en_el_repositorio():
    """Solo la pública: ningún archivo lleva una clave privada PEM ni otra clave en base64 junto a la del catálogo."""
    publica = [x for x in leer("src/programaciones/recursos/clave_catalogo.txt").splitlines() if not x.startswith("#")]
    assert len(publica) == 1 and len(publica[0]) == 44
    for p in RAIZ.rglob("*"):
        if p.is_file() and p.suffix in TEXTO and ".git" not in p.parts and "__pycache__" not in p.parts \
                and ".ruff_cache" not in p.parts:
            t = p.read_text(encoding="utf-8", errors="ignore")
            assert "PRIVATE KEY" not in t or p.name == "test_proyecto.py", p
