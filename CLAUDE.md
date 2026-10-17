@AGENTS.md

## Propio del asistente

- La sesión se abre en esta carpeta (`PROGRAMACIONES - CÓDIGO FUENTE/`): aquí mandan `AGENTS.md`, los ganchos de `.claude/settings.json` y las reglas de `.claude/rules/`.
- Las reglas de redacción del documento son las de la skill de la bóveda `programacion-didactica`. Si una de ellas cambia, se cambia también en `docs/DOCUMENTO_GENERADO.md`.
- Salidas largas (suite, logs de la CI, render del PDF) filtradas con `tail`/`grep`; o en el subagente `verificador`.
- Para revisar un cambio antes de publicarlo, el subagente `revisor`.
- Tras publicar una versión, `/clear` antes de empezar otra tarea.
