"""Enviar por correo (ADR-014), sin Qt: plantilla, destinatarios, tamaño, programa de correo de cada plataforma y la
reserva. Con el cliente de correo simulado de `conftest.py`: nunca se lanza osascript ni PowerShell ni se abre nada."""
import json
import plistlib
from email import message_from_bytes
from email.policy import default
from pathlib import Path
from urllib.parse import unquote

import pytest

from programaciones import correo
from programaciones.ajustes import ASUNTO_UNA


@pytest.fixture
def adjuntos(tmp_path):
    carpeta = tmp_path / "Programaciones 2030-2031"
    carpeta.mkdir()
    rutas = []
    for nombre in ("SEA 2 - 0991 - Módulo ficticio uno.docx", "SEA 2 - 0991 - Módulo ficticio uno.pdf"):
        r = carpeta / nombre
        r.write_bytes(b"ficticio " * 100)
        rutas.append(r)
    return rutas


@pytest.fixture
def borrador(adjuntos):
    return correo.Borrador(["jefatura@example.com", "departamento@example.com"],
                           "Programación didáctica — 0991 Módulo ficticio uno (2030-2031)",
                           "Hola:\n\nAdjunto «la programación» & <lo demás>.\n", adjuntos)


def test_separar_destinatarios():
    assert correo.separar("a@example.com, b@example.com; a@example.com  c") == (
        ["a@example.com", "b@example.com"], ["c"])
    assert correo.separar("") == ([], [])


def test_asunto_y_cuerpo_de_una_y_de_varias(tmp_path):
    archivos = [tmp_path / "SEA 2 - 0991 - Uno.docx", tmp_path / "SEA 2 - 0991 - Uno.pdf"]
    c = correo.campos(["0991 Módulo ficticio uno"], ["2030-2031"], archivos, "Profesora Ficticia Uno ")
    asunto, cuerpo = correo.asunto_y_cuerpo(c)
    assert asunto == "Programación didáctica — 0991 Módulo ficticio uno (2030-2031)"
    assert "la programación didáctica de 0991 Módulo ficticio uno" in cuerpo
    assert "- SEA 2 - 0991 - Uno.docx\n- SEA 2 - 0991 - Uno.pdf" in cuerpo and cuerpo.endswith("Profesora Ficticia Uno")
    varias = correo.campos(["0991 Uno", "0992 Dos", "0993 Tres"], ["2030-2031"] * 3, archivos, "")
    asunto, cuerpo = correo.asunto_y_cuerpo(varias)
    assert asunto == "Programaciones didácticas — 3 módulos (2030-2031)"
    assert "las programaciones didácticas de 3 módulos" in cuerpo


def test_la_plantilla_se_edita_en_ajustes_y_no_se_rompe(tmp_path):
    c = correo.campos(["0991 Uno"], ["2030-2031"], [], "")
    assert correo.asunto_y_cuerpo(c, "PD {modulo} · {otro}")[0] == "PD 0991 Uno · {otro}", "campo desconocido: tal cual"
    assert correo.asunto_y_cuerpo(c, "Llave suelta {")[0] == ASUNTO_UNA.format(**c), "llaves sueltas: la de la app"
    assert correo.asunto_y_cuerpo(c, "  ")[0] == ASUNTO_UNA.format(**c), "vacía: la de la app"


def test_tamano_y_limite(tmp_path):
    grande = tmp_path / "grande.pdf"
    with open(grande, "wb") as f:
        f.truncate(21 * 1024 * 1024)
    total = correo.tamano([grande, tmp_path / "no-existe.docx"])
    assert total == 21 * 1024 * 1024 and correo.supera_limite(total) and not correo.supera_limite(19 * 1024 * 1024)
    assert correo.texto_tamano(total) == "21,0 MB" and correo.texto_tamano(2048) == "2 KB"


def test_programa_de_correo_por_defecto_en_macos(tmp_path):
    plist = tmp_path / "launchservices.plist"
    plist.write_bytes(plistlib.dumps({"LSHandlers": [
        {"LSHandlerURLScheme": "https", "LSHandlerRoleAll": "com.example.navegador"},
        {"LSHandlerURLScheme": "mailto", "LSHandlerRoleAll": "com.microsoft.outlook"}]}, fmt=plistlib.FMT_BINARY))
    assert correo.cliente_macos(plist) == "outlook"
    plist.write_bytes(plistlib.dumps({"LSHandlers": []}))
    assert correo.cliente_macos(plist) == "mail", "sin elegir: Mail, el de serie"
    assert correo.cliente_macos(tmp_path / "no-existe.plist") == "mail"


def test_orden_de_los_metodos_por_plataforma(monkeypatch):
    monkeypatch.setattr(correo, "cliente_macos", lambda: "outlook")
    assert correo.metodos("auto", "darwin") == ["outlook", "mailto"]
    assert correo.metodos("mail", "darwin") == ["mail", "mailto"]
    monkeypatch.setattr(correo, "hay_outlook_clasico", lambda: True)
    assert correo.metodos("auto", "win32") == ["outlook", "eml", "mailto"]
    assert correo.metodos("eml", "win32") == ["eml", "mailto"]
    monkeypatch.setattr(correo, "hay_outlook_clasico", lambda: False)
    assert correo.metodos("auto", "win32") == ["eml", "mailto"], "el nuevo Outlook no tiene COM: .eml"
    assert correo.metodos("auto", "linux") == ["mailto"]
    assert correo.metodos("mailto", "darwin") == ["mailto"]
    assert "adjuntarlos tú" in correo.que_se_abre("mailto")


def test_mail_en_macos_con_adjuntos_y_destinatarios(borrador, cliente_correo):
    r = correo.abrir_borrador(borrador, "mail", plataforma="darwin")
    assert r.metodo == "mail" and not r.manual and "Mail" in r.texto
    (orden,) = cliente_correo.ordenes
    assert orden[:3] == ["osascript", "-e", correo.APPLESCRIPT_MAIL]
    asunto, cuerpo, para, adjuntos = orden[3:]
    assert asunto == borrador.asunto and cuerpo == borrador.cuerpo
    assert para.split("\n") == borrador.para
    assert adjuntos.split("\n") == [str(a.resolve()) for a in borrador.adjuntos]
    assert borrador.asunto not in correo.APPLESCRIPT_MAIL, "los datos van como argumentos, no dentro del script"
    assert not cliente_correo.abiertos


def test_outlook_en_macos_con_el_cuerpo_en_html(borrador, cliente_correo):
    r = correo.abrir_borrador(borrador, "outlook", plataforma="darwin")
    assert r.metodo == "outlook"
    orden = cliente_correo.ordenes[0]
    assert orden[2] == correo.APPLESCRIPT_OUTLOOK
    assert orden[4] == "Hola:<br><br>Adjunto «la programación» &amp; &lt;lo demás&gt;.<br>"


def test_outlook_clasico_en_windows_por_com(borrador, cliente_correo, monkeypatch):
    leidos = []

    def ejecutar(orden, tiempo_max=0):
        cliente_correo.ordenes.append(orden)
        ruta = orden[-1].split("-LiteralPath '", 1)[1].split("'", 1)[0]
        leidos.append(json.loads(Path(ruta).read_text(encoding="utf-8")))

    monkeypatch.setattr(correo, "_ejecutar", ejecutar)
    monkeypatch.setattr(correo, "hay_outlook_clasico", lambda: True)
    r = correo.abrir_borrador(borrador, "auto", plataforma="win32")
    assert r.metodo == "outlook" and cliente_correo.ordenes[0][0] == "powershell"
    assert "Outlook.Application" in cliente_correo.ordenes[0][-1] and "Display" in cliente_correo.ordenes[0][-1]
    assert borrador.asunto not in cliente_correo.ordenes[0][-1], "los datos van en el JSON, no en la orden"
    assert leidos == [{"para": borrador.para, "asunto": borrador.asunto, "cuerpo": borrador.cuerpo,
                       "adjuntos": [str(a.resolve()) for a in borrador.adjuntos]}]


def test_si_outlook_falla_en_windows_un_eml_sin_enviar(borrador, cliente_correo, monkeypatch, tmp_path):
    monkeypatch.setattr(correo, "hay_outlook_clasico", lambda: True)
    cliente_correo.fallan.add("powershell")
    r = correo.abrir_borrador(borrador, "auto", carpeta_eml=tmp_path / "correo", plataforma="win32")
    assert r.metodo == "eml" and r.errores and "Outlook" in r.errores[0]
    (eml,) = cliente_correo.abiertos
    m = message_from_bytes(Path(eml).read_bytes(), policy=default)
    assert m["X-Unsent"] == "1" and m["Subject"] == borrador.asunto
    assert m["To"] == "jefatura@example.com, departamento@example.com"
    assert [a.get_filename() for a in m.iter_attachments()] == [a.name for a in borrador.adjuntos]
    assert next(m.iter_attachments()).get_content() == borrador.adjuntos[0].read_bytes()


def test_reserva_mailto_con_la_carpeta_y_aviso_de_adjuntar_a_mano(borrador, cliente_correo):
    cliente_correo.fallan.add("osascript")
    r = correo.abrir_borrador(borrador, "mail", plataforma="darwin")
    assert r.metodo == "mailto" and r.manual and "adjúntalos a mano" in r.texto and r.errores
    carpeta, enlace = cliente_correo.abiertos
    assert carpeta == str(borrador.adjuntos[0].resolve().parent)
    assert enlace.startswith("mailto:jefatura@example.com,departamento@example.com?subject=")
    assert unquote(enlace.split("subject=")[1].split("&body=")[0]) == borrador.asunto
    assert unquote(enlace.split("&body=")[1]) == borrador.cuerpo


def test_sin_adjuntos_o_sin_nada_que_funcione(borrador, cliente_correo, tmp_path):
    falta = correo.Borrador([], "Asunto", "Cuerpo", [tmp_path / "no-existe.docx"])
    with pytest.raises(correo.ErrorCorreo, match="no-existe.docx"):
        correo.abrir_borrador(falta, "mail", plataforma="darwin")
    assert not cliente_correo.ordenes
    cliente_correo.fallan |= {"osascript", "abrir"}
    with pytest.raises(correo.ErrorCorreo):
        correo.abrir_borrador(borrador, "mail", plataforma="darwin")
