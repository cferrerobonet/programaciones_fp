# Operaciones

Cómo se instala, se publica, se restaura y se diagnostica. Primera versión publicada: 0.1.0 (2026-10-17). Las versiones se publican como **normales** desde la 0.2.0, para que el aviso de actualización llegue (ADR-026); siguen en 0.x hasta el piloto (F6).

## Para el profesorado

| Tarea | Pasos |
| --- | --- |
| **Instalar** | Bajar de las releases de `cferrerobonet/programaciones_fp`: DMG en macOS (Mac con chip de Apple), instalador en Windows, o **portable** (ZIP) si el equipo no deja instalar. Repositorio público: sin cuenta de GitHub |
| **Primer arranque** | La app pide el nombre del profesor y la carpeta de entrega del curso (también al empezar cada curso escolar; se puede dejar para más tarde) |
| **Carpeta de entrega** | Recomendado: en Teams, «Agregar acceso directo a Mis archivos» sobre la carpeta del curso; después, en la app, Ajustes → Curso escolar → elegir esa carpeta de OneDrive (también desde el menú, «Curso escolar…»). Ayuda con capturas dentro de la app |
| **Enviar por correo** | Programaciones → marcar una o varias → «Enviar por correo…»: la app abre un correo nuevo en Mail u Outlook con los archivos adjuntos y el profesor lo envía desde su cuenta. Destinatarios habituales, programa de correo y texto, en Ajustes → Correo. Sin Outlook ni Mail, se abre la carpeta y un correo nuevo, y se adjuntan a mano (ADR-014) |
| **Borrar una programación de este equipo** | Programaciones → marcarla → «Borrar…»: el archivo de trabajo va a la papelera del sistema (se recupera de allí). Lo exportado (Word, PDF, Teams) no se toca (ADR-024) |
| **Actualizar la app** | Botón dorado «↑ Actualizar a X.Y.Z» → «Actualizar ahora». Los ajustes y las programaciones se conservan |
| **Catálogo nuevo** | Se descarga solo al arrancar. Al abrir una programación afectada, la app enseña los cambios y **el profesor decide** «Aceptar cambios» o «Más tarde» |
| **Recuperar tras formatear o cambiar de equipo** | Instalar, abrir el `.docx` exportado desde la carpeta de Teams (o el `.programacion` de OneDrive) y seguir |
| **Heredar una programación** | «Nueva a partir de…» → elegir el `.docx` del curso anterior en Teams → revisar y confirmar cada bloque |
| **Empezar un curso nuevo** | Al primer arranque del curso, la app pide la carpeta de entrega nueva. Las programaciones del curso anterior se heredan |

## Para el mantenedor (CarlosFB)

| Tarea | Cómo |
| --- | --- |
| Publicar una versión de la app | Skill `publicar`: versión, `CHANGELOG.md` (que es lo que ven los profesores en la ventana de novedades), commit, push, etiqueta `vX.Y.Z` y seguimiento de `compilar.yml`. Nunca compilar en local. `compilar.yml` crea la release como **versión normal y «latest»**: la app pregunta a `/releases/latest`, que no ve las pre-release (ADR-026). Pre-release solo si CarlosFB lo pide (`gh release edit vX.Y.Z --prerelease`), sabiendo que esa versión no avisa a nadie. Comprobar después: `curl -s https://api.github.com/repos/cferrerobonet/programaciones_fp/releases/latest \| jq -r .tag_name` |
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
