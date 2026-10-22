# Pendiente

Única lista de lo que falta. Lo más reciente arriba en cada tabla.

## Datos que faltan (los aporta CarlosFB)

| Desde | Qué | Para qué |
| --- | --- | --- |
| 2026-10-14 | Optativos que ofrece el centro en GS de otras familias (ISO): **los dará CarlosFB**. Ya en el catálogo: SEA, STI y ARI (0179, CVOPS031 y CVOPS141), ADM (solo el 0179) y AUT (0179 y CVOPS192 Peritación) (CarlosFB, 2026-10-21) y GM (IT, IEA, GA, CAR y EMV: ANEXO X-I, Inglés oral para entornos profesionales, 2.º; CarlosFB, 2026-10-18) | Apartado 2.2 |

## Por comprobar (sin preguntar a nadie)

| Desde | Qué |
| --- | --- |
| 2026-10-22 | Dadas por buenas por CarlosFB: la prueba de Word (R1) en Windows y sus revisiones de contenido (textos fijos de la plantilla de ámbitos, dudas del catálogo de GB y propuestas de IA de las competencias por RA). Dada la FE de 2.º de GA (como 2.º de GM y GS) |
| 2026-10-20 | Dadas por hechas por CarlosFB: la versión de Linux en un equipo real, la actualización en su sitio en un Mac, la primera PR del vigía, el correo con Mail y Outlook, la tipografía de la tabla 4 en Word y las pantallas reales de la app |
| 2026-10-17 | **Contenidos básicos sin leer por bloques** (ADR-031: sin propuesta de unidades en una programación nueva): 0239, 0240, 0254, 0257, 0258, 0292 y 0439 (BOE de 2008 con el texto pegado), 1709, 1710 y los optativos (DOGV sin numerar), 1665 y 1708 (bloques sin título propio). Mejorar el lector si aparece una regla segura |
| 2026-10-17 | **`hdiutil attach` está obsoleto en macOS 27** (avisa de usar `diskutil image attach`), aunque sigue funcionando: la actualización en su sitio (ADR-029) lo usa para montar el DMG. Si una versión de macOS lo quita, la app pasa sola a la reserva (abre el DMG); entonces, cambiarlo por `diskutil image attach` |

Comprobado el 2026-10-17: PyQt6 6.7 trae `QtPdf` en macOS y Windows (lo abre la prueba de arranque de `compilar.yml` en la app compilada). El 2026-10-19: también en Linux, con la app compilada en la CI (ADR-034).

## Aparcado (no se pregunta hasta que CarlosFB lo retome)

| Desde | Qué | Para qué |
| --- | --- | --- |
| 2026-10-14 | **Documento en valenciano e inglés:** ¿un idioma o varios a la vez?, nombre del archivo de cada idioma, quién revisa las traducciones de la plantilla y cómo se traducen los textos del profesor | Fase F10 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-documento-en-valenciano-e-inglés)) |

## Repositorio

Nada abierto: desde el 2026-10-17 están copiados y adaptados de Partes de salida los ganchos, las plantillas de `.github/`, el `Makefile` y `scripts/qa.sh`.
