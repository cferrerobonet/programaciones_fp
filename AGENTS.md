# Programaciones — instrucciones para agentes

App de escritorio (macOS y Windows, Python 3.11 + PyQt6) con la que el profesorado de FP de EPLA (GM y GS) genera en Word y PDF la programación didáctica de un módulo, con la plantilla del centro. Sin servidor. Catálogo curricular actualizado por un vigía en GitHub Actions.
- Repositorio **público**: `github.com/cferrerobonet/programaciones_fp`.
- Fuente única de instrucciones: `CLAUDE.md` solo la importa.
- **Estado:** en diseño. Hay documentación y todavía no hay código.

## Forma de trabajar

- **Idioma y estilo:** español. Usuario: **CarlosFB**. Respuestas cortas, sin explicaciones ni código no pedidos.
- **Palabra prohibida:** nunca se escribe la de la bóveda (el nombre del asistente) en ningún archivo ni commit. Los nombres `CLAUDE.md` y `.claude/` sí valen. Los commits van sin coautoría.
- **Sin datos, no se implementa:** si falta un dato del que depende algo, se apunta en `docs/PENDIENTE.md` y se pide. **No inventar** RA, normas, horas, fechas ni textos de la plantilla.
- **Repositorio público:** ningún dato personal, contraseña ni clave privada. Las programaciones reales de los profesores no entran: para pruebas, solo las de CarlosFB, fuera del repositorio, y `.docx` ficticios en `tests/datos/`.
- **Correo:** ningún dato del servidor de correo (servidor, puerto, buzón, usuario, contraseña) en código ni en documentos (ADR-016). Al copiar `ajustes.py` o `correo.py` de Partes de salida, los campos del correo quedan vacíos. Lo vigilan `scripts/comprobar_secretos.sh`, el gancho y la CI `Secretos`.
- **Compilación:** no se compila en local, se compila en GitHub (skill `publicar`).
- **Conexiones:** sin conexiones `ssh`, `sftp` ni `scp`. La app no usa servidor y el puerto 22 de IONOS no se toca.
- **«Verificado»** = hay una prueba que falla al revertir el cambio. Un cambio en el documento generado se comprueba con el render en PDF y mirando todas las páginas.
- Leer por rangos (`grep -n`), no releer, usar el mapa.

## Reglas del producto (no negociables)

1. **Ciclos y módulos son fijos.** Vienen en el catálogo y no hay pantalla para editarlos.
2. **Los textos fijos de la plantilla no se muestran en la interfaz:** solo en la vista previa y en el documento.
3. **Los datos oficiales son de solo lectura** y llevan su fuente. Los datos manuales los introduce y confirma el profesor. Un bloque heredado no vale para la definitiva hasta que el profesor lo confirma. **Los cambios de currículo los acepta cada profesor** en su programación (ADR-015): la app nunca los aplica por su cuenta.
4. **Lo que no se puede perder viaja dentro del `.docx` exportado.** El equipo del profesor no es la fuente de verdad.
5. **Interfaz idéntica a Partes de salida** (`DESIGN.md`). Antes de crear un componente, se copia el suyo.
6. **Reglas del documento:** las de la skill `programacion-didactica` de la bóveda:
   - Legislación con hipervínculo y por fecha creciente.
   - Índice automático con los títulos literales de la plantilla.
   - Tabla 4.1 cuadrada.
   - Porcentajes de centro y empresa en enteros.
   - «CYPE» como nombre de la suite.

## Mapa

| Qué | Dónde |
| --- | --- |
| Producto · técnica · diseño | `PRD.md` · `TRD.md` · `DESIGN.md` |
| Documento generado, apartado por apartado, y validaciones | `docs/DOCUMENTO_GENERADO.md` |
| Catálogo, archivo de trabajo y cálculos | `docs/MODELO_DE_DATOS.md` |
| Fuentes oficiales y vigía | `docs/CATALOGO_Y_FUENTES.md` |
| Decisiones (ADR) · pendiente · hoja de ruta | `docs/DECISIONES.md` · `docs/PENDIENTE.md` · `docs/HOJA_DE_RUTA.md` |
| Mapa de toda la documentación | `docs/README.md` |
| Código (previsto) | `src/programaciones/` (dominio sin Qt) y `src/programaciones/ui/`. Módulos en `TRD.md` §3 |
| Plantilla `.docx` con marcas | `src/programaciones/recursos/plantilla/` |
| Catálogo fuente y publicado | `catalogo/` (YAML) · `catalogo/publicado/` (firmado) |
| App de referencia (se copia de aquí) | `../../PARTES DE SALIDA (python)/PARTES DE SALIDA - CÓDIGO FUENTE/` |
| Scripts del currículo que se reutilizan | `curriculo.py` y `vigilancia.py` en `.claude/skills/apuntes-auditoria/scripts/` de la bóveda |

## Comandos (previstos, como en Partes de salida)

```bash
PY=~/.venvs/programaciones/bin/python     # fuera de iCloud, obligatorio
make venv · make ganchos · make run · make capturas
scripts/qa.sh todo                          # ruff + suite
QT_QPA_PLATFORM=offscreen $PY -m pytest tests/test_x.py -x
$PY scripts/catalogo.py construir <ciclo>   # rehace el catálogo desde BOE y DOGV
$PY scripts/catalogo.py comprobar           # esquema y firma del catálogo
```

## Reglas por zona (`.claude/rules/`, se crean con el código)

| Al tocar… | Regla |
| --- | --- |
| `tests/`, `pyproject.toml`, `scripts/qa.sh` | `tests.md` |
| spec, instalador, Makefile, workflows, actualizaciones | `empaquetado.md` |
| `catalogo/`, `catalogo.py`, `scripts/catalogo.py`, `vigia.yml` | `catalogo.md` |
| plantilla, `documento.py`, `incrustar.py`, `pdf.py` | `documento.md` |
| `ui/`, `DESIGN.md` | `interfaz.md` |
| documentación y `.claude/` | `documentacion.md` |

## Cada cambio publicado es una versión

SemVer en `pyproject.toml` **y** `src/programaciones/__init__.py`, comprobado por un test. Cada versión lleva:
- Su entrada en `CHANGELOG.md`, que es la nota del release y lo que el profesor ve en la ventana de novedades.
- Commit con ficheros concretos, en Conventional Commits en español.
- Push y etiqueta `vX.Y.Z`.

Lo hace la skill `publicar`, que además anota la versión en la ficha de la bóveda (`../PROGRAMACIONES — Índice.md`). Un cambio solo del catálogo no es una versión de la app: se publica con `catalogo.yml`.

## Skills y agentes del proyecto

**Previstos, adaptados de Partes de salida:**
- Skills: `publicar`, `tests` y `auditar`.
- Agentes: `revisor` (solo lectura, hallazgos con fichero:línea) y `verificador` (pasa `qa.sh` y devuelve solo el resultado).

**Propios:**
- `catalogo`: construir o revisar un ciclo, o aceptar una PR del vigía.
- `regenerar`: rehacer una programación de referencia y compararla con su `.docx`.

## Entorno

- Intérprete en `~/.venvs/programaciones` (`make venv`). Dentro de iCloud, Qt deja de arrancar.
- `make ganchos` activa `.githooks/pre-commit`.
- Datos del equipo de desarrollo: `~/Library/Application Support/Programaciones`.
