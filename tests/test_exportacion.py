"""Exportar (RF-07) y vista previa sin Qt, con datos ficticios. El PDF se simula: lo prueba test_pdf.py."""
from pathlib import Path

import pytest

from programaciones import contenido, documento, exportacion, importar_docx, incrustar, pdf, validacion


@pytest.fixture
def pdf_falso(monkeypatch):
    hechos = []

    def falso(docx, ruta, motor="auto", tiempo_max=0):
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(b"%PDF-1.4 ficticio")
        hechos.append((ruta, motor))
        return ruta

    monkeypatch.setattr(pdf, "exportar_pdf", falso)
    return hechos


def test_exporta_word_y_pdf_con_el_nombre_normalizado(prog, cat, curso, tmp_path, pdf_falso):
    pasos = []
    res = exportacion.exportar(prog, cat, curso, tmp_path, ["docx", "pdf"], documento.Opciones(), "libreoffice",
                               lambda *a: pasos.append(a))
    nombre = "SEA 2 - 0517 - Procesos en instalaciones de infraestructuras comunes de telecomunicaciones"
    assert [p.name for p in res.archivos] == [f"{nombre}.docx", f"{nombre}.pdf"]
    assert not res.error_pdf and pdf_falso[0][1] == "libreoffice"
    assert [p[0] for p in pasos] == [0, 1, 2, 3] and pasos[-1][2] == "Hecho"
    # Volver a abrirlo: el Word lleva dentro todos los datos (RF-08)
    datos = res.archivos[0].read_bytes()
    assert incrustar.leer(datos).programacion == prog
    assert importar_docx.importar(datos, cat, res.archivos[0].name) == prog


def test_solo_word_sin_pdf(prog, cat, curso, tmp_path, pdf_falso):
    res = exportacion.exportar(prog, cat, curso, tmp_path, ["docx"], documento.Opciones())
    assert [p.suffix for p in res.archivos] == [".docx"] and not pdf_falso


def test_sin_word_ni_libreoffice_queda_el_docx_y_un_aviso(prog, cat, curso, tmp_path, monkeypatch):
    def sin_motor(*_a, **_k):
        raise pdf.ErrorPDF("No hay Word ni LibreOffice en este equipo")

    monkeypatch.setattr(pdf, "exportar_pdf", sin_motor)
    res = exportacion.exportar(prog, cat, curso, tmp_path, ["docx", "pdf"], documento.Opciones())
    assert [p.suffix for p in res.archivos] == [".docx"] and "LibreOffice" in res.error_pdf


def test_un_documento_que_no_pasa_las_comprobaciones_no_se_escribe(prog, cat, curso, tmp_path, monkeypatch):
    monkeypatch.setattr(exportacion, "problemas", lambda _d: ["falta el índice automático"])
    with pytest.raises(exportacion.DocumentoConErrores):
        exportacion.exportar(prog, cat, curso, tmp_path, ["docx"], documento.Opciones())
    assert not list(tmp_path.iterdir())


def test_el_documento_generado_pasa_las_comprobaciones(prog, cat, curso):
    assert exportacion.problemas(documento.generar(prog, cat, curso)) == []


def test_vista_previa_con_borrador(prog, cat, curso, tmp_path, monkeypatch):
    generados = []
    original = documento.generar
    monkeypatch.setattr(documento, "generar", lambda *a, **k: generados.append(a[3]) or original(*a, **k))
    monkeypatch.setattr(pdf, "exportar_pdf", lambda docx, ruta, motor="auto": Path(ruta))
    ruta = exportacion.vista_previa(prog, cat, curso, documento.Opciones(correo_pie="dep@example.com"), tmp_path)
    assert ruta.suffix == ".pdf" and generados[0].borrador and generados[0].correo_pie == "dep@example.com"


# Curso escolar sin dar de alta: «pendiente», nunca fechas inventadas
def test_sin_curso_escolar_las_fechas_salen_pendientes(prog, cat):
    docx = documento.generar(prog, cat, None, documento.Opciones(borrador=True))
    texto = " ".join(e.texto for e in contenido.secciones(contenido.leer(docx))["9"])
    assert texto.count(documento.PENDIENTE) >= 6
    assert "Periodos de formación en empresa: pendiente" in " ".join(
        e.texto for e in contenido.secciones(contenido.leer(docx))["9.1"])


def test_sin_curso_escolar_la_definitiva_queda_bloqueada(prog, cat):
    prog["bloques"] = {b: "confirmado" for b in prog["bloques"]}
    ficha = cat.ficha("SEA", "0517", 2)
    assert not validacion.bloquean(validacion.validar(prog, ficha))
    avisos = validacion.validar(prog, ficha, curso_pendiente="fechas del curso 2030-2031")
    assert [a.id for a in avisos if a.gravedad == validacion.ROJA] == ["V-11"]
