# Registro de decisiones (ADR)

Formato: contexto → decisión → consecuencias. Una decisión no se reescribe: si cambia, se añade otra que la sustituye y se marca la anterior. Estado: **Aceptada** (confirmada por CarlosFB) o **Propuesta** (pendiente de su visto bueno). Fecha en `AAAA-MM-DD`.

## ADR-001 · App de escritorio Python + PyQt6, al estilo de Partes de salida — 2026-10-14 · Aceptada

- **Contexto.** Se valoraron tres opciones:
  - **A · Web propia en Python con un servidor pequeño.** Era la más completa, pero no hay presupuesto.
  - **B · Web en PHP en el IONOS actual, o dentro de Web Pedidos.** Sin PDF en el servidor (no se puede instalar LibreOffice), con más superficie de ataque en una app que maneja importes y datos personales, y las programaciones no encajan en una app de pedidos.
  - **C · App de escritorio.** Es la elegida.
- **Decisión.** Escritorio con Python 3.11 y PyQt6 6.7, PyInstaller y publicación en GitHub, con la misma base que Partes de salida.
- **Consecuencias:**
  - Se reutilizan su interfaz, sus actualizaciones, su CI y sus ganchos (`TRD.md` §2).
  - El PDF lo hace el Word del equipo.
  - No hay panel central: las programaciones se entregan en Teams.

## ADR-002 · Sin base de datos ni servidor: los datos viajan en el documento — 2026-10-14 · Aceptada

- **Contexto.** Guardias de patio sincroniza por SFTP con IONOS por el puerto 22. Con muchos profesores habría muchas conexiones seguidas, justo lo que hace que IONOS cierre ese puerto, que necesitan los despliegues de las otras apps. Además, una programación se hace una vez al año y es de un profesor.
- **Decisión:**
  - Archivo de trabajo `.programacion` (JSON), que el profesor guarda donde quiera.
  - Al exportar, el `.docx` lleva dentro una copia completa de los datos (parte XML personalizada) con sus huellas.
  - El `.docx` que se sube a Teams es a la vez la entrega y la copia de seguridad.
- **Consecuencias:**
  - Si se formatea un equipo, se abre el `.docx` de Teams y se recupera todo.
  - SharePoint guarda además el historial de versiones.
  - Hay que comprobar que Word conserva esa parte al guardar (riesgo R1).

## ADR-003 · Ciclos y módulos fijos, sin pantalla de configuración — 2026-10-14 · Aceptada

- **Contexto.** CarlosFB: «son siempre los mismos cada año».
- **Decisión.** Los 11 ciclos de GM y GS y sus 176 módulos van en el catálogo de la app (listado en la nota de la bóveda «PROGRAMACIONES — Ciclos y módulos», sacado de Web Pedidos y del Decreto 114/2025).
- **Consecuencias.** Si una norma cambia los módulos, es una actualización del catálogo, no un ajuste.

## ADR-004 · Grado Básico fuera hasta tener su modelo — 2026-10-14 · Aceptada

- **Decisión.** Solo GM y GS. Grado Básico se añadirá cuando CarlosFB tenga la programación modelo que usan.

## ADR-005 · Catálogo curricular en el repositorio, vigía en GitHub Actions y canal propio de publicación — 2026-10-14 · **Sustituida por ADR-015** en cuanto a quién aprueba (el resto sigue vigente)

- **Contexto.** La app tiene que actualizar sola los RA y la normativa a partir de fuentes oficiales, de forma transparente para el profesor, y sin servidor.
- **Decisión propuesta:**
  - El catálogo se guarda en YAML en `catalogo/` del repositorio.
  - Un flujo semanal (`vigia.yml`) comprueba BOE y DOGV, rehace lo afectado y abre una PR con las diferencias.
  - Al fusionarla, `catalogo.yml` lo firma (Ed25519) y lo publica en `catalogo/publicado/`.
  - La app lo descarga de `raw.githubusercontent.com` sin reinstalar y lo avisa con la misma ventana de novedades que las versiones.
- **Alternativa descartada.** Meter el catálogo solo dentro de la app y publicar una versión por cada cambio normativo. Es más simple, pero obliga a reinstalar por un criterio de evaluación.
- **Aprobación.** Resuelta en ADR-015: cada profesor, no CarlosFB.

## ADR-006 · Documento desde la plantilla vigente con docxtpl — 2026-10-14 · Aceptada

- **Contexto.** La plantilla de referencia es la programación de PIICT (0517), vigente desde el 2026-10-06. La del departamento («Plantilla para GM y GS_base SIRL») sirve para GM y GS. Generar el Word desde cero perdería encabezado, pie, franja vertical e índice.
- **Decisión:**
  - Se convierte una copia de la plantilla en plantilla con marcas Jinja (`docxtpl`).
  - Tras rellenarla, un retoque con `lxml` añade los hipervínculos, `updateFields` y `keepNext`.
  - La plantilla lleva versión. Si el departamento la cambia, sale una plantilla nueva y una versión de la app.
- **Consecuencias.** El criterio de aceptación es regenerar las seis programaciones revisadas en 2026-10.

## ADR-007 · Textos fijos ocultos en la app — 2026-10-14 · Aceptada

- **Contexto.** CarlosFB: los textos fijos meten ruido al profesor.
- **Decisión.** La interfaz solo enseña los datos del módulo y los bloques manuales. Los textos fijos aparecen en la vista previa y en el documento.

## ADR-008 · Herencia con confirmación obligatoria — 2026-10-14 · Aceptada

- **Contexto.** Hay datos 100 % manuales que solo conoce el profesor de cada módulo. Un profesor puede heredar un módulo de otro, o partir de su programación del curso anterior.
- **Decisión:**
  - «Nueva a partir de…» copia los bloques manuales como **heredados** y actualiza lo oficial y las fechas.
  - La definitiva exige confirmar o cambiar cada bloque heredado.
  - La app nunca inventa ni completa datos manuales.
- **Consecuencias.** Se guarda de quién y de qué curso viene la programación.

## ADR-009 · Entrega en la carpeta de Teams de cada curso — 2026-10-14 · Aceptada

- **Contexto.** Sin administrador de Microsoft 365 no se puede integrar con Teams. La carpeta es la misma para todos los profesores en un curso y cambia cada curso.
- **Decisión:**
  - Cada profesor introduce en Ajustes la carpeta del curso: una ruta sincronizada con OneDrive o el enlace de Teams.
  - Si es una ruta local, la app exporta directamente en ella.
  - Si es un enlace, exporta en local y abre la carpeta de Teams en el navegador.
- **Consecuencias.** La app pide la carpeta al empezar cada curso escolar.

## ADR-010 · Mismo sistema de actualizaciones y novedades que Partes de salida — 2026-10-14 · Aceptada

- **Decisión.** Se copian `actualizaciones.py` y `DialogoActualizacion` (API de GitHub con plan B por la web, hosts permitidos, `certifi`, novedades en Markdown desde `CHANGELOG.md`, descarga e instalador), cambiando el repositorio a `cferrerobonet/programaciones_fp`.
- **Consecuencias.** El repositorio es público, así que los equipos consultan las releases sin cuenta.

## ADR-011 · Compilar solo en GitHub — 2026-10-14 · Aceptada

- **Decisión.** Como en Partes de salida: etiqueta `vX.Y.Z` → `compilar.yml` (DMG, instalador y portable, con prueba de arranque). El gancho bloquea compilar en local.

## ADR-012 · Sin login ni cifrado — 2026-10-14 · Aceptada

- **Contexto.** Cada profesor usa su equipo. La programación no tiene datos del alumnado: solo nombres de profesores y textos que acaban siendo públicos para el centro.
- **Decisión.** Sin usuarios ni contraseñas, y sin cifrado local. Se confía en la sesión del sistema.
- **Consecuencias.** Menos código que Partes de salida: no hacen falta `cifrado.py` ni `keyring`.

## ADR-013 · Catálogo y plantilla preparados para varios idiomas — 2026-10-14 · Aceptada

- **Contexto.** A CarlosFB le gusta poder sacar la programación también en valenciano y en inglés. Todavía no está definido cómo, pero añadirlo después a un catálogo de un solo idioma obligaría a rehacer el formato.
- **Decisión:**
  - Desde la 1.0, cada texto del catálogo se guarda por idioma (`{es: …}`).
  - La plantilla vive en `recursos/plantilla/<idioma>/`.
  - La interfaz sigue solo en castellano.
- **Consecuencias.** La 1.0 solo exporta en castellano. La función se define en la fase F10 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md)).

## ADR-014 · Envío por correo de una o varias programaciones — 2026-10-14 · Propuesta (la función está aceptada; falta elegir el mecanismo)

- **Contexto.** CarlosFB quiere poder enviar por email una o varias programaciones. Partes de salida ya envía correo:
  - Módulo `correo.py`, con el servidor de correo del centro y el buzón compartido de las apps (sus datos no se escriben en el repositorio: ver ADR-016).
  - Contraseña en el llavero del sistema.
  - Envío en un hilo (`Tarea`), con el aviso de enviado o no enviado.
- **Opciones:**

| Opción | Cómo | A favor | En contra |
| --- | --- | --- | --- |
| **A · Borrador en el correo del profesor** (recomendada) | La app crea el mensaje con los adjuntos en Outlook (o Mail en macOS) y el profesor lo revisa y lo envía desde su cuenta del centro | Sale de su cuenta y queda en sus enviados. Sin contraseñas en la app. Las respuestas le llegan a él | Depende de tener Outlook o Mail configurado. En macOS por AppleScript y en Windows por COM de Outlook |
| B · SMTP con el buzón de las apps | `correo.py` de Partes de salida | Código probado. Sin cliente de correo | Habría que dar la contraseña del buzón compartido a todo el profesorado de FP. Las respuestas no llegan al profesor |
| C · SMTP con la cuenta del profesor | `correo.py` con el servidor de Microsoft 365 | Sale de su cuenta | El inquilino puede tener desactivado el SMTP autenticado y no hay administrador para activarlo |

- **Decisión propuesta.** A, con B como alternativa si un equipo no tiene cliente de correo. Si se usa B o C, se recupera de Partes de salida el llavero (`keyring`) para la contraseña, lo que matiza ADR-012.
- **Común a todas:**
  - Un solo mensaje con todos los adjuntos.
  - Formatos a elegir (Word, PDF o ambos).
  - Destinatarios recordados en los ajustes.
  - Asunto de plantilla: «Programaciones <curso escolar> · <profesor> · <n> módulos».
  - Aviso antes de enviar si los adjuntos superan el tamaño máximo (dato pendiente).

## ADR-015 · Cada profesor aprueba los cambios de currículo en su programación — 2026-10-14 · Aceptada

- **Contexto.** ADR-005 proponía que CarlosFB aprobara cada cambio fusionando la PR del vigía. CarlosFB decide que los apruebe **cada usuario, es decir, cada profesor**.
- **Decisión:**
  - **El vigía publica solo** si pasan las comprobaciones automáticas: esquema, diferencias legibles, enlaces vivos y regeneración de las programaciones de referencia. Abre la PR y la fusiona él mismo, y `catalogo.yml` firma y publica. Si alguna comprobación falla, la PR queda abierta para CarlosFB.
  - **La app descarga el catálogo nuevo,** pero **no lo aplica** a ninguna programación por su cuenta.
  - **Al abrir una programación** de un módulo afectado, enseña las diferencias en la ventana de novedades («Cambios en el currículo») con «Más tarde» y «Aceptar cambios».
  - **Al aceptar,** la programación pasa a la versión nueva del catálogo, se recalcula lo automático y se señalan los bloques manuales afectados: por ejemplo, unidades que apuntaban a un RA que ya no existe.
  - **Mientras no acepta,** la programación sigue con su versión del catálogo y la app lo recuerda (validación V-08, ámbar).
- **Consecuencias:**
  - Ninguna actualización pasa por CarlosFB, pero él puede ver el historial de PR y deshacer un cambio publicando otra versión del catálogo.
  - Riesgo R7 (un RA mal extraído): lo frenan las comprobaciones automáticas y que cada profesor ve la diferencia antes de aceptarla.

## ADR-016 · Ningún dato del servidor de correo en el repositorio — 2026-10-14 · Aceptada

- **Contexto.** La app podrá enviar correo (ADR-014) y el repositorio es público. CarlosFB pide que no llegue al repositorio información del servidor SMTP, ni ahora ni en el futuro. El `ajustes.py` de Partes de salida, que se iba a copiar, lleva escritos servidor, puerto y buzón como valores por defecto.
- **Decisión:**
  - **Ni en el código ni en la documentación** se escriben servidor, puerto, buzón, usuario ni contraseña del correo. Se habla de «el servidor de correo del centro» o de «el buzón compartido de las apps».
  - **Al copiar `ajustes.py` y `correo.py`,** los campos del correo quedan **vacíos** por defecto.
  - **Los datos reales** se introducen en Ajustes → Correo de cada equipo, o se importan de un archivo de configuración que se guarda fuera del repositorio. La contraseña va al llavero del sistema.
  - **Tres barreras:**
    - `scripts/comprobar_secretos.sh` desde `.githooks/pre-commit`, en cada commit.
    - El mismo script en `.github/workflows/secretos.yml`, en cada push y PR.
    - El escaneo de secretos y la protección al hacer push de GitHub, activados en el repositorio.
- **Consecuencias.** Si un commit lleva un dato así, no se confirma. Si se cuela, la CI falla. Un test de la suite pasa el script sobre todo el árbol.
