# Pendiente

Única lista de lo que falta. Lo más reciente arriba en cada tabla.

## Datos que faltan (los aporta CarlosFB)

| Desde | Qué | Para qué |
| --- | --- | --- |
| 2026-10-17 | **Formación en empresa de 2.º de GA** en 2026-2027: la propuesta del centro solo da la de 1.º de GA (febrero). Hasta tenerla, el documento de 2.º de GA la enseña como «pendiente» y no deja exportar la definitiva (V-11) | `cursos/2026-2027.yaml` (ADR-023) |
| 2026-10-17 | Capturas de Teams para la ayuda «Añadir la carpeta de Teams a OneDrive» (los tres pasos): hoy la ayuda va solo con texto | Ayuda de la carpeta de entrega |
| 2026-10-17 | **Prueba de Word con los datos incrustados (R1), en macOS y en Windows.** Con LibreOffice ya está probado (automático, también en la CI). Pasos: (1) `~/.venvs/programaciones/bin/python scripts/prueba_word.py preparar ~/Desktop` deja «Prueba R1 - ficticia.docx» (datos inventados); (2) abrirlo en Word, aceptar la actualización de campos si la pide, escribir una palabra al final, guardar (Cmd/Ctrl+S) y cerrar; con otra copia, «Guardar como…» .docx; (3) `scripts/prueba_word.py comprobar <archivo guardado>…`. Esperado: «datos: sí» y «texto: cambiado en Word». En Windows, copiar el archivo a un equipo con Word y traer de vuelta el guardado | Lo único que falta para cerrar F2 (riesgo R1) |
| 2026-10-14 | **Documento en valenciano e inglés:** ¿un idioma o varios a la vez?, nombre del archivo de cada idioma, quién revisa las traducciones de la plantilla y cómo se traducen los textos del profesor | Fase F10 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-documento-en-valenciano-e-inglés)) |
| 2026-10-14 | Indicaciones del **Excel de RA** que generará la app: qué cambia respecto al Excel actual | Fase F9 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-excel-de-ra)) |
| 2026-10-14 | Optativos que ofrece el centro en GM (IT, IEA, GA, CAR, EMV) y en GS de otras familias (ADM, ISO, AUT): **los dará CarlosFB**. SEA, STI y ARI: 0179, CVOPS031 y CVOPS141, ya en el catálogo | Apartado 2.2 |
| 2026-10-14 | Fuente de los RA del Proyecto intermodular de GM (`1713xxx` en el decreto). En el catálogo, con `pendiente` en GA, IT, IEA, CAR y EMV | Catálogo |
| 2026-10-14 | ¿Quién da de alta cada curso escolar (fechas, resolución, FE)? Propuesta: CarlosFB, en julio, con la incidencia del vigía | Operaciones |
| 2026-10-14 | Programación modelo de Grado Básico | Fase F8 |

## Por comprobar (sin preguntar a nadie)

| Desde | Qué |
| --- | --- |
| 2026-10-17 | **Propuesta de IA de las competencias de cada RA** (ADR-031): revisarla por familias (CarlosFB) y rehacer la de los módulos cuyos RA cambie el vigía. Dudas de la primera pasada: EMV 0452 RA6 (sin la h de PRL entre las del módulo), EMV 0260 (solo la a), AUT 0294 RA1-2 y AUT 0291 RA6 |
| 2026-10-17 | **Contenidos básicos sin leer por bloques** (ADR-031: sin propuesta de unidades en una programación nueva): 0239, 0240, 0254, 0257, 0258, 0292 y 0439 (BOE de 2008 con el texto pegado), 1709, 1710 y los optativos (DOGV sin numerar), 1665 y 1708 (bloques sin título propio). Mejorar el lector si aparece una regla segura |
| 2026-10-17 | **Actualización en su sitio en un Mac real** (ADR-029): solo funciona desde la 0.3.0, así que se verá al publicar la siguiente versión. Con la 0.3.0 instalada en `/Applications/EPLA/`, «Actualizar ahora» tiene que cerrar la app, dejar la nueva en `/Applications/EPLA/` (sin copia en `/Applications`) y abrirla; el registro queda en `logs/actualizacion_*.log`. Probar también un usuario sin permiso de escritura en esa carpeta (sale el DMG con la carpeta a la que arrastrarla) |
| 2026-10-17 | **`hdiutil attach` está obsoleto en macOS 27** (avisa de usar `diskutil image attach`), aunque sigue funcionando: la actualización en su sitio (ADR-029) lo usa para montar el DMG. Si una versión de macOS lo quita, la app pasa sola a la reserva (abre el DMG); entonces, cambiarlo por `diskutil image attach` |
| 2026-10-17 | **Primera PR real del vigía:** revisar que la lista «Revisar a mano» y las diferencias se entienden, y seguir los pasos de `docs/OPERACIONES.md`. Hasta que haya una, el recorrido está probado con fuentes falsas y con el simulacro |
| 2026-10-17 | **Enviar por correo con un programa de correo de verdad** (ADR-014): en las pruebas el programa se simula. Probar a mano en un Mac con **Mail** y con **Outlook** (el nuevo Outlook de Mac tiene un AppleScript limitado: si falla, la app abre la carpeta y un correo nuevo) y en un Windows con **Outlook clásico** (COM) y sin él (`.eml`). Esperado: un correo nuevo con los destinatarios, el asunto, el cuerpo y los adjuntos, sin enviar |
| 2026-10-17 | **Tipografía en Word:** la tabla 4 ya no puede caer en Times New Roman (lo comprueba una prueba que resuelve la fuente de cada texto, también la ranura asiática con la que Word dibuja «→», y el PDF de LibreOffice sale sin ella); falta verlo en Word en macOS y en Windows con una programación exportada con la 0.2.0. Va con la prueba de Word (R1) |
| 2026-10-17 | Las pantallas de la 0.1.0 en un Mac y un Windows reales (con pantalla, ratón y Word): se prueban sin pantalla con pytest-qt y la app compilada arranca en la CI, pero arrastrar filas, los menús y la conversión con Word solo se ven a mano. Va con el piloto (F6) |

Comprobado el 2026-10-17: PyQt6 6.7 trae `QtPdf` en macOS y Windows (lo abre la prueba de arranque de `compilar.yml` en la app compilada).

## Repositorio

Nada abierto: desde el 2026-10-17 están copiados y adaptados de Partes de salida los ganchos, `.claude/` (reglas, skills y agentes), las plantillas de `.github/`, el `Makefile` y `scripts/qa.sh`.
