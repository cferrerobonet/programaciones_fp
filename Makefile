.PHONY: help venv ganchos run test test-rapido lint qa catalogo plantilla icono limpiar

# El entorno vive FUERA del repositorio: iCloud duplica los binarios y deja a Qt
# sin complementos (lección de Guardias de patio). Copia del Makefile de Partes de salida.
VENV := $(HOME)/.venvs/programaciones
PY := $(VENV)/bin/python
export QT_QPA_PLATFORM ?= offscreen

help:
	@echo "Programaciones — órdenes"
	@echo "  make venv        Crear o actualizar el entorno ($(VENV))"
	@echo "  make ganchos     Activar los ganchos de git del repositorio (.githooks)"
	@echo "  make run         Abrir la aplicación desde el código"
	@echo "  make test        Suite completa (dominio e interfaz sin pantalla)"
	@echo "  make test-rapido Sin interfaz"
	@echo "  make lint        ruff"
	@echo "  make qa          lint + catálogo + plantilla + suite, con la salida completa en /tmp/programaciones-qa-*.log"
	@echo "  make catalogo    Comprobar el catálogo"
	@echo "  make plantilla   Comprobar la plantilla con marcas"
	@echo "  make icono       Rehacer imagenes/icono.ico (y .icns en macOS) desde imagenes/icono.png"
	@echo "  make limpiar     Borrar cachés"
	@echo "  Compilar: solo en GitHub (etiqueta vX.Y.Z o Actions → Compilar). En local no se compila."

venv:
	@test -x "$(PY)" || python3.11 -m venv "$(VENV)"
	$(PY) -m pip install --upgrade pip setuptools
	$(PY) -m pip install -r requirements-dev.txt

ganchos:
	git config core.hooksPath .githooks
	chmod +x .githooks/* scripts/*.sh scripts/build/*.sh
	@echo "Ganchos activos: .githooks/pre-commit y pre-push"

run:
	QT_QPA_PLATFORM= $(PY) -B src/main.py

test:
	$(PY) -m pytest

test-rapido:
	$(PY) -m pytest -m "not ui"

lint:
	$(PY) -m ruff check scripts src tests

qa:
	scripts/qa.sh todo

catalogo:
	$(PY) scripts/catalogo.py comprobar

plantilla:
	$(PY) scripts/plantilla.py comprobar

icono:
	PY="$(PY)" scripts/crear_icono.sh

limpiar:
	rm -rf build dist Output *.dmg test-results imagenes/*.iconset .ruff_cache
	find . -path ./.git -prune -o -name "__pycache__" -type d -print0 | xargs -0 rm -rf
