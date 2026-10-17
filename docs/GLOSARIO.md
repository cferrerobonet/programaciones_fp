# Glosario

Términos del dominio, tal como se usan en el código y en la documentación. Los nombres del código van en castellano y sin tildes (`resultados_aprendizaje` no: `ra`; `elemento`; `empresa`).

| Término | Significado | En el código |
| --- | --- | --- |
| **FP · GB · GM · GS** | Formación Profesional · Grado Básico, Medio y Superior | `grado` |
| **Ciclo** | Ciclo formativo (título), p. ej. SEA = Técnico Superior en Sistemas Electrotécnicos y Automatizados | `ciclo` (sigla) |
| **Módulo** | Módulo profesional, con código de 4 cifras (0517). Los del Decreto 114/2025 pueden llevar sufijo de ciclo (1665031) | `modulo` |
| **Módulo común** | Inglés profesional (0156 GM, 0179 GS), Itinerario personal para la empleabilidad I y II (1709, 1710), Digitalización aplicada (1664 GM, 1665 GS), Sostenibilidad aplicada (1708) | `tipo` |
| **Proyecto intermodular (PI)** | Módulo integrador. En GS tiene parte en 1.º (código con «p») y en 2.º | `tipo: proyecto` |
| **Optativo** | Módulo de 3 h en 2.º (CVOPM… en GM, CVOPS… en GS) que elige el centro | `tipo: optativo` |
| **RA** | Resultado de aprendizaje: prescriptivo, del anexo I del RD del título | `ra` (numerados 1…n) |
| **CE** | Criterio de evaluación de un RA | `criterios` |
| **Competencias** | Competencias profesionales, personales y sociales del título (art. 5, letras a)…). La **competencia general** es la del art. 4 | `competencias` |
| **UC · ECP** | Unidad de competencia (antigua) · Estándar de competencia profesional (RD 532/2025: mismo código) | `ecp` |
| **Anexo V B** | Anexo del RD del título con la correspondencia entre módulos y UC/ECP | `correspondencias_ecp` |
| **FE** | Formación en empresa (antes FCT/dual). Desarrolla parte de los RA del módulo; jornada de 7 u 8 h | `empresa` |
| **Unidad** | Unidad didáctica (UD00, UD01…), práctica u otra actividad con horas y trimestre | `unidades` |
| **Elemento de evaluación** | Lo que se califica: examen (E), práctica (P) o trabajo (T). Agrupa unidades y tiene sus RA | `elementos` |
| **Peso** | % del módulo de un elemento = sus horas / horas del módulo | `calculos.peso` |
| **Tabla 4 · 4.1** | Secuenciación de unidades · ponderación de cada RA (horas totales, modalidad y empresa) | `calculos.tabla41` |
| **Ajuste de centro** | Horas de centro de un RA que fija el profesor en vez de la propuesta (dentro de sus límites) | `centro_ajustado` |
| **Modalidad del RA** | Centro · Mixto · Empresa, según dónde se trabajan sus horas | `modalidad` |
| **Bloque** | Grupo de datos manuales que el profesor confirma de una vez | `bloques` |
| **Heredado** | Bloque copiado de una programación anterior que el profesor aún no ha confirmado | `"heredado"` |
| **Catálogo** | Datos oficiales de ciclos, módulos, RA, normativa y curso escolar que trae la app | `catalogo` |
| **Vigía** | Flujo programado de GitHub que comprueba las fuentes oficiales y propone cambios del catálogo | `vigia.yml` |
| **Plantilla** | La programación de referencia (PIICT, 0517, desde el 2026-10-06) con marcas, desempaquetada | `recursos/plantilla/`, `scripts/plantilla.py` |
| **Marca** | Hueco de la plantilla que rellena la app: `{{nombre}}`, `{{*lista}}`, `{{@lista.campo}}`, `{{#grupo}}`, `{{?condición}}` | `documento.Motor` |
| **Texto propio** | Párrafos del profesor que sustituyen un bloque fijo de la plantilla (calificación, instrumentos, elementos de evaluación…) | `textos_propios` |
| **Errata corregida** | Texto del BOE con un error que el catálogo guarda literal y, aparte, corregido; el corregido va al documento | `corregido`, `CORRECCIONES` |
| **Regeneración** | Rehacer una programación de referencia desde sus datos y compararla con su `.docx` | `scripts/regenerar.py`, `contenido.comparar` |
| **Datos incrustados** | Copia de la programación dentro del `.docx` exportado (customXml), con sus huellas | `incrustar.py` |
| **Curso escolar** | 2026-2027… Fechas de evaluación, resolución de instrucciones y periodos de FE | `curso_escolar` |
| **PCCF** | Proyecto curricular del ciclo formativo (art. 8 del Decreto 114/2025): enmarca las programaciones | — |
| **SAÓ · Educamos** | Plataforma de la Conselleria (registro diario y FE) · plataforma del centro con las familias | — |
| **BOE · DOGV** | Boletín Oficial del Estado · Diari Oficial de la Generalitat Valenciana | — |
