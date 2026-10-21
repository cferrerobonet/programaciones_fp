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

## ADR-004 · Grado Básico fuera hasta tener su modelo — 2026-10-14 · **Sustituida por ADR-032**

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
- **Consecuencias.** La definitiva ya se puede exportar en todos los ciclos y cursos salvo 2.º de GA. Formato del archivo y esquema (`catalogo_curso.schema.json`): docs/MODELO_DE_DATOS.md §1. Las convocatorias, sustituidas por ADR-033 (2026-10-18).

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

## ADR-031 · Programación nueva con los apartados 3 y 4 propuestos — 2026-10-17 · Aceptada

- **Contexto.** CarlosFB pide que, al empezar una programación desde cero, la app dé rellenos el paso «RA y competencias» y el apartado 4, en todos los módulos, y que al importar o heredar una programación cuyas competencias de cada RA no casan con las de la app, un botón «Proponer corrección con IA» deje decidir al profesor.
- **Decisión** (CarlosFB, 2026-10-17):
  - **Unidades (apartado 4):** una por bloque de **contenidos básicos** del módulo (BOE o DOGV, dato oficial y público, en `contenidos` del catálogo), «UDnn. título del bloque», con las horas del módulo repartidas según la extensión del bloque (al menos 1 h, suma exacta) y el trimestre del punto medio de la unidad. **Sin elementos de evaluación:** los pone el profesor.
  - **Lectura de los contenidos:** tres formatos del BOE (títulos con «:» y puntos con guion; sin guion; los de 2008 con «Título: primer punto») y el formato numerado del DOGV. Solo se acepta si no queda texto suelto, todos los bloques tienen puntos, no se repite ningún título y hay tantos bloques como RA (uno más o uno menos). Si no, `contenidos_pendiente`: sin propuesta, nunca inventada.
  - **Competencias de cada RA (apartado 3):** el real decreto solo dice a qué competencias contribuye el módulo entero, así que el reparto por RA es una **propuesta hecha con IA**, marcada como tal en el catálogo, en la banda del paso y en el diálogo. Solo letras del módulo (en los comunes, las del título) y al menos una por RA. Vive en `scripts/propuestas/ra_competencias.yaml` con la huella de los RA de cada módulo; `construir` la lleva al catálogo y la descarta si los RA cambian.
  - **Programación nueva:** las unidades y las competencias propuestas, con los dos bloques «heredados» (por revisar) y una banda que dice de dónde salen. No cuentan para la definitiva hasta que el profesor los confirma (V-06).
  - **Importada o heredada:** si las competencias de algún RA no son las de la propuesta, el paso «RA y competencias» enseña «Proponer corrección con IA»: un diálogo con las diferencias RA por RA y dos salidas, «Mantener las mías» (no cambia nada) y «Aplicar la propuesta» (pone la de todos los RA).
- **Consecuencias.** El catálogo crece con `contenidos`, `contenidos_pendiente` y `propuesta_ra_competencias` (opcionales: las apps anteriores los ignoran). Rehacer la propuesta de un módulo cuyos RA cambian es tarea de la PR del vigía (`docs/OPERACIONES.md`).

## ADR-032 · Grado Básico: los cuatro ciclos del centro, técnicos como GM y GS, ámbitos con su plantilla — 2026-10-17 · Aceptada

- **Contexto.** CarlosFB da dos programaciones modelo de GB (un ámbito común, 3164, y un módulo técnico, 3016, de Informática y Comunicaciones) para aplicarlas a los módulos de GB, y pide los cuatro ciclos que tiene el centro (web de pedidos en producción, copia del 2026-10-10: Electricidad y Electrónica, Informática y Comunicaciones, Mantenimiento de Vehículos y Servicios Administrativos, 1.º y 2.º). Fase F8.
- **Fuentes** (comprobadas el 2026-10-17): títulos del RD 127/2014 (un anexo por título: I SA, II EE, IV IC, VI MV), con el RD 498/2024, que los actualiza sin cambiar los RA técnicos y añade el 6 bis (UC → módulo) y el Proyecto 3160 (anexo I); horario del Decreto 117/2025, anexos III-A y III-B, en la redacción del anexo VI del Decreto 95/2026; 3159 (Itinerario para la empleabilidad, 9 RA) del anexo I del Decreto 117/2025; ámbitos (3161-3164) del anexo V del RD 217/2022. El «RD 289/2023» que cita el modelo técnico es de otros títulos (Integración Social): error del modelo.
- **Decisión** (CarlosFB, 2026-10-17):
  - **Módulos técnicos, 3159 y Proyecto:** el documento de GM y GS (ellos lo dicen: «más parecida a las que ya haces») con los datos de GB. La plantilla cambia por marcas lo que en GB es otro: «en su anexo II» del RD 127/2014, el «apartado 6 bis del anexo II … añadido por el RD 498/2024» por el anexo V B), los «apartados 2.1 y 2.2 del anexo II» por los artículos 4 y 5, y las orientaciones del anexo II; sin el apartado 2.2 (GB no tiene optativos). **Tabla 4.1 y bloque de empresa iguales que en GM y GS**, en el documento y en la pantalla.
  - **Índice:** el motor quita las entradas cuyo título ya no está (el 2.2 en GB) y la conversión con Word rehace el índice entero (`update`), no solo las páginas.
  - **Ámbitos (3161-3164):** se evalúan por **competencias específicas** con sus descriptores del perfil de salida, no por RA, y se califican **IN, SU, BI, NT, SB** (disp. adic. 7.ª del RD 498/2024; art. 5 de la Orden 8/2025), como dice el modelo común (el técnico, que copia ese texto, habla de «competencias específicas» y nota numérica en un módulo técnico). Las CE y los criterios son los oficiales (los del modelo no casan: «quizás haya errores que haya que corregir», CarlosFB), los mismos en I y II. Se programan **por partes** con su tabla 3 y 3.1 por parte: en Comunicación y Ciencias Sociales, las materias del anexo III-B; en Ciencias Aplicadas, las que defina el profesor (el modelo: Matemáticas y Ciencias; desde ADR-039, la app las propone). **Plantilla propia** (0.7.0): `es-ambito`, que `scripts/plantilla.py crear` saca de la de PIICT (misma identidad, portada con «Ámbito:») con los apartados del modelo común corregidos: 2 competencias específicas, descriptores y criterios; 3 y 3.1, una tabla por parte (unidades; peso en horas de cada CE: las horas de cada unidad a partes iguales entre las CE de su elemento, en enteros que suman la parte); 4 a 7 y 9, los 5 a 8 y 10 de PIICT renumerados; 8 evaluación con la tabla de fechas, sin formación en empresa; 10 criterios y procedimientos; 11 recuperación. En la app, tres pasos (sin empresa ni RA y competencias), «CE» en lugar de «RA» y las partes en «Unidades y evaluación» (V-14). La 0.6.0 los enseñaba como «pendiente».
  - **Tutoría:** fuera de la lista (no tiene programación propia).
  - **Formación en empresa de GB:** no está en el calendario de FE del centro ni en calendarios.epla.es: «pendiente» en el curso 2026-2027 (V-11).
  - **Comunes (también en GM y GS):** los apartados 3 y 11 citan la norma que trae su currículo («anexo V del Decreto 114/2025», «anexo I del RD 498/2024», «anexo I del Decreto 117/2025»), no el real decreto del título.
- **Consecuencias.** Catálogo en formato `catalogo/2`: las apps anteriores no lo aceptan y piden actualizarse. Normativa por grados (RD 217/2022 y Decreto 117/2025, solo GB; Decreto 114/2025 y la corrección del 95/2026, solo GM y GS). Propuesta de IA de competencias por RA también en GB (ADR-031).

## ADR-033 · Convocatorias de 2026-2027 con su fecha de fin: la ordinaria el 8 de junio y la extraordinaria el 22 de junio de 2027 — 2026-10-18 · Aceptada

- **Contexto.** CarlosFB revisó el documento exportado: la convocatoria ordinaria (del 2027-05-31 al 2027-06-03) y la extraordinaria (desde el 2027-06-14), las del calendario escolar de FP (ADR-023), no son las que quiere en GB, GM y GS.
- **Alternativas** (preguntadas el 2026-10-18): las fechas nuevas tal cual; cambiar además la frase de la plantilla; o dejar las del calendario. En el calendario, el 2027-06-08 y el 2027-06-22 son las entregas de boletines de cada convocatoria.
- **Decisión** (CarlosFB): **las fechas nuevas, y son fechas de fin, como las de las evaluaciones**: «La convocatoria ordinaria finalizará el 8 de junio de 2027 y la convocatoria extraordinaria finalizará el 22 de junio de 2027» (antes, «se realizará del … al …» y «comenzará el …»). En la tabla de fechas de los ámbitos de GB, como las evaluaciones de encima: «08/06/2027» y «22/06/2027».
- **Datos.** El curso escolar pasa a `curso/2`: las dos convocatorias van en `evaluaciones` (`ordinaria`, `extraordinaria`), todas fechas de fin; desaparecen `ordinaria` `{desde, hasta}` y `extraordinaria_desde`. Como una app anterior no sabría leerlo (no valida el curso del catálogo descargado y fallaría al generar), el catálogo sube a `catalogo/3`: las apps anteriores no lo aceptan y piden actualizarse. La plantilla cambia el verbo (versión 2026-10-18). La importación lee las dos frases; de una programación anterior toma el fin del intervalo de la ordinaria y el inicio de la extraordinaria, lo único que dice.
- **Consecuencias.** Las seis referencias de la bóveda llevan las fechas antiguas: diferencia aceptada en `tests/test_regeneracion.py`. Sustituye a ADR-023 en lo que toca a las convocatorias.

## ADR-034 · Versión para Linux: un tar.gz portable, como el portable de Windows — 2026-10-19 · Aceptada

- **Contexto.** CarlosFB pide una versión de Linux, como las que ya hay de Windows (instalador y portable) y de macOS (DMG). La app es Python + PyQt6 y solo necesita las bibliotecas de Qt: la CI ya compila y arranca la app en Ubuntu (las pruebas, sin pantalla), así que el empaquetado no tiene una dificultad propia.
- **Alternativas.**
  - **AppImage:** un solo archivo que se ejecuta. Pero necesita FUSE, que en Ubuntu 24.04 ya no viene instalado: el profesor tendría que descomprimirlo a mano o instalar `libfuse2`. Además el `AppImage` de la appimagetool hay que bajarlo en cada compilación.
  - **`.deb`:** instalador de Debian/Ubuntu, pero ata la app a una distribución y a una ruta de instalación (`/opt`, `~/.local`), y los equipos del centro no son homogéneos. En la práctica no hay ningún equipo con Linux en el centro: la versión es para quien la pida.
  - **`tar.gz` portable:** un archivo que se descomprime y se ejecuta, sin instalar nada, igual que el portable de Windows que ya se ofrece (R4).
- **Decisión** (CarlosFB, 2026-10-19: «añade la versión de Linux a las que ya hay»):
  - **Paquete:** `Programaciones-X.Y.Z-Linux-x86_64.tar.gz` (nombre fijo, como los otros instaladores). Dentro: la app de PyInstaller (`onedir`), el lanzador `Programaciones.sh`, el script `instalar.sh` (que crea el acceso directo del menú y da permiso de ejecución) y el icono.
  - **Compilación:** en GitHub, nunca en local (ADR-011). Job `linux` de `compilar.yml` (`scripts/build/build_linux.sh`): compila con PyInstaller, comprueba los datos empaquetados (`scripts/comprobar_paquete.sh`) y **arranca la app** hasta la ventana principal, como en las otras dos plataformas.
  - **Icono:** el ejecutable de Linux no lleva icono (PyInstaller no lo pone ahí); lo lleva el acceso directo del menú. Por eso el spec solo pasa el icono en macOS y Windows.
  - **Actualización:** la app descarga el `tar.gz` (comprobando su sha256, como siempre) y lo abre con el gestor de archivos: se extrae encima de la carpeta donde está la app. No se sustituye en su sitio como en macOS (ADR-029).
  - **Datos del equipo:** `~/.local/share/Programaciones`, que `rutas.py` ya tenía previsto para Linux.
- **Consecuencias.** Un Linux más que actualizar en la app y en la documentación. El profesor de Linux tiene que descomprimir el `tar.gz` y, si quiere la app en el menú, ejecutar `instalar.sh` una vez. Falta la prueba a mano en un equipo con pantalla (`docs/PENDIENTE.md`).

## ADR-035 · Importar el formato antiguo de las programaciones — 2026-10-19 · Aceptada

- **Contexto.** CarlosFB pide que la app lea también las programaciones del formato antiguo del departamento (anterior a la plantilla de PIICT): tienen los mismos datos del profesor, en otros apartados y con otros títulos, y al final se exportan igual que las demás. El importador de siempre no las reconocía: sus títulos son párrafos normales («7.- TEMPORALIZACIÓN…», sin estilo de título) y el archivo no sigue el patrón «SIGLA N - 0xxx - Nombre».
- **Alternativas.**
  - **Convertir el documento al formato actual y pasarlo por el importador de siempre:** reescribir un `.docx` en otro es más frágil que leer sus datos.
  - **Un lector propio que lleva cada apartado antiguo al bloque de siempre** (`importar_antigua.py`), con las mismas lecturas de tablas y párrafos.
- **Decisión:** el lector propio. Se usa solo si el documento no tiene los apartados de la plantilla y sí la tabla de temporalización del formato antiguo.
  - **Apartados por el principio de su título**, no por su número, que cambia de una programación a otra: temporalización → tabla 4; ponderación de cada RA → 4.1; metodología → 5.1; recursos → 6, y los que empiezan por aula, taller o laboratorio → 7; actividades complementarias o extraescolares → 10; evaluación → los bloques sustituibles de 9, 11.1 y 11.2, cada uno entre su párrafo de entrada y el siguiente párrafo de entrada o de salida de la plantilla (comparados por el principio del párrafo, porque en el formato antiguo un título corto sigue en el mismo párrafo que su texto), y solo si difiere del de la plantilla.
  - **Módulo:** el del nombre del archivo si sigue el patrón; si no, el código de la portada («Módulo profesional: 0xxx - …») buscado en el catálogo y, si está en varios ciclos o cursos, el ciclo de la portada. Si aun así hay dudas, se pide renombrar el archivo con el patrón.
  - **Viñetas escritas a mano** («• …») pasan a viñetas de verdad; los párrafos que repiten un título de la plantilla («Principios generales y pedagógicos») no se importan; las horas pegadas al nombre del elemento («PRÁCTICA/TAREA 1(2h)») se separan (también en el formato actual).
  - **No se importa** lo que pone el catálogo o la plantilla: normativa, objetivos, competencias, RA y criterios, contenidos básicos, plan de empresa y atención a la diversidad.
- **Consecuencias.** El formato antiguo no relaciona cada RA con sus competencias: esa tabla queda vacía para que la complete el profesor. Como siempre, todo lo importado queda heredado hasta que el profesor lo confirma (ADR-008), y los pesos escritos que no coinciden con el cálculo de la app se guardan como ajuste del profesor. Las pruebas usan un documento antiguo ficticio que se crea dentro de la prueba.
- **Ampliación (2026-10-19, CarlosFB: «que los lea»).** Las antiguas de 2026-09 llevan los títulos con estilo de título de Word: el lector general los descarta, así que el del formato antiguo se reintenta con ellos como párrafos (`contenido.leer(titulos=True)`). Se distingue del formato actual por la tabla 4.1, que el actual siempre tiene. En su ponderación, «Horas» a secas son las horas totales del RA (antes se leían 0 y las de centro salían negativas). Probado con las seis de CarlosFB (fuera del repositorio): entran y exportan sin avisos, con las mismas horas de empresa que sus Excel de RA.

## ADR-041 · Excel de RA desde la app (F9) — 2026-10-19 · Aceptada

- **Contexto.** Junto a cada programación hay un Excel de RA (`SEA 2 - 0517 - ….xlsx`) para importar los RA y sus criterios en el cuaderno por RA de Educamos. Se hacía aparte. CarlosFB (2026-10-19): «no cambia nada, es idéntico patrón y diseño», y que cada profesor se lo descargue desde la app cuando quiera.
- **Alternativas.** Un botón aparte de «Descargar Excel de RA»; o un formato más al exportar, junto a Word y PDF, con el mismo nombre normalizado y en la misma carpeta.
- **Decisión:** un tercer chip, «Excel de RA», en la zona «Exportar» y en Ajustes → Exportación (formato `xlsx`, no marcado de serie). `excel_ra.generar` reproduce el Excel de siempre: hoja con el nombre del módulo (31 caracteres), «Módulo» y «Clase» («2º CFGS Sistemas …»), cabecera en la fila 5, los RA y después sus criterios, B:G combinadas, X en Visible, X y horas en los RA que van a la empresa (tabla 4.1; las horas, numéricas, como pide Educamos), los mismos anchos y la hoja «Leyenda». Los textos, los del documento.
- **Consecuencias.** Comparado celda a celda con los tres Excel de referencia (0517, 0524 y 0525, fuera del repositorio), generados desde sus programaciones: idénticos salvo las cuatro erratas del BOE que el documento corrige (ADR-018), que el Excel también lleva corregidas. Los ámbitos de GB no tienen RA: el chip se desactiva y la exportación no escribe Excel. El correo sigue adjuntando Word y PDF.

## ADR-040 · Importar un ámbito de Grado Básico sin datos de la app — 2026-10-19 · Aceptada

- **Contexto.** Un ámbito solo se podía importar si lo había exportado la app con sus datos dentro; el modelo del departamento (3164) o un ámbito que hubiera perdido los datos daban «sin la tabla del apartado 4», porque los ámbitos llevan sus tablas en el 3 y el 3.1, una por parte. CarlosFB (2026-10-19): «que los lea».
- **Decisión:** `importar_ambito.py`, antes que el formato actual y el antiguo, si el apartado 3 tiene una tabla con la columna de competencias específicas. Cada tabla del 3 es una parte (nombre y horas del párrafo «Para … (N h)» que la precede) y cada fila una unidad con su propio elemento (tipo por el nombre, CE en `ra`). El módulo, como en el formato antiguo, con las filas «Código» y «Ámbito» de la portada. Los párrafos propios van a contenidos y notas (3), notas del 3.1, metodología (4 o 4.1), recursos (5), espacios (6) y actividades (9); un párrafo casi igual a uno fijo de la plantilla de ámbitos (95 %, sin cifras ni marcas) se toma por ese párrafo. La evaluación (8, 10 y 11) no se importa: la plantilla de ámbitos no tiene bloques sustituibles. «Curso académico 2026/2027» vale como 2026-2027.
- **El 3.1 no se importa:** la app lo calcula de la tabla 3 (`calculos.ponderacion_parte`) y no tiene campo para pesos a mano. En el modelo 3164 no cuadra con su propia tabla 3 (da horas a la CE6 en Matemáticas sin ninguna unidad de Matemáticas con la CE6), y la tabla de Ciencias II suma 63 h aunque el texto y el total dicen 66: se importa lo que dicen las filas y la parte con las 66 h que declara, para que el profesor lo vea y lo corrija.
- **Consecuencias.** Probado con el modelo 3164 real (fuera del repositorio): IC 2.º, dos partes, 22 unidades, exporta sin avisos. La comprobación de títulos de la exportación acepta también la plantilla de ámbitos (antes avisaba en todo ámbito). Todo lo importado queda «heredado».

## ADR-039 · Ciencias Aplicadas se propone en Matemáticas y Ciencias — 2026-10-19 · Aceptada

- **Contexto.** ADR-032 programa los ámbitos por partes. Comunicación y Ciencias Sociales trae sus materias con horas en el anexo III-B; Ciencias Aplicadas no (el decreto solo da las horas del ámbito), y la app proponía una sola parte con todo el ámbito. El modelo del departamento (3164, 2.º IC) la divide en Matemáticas II (99 h) y Ciencias II (66 h), 3 h y 2 h de sus 5 h semanales, aunque suma 165 de 166 h. En otros ciclos el ámbito tiene 4 h semanales.
- **Alternativas** (preguntadas a CarlosFB): por horas semanales; siempre 3/5 y 2/5; mitad y mitad; o dos partes sin horas.
- **Decisión** (CarlosFB, 2026-10-19: dos partes y «por horas semanales»): `propuesta.partes` propone «Matemáticas I/II» y «Ciencias I/II». Matemáticas lleva la mitad de las horas semanales redondeada hacia arriba (5 h → 3; 4 h → 2) y las anuales en esa proporción, redondeadas; Ciencias, el resto, para que sumen las del ámbito (166 h → 100 + 66; 133 h → 67 + 66).
- **Consecuencias.** Es una propuesta: el profesor puede cambiar nombres y horas. Con dos partes, los saberes básicos no se asignan solos a ninguna: los reparte el profesor, como en Comunicación y Ciencias Sociales. Las programaciones ya creadas con una sola parte no cambian.

## ADR-038 · ONLYOFFICE como tercer programa para el PDF — 2026-10-19 · Aceptada

- **Contexto.** CarlosFB pide que la app admita y exporte documentos para ONLYOFFICE, no solo Word o LibreOffice. El `.docx` que genera la app es OOXML estándar y ONLYOFFICE lo abre y edita sin más; lo que faltaba era hacer el PDF en un equipo que solo tenga ONLYOFFICE.
- **Alternativas.**
  - **Abrir ONLYOFFICE Desktop Editors con el documento y pedir al profesor que exporte a PDF:** manual, y la app no sabría cuándo está el PDF.
  - **ONLYOFFICE Document Builder o Document Server:** otra instalación (o un servidor) solo para convertir.
  - **El conversor `x2t` que ya lleva Desktop Editors** en su carpeta `converter/` (macOS, Windows, Linux y snap): `x2t entrada.docx salida.pdf`, el formato por la extensión.
- **Decisión:** `pdf.con_onlyoffice` ejecuta `x2t` desde su propia carpeta (ahí tiene la selección de fuentes que necesita para el PDF), con el mismo tiempo máximo y los mismos errores que LibreOffice. «Automático» prueba Word → LibreOffice → ONLYOFFICE; en Ajustes → Exportación se puede elegir «ONLYOFFICE Desktop Editors» a mano. Como LibreOffice, no actualiza el campo del índice: se numera con las páginas del PDF en una segunda pasada. Los avisos de «sin programa» nombran las dos opciones gratuitas.
- **Consecuencias.** Probado el 2026-10-19 en macOS con ONLYOFFICE 9: por la línea de órdenes (`x2t entrada salida`) el PDF falla («DoctRenderer: error open») porque no encuentra las fuentes; con un XML de parámetros (`m_sFileFrom`, `m_sFileTo`, `m_nFormatTo` 513 para PDF y 65 para DOCX, `m_sFontDir` y `m_sAllFontsPath` apuntando a la carpeta `data/fonts` del perfil del usuario, que Desktop Editors genera al abrirse por primera vez) sale un PDF correcto con el índice numerado, y abrir y guardar el `.docx` conserva los datos incrustados (R1). `x2t` devuelve 0 aunque falle: se comprueba que el archivo exista. Si el perfil no tiene las fuentes, el error pide abrir ONLYOFFICE una vez. La prueba real (`test_pdf_con_onlyoffice_de_verdad_y_r1`) corre sola donde haya ONLYOFFICE con sus fuentes. Si `x2t` cambiara en una versión futura, el error dice qué programa ha fallado y «auto» cae a los otros dos.

## ADR-037 · Las programaciones antiguas de Grado Básico, con el lector del formato antiguo — 2026-10-19 · Aceptada

- **Contexto.** Las programaciones antiguas de los módulos técnicos de Grado Básico («TID 1 - 3001 - Tratamiento Informático de Datos») no son ni la plantilla actual ni el formato antiguo de ADR-035: la temporalización va en el apartado 7 con una fila por elemento de trabajo («EXAMEN UT1», «TAREAS UT1») y el título de la unidad, con sus horas pegadas, dentro de la celda del examen; la ponderación en el 7.1 con porcentaje, horas de centro y de empresa; la evaluación sigue a esa tabla sin título propio, en bloques con subtítulos cortos; y el nombre del archivo lleva la sigla del módulo, no la del ciclo (la app lo tomaba por un ciclo «TID» y fallaba).
- **Alternativas.** Un tercer lector completo; o ampliar el del formato antiguo, que ya reparte por títulos y reutiliza las lecturas de tablas.
- **Decisión:** ampliar `importar_antigua.py` e `importar_docx.leer_tablas`. (1) La tabla se reconoce también por «Elementos de Trabajo» y, en ese caso, cada fila es una unidad con su elemento: el título sale del segundo párrafo de la celda del examen (sin el «(35h)») y, en las filas de tareas, es el propio nombre del elemento, como las filas «Práctica/tarea» del formato antiguo; «HORAS» y «RA ASOCIADO» se admiten como cabeceras. (2) La sigla del nombre del archivo solo vale si es un ciclo del catálogo (`modulo_del_nombre`); si no, el módulo sale de la portada. (3) Sin apartado de evaluación, los párrafos que siguen a la tabla de ponderación son la evaluación y no notas de la tabla; si los párrafos de entrada de la plantilla no aparecen, se reparten por subtítulos (`SUBTITULOS_EVALUACION`): instrumentos y desempeño profesional → elementos de evaluación (11.2); criterios generales → asistencia y pruebas. Lo anterior a los subtítulos (normativa de evaluación, sesiones, formación en empresa) es texto fijo de la plantilla o del catálogo y no se importa. (4) «Nombre Uno / Nombre Dos» en la celda del profesorado son dos personas.
- **Consecuencias.** Probado con la programación real del escritorio de CarlosFB (fuera del repositorio): módulo SA 1 3001, 8 filas (4 unidades con examen y tareas), horas de empresa de 3 RA, 5 párrafos de metodología y 8 de recursos; exporta y vuelve igual. Las horas del documento (233) no coinciden con las del catálogo (266): el peso de cada elemento se calcula sobre las del catálogo y la tabla lo enseña, para que el profesor lo revise. Los avisos del documento de GB (títulos y normas sin enlace) son previos y van en PENDIENTE.md.

## ADR-036 · Importar en el módulo elegido, sin renombrar el archivo — 2026-10-19 · Aceptada

- **Contexto.** Un Word sin datos de la app solo se importaba si el archivo se llamaba «SIGLA N - 0xxx - Nombre» (o, en el formato antiguo, si la portada decía el módulo sin dudas). CarlosFB propone que, si ya hay un módulo elegido en la columna «Módulos», no haga falta renombrar nada.
- **Alternativas.**
  - **Usar siempre el elegido, sin mirar el documento:** cómodo, pero un despiste en la columna mezclaría RA y horas de otro módulo sin que nadie se entere.
  - **Usar el elegido y preguntar solo si el documento dice otro módulo.**
- **Decisión** (CarlosFB, 2026-10-19: «ok» a la propuesta con aviso): el módulo se decide por este orden: datos incrustados → **módulo elegido** → nombre del archivo → portada (formato antiguo). Si el nombre del archivo o la portada dicen otro módulo que el elegido, la app pregunta en cuál se importa («El del documento», «El elegido» o «Cancelar»; si la portada solo da un código que está en varios ciclos, solo se ofrece el elegido). Si el documento no dice nada, se usa el elegido sin preguntar. Sin módulo elegido, como antes. Vale para «Nueva a partir de…» y para «Abrir» con un Word sin datos de la app (`importar_docx.decidir_modulo`, `ModuloDistinto`; en la interfaz, `ui/programaciones.leer_origen`).
- **Consecuencias.** Renombrar el archivo ya solo hace falta sin módulo elegido. La pregunta sale una sola vez: «Abrir» pasa al diálogo de herencia lo que ya ha leído.

## ADR-042 · Tabla 4.1 con los % antes que las horas y la nota de Educamos — 2026-10-21 · Aceptada

- **Contexto.** CarlosFB copia la tabla 4.1 en Educamos (Menú Evaluación → Competencias clave → Pestaña perfil), donde las columnas van en otro orden que el de ADR-025.
- **Decisión** (CarlosFB, 2026-10-21):
  - **Columnas:** Resultado de aprendizaje · Modalidad · % Horas Centro · % Horas Empresa · Horas Centro · Horas Empresa (la columna opcional «% del curso (aprox.)» sigue al final). Mismo formato de ADR-025; en la fila TOTAL, los dos % combinados y vacíos van antes que las dos sumas.
  - **Nota pegada a la tabla**, a la izquierda y sin espacio antes: «Tabla de Educamos: Menú Evaluación → Competencias clave → Pestaña perfil», en 8 pt, gris (808080) y cursiva. Es texto fijo de la plantilla: la importación no la lee como nota del profesor (`es_fijo`, apartado 4.1).
- **Consecuencias.** `COLUMNAS_41`, `tabla_41()` y `nota_educamos()` en `scripts/plantilla.py` (versión 2026-10-21, aplicada a la plantilla guardada sin rehacerla desde PIICT); `columna_pct_curso()` toma sus moldes de las columnas nuevas; la lectura de documentos reconoce las columnas por su cabecera, así que importa los dos órdenes. Pruebas: `test_tabla_41_cuadrada_con_el_ajuste_del_profesor`, `test_nota_de_educamos_pegada_a_la_tabla_41`, `test_pesos_ajustados_y_columna_del_curso`.

## ADR-043 · Módulos con varios códigos o en varios ciclos, y optativos programables — 2026-10-21 · Aceptada

- **Contexto.** CarlosFB: las programaciones de los módulos comunes (sostenibilidad, digitalización, inglés) no se podían leer ni heredar. Tres causas: el catálogo usa el código del horario de cada ciclo (1665031, 1708001) y los documentos el general (1665, 1708); el nombre de archivo solo admitía códigos de cuatro cifras (ni 1665031, ni CV0015, ni CVOPS…); y la programación de un ciclo no servía de base para el mismo módulo en otro (con los datos de la app, el ciclo elegido se ignoraba). Además, los optativos ofertados no se podían programar: la columna «Módulos» solo enseñaba la casilla «Módulo optativo», sin RA.
- **Decisión** (CarlosFB, 2026-10-21):
  - **Cualquier código del módulo** (`Catalogo.resolver`): el del horario, el general, el del Proyecto de 1.º sin la «p», los que no son de cuatro cifras, el identificador de un optativo y el código de su casilla; si varios optativos comparten código, decide el nombre. Vale en el nombre del archivo (`SIGLA N - código - Nombre`) y en la portada del formato antiguo; con el módulo elegido, 1665 y 1665031 ya no son «módulos distintos».
  - **Optativos programables:** cada optativo ofertado es un módulo del ciclo con sus RA; la programación guarda como `modulo` su identificador (`OPT-EE-IA`) y el documento y el archivo enseñan el código de la casilla de su ciclo. El inglés oral de GS pasa a ese código (CVOPS031 en SEA, STI y ARI, que comparte con IA; CVOPS001 en ADM; CVOPS192 en AUT, que comparte con Peritación). La casilla genérica solo sale en un ciclo sin optativos ofertados.
  - **Copiar a otro ciclo:** al abrir o heredar la programación de un módulo que está en varios ciclos con otro ciclo elegido, la app pregunta si se usa como base para el elegido. Se copia lo del profesor; las competencias de cada RA no (son las letras del título de origen) y se avisa si cambian las horas o hay horas en empresa. Solo entre ciclos del mismo módulo (`Catalogo.mismo_modulo`).
  - El aviso de módulo distinto nombra los ciclos («0179 de SEA 1.º y está elegido el 0179 de STI 1.º»).
- **Consecuencias.** `Ficha.clave` (la clave que guarda la programación) junto a `Ficha.codigo` (el que se ve); `EntradaModulo.codigo_visible`. `herencia.heredar(…, destino)`. Pruebas: `tests/test_modulos_comunes.py`.
