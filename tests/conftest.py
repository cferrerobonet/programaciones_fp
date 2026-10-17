"""Pruebas de Programaciones. Repositorio público: solo datos ficticios (los RA de ejemplo, las unidades, los
profesores y los textos del profesor son inventados; el catálogo es el del repositorio, que es público)."""
import copy
import os
import sys

sys.dont_write_bytecode = True  # sin __pycache__ en iCloud
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # la interfaz, sin pantalla (antes de importar Qt)

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def datos(tmp_path_factory, monkeypatch):
    """Cada prueba, con su carpeta de datos (ajustes y registro): nunca la del equipo de desarrollo. Fuera de
    `tmp_path`, que algunas pruebas esperan vacío."""
    carpeta = tmp_path_factory.mktemp("datos")
    monkeypatch.setenv("PROGRAMACIONES_DATOS", str(carpeta))
    return carpeta


class ClienteSimulado:
    """Lo que la app habría lanzado (osascript, PowerShell) o abierto (carpetas, .eml, mailto): nunca se ejecuta."""

    def __init__(self):
        self.ordenes: list[list[str]] = []
        self.abiertos: list[str] = []
        self.fallan: set[str] = set()   # «osascript», «powershell» o «abrir»: ese paso falla como fallaría de verdad

    def ejecutar(self, orden, tiempo_max=0):
        from programaciones.correo import ErrorCorreo

        self.ordenes.append(list(orden))
        if orden[0] in self.fallan:
            raise ErrorCorreo(f"{orden[0]} ha fallado (simulado)")

    def abrir(self, destino):
        from programaciones.correo import ErrorCorreo

        self.abiertos.append(destino)
        if "abrir" in self.fallan:
            raise ErrorCorreo("no se abre (simulado)")


@pytest.fixture(autouse=True)
def cliente_correo(monkeypatch):
    """Ninguna prueba abre un programa de correo, una carpeta ni un enlace de verdad (tampoco en la CI)."""
    from programaciones import correo

    cliente = ClienteSimulado()
    monkeypatch.setattr(correo, "_ejecutar", cliente.ejecutar)
    monkeypatch.setattr(correo, "_abrir", cliente.abrir)
    return cliente


@pytest.fixture(autouse=True)
def papelera(monkeypatch, tmp_path_factory):
    """La papelera del sistema, simulada: lo que la app borra se mueve aquí (nunca a la papelera del equipo)."""
    import shutil

    carpeta = tmp_path_factory.mktemp("papelera")
    movidos = []

    def mover(ruta):
        destino = carpeta / f"{len(movidos)}-{ruta.name}"
        shutil.move(str(ruta), destino)
        movidos.append(destino)
        return True

    monkeypatch.setattr("programaciones.ui.gestion.papelera", mover)
    return movidos

# Curso escolar ficticio (fechas inventadas con la forma de las reales)
CURSO = {
    "evaluaciones": {"inicial": "2030-09-30", "primera": "2030-11-22", "segunda": "2031-02-28", "tercera": "2031-05-30"},
    "ordinaria": {"desde": "2031-06-02", "hasta": "2031-06-05"},
    "extraordinaria_desde": "2031-06-16",
    "formacion_empresa": {"GS": {
        1: [{"jornada": 8, "dias": 20, "desde": "2031-05-05", "hasta": "2031-05-30"},
            {"jornada": 7, "dias": 23, "desde": "2031-04-30", "hasta": "2031-05-30"}],
        2: [{"jornada": 8, "dias": 43, "desde": "2031-03-03", "hasta": "2031-05-30"},
            {"jornada": 7, "dias": 49, "desde": "2031-02-26", "hasta": "2031-06-05"}]}},
}


def programacion_ficticia(ciclo="SEA", curso=2, modulo="0517"):
    """Programación de 0517 con datos del profesor inventados y la estructura de horas que documenta
    docs/MODELO_DE_DATOS.md §3 (103 h de centro y 63 de empresa)."""
    from programaciones import programacion
    from programaciones.catalogo import Catalogo
    cat = Catalogo()
    p = programacion.nueva(ciclo, curso, modulo, "2030-2031", cat.version, "2026-10-06")
    p["profesorado"] = ["Profesora Ficticia Uno"]
    # horas de cada elemento como en el ejemplo de PIICT de MODELO_DE_DATOS (24, 16, 12, 16…); el reparto entre
    # unidades es inventado
    els = [("e0", "E", "EXAMEN 0", [6], [4]), ("e1", "E", "EXAMEN 1", [1, 2], [12, 12]),
           ("e2", "P", "PRÁCTICA 1", [3, 4, 6], [7]), ("e3", "E", "EXAMEN 2", [1, 2], [8, 8]),
           ("e4", "P", "PRÁCTICA 2", [2], [5]), ("e5", "P", "PRÁCTICA 3", [2, 4], [4]),
           ("e6", "E", "EXAMEN 3", [1, 2], [5, 4, 3]), ("e7", "P", "PRÁCTICA 4", [3, 4, 6], [6]),
           ("e8", "E", "EXAMEN 4", [1, 2], [9, 7]), ("e9", "P", "PRÁCTICA 5", [3, 4, 6], [9])]
    k = 0
    for eid, tipo, nombre, ras, horas in els:
        p["elementos"].append({"id": eid, "tipo": tipo, "nombre": nombre, "ra": ras})
        for h in horas:
            k += 1
            trim = 1 if k <= 7 else 2
            p["unidades"].append({"id": f"u{k}", "titulo": f"UD{k:02d}. Unidad ficticia {k}", "horas": h,
                                  "trimestre": trim, "elemento": eid})
    p["empresa"] = {"2": 12, "3": 13, "4": 13, "5": 13, "6": 12}
    p["centro_ajustado"] = {"3": 8, "4": 10, "6": 10}
    p["ra_competencias"] = {"1": ["a", "d"], "2": ["a", "b", "d"], "3": ["e", "f"], "4": ["h", "k"], "5": ["j"],
                            "6": ["f", "h"]}
    p["metodologia"] = [{"texto": "Párrafo ficticio de metodología con el **cuaderno ficticio** y el Real Decreto "
                                  "1127/2010, de 10 de septiembre."}]
    p["recursos"] = [{"texto": "Recurso ficticio uno.", "nivel": 0}, {"texto": "Subrecurso ficticio.", "nivel": 1}]
    p["espacios"] = [{"texto": "**Aula ficticia** con material inventado.", "nivel": 0}]
    p["notas_tabla4"] = [{"texto": "Nota ficticia de la tabla 4."}]
    return p


@pytest.fixture
def prog():
    return programacion_ficticia()


@pytest.fixture
def curso():
    return copy.deepcopy(CURSO)


@pytest.fixture(scope="session")
def cat():
    from programaciones.catalogo import Catalogo
    return Catalogo()


@pytest.fixture
def contexto(qapp, datos, cat):
    """Aplicación preparada: estilo de la familia y contexto con el catálogo del repositorio."""
    from programaciones.contexto import Contexto
    from programaciones.ui import estilo

    estilo.cargar_fuentes()
    estilo.aplicar(qapp)
    return Contexto(datos, catalogo=cat)


def programacion_minima(cat, sigla, curso, modulo, curso_escolar="2026-2027"):
    """Programación válida y completa de cualquier módulo, con datos del profesor inventados: un elemento con todos
    los RA y una unidad por trimestre que suman las horas del módulo; sin empresa."""
    from programaciones import documento, programacion
    ficha = cat.ficha(sigla, modulo, curso)
    p = programacion.nueva(sigla, curso, modulo, curso_escolar, cat.version, documento.metadatos_plantilla()["version"])
    p["profesorado"] = ["Profesora Ficticia Uno"]
    p["elementos"] = [{"id": "e1", "tipo": "E", "nombre": "EXAMEN FICTICIO", "ra": ficha.numeros_ra}]
    h = ficha.horas
    for t, horas in enumerate((h // 3, h // 3, h - 2 * (h // 3)), start=1):
        p["unidades"].append({"id": f"u{t}", "titulo": f"UD0{t}. Unidad ficticia", "horas": horas, "trimestre": t,
                              "elemento": "e1"})
    letras = ficha.competencias_modulo or [c["letra"] for c in cat.ciclo(sigla)["competencias"]]
    p["ra_competencias"] = {str(n): [letras[0]] for n in ficha.numeros_ra}
    p["bloques"] = {b: "confirmado" for b in p["bloques"]}
    return p


@pytest.fixture
def pdf_falso(monkeypatch, tmp_path_factory):
    """Un PDF de verdad (una página, hecho con QPdfWriter) que se copia donde la app lo pide."""
    import shutil
    from pathlib import Path

    from PyQt6.QtGui import QPainter, QPdfWriter

    from programaciones import pdf

    modelo = tmp_path_factory.mktemp("pdf") / "modelo.pdf"
    escritor = QPdfWriter(str(modelo))
    p = QPainter(escritor)
    p.drawText(100, 100, "BORRADOR")
    p.end()
    del p, escritor
    hechos = []

    def falso(docx, ruta, motor="auto", tiempo_max=0):
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(modelo, ruta)
        hechos.append((ruta, motor, docx))
        return ruta

    monkeypatch.setattr(pdf, "exportar_pdf", falso)
    return hechos
