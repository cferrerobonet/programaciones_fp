# Programaciones

App de escritorio (macOS y Windows) para que el profesorado de FP de EPLA (grado medio y superior) genere en Word y PDF la **programación didáctica** de un módulo con la plantilla del centro.

La app ya conoce los datos oficiales de cada módulo (RA, criterios, competencias, normativa, horas) y los mantiene al día sola desde el BOE y el DOGV. Al profesor solo le pregunta lo que únicamente sabe él: unidades, horas, evaluación, metodología y recursos.

> **Estado:** en desarrollo. Documentación inicial del 2026-10-14, catálogo curricular (fase F1, 2026-10-17) y motor del documento (fase F2, cerrada el 2026-10-17 salvo la prueba en Word: plantilla, cálculos, validaciones, importación, datos incrustados y PDF). Todavía no hay app (interfaz).
> Repositorio **público**: [github.com/cferrerobonet/programaciones_fp](https://github.com/cferrerobonet/programaciones_fp). Nunca lleva datos personales ni contraseñas.

## Cómo se usa (previsto)

1. Elegir el módulo: ciclo, curso y código.
2. Revisar los datos del currículo, que la app ya trae.
3. Rellenar los bloques del profesor, o heredarlos de la programación del curso anterior y confirmarlos.
4. Vista previa (PDF con marca «BORRADOR») y exportar la definitiva en Word y PDF.
5. Subir el archivo exportado a la carpeta de Teams del curso. El archivo lleva dentro todos los datos: con él se recupera o se hereda la programación otro año.

## Documentación

| Documento | Para qué |
| --- | --- |
| [PRD.md](PRD.md) | Qué problema resuelve, para quién, alcance y requisitos |
| [TRD.md](TRD.md) | Cómo se construye: stack, arquitectura, requisitos técnicos |
| [DESIGN.md](DESIGN.md) | Cómo se ve: diseño idéntico a Partes de salida |
| [docs/README.md](docs/README.md) | Mapa del resto de documentos |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo se trabaja en el repositorio |
| [CHANGELOG.md](CHANGELOG.md) | Cambios por versión |

Ficha en la bóveda: `../PROGRAMACIONES — Índice.md`.
