# Operaciones

Cómo se instala, se publica, se restaura y se diagnostica. Primera versión publicada: 0.1.0 (pre-release, 2026-10-17).

## Para el profesorado

| Tarea | Pasos |
| --- | --- |
| **Instalar** | Bajar de las releases de `cferrerobonet/programaciones_fp`: DMG en macOS (Mac con chip de Apple), instalador en Windows, o **portable** (ZIP) si el equipo no deja instalar. Repositorio público: sin cuenta de GitHub |
| **Primer arranque** | La app pide el nombre del profesor y la carpeta de entrega del curso (también al empezar cada curso escolar; se puede dejar para más tarde) |
| **Carpeta de entrega** | Recomendado: en Teams, «Agregar acceso directo a Mis archivos» sobre la carpeta del curso; después, en la app, Ajustes → Carpeta de entrega → elegir esa carpeta de OneDrive. Ayuda con capturas dentro de la app |
| **Actualizar la app** | Botón dorado «↑ Actualizar a X.Y.Z» → «Actualizar ahora». Los ajustes y las programaciones se conservan |
| **Catálogo nuevo** | Se descarga solo al arrancar. Al abrir una programación afectada, la app enseña los cambios y **el profesor decide** «Aceptar cambios» o «Más tarde» |
| **Recuperar tras formatear o cambiar de equipo** | Instalar, abrir el `.docx` exportado desde la carpeta de Teams (o el `.programacion` de OneDrive) y seguir |
| **Heredar una programación** | «Nueva a partir de…» → elegir el `.docx` del curso anterior en Teams → revisar y confirmar cada bloque |
| **Empezar un curso nuevo** | Al primer arranque del curso, la app pide la carpeta de entrega nueva. Las programaciones del curso anterior se heredan |

## Para el mantenedor (CarlosFB)

| Tarea | Cómo |
| --- | --- |
| Publicar una versión de la app | Versión, `CHANGELOG.md` (que es lo que ven los profesores en la ventana de novedades), commit, push, etiqueta `vX.Y.Z` y seguimiento de `compilar.yml`. Nunca compilar en local |
| Compilación de prueba, sin publicar | `gh workflow run compilar.yml` (o Actions → Compilar → *Run workflow*; `-f plataforma=macos\|windows`, `-f depurar=true`). Pasa las pruebas, compila, comprueba los datos empaquetados (`scripts/comprobar_paquete.sh`) y arranca la app en las dos plataformas. Los instaladores quedan como artefactos de la ejecución (`gh run download <id>`) |
| Vigilar el vigía | Las PR que pasan las comprobaciones se publican solas. Las que fallan quedan abiertas: revisar, corregir y fusionar. Si un cambio publicado está mal, corregir el YAML y publicar otra versión del catálogo |
| **Alta del curso escolar** (cada julio-septiembre) | `catalogo/cursos/AAAA-AAAA.yaml`: fechas de evaluación, ordinaria y extraordinaria; resolución de instrucciones; periodos de empresa por curso y jornada; optativos ofertados si cambian. Fuente: las notas del curso en la bóveda |
| Cambio de plantilla del departamento | `scripts/plantilla.py crear <programación nueva de referencia> --proyecto <la del Proyecto>` (subir `VERSION` en el script), revisar las marcas, `scripts/regenerar.py` con las referencias, `pytest -m referencias` y versión menor de la app |
| Rotar la clave del catálogo | Clave nueva en el secreto, pública nueva en la app, versión mayor. Los catálogos antiguos dejan de aceptarse al actualizar |

## Diagnóstico

- **Registro:** `<carpeta de datos>/logs/app_AAAAMMDD.log` y `faulthandler.log`.
- **Carpeta de datos:** macOS `~/Library/Application Support/Programaciones` · Windows `%APPDATA%\Programaciones`.
- **El PDF no sale:** comprobar que hay Word o LibreOffice (Ajustes → Exportación). Mientras tanto, exportar solo en Word.
- **«Datos incrustados no válidos»:** abrir la última versión de `autoguardado/` o el `.programacion`.
