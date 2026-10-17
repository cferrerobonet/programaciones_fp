# Pendiente

Única lista de lo que falta. Lo más reciente arriba en cada tabla.

## Datos que faltan (los aporta CarlosFB)

| Desde | Qué | Para qué |
| --- | --- | --- |
| 2026-10-17 | **Prueba de Word con los datos incrustados (R1), en macOS y en Windows.** Con LibreOffice ya está probado (automático, también en la CI). Pasos: (1) `~/.venvs/programaciones/bin/python scripts/prueba_word.py preparar ~/Desktop` deja «Prueba R1 - ficticia.docx» (datos inventados); (2) abrirlo en Word, aceptar la actualización de campos si la pide, escribir una palabra al final, guardar (Cmd/Ctrl+S) y cerrar; con otra copia, «Guardar como…» .docx; (3) `scripts/prueba_word.py comprobar <archivo guardado>…`. Esperado: «datos: sí» y «texto: cambiado en Word». En Windows, copiar el archivo a un equipo con Word y traer de vuelta el guardado | Cierre de F2 (riesgo R1) |
| 2026-10-17 | **Formación en empresa de 1.º** (0524, 0525, 0962 y 0963): la app usa la redacción y el orden de la plantilla («Alumnos que realicen 8h/día (en total 20 días de formación): desde el 3 de mayo…», 8 h primero); esas cuatro programaciones usan otra («(N días de formación, M h aprox.): del …», con las horas aproximadas) y ponen primero las 7 h. ¿Cuál va? | Cierre de F2, apartado 9.1 |
| 2026-10-17 | **Fila «HORAS CENTRO» de la tabla 4:** en PIICT, 0525 y 0962, la celda de RA va vacía (la app lo hace así); 0524 y 0963 listan los RA de centro («RA1 → RA7»). ¿Vacía o con los RA? | Cierre de F2, apartado 4 |
| 2026-10-17 | **Apartado 2, párrafo del anexo V B):** la app usa una redacción por caso (la de PIICT si el anexo lo reescribe otra norma, la de 0963 en ARI y «cuya redacción no ha sido modificada por el Real Decreto 500/2024» en STI). 0962 dice «en su redacción vigente» y 0525 añade «, con la denominación que les da el Real Decreto 532/2025». ¿Vale la de la app? | Cierre de F2, apartado 2 |
| 2026-10-17 | **Cabecera «RA asociados» de la tabla 4:** la app cita el real decreto entre paréntesis, como PIICT; 0525 y 0962 no lo citan | Cierre de F2, apartado 4 |
| 2026-10-17 | **Resolución de instrucciones del curso (1.2):** la app pone el título oficial del DOGV («… de Formación Profesional … en la Comunitat Valenciana»); la plantilla decía «Formación profesional» y «Comunidad Valenciana». ¿Vale el oficial? | Cierre de F2, apartado 1.2 |
| 2026-10-17 | **Pesos de 0962 y 0963:** la app calcula el peso de cada elemento (horas del elemento / horas del módulo, regla de la plantilla). 0962 tiene pesos puestos a mano que no salen de sus horas y una columna «% del curso (aprox.)» en la tabla 4.1; 0963 da el peso de cada práctica de un bloque («… % / x práctica»). ¿Se corrigen las programaciones o la app admite peso por práctica (y cómo)? | Cierre de F2, apartados 4 y 4.1 |
| 2026-10-17 | **Proyecto intermodular (0526):** sus textos de calificación (9), instrumentos (11.1) y elementos de evaluación (11.2) van como textos propios del profesor (ADR-020). ¿Pasan a ser la variante de la plantilla para todos los proyectos? Y la cabecera de su tabla 4 («TAREA (Item del proyecto)», «Peso»): la app usa la de la plantilla | ADR-020, cierre de F2 |
| 2026-10-17 | **Correo del pie de página** (el del departamento): no va en la plantilla del repositorio, que es público. Hoy el documento sale sin él (opción `correo_pie`, vacía). ¿Se pone en Ajustes o se deja fuera? | Pie del documento, F4 |
| 2026-10-14 | Aprobar la maqueta v0 o indicar cambios | Fase F3 |
| 2026-10-14 | **Envío por correo:** mecanismo (A borrador en Outlook o Mail, B buzón de las apps, C cuenta del profesor), destinatarios habituales (¿jefatura, jefe de departamento?) y tamaño máximo de adjuntos | ADR-014 |
| 2026-10-14 | **Documento en valenciano e inglés:** ¿un idioma o varios a la vez?, nombre del archivo de cada idioma, quién revisa las traducciones de la plantilla y cómo se traducen los textos del profesor | Fase F10 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-documento-en-valenciano-e-inglés)) |
| 2026-10-14 | Indicaciones del **Excel de RA** que generará la app: qué cambia respecto al Excel actual | Fase F9 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-excel-de-ra)) |
| 2026-10-14 | Optativos que ofrece el centro en GM (IT, IEA, GA, CAR, EMV) y en GS de otras familias (ADM, ISO, AUT): **los dará CarlosFB**. SEA, STI y ARI: 0179, CVOPS031 y CVOPS141, ya en el catálogo | Apartado 2.2 |
| 2026-10-14 | Fuente de los RA del Proyecto intermodular de GM (`1713xxx` en el decreto). En el catálogo, con `pendiente` en GA, IT, IEA, CAR y EMV | Catálogo |
| 2026-10-14 | ¿Las fechas de evaluación y los periodos de empresa de GM son los mismos que los de GS? Y los de 1.º de cada ciclo (los de 1.º de GS están en las cuatro programaciones de 1.º revisadas: ¿valen para todos los ciclos de GS?). Sin ellos no se crea `cursos/2026-2027.yaml`: la prueba de regeneración toma las fechas de cada referencia | `cursos/2026-2027.yaml` |
| 2026-10-14 | ¿Quién da de alta cada curso escolar (fechas, resolución, FE)? Propuesta: CarlosFB, en julio, con la incidencia del vigía | Operaciones |
| 2026-10-14 | Programación modelo de Grado Básico | Fase F8 |

## Por comprobar (sin preguntar a nadie)

| Desde | Qué | Cómo |
| --- | --- | --- |
| 2026-10-14 | Que PyQt6 6.7 trae `QtPdf` en los paquetes de macOS y Windows | Prueba en F4 |

## Repositorio

| Desde | Qué |
| --- | --- |
