# Pendiente

Única lista de lo que falta. Lo más reciente arriba en cada tabla.

## Datos que faltan (los aporta CarlosFB)

| Desde | Qué | Para qué |
| --- | --- | --- |
| 2026-10-17 | **Erratas del BOE que corrigen las programaciones.** Tres criterios de 0517 (RA1 a y c, RA4 d) y uno de 0524 (RA1 a) no copian el BOE literal: corrigen «de acuerdo a», «(ITC)», «medidas, cumplen» y «las distintos» (comprobado en el PDF del BOE). El catálogo guarda el literal. ¿El documento usa el literal o la corrección? | ADR-017, F2 |
| 2026-10-17 | **Denominación de los ECP.** La tabla del apartado 2 de las programaciones de SEA pone a ECP1180_3, 1182_3, 1275_3, 1276_3 y 1277_3 el nombre de la UC del anexo V B) (RD 401/2023). El RD 532/2025 les da otro («Gestionar…», «Supervisar los procesos…»), que es el del catálogo. ¿Cuál va? | ADR-017, apartado 2 |
| 2026-10-17 | **Nombre del módulo cuando el RD y el Decreto 95/2026 no coinciden:** 0292, 0343, 0361 («… y sistemas de telefonía» en el RD), 0364 («… y Seguridad Electrónica» en el RD), 0365, 0438, 0454 y 0959. Hoy el catálogo da el del RD en `modulos/` y el del decreto en el ciclo. ¿Cuál va en la portada y en el nombre del archivo? | ADR-017, portada |
| 2026-10-17 | **Competencias de GA e IT:** su art. 5 las numera (1., 2.…) y las orientaciones del anexo I las citan con letras (a), b)…). ¿Se da por buena la correspondencia 1 = a), 2 = b)…? Hasta entonces, sin comprobar | Apartados 2.1 y 3 |
| 2026-10-17 | **Módulos comunes:** el catálogo usa el texto de los anexos del Decreto 114/2025, que amplía el RD 659/2023 (por ejemplo, un RA más en 1709 y en 1710). Confirmar que es el que va en la programación | ADR-017 |
| 2026-10-17 | **Normativa autonómica:** ¿se cita el Decreto 95/2026 en 1.2? Cambia los anexos I y II (horas) del Decreto 114/2025; las programaciones de referencia no lo citan | Apartado 1.2 |
| 2026-10-17 | **Programación de 0963 (ARI):** el enlace «RD 1581/2011, redacción RD 401/2023» del apartado 4 (cabecera de la tabla) apunta al RD 1127/2010 (BOE-A-2010-15355, el de SEA). No se ha corregido | Programación de referencia |
| 2026-10-14 | Aprobar la maqueta v0 o indicar cambios | Fase F3 |
| 2026-10-14 | **Envío por correo:** mecanismo (A borrador en Outlook o Mail, B buzón de las apps, C cuenta del profesor), destinatarios habituales (¿jefatura, jefe de departamento?) y tamaño máximo de adjuntos | ADR-014 |
| 2026-10-14 | **Documento en valenciano e inglés:** ¿un idioma o varios a la vez?, nombre del archivo de cada idioma, quién revisa las traducciones de la plantilla y cómo se traducen los textos del profesor | Fase F10 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-documento-en-valenciano-e-inglés)) |
| 2026-10-14 | Indicaciones del **Excel de RA** que generará la app: qué cambia respecto al Excel actual | Fase F9 ([HOJA_DE_RUTA.md](HOJA_DE_RUTA.md#función-futura-excel-de-ra)) |
| 2026-10-14 | Optativos que ofrece el centro en GM (IT, IEA, GA, CAR, EMV) y en GS de otras familias (ADM, ISO, AUT): **los dará CarlosFB**. SEA, STI y ARI: 0179, CVOPS031 y CVOPS141, ya en el catálogo | Apartado 2.2 |
| 2026-10-14 | Fuente de los RA del Proyecto intermodular de GM (`1713xxx` en el decreto). En el catálogo, con `pendiente` en GA, IT, IEA, CAR y EMV | Catálogo |
| 2026-10-14 | ¿Las fechas de evaluación y los periodos de empresa de GM son los mismos que los de GS? Y los de 1.º de cada ciclo | `cursos/2026-2027.yaml` |
| 2026-10-14 | ¿Quién da de alta cada curso escolar (fechas, resolución, FE)? Propuesta: CarlosFB, en julio, con la incidencia del vigía | Operaciones |
| 2026-10-14 | Regla de redondeo de la propuesta de horas de centro por RA (PIICT: 7,33 / 9,33 / 11,33 → 8 / 10 / 10, ajuste a mano). ¿La app propone «al entero más cercano y el resto al RA con más horas», o deja siempre el ajuste al profesor? | `calculos.py` |
| 2026-10-14 | Programación modelo de Grado Básico | Fase F8 |

## Por comprobar (sin preguntar a nadie)

| Desde | Qué | Cómo |
| --- | --- | --- |
| 2026-10-17 | EMV: el anexo V B) del RD 499/2024 asocia 0456 a «UC0626_3», que no está en el RD 532/2025; su art. 6 y el RD 532/2025 dicen 0626_2. Probable errata: el ECP queda sin código | BOE: corrección de errores del RD 499/2024 o nueva redacción |
| 2026-10-17 | Título de la Orden 20/2019: tomado del resumen de la Conselleria; falta cotejarlo con el PDF del DOGV núm. 8540 (2019-05-03) | DOGV |
| 2026-10-14 | Que Word conserva la parte incrustada al abrir y guardar (R1) | Prueba en F2 |
| 2026-10-14 | Que PyQt6 6.7 trae `QtPdf` en los paquetes de macOS y Windows | Prueba en F4 |

## Repositorio

| Desde | Qué |
| --- | --- |
