# Seguridad y datos

## 1. Qué datos se tratan

| Dato | Personal | Dónde está |
| --- | --- | --- |
| Nombre del profesorado de cada módulo | Sí (identificativo, profesional) | Archivo `.programacion`, `.docx` y `.pdf` exportados, `ajustes.json` |
| Textos de la programación (unidades, metodología, recursos) | No | Archivo `.programacion` y documentos exportados |
| Correo del departamento para el pie y carpeta de entrega de cada curso | No (direcciones profesionales y rutas del equipo) | `ajustes.json` de la carpeta de datos (y el correo, en el pie del documento). Nunca en el repositorio: valores por defecto vacíos y pruebas con `@example.com` |
| Catálogo curricular y normativa | No (públicos) | Repositorio, paquete de la app y carpeta de datos |
| Registro de la app | No (rutas y errores; nunca el contenido de la programación) | `logs/` en la carpeta de datos |

**Sin datos del alumnado.** Si alguna vez se añade un campo que pueda llevarlos, se para y se decide con CarlosFB.

## 2. Repositorio público

- **Nunca entran:** programaciones reales de profesores, nombres de profesores (salvo el de CarlosFB, que ya figura como autor), contraseñas, tokens ni la clave privada del catálogo. Esa clave (Ed25519, ADR-027) se generó el 2026-10-17 y se guardó directamente como secreto `CATALOGO_CLAVE` de GitHub, borrando el archivo en el acto: no está en el repositorio, en la carpeta 02 EPLA ni en ningún registro; solo la ve el paso «Firmar» de `catalogo.yml`. En el repositorio va solo la pública (`recursos/clave_catalogo.txt`).
- **Programaciones de referencia** para los tests de regeneración: están en la carpeta 02 EPLA y se leen por ruta local (`-m referencias`, `scripts/regenerar.py`), que escribe los regenerados en una carpeta temporal fuera del repositorio. Las pruebas solo guardan posiciones y el principio del texto generado (que sale de la plantilla o del catálogo), nunca texto de las referencias. En la CI, los documentos de prueba se generan dentro de la prueba con datos ficticios.
- **Plantilla del documento** (`src/programaciones/recursos/plantilla/`): sale de la programación de PIICT, de CarlosFB, con `scripts/plantilla.py`, que quita los comentarios, las personas, el autor, los metadatos de SharePoint, los identificadores aleatorios de Word y el correo del departamento del pie. Con `--proyecto`, añade de la programación de 0526 solo la tabla 4 y los bloques de 9, 11.1 y 11.2 de la variante de los proyectos (sin los tutores ni la metodología). Se quedan los textos fijos de la plantilla, los logotipos (los mismos que ya publica Partes de salida) y la dirección y el teléfono del centro, que son públicos. Va desempaquetada, para que la barrera de secretos lea su texto; `scripts/plantilla.py comprobar` (también en la CI) busca correos, nombres y partes que no tocan.
- **Barreras:**
  - `.gitignore`.
  - `.githooks/pre-commit`, que ya pasa `scripts/comprobar_secretos.sh`. Con el código se le añadirán las comprobaciones del de Partes de salida, que permiten la plantilla `.docx` y los ficticios.
  - La CI `Secretos`, en cada push.
  - El escaneo de secretos y la protección al hacer push de GitHub.

## 3. Integridad

| Riesgo | Medida |
| --- | --- |
| Catálogo falso o manipulado en la descarga | Firma Ed25519 de `indice.json` con la clave de la app, sha256 firmado del paquete, rutas permitidas, huella del contenido, versión mayor que la que se tiene y formato conocido (`catalogo_remoto.py`). HTTPS solo a `raw.githubusercontent.com`, rama `catalogo-publicado` de este repositorio. Pruebas: sin firma, firma mala, otra clave, paquete cambiado, rutas raras y catálogo viejo |
| Flujos de GitHub con escritura | `vigia.yml` solo escribe en ramas `vigia/…` y en sus PR, que nunca fusiona ni aprueba (ADR-028; lo comprueba `scripts/comprobar_sin_fusion.sh` en la CI). El ajuste de GitHub «Allow GitHub Actions to create and approve pull requests» está activado porque sin él el vigía no puede abrir su PR con `GITHUB_TOKEN`; `catalogo.yml` solo en la rama `catalogo-publicado`, y el secreto solo llega al paso que firma |
| Actualización de la app en macOS | Solo se monta un DMG con el sha256 publicado; el script de sustitución va en una carpeta temporal propia y recibe las rutas como argumentos; nunca borra la versión instalada antes de tener la nueva en su sitio (ADR-029) |
| Instalador falso | Descarga solo desde las releases del repositorio (código de Partes de salida) |
| `.programacion` o datos incrustados dañados | Esquema JSON y huella SHA-256. Si fallan, se avisa y se ofrece la última versión del autoguardado |
| Documento retocado en Word después de exportarlo | Huella del texto: se avisa de que esos cambios no se recuperan |
| Plantilla con macros o contenido ajeno | La plantilla se guarda desempaquetada, solo con las partes de un .docx sin macros; una prueba comprueba que no hay `vbaProject.bin`, comentarios, personas ni customXml |

## 4. Sin login ni cifrado

Ver ADR-012. Cada profesor trabaja en su equipo y con su sesión. El documento acaba en la carpeta de Teams del centro, con los permisos que fije el centro.

## 5. Correo

Envío de programaciones por correo (RF-14, ADR-014, aceptada el 2026-10-17):
- **Borrador en el programa de correo del profesor:** la app abre un correo nuevo en Mail u Outlook con los adjuntos y es el profesor quien lo revisa y lo envía desde su cuenta. **La app no guarda ninguna contraseña, no habla con ningún servidor de correo y no envía nada.**
- Los datos del correo (destinatarios, asunto, cuerpo y rutas de los adjuntos) pasan a AppleScript como argumentos y a PowerShell en un JSON temporal, nunca dentro del texto de la orden. El `.eml` de Windows se escribe en `correo/` de la carpeta de datos.
- **Destinatarios habituales:** se guardan en `ajustes.json` de cada equipo; son direcciones profesionales del centro. Por defecto, vacíos; las pruebas usan `@example.com`.
- Si algún día se enviara por SMTP (opciones B o C de ADR-014, descartadas), la contraseña iría al llavero y los datos del servidor, a Ajustes (ADR-016).

## 6. RGPD

Tratamiento mínimo: el nombre del profesor en un documento profesional del propio centro. Sin telemetría. La app solo descarga el catálogo (una vez al día, sin enviar nada salvo la petición con su versión en el agente) y las versiones, y lo único que envía es el correo que el profesor decide mandar.
