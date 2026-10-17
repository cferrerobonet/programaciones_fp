---
paths:
  - "Programaciones.spec"
  - "installer_windows.iss"
  - "Makefile"
  - "scripts/build/**"
  - "scripts/*.ps1"
  - "scripts/comprobar_paquete.sh"
  - "scripts/crear_icono.sh"
  - ".github/workflows/**"
  - "src/programaciones/actualizaciones.py"
  - "src/programaciones/app.py"
  - "src/programaciones/rutas.py"
  - "src/programaciones/diagnostico.py"
---

# Empaquetado y publicación

Copia de la regla de Partes de salida, con lo propio de Programaciones.

- **No se compila en local** (CarlosFB, ADR-011): ni PyInstaller, ni Inno Setup, ni `hdiutil`. Etiqueta `vX.Y.Z` → `.github/workflows/compilar.yml` pasa las pruebas, compila Windows (instalador y portable) y macOS (DMG arm64) y los adjunta al release. Para probar sin publicar: Actions → Compilar → *Run workflow* (`gh workflow run compilar.yml`) y, si hace falta, descargar los artefactos. El gancho `guardia_bash_extra.sh` bloquea compilar en local.
- **Un solo spec** (`Programaciones.spec`) para las dos plataformas, con la plantilla (`recursos/`), los esquemas y el catálogo (`catalogo/` → `sys._MEIPASS/catalogo`, que lee `catalogo.carpeta_por_defecto`). Lo vigila `tests/test_proyecto.py`.
- **Nombres ASCII** dentro de la app: un archivo con acento rompe la firma del `.app` (BLD-010 de Guardias). `test_proyecto.py` lo comprueba en `recursos/`.
- **Datos empaquetados:** `scripts/comprobar_paquete.sh` mira en la app compilada el catálogo, los esquemas, la plantilla (con `_rels/.rels`), las tipografías, el icono y QtPdf.
- **Prueba de arranque** en las dos plataformas: `PROGRAMACIONES_PRUEBA_DE_ARRANQUE=ventana` abre la ventana, lee los datos (`diagnostico.comprobar_datos`), abre un PDF con QtPdf (`ui/vista_previa.comprobar_qtpdf`), escribe las marcas `PRUEBA DE ARRANQUE: datos empaquetados`, `… QtPdf` y `… ventana principal a la vista` en el registro y sale. No quitarla: un exe que existe no es un exe que arranca.
- **Nombres fijos de los instaladores** (`Programaciones-<v>-macOS-arm64.dmg`, `Programaciones-<v>-Windows-Setup.exe`, `Programaciones-<v>-Windows-Portable.zip`): `actualizaciones.py` los usa para el plan B sin API. Si cambian aquí, cambian allí (test).
- **`AppId` de Inno Setup fijo** (`installer_windows.iss`): con él cada versión sustituye a la anterior. No se cambia nunca. Nombre visible «Programaciones».
- Icono: `imagenes/icono.png` → `scripts/crear_icono.sh` (el `.ico` va en el repositorio; el `.icns` lo rehace la CI de macOS). La ventana y la barra de tareas llevan el icono de la app; el logo de EPLA solo va dentro del documento (y en la presentación, como en Partes de salida).
- Versión: `pyproject.toml` y `src/programaciones/__init__.py` coinciden (test) y la CI rechaza una etiqueta que no case con `pyproject.toml`.
- Registro de la app instalada: macOS `~/Library/Application Support/Programaciones/logs/`, Windows `%APPDATA%\Programaciones\logs\`. Si «la app no abre», pedir antes ese registro.
