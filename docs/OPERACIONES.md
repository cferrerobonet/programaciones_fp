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
| **Actualizar la app** | Botón dorado «↑ Actualizar a X.Y.Z» → «Actualizar ahora». Los ajustes y las programaciones se conservan. **macOS, desde la 0.3.0:** la app se cierra, se sustituye en la carpeta donde está instalada (por ejemplo `/Applications/EPLA`) y se vuelve a abrir, sin arrastrar nada (ADR-029); si no hay permiso en esa carpeta, se abre el DMG y la app dice a qué carpeta arrastrarla. Registro: `logs/actualizacion_*.log`. **Para pasar a la 0.3.0** desde la 0.2.0 todavía se usa el DMG: arrastrar «Programaciones» a la carpeta donde ya estaba y sustituir. **Windows:** el instalador sustituye la versión anterior en su carpeta (`AppId` fijo) |
| **Catálogo nuevo** | La app lo comprueba al arrancar, como mucho una vez al día (o en Ajustes → Catálogo → «Comprobar ahora»), y solo lo acepta con su firma. Sale el botón dorado «§ Cambios en el currículo» y, la primera vez, la ventana con qué normas cambian, qué módulos afectan y la diferencia. «Revisar mis programaciones» abre la primera afectada: **el profesor decide** «Aceptar cambios» o «Más tarde». Lo no aceptado se recuerda (el botón cuenta las pendientes). Sin conexión, sigue con el catálogo que tiene |
| **Recuperar tras formatear o cambiar de equipo** | Instalar, abrir el `.docx` exportado desde la carpeta de Teams (o el `.programacion` de OneDrive) y seguir |
| **Heredar una programación** | «Nueva a partir de…» → elegir el `.docx` del curso anterior en Teams → revisar y confirmar cada bloque |
| **Empezar un curso nuevo** | Al primer arranque del curso, la app pide la carpeta de entrega nueva. Las programaciones del curso anterior se heredan |

## Para el mantenedor (CarlosFB)

| Tarea | Cómo |
| --- | --- |
| Publicar una versión de la app | Skill `publicar`: versión, `CHANGELOG.md` (que es lo que ven los profesores en la ventana de novedades), commit, push, etiqueta `vX.Y.Z` y seguimiento de `compilar.yml`. Nunca compilar en local. `compilar.yml` crea la release como **versión normal y «latest»**: la app pregunta a `/releases/latest`, que no ve las pre-release (ADR-026). Pre-release solo si CarlosFB lo pide (`gh release edit vX.Y.Z --prerelease`), sabiendo que esa versión no avisa a nadie. Comprobar después: `curl -s https://api.github.com/repos/cferrerobonet/programaciones_fp/releases/latest \| jq -r .tag_name` |
| Compilación de prueba, sin publicar | `gh workflow run compilar.yml` (o Actions → Compilar → *Run workflow*; `-f plataforma=macos\|windows`, `-f depurar=true`). Pasa las pruebas, compila, comprueba los datos empaquetados (`scripts/comprobar_paquete.sh`) y arranca la app en las dos plataformas. Los instaladores quedan como artefactos de la ejecución (`gh run download <id>`) |
| Vigilar el vigía | Cada lunes (Actions → Vigía). **Nada se publica solo** (ADR-028): si el vigía encuentra algo, abre una PR asignada a CarlosFB (llega el aviso de GitHub) y espera; ver «Cuando el vigía abre una PR». Si el vigía falla porque una fuente no responde, no ha tocado nada: se vuelve a lanzar (`gh workflow run vigia.yml`) |
| Publicar el catálogo a mano | Cuando un cambio de `catalogo/` llega a `main` (una PR del vigía que fusiona CarlosFB o un cambio suyo, por ejemplo de `cursos/`), `catalogo.yml` firma y publica; `construir` y `scripts/catalogo.py version` suben la versión (`comprobar` avisa si falta). Para forzarlo: `gh workflow run catalogo.yml`. Comprobar lo publicado: `scripts/catalogo.py verificar https://raw.githubusercontent.com/cferrerobonet/programaciones_fp/catalogo-publicado` |
| **Alta del curso escolar** (cada julio-septiembre; el vigía abre una incidencia) | `catalogo/cursos/AAAA-AAAA.yaml`: fechas de evaluación, ordinaria y extraordinaria; resolución de instrucciones; periodos de empresa por curso y jornada; optativos ofertados si cambian. Fuente: las notas del curso en la bóveda. Después, `scripts/catalogo.py version` y push: `catalogo.yml` lo publica |
| Cambio de plantilla del departamento | `scripts/plantilla.py crear <programación nueva de referencia> --proyecto <la del Proyecto>` (subir `VERSION` en el script), revisar las marcas, `scripts/regenerar.py` con las referencias, `pytest -m referencias` y versión menor de la app |
| Rotar la clave del catálogo | Solo si se cree comprometida. Generar la clave nueva fuera del repositorio, `gh secret set CATALOGO_CLAVE < archivo` y borrar el archivo en el acto; pública nueva en `src/programaciones/recursos/clave_catalogo.txt` y versión de la app. Los equipos que no actualicen dejan de recibir catálogos (ADR-027) |

## Cuando el vigía abre una PR

La PR se llama «Currículo: …», lleva la etiqueta `vigia`, está asignada a CarlosFB y dice qué norma o documento ha cambiado (con su huella vieja y nueva), la diferencia por módulo y, si hace falta, la lista «Revisar a mano». Un comentario del vigía dice si las comprobaciones automáticas han salido en verde. **El vigía nunca la fusiona ni la aprueba:** todo cambio pasa por CarlosFB (ADR-028), también los de solo texto con todo en verde.

1. **Leer la diferencia** (lo que verá el profesor) y abrir el enlace de cada norma. Si solo cambia el texto de RA o criterios de un real decreto, basta con comprobarlo en el BOE. Si hay lista «Revisar a mano», según lo que sea:
   - **PDF del DOGV o horas** (R2): comprobar en el PDF que lo que ha leído `construir` es lo que dice el anexo.
   - **Referencia posterior nueva o norma nueva:** ver si reescribe módulos, el art. 4 o el anexo V. Si sí, añadirla a la receta de `scripts/catalogo.py` (`CICLOS`: `reescritos`, `art4`, `anexo_v`) y en local `construir todo`; si no, basta con lo que trae la PR (la norma pasa a la normativa del documento).
   - **Texto consolidado, sumario del BOE o página de la Conselleria:** decidir si afecta a algún ciclo. Si no, nada que tocar: la PR solo anota que ya se ha visto.
   - **No se ha podido leer:** arreglar el lector o la receta, nunca el YAML (regla `catalogo.md`).
2. **En local**, con la rama de la PR (`gh pr checkout <n>`): `scripts/catalogo.py comprobar --red`, `pytest` y `PROGRAMACIONES_REFERENCIAS=… pytest -m referencias` si cambian RA de las seis referencias. Si se corrige algo, commit a esa rama.
3. **Fusionarla CarlosFB** (botón «Squash and merge» o `gh pr merge <n> --squash`). Si las comprobaciones salieron en rojo, corregir antes. Si no hay que publicar nada, cerrarla.
4. **Qué pasa después:** al llegar a `main`, `catalogo.yml` firma y publica la versión nueva en la rama `catalogo-publicado` (Actions → Catálogo, en verde). Cada equipo la descarga al arrancar (como mucho una vez al día), ve el aviso «§ Cambios en el currículo» y **cada profesor acepta** los cambios en su programación (ADR-015). Nadie tiene que reinstalar.
5. **Si un cambio publicado está mal:** corregir la receta o el lector, `construir`, push: sale otra versión que lo deshace (la app nunca acepta una versión menor).

## Diagnóstico

- **Registro:** `<carpeta de datos>/logs/app_AAAAMMDD.log` y `faulthandler.log`; en macOS, la actualización en su sitio deja `actualizacion_*.log`.
- **Catálogo publicado:** Ajustes → Catálogo (versión, origen y última comprobación); `<carpeta de datos>/catalogo/estado.json` y `catalogo/versiones/`. Si no se acepta («firma no válida»), la app sigue con el que tenía: revisar Actions → Catálogo.
- **Carpeta de datos:** macOS `~/Library/Application Support/Programaciones` · Windows `%APPDATA%\Programaciones`.
- **El PDF no sale:** comprobar que hay Word o LibreOffice (Ajustes → Exportación). Mientras tanto, exportar solo en Word.
- **«Datos incrustados no válidos»:** abrir la última versión de `autoguardado/` o el `.programacion`.
- **macOS dice que la app «está dañada y no se puede abrir»:** no lo está; la app no lleva certificado de pago de Apple (firma ad hoc) y el aviso es el mismo que el de un archivo roto. Una vez por equipo: arrastrar «Programaciones» a Aplicaciones, abrir Terminal y ejecutar `xattr -dr com.apple.quarantine "/Applications/Programaciones.app"` (solo quita la marca de «descargado de internet»). El DMG ya no lleva un «LÉEME» con estos pasos (CarlosFB, 2026-10-17: las apps abren bien). Solo Mac con chip de Apple.
