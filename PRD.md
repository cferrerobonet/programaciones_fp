# PRD · Programaciones

Documento de requisitos de producto. Versión inicial: 2026-10-14. Las decisiones y su porqué están en [docs/DECISIONES.md](docs/DECISIONES.md); lo que falta, en [docs/PENDIENTE.md](docs/PENDIENTE.md).

## 1. Problema

Cada curso, cada profesor de FP rehace la programación didáctica de sus módulos. La mayor parte del documento no depende de él:
- **Datos oficiales:** RA, criterios de evaluación, competencias, correspondencias con los estándares de competencia (ECP) y normativa.
- **Datos del curso:** fechas de evaluación y periodos de formación en empresa.
- **Textos fijos de la plantilla del centro.**

Copiar y pegar todo eso a mano tiene cuatro consecuencias:
- Programaciones con normativa derogada o RA desactualizados.
- Tablas 4 y 4.1 que no cuadran.
- Textos de plantillas antiguas que se quedan en el documento.
- Horas perdidas cada septiembre.

## 2. Objetivo

Que el profesor dedique su tiempo **solo a lo que únicamente él sabe**, y que todo lo demás salga correcto, actualizado y con el formato de la plantilla vigente.

| Métrica | Meta |
| --- | --- |
| Datos oficiales que introduce el profesor | Ninguno |
| Programaciones exportadas con la tabla 4.1 descuadrada | 0 (la app no deja exportar) |
| Tiempo de una programación heredada del curso anterior | Menos de 30 min (revisar y confirmar) |
| Las seis programaciones de 2026-2027 regeneradas desde sus datos | Iguales a las revisadas el 2026-10-06 (`comparar.py`) |

## 3. Usuarios

| Usuario | Qué necesita |
| --- | --- |
| Profesorado de FP de GM y GS (todas las familias del centro) | Hacer su programación rápido, sin errores y sin leer normativa |
| Profesor que hereda un módulo de otro | Partir de lo que hizo el anterior y cambiar solo lo suyo |
| CarlosFB (mantenedor) | Que el catálogo se mantenga solo y que cada cambio sea revisable |
| Jefatura y departamentos | Recibir las programaciones en la carpeta de Teams del curso, todas con la misma plantilla |

## 4. Alcance

**Dentro:**
- Los 11 ciclos de GM y GS del centro, con todos sus módulos (`catalogo/ciclos/`), incluidos los comunes (Inglés profesional, Itinerario personal para la empleabilidad I y II, Digitalización, Sostenibilidad, Proyecto intermodular y optativos). Listado en la nota de EPLA «PROGRAMACIONES — Ciclos y módulos».
- La plantilla del departamento en su versión vigente (la de PIICT, 0517, desde el 2026-10-06), válida para GM y GS.

**Fuera:**
- **Grado Básico** (ADR-032): los cuatro ciclos del centro (EE, IC, MV, SA). Módulos técnicos, Itinerario para la empleabilidad y Proyecto desde la 0.6.0, como GM y GS; los ámbitos comunes desde la 0.7.0, con su plantilla (competencias específicas y partes).
- **Editar ciclos o módulos:** son fijos (ver ADR-003).
- **Panel central de seguimiento** y conexión automática con Teams o Microsoft 365.
- **Datos del alumnado.**
**Más adelante** (decidido, pendiente de definir):
- **Documento en valenciano e inglés,** además de en castellano (CarlosFB, 2026-10-14). **Solo el documento final:** la app sigue siempre en castellano. El catálogo y la plantilla se diseñan desde la 1.0 para admitir varios idiomas ([docs/HOJA_DE_RUTA.md](docs/HOJA_DE_RUTA.md#función-futura-documento-en-valenciano-e-inglés)).
- **Excel de RA** que acompaña a cada programación en su carpeta, con el mismo nombre y algunas variaciones respecto al actual. CarlosFB dará las indicaciones ([docs/HOJA_DE_RUTA.md](docs/HOJA_DE_RUTA.md#función-futura-excel-de-ra)).

## 5. Qué es automático y qué es del profesor

| Parte del documento | Origen |
| --- | --- |
| Portada (familia, ciclo, módulo, horas), normativa, ECP, competencias, RA y criterios, horas semanales, fechas, formación en empresa, optativos | **Automático**, desde el catálogo |
| Pesos de cada elemento, horas y modalidad de cada RA (tabla 4.1), porcentajes de centro y empresa | **Calculado** a partir de lo que introduce el profesor |
| Profesorado, unidades y prácticas con horas y trimestre, elementos de evaluación y sus RA, horas de empresa por RA, competencias de cada RA, metodología propia, recursos, espacios, actividades | **Del profesor**: 100 % manual |
| Diversidad, recuperación, instrumentos, asistencia, principios pedagógicos… | **Texto fijo** de la plantilla, que **no se muestra en la app** hasta la vista previa |

El detalle, apartado por apartado: [docs/DOCUMENTO_GENERADO.md](docs/DOCUMENTO_GENERADO.md).

## 6. Historias de usuario y criterios de aceptación

| ID | Como… | Quiero… | Criterio de aceptación |
| --- | --- | --- | --- |
| HU-01 | profesor | elegir mi módulo por ciclo, curso o código | En 3 pulsaciones o tecleando el código aparece la ficha del módulo |
| HU-02 | profesor | ver los datos oficiales del módulo sin buscarlos | La ficha muestra horas, h/semana, RA con criterios, competencias, normativa y «comprobado en el BOE el AAAA-MM-DD» |
| HU-03 | profesor | introducir solo mis datos | La app pide únicamente los bloques manuales del §5. Ningún texto fijo aparece en la interfaz |
| HU-04 | profesor | que las tablas cuadren solas | Pesos, tabla 4.1 y porcentajes se calculan mientras escribo. Si algo no cuadra, se ve el aviso y la exportación definitiva queda bloqueada |
| HU-05 | profesor | ver cómo quedará antes de entregar | «Vista previa» abre el PDF con marca «BORRADOR» en menos de 30 s |
| HU-06 | profesor | exportar en Word y PDF | Salen dos archivos con el nombre normalizado. Si la carpeta de Teams del curso está configurada y sincronizada, se guardan directamente en ella |
| HU-07 | profesor | no perder nada si se me estropea el equipo | Abrir el `.docx` exportado recupera todos mis datos, también los manuales |
| HU-08 | profesor | partir de la programación del curso anterior, mía o de otro | «Nueva a partir de…» trae los bloques manuales como «heredados». Lo oficial y las fechas se actualizan |
| HU-09 | profesor | que nadie dé por buenos datos que no he revisado | La exportación definitiva exige confirmar o cambiar cada bloque heredado |
| HU-10 | profesor | saber si ha cambiado la normativa de mi módulo y decidir yo cuándo aplicarlo | Al abrir mi programación, la app me enseña qué RA o normas han cambiado y qué bloques míos afecta. Hasta que pulso «Aceptar cambios», mi programación sigue con la versión anterior y la app me lo recuerda |
| HU-11 | profesor | no tener que configurar nada técnico | Al empezar un curso escolar, la app solo pregunta mi nombre y la carpeta de Teams de ese curso |
| HU-12 | mantenedor | que el catálogo se actualice solo | El vigía semanal detecta cambios en BOE y DOGV y abre una PR con la diferencia, que revisa y fusiona CarlosFB: nada se publica solo (ADR-028). Al fusionarla se publica; cada profesor lo recibe en la app y lo acepta (ADR-015) |
| HU-13 | mantenedor | publicar versiones sin compilar en local | Una etiqueta `vX.Y.Z` compila macOS, Windows y Linux en GitHub y la app avisa sola |
| HU-14 | profesor | enviar por correo una o varias de mis programaciones | Desde «Programaciones» marco una o varias, elijo Word, PDF o ambos y los destinatarios (los habituales de Ajustes y otros), y se abre en mi Outlook o Mail un solo correo con todos los adjuntos y el asunto ya escrito, que reviso y envío yo. Lo que no estaba exportado se exporta antes. Si los adjuntos pasan de 20 MB, la app avisa |
| HU-15 | profesor | gestionar mis programaciones de este equipo | En «Programaciones» marco una o varias y, con botones o con clic derecho, las abro (solo una), las veo en vista previa, las exporto a una carpeta (sin sustituir nada sin preguntar), las envío por correo o las borro (a la papelera; lo exportado no se toca) |
| HU-16 | profesor | tener a mano mis módulos | Marco con una estrella mis módulos (clic, clic derecho o ⌘D) y el chip «Favoritos» deja ver solo esos |

## 7. Requisitos funcionales

| ID | Requisito |
| --- | --- |
| RF-01 | Catálogo de ciclos y módulos incorporado y no editable |
| RF-02 | Ficha de solo lectura con los datos oficiales del módulo |
| RF-03 | Formulario por bloques para los datos manuales, con validación en directo |
| RF-04 | Cálculo automático: peso de cada elemento = horas del elemento / horas del módulo · horas de centro de cada RA = propuesta de reparto a partes iguales de las horas de cada elemento entre sus RA, **ajustable por el profesor** en enteros dentro de sus límites · total de cada RA = centro + empresa · % de empresa entero redondeado hacia arriba y % de centro = 100 − empresa |
| RF-05 | Archivo de trabajo `.programacion` con autoguardado |
| RF-06 | Vista previa en PDF con marca de agua |
| RF-07 | Exportación definitiva en `.docx` y `.pdf` desde la plantilla, con los datos del profesor incrustados en el `.docx` |
| RF-08 | Abrir un `.docx` exportado por la app y recuperar todos sus datos. Si se ha modificado en Word después, avisar de que esos cambios no se recuperan |
| RF-09 | «Nueva a partir de…»: herencia con bloques marcados y confirmación obligatoria |
| RF-10 | Importar una vez las programaciones existentes en `.docx` (tablas 4 y 4.1) como punto de partida, también las del formato antiguo del departamento (ADR-035) y las antiguas de Grado Básico, con las tablas en 7 y 7.1 (ADR-037), y los ámbitos de GB sin datos de la app (ADR-040). Con un módulo elegido en la columna «Módulos», el archivo no tiene que llamarse «SIGLA N - 0xxx - Nombre»; si el documento dice otro módulo, se pregunta cuál (ADR-036) |
| RF-11 | Actualización del catálogo y de la app por HTTPS desde GitHub, con aviso |
| RF-12 | Funciona sin conexión con el último catálogo descargado |
| RF-13 | Ajustes mínimos: nombre del profesor, curso escolar con sus fechas y su carpeta de Teams (un solo apartado), formato de salida, correo y favoritos |
| RF-14 | Enviar por correo una o varias programaciones (Word, PDF o ambos) en un solo mensaje, con destinatarios recordados y asunto y cuerpo de plantilla: borrador en el programa de correo del profesor, sin contraseñas (ADR-014) |
| RF-15 | Listado «Programaciones» con acciones sobre una o varias marcadas: abrir, vista previa, exportar a carpeta, enviar por correo y borrar (a la papelera, ADR-024) |
| RF-16 | Módulos favoritos guardados en los ajustes de cada equipo, con su filtro |

## 8. Supuestos y restricciones

- Ciclos y módulos no cambian de un curso a otro (CarlosFB, 2026-10-14). Si un real decreto los cambia, es una actualización del catálogo, no una configuración.
- La carpeta de Teams es la misma para todos los profesores en un curso y cambia cada curso. Cada profesor la introduce en la app.
- Sin presupuesto para servidor: no hay backend propio.
- Sin administrador de Microsoft 365: nada de integración con Teams o Graph.
- Los equipos del centro pueden no permitir instalar programas: se ofrece versión portable en Windows y en Linux.

## 9. Riesgos principales

Están en [docs/HOJA_DE_RUTA.md](docs/HOJA_DE_RUTA.md#riesgos): que Word conserve los datos incrustados al guardar, la lectura de anexos del DOGV en PDF, que haya equipos sin Word y los cambios de plantilla del departamento.
