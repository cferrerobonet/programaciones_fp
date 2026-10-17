---
paths:
  - "catalogo/**"
  - "scripts/catalogo.py"
  - "src/programaciones/esquemas/**"
  - ".github/workflows/vigia.yml"
---

# Catálogo

Fuentes, reglas de lectura y vigía: `docs/CATALOGO_Y_FUENTES.md`. Formato: `docs/MODELO_DE_DATOS.md` §1.

- **`catalogo/` no se edita a mano.** Todo sale de `scripts/catalogo.py construir <SIGLA>|todo` (BOE y DOGV, caché fuera de iCloud). Si un dato está mal, se arregla el lector o la receta (`CICLOS`, `COMUNES`), nunca el YAML.
- **Sin datos, no se implementa.** Lo que la fuente no dice o dice de forma ambigua queda con `pendiente` y su motivo, y va a `docs/PENDIENTE.md`. Las erratas del BOE se guardan tal cual: el texto literal y, si la numeración no sigue, `n_boe` o `letra_boe`.
- **Cierre de cada cambio:**
  - `catalogo.py comprobar` limpio (`--red` para los enlaces).
  - `pytest`.
  - En local, `PROGRAMACIONES_REFERENCIAS=…/01 DOCENCIA/FP pytest -m referencias`: los RA de las seis programaciones, idénticos.
- **Las programaciones de la bóveda se leen en local y nunca se copian al repositorio**, ni siquiera un fragmento en un test (solo posición: módulo, RA y letra).
- Un módulo con el mismo código en dos títulos va en un solo archivo si el texto coincide; si no, uno por título (`0237-IT`, `0237-IEA`).
- Esquema o formato nuevo: se cambian a la vez `src/programaciones/esquemas/`, `docs/MODELO_DE_DATOS.md` y `tests/test_esquemas.py`; un cambio incompatible sube `catalogo/N`.
