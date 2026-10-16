# Documentación de Programaciones

Cada documento tiene un dueño temático: un cambio actualiza el suyo en la misma tarea. No se crean documentos paralelos ni fechados.

| Documento | Responde a | Se actualiza cuando… |
| --- | --- | --- |
| [../PRD.md](../PRD.md) | ¿Qué problema resuelve, para quién y con qué alcance? Historias y requisitos funcionales | cambia el alcance o un comportamiento |
| [../TRD.md](../TRD.md) | ¿Cómo está hecha? Stack, reutilización de Partes de salida, arquitectura, requisitos no funcionales, actualizaciones | se añade un módulo o cambia un flujo |
| [../DESIGN.md](../DESIGN.md) | ¿Cómo se ve? Mismo sistema que Partes de salida, ventanas y bloques | cambia algo visible |
| [DOCUMENTO_GENERADO.md](DOCUMENTO_GENERADO.md) | ¿Qué lleva la programación exportada, de dónde sale cada pieza, cómo se llama el archivo y qué se valida? | cambia la plantilla o una regla de redacción |
| [MODELO_DE_DATOS.md](MODELO_DE_DATOS.md) | Catálogo, curso escolar, archivo `.programacion` y fórmulas | cambia un formato o un cálculo |
| [CATALOGO_Y_FUENTES.md](CATALOGO_Y_FUENTES.md) | ¿De dónde sale cada dato oficial y cómo se mantiene al día? | cambia una fuente o el vigía |
| [SEGURIDAD_Y_DATOS.md](SEGURIDAD_Y_DATOS.md) | ¿Qué datos se tratan y cómo se protegen? | cambia el tratamiento de datos o la integridad |
| [PLAN_DE_PRUEBAS.md](PLAN_DE_PRUEBAS.md) | ¿Cómo se comprueba que funciona? | cambia la estrategia de pruebas |
| [OPERACIONES.md](OPERACIONES.md) | ¿Cómo se instala, publica, restaura y diagnostica? Alta anual del curso | cambia la compilación, la publicación o el soporte |
| [DECISIONES.md](DECISIONES.md) | ¿Por qué es así? (ADR) | se toma una decisión con alternativas |
| [HOJA_DE_RUTA.md](HOJA_DE_RUTA.md) | Fases, funciones futuras y riesgos | se cierra una fase o aparece un riesgo |
| [PENDIENTE.md](PENDIENTE.md) | ¿Qué falta? Datos de CarlosFB y comprobaciones | aparece o se cierra algo |
| [GLOSARIO.md](GLOSARIO.md) | Términos del dominio y su nombre en el código | aparece un término nuevo |
| [HERRAMIENTAS.md](HERRAMIENTAS.md) | Skills y herramientas de apoyo al desarrollo | se añade o descarta una |
| [../CHANGELOG.md](../CHANGELOG.md) | ¿Qué cambió en cada versión? (también son las novedades que ve el profesor) | se publica una versión |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | ¿Cómo se trabaja? Entorno, ramas, commits | cambia el flujo de trabajo |

Instrucciones para asistentes de código: [../AGENTS.md](../AGENTS.md) (y `.claude/rules/` cuando haya código).

**Fuentes de verdad:** no se copian cifras vivas en los documentos.
- Versión → `pyproject.toml`.
- Tokens → `ui/estilo.py`.
- Datos oficiales → `catalogo/`.
- Reglas de redacción → skill `programacion-didactica` de la bóveda.
