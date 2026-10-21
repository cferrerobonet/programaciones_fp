# Plan de pruebas

**Infraestructura:** la de Partes de salida.
- pytest (configuración en `pyproject.toml`) y, con la app, pytest-qt con `QT_QPA_PLATFORM=offscreen`.
- `comprobar.yml` en cada push: ruff, `catalogo.py comprobar`, `plantilla.py comprobar` y la suite, también la interfaz sin pantalla. En local, lo mismo con `scripts/qa.sh todo` (o `rapido`, `ui`).
- `compilar.yml` comprueba los datos empaquetados (`scripts/comprobar_paquete.sh`) y arranca la app compilada en macOS y Windows: llega a la ventana, lee el catálogo, los esquemas y la plantilla que lleva dentro y abre un PDF con QtPdf.

**«Verificado»** = hay una prueba que falla al revertir el cambio.

## Niveles

| Nivel | Qué se prueba | Herramienta |
| --- | --- | --- |
| Cálculos | Pesos, reparto por RA (la regla de CarlosFB: PIICT 7 / 9 / 12), límites, tabla 4.1, modalidad, porcentajes y listas de RA, con la estructura de horas de PIICT que documenta MODELO_DE_DATOS | pytest (`test_calculos.py`) |
| Validaciones | Cada V-xx con un caso que la cumple y otro que no | pytest (`test_validacion.py`) |
| Archivo de trabajo | Ida y vuelta del `.programacion`, esquema, formatos desconocidos y escritura atómica | pytest (`test_programacion.py`) |
| Lector del catálogo | Ficha de cada módulo (textos corregidos, nombre del Decreto 95/2026, Proyecto de 1.º y 2.º, pendientes), normativa por fecha y por curso, citas de las normas y diferencias entre dos catálogos | pytest (`test_catalogo_app.py`) |
| Herencia y archivo de trabajo | Bloques heredados (los vacíos no), RA que ya no están, curso escolar nuevo, leer un `.docx` exportado, uno antiguo y un `.programacion`; guardado con 10 copias y estado de cada paso | pytest (`test_herencia.py`) |
| Exportación | Word y PDF con el nombre normalizado y los datos dentro, solo Word, sin Word ni LibreOffice, documento que no pasa las comprobaciones, vista previa con «BORRADOR», fechas «pendiente» sin curso escolar | pytest (`test_exportacion.py`) |
| Catálogo (F1) | `catalogo.py comprobar` limpio sobre el catálogo real. Lectores del BOE y del DOGV con textos ficticios que imitan sus formatos y erratas. Esquemas que aceptan lo bueno y rechazan lo malo. `comprobar` detecta cada error en un catálogo ficticio: horas, RA, criterios, fuentes, referencias y orden de la normativa. Con F5: firma válida y no válida, versión menor rechazada | pytest (`test_catalogo.py`, `test_esquemas.py`) |
| **RA de referencia** (F1) | Los RA y criterios del apartado 11 de las seis programaciones de 2026-2027 frente al catálogo, con las erratas del BOE corregidas (ADR-018): idénticos. La prueba comprueba también que las correcciones del catálogo son justo las que hacen las programaciones (solo su posición) | `-m referencias` (local, `PROGRAMACIONES_REFERENCIAS` = carpeta `01 DOCENCIA/FP` de la bóveda) |
| Plantilla | `scripts/plantilla.py comprobar` limpio (sin partes personales, correos ni macros), títulos literales de PIICT y todas sus marcas con valor | pytest (`test_plantilla.py`) + CI |
| Documento | Plantilla rellenada con datos ficticios: títulos exactos, campo TOC, 0 citas sin enlace, `updateFields`, `keepNext`, sin términos vetados ni identificadores repetidos; normativa por fecha, Decreto 95/2026 y resolución del curso, tablas 4 y 4.1 (pesos, combinaciones, sin empresa), criterios con su numeración, negrita y enlaces en los párrafos del profesor, textos propios, fechas, GM con letras, Proyecto, marca «BORRADOR» | pytest (`test_documento.py`) |
| Importación | Ida y vuelta: documento generado → importar → los mismos datos del profesor (unidades, elementos, empresa, ajuste de centro, competencias, párrafos, textos propios) y las mismas fechas del curso | pytest (`test_importar.py`) |
| Incrustación | Exportar → abrir → mismos datos. Huellas: tocado en Word, índice actualizado (no cuenta), datos dañados, una sola parte. **R1 con LibreOffice:** abrir y guardar conserva la parte y sus huellas (automática, también en la CI). **R1 con Word de macOS:** pasada el 2026-10-19 (Guardar y Guardar como…). **Con Word de Windows:** manual, con `scripts/prueba_word.py` ([PENDIENTE.md](PENDIENTE.md)) | pytest (`test_incrustar.py`) + prueba manual |
| **Regeneración** | Las seis programaciones de 2026-2027 (0517, 0524, 0525, 0526, 0962, 0963): se importan de su `.docx`, se regeneran y se comparan apartado a apartado. Las diferencias de contenido tienen que ser exactamente las aceptadas, cada una con su motivo (abajo). Además: comprobaciones de la guía sobre las regeneradas, la regla del reparto frente al ajuste de PIICT y los datos incrustados iguales a los importados | `-m referencias` (local, lee la bóveda: `test_regeneracion.py`) + `scripts/regenerar.py` |
| PDF | Conversión con LibreOffice (en la CI, instalado) y el índice numerado con las páginas del PDF. Órdenes de Word y paso a LibreOffice si Word falla, sin ejecutar Word. ONLYOFFICE (`x2t` con XML de parámetros y las fuentes del perfil) simulado y, donde esté instalado y abierto una vez, la conversión real y R1 (`test_pdf_con_onlyoffice_de_verdad_y_r1`). Render de todas las páginas sin tablas cortadas ni títulos solos al pie | pytest (`test_pdf.py`) + revisión |
| Interfaz | Arranque, barra y tres zonas, estados vacíos, navegación (Programaciones, Ajustes, menú, ayuda, novedades), Ajustes, vista previa con QtPdf y la prueba de arranque. **Flujo completo** (`test_flujo.py`): elegir el módulo tecleando el código y con filtros, lo oficial de solo lectura, rellenar los cinco bloques, cálculos en gris, ajustes de horas (V-04) y de pesos (V-12), avisos, vista previa y miniatura, exportar Word y PDF con el nombre normalizado, no sobrescribir sin preguntar, volver a abrir el Word (y el aviso si se tocó en Word), sin curso escolar (V-11), heredar y confirmar, cambios de currículo con un catálogo anterior ficticio, listado con el patrón de los listados, primer arranque, ordenar y quitar filas con el teclado y autoguardado. Exportar con LibreOffice de verdad si está | pytest-qt (`test_interfaz.py`, `test_flujo.py`) |
| Actualizaciones | Las de Partes de salida (sha256 contra el digest, timeout, plan B por la web, hosts, versiones) , una 0.1.2 que detecta la 0.2.0 en `/releases/latest` (ADR-026) y, en macOS, la sustitución en su sitio con bundles falsos y `hdiutil`, `ditto` y `open` simulados: éxito, sin permiso, copia que falla con la vieja en su sitio, desarrollo y Windows sin cambios (ADR-029) | pytest con red simulada (`test_actualizaciones.py`, `test_actualizacion_macos.py`) |
| Catálogo publicado y vigía (F5) | Versión del catálogo y huella, publicar y verificar con una clave de prueba, descarga una vez al día, **nunca sin firma o con firma mala**, otra clave, paquete cambiado, rutas raras, catálogo viejo, sin red, versiones que faltan. Vigía con fuentes falsas: sin cambios, punto de partida, texto de un criterio (PR para CarlosFB), DOGV y horas, RA nuevo, normas nuevas en sumarios, Conselleria y consolidados (a mano), fuente caída sin tocar nada, lo que no sabe leer, simulacro y la PR con git y gh simulados, que **nunca se fusiona ni se aprueba** (ADR-028; además, `scripts/comprobar_sin_fusion.sh` en la CI). **Prueba de cierre:** un cambio simulado en una norma recorre vigía → PR → CarlosFB fusiona → catálogo firmado → aviso en la app → la profesora acepta. Ejecución real de `vigia.yml` con `workflow_dispatch` | pytest y pytest-qt (`test_catalogo_remoto.py`, `test_vigia.py`) y GitHub Actions |
| Correo (ADR-014) | Plantilla del asunto y del cuerpo, destinatarios, tamaño, programa por defecto de macOS, orden de los métodos por plataforma, Mail y Outlook por AppleScript (datos como argumentos), Outlook clásico por COM (datos en JSON), `.eml` con `X-Unsent: 1` y la reserva `mailto:`, con el programa de correo **simulado** (`conftest.ClienteSimulado`): nunca se abre uno de verdad. Falta la prueba a mano (`docs/PENDIENTE.md`) | pytest (`test_correo.py`) |
| Gestión, curso escolar y favoritos (0.2.0) | Apartado «Curso escolar» de Ajustes y menú, acciones del listado según las marcadas (botones y clic derecho), vista previa de varias, exportar a carpeta sin sustituir sin preguntar, enviar por correo (exporta lo que falta), borrar a la papelera simulada sin tocar lo exportado, Ajustes → Correo y la estrella (clic, clic derecho, ⌘D, chip y «Limpiar», nombre accesible) | pytest-qt (`test_gestion.py`) |
| Tipografía | Cada texto del documento, encabezados y pies (normal, Proyecto y GM, con textos propios) resuelve a una fuente del texto de la plantilla y nunca a Times New Roman, en las ranuras ascii, hAnsi y asiática (`ooxml.fuentes_de_texto`) | pytest (`test_documento.py`) |
| Capturas | `make capturas` con datos ficticios | `scripts/capturas.py` |
| Proyecto y app compilada | Versión coherente, spec con plantilla, catálogo, esquemas y QtPdf, catálogo leído de `sys._MEIPASS`, nombres ASCII, nombres de los instaladores, `AppId` propio, BOM de `build_windows.ps1`, marcas de la prueba de arranque en la CI. En GitHub: datos empaquetados y arranque en macOS y Windows | pytest (`test_proyecto.py`) + `compilar.yml` |
| Secretos | `scripts/comprobar_secretos.sh --todo` sobre todo el árbol: ningún dato del servidor de correo ni contraseñas (ADR-016). También se prueba que detecta casos de ejemplo | pytest + CI `Secretos` |

## Criterio de salida de la 1.0

- Las seis programaciones regeneradas sin diferencias de contenido.
- `verificar.py` y `validate.py` limpios.
- Prueba manual en Word (macOS y Windows): la parte incrustada sobrevive a abrir y guardar.
- Instalación desde el release en un equipo del centro (Windows portable incluido).
- Piloto con al menos un profesor que no sea CarlosFB, que hereda una programación.

## Regeneración: qué es diferencia de contenido

`contenido.comparar` lee el cuerpo de las dos programaciones por apartados (sin el índice ni los párrafos vacíos; en las tablas, una celda combinada en vertical repite la de arriba) y empareja párrafos y filas. **No cuentan** (son forma): mayúsculas, comillas y guiones, «RD» por «Real Decreto», espacios ante «%» y un decimal de más («15%» = «15,0 %»), el punto final, «R.A.1.» por «RA1.», «y» o coma ante el último RA, «2/3» por «2 y 3», «HORAS DE CENTRO» por «HORAS CENTRO», la etiqueta del profesorado, celdas vacías de más, el orden de las columnas de las tablas 4 y 4.1 (por su cabecera), el orden de los párrafos dentro de una celda y el de las filas. Todo lo demás es contenido.

**Diferencias esperadas por decisión de CarlosFB** (2026-10-17, ADR-018; las fija `tests/test_regeneracion.py`, sin texto de las referencias):

| Diferencia | En | Decisión |
| --- | --- | --- |
| Decreto 95/2026 en 1.2 | las seis | 4 |
| Denominación de cinco ECP (RD 532/2025) | 0517, 0524, 0526 | 2 |
| Nombre del módulo en la portada (Decreto 95/2026) | 0526 | 3 |
| Nota de Educamos bajo la 4.1 (texto fijo de la plantilla, ADR-042; desaparece al volver a exportar la referencia) | las seis | 2026-10-21 |
| Título oficial de la resolución de instrucciones del curso | las seis | 8 |
| Redacción y orden de la plantilla en los periodos de empresa de 1.º | 0524, 0525, 0962, 0963 | 8 |
| Fila de horas de centro sin los RA, como PIICT | 0524, 0963 | 8 |
| Párrafo del anexo V B) con la redacción común | 0525, 0962 | 8 |
| Real decreto en la cabecera «RA asociados», como PIICT | 0525, 0962 | 8 |

**Diferencia de formato aceptada:** la franja vertical del margen, recolocada bajo el escudo (no es contenido: la comparación lee el cuerpo, y `tests/test_plantilla.py` mide en EMU que no se solape con el escudo ni toque el pie).

Los pesos que no salen de las horas (0962, a mano; 0963, por práctica) y la columna «% del curso» de 0962 se importan como ajustes del profesor (decisión 9) y la tabla 4 de 0526 es la variante de los proyectos (decisión 10): no dan diferencias.

El reparto de centro por RA de cada referencia se importa como ajuste del profesor (`centro_ajustado`), así que no da diferencias: la regla da 7 / 9 / 12 en los RA 3, 4 y 6 de PIICT y la programación lleva 8 / 10 / 10.

