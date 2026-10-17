# Hoja de ruta

Fases sin fechas: no hay datos para fijarlas. Cada fase se cierra con su criterio. Los datos que faltan están en [PENDIENTE.md](PENDIENTE.md).

| Fase | Qué | Criterio de cierre |
| --- | --- | --- |
| **F0 · Documentación** | PRD, TRD, diseño, ADR, modelo de datos, documento generado, fuentes, pruebas, operaciones | Revisada por CarlosFB (2026-10-14: primera versión) |
| **F1 · Catálogo** · **cerrada el 2026-10-17** | `scripts/catalogo.py` (a partir de `curriculo.py`), esquemas, 11 ciclos con módulos y horas, SEA, STI y ARI completos y después el resto. Hecho: los 11 ciclos con las horas del Decreto 95/2026 y los RA de todos los módulos propios, comunes y optativos ofertados. Pendiente de CarlosFB: el Proyecto intermodular de GM, los optativos de GM y de las otras familias (las dudas de ADR-017, resueltas en ADR-018) | `catalogo.py comprobar` limpio. RA de las seis programaciones de referencia idénticos a los del catálogo (cumplido: los criterios coinciden salvo cuatro erratas del BOE que corrigen 0517 y 0524) |
| **F2 · Motor del documento** · **cerrada el 2026-10-17, salvo la prueba de Word (R1)** | Plantilla con marcas a partir de PIICT (con la variante de los proyectos de 0526), `calculos.py`, `validacion.py`, `documento.py`, `incrustar.py`, `pdf.py`, `importar_docx.py` y el lector del catálogo (`catalogo.py`), con `scripts/regenerar.py` y la prueba `-m referencias`. Las seis se regeneran sin diferencias de contenido salvo las esperadas por decisión de CarlosFB (ADR-018), documentadas una a una en la prueba. R1 probado con LibreOffice. **Falta solo** la prueba manual en Word de macOS y Windows ([PENDIENTE.md](PENDIENTE.md)) | Las seis programaciones regeneradas sin diferencias de contenido. **Prueba de Word con la parte incrustada (R1)** |
| **F3 · Maqueta** · **cerrada el 2026-10-17** | Maqueta interactiva de todas las pantallas con el diseño de Partes de salida. **v0 hecha el 2026-10-14:** `../Maqueta v0 (2026-10-14)/` en la bóveda (23 pantallas). **Aprobada «tal cual» por CarlosFB el 2026-10-17** | Aprobada por CarlosFB |
| **F4 · App** · **cerrada el 2026-10-17 con la 0.1.0** (aprobada entera el 2026-10-17) | Dos tandas. **Tanda 1, base y empaquetado:** arranque con instancia única y prueba de arranque, contexto, `ui/estilo.py`, componentes, presentación, actualizaciones y novedades, registro, Ajustes y ventana principal; spec, instalador de Windows y portable, DMG arm64 y `compilar.yml` (datos empaquetados, QtPdf y prueba de arranque en macOS y Windows); ganchos, reglas, skills y agentes. **Tanda 2, las pantallas de la maqueta:** módulos con filtros, ficha con «DEL CURRÍCULO», los cinco bloques del profesor, estado con avisos V-xx, vista previa, exportar (`exportacion.py`), abrir un Word exportado, «Nueva a partir de…» (`herencia.py`), cambios de currículo, listado «Programaciones», archivo de trabajo con autoguardado (`almacen.py`) y primer arranque. Quedan como «pendiente»: el envío por correo (ADR-014) y el catálogo remoto (F5) | Flujo completo en pytest-qt (cumplido). Primer release con instaladores (0.1.0, pre-release a falta del piloto F6). **0.1.1** (2026-10-17): fechas del curso 2026-2027 (ADR-023); la definitiva ya se exporta, salvo 2.º de GA |
| **F5 · Vigía y catálogo remoto** | `vigia.yml`, `catalogo.yml`, firma y descarga en la app con la ventana de novedades | Un cambio simulado en una norma se publica solo y el profesor lo acepta en la app |
| **F6 · Piloto** | Departamento de Electricidad y Electrónica: 2-3 profesores, una herencia real | Sin bloqueos y con el tiempo de la meta del PRD |
| **F7 · Todo FP** | Resto de familias (ADM, GA, ISO, AUT, CAR, EMV) | Una programación exportada por familia |
| **F8 · Grado Básico** | Cuando haya programación modelo | — |
| **F9 · Excel de RA** | Ver «Función futura: Excel de RA» | Cuando CarlosFB dé las indicaciones |
| **F10 · Valenciano e inglés** | Ver «Función futura: documento en valenciano e inglés» | Una programación de referencia exportada en cada idioma y revisada |

## Función futura: documento en valenciano e inglés

**Estado:** le gusta a CarlosFB (2026-10-14). Sin definir. **No se implementa hasta decidir lo pendiente.**

**Alcance:** **solo el documento final** (Word y PDF). La interfaz de la app sigue siempre en castellano (CarlosFB, 2026-10-14). En la app, el idioma es una opción más al exportar: un chip «Castellano · Valencià · English» junto a «Word» y «PDF».

**Lo que ya se deja preparado desde la 1.0 (ADR-013):**
- **Catálogo:** guarda cada texto oficial por idioma (`texto: {es: …}`), aunque al principio solo tenga `es`.
- **Plantilla:** lleva la versión del idioma (`plantilla/es/…`).
- **Nombres del código:** independientes del idioma.

**Tres fuentes de texto, tres problemas distintos:**

| Texto | Valenciano | Inglés |
| --- | --- | --- |
| Datos oficiales (RA, criterios, competencias, normas) | El DOGV publica el Decreto 114/2025 también en valenciano. Para los RA de cada RD hay que buscar si existe texto oficial | No hay texto oficial: traducción revisada |
| Textos fijos de la plantilla | Traducción una sola vez, revisada por el centro | Traducción una sola vez, revisada |
| Datos manuales del profesor | ¿Los escribe en cada idioma, o la app propone una traducción que él revisa? | Igual |

**Por decidir** (en [PENDIENTE.md](PENDIENTE.md)):
- Si se exporta un idioma cada vez o varios a la vez.
- Cómo se llama el archivo de cada idioma.
- Quién revisa las traducciones de la plantilla.
- Si se usa IA para proponer la traducción de los textos del profesor.

## Función futura: Excel de RA

**Estado:** decidida, pero todavía sin definir (CarlosFB, 2026-10-14). Las indicaciones llegarán más tarde. **No se implementa nada hasta tenerlas.**

- **Qué será:** la app creará también el Excel de RA que hoy acompaña a cada programación en su carpeta `01 Programación`. Por ejemplo, `SEA 2 - 0517 - Procesos en instalaciones de infraestructuras comunes de telecomunicaciones.xlsx` junto a su `.docx`.
- **Nombre:** el mismo que la programación (ver [DOCUMENTO_GENERADO.md](DOCUMENTO_GENERADO.md#nombre-de-los-archivos)).
- **Formato:** tendrá algunas variaciones respecto al Excel actual, que se concretarán con las indicaciones.
- **Lo que ya se sabe:** el Excel sirve para comprobar la tabla 4.1 (por RA, si va a empresa y sus horas: skill `programacion-didactica`). La plantilla de evaluación por RA-CE de la bóveda está en `05 RECURSOS/PLANTILLAS/Evaluación por RA-CE (excel)/`. Los datos que necesita (RA, criterios, unidades, elementos, horas y empresa por RA) ya están en el modelo de la app, así que no hace falta pedir nada nuevo al profesor.
- **Preparación:** `openpyxl` ya se usa en Partes de salida. El módulo previsto es `excel_ra.py` en el dominio.

## Funcionalidades futuras aceptadas

Propuestas del 2026-10-14. CarlosFB acepta P-01 a P-05 y descarta P-06 a P-12 (2026-10-14). Ninguna se implementa sin los datos que necesita.

| ID | Propuesta | Qué resuelve | Datos que necesita | Esfuerzo |
| --- | --- | --- | --- | --- |
| P-01 | **Sesiones reales por trimestre.** Con los días de clase del módulo y el calendario escolar (festivos, Fallas, Pascua, periodos de FE), la app cuenta las sesiones disponibles en cada trimestre y avisa si las unidades no caben | Temporalizaciones imposibles que se descubren en marzo | Días y horas de clase del módulo (manual: 2-3 casillas) · calendario del curso (ya en `cursos/`) | Medio |
| P-02 | **Fechas de cada unidad y calendario `.ics`.** A partir de P-01, la fecha prevista de inicio y fin de cada unidad y de cada examen, exportable al calendario de Outlook o Teams | Planificación del curso en un clic | P-01 | Bajo tras P-01 |
| P-03 | **Panel del departamento sin servidor.** La app lee los `.docx` de la carpeta de Teams del curso (llevan los datos dentro) y muestra qué módulos de cada ciclo tienen programación, cuáles faltan y con qué versión del catálogo | Recupera el seguimiento central que se perdió al descartar la web | Acceso de lectura a la carpeta de Teams sincronizada | Medio |
| P-04 | **Comprobaciones del ciclo** (sobre P-03). La FE de todo el ciclo está entre el 25 y el 35 % de su duración y cubre al menos el 10 % de los RA (Decreto 114/2025, art. 7). Además, todas las competencias del título están cubiertas por algún RA de algún módulo | Lo que exige el decreto al ciclo, no al módulo, y nadie suma a mano | P-03 | Bajo tras P-03 |
| P-05 | **Seguimiento y memoria final.** Durante el curso, el profesor marca las horas impartidas y las sesiones perdidas (suspensiones, sustituciones), y la app genera el informe de desviación para la evaluación de la programación y de la práctica docente (Decreto 114/2025, art. 9) | La memoria de final de curso, hecha con los datos de la programación | Horas impartidas (manual) | Medio |

**Descartadas** (CarlosFB, 2026-10-14):
- P-06 · Comparar con el curso anterior
- P-07 · Unidades desde los apuntes web
- P-08 · Rúbricas y fichas de práctica
- P-09 · Programación de aula
- P-10 · Nota gemela para la bóveda
- P-11 · PDF accesible
- P-12 · Ayuda a redactar (IA, opcional)

## Riesgos

| ID | Riesgo | Impacto | Medida |
| --- | --- | --- | --- |
| R1 | Word no conserva la parte XML personalizada al guardar | Alto: se pierde la recuperación desde Teams | Con LibreOffice, probado: la conserva con las huellas (prueba automática, también en la CI). Con Word de macOS y de Windows, prueba manual con `scripts/prueba_word.py` ([PENDIENTE.md](PENDIENTE.md)). Plan B: guardar el JSON también como adjunto del PDF y como `.programacion` junto al `.docx` en la carpeta de entrega |
| R2 | Los anexos del DOGV solo están en PDF y cambian de maquetación | Medio | Extracción asistida y revisión humana en la PR del vigía. Huella del PDF para detectar cambios |
| R3 | Equipos sin Word ni LibreOffice | Medio | Exportar solo en Word y avisar. Versión portable de LibreOffice como opción documentada |
| R4 | Equipos del centro que no dejan instalar | Medio | Versión portable de Windows (como Partes de salida) |
| R5 | El departamento cambia la plantilla durante el curso | Medio | Versionado de la plantilla y regeneración de las referencias |
| R6 | Límite de la API de GitHub (60 consultas por hora y por IP, y todo el centro sale por la misma) | Bajo | Plan B por la web (ya en Partes de salida) y catálogo por `raw.githubusercontent.com` |
| R7 | Un RA mal extraído llega a los profesores | Alto | Comprobaciones automáticas antes de publicar, prueba de regeneración y aprobación de cada profesor viendo la diferencia (ADR-015) |
