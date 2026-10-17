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
