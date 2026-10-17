---
name: publicar
description: Cierra y publica una versión de Programaciones — sube la versión (SemVer), escribe el CHANGELOG, pasa qa.sh, hace commit con ficheros concretos, push, etiqueta vX.Y.Z y sigue la compilación de GitHub hasta que el release tiene el DMG de macOS y el instalador y el portable de Windows; después anota la versión en la ficha de la bóveda. También lanza una compilación de prueba sin publicar. Usar tras cada cambio que se quiera llevar a los equipos, o cuando CarlosFB diga «publica», «sube versión», «commit y push» o «compila».
---

# Publicar una versión

Copia de la skill de Partes de salida. Sin pedir confirmación en cada paso: es el flujo acordado. Se compila **solo en GitHub** (nunca en local: ni PyInstaller, ni Inno Setup, ni `hdiutil`).

## 1. Situarse

- `git status --short` y `git log --oneline -5`. Si hay cambios de otra tarea sin terminar, preguntarlo antes de mezclarlos.
- Versión actual: `sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml`.
- Decidir el salto (SemVer): arreglo → patch · función nueva o cambio visible → minor · rompe el formato del `.programacion`, de la parte incrustada o de los ajustes → major (RNF-08).
- Un cambio solo del catálogo no es una versión de la app (se publica con `catalogo.yml`, fase F5).

## 2. Preparar

1. Subir la versión en **los dos sitios**: `pyproject.toml` (`version = "X.Y.Z"`) y `src/programaciones/__init__.py` (`__version__`). Un test vigila que coincidan.
2. `CHANGELOG.md`: pasar lo de `[Sin publicar]` a una entrada `## [X.Y.Z] - AAAA-MM-DD`, escrita para el profesorado (qué cambia en su pantalla o en su documento), con `Añadido`, `Cambiado`, `Corregido` o `Seguridad`. Es la nota del release y lo que ve el profesor en la ventana de novedades.
3. Impacto documental (regla `documentacion.md`): actualizar lo que toque o decir «sin impacto documental».
4. `scripts/qa.sh todo` → tiene que acabar en `QA todo: OK`. Si falla, leer el log con `grep`, no relanzar.

## 3. Commit, push y etiqueta

- **Antes del commit, copias de iCloud:** `find . -path ./.git -prune -o \( -name '* 2' -o -name '* 2.*' \) -print`. Si son idénticas a su original (`cmp`), se borran.
- **Nunca `git add -A` ni `git add .`** (el gancho lo bloquea): ficheros concretos.
- `git diff --cached --name-only` no puede tener `.docx`, `.pdf`, `.programacion` (salvo los ficticios de `tests/datos/`), `.zip`, `.dmg`, `.exe` ni imágenes fuera de `imagenes/`, `src/programaciones/recursos/` o `docs/capturas/`. El gancho `.githooks/pre-commit` lo vigila también (`make ganchos`).
- Mensaje: Conventional Commits en español, minúscula tras los dos puntos: `feat(ui): …`, `fix(documento): …`, `docs: …`, `chore(release): vX.Y.Z`. Sin línea de coautoría, sin la palabra prohibida y sin `--no-verify`.

```bash
git add <ficheros>
git commit -m "tipo(zona): descripción"
git push origin main
git tag vX.Y.Z
git push origin vX.Y.Z
```

## 4. Seguir la compilación

```bash
gh run list --workflow compilar.yml --limit 1
gh run watch <id> --exit-status
gh release view vX.Y.Z --json assets --jq '.assets[].name'
```

**Versión normal, no pre-release** (ADR-026): `compilar.yml` la crea con `--latest`, porque la app pregunta a `/releases/latest` y las pre-release no avisan a nadie. Comprobar que `curl -s https://api.github.com/repos/cferrerobonet/programaciones_fp/releases/latest | jq -r .tag_name` da la etiqueta nueva. Pre-release solo si CarlosFB lo pide.

Tienen que estar los tres: `Programaciones-X.Y.Z-macOS-arm64.dmg`, `Programaciones-X.Y.Z-Windows-Setup.exe` y `Programaciones-X.Y.Z-Windows-Portable.zip`. Si un job falla: `gh run view <id> --log-failed | tail -60`, arreglar y subir **patch nuevo** (nunca reescribir una etiqueta publicada).

**Compilación de prueba sin publicar:** `gh workflow run compilar.yml` (opciones `-f plataforma=macos|windows`, `-f depurar=true`), seguirla igual y, si hace falta mirar el resultado, `gh run download <id>`.

## 5. Cerrar

- Ficha de la bóveda `../PROGRAMACIONES — Índice.md`: «Versión vigente» y la fila del historial arriba (fecha, versión, una línea). `fecha_actualizacion` a hoy.
- Responder a CarlosFB en dos o tres líneas: versión, qué cambia, enlace del release.
