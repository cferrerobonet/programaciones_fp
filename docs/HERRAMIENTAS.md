# Herramientas de apoyo al desarrollo

Skills y herramientas para construir y mantener la app. Revisión del 2026-10-14. **Nada de lo externo está instalado:** antes de adoptar una skill se lee entera, se adapta y se comprueba que no lleva la palabra prohibida ni añade coautoría a los commits.

## 1. Skills propias que ya existen (se copian o se usan)

| Skill | Dónde está | Uso en Programaciones |
| --- | --- | --- |
| `programacion-didactica` | Bóveda (`02 EPLA/.claude/skills/`) | **Fuente de las reglas del documento.** Sus scripts (`verificar.py`, `comparar.py`, `paginas_indice.py`, `fila_proyecto.py`, `montar.py`) son la base de las pruebas del documento generado |
| `apuntes-auditoria` → `curriculo.py`, `vigilancia.py` | Bóveda | Base del lector del BOE (`catalogo.py`) y del vigía |
| `publicar`, `tests` + agentes `revisor` y `verificador` | Partes de salida | Se copian y se adaptan (TRD §2) |
| `build-macos-dmg`, `build-windows-exe`, `tests-locales` | Guardias de patio | Consulta si falla el empaquetado: recogen las lecciones de PyInstaller en los dos sistemas |
| `auditoria-apps` | Usuario | Auditoría; hallazgos en la bóveda (`PROGRAMACIONES — Auditoría.md`), no en el repositorio |
| `docx`, `pdf`, `xlsx` | Usuario | Validar el `.docx` generado (`validate.py`), revisar PDF y, en la fase F9, el Excel de RA |
| `systematic-debugging`, `verification-before-completion`, `security-and-hardening`, `code-review`, `simplify` | Usuario | Trabajo diario |
| `diagram-design` | Usuario | Diagramas de arquitectura y flujos de esta documentación |
| `impeccable`, `emil-design-eng`, `apple-design` | Usuario | Solo para pulir la maqueta. El diseño manda en `DESIGN.md`: idéntico a Partes de salida |

## 2. Skills externas candidatas (GitHub)

Estrellas comprobadas el 2026-10-14. Rutas `SKILL.md` verificadas. No se ha encontrado nada malicioso en ellas.

| Prioridad | Repositorio (★) | Skill | Para qué aquí | Licencia |
| --- | --- | --- | --- | --- |
| Alta | `github/awesome-copilot` (≈40 000) | `github-actions-hardening` | Revisar la seguridad de `vigia.yml` (abre PR con permisos de escritura) y `catalogo.yml` (firma con un secreto) | MIT |
| Alta | `obra/superpowers` (≈299 000) | `test-driven-development` | Rojo-verde-refactor para `calculos.py`, `validacion.py` y `herencia.py` | MIT |
| Alta | `trailofbits/skills` (≈7 500) | `property-based-testing` (Hypothesis) | Ida y vuelta del `.programacion` y del `.docx` incrustado, lector del BOE y normalización de nombres | CC-BY-SA-4.0 |
| Media | `addyosmani/agent-skills` (≈106 000) | `documentation-and-adrs`, `git-workflow-and-versioning` | Mantener los ADR y decidir parche, menor o mayor (el mismo repositorio de `security-and-hardening`) | MIT |
| Media | `openai/skills` (≈28 000) | `gh-fix-ci` | Diagnosticar compilaciones fallidas en los runners de macOS y Windows | Apache-2.0 |
| Media | `affaan-m/ECC` (≈279 000) o `wshobson/agents` (≈40 600) | `python-testing` / `python-testing-patterns` | Patrones de pytest: fixtures, parametrize, mocks | MIT |
| Media | `wshobson/agents` | `changelog-automation` | Formato Keep a Changelog: las novedades que ve el profesor | MIT |
| Media | `github/awesome-copilot` | `docs-sync-audit` | Detectar documentación que se ha quedado atrás respecto al código | MIT |
| Referencia | `borgbase/vorta` (≈2 500) | `release` | Publicación de una app **PyQt6** real. Solo como modelo | GPL-3.0 (no se copia código) |
| Referencia | `lncrawl/lightnovel-crawler` (≈2 600) | `releasing` | Etiqueta → PyInstaller + Inno Setup + notas desde `CHANGELOG.md`: la misma cadena. Solo como modelo | GPL-3.0 (no se copia código) |
| Referencia | `talmolab/sleap` (≈600) | `qt-testing` | Capturar widgets fuera de pantalla para revisarlos. Escrita para PySide6 | BSD-3-Clause-Clear |
| Referencia | `anthropics/skills` (≈181 000) | `doc-coauthoring` | Redactar especificaciones y ADR nuevos | Sin licencia declarada: solo lectura |

## 3. Descartadas

| Repositorio | Motivo |
| --- | --- |
| `garrytan/gstack` (`ship`, `document-release`) | Exige instalar todo gstack, guarda telemetría local y añade una línea de coautoría a los commits |
| `trailofbits/skills` → `modern-python` | Su plugin instala ganchos que interceptan `python` y `pip`: demasiado intrusivo |
| `D4Vinci/Scrapling` | Scraping para saltar protecciones anti-bot: innecesario para la API pública del BOE |
| `CodeAtCode/oss-ai-skills` → `pyqt` | Contenido útil (pytest-qt, QThread), pero con 24 estrellas y licencia GPL: solo lectura puntual |
| `jaimebs2/OpenSpain` → `boe` | Recoge los endpoints de la API del BOE, pero tiene 0 estrellas: se contrasta con la documentación oficial |

## 4. Herramientas (no skills)

| Herramienta | Uso |
| --- | --- |
| API de datos abiertos del BOE | Textos consolidados, metadatos y análisis (vigía y catálogo) |
| `lxml` | Plantilla con marcas, documento y retoque (ADR-019; sin docxtpl ni python-docx) |
| Word del equipo (AppleScript o COM) · LibreOffice sin interfaz | PDF en el equipo del profesor; LibreOffice también en la CI (PDF y datos incrustados) |
| `jsonschema`, `PyYAML`, `cryptography` (Ed25519) | Esquemas, catálogo y firma |
| `openpyxl` | Excel de RA (fase F9) |
| `Hypothesis` | Pruebas de propiedades |
| LanguageTool en local (ya en uso en los apuntes) | Ortografía de las plantillas y, en F10, de las traducciones |
