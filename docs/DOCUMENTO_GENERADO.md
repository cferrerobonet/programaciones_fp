# Documento generado

Qué lleva la programación que exporta la app, de dónde sale cada pieza y qué se comprueba antes de exportarla.

**Referencia:** la programación de PIICT (0517, SEA 2.º), plantilla vigente desde el 2026-10-06. En la bóveda, `01 DOCENCIA/FP/517 - …/01 Programación/`, con su nota gemela.

**Reglas de redacción:** las de la guía de la bóveda `programacion-didactica`. Si cambian allí, se cambian aquí.

**Origen de cada pieza:**
- **A:** automático, desde el catálogo.
- **C:** calculado.
- **M:** manual del profesor.
- **F:** texto fijo de la plantilla, con variables `{…}` cuando las lleva.

## Portada

| Pieza | Origen |
| --- | --- |
| «PROGRAMACIÓN DIDÁCTICA» y estructura de las tablas | F |
| Familia profesional · ciclo («Grado Superior: …») · módulo («0517 – …») · Nº horas del módulo | A |
| Profesor (uno o varios) | M |
| Curso académico | A (curso escolar en vigor) |

La portada no lleva encabezado ni pie. El resto de páginas, sí: logotipos, franja vertical «Escuelas Profesionales Luis Amigó – Programación didáctica» y la dirección en el pie.

## Índice

Campo `TOC \o "2-3" \h \z \u` con exactamente los títulos de la plantilla:
- **Nivel 1 (Título 2):** en versales y negrita.
- **Nivel 2 (Título 3):** normal.
- **Interlineado** en los estilos TDC2 y TDC3, no en las entradas.
- `<w:updateFields w:val="true"/>` en `settings.xml`.

## Apartados

| Apartado | Piezas | Origen |
| --- | --- | --- |
| **1. Datos identificativos** | Párrafo inicial con el título del ciclo y su familia | F + A |
| 1.1 Normativa básica estatal | Real decreto del título y sus modificaciones; LO 3/2022, RD 659/2023, RD 532/2025, LOE y la norma de 2024 que modifica los títulos de su grado (RD 499/2024 en GM, RD 500/2024 en GS) | A |
| 1.2 Normativa autonómica | Orden 20/2019, Orden 8/2025 (modificada por la Orden 5/2026), Decreto 114/2025 y la resolución de instrucciones de FP del curso | A (la resolución cambia cada curso) |
| **2. Estándares de competencia y módulos** | Párrafos sobre el RD del título, la LO 3/2022, el RD 659/2023 y el RD 532/2025 | F + A |
| | Tabla: todos los módulos técnicos del ciclo **y el de proyecto**, con sus ECP según el anexo V B del RD (UC → ECP con el mismo código) | A |
| | Competencia general (art. 4 del RD) | A |
| 2.1 Competencias profesionales, personales y sociales | Lista completa a)…r) del art. 5 | A |
| 2.2 Módulos optativos ofertados | Tabla de optativos del ciclo y párrafos | A (oferta del centro) + F |
| **3. Contribución de los RA** | Párrafos y letras de competencias del módulo (orientaciones pedagógicas del anexo I) | F + A |
| | Tabla RA → competencias | **M** (la app propone las letras del módulo y el profesor marca cuáles van con cada RA) |
| **4. Secuenciación** | «El presente módulo tiene una carga horaria de {h} h semanales» | F + A |
| | Tabla: unidad, sesiones/horas, trimestre, elemento de evaluación (horas), peso y RA | **M** + C (peso) |
| | Filas de horas de centro y de empresa (con los RA que van a empresa) y total | C |
| 4.1 Ponderación de cada RA | RA, horas totales (centro + empresa), modalidad y horas en empresa | C (a partir de M), con el reparto de centro por RA ajustable por el profesor |
| **5.1 Metodología** | Principios generales y pedagógicos, pedagogía amigoniana y evaluación continua | F |
| | Párrafos propios del módulo: material de referencia, aula y taller, entrega de ejercicios | **M** |
| **6. Recursos** | Cuaderno o libro, plataformas, software, multimedia | **M** (con opciones habituales) |
| | Párrafo del móvil | F |
| **7. Espacios y equipamientos** | Aulas y talleres del módulo | **M** |
| | Párrafo general | F |
| **8. Atención a la diversidad** | Todo, con Decreto 104/2018, Orden 20/2019 y Resolución de 2021-12-23 | F |
| **9. Evaluación** | Párrafos de la Orden 8/2025 | F + A |
| | % de empresa del módulo dentro del párrafo de calificación | C |
| | Fechas: evaluación inicial, 1.ª, 2.ª, 3.ª, ordinaria y extraordinaria | A (curso escolar) |
| 9.1 Formación en empresa | Periodos según jornada (7 h u 8 h al día) y curso (1.º y 2.º difieren) | A (curso escolar) |
| | Párrafo del Proyecto intermodular | F |
| **10. Actividades complementarias** | Párrafos generales, sin excursiones lúdicas | F (+ M opcional) |
| **11. Criterios y procedimientos** | Párrafo con el RD del título | F + A |
| | Cada RA con sus criterios de evaluación, literales | A |
| 11.1 Instrumentos · 11.2 Elementos de evaluación | Instrumentos, E/P/T, asistencia del 85 %, repetición de pruebas, conductas fraudulentas, visitas, expulsiones | F |
| **12. Recuperación** | Programa de recuperación (art. 14 de la Orden 8/2025), sin el párrafo propio antiguo | F |

**Fuera siempre:** objetivos generales y contenidos básicos (no están en el guion), excursiones lúdicas y el párrafo propio de recuperación en el 12.

## Formato

- **Legislación:** siempre con hipervínculo a BOE o DOGV, también la citada dentro de un párrafo. Las listas, por fecha creciente.
- **Porcentajes de centro y empresa:** enteros. Empresa redondeada hacia arriba; centro = 100 − empresa. Los pesos de cada elemento sí llevan un decimal con coma («14,5 %»).
- **Títulos:** ningún párrafo fuera de los títulos de la plantilla con estilo Título 1-3. `keepNext` en los títulos, para que no se queden solos al pie.
- **Fechas:** en el texto, como en la plantilla («20/11/2026» en las listas, «del 31 de mayo al 3 de junio de 2027» en la prosa).
- **Software:** «CYPE» como nombre de la suite, salvo que el profesor nombre a propósito un programa concreto.

## Nombre de los archivos

**La misma nomenclatura que las programaciones actuales de CarlosFB** (convención de la bóveda: `CICLO N - 0xxx - Nombre del módulo`):

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
- **Nombre:** el oficial completo del catálogo, sin abreviar. Si contiene caracteres que no admite el sistema de archivos (`/ : * ? " < > |`), se sustituyen por un guion.
- **Nombre ya existente en la carpeta de destino:** la app pregunta si se sustituye. Nunca sobrescribe sin preguntar.

## Datos incrustados

Parte XML personalizada (`customXml/`) con espacio de nombres `urn:epla:programaciones:1`. Contiene:
- El JSON completo de la programación (ver [MODELO_DE_DATOS.md](MODELO_DE_DATOS.md)).
- La versión del catálogo y de la plantilla.
- Dos huellas SHA-256: la del JSON y la del texto del cuerpo del documento al exportar.

Al abrir el `.docx`:
- Si la huella del texto no coincide, se avisa de que se modificó en Word.
- Si la del JSON no coincide, el archivo se trata como dañado.

## Validaciones

**Rojas:** bloquean la definitiva. **Ámbar:** solo avisan.

| ID | Regla | Gravedad |
| --- | --- | --- |
| V-01 | Horas de las unidades + horas de empresa = horas del módulo | Roja |
| V-02 | Cada RA está en al menos un elemento de evaluación o en empresa | Roja |
| V-03 | Cada unidad tiene horas > 0, trimestre (1-3) y elemento de evaluación; cada elemento tiene al menos un RA | Roja |
| V-04 | Las horas de centro de cada RA (propuestas o ajustadas) quedan entre las de sus elementos exclusivos y las de todos los que lo incluyen, y suman las horas de centro | Roja |
| V-05 | Profesorado no vacío | Roja |
| V-06 | Ningún bloque heredado sin confirmar | Roja |
| V-07 | Cada RA tiene al menos una competencia en la tabla del apartado 3 | Roja |
| V-08 | Hay cambios del currículo de este módulo sin aceptar (ADR-015): se exportaría con la versión anterior | Ámbar |
| V-09 | Un trimestre sin unidades | Ámbar |
| V-10 | Un RA con modalidad «Empresa» y 0 h de empresa, o «Centro» con horas de empresa | Roja |

## Comprobación del documento

Los mismos pasos de la guía `programacion-didactica`, ahora automatizados en los tests:
- `verificar.py`: títulos iguales a la plantilla, campo TOC, 0 citas sin enlace y términos vetados.
- Validación del `.docx`.
- Render a PDF y revisión de que portada, tablas e índice están completos.
