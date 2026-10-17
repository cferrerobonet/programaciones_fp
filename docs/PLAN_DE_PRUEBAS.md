# Plan de pruebas

**Infraestructura:** la de Partes de salida.
- pytest (configuración en `pyproject.toml`) y, con la app, pytest-qt con `QT_QPA_PLATFORM=offscreen`.
- `comprobar.yml` en cada push: ruff, `catalogo.py comprobar` y la suite. Con la app, también `scripts/qa.sh todo|rapido`.
- `compilar.yml` arranca la app compilada en macOS y Windows.

**«Verificado»** = hay una prueba que falla al revertir el cambio.

## Niveles

| Nivel | Qué se prueba | Herramienta |
| --- | --- | --- |
| Cálculos | Pesos, reparto por RA (la regla de CarlosFB: PIICT 7 / 9 / 12), límites, tabla 4.1, modalidad, porcentajes y listas de RA, con la estructura de horas de PIICT que documenta MODELO_DE_DATOS | pytest (`test_calculos.py`) |
| Validaciones | Cada V-xx con un caso que la cumple y otro que no | pytest (`test_validacion.py`) |
| Archivo de trabajo | Ida y vuelta del `.programacion`, esquema, formatos desconocidos y escritura atómica | pytest (`test_programacion.py`) |
| Lector del catálogo | Ficha de cada módulo (textos corregidos, nombre del Decreto 95/2026, Proyecto de 1.º y 2.º, pendientes), normativa por fecha y por curso, citas de las normas y diferencias entre dos catálogos | pytest (`test_catalogo_app.py`) |
| Herencia | Bloques heredados, RA eliminados o renumerados en el catálogo, fechas del curso nuevo | pytest |
| Catálogo (F1) | `catalogo.py comprobar` limpio sobre el catálogo real. Lectores del BOE y del DOGV con textos ficticios que imitan sus formatos y erratas. Esquemas que aceptan lo bueno y rechazan lo malo. `comprobar` detecta cada error en un catálogo ficticio: horas, RA, criterios, fuentes, referencias y orden de la normativa. Con F5: firma válida y no válida, versión menor rechazada | pytest (`test_catalogo.py`, `test_esquemas.py`) |
| **RA de referencia** (F1) | Los RA y criterios del apartado 11 de las seis programaciones de 2026-2027 frente al catálogo, con las erratas del BOE corregidas (ADR-018): idénticos. La prueba comprueba también que las correcciones del catálogo son justo las que hacen las programaciones (solo su posición) | `-m referencias` (local, `PROGRAMACIONES_REFERENCIAS` = carpeta `01 DOCENCIA/FP` de la bóveda) |
| Plantilla | `scripts/plantilla.py comprobar` limpio (sin partes personales, correos ni macros), títulos literales de PIICT y todas sus marcas con valor | pytest (`test_plantilla.py`) + CI |
| Documento | Plantilla rellenada con datos ficticios: títulos exactos, campo TOC, 0 citas sin enlace, `updateFields`, `keepNext`, sin términos vetados ni identificadores repetidos; normativa por fecha, Decreto 95/2026 y resolución del curso, tablas 4 y 4.1 (pesos, combinaciones, sin empresa), criterios con su numeración, negrita y enlaces en los párrafos del profesor, textos propios, fechas, GM con letras, Proyecto, marca «BORRADOR» | pytest (`test_documento.py`) |
| Importación | Ida y vuelta: documento generado → importar → los mismos datos del profesor (unidades, elementos, empresa, ajuste de centro, competencias, párrafos, textos propios) y las mismas fechas del curso | pytest (`test_importar.py`) |
| Incrustación | Exportar → abrir → mismos datos. Huellas: tocado en Word, índice actualizado (no cuenta), datos dañados, una sola parte. **R1 con LibreOffice:** abrir y guardar conserva la parte y sus huellas (automática, también en la CI). **R1 con Word de macOS y Windows:** manual, con `scripts/prueba_word.py` ([PENDIENTE.md](PENDIENTE.md)) | pytest (`test_incrustar.py`) + prueba manual |
| **Regeneración** | Las seis programaciones de 2026-2027 (0517, 0524, 0525, 0526, 0962, 0963): se importan de su `.docx`, se regeneran y se comparan apartado a apartado. Las diferencias de contenido tienen que ser exactamente las aceptadas, cada una con su motivo (abajo). Además: comprobaciones de la guía sobre las regeneradas, la regla del reparto frente al ajuste de PIICT y los datos incrustados iguales a los importados | `-m referencias` (local, lee la bóveda: `test_regeneracion.py`) + `scripts/regenerar.py` |
| PDF | Conversión con LibreOffice (en la CI, instalado) y el índice numerado con las páginas del PDF. Órdenes de Word y paso a LibreOffice si Word falla, sin ejecutar Word. Render de todas las páginas sin tablas cortadas ni títulos solos al pie | pytest (`test_pdf.py`) + revisión |
| Interfaz | Flujo completo con teclado: elegir módulo, rellenar, avisos, vista previa y exportar. Estados vacíos. Bloques heredados que bloquean | pytest-qt |
| Actualizaciones | Las de Partes de salida (API, plan B, hosts) y el catálogo remoto con firma | pytest con red simulada |
| Capturas | `make capturas` con datos ficticios | `scripts/capturas.py` |
| Secretos | `scripts/comprobar_secretos.sh --todo` sobre todo el árbol: ningún dato del servidor de correo ni contraseñas (ADR-016). También se prueba que detecta casos de ejemplo | pytest + CI `Secretos` |

## Criterio de salida de la 1.0

- Las seis programaciones regeneradas sin diferencias de contenido.
- `verificar.py` y `validate.py` limpios.
- Prueba manual en Word (macOS y Windows): la parte incrustada sobrevive a abrir y guardar.
- Instalación desde el release en un equipo del centro (Windows portable incluido).
- Piloto con al menos un profesor que no sea CarlosFB, que hereda una programación.

## Regeneración: qué es diferencia de contenido

`contenido.comparar` lee el cuerpo de las dos programaciones por apartados (sin el índice ni los párrafos vacíos; en las tablas, una celda combinada en vertical repite la de arriba) y empareja párrafos y filas. **No cuentan** (son forma): mayúsculas, comillas y guiones, «RD» por «Real Decreto», espacios ante «%» y un decimal de más («15%» = «15,0 %»), el punto final, «R.A.1.» por «RA1.», «y» o coma ante el último RA, «2/3» por «2 y 3», «HORAS DE CENTRO» por «HORAS CENTRO», la etiqueta del profesorado, celdas vacías de más, el orden de las columnas de las tablas 4 y 4.1 (por su cabecera), el orden de los párrafos dentro de una celda y el de las filas. Todo lo demás es contenido.

**Diferencias aceptadas** (las fija `tests/test_regeneracion.py`, sin texto de las referencias):

| Diferencia | En | Motivo |
| --- | --- | --- |
| Decreto 95/2026 en 1.2 | las seis | Decisión 4 de CarlosFB (ADR-018) |
| Denominación de cinco ECP | 0517, 0524, 0526 | Decisión 2: la del RD 532/2025 |
| Nombre del módulo en la portada | 0526 | Decisión 3: el del Decreto 95/2026 |
| Título de la resolución de instrucciones del curso | las seis | El oficial del DOGV (catálogo). Pendiente de CarlosFB |
| Periodos de empresa de 1.º | 0524, 0525, 0962, 0963 | Redacción y orden de la plantilla. Pendiente |
| RA en la fila de horas de centro | 0524, 0963 | La plantilla la deja vacía. Pendiente |
| Párrafo del anexo V B) en el apartado 2 | 0525, 0962 | Redacción común. Pendiente |
| Real decreto en la cabecera «RA asociados» | 0525, 0962 | Como la plantilla. Pendiente |
| Cabeceras de la tabla 4 del Proyecto | 0526 | Las de la plantilla. Pendiente (ADR-020) |
| Pesos de los elementos | 0962 (a mano), 0963 (por práctica) | La app los calcula. Pendiente |
| Columna «% del curso» en 4.1 | 0962 | La plantilla no la tiene |

El reparto de centro por RA de cada referencia se importa como ajuste del profesor (`centro_ajustado`), así que no da diferencias: la regla da 7 / 9 / 12 en los RA 3, 4 y 6 de PIICT y la programación lleva 8 / 10 / 10.

