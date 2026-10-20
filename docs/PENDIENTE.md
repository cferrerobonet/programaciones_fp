# Pendiente

Única lista de lo que falta. Lo más reciente arriba en cada tabla.

## Datos que faltan (los aporta CarlosFB)

| Desde | Qué | Para qué |
| --- | --- | --- |
| 2026-10-17 | **Formación en empresa de 2.º de GA** en 2026-2027: la propuesta del centro solo da la de 1.º de GA (febrero). Hasta tenerla, el documento de 2.º de GA la enseña como «pendiente» y no deja exportar la definitiva (V-11) | `cursos/2026-2027.yaml` (ADR-023) |
| 2026-10-17 | **Prueba de Word con los datos incrustados (R1), en Windows.** Con LibreOffice y ONLYOFFICE ya está probado (automático); con Word de macOS, el 2026-10-19 (Guardar y Guardar como…: «datos: sí»). Pasos: (1) `~/.venvs/programaciones/bin/python scripts/prueba_word.py preparar ~/Desktop` deja «Prueba R1 - ficticia.docx» (datos inventados); (2) abrirlo en Word, aceptar la actualización de campos si la pide, escribir una palabra al final, guardar (Cmd/Ctrl+S) y cerrar; con otra copia, «Guardar como…» .docx; (3) `scripts/prueba_word.py comprobar <archivo guardado>…`. Esperado: «datos: sí» y «texto: cambiado en Word». En Windows, copiar el archivo a un equipo con Word y traer de vuelta el guardado | Lo único que falta para cerrar F2 (riesgo R1), solo en Windows |
| 2026-10-14 | Optativos que ofrece el centro en GS de otras familias (ADM, ISO, AUT): **los dará CarlosFB**. Ya en el catálogo: SEA, STI y ARI (0179, CVOPS031 y CVOPS141) y GM (IT, IEA, GA, CAR y EMV: ANEXO X-I, Inglés oral para entornos profesionales, 2.º; CarlosFB, 2026-10-18) | Apartado 2.2 |

## Por comprobar (sin preguntar a nadie)

| Desde | Qué |
| --- | --- |
| 2026-10-20 | Dadas por hechas por CarlosFB: la versión de Linux en un equipo real, la actualización en su sitio en un Mac, la primera PR del vigía, el correo con Mail y Outlook, la tipografía de la tabla 4 en Word y las pantallas reales de la app |
| 2026-10-17 | **Textos fijos de la plantilla de ámbitos** (ADR-032): revisar los apartados 2, 3, 3.1, 8, 10 y 11, sacados del modelo común y corregidos («al menos Suficiente», «apartado 3.1», sin la CE6 del modelo como desempeño, criterios del apartado 2) (Ciencias Aplicadas ya propone Matemáticas y Ciencias: ADR-039) |
| 2026-10-17 | **Dudas del catálogo de GB:** 3013 (EE) no tiene la competencia g) entre las de sus orientaciones aunque su RA5 es de mantenimiento, ni 3046 (MV) la c) (carga y arranque): así lo dice el RD 127/2014. 3043 se llama «Mecanizado y soldadura» en el RD y «Mecanización y soldadura» en el decreto (va el del decreto, ADR-018). Errata del RD 217/2022: el descriptor «CL3» (por CCL3) de la CE4 de Comunicación y Ciencias Sociales, guardado literal y corregido en el documento (`catalogo.ERRATAS_DESCRIPTORES`; CarlosFB, 2026-10-19). Las competencias de 3013 y 3046 se quedan como dice el RD 127/2014 (CarlosFB, 2026-10-19): el profesor puede añadirlas en su tabla. Contenidos sin leer por bloques: 3013, 3043 y 3159 |
| 2026-10-17 | **Propuesta de IA de competencias por RA de GB** (ADR-031): revisarla; dudas en 3013, 3046, 3015-IC (h), 3029 (f, g) y 3006 (p), y la v) (derechos) en los técnicos |
| 2026-10-17 | **Propuesta de IA de las competencias de cada RA** (ADR-031): revisarla por familias (CarlosFB) y rehacer la de los módulos cuyos RA cambie el vigía. Dudas de la primera pasada: EMV 0452 RA6 (sin la h de PRL entre las del módulo), EMV 0260 (solo la a), AUT 0294 RA1-2 y AUT 0291 RA6 |
| 2026-10-17 | **Contenidos básicos sin leer por bloques** (ADR-031: sin propuesta de unidades en una programación nueva): 0239, 0240, 0254, 0257, 0258, 0292 y 0439 (BOE de 2008 con el texto pegado), 1709, 1710 y los optativos (DOGV sin numerar), 1665 y 1708 (bloques sin título propio). Mejorar el lector si aparece una regla segura |
| 2026-10-17 | **`hdiutil attach` está obsoleto en macOS 27** (avisa de usar `diskutil image attach`), aunque sigue funcionando: la actualización en su sitio (ADR-029) lo usa para montar el DMG. Si una versión de macOS lo quita, la app pasa sola a la reserva (abre el DMG); entonces, cambiarlo por `diskutil image attach` |

Comprobado el 2026-10-17: PyQt6 6.7 trae `QtPdf` en macOS y Windows (lo abre la prueba de arranque de `compilar.yml` en la app compilada). El 2026-10-19: también en Linux, con la app compilada en la CI (ADR-034).

## Aparcado (no se pregunta hasta que CarlosFB lo retome)

| Desde | Qué | Para qué |
| --- | --- | --- |
| 2026-10-14 | **Documento en valenciano e inglés:** ¿un idioma o varios a la vez?, nombre del archivo de cada idioma, quién revisa las traducciones de la plantilla y cómo se traducen los textos del profesor | Fase F10 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-documento-en-valenciano-e-inglés)) |

## Repositorio

Nada abierto: desde el 2026-10-17 están copiados y adaptados de Partes de salida los ganchos, las plantillas de `.github/`, el `Makefile` y `scripts/qa.sh`.
