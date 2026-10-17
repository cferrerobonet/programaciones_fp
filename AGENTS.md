# Programaciones — instrucciones para agentes

App de escritorio (macOS y Windows, Python 3.11 + PyQt6) con la que el profesorado de FP de EPLA (GM y GS) genera en Word y PDF la programación didáctica de un módulo, con la plantilla del centro. Sin servidor. Catálogo curricular actualizado por un vigía en GitHub Actions.
- Repositorio **público**: `github.com/cferrerobonet/programaciones_fp`.
- Fuente única de instrucciones: `CLAUDE.md` solo la importa.
- **Estado:** en desarrollo. Hay documentación, el catálogo curricular (fase F1, cerrada el 2026-10-17) y el motor del documento (fase F2, cerrada el 2026-10-17 salvo la prueba manual de Word: `docs/PENDIENTE.md`). Todavía no hay interfaz.

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
| Código | `src/programaciones/` (dominio sin Qt: catálogo, programación, cálculos, validación, documento, importación, incrustación, PDF) y, en F4, `src/programaciones/ui/`. Módulos en `TRD.md` §3 |
| Plantilla con marcas (desempaquetada) · su constructor | `src/programaciones/recursos/plantilla/` · `scripts/plantilla.py` |
| Regenerar las referencias · prueba manual de Word (R1) | `scripts/regenerar.py` · `scripts/prueba_word.py` |
| Catálogo fuente y publicado | `catalogo/` (YAML generado, no se edita a mano) · `catalogo/publicado/` (firmado, F5) |
| Constructor y comprobación del catálogo · esquemas | `scripts/catalogo.py` · `src/programaciones/esquemas/` |
| Pruebas | `tests/` (`-m referencias`: solo en local, lee la bóveda) |
| App de referencia (se copia de aquí) | `../../PARTES DE SALIDA (python)/PARTES DE SALIDA - CÓDIGO FUENTE/` |
| Scripts del currículo que se reutilizan | `curriculo.py` y `vigilancia.py` en `.claude/skills/apuntes-auditoria/scripts/` de la bóveda |

## Comandos

```bash
PY=~/.venvs/programaciones/bin/python     # fuera de iCloud, obligatorio
$PY scripts/catalogo.py construir <SIGLA>|todo [--sin-red]   # rehace el catálogo desde BOE y DOGV
$PY scripts/catalogo.py comprobar [--red]   # esquemas, horas, RA, fuentes y huellas (la firma, en F5)
$PY scripts/catalogo.py comparar <docx>…    # RA y criterios de una programación frente al catálogo
$PY scripts/plantilla.py crear <PIICT.docx> --proyecto <0526.docx> | comprobar   # plantilla con marcas, sin datos personales
$PY scripts/regenerar.py "<…/01 DOCENCIA/FP>" [código…] [--detalle]   # regenera las referencias y las compara
$PY scripts/prueba_word.py preparar <carpeta> | comprobar <docx>…     # prueba manual de Word (R1)
$PY -m pytest                               # suite; con PROGRAMACIONES_REFERENCIAS=…/01 DOCENCIA/FP, también -m referencias
$PY -m ruff check scripts src tests
scripts/crear_icono.sh                      # icono.ico (y .icns en macOS) desde imagenes/icono.png
# Previstos con la app, como en Partes de salida:
make venv · make ganchos · make run · make capturas · scripts/qa.sh todo
```

## Reglas por zona (`.claude/rules/`; hoy, `catalogo.md`, `documento.md` y `tests.md`; las demás, con la app)

| Al tocar… | Regla |
| --- | --- |
| `tests/`, `pyproject.toml`, `scripts/qa.sh` | `tests.md` |
| spec, instalador, Makefile, workflows, actualizaciones | `empaquetado.md` |
| `catalogo/`, `catalogo.py`, `scripts/catalogo.py`, `vigia.yml` | `catalogo.md` |
| plantilla, `documento.py`, `incrustar.py`, `pdf.py`, `importar_docx.py`, `contenido.py`, `scripts/plantilla.py`, `scripts/regenerar.py` | `documento.md` |
| `ui/`, `DESIGN.md` | `interfaz.md` |
| documentación y `.claude/` | `documentacion.md` |

## Cada cambio publicado es una versión (cuando haya código)

SemVer en `pyproject.toml` **y** `src/programaciones/__init__.py`, comprobado por un test. Cada versión lleva:
- Su entrada en `CHANGELOG.md`, que es la nota del release y lo que el profesor ve en la ventana de novedades.
- Commit con ficheros concretos, en Conventional Commits en español.
- Push y etiqueta `vX.Y.Z`.

Lo hace la skill `publicar`, que además anota la versión en la ficha de la bóveda (`../PROGRAMACIONES — Índice.md`). Un cambio solo del catálogo no es una versión de la app: se publica con `catalogo.yml`.

## Skills y agentes del proyecto

**Previstos, adaptados de Partes de salida:**
- Skills: `publicar` y `tests`.
- Agentes: `revisor` (solo lectura, fichero:línea) y `verificador` (pasa `qa.sh`).

**Propios:**
- `catalogo`: construir o revisar un ciclo, o aceptar una PR del vigía.
- `regenerar`: rehacer una programación de referencia y compararla con su `.docx`.

Auditoría: skill de usuario `auditoria-apps`; hallazgos en la bóveda, `PROGRAMACIONES — Auditoría.md`.

## Entorno (hoy no hay Makefile)

- Intérprete en `~/.venvs/programaciones` (Python 3.11, `pip install -r requirements-dev.txt`; con la app, `make venv`). Dentro de iCloud, Qt deja de arrancar. `construir` necesita además `pdftotext` (poppler) y guarda la caché de los documentos en `~/Library/Caches/programaciones`. Las pruebas del PDF y de R1 usan LibreOffice si está instalado (en la CI, sí).
- Los ganchos de git se activan hoy con `git config core.hooksPath .githooks`; con el Makefile, `make ganchos`.
- Datos del equipo de desarrollo: `~/Library/Application Support/Programaciones`.

## Secretos y datos personales

- Barrera común: `scripts/comprobar_secretos.sh` (gancho de git y CI «Secretos» con gitleaks). Ni contraseñas, ni datos del hosting, ni datos reales de personas, ni documentos del centro en el repositorio; tests con datos ficticios (móviles 600…, `12345678Z`, `@example.com`). Excepciones en `.secretos-ignorar`, siempre con su motivo. Reglas completas: skill de usuario `barrera-secretos`.
