# -*- mode: python ; coding: utf-8 -*-
# Un único spec para macOS y Windows (copia del de Partes de salida, lección BLD-008 de Guardias de patio):
#   · nombre: «Programaciones» en las dos (sin espacios ni «_»): Programaciones.app y Programaciones.exe;
#   · icono: .icns en macOS (scripts/crear_icono.sh lo rehace en la CI), .ico en Windows; el BUNDLE solo en macOS;
#   · dentro van la plantilla, el catálogo y los esquemas: sin ellos la app no genera nada (diagnostico.py lo
#     comprueba en la prueba de arranque).
# Rutas siempre con barra normal. Ningún archivo empaquetado lleva acentos en el nombre: rompería la firma del .app al
# copiarlo (BLD-010 de Guardias).
import os
import re
import sys
from pathlib import Path

ES_MACOS = sys.platform == "darwin"
NOMBRE = "Programaciones"
VERSION = re.search(
    r'^version = "([^"]+)"', (Path(SPECPATH) / "pyproject.toml").read_text(encoding="utf-8"), re.M
).group(1)
ICONO = "imagenes/icono.icns" if ES_MACOS else "imagenes/icono.ico"
# Variante de diagnóstico (Actions → Compilar → «depurar»): el arranque de PyInstaller cuenta cada paso por la consola.
DEPURAR = os.getenv("PROGRAMACIONES_BUILD_DEPURAR") == "1"

datas = [
    # Tipografías, logos, icono y la plantilla desempaquetada (con «_rels/.rels»): PyInstaller solo empaqueta los .py.
    ("src/programaciones/recursos", "programaciones/recursos"),
    ("src/programaciones/esquemas", "programaciones/esquemas"),
    # El catálogo que la app lleva dentro (catalogo.carpeta_por_defecto lo busca en sys._MEIPASS/catalogo).
    ("catalogo/ciclos", "catalogo/ciclos"),
    ("catalogo/modulos", "catalogo/modulos"),
    ("catalogo/normativa.yaml", "catalogo"),
    ("catalogo/fuentes.yaml", "catalogo"),
    ("catalogo/version.yaml", "catalogo"),   # versión del catálogo (ADR-027); vigia.yaml no va: es del vigía
]
if Path("catalogo/cursos").is_dir():  # fechas de cada curso escolar, cuando estén dadas de alta
    datas.append(("catalogo/cursos", "catalogo/cursos"))
hiddenimports = ["PyQt6.QtNetwork", "PyQt6.QtPdf", "PyQt6.QtPdfWidgets", "certifi", "cryptography"]

a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "PyQt6.QtWebEngineCore", "PyQt6.QtQml", "PyQt6.QtQuick"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Sin UPX: el empaquetado comprimido dispara los antivirus (BLD-011 de Guardias).
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NOMBRE,
    debug="all" if DEPURAR else False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=DEPURAR,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[ICONO],
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, upx_exclude=[], name=NOMBRE)

if ES_MACOS:
    app = BUNDLE(
        coll,
        name=f"{NOMBRE}.app",
        icon=ICONO,
        bundle_identifier="es.epla.programaciones",
        info_plist={
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "LSUIElement": False,
        },
    )
