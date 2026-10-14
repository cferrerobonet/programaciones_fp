# Cómo trabajar en Programaciones

El mismo flujo que Partes de salida.

## Entorno

```bash
make venv      # ~/.venvs/programaciones (fuera de iCloud)
make ganchos   # .githooks/pre-commit: bloquea datos personales, binarios fuera de sitio, secretos y la palabra prohibida
               # mientras no hay Makefile: git config core.hooksPath .githooks
make run
```

La carpeta del repositorio está en iCloud: el entorno virtual, las cachés y los artefactos van fuera (`~/.venvs`, `/tmp`). Las programaciones reales de referencia se leen de la bóveda por ruta y **nunca se copian dentro**.

## Ciclo de un cambio

1. Leer el documento que manda (`docs/README.md`) y la regla de la zona (`.claude/rules/`).
2. Cambiar el código **y su test**: una regresión debe fallar al revertir el arreglo.
3. `scripts/qa.sh todo` en verde. Si toca el documento generado, además `-m referencias` y revisar el render.
4. Actualizar el documento que toque o anotar «sin impacto documental».
5. Commit con ficheros concretos (nunca `git add -A`), push y, si va a los equipos, versión y etiqueta (skill `publicar`).

## Ramas y PR

- `main` siempre publicable. Para cambios grandes, rama `tipo/descripcion-corta` y PR con la CI `Comprobar` en verde.
- Las PR del vigía (`curriculo/…`) se fusionan solas si pasan las comprobaciones automáticas. La aprobación de cada cambio la da cada profesor en la app (ADR-015). Si una PR falla las comprobaciones, la revisa CarlosFB.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/es/) en español, minúscula tras los dos puntos, sin línea de coautoría:

`feat(ui): …` · `fix(documento): …` · `feat(catalogo): …` · `docs: …` · `test: …` · `chore(release): v0.2.0`

Zonas: `ui`, `documento`, `catalogo`, `calculos`, `herencia`, `pdf`, `build`, `vigia`.

## Versiones

SemVer en `pyproject.toml` y `src/programaciones/__init__.py`:
- **Arreglo** → patch.
- **Función o cambio visible** → minor.
- **Cambio de formato del `.programacion` o de la parte incrustada** → major, con migración.

Cada versión lleva su entrada en `CHANGELOG.md`, escrita para el profesorado: es lo que ven en la ventana de novedades.

## Código

- Ruff, 120 columnas. Comentarios que explican **por qué**, no qué.
- Dominio sin Qt. La interfaz solo llama al dominio.
- Nombres en castellano sin tildes, con los términos de `docs/GLOSARIO.md`.
