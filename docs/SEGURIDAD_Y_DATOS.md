# Seguridad y datos

## 1. Qué datos se tratan

| Dato | Personal | Dónde está |
| --- | --- | --- |
| Nombre del profesorado de cada módulo | Sí (identificativo, profesional) | Archivo `.programacion`, `.docx` y `.pdf` exportados, `ajustes.json` |
| Textos de la programación (unidades, metodología, recursos) | No | Archivo `.programacion` y documentos exportados |
| Catálogo curricular y normativa | No (públicos) | Repositorio, paquete de la app y carpeta de datos |
| Registro de la app | No (rutas y errores; nunca el contenido de la programación) | `logs/` en la carpeta de datos |

**Sin datos del alumnado.** Si alguna vez se añade un campo que pueda llevarlos, se para y se decide con CarlosFB.

## 2. Repositorio público

- **Nunca entran:** programaciones reales de profesores, nombres de profesores (salvo el de CarlosFB, que ya figura como autor), contraseñas, tokens ni la clave privada del catálogo.
- **Programaciones de referencia** para los tests de regeneración: están en la bóveda y se leen por ruta local (`-m referencias`, `scripts/regenerar.py`), que escribe los regenerados en una carpeta temporal fuera del repositorio. Las pruebas solo guardan posiciones y el principio del texto generado (que sale de la plantilla o del catálogo), nunca texto de las referencias. En la CI, los documentos de prueba se generan dentro de la prueba con datos ficticios.
- **Plantilla del documento** (`src/programaciones/recursos/plantilla/`): sale de la programación de PIICT, de CarlosFB, con `scripts/plantilla.py`, que quita los comentarios, las personas, el autor, los metadatos de SharePoint, los identificadores aleatorios de Word y el correo del departamento del pie. Se quedan los textos fijos de la plantilla, los logotipos (los mismos que ya publica Partes de salida) y la dirección y el teléfono del centro, que son públicos. Va desempaquetada, para que la barrera de secretos lea su texto; `scripts/plantilla.py comprobar` (también en la CI) busca correos, nombres y partes que no tocan.
- **Barreras:**
  - `.gitignore`.
  - `.githooks/pre-commit`, que ya pasa `scripts/comprobar_secretos.sh`. Con el código se le añadirán las comprobaciones del de Partes de salida, que permiten la plantilla `.docx` y los ficticios.
  - La CI `Secretos`, en cada push.
  - El escaneo de secretos y la protección al hacer push de GitHub.

## 3. Integridad

| Riesgo | Medida |
| --- | --- |
| Catálogo falso o manipulado en la descarga | Firma Ed25519 y versión creciente. HTTPS solo a los hosts permitidos (los de `actualizaciones.py` más `raw.githubusercontent.com`) |
| Instalador falso | Descarga solo desde las releases del repositorio (código de Partes de salida) |
| `.programacion` o datos incrustados dañados | Esquema JSON y huella SHA-256. Si fallan, se avisa y se ofrece la última versión del autoguardado |
| Documento retocado en Word después de exportarlo | Huella del texto: se avisa de que esos cambios no se recuperan |
| Plantilla con macros o contenido ajeno | La plantilla se guarda desempaquetada, solo con las partes de un .docx sin macros; una prueba comprueba que no hay `vbaProject.bin`, comentarios, personas ni customXml |

## 4. Sin login ni cifrado

Ver ADR-012. Cada profesor trabaja en su equipo y con su sesión. El documento acaba en la carpeta de Teams del centro, con los permisos que fije el centro.

## 5. Correo

Envío de programaciones por correo (RF-14, ADR-014):
- **Opción A (recomendada):** la app no guarda ninguna contraseña. Crea un borrador en el cliente de correo del profesor y es él quien lo envía.
- **Opción B o C:**
  - La contraseña va en el llavero del sistema, como en Partes de salida, nunca en `ajustes.json` ni en el repositorio.
  - Servidor, puerto y buzón se escriben en Ajustes → Correo de cada equipo, o se importan de un archivo de configuración guardado fuera del repositorio. **En el código, sus valores por defecto están vacíos** (ADR-016).
- **Destinatarios recordados:** se guardan en `ajustes.json`; son direcciones profesionales del centro.

## 6. RGPD

Tratamiento mínimo: el nombre del profesor en un documento profesional del propio centro. Sin telemetría. La app solo descarga el catálogo y las versiones, y lo único que envía es el correo que el profesor decide mandar.
