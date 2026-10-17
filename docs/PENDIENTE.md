# Pendiente

Única lista de lo que falta. Lo más reciente arriba en cada tabla.

## Datos que faltan (los aporta CarlosFB)

| Desde | Qué | Para qué |
| --- | --- | --- |
| 2026-10-17 | **Formación en empresa de 2.º de GA** en 2026-2027: la propuesta del centro solo da la de 1.º de GA (febrero). Hasta tenerla, el documento de 2.º de GA la enseña como «pendiente» y no deja exportar la definitiva (V-11) | `cursos/2026-2027.yaml` (ADR-023) |
| 2026-10-17 | Capturas de Teams para la ayuda «Añadir la carpeta de Teams a OneDrive» (los tres pasos): hoy la ayuda va solo con texto | Ayuda de la carpeta de entrega |
| 2026-10-17 | **Prueba de Word con los datos incrustados (R1), en macOS y en Windows.** Con LibreOffice ya está probado (automático, también en la CI). Pasos: (1) `~/.venvs/programaciones/bin/python scripts/prueba_word.py preparar ~/Desktop` deja «Prueba R1 - ficticia.docx» (datos inventados); (2) abrirlo en Word, aceptar la actualización de campos si la pide, escribir una palabra al final, guardar (Cmd/Ctrl+S) y cerrar; con otra copia, «Guardar como…» .docx; (3) `scripts/prueba_word.py comprobar <archivo guardado>…`. Esperado: «datos: sí» y «texto: cambiado en Word». En Windows, copiar el archivo a un equipo con Word y traer de vuelta el guardado | Lo único que falta para cerrar F2 (riesgo R1) |
| 2026-10-14 | **Envío por correo:** mecanismo (A borrador en Outlook o Mail, B buzón de las apps, C cuenta del profesor), destinatarios habituales (¿jefatura, jefe de departamento?) y tamaño máximo de adjuntos | ADR-014 |
| 2026-10-14 | **Documento en valenciano e inglés:** ¿un idioma o varios a la vez?, nombre del archivo de cada idioma, quién revisa las traducciones de la plantilla y cómo se traducen los textos del profesor | Fase F10 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-documento-en-valenciano-e-inglés)) |
| 2026-10-14 | Indicaciones del **Excel de RA** que generará la app: qué cambia respecto al Excel actual | Fase F9 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-excel-de-ra)) |
| 2026-10-14 | Optativos que ofrece el centro en GM (IT, IEA, GA, CAR, EMV) y en GS de otras familias (ADM, ISO, AUT): **los dará CarlosFB**. SEA, STI y ARI: 0179, CVOPS031 y CVOPS141, ya en el catálogo | Apartado 2.2 |
| 2026-10-14 | Fuente de los RA del Proyecto intermodular de GM (`1713xxx` en el decreto). En el catálogo, con `pendiente` en GA, IT, IEA, CAR y EMV | Catálogo |
| 2026-10-14 | ¿Quién da de alta cada curso escolar (fechas, resolución, FE)? Propuesta: CarlosFB, en julio, con la incidencia del vigía | Operaciones |
| 2026-10-14 | Programación modelo de Grado Básico | Fase F8 |

## Por comprobar (sin preguntar a nadie)

| Desde | Qué |
| --- | --- |
| 2026-10-17 | Las pantallas de la 0.1.0 en un Mac y un Windows reales (con pantalla, ratón y Word): se prueban sin pantalla con pytest-qt y la app compilada arranca en la CI, pero arrastrar filas, los menús y la conversión con Word solo se ven a mano. Va con el piloto (F6) |
| 2026-10-17 | «Cambios en el currículo» compara con el catálogo con el que se hizo la programación: hasta F5 la app solo tiene el que lleva dentro, así que con la 0.1.0 la ventana no saldrá en la práctica (probada con un catálogo anterior ficticio) |

Comprobado el 2026-10-17: PyQt6 6.7 trae `QtPdf` en macOS y Windows (lo abre la prueba de arranque de `compilar.yml` en la app compilada).

## Repositorio

Nada abierto: desde el 2026-10-17 están copiados y adaptados de Partes de salida los ganchos, las plantillas de `.github/`, el `Makefile` y `scripts/qa.sh`.
