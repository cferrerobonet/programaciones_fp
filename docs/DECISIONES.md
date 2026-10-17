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

## ADR-005 · Catálogo curricular en el repositorio, vigía en GitHub Actions y canal propio de publicación — 2026-10-14 · **Sustituida por ADR-015** en cuanto a quién aprueba y **por ADR-027** en dónde se publica (el resto sigue vigente)

- **Contexto.** La app tiene que actualizar sola los RA y la normativa a partir de fuentes oficiales, de forma transparente para el profesor, y sin servidor.
- **Decisión propuesta:**
  - El catálogo se guarda en YAML en `catalogo/` del repositorio.
  - Un flujo semanal (`vigia.yml`) comprueba BOE y DOGV, rehace lo afectado y abre una PR con las diferencias.
  - Al fusionarla, `catalogo.yml` lo firma (Ed25519) y lo publica en `catalogo/publicado/`.
  - La app lo descarga de `raw.githubusercontent.com` sin reinstalar y lo avisa con la misma ventana de novedades que las versiones.
- **Alternativa descartada.** Meter el catálogo solo dentro de la app y publicar una versión por cada cambio normativo. Es más simple, pero obliga a reinstalar por un criterio de evaluación.
- **Aprobación.** Resuelta en ADR-015: cada profesor, no CarlosFB.

## ADR-006 · Documento desde la plantilla vigente con docxtpl — 2026-10-14 · Aceptada; **la herramienta, sustituida por ADR-019** (lxml con marcas propias)

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

## ADR-014 · Envío por correo de una o varias programaciones — 2026-10-14 · **Aceptada el 2026-10-17: opción A** (decisión e implementación al final)

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
- **Decisión** (CarlosFB, 2026-10-17): **opción A, borrador en el programa de correo del profesor.** La app abre un correo nuevo con los adjuntos y los destinatarios; el profesor lo revisa y lo envía desde su cuenta. La app no guarda contraseñas ni envía nada por sí misma.
  - **Destinatarios:** lista editable en Ajustes → Correo; al enviar se eligen de la lista (chips) y se pueden añadir otros.
  - **Adjuntos:** Word, PDF o ambos, elegidos al enviar; por defecto, los de Ajustes → Exportación. Si falta el archivo exportado (en la carpeta de entrega del curso o, con un enlace de Teams o sin carpeta, en «Documentos/Programaciones <curso>», ADR-021), se exporta antes con el nombre normalizado. Uno exportado antes de los últimos cambios se adjunta tal cual, con aviso, salvo que el profesor marque «Exportar de nuevo» (sustituye ese archivo). Una programación con avisos en rojo y sin exportar no se adjunta.
  - **Asunto y cuerpo:** plantillas de Ajustes → Correo («Programación didáctica — {modulo} ({curso})», en plural «Programaciones didácticas — {n} módulos ({curso})», y un cuerpo con {archivos} y {profesor}), editables también en la ventana de enviar.
  - **Tamaño:** aviso si los adjuntos pasan de **20 MB**.
- **Implementación por plataforma** (`correo.py`; se prueba siempre con un programa de correo simulado, nunca con uno real):

| Plataforma | Método | Por qué | Si falla |
| --- | --- | --- | --- |
| macOS | **Mail** o **Outlook** con AppleScript (`osascript -e`, script fijo con `on run argv`): `make new outgoing message`, destinatarios y `make new attachment` con la ruta POSIX | Es la única forma de dar adjuntos a un borrador en macOS (`mailto:` no admite adjuntos). Los datos van como argumentos, no dentro del script: ni comillas ni inyección | Reserva |
| macOS, ¿cuál? | Ajustes → Correo → Programa de correo: «Automático» lee el programa de `mailto` de LaunchServices (`com.apple.launchservices.secure.plist`); si es Outlook, Outlook; si no, Mail. También se elige a mano | El nuevo Outlook de Mac tiene un AppleScript limitado: si falla, la reserva lo abre igual | — |
| Windows | **Outlook clásico por COM** (PowerShell, como el PDF con Word): `CreateItem(0)`, `To`, `Subject`, `Body`, `Attachments.Add` y `Display()`. Los datos, en un JSON temporal | COM es el camino fiable para Outlook clásico, el del centro. **`MAPISendMail` (MAPI simple) se descarta:** exige la misma arquitectura (32/64 bits) que Outlook, con `MAPI_DIALOG` deja la app esperando a que se cierre el correo y no se puede probar sin un Outlook instalado | `.eml` |
| Windows, alternativa | Un **`.eml` con `X-Unsent: 1`** (estándar `email` de Python, adjuntos incluidos) que se abre con el programa por defecto: Outlook lo abre como correo nuevo listo para enviar | Funciona sin COM (Outlook nuevo, otros programas) | Reserva |
| **Reserva, siempre** | Se abre la carpeta con los archivos y un `mailto:` con destinatarios, asunto y cuerpo; la app avisa de que hay que adjuntarlos a mano | `mailto:` no lleva adjuntos, pero siempre hay un programa que lo abre | Error claro |

- **Consecuencias.** Sin contraseñas ni servidor de correo en la app (se cumplen ADR-012 y ADR-016 sin el llavero). El correo sale de la cuenta del profesor y queda en sus enviados. Queda por comprobar a mano en un Mac con Mail y con Outlook y en un Windows con Outlook clásico (`docs/PENDIENTE.md`).

## ADR-015 · Cada profesor aprueba los cambios de currículo en su programación — 2026-10-14 · Aceptada; **«el vigía publica solo», sustituido por ADR-028** (todo lo publica CarlosFB al fusionar; lo demás sigue vigente)

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

## ADR-017 · Reglas de lectura del catálogo — 2026-10-17 · Aceptada (las tres dudas, resueltas en ADR-018)

- **Contexto.** En F1 se ha visto que:
  - Los reales decretos de los títulos no están consolidados en el BOE.
  - El Decreto 95/2026 cambió las horas del Decreto 114/2025 en junio de 2026.
  - Los anexos del DOGV de los módulos comunes amplían los del RD 659/2023.
  - El BOE tiene erratas de texto y de numeración.
  - Algunos módulos tienen texto distinto según el título.
- **Decisión:**
  - **Horas y módulos:** los del Decreto 95/2026 (anexo IV), que da nueva redacción a los anexos I y II del Decreto 114/2025.
  - **Módulos propios:** el original del real decreto más lo que reescriben las normas que lo modifican, revisadas una a una ([CATALOGO_Y_FUENTES.md](CATALOGO_Y_FUENTES.md) §5).
  - **Texto literal,** también con las erratas. La numeración es la posición; lo que imprime el BOE se guarda en `n_boe` y `letra_boe`.
  - **Módulo en dos títulos:** un archivo si el texto coincide; si no, uno por título.
  - **Lo ambiguo no se supone:** competencias numeradas en GA e IT, UC sin ECP. Queda pendiente.
- **Alternativas descartadas:**
  - Las horas de la nota «Ciclos y módulos» de la bóveda: eran las del Decreto 114/2025 original.
  - Un solo archivo para 0237, 0238 y 0260: habría que elegir el texto de un título para el otro.
- **Dudas** (resueltas por CarlosFB el 2026-10-17 en ADR-018):
  - Texto literal del BOE o corrección de sus erratas, como hacen ya 0517 y 0524.
  - Nombre del real decreto o del decreto valenciano cuando no coinciden.
  - Denominación de los ECP: la del RD 532/2025 o la de la UC en el anexo V B).
- **Consecuencias.** `comprobar` y la prueba `-m referencias` vigilan estas reglas. Si CarlosFB decide corregir las erratas, se hará con una lista de correcciones en la receta, con su motivo, nunca editando el YAML.

## ADR-018 · Decisiones de CarlosFB sobre el catálogo y el documento — 2026-10-17 · Aceptada

- **Contexto.** Las dudas de ADR-017 y las que salieron al preparar F2.
- **Decisión** (CarlosFB, 2026-10-17):
  1. **Erratas del BOE:** el catálogo guarda el texto literal y una lista de correcciones con su motivo (`CORRECCIONES` y `CORRECCIONES_CICLO` en `scripts/catalogo.py`; en el YAML, `corregido` y `correccion`), y el documento sale **corregido**, como las programaciones de 0517 y 0524. Lo mismo con la UC0626_3 de EMV, errata del RD 499/2024 (`ERRATAS_UC`: su art. 6 y el RD 532/2025 dicen 0626_2).
  2. **ECP:** la denominación del **RD 532/2025**, el vigente. Las programaciones de SEA tienen otra en cinco ECP: diferencia esperada en la regeneración.
  3. **Nombre del módulo** (0292, 0343, 0361, 0364, 0365, 0438, 0454 y 0959): en la portada, en la tabla del apartado 2 y en el nombre del archivo, el del **Decreto 95/2026** (el del ciclo en el catálogo). Los RA siguen saliendo del real decreto.
  4. **El Decreto 95/2026 se cita en el apartado 1.2.** Las referencias no lo tienen: diferencia esperada.
  5. **GA e IT:** la competencia 1 es la letra a), la 2 la b)… (con la ñ, como las orientaciones del anexo I). El catálogo guarda la letra y el número del BOE (`numero_boe`) y el documento usa letras en todos los ciclos.
  6. **Módulos comunes:** el texto del **DOGV** (Decreto 114/2025), que amplía el RD 659/2023.
  7. **Horas de centro por RA:** la propuesta redondea cada reparto al entero más cercano y lo que sobre o falte va al RA con más horas de los redondeados; el profesor lo puede retocar (`centro_ajustado`, V-04). En PIICT la regla da 7 / 9 / 12 en los RA 3, 4 y 6; la programación lleva 8 / 10 / 10, que se trata como ajuste del profesor.
  8. **Forma: mandan la plantilla de PIICT y el texto oficial.** El título de la resolución del curso es el oficial del DOGV; los periodos de empresa de 1.º, la fila de horas de centro de la tabla 4 (sin los RA), el párrafo del anexo V B) y el real decreto en la cabecera de la tabla 4 siguen la plantilla. Las referencias que no lo hacen se alinean al regenerar.
  9. **Pesos puestos a mano: ajuste del profesor.** La app propone el peso de cada elemento y el profesor lo puede cambiar (`peso_ajustado`, con su texto si lo escribe de otra forma, «1,25 % / x práctica»); los pesos tienen que sumar el % de centro del módulo (V-12). La columna «% del curso (aprox.)» de la tabla 4.1 es opcional (`columna_pct_curso`). Los pesos de 0962 y 0963 se reproducen como ajustes, igual que el 8 / 10 / 10 de PIICT.
  10. **Variante de plantilla para todos los proyectos** (ADR-020).
  11. **Correo del departamento, en Ajustes de la app**, nunca en el repositorio: el motor lo pinta en el pie si se le da (`correo_pie`); la pantalla de Ajustes llega en F4.
- **Consecuencias.** Sin dudas abiertas en las reglas de lectura ni en el documento. La prueba de regeneración marca como esperadas por decisión las diferencias de los puntos 2, 3, 4 y 8, cada una con su motivo; con los puntos 9 y 10, las de los pesos, la columna de 4.1 y la tabla del Proyecto desaparecen.

## ADR-019 · Motor del documento con lxml y plantilla desempaquetada — 2026-10-17 · Aceptada

- **Contexto.** ADR-006 preveía `docxtpl` (Jinja dentro de Word). Al hacer F2 se vio que el documento necesita cosas que docxtpl no da o da mal: reiniciar la numeración de los criterios en cada RA, insertar las normas del título en su sitio por fecha entre las fijas de la plantilla, combinar celdas en vertical en la tabla 4, quitar una columna de la tabla 4.1 cuando el módulo no tiene empresa y crear hipervínculos dentro de un párrafo. Además, un `.docx` en un repositorio público es un binario que la barrera de secretos no lee.
- **Decisión:**
  - **Motor propio con lxml** (`documento.py`) sobre marcas en la plantilla: `{{nombre}}` (texto o hipervínculos), `{{*lista}}` (párrafo que se repite), `{{@lista.campo}}` (fila de tabla que se repite), `{{#grupo}}…{{/grupo}}` (grupo que se repite, con sus listas reiniciadas) y `{{?condición}}…{{/condición}}` (bloque que solo queda si se cumple o que el profesor sustituye: ADR-020).
  - **Plantilla desempaquetada** en `src/programaciones/recursos/plantilla/es/` (las partes XML del .docx y los logotipos) y generada por `scripts/plantilla.py crear` desde la programación de PIICT: la barrera de secretos lee su texto, cada cambio se ve en git y la app la empaqueta en memoria. Versión en `plantilla.yaml`.
- **Consecuencias:**
  - Sin dependencias nuevas (ni docxtpl, ni python-docx, ni Jinja2): solo lxml, que ya estaba.
  - Un cambio de plantilla del departamento es volver a pasar `scripts/plantilla.py crear` con la programación nueva y regenerar las referencias (R5).

## ADR-020 · Variante de plantilla para los proyectos y textos propios del profesor — 2026-10-17 · Aceptada

- **Contexto.** La programación del Proyecto intermodular (0526) no tiene exámenes ni prácticas de taller: su tabla 4 (tareas), su calificación (apartado 9), sus instrumentos (11.1) y sus elementos de evaluación (11.2) no son los de PIICT.
- **Decisión** (CarlosFB, 2026-10-17):
  - **Variante de la plantilla para todos los proyectos:** `scripts/plantilla.py crear` toma de la programación de 0526 su tabla 4 y esos bloques, con sus numeraciones y enlaces, y los pone en la plantilla dentro de `{{?proyecto}}`; los de PIICT van dentro de `{{?no_proyecto}}`. Las tareas («T01 a T08») las cuenta la app con los elementos de tipo T. Nada personal de 0526 entra (ni los tutores ni la metodología, que son del profesor).
  - **Textos propios:** cualquier módulo puede sustituir esos cuatro bloques por sus párrafos (`textos_propios`: `calificacion`, `instrumentos`, `elementos`, `asistencia_y_pruebas`). La importación los detecta cuando una programación no coincide con la variante que le toca.
- **Consecuencias.** ADR-007 se mantiene: la interfaz no enseña el texto fijo; en F4, los textos propios serán opcionales («Usar un texto propio»). 0526 se regenera con su propia tabla y sus textos, sin datos importados de más.

## ADR-021 · Exportar en «Documentos/Programaciones <curso>» cuando la carpeta de entrega es un enlace de Teams — 2026-10-17 · Aceptada

- **Contexto.** ADR-009 permite poner en Ajustes el enlace de Teams en vez de una carpeta sincronizada; con un enlace, la app no puede escribir en la carpeta del curso y tiene que exportar en local.
- **Alternativas:** preguntar dónde guardar en cada exportación; la carpeta de datos de la app (oculta para el profesor); una carpeta fija en Documentos.
- **Decisión** (CarlosFB, 2026-10-17): la app exporta en «Documentos/Programaciones <curso escolar>» de ese equipo y, al terminar, ofrece «Abrir la carpeta de Teams» (el enlace) para subir los archivos.
- **Consecuencias.** Sin preguntas en el camino de exportar (DESIGN.md). Con una carpeta sincronizada, como siempre, se exporta directamente en ella.

## ADR-022 · La metodología propia de más de 600 caracteres solo avisa — 2026-10-17 · Aceptada

- **Contexto.** DESIGN.md fija un máximo de 600 caracteres para el texto libre de metodología, pero las programaciones importadas o heredadas lo pasan.
- **Alternativas:** cortar el texto al límite; quitar el límite; avisar sin cortar.
- **Decisión** (CarlosFB, 2026-10-17): la app cuenta los caracteres y, si pasa de 600, lo dice en ámbar («resúmelo si puedes»), sin cortar ni bloquear la exportación.
- **Consecuencias.** Nunca se pierde texto del profesor. No es una validación V-xx.

## ADR-023 · Fechas del curso 2026-2027 desde las notas de la bóveda — 2026-10-17 · Aceptada

- **Contexto.** Faltaban las fechas de GM y de 1.º; sin ellas no existía `catalogo/cursos/2026-2027.yaml` y la definitiva estaba bloqueada (V-11).
- **Decisión** (CarlosFB, 2026-10-17): `cursos/2026-2027.yaml` sale de las notas «Calendario escolar FP 2026-2027», «Calendario FE (prácticas en empresa) 2026-2027» y «No lectivos 2026-2027» de la bóveda (02 CURSOS ESCOLARES/2026-2027), con la fuente citada en el archivo:
  - **Evaluaciones** comunes a GB, GM y GS: inicial 2026-09-30, 1.ª 2026-11-20, 2.ª 2027-02-26, **3.ª 2027-05-28**, ordinaria del 2027-05-31 al 2027-06-03 y extraordinaria desde el 2027-06-14.
  - **Formación en empresa:** los bloques de la propuesta del centro tal como están confirmados, incluida la FE de Pascua. El itinerario «1.º + 2.º» es el mismo para los GM (IEA, IT, CAR, EMV) y los GS (ARI, STI, SEA, AUT, ADM, ISO); 1.º de GA va en febrero (excepción por ciclo, `formacion_empresa_ciclo`). Sin sufijo, jornada de 8 h; «- 7h», de 7 h: quien hace 7 h/día hace el bloque de 8 h y los días «- 7h» de su curso, como en las programaciones de 1.º revisadas el 2026-10-06.
  - **Fin de la 3.ª evaluación: el 2027-05-28, no el 2027-05-27 del calendario escolar oficial** (CarlosFB, 2026-10-11; confirmado el 2026-10-17, tras un primer encargo con el 27/05 que fue un error). Es el viernes que fija la propuesta de FE del centro, que acaba la FE de 1.º ese día, y el que llevan las programaciones revisadas el 2026-10-06; la convocatoria ordinaria (del 2027-05-31 al 2027-06-03) no cambia.
  - **FE de 2.º a 7 h: 50 días** (del 2027-03-03 al 2027-05-21), los que salen de la propuesta, no los 49 de la plantilla de 2025-2026 (CarlosFB, 2026-10-17).
  - **Días de Proyecto («PROY»):** se guardan en `proyecto`; no salen en el documento, que lleva el párrafo fijo del Proyecto.
  - **Lo que las notas no dan** (la FE de 2.º de GA) queda en `pendiente`: el documento lo enseña como «pendiente» y V-11 bloquea esa definitiva.
- **Consecuencias.** La definitiva ya se puede exportar en todos los ciclos y cursos salvo 2.º de GA. Formato del archivo y esquema (`catalogo_curso.schema.json`): docs/MODELO_DE_DATOS.md §1.

## ADR-024 · Borrar una programación de este equipo: a la papelera, nunca lo exportado — 2026-10-17 · Aceptada

- **Contexto.** El listado «Programaciones» gana acciones sobre las marcadas (abrir, vista previa, exportar a carpeta, enviar por correo y borrar). Borrar puede entenderse como quitarla de la lista, borrar su archivo de trabajo o borrar también los Word y PDF exportados.
- **Alternativas:** quitarla solo de la lista (el archivo seguiría y volvería a salir); borrar el archivo de trabajo del todo; borrar además lo exportado.
- **Decisión** (CarlosFB, 2026-10-17): «Borrar…» pide confirmación diciendo qué se borra y mueve a la **papelera del sistema** el archivo de trabajo (`programaciones/<curso>/<id>.programacion`) y sus copias de `autoguardado/`. **Nunca** toca los Word ni los PDF exportados ni nada de Teams. Si la papelera no lo acepta, no se borra nada. Si es la programación abierta, se cierra antes, sin guardar lo pendiente.
- **Consecuencias.** Se recupera desde la papelera o abriendo el Word exportado, que lleva todos los datos dentro (ADR-002).

## ADR-025 · Tabla 4.1 con horas de centro y de empresa y % de los RA mixtos — 2026-10-17 · Aceptada

- **Contexto.** CarlosFB pide otra maquetación de la tabla 4.1 «Ponderación de cada RA» (modelo: su programación de 0963, revisada el 2026-10-17).
- **Decisión** (CarlosFB, 2026-10-17):
  - **Columnas:** Resultado de aprendizaje · Modalidad · Horas Centro · Horas Empresa · % Horas Centro · % Horas Empresa. Cabeceras en negrita, en dos líneas, sobre gris claro; «R.A.n.» subrayado y en negrita con el enunciado justificado; el resto, centrado. La fila de un RA no se parte entre páginas.
  - **Cada RA:** modalidad Centro, Empresa o Mixto por sus horas; horas o «-» si son 0; los % solo en los mixtos, en negrita («71 %»), y «-» en los demás.
  - **Redondeo:** el % de empresa al entero más cercano (la mitad, hacia arriba) y el de centro, 100 − empresa, para que sumen 100. Es lo que dan los ejemplos de CarlosFB (10 + 4 → 71/29; 27 + 4, 21 + 3 y 20 + 3 → 87/13): con 21 + 3 el centro es 87,5, y redondear el centro hacia arriba daría 88/12.
  - **TOTAL:** sobre gris, «TOTAL» a la derecha en RA y Modalidad combinadas, las dos sumas en negrita y los dos % combinados y vacíos.
  - **Sin empresa (el Proyecto):** las seis columnas, con «-» en lo de empresa (antes se quitaba la columna).
  - **«% del curso (aprox.)»,** opcional: como última columna, con letra de 8 pt y el ancho que se le quita a la del RA; la tabla no pasa del ancho de la página.
  - **RA sin horas (0/0):** modalidad «-» y V-10 (roja), como antes.
- **Consecuencias.** La plantilla se rehace con `scripts/plantilla.py crear` (versión 2026-10-17). La importación lee los dos formatos. La regeneración de las referencias cuenta la 4.1 como diferencia de formato decidida (la de 0963 ya está en el formato nuevo).

## ADR-026 · Las versiones se publican como normales — 2026-10-17 · Aceptada

- **Contexto.** Las 0.1.0 a 0.1.2 se publicaron como pre-release. La app pregunta por la versión nueva a `/releases/latest` de la API de GitHub, que no tiene en cuenta las pre-release: con ellas, ningún equipo recibe el aviso.
- **Decisión** (CarlosFB, 2026-10-17): las versiones se publican como **normales** («latest»: `compilar.yml` crea la release con `--latest`) para que el aviso llegue. La numeración sigue en **0.x hasta el piloto (F6)**. Pre-release solo si CarlosFB lo pide, sabiendo que esa versión no avisa.
- **Consecuencias.** La 0.2.0 es la primera versión normal; las 0.1.x instaladas la detectan (prueba con la respuesta de la API simulada en `tests/test_actualizaciones.py`).

## ADR-027 · Catálogo publicado: versión propia, rama `catalogo-publicado` y firma Ed25519 — 2026-10-17 · Aceptada

- **Contexto.** F5, aprobada por CarlosFB el 2026-10-17: la app tiene que saber cuándo cambia la normativa, como sabe cuándo hay versión nueva. ADR-005 preveía publicar en `catalogo/publicado/` de `main`, pero eso obliga a la CI a hacer commits en `main` (que chocan con los push de CarlosFB) y mezcla datos generados con el código. La versión del catálogo era la fecha de comprobación más reciente: dos cambios el mismo día tendrían la misma.
- **Decisión:**
  - **Versión explícita** en `catalogo/version.yaml`: `AAAA.MM.DD` y `.1`, `.2`… si ya hay una ese día, con la fecha y la huella SHA-256 del contenido (todos los archivos del catálogo salvo ese). La escriben `catalogo.py construir` y `catalogo.py version`; `comprobar` falla si el contenido cambia sin versión nueva. Volver a leer lo mismo otro día no reescribe nada (las fechas de comprobación no cuentan). La versión de partida es la `2026.10.17`, la que ya llevan las programaciones.
  - **Publicación** con `catalogo.yml` al fusionar en `main` un cambio del catálogo (o a mano): `catalogo-<versión>.json.gz` (todos los YAML en un JSON) e `indice.json` con versión, fecha, sha256, novedades y versiones anteriores, firmado con Ed25519 sobre el JSON canónico de sus datos. Va a la rama **`catalogo-publicado`**, solo con eso, servida por `raw.githubusercontent.com` (sin la API de GitHub, R6). No va en releases, para que `releases/latest` siga siendo la app.
  - **Clave:** la privada, generada el 2026-10-17, solo en el secreto `CATALOGO_CLAVE` de GitHub (nunca en un archivo, el repositorio, un registro ni la bóveda); `publicar` comprueba que corresponde a la pública. La pública va en `src/programaciones/recursos/clave_catalogo.txt`, dentro de la app (la prueba de arranque y `comprobar_paquete.sh` la buscan).
  - **En la app** (`catalogo_remoto.py`): al arrancar, como mucho una vez al día, baja `indice.json`; sin firma, con firma mala, con otra clave, con un formato que no entiende o con una versión que no es mayor que la suya, no acepta nada. Si es nuevo, baja el paquete, comprueba el sha256, las rutas, la huella y que se lee, y lo guarda en `<datos>/catalogo/versiones/<versión>/`. Guarda también una copia del catálogo que lleva la app, para poder comparar después de actualizarla, y baja las versiones de las programaciones del equipo que no tenga. Sin red, se reintenta en el próximo arranque.
- **Alternativas descartadas.** `catalogo/publicado/` en `main` (commits de la CI en `main`); un asset de una release de catálogo (`releases/latest` dejaría de ser la app); la API de GitHub (60 consultas por hora para todo el centro).
- **Consecuencias.** Rotar la clave: secreto nuevo, `clave_catalogo.txt` nuevo y versión de la app; los equipos que no actualicen dejan de recibir catálogos. Un cambio de `cursos/` también sube la versión y se publica.

## ADR-028 · Todo lo que detecta el vigía lo revisa y lo publica CarlosFB — 2026-10-17 · Aceptada (sustituye a «el vigía publica solo» de ADR-015)

- **Contexto.** ADR-015 decía que el vigía publica solo si pasan las comprobaciones automáticas. Una de ellas, la regeneración de las programaciones de referencia, solo se puede hacer en local (las referencias están en la bóveda y nunca entran en el repositorio). R2 pide revisión humana de lo que sale de los PDF del DOGV y R7, frenar un RA mal extraído. Una primera versión de esta decisión dejaba publicar solo los cambios de texto de RA o criterios de un real decreto con todo en verde.
- **Decisión** (CarlosFB, 2026-10-17): **nada se publica solo**, ni siquiera un cambio de texto con todo en verde.
  - El vigía (`scripts/vigia.py`, `vigia.yml`) abre la PR con la diferencia legible, la huella nueva y la lista «Revisar a mano», se la asigna a CarlosFB y comenta el resultado de las comprobaciones (`catalogo.py comprobar --red`, ruff y la suite). **Nunca la fusiona ni la aprueba**, y no lanza `catalogo.yml`.
  - `catalogo.yml` solo publica cuando el cambio llega a `main`, es decir, cuando CarlosFB fusiona (o lo lanza él a mano).
  - «Revisar a mano» señala lo que pide más cuidado que leer la diferencia: cualquier cambio de un PDF del DOGV (horas, anexos, R2), RA o criterios que aparecen o desaparecen, horas, normas nuevas, quitadas o cambiadas, referencias posteriores nuevas de un real decreto (pueden obligar a tocar la receta), textos consolidados actualizados, disposiciones de FP o que citan un real decreto del catálogo en los sumarios del BOE, normas nuevas en la página de la Conselleria, otros campos del ciclo o del módulo y lo que el lector no ha sabido leer (el catálogo se queda como estaba: no se inventa nada).
  - **Fuente que no responde:** si es del catálogo (BOE o DOGV de `fuentes.yaml`), el vigía falla con aviso y no toca nada. La página de normativa de FP de la Conselleria es solo para encontrar normas nuevas y no responde a los servidores de GitHub con regularidad (primera ejecución real, 2026-10-17): tres intentos y, si no, un aviso en el resumen, sin fallar y sin olvidar lo que ya había visto.
  - Lo ya visto se guarda en `catalogo/vigia.yaml`; la primera vez es punto de partida. Los mismos cambios no abren otra PR; una PR nueva sustituye a la anterior abierta.
  - **Peticiones:** agente identificable (`Programaciones-catalogo/1.0` con la dirección del repositorio) y 2 s entre peticiones; cada lunes y a mano (`workflow_dispatch`, con `simulacro` para probar el recorrido con una PR en borrador).
  - **Barrera:** `scripts/comprobar_sin_fusion.sh` (paso «Sin fusión automática» de `comprobar.yml` y una prueba) falla si algún flujo o script de `.github/` o `scripts/` fusiona o aprueba PR o activa el auto-merge.
- **Alternativa para el permiso de GitHub** (propuesta, no aplicada): para abrir una PR con `GITHUB_TOKEN` hace falta el ajuste «Allow GitHub Actions to create and approve pull requests», que es un único interruptor para crear y aprobar. Se podría desactivar si el vigía solo subiera su rama y abriera una incidencia con el enlace «comparar y crear PR»: CarlosFB crearía la PR con un clic. Queda activado mientras CarlosFB no decida otra cosa; la barrera impide que se use para aprobar.
- **Consecuencias.** Cada cambio del currículo pasa por CarlosFB y, después, por cada profesor (ADR-015). La prueba de las referencias la hace él en local cuando la PR la necesita.

## ADR-029 · En macOS, la actualización sustituye la app donde está instalada — 2026-10-17 · Aceptada

- **Contexto.** CarlosFB guarda las apps de EPLA en `/Applications/EPLA/`. Al actualizar se abría el DMG; al arrastrar al acceso «Applications», la 0.2.0 quedó en `/Applications` mientras el Dock seguía abriendo la 0.1.0 de `/Applications/EPLA`, que volvía a avisar de la misma actualización.
- **Decisión** (`actualizaciones.instalar_macos`, CarlosFB, 2026-10-17):
  - Se descarga y se comprueba el sha256 como antes; se monta el DMG (`hdiutil attach -nobrowse -readonly -mountrandom`) y se busca el `.app`.
  - La carpeta de la app sale de `sys.executable` (`…/X.app/Contents/MacOS/x`). Un script aparte (en una carpeta temporal, separado de la app) espera a que la app se cierre, copia la nueva con `ditto` junto a la vieja, aparta la vieja, pone la nueva en su sitio, borra la vieja, quita la cuarentena, desmonta el DMG y abre la actualizada. Deja su registro en `logs/actualizacion_*.log` de la carpeta de datos.
  - **Nunca dos copias ni la vieja borrada si la nueva no está entera en su sitio:** si la copia o el cambio fallan, la vieja se queda o vuelve, se avisa con una alerta y se abre la que había.
  - **Reserva:** en desarrollo, sin permiso de escritura en la carpeta o si el DMG no se monta, se abre el DMG como antes y la app dice a qué carpeta arrastrarla.
  - Windows no cambia: el instalador de Inno Setup, con su `AppId` fijo y la carpeta anterior por defecto, ya sustituye la versión instalada.
- **Consecuencias.** Solo funciona desde la versión que lo lleva: para pasar a la 0.3.0 todavía se usa el DMG (dicho en la nota del release).

## ADR-030 · La tabla de la app tiene las columnas de la 4.1 y la modalidad la elige el profesor — 2026-10-17 · Aceptada

- **Contexto.** El bloque «Empresa por RA» tenía columnas propias (centro, «Prop.», «va a empresa», empresa, total y modalidad calculada) que no casaban con la tabla 4.1 del documento (ADR-025).
- **Decisión** (CarlosFB, 2026-10-17: «manda la del documento»):
  - **Columnas de la app:** RA · Modalidad · Horas centro · Horas empresa · % centro · % empresa, como la 4.1. Fuera «Prop.», la casilla y «Total»; la fila Total suma las horas.
  - **Las tres primeras las pone el profesor** (o se leen al importar un .docx); **los dos %, se calculan** con la regla de ADR-025 (solo en los mixtos).
  - **Modalidad:** desplegable Centro · Mixto · Empresa, guardado en `modalidad` (`{"2": "Mixto"}`). Centro quita la empresa del RA; Empresa deja su centro a 0; Mixto pide las dos. Sin elegir (programaciones de antes), se deduce de las horas como hasta ahora.
  - **Horas de centro:** siguen partiendo de la propuesta de la app y se ajustan dentro de sus límites (V-04); la propuesta y los límites, en la ayuda de la celda, y en dorado si se ha ajustado.
  - **V-13 (roja):** la modalidad elegida no casa con las horas (Centro con empresa, Empresa con centro, Mixto sin uno de los dos).
- **Consecuencias.** Campo nuevo en el esquema: una versión anterior de la app no abre un archivo que lo lleve. La importación lee la columna «Modalidad». El documento no cambia.

