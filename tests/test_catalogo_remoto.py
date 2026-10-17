"""Catálogo publicado y firmado (F5, ADR-027): versión, paquete, firma y descarga en la app. Sin red: un servidor falso
sirve lo que `scripts/catalogo.py publicar` escribe, firmado con una clave de prueba que se crea aquí (nunca la de
verdad, que solo está en un secreto de GitHub)."""
import base64
import datetime as dt
import gzip
import io
import json
import shutil
import urllib.error

import pytest
import yaml
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

import catalogo as receta
from programaciones import catalogo_remoto as cr
from programaciones import firma
from programaciones.catalogo import Catalogo


def _clave():
    k = Ed25519PrivateKey.generate()
    priv = base64.b64encode(k.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())).decode()
    return priv, k.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)


@pytest.fixture
def clave(monkeypatch):
    """Clave de prueba: la app la toma como la suya mientras dura la prueba."""
    priv, pub = _clave()
    monkeypatch.setattr(firma, "clave_publica", lambda: pub)
    return priv


def copia_del_catalogo(destino):
    shutil.copytree(Catalogo().carpeta, destino, ignore=shutil.ignore_patterns("vigia.yaml"))
    return destino


def cambiar_criterio(carpeta, modulo="0517", n=3, letra="b", texto="Se ha cambiado un criterio (ficticio).",
                     hoy="2030-01-15"):
    p = carpeta / "modulos" / f"{modulo}.yaml"
    m = yaml.safe_load(p.read_text(encoding="utf-8"))
    crit = next(c for c in next(r for r in m["ra"] if r["n"] == n)["criterios"] if c["letra"] == letra)
    crit["texto"]["es"] = texto
    crit.pop("corregido", None)
    crit.pop("correccion", None)
    receta.escribir_yaml(p, m)
    return receta.actualizar_version(carpeta, hoy)


class Servidor:
    """raw.githubusercontent.com falso: sirve la carpeta de la rama catalogo-publicado y cuenta las peticiones."""

    def __init__(self, carpeta):
        self.carpeta = carpeta
        self.pedidas = []
        self.caido = False

    def __call__(self, url, timeout=None):
        assert cr.url_permitida(url), url
        self.pedidas.append(url)
        if self.caido:
            raise urllib.error.URLError("sin red (simulado)")
        p = self.carpeta / url[len(cr.URL_BASE):]
        if not p.is_file():
            raise urllib.error.HTTPError(url, 404, "no está", {}, None)
        return io.BytesIO(p.read_bytes())


@pytest.fixture
def publicado(tmp_path, clave):
    """Rama catalogo-publicado con la versión de ahora (V0) y, encima, una V1 con un criterio cambiado."""
    origen = copia_del_catalogo(tmp_path / "origen")
    rama = tmp_path / "rama"
    v0 = receta.publicar(rama, origen, clave=clave)
    v1 = cambiar_criterio(origen)
    assert receta.publicar(rama, origen, clave=clave) == v1
    return {"rama": rama, "v0": v0, "v1": v1, "origen": origen, "clave": clave}


# ---------------------------------------------------------------------------------------------------------------------
# Versión del catálogo (catalogo/version.yaml)
# ---------------------------------------------------------------------------------------------------------------------
def test_el_catalogo_del_repositorio_tiene_su_version_al_dia():
    cat = Catalogo()
    meta = yaml.safe_load((cat.carpeta / "version.yaml").read_text(encoding="utf-8"))
    assert meta["version"] == cat.version and meta["fecha"] == cat.fecha
    assert meta["huella"] == cr.huella_contenido(cr.archivos(cat.carpeta)), "catalogo.py version"


def test_version_nueva_solo_si_cambia_el_contenido(tmp_path):
    c = copia_del_catalogo(tmp_path / "c")
    antes = Catalogo(c).version
    assert receta.actualizar_version(c, "2030-01-15") == antes, "sin cambios, la misma versión"
    assert cambiar_criterio(c, hoy="2030-01-15") == "2030.01.15"
    assert cambiar_criterio(c, texto="Otro cambio ficticio.", hoy="2030-01-15") == "2030.01.15.1"
    assert cambiar_criterio(c, texto="Y otro.", hoy="2030-01-15") == "2030.01.15.2"
    assert receta.comprobar(c) == []


def test_comprobar_detecta_un_cambio_sin_version(tmp_path):
    c = copia_del_catalogo(tmp_path / "c")
    p = c / "modulos" / "0517.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace("Se han", "Se han (ficticio)", 1), encoding="utf-8")
    assert any("version.yaml: el catálogo ha cambiado" in e for e in receta.comprobar(c))


def test_volver_a_leer_lo_mismo_otro_dia_no_reescribe_nada(tmp_path):
    """Solo cambian las fechas de comprobación: el archivo no se toca y la versión no sube (el vigía no ve nada)."""
    p = tmp_path / "modulo.yaml"
    datos = {"id": "0999", "ra": [{"n": 1}], "fuente": {"huella": "sha256:x", "comprobado": "2026-10-17"}}
    receta.escribir_yaml(p, datos)
    texto = p.read_text(encoding="utf-8")
    receta.escribir_yaml(p, {**datos, "fuente": {**datos["fuente"], "comprobado": "2030-01-15"}})
    assert p.read_text(encoding="utf-8") == texto
    receta.escribir_yaml(p, {**datos, "ra": [{"n": 2}], "fuente": {**datos["fuente"], "comprobado": "2030-01-15"}})
    assert "2030-01-15" in p.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------------------------------------------------
# Publicar y firmar (scripts/catalogo.py publicar, en catalogo.yml)
# ---------------------------------------------------------------------------------------------------------------------
def test_publicar_firma_y_verificar_lo_comprueba(publicado):
    rama = publicado["rama"]
    indice = json.loads((rama / "indice.json").read_text(encoding="utf-8"))
    d = indice["datos"]
    assert d["version"] == publicado["v1"] and d["anterior"] == publicado["v0"]
    assert set(d["versiones"]) == {publicado["v0"]}, "la anterior se conserva para comparar"
    assert "RA3 de 0517: criterio b) cambia" in d["novedades"]
    assert firma.verificar(d, indice["firma"]) and indice["clave"] == firma.id_clave(firma.clave_publica())
    assert receta.verificar(str(rama)) == publicado["v1"]
    assert publicado["clave"] not in (rama / "indice.json").read_text(encoding="utf-8")


def test_publicar_otra_vez_lo_mismo_no_hace_nada_y_sin_subir_la_version_para(publicado):
    rama, origen = publicado["rama"], publicado["origen"]
    assert receta.publicar(rama, origen, clave=publicado["clave"]) == ""
    p = origen / "modulos" / "0517.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace("Se han", "Se han (ficticio)", 1), encoding="utf-8")
    with pytest.raises(SystemExit, match="no está limpio"):
        receta.publicar(rama, origen, clave=publicado["clave"])


def test_publicar_encima_de_un_formato_anterior_no_lo_compara(publicado):
    """El publicado era catalogo/1 (antes de Grado Básico): la app nueva no lo entiende, así que no se compara."""
    rama, origen = publicado["rama"], publicado["origen"]
    indice = json.loads((rama / "indice.json").read_text(encoding="utf-8"))
    indice["datos"]["formato_catalogo"] = "catalogo/1"
    (rama / "indice.json").write_text(json.dumps(indice), encoding="utf-8")
    v2 = cambiar_criterio(origen, texto="Otro cambio ficticio.")
    assert receta.publicar(rama, origen, clave=publicado["clave"]) == v2
    d = json.loads((rama / "indice.json").read_text(encoding="utf-8"))["datos"]
    assert "formato nuevo" in d["novedades"] and d["formato_catalogo"] == receta.FORMATO


def test_publicar_sin_clave_o_con_otra_clave_para(tmp_path, clave, monkeypatch):
    origen = copia_del_catalogo(tmp_path / "origen")
    monkeypatch.delenv("CATALOGO_CLAVE", raising=False)
    with pytest.raises(SystemExit, match="Falta la clave"):
        receta.publicar(tmp_path / "rama", origen, clave="")
    with pytest.raises(SystemExit, match="no corresponde"):
        receta.publicar(tmp_path / "rama", origen, clave=_clave()[0])


def test_el_paquete_sale_igual_cada_vez(tmp_path):
    c = copia_del_catalogo(tmp_path / "c")
    assert cr.empaquetar(c) == cr.empaquetar(c)


# ---------------------------------------------------------------------------------------------------------------------
# En la app: comprobar, verificar y guardar
# ---------------------------------------------------------------------------------------------------------------------
def test_descarga_un_catalogo_nuevo_firmado(publicado, datos):
    servidor = Servidor(publicado["rama"])
    r = cr.comprobar(datos, publicado["v0"], abrir=servidor)
    assert r.estado == "nuevo" and r.nuevas == [publicado["v1"]]
    assert Catalogo(cr.locales(datos)[publicado["v1"]]).version == publicado["v1"]
    estado = cr.leer_estado(datos)
    assert estado["resultado"] == "nuevo" and estado["ultima_comprobacion"]


def test_como_mucho_una_vez_al_dia(publicado, datos):
    servidor = Servidor(publicado["rama"])
    ahora = dt.datetime(2030, 1, 15, 9, 0)
    cr.comprobar(datos, publicado["v1"], abrir=servidor, ahora=ahora)
    n = len(servidor.pedidas)
    assert cr.comprobar(datos, publicado["v1"], abrir=servidor, ahora=ahora.replace(hour=18)).estado == "hoy_ya"
    assert len(servidor.pedidas) == n, "el mismo día no se vuelve a preguntar"
    assert cr.comprobar(datos, publicado["v1"], abrir=servidor, ahora=ahora.replace(hour=18), forzar=True).estado \
        == "al_dia", "«Comprobar ahora» sí pregunta"
    assert cr.comprobar(datos, publicado["v1"], abrir=servidor, ahora=ahora + dt.timedelta(days=1)).estado == "al_dia"


def _indice(rama):
    return json.loads((rama / "indice.json").read_text(encoding="utf-8"))


def _escribir(rama, indice):
    (rama / "indice.json").write_text(json.dumps(indice), encoding="utf-8")


@pytest.mark.parametrize("estropear, motivo", [
    (lambda i: i.pop("firma"), "no está firmado"),
    (lambda i: i["datos"].update(novedades="Cambiado por el camino"), "firma"),
    (lambda i: i.update(firma=base64.b64encode(b"x" * 64).decode()), "firma"),
    (lambda i: i.update(clave="00000000"), "otra clave"),
])
def test_nunca_acepta_sin_firma_o_con_firma_mala(publicado, datos, estropear, motivo):
    rama = publicado["rama"]
    i = _indice(rama)
    estropear(i)
    _escribir(rama, i)
    r = cr.comprobar(datos, publicado["v0"], abrir=Servidor(rama))
    assert r.estado == "error" and motivo in r.mensaje
    assert cr.locales(datos) == {}, "no se guarda nada"


def test_firmado_con_otra_clave_no_vale(publicado, datos, monkeypatch):
    monkeypatch.setattr(firma, "clave_publica", lambda: _clave()[1])
    r = cr.comprobar(datos, publicado["v0"], abrir=Servidor(publicado["rama"]))
    assert r.estado == "error" and cr.locales(datos) == {}


def test_paquete_cambiado_por_el_camino_no_vale(publicado, datos):
    rama = publicado["rama"]
    archivo = rama / _indice(rama)["datos"]["archivo"]
    archivo.write_bytes(archivo.read_bytes()[:-10] + b"0123456789")
    r = cr.comprobar(datos, publicado["v0"], abrir=Servidor(rama))
    assert r.estado == "error" and "sha256" in r.mensaje and cr.locales(datos) == {}


def test_catalogo_viejo_no_se_descarga(publicado, datos):
    """El publicado no es más nuevo que el que hay (o alguien sirve uno antiguo con su firma buena): nada."""
    servidor = Servidor(publicado["rama"])
    r = cr.comprobar(datos, "2099.01.01", abrir=servidor)
    assert r.estado == "al_dia" and cr.locales(datos) == {}
    assert servidor.pedidas == [cr.URL_INDICE], "ni siquiera se pide el paquete"


def test_sin_red_sigue_con_el_que_tiene_y_lo_vuelve_a_intentar(publicado, datos):
    servidor = Servidor(publicado["rama"])
    servidor.caido = True
    r = cr.comprobar(datos, publicado["v0"], abrir=servidor)
    assert r.estado == "error" and "sin conexión" in r.mensaje
    estado = cr.leer_estado(datos)
    assert "ultima_comprobacion" not in estado and estado["ultimo_intento"], "sin red no cuenta como comprobado"
    assert cr.toca(estado)


def test_baja_tambien_la_version_de_una_programacion_que_falta(publicado, datos):
    """Una programación hecha con un catálogo que no está en el equipo: se baja para poder comparar."""
    r = cr.comprobar(datos, publicado["v1"], faltan=[publicado["v0"]], abrir=Servidor(publicado["rama"]))
    assert r.nuevas == [publicado["v0"]] and publicado["v0"] in cr.locales(datos)


def _paquete_con(archivos, version="2030.01.15"):
    crudo = json.dumps({"formato": cr.FORMATO_PAQUETE, "version": version, "fecha": "2030-01-15",
                        "archivos": archivos}).encode()
    return gzip.compress(crudo)


@pytest.mark.parametrize("ruta", ["../fuera.yaml", "ciclos/../../x.yaml", "/etc/x.yaml", "modulos/x.py",
                                  "otra/cosa.yaml"])
def test_un_paquete_con_rutas_raras_no_se_escribe(tmp_path, ruta):
    paquete = _paquete_con({ruta: "x: 1\n"})
    with pytest.raises(cr.CatalogoNoValido, match="rutas"):
        cr.desempaquetar(paquete, cr.sha256(paquete), "2030.01.15", tmp_path / "versiones")
    assert not (tmp_path / "versiones" / "2030.01.15").exists() and not (tmp_path / "fuera.yaml").exists()


def test_un_paquete_incompleto_no_se_acepta(tmp_path):
    paquete = _paquete_con({"normativa.yaml": "formato: catalogo/2\nnormas: []\n"})
    with pytest.raises(cr.CatalogoNoValido):
        cr.desempaquetar(paquete, cr.sha256(paquete), "2030.01.15", tmp_path / "versiones")
    assert list((tmp_path / "versiones").iterdir()) == [], "ni la carpeta temporal se queda"


def test_la_copia_del_catalogo_de_la_app_se_guarda_una_vez(datos):
    cat = Catalogo()
    cr.guardar_copia(cat, datos)
    cr.guardar_copia(cat, datos)
    assert list(cr.locales(datos)) == [cat.version]
    assert cr.comprobar_carpeta(cr.locales(datos)[cat.version], cat.version).version == cat.version


def test_solo_raw_githubusercontent_de_la_rama_publicada():
    assert cr.url_permitida(cr.URL_INDICE)
    assert not cr.url_permitida("http://raw.githubusercontent.com/cferrerobonet/programaciones_fp/catalogo-publicado/x")
    assert not cr.url_permitida("https://raw.githubusercontent.com/otro/repo/catalogo-publicado/indice.json")
    assert not cr.url_permitida("https://example.com/cferrerobonet/programaciones_fp/catalogo-publicado/indice.json")


def test_la_clave_publica_de_la_app():
    pub = firma.clave_publica()
    assert len(pub) == 32 and len(firma.id_clave(pub)) == 8
    assert not firma.verificar({"x": 1}, "")
