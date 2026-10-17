---
paths:
  - "tests/**"
  - "pyproject.toml"
  - "requirements-dev.txt"
  - "scripts/qa.sh"
---

# Tests

- Intérprete: `~/.venvs/programaciones/bin/python -m pytest` (venv fuera de iCloud) o `scripts/qa.sh` (skill `tests`). La configuración, en `pyproject.toml`; `tests/conftest.py` evita `__pycache__`, pone `QT_QPA_PLATFORM=offscreen` y da a cada prueba su carpeta de datos (`PROGRAMACIONES_DATOS`).
- Marcador `ui`: pytest-qt sin pantalla (fixture `contexto`). Una prueba que pueda tocar la red, Word o el navegador los sustituye con `monkeypatch`: nunca descarga ni abre nada de verdad.
- **Datos ficticios siempre:** RA, módulos y documentos inventados (códigos 099x, `example.com`). Los `.docx` de prueba se crean dentro de la prueba, en `tmp_path`.
- Marcador `referencias`: lee la bóveda en local con `PROGRAMACIONES_REFERENCIAS` y se salta si no está (en la CI no está).
- **Una prueba de regresión debe fallar al revertir el arreglo:** comprobarlo y decirlo.
- Una prueba que vigila un invariante (catálogo limpio, códigos entre comillas, ningún dato sin fuente) no se relaja: se corrige el código o el dato.
- No citar recuentos de tests en ningún documento: cambian con cada cambio.
