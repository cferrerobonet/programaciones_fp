@AGENTS.md

## Propio del asistente

- La sesión se abre en esta carpeta (`PROGRAMACIONES - CÓDIGO FUENTE/`): aquí mandan `AGENTS.md`, los ganchos de `.claude/settings.json` y, cuando se creen con el código, las reglas de `.claude/rules/`.
- Las reglas de redacción del documento son las de la skill de la bóveda `programacion-didactica`. Si una de ellas cambia, se cambia también en `docs/DOCUMENTO_GENERADO.md`.
- Salidas largas (suite, logs de la CI, render del PDF) filtradas con `tail`/`grep`; con el código, en el subagente `verificador` (previsto, aún no existe).
- Para revisar un cambio antes de publicarlo, el subagente `revisor` (previsto, aún no existe).
- Tras publicar una versión, `/clear` antes de empezar otra tarea.
