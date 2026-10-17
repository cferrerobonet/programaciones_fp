# Documento generado

Qué lleva la programación que exporta la app, de dónde sale cada pieza y qué se comprueba antes de exportarla. Lo genera `src/programaciones/documento.py` (ADR-006 y ADR-019).

**Referencia:** la programación de PIICT (0517, SEA 2.º), plantilla vigente desde el 2026-10-06. En la bóveda, `01 DOCENCIA/FP/517 - …/01 Programación/`, con su nota gemela.

**Reglas de redacción:** las de la skill de la bóveda `programacion-didactica`. Si cambian allí, se cambian aquí.

**Origen de cada pieza:**
- **A:** automático, desde el catálogo.
- **C:** calculado.
- **M:** manual del profesor.
- **F:** texto fijo de la plantilla, con variables `{…}` cuando las lleva.

## Plantilla y marcas

- **Dónde:** `src/programaciones/recursos/plantilla/es/`, desempaquetada (las partes XML del .docx y los logotipos), con su versión en `plantilla.yaml`. La genera `scripts/plantilla.py crear <programación de PIICT>`, que quita lo personal (comentarios, autor, metadatos de SharePoint, el correo del pie, los identificadores aleatorios de Word) y cambia por marcas lo que depende del ciclo, del módulo, del curso o del profesor. `scripts/plantilla.py comprobar` la revisa.
- **Marcas:**
  - `{{nombre}}`: texto o hipervínculos dentro de un párrafo.
  - `{{*lista}}`: un párrafo que se repite (normas, competencias, párrafos del profesor).
  - `{{@lista.campo}}`: una fila de tabla que se repite.
  - `{{#grupo}}` … `{{/grupo}}`: un grupo de párrafos que se repite (cada RA con sus criterios; cada periodo de empresa). Cada copia reinicia sus listas: los criterios de cada RA empiezan en a).
  - `{{?condición}}` … `{{/condición}}`: un bloque que solo queda si se cumple. Con `sustituible:clave`, un bloque fijo que el profesor puede cambiar por el suyo (`textos_propios`, ADR-020).
- **Formato:** cada marca lleva el formato del texto al que sustituye. Donde la plantilla tiene un prefijo con otro formato («R.A.1.», «UD00.», «Alumnos que realicen 8h/día»), hay dos marcas seguidas.

## Portada

| Pieza | Origen |
| --- | --- |
| «PROGRAMACIÓN DIDÁCTICA» y estructura de las tablas | F |
| Familia profesional · ciclo («Grado Superior:» o «Grado Medio:» y el nombre del ciclo) · módulo («0517 – …», con el nombre del Decreto 95/2026) · Nº horas del módulo | A |
| Profesor (uno o varios): «Profesor:» con uno y «Profesores:» con varios, un nombre por línea | M |
| Curso académico | M (el de la programación) |

La portada no lleva encabezado ni pie. El resto de páginas, sí: logotipos, franja vertical «Escuelas Profesionales Luis Amigó – Programación didáctica» y la dirección en el pie. El correo del departamento no va en la plantilla del repositorio (es público): sale solo si se da en la opción `correo_pie` (Ajustes, F4; pendiente de CarlosFB).

## Índice

Campo `TOC \o "2-3" \h \z \u` con exactamente los títulos de la plantilla:
- **Nivel 1 (Título 2):** en versales y negrita.
- **Nivel 2 (Título 3):** normal.
- **Interlineado** en los estilos TDC2 y TDC3, no en las entradas.
- `<w:updateFields w:val="true"/>` en `settings.xml`: Word lo rehace al abrir. Con LibreOffice (PDF sin Word), `pdf.py` numera las entradas con las páginas del PDF y vuelve a convertir.

## Apartados

| Apartado | Piezas | Origen |
| --- | --- | --- |
| **1. Datos identificativos** | Párrafo inicial con el título del ciclo y su familia | F + A |
| 1.1 Normativa básica estatal | Las comunes de la plantilla, con su texto y sus enlaces: LO 3/2020 (con la LOE), LO 3/2022, RD 659/2023, RD 500/2024 (solo GS) y RD 532/2025. Más las del título, con su título oficial: el real decreto, sus correcciones de errores y las normas que lo modifican (RD 401/2023 en SEA y ARI; RD 499/2024 en GM). Todas por fecha de publicación | F + A |
| 1.2 Normativa autonómica | Las comunes de la plantilla (Orden 20/2019, Orden 8/2025 modificada por la Orden 5/2026, Decreto 114/2025), el **Decreto 95/2026** (ADR-018) y la resolución de instrucciones de FP del curso, con su título oficial del DOGV. Por fecha | F + A (la resolución cambia cada curso) |
| **2. Estándares de competencia y módulos** | Párrafos sobre el RD del título («en su redacción vigente, actualizada por» la norma que actualiza el título o «modificada por» el RD 500/2024), la LO 3/2022, el RD 659/2023 y el RD 532/2025. El del anexo V B): «en la redacción dada por» la norma que lo reescribe, «(anexo que el … no modifica)» si el título se actualizó sin tocarlo, o «cuya redacción no ha sido modificada por el Real Decreto 500/2024» | F + A |
| | Tabla: las correspondencias del anexo V B) (UC → ECP con el mismo código y la denominación del RD 532/2025) y, una fila cada uno, los módulos técnicos y el Proyecto sin correspondencia («Sin correspondencia directa … del RD …»). Primero las filas del módulo de la programación; después, por el código del primer módulo. Los módulos de una fila, por código, con el nombre del Decreto 95/2026 | A |
| | Competencia general (art. 4, con las erratas corregidas) | A |
| 2.1 Competencias profesionales, personales y sociales | Lista completa a)…r) del art. 5 (en GA e IT, con letras: ADR-018) | A |
| 2.2 Módulos optativos ofertados | Tabla de optativos del ciclo y párrafos | A (oferta del centro) + F |
| **3. Contribución de los RA** | Párrafos y letras de competencias del módulo (orientaciones pedagógicas del anexo I, «en la redacción dada por» la norma que reescribe el módulo si no es el RD del título). En el Proyecto, «la totalidad de las competencias … del título, de la a) a la r)» | F + A |
| | Tabla RA → competencias | **M** (la app propone las letras del módulo y el profesor marca cuáles van con cada RA) |
| **4. Secuenciación** | «El presente módulo tiene una carga horaria de {h} h semanales» | F + A |
| | Contenidos propios, si el módulo no tiene contenidos básicos (el Proyecto) | **M** |
| | Tabla: unidad (código en negrita, título y, debajo, su descripción), sesiones/horas, trimestre («1 y 2» si son dos), elemento de evaluación (nombre y, debajo, «(Nh)» o su detalle), peso y RA. Las unidades seguidas de un mismo elemento combinan en vertical las celdas del elemento, el peso y los RA | **M** + C (peso) |
| | Filas de horas de centro y de empresa (con los RA que van a empresa) y total. Sin horas de empresa (el Proyecto), solo el total | C |
| | Notas bajo la tabla | **M** |
| 4.1 Ponderación de cada RA | RA, horas totales (centro + empresa), modalidad y horas en empresa («—» si no tiene). Sin horas de empresa, sin esa columna. Notas bajo la tabla (M) | C (a partir de M), con el reparto de centro por RA ajustable por el profesor |
| **5.1 Metodología** | Principios generales y pedagógicos, pedagogía amigoniana y evaluación continua | F |
| | Párrafos propios del módulo: antes de los comunes del medio (material, aula y taller, entrega de ejercicios) y al final («Finalmente…») | **M** |
| **6. Recursos** | Cuaderno o libro, plataformas, software, multimedia | **M** (con opciones habituales) |
| | «Empleo de recursos didácticos multimedia en el aula» y párrafo del móvil | F |
| **7. Espacios y equipamientos** | Aulas y talleres del módulo | **M** |
| | Párrafos generales | F |
| **8. Atención a la diversidad** | Todo, con Decreto 104/2018, Orden 20/2019 y Resolución de 2021-12-23 | F |
| **9. Evaluación** | Párrafos de la Orden 8/2025 | F + A |
| | Párrafo de calificación con el % de empresa del módulo y «el profesor del módulo» (o «el profesorado», con varios). Sustituible por un texto propio | C + F |
| | Fechas: evaluación inicial, 1.ª, 2.ª, 3.ª, ordinaria («del 31 de mayo al 3 de junio de 2027») y extraordinaria | A (curso escolar) |
| 9.1 Formación en empresa | Un párrafo por jornada, de más a menos horas: «Alumnos que realicen 8h/día (en total 43 días de formación): desde el 2 de marzo al 28 de mayo de 2027». Según el grado y el curso (1.º y 2.º difieren) | A (curso escolar) |
| | Párrafo del Proyecto intermodular | F |
| **10. Actividades complementarias** | Párrafos generales, sin excursiones lúdicas | F (+ M opcional) |
| **11. Criterios y procedimientos** | Párrafo con el RD del título («en su redacción actualizada por…»; en el Proyecto, además, «y por el Real Decreto 500/2024, que da al módulo la denominación de «Proyecto intermodular»…») | F + A |
| | Cada RA («R.A.n.») con sus criterios de evaluación, con las erratas del BOE corregidas (ADR-018) | A |
| 11.1 Instrumentos · 11.2 Elementos de evaluación | Instrumentos, E/P/T, asistencia del 85 %, repetición de pruebas, conductas fraudulentas, visitas, expulsiones. Instrumentos, elementos y el bloque de pérdida de evaluación continua, repeticiones y conductas, sustituibles por textos propios | F (o M) |
| **12. Recuperación** | Programa de recuperación (art. 14 de la Orden 8/2025), sin el párrafo propio antiguo | F |

**Fuera siempre:** objetivos generales y contenidos básicos (no están en el guion), excursiones lúdicas y el párrafo propio de recuperación en el 12.

## Formato

- **Legislación:** siempre con hipervínculo a BOE o DOGV, también la citada dentro de un párrafo. En los párrafos del profesor, la app enlaza sola las normas del catálogo que se citen («Real Decreto 1127/2010, de 10 de septiembre», «RD 1127/2010», «Decreto 114/2025»…). Las listas, por fecha creciente.
- **Porcentajes de centro y empresa:** enteros. Empresa redondeada hacia arriba; centro = 100 − empresa. Los pesos de cada elemento sí llevan un decimal con coma («14,5 %»).
- **RA de una celda:** «RA1 y RA2», «RA3, RA4 y RA6» y, con cinco o más seguidos, «RA2 → RA6».
- **Títulos:** ningún párrafo fuera de los títulos de la plantilla con estilo Título 1-3. `keepNext` en los títulos, para que no se queden solos al pie.
- **Fechas:** en el texto, como en la plantilla («20/11/2026» en las listas, «del 31 de mayo al 3 de junio de 2027» en la prosa).
- **Software:** «CYPE» como nombre de la suite, salvo que el profesor nombre a propósito un programa concreto.
- **Vista previa:** marca de agua «BORRADOR» en diagonal en las páginas con encabezado.

## Nombre de los archivos

**La misma nomenclatura que las programaciones actuales de CarlosFB** (convención de la bóveda: `CICLO N - 0xxx - Nombre del módulo`), en `documento.nombre_archivo`:

```
<SIGLA DEL CICLO> <curso> - <código de 4 cifras> - <nombre oficial del módulo>.<ext>
```

| Archivo | Ejemplo |
| --- | --- |
| Programación en Word | `SEA 2 - 0517 - Procesos en instalaciones de infraestructuras comunes de telecomunicaciones.docx` |
| Programación en PDF | `… .pdf`, con el mismo nombre |
| Archivo de trabajo | `… .programacion`, con el mismo nombre |
| Excel de RA (función futura, ver [HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-excel-de-ra)) | `… .xlsx`, con el mismo nombre, como el que ya acompaña a cada programación |

Ejemplos reales en la bóveda: `STI 1 - 0525 - Configuración de infraestructuras de sistemas de telecomunicaciones.docx`, `ARI 1 - 0962 - Sistemas de potencia.docx` y `SEA 1 - 0524 - Configuración de instalaciones eléctricas.docx`.

- **Sigla del ciclo:** SEA, STI y ARI, como en las programaciones actuales. Para el resto de ciclos se toman las de los grupos de Web Pedidos (GA, IT, IEA, CAR, EMV, ADM, ISO, AUT).
- **Curso:** 1 o 2.
- **Nombre:** el oficial completo del Decreto 95/2026 (ADR-018), sin abreviar. Si contiene caracteres que no admite el sistema de archivos (`/ : * ? " < > |`), se sustituyen por un guion.
- **Nombre ya existente en la carpeta de destino:** la app pregunta si se sustituye. Nunca sobrescribe sin preguntar.

## Datos incrustados

Parte XML personalizada (`customXml/itemN.xml`, con su `itemPropsN.xml`) con espacio de nombres `urn:epla:programaciones:1` (`incrustar.py`). Contiene:
- El JSON completo de la programación (ver [MODELO_DE_DATOS.md](MODELO_DE_DATOS.md)).
- La versión del catálogo y de la plantilla.
- Dos huellas SHA-256: la del JSON canónico y la del texto del cuerpo del documento al exportar (sin el índice, que Word rehace al abrir).

Al abrir el `.docx`:
- Si la huella del texto no coincide, se avisa de que se modificó en Word.
- Si la del JSON no coincide, el archivo se trata como dañado.
- Una exportación nueva sustituye la parte anterior.

## Validaciones

**Rojas:** bloquean la definitiva. **Ámbar:** solo avisan (`validacion.py`).

| ID | Regla | Gravedad |
| --- | --- | --- |
| V-01 | Horas de las unidades + horas de empresa = horas del módulo | Roja |
| V-02 | Cada RA está en al menos un elemento de evaluación o en empresa | Roja |
| V-03 | Cada unidad tiene horas > 0, trimestre (1-3) y elemento de evaluación; cada elemento tiene al menos un RA y solo RA del módulo | Roja |
| V-04 | Las horas de centro de cada RA (propuestas o ajustadas) quedan entre las de sus elementos exclusivos y las de todos los que lo incluyen, y suman las horas de centro | Roja |
| V-05 | Profesorado no vacío | Roja |
| V-06 | Ningún bloque heredado sin confirmar | Roja |
| V-07 | Cada RA tiene al menos una competencia en la tabla del apartado 3 | Roja |
| V-08 | Hay cambios del currículo de este módulo sin aceptar (ADR-015): se exportaría con la versión anterior | Ámbar |
| V-09 | Un trimestre sin unidades (en 2.º, el 3.º suele ser de empresa: es un aviso) | Ámbar |
| V-10 | Un RA sin horas de centro ni de empresa (sin modalidad posible; la modalidad se calcula, así que no puede contradecir las horas) | Roja |
| V-11 | Falta en el catálogo un dato que el documento necesita (`pendiente`: el Proyecto de GM, optativos sin oferta…) | Roja |

## Comprobación del documento

Los mismos pasos de la skill `programacion-didactica`, automatizados en las pruebas:
- `contenido.verificar` (lo de `verificar.py`): títulos iguales a la plantilla, campo TOC, `updateFields`, 0 citas sin enlace y palabra prohibida.
- Ningún identificador repetido (marcadores, `w14:paraId`), que Word da por documento dañado.
- `scripts/regenerar.py <carpeta 01 DOCENCIA/FP>`: rehace las seis programaciones de referencia y las compara apartado a apartado (`contenido.comparar`). La prueba `-m referencias` fija las diferencias aceptadas ([PLAN_DE_PRUEBAS.md](PLAN_DE_PRUEBAS.md)).
- `validate.py` de la skill `docx` y render a PDF con LibreOffice, mirando portada, tablas e índice.
