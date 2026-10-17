# Plan de pruebas

**Infraestructura:** la de Partes de salida.
- pytest (configuración en `pyproject.toml`) y, con la app, pytest-qt con `QT_QPA_PLATFORM=offscreen`.
- `comprobar.yml` en cada push: ruff, `catalogo.py comprobar` y la suite. Con la app, también `scripts/qa.sh todo|rapido`.
- `compilar.yml` arranca la app compilada en macOS y Windows.

**«Verificado»** = hay una prueba que falla al revertir el cambio.

## Niveles

| Nivel | Qué se prueba | Herramienta |
| --- | --- | --- |
| Cálculos | Pesos, reparto por RA, tabla 4.1, modalidad, porcentajes. Casos: las seis programaciones de referencia | pytest (paramétrico) |
| Validaciones | Cada V-xx con un caso que la cumple y otro que no | pytest |
| Archivo de trabajo | Ida y vuelta del `.programacion`, esquema, migración de formato y escritura atómica | pytest |
| Herencia | Bloques heredados, RA eliminados o renumerados en el catálogo, fechas del curso nuevo | pytest |
| Catálogo (F1) | `catalogo.py comprobar` limpio sobre el catálogo real. Lectores del BOE y del DOGV con textos ficticios que imitan sus formatos y erratas. Esquemas que aceptan lo bueno y rechazan lo malo. `comprobar` detecta cada error en un catálogo ficticio: horas, RA, criterios, fuentes, referencias y orden de la normativa. Con F5: firma válida y no válida, versión menor rechazada | pytest (`test_catalogo.py`, `test_esquemas.py`) |
| **RA de referencia** (F1) | Los RA y criterios del apartado 11 de las seis programaciones de 2026-2027 frente al catálogo: enunciados idénticos y criterios idénticos salvo las erratas del BOE que corrige la programación (lista en la prueba, solo con su posición) | `-m referencias` (local, `PROGRAMACIONES_REFERENCIAS` = carpeta `01 DOCENCIA/FP` de la bóveda) |
| Documento | Plantilla rellenada con los títulos exactos, campo TOC, 0 citas sin enlace, `updateFields`, `keepNext` y sin términos vetados | pytest + lógica de `verificar.py` |
| Incrustación | Exportar → abrir → mismos datos. Huellas. **Abrir y guardar en Word real conserva la parte** (manual en macOS y Windows, riesgo R1) | pytest + prueba manual |
| **Regeneración** | Las seis programaciones de 2026-2027 (0517, 0524, 0525, 0526, 0962, 0963), desde sus datos, sin diferencias de contenido con su `.docx` | `-m referencias` (local, lee la bóveda) + `comparar.py` |
| PDF | Conversión con LibreOffice en la CI. Con Word, manual. Render de todas las páginas sin tablas cortadas ni títulos solos al pie | pytest + revisión |
| Interfaz | Flujo completo con teclado: elegir módulo, rellenar, avisos, vista previa y exportar. Estados vacíos. Bloques heredados que bloquean | pytest-qt |
| Actualizaciones | Las de Partes de salida (API, plan B, hosts) y el catálogo remoto con firma | pytest con red simulada |
| Capturas | `make capturas` con datos ficticios | `scripts/capturas.py` |
| Secretos | `scripts/comprobar_secretos.sh --todo` sobre todo el árbol: ningún dato del servidor de correo ni contraseñas (ADR-016). También se prueba que detecta casos de ejemplo | pytest + CI `Secretos` |

## Criterio de salida de la 1.0

- Las seis programaciones regeneradas sin diferencias de contenido.
- `verificar.py` y `validate.py` limpios.
- Prueba manual en Word (macOS y Windows): la parte incrustada sobrevive a abrir y guardar.
- Instalación desde el release en un equipo del centro (Windows portable incluido).
- Piloto con al menos un profesor que no sea CarlosFB, que hereda una programación.
