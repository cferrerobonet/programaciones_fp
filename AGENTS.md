# Programaciones — instrucciones para agentes

App de escritorio (macOS y Windows, Python 3.11 + PyQt6) con la que el profesorado de FP de EPLA (GB, GM y GS) genera en Word y PDF la programación didáctica de un módulo, con la plantilla del centro. Sin servidor. Catálogo curricular actualizado por un vigía en GitHub Actions.
- Repositorio **público**: `github.com/cferrerobonet/programaciones_fp`.
- Fuente única de instrucciones: `CLAUDE.md` solo la importa.
- **Estado:** F1 a F5 cerradas (versión en `pyproject.toml`; ADR-026); de F2 falta la prueba de Word (`docs/PENDIENTE.md`). Sigue F6 (piloto). F8 (Grado Básico, ADR-032): faltan los ámbitos.

## Forma de trabajar

- **Idioma y estilo:** español. Usuario: **CarlosFB**. Respuestas cortas, sin explicaciones ni código no pedidos.
- **Palabra prohibida:** nunca se escribe la de la bóveda (el nombre del asistente) en ningún archivo ni commit. Los nombres `CLAUDE.md` y `.claude/` sí valen. Los commits van sin coautoría.
- **Sin datos, no se implementa:** si falta un dato, se apunta en `docs/PENDIENTE.md`, se pide y en la interfaz sale «pendiente». **No inventar** RA, normas, horas, fechas ni textos de la plantilla.
- **Repositorio público:** ningún dato personal, contraseña ni clave privada (la del catálogo, solo en el secreto). Ni programaciones reales: las de CarlosFB, fuera; `.docx` ficticios en `tests/datos/`.
- **Correo:** borrador en el programa de correo del profesor, sin contraseñas (ADR-014) ni datos del servidor (ADR-016); pie y destinatarios, en Ajustes. Las pruebas simulan el correo y la papelera (`conftest.py`).
- **Compilación:** nunca en local (ni PyInstaller, ni Inno Setup, ni `hdiutil`): en GitHub (skill `publicar`; prueba con `gh workflow run compilar.yml`).
- **Conexiones:** sin `ssh`, `sftp` ni `scp`. El puerto 22 de IONOS no se toca.
- **«Verificado»** = hay una prueba que falla al revertir el cambio. Un cambio en el documento generado se comprueba con el render en PDF, mirando todas las páginas.
- **Copias de iCloud:** antes de cada commit, buscar «nombre 2.ext» y carpetas «x 2»; si son idénticas a su original, se borran.
- Leer por rangos (`grep -n`), no releer, usar el mapa.

## Reglas del producto (no negociables)

1. **Ciclos y módulos son fijos.** Vienen en el catálogo y no hay pantalla para editarlos.
2. **Los textos fijos de la plantilla no se muestran en la interfaz:** solo en la vista previa y en el documento.
3. **Los datos oficiales son de solo lectura** y llevan su fuente. Los manuales los introduce y confirma el profesor; un bloque heredado no vale para la definitiva hasta que lo confirma. **Los cambios de currículo los acepta cada profesor** (ADR-015).
4. **Lo que no se puede perder viaja dentro del `.docx` exportado.**
5. **Interfaz idéntica a Partes de salida** (`DESIGN.md`). Antes de crear un componente, se copia el suyo.
6. **Reglas del documento:** las de la skill `programacion-didactica` de la bóveda (legislación con hipervínculo y por fecha, índice automático con los títulos literales, tabla 4.1 cuadrada, porcentajes enteros, «CYPE»).

## Mapa

| Qué | Dónde |
| --- | --- |
| Producto · técnica · diseño | `PRD.md` · `TRD.md` · `DESIGN.md` (maqueta: `../Maqueta v0 (2026-10-14)/`) |
| Documento generado y validaciones · modelo de datos · fuentes | `docs/DOCUMENTO_GENERADO.md` · `docs/MODELO_DE_DATOS.md` · `docs/CATALOGO_Y_FUENTES.md` |
| Decisiones · pendiente · hoja de ruta · toda la documentación | `docs/DECISIONES.md` · `docs/PENDIENTE.md` · `docs/HOJA_DE_RUTA.md` · `docs/README.md` |
| Dominio (sin Qt) | `src/programaciones/`: catálogo, catálogo remoto y firma, programación, cálculos, validación, documento, importación, incrustación, PDF, herencia, almacén, exportación, correo, ajustes, actualizaciones… (`TRD.md` §3) |
| Arranque · estado compartido | `app.py` (entrada `src/main.py`) · `contexto.py` |
| Interfaz | `ui/`: `ventana.py` (barra, avisos, menú, exportar), `columnas.py` (tres zonas), `modales.py`, `ajustes.py`, `programaciones.py`, `gestion.py`, `dialogos.py`… (`TRD.md` §3) |
| Plantilla con marcas · su constructor | `src/programaciones/recursos/plantilla/` · `scripts/plantilla.py` |
| Catálogo · constructor · esquemas | `catalogo/` (generado, no se edita a mano; `cursos/` lo da CarlosFB) · `scripts/catalogo.py` · `src/programaciones/esquemas/` |
| Vigía · publicación firmada | `scripts/vigia.py`, `vigia.yml` (ADR-028) · `catalogo.yml`, rama `catalogo-publicado`, secreto `CATALOGO_CLAVE` (ADR-027) |
| Referencias · prueba de Word (R1) | `scripts/regenerar.py` · `scripts/prueba_word.py` |
| Compilación | `Programaciones.spec`, `installer_windows.iss`, `scripts/build/`, `scripts/*.ps1`, `scripts/comprobar_paquete.sh`, `.github/workflows/compilar.yml` |
| Pruebas | `tests/` (`-m ui`: interfaz; `-m referencias`: solo en local, lee la bóveda) |
| App de referencia (se copia de aquí) | `../../PARTES DE SALIDA (python)/PARTES DE SALIDA - CÓDIGO FUENTE/` |

## Comandos

```bash
PY=~/.venvs/programaciones/bin/python     # fuera de iCloud, obligatorio
make venv · make ganchos · make run         # entorno, ganchos de git y abrir la app desde el código
scripts/qa.sh todo|rapido|ui|lint           # ruff, catálogo, plantilla y suite; log en /tmp/programaciones-qa-*.log
$PY scripts/catalogo.py construir <SIGLA>|todo [--sin-red] · comprobar [--red] · comparar <docx>… · version · verificar <URL>
$PY scripts/vigia.py revisar                # el vigía en local (toca catalogo/)
$PY scripts/plantilla.py crear <PIICT.docx> --proyecto <0526.docx> | comprobar
$PY scripts/regenerar.py "<…/01 DOCENCIA/FP>" [código…] [--detalle]
$PY scripts/prueba_word.py preparar <carpeta> | comprobar <docx>…
scripts/crear_icono.sh                      # icono.ico (y .icns en macOS) desde imagenes/icono.png
gh workflow run compilar.yml | vigia.yml [-f simulacro=true] | catalogo.yml
```

## Reglas por zona (`.claude/rules/`, se cargan solas al tocar la zona)

| Al tocar… | Regla |
| --- | --- |
| `tests/`, `pyproject.toml`, `scripts/qa.sh` | `tests.md` |
| spec, instalador, Makefile, workflows, actualizaciones, arranque | `empaquetado.md` |
| `catalogo/`, `scripts/catalogo.py` y `vigia.py`, esquemas, `vigia.yml`, `catalogo.yml` | `catalogo.md` |
| plantilla, `documento.py`, `incrustar.py`, `pdf.py`, `importar_docx.py`, `contenido.py`, sus scripts | `documento.md` |
| `ui/`, `contexto.py`, `DESIGN.md` | `interfaz.md` |
| documentación y `.claude/` | `documentacion.md` |

## Cada cambio publicado es una versión

SemVer en `pyproject.toml` **y** `src/programaciones/__init__.py` (test), entrada en `CHANGELOG.md` (nota del release y ventana de novedades), commit con ficheros concretos en Conventional Commits en español, push y etiqueta `vX.Y.Z`: skill `publicar`, que sigue la compilación y anota la versión en la ficha de la bóveda (`../PROGRAMACIONES — Índice.md`). Un cambio solo del catálogo no es una versión de la app: `catalogo.yml` lo firma y publica al llegar a `main`.

## Skills y agentes del proyecto

- Skills: `publicar` · `tests`. Agentes: `revisor` (solo lectura, fichero:línea) · `verificador` (pasa `qa.sh`).
- Previstos: skills `catalogo` (construir un ciclo, revisar una PR del vigía) y `regenerar`.
- Auditoría: skill de usuario `auditoria-apps`; hallazgos en la bóveda, `PROGRAMACIONES — Auditoría.md`.

## Entorno

- Intérprete en `~/.venvs/programaciones` (`make venv`); dentro de iCloud, Qt no arranca. `construir` necesita `pdftotext` (poppler); caché en `~/Library/Caches/programaciones`. El PDF y R1 usan LibreOffice si está (en la CI, sí).
- `make ganchos` activa `.githooks/` (pre-commit y pre-push).
- Datos del equipo de desarrollo: `~/Library/Application Support/Programaciones` (ajustes y registro).

## Secretos y datos personales

Barrera común: `scripts/comprobar_secretos.sh` (gancho y CI «Secretos» con gitleaks). Tests con datos ficticios (móviles 600…, `12345678Z`, `@example.com`). Excepciones en `.secretos-ignorar`, siempre con su motivo. Reglas completas: skill de usuario `barrera-secretos`.
