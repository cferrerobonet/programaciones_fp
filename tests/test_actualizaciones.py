"""Actualizaciones (copia de las pruebas de Partes de salida): sha256 contra el digest de la API de releases, timeout,
plan B por la web y comparación de versiones. Sin red (mock)."""

import hashlib
import io
import json

import pytest

from programaciones import actualizaciones as act

VERSION = "9.9.9"
NOMBRE = f"Programaciones-{VERSION}-Windows-Setup.exe"
URL = f"{act.DESCARGAS_WEB}/v{VERSION}/{NOMBRE}"
API_TAG = f"https://api.github.com/repos/{act.REPO}/releases/tags/v{VERSION}"
CONTENIDO = b"instalador ficticio " * 5000


class _Respuesta(io.BytesIO):
    def __init__(self, datos: bytes, url: str):
        super().__init__(datos)
        self.headers = {"Content-Length": str(len(datos))}
        self._url = url

    def geturl(self):
        return self._url


@pytest.fixture
def red(monkeypatch):
    """Sustituye urlopen: la API da el digest que se pida y la descarga, el contenido que se pida."""
    estado = {"digest": "sha256:" + hashlib.sha256(CONTENIDO).hexdigest(), "contenido": CONTENIDO, "pedidas": []}

    def urlopen(req, timeout=None, context=None):
        url = req.full_url if hasattr(req, "full_url") else req
        estado["pedidas"].append((url, timeout))
        if url == API_TAG:
            assets = [{"name": NOMBRE, "browser_download_url": URL}]
            if estado["digest"] is not None:
                assets[0]["digest"] = estado["digest"]
            return _Respuesta(json.dumps({"tag_name": f"v{VERSION}", "assets": assets}).encode(), url)
        if url == URL:
            return _Respuesta(estado["contenido"], url)
        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr(act.urllib.request, "urlopen", urlopen)
    return estado


def test_digest_del_asset_lee_la_api_de_releases(red):
    assert act.digest_del_asset(URL) == hashlib.sha256(CONTENIDO).hexdigest()


def test_digest_del_asset_sin_digest_o_con_formato_raro_es_vacio(red):
    red["digest"] = None
    assert act.digest_del_asset(URL) == ""
    red["digest"] = "md5:abc"
    assert act.digest_del_asset(URL) == ""


def test_digest_de_una_url_ajena_no_consulta_nada(red):
    assert act.digest_del_asset("https://ejemplo.example.com/v1/x.exe") == ""
    assert red["pedidas"] == []


def test_descarga_correcta_se_guarda_y_avanza(red, tmp_path):
    destino = tmp_path / NOMBRE
    avances = []
    assert act.descargar_verificado(URL, destino, avances.append) == destino
    assert destino.read_bytes() == CONTENIDO
    assert avances and avances[-1] == 100


def test_descarga_manipulada_se_borra_y_no_se_abre(red, tmp_path):
    red["contenido"] = CONTENIDO + b"cambiado"
    destino = tmp_path / NOMBRE
    with pytest.raises(act.DescargaNoVerificada, match="no coincide"):
        act.descargar_verificado(URL, destino)
    assert not destino.exists()


def test_sin_digest_no_se_descarga(red, tmp_path):
    red["digest"] = None
    destino = tmp_path / NOMBRE
    with pytest.raises(act.DescargaNoVerificada, match="comprobar"):
        act.descargar_verificado(URL, destino)
    assert not destino.exists()
    assert [u for u, _ in red["pedidas"]] == [API_TAG]


def test_toda_peticion_lleva_timeout(red, tmp_path):
    act.descargar_verificado(URL, tmp_path / NOMBRE)
    assert red["pedidas"] and all(t for _, t in red["pedidas"])


def test_url_no_de_confianza_se_rechaza(red, tmp_path):
    with pytest.raises(ValueError):
        act.descargar_verificado("http://github.com/x/releases/download/v1/x.exe", tmp_path / "x.exe")
    assert red["pedidas"] == []


@pytest.mark.ui
def test_el_dialogo_no_abre_un_instalador_manipulado(qtbot, red, tmp_path):
    from programaciones.ui.dialogos import _Descargador

    red["contenido"] = CONTENIDO + b"cambiado"
    hilo = _Descargador(URL, tmp_path / NOMBRE)
    listos, errores = [], []
    hilo.listo.connect(listos.append)
    hilo.error.connect(errores.append)
    hilo.run()  # en este hilo: sin red ni espera
    assert listos == []
    assert errores and "no coincide" in errores[0]
    assert not (tmp_path / NOMBRE).exists()


def test_comparacion_de_versiones():
    assert act.es_mas_nueva("0.2.0", "0.1.0") and act.es_mas_nueva("1.0.0", "0.9.9")
    assert not act.es_mas_nueva("0.1.0", "0.1.0") and not act.es_mas_nueva("v0.2", "0.1.0")


def test_plan_b_por_la_web_arma_el_nombre_del_instalador(monkeypatch):
    """Sin API (límite de 60 consultas por hora en el centro), la web redirige a la etiqueta y el nombre es el fijo."""

    def urlopen(req, timeout=None, context=None):
        url = req.full_url
        if url == act.RELEASES_URL:
            raise OSError("límite de la API")
        assert url == act.RELEASES_WEB
        return _Respuesta(b"", f"https://github.com/{act.REPO}/releases/tag/v{VERSION}")

    monkeypatch.setattr(act.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(act.platform, "system", lambda: "Windows")
    assert act.ultima_version() == (VERSION, URL, "")


def test_solo_hosts_de_github():
    assert act.url_de_confianza(URL)
    assert not act.url_de_confianza("https://example.com/x.exe")
    assert not act.url_de_confianza(URL.replace("https", "http"))


def test_una_012_instalada_detecta_la_020_publicada_como_normal(monkeypatch):
    """ADR-026: la app pregunta a /releases/latest, que solo devuelve versiones normales. Con la 0.2.0 publicada así,
    una 0.1.2 avisa (respuesta de la API simulada, sin red)."""
    pedidas = []

    def urlopen(req, timeout=None, context=None):
        url = req.full_url if hasattr(req, "full_url") else req
        pedidas.append(url)
        assert url == act.RELEASES_URL, url
        datos = {"tag_name": "v0.2.0", "prerelease": False, "body": "### Añadido\n- Enviar por correo.",
                 "assets": [{"name": f"Programaciones-0.2.0-{s}", "browser_download_url":
                             f"{act.DESCARGAS_WEB}/v0.2.0/Programaciones-0.2.0-{s}"}
                            for s in ("macOS-arm64.dmg", "Windows-Setup.exe", "Windows-Portable.zip")]}
        return _Respuesta(json.dumps(datos).encode(), url)

    class Hilo:   # comprobar() lanza un hilo: aquí, en el momento
        def __init__(self, target, daemon=True):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(act.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(act, "Thread", Hilo)
    avisos = []
    act.comprobar("0.1.2", lambda v, url, notas: avisos.append((v, url, notas)))
    assert pedidas == [act.RELEASES_URL] and act.RELEASES_URL.endswith("/releases/latest")
    assert avisos and avisos[0][0] == "0.2.0" and "Enviar por correo" in avisos[0][2]
    avisos.clear()
    act.comprobar("0.2.0", lambda v, url, notas: avisos.append(v))
    assert not avisos, "la 0.2.0 ya está al día"
