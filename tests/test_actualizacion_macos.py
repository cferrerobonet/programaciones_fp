"""Actualización en macOS en su sitio (ADR-029): el script de sustitución con bundles falsos en `tmp_path` y `hdiutil`,
`open`, `ditto`, `xattr` y `osascript` simulados (nunca se montan, copian ni abren apps de verdad), y la preparación
desde la app: éxito, carpeta sin permiso, fallo de la copia con la vieja en su sitio y modo de desarrollo."""
import os
import plistlib
import shutil
import subprocess
import sys

import pytest

from programaciones import actualizaciones as act

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="sin bash")


def bundle(ruta, contenido):
    exe = ruta / "Contents" / "MacOS" / "Programaciones"
    exe.parent.mkdir(parents=True)
    exe.write_text(contenido)
    return ruta


@pytest.fixture
def escena(tmp_path):
    """/Applications/EPLA/Programaciones.app (vieja), el DMG montado con la nueva y las órdenes simuladas."""
    instalada = bundle(tmp_path / "Applications" / "EPLA" / "Programaciones.app", "0.2.0")
    montaje = tmp_path / "montaje"
    nueva = bundle(montaje / "Programaciones.app", "0.3.0")
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    llamadas = tmp_path / "llamadas.txt"
    for nombre, cuerpo in {
        "hdiutil": "",
        "open": "",
        "xattr": "",
        "osascript": "",
        # ditto de verdad copia el bundle; con FALLA_DITTO falla, con DITTO_A_MEDIAS deja una copia incompleta
        "ditto": '[ -n "${FALLA_DITTO:-}" ] && exit 1\n'
                 '[ -n "${DITTO_A_MEDIAS:-}" ] && { mkdir -p "$2"; exit 0; }\ncp -R "$1" "$2"\n',
    }.items():
        p = bin_ / nombre
        p.write_text(f'#!/bin/bash\necho "{nombre} $*" >> "{llamadas}"\n{cuerpo}')
        p.chmod(0o755)
    script = tmp_path / "actualizar.sh"
    script.write_text(act.SCRIPT_SUSTITUCION)
    return {"tmp": tmp_path, "instalada": instalada, "nueva": nueva, "montaje": montaje, "bin": bin_,
            "llamadas": llamadas, "script": script, "log": tmp_path / "logs" / "actualizacion.log"}


def pid_terminado():
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def lanzar_script(e, **entorno):
    env = {**os.environ, "HDIUTIL": str(e["bin"] / "hdiutil"), "DITTO": str(e["bin"] / "ditto"),
           "ABRIR": str(e["bin"] / "open"), "XATTR": str(e["bin"] / "xattr"), "OSASCRIPT": str(e["bin"] / "osascript"),
           "ESPERA": "5", **entorno}
    return subprocess.run(["bash", str(e["script"]), str(e["nueva"]), str(e["instalada"]), str(pid_terminado()),
                           str(e["montaje"]), str(e["log"])], env=env, timeout=60)


def hermanas(e):
    return sorted(p.name for p in e["instalada"].parent.iterdir())


def version_instalada(e):
    return (e["instalada"] / "Contents" / "MacOS" / "Programaciones").read_text()


def test_sustituye_la_app_en_su_carpeta(escena):
    r = lanzar_script(escena)
    assert r.returncode == 0
    assert version_instalada(escena) == "0.3.0", "la nueva, en /Applications/EPLA y no en /Applications"
    assert hermanas(escena) == ["Programaciones.app"], "nunca dos copias"
    llamadas = escena["llamadas"].read_text()
    assert f"xattr -dr com.apple.quarantine {escena['instalada']}" in llamadas
    assert f"hdiutil detach {escena['montaje']} -quiet" in llamadas
    assert llamadas.strip().endswith(f"open {escena['instalada']}"), "se abre la ya actualizada"
    assert "Actualizada" in escena["log"].read_text(), "deja registro en la carpeta de logs de la app"


@pytest.mark.parametrize("fallo", ["FALLA_DITTO", "DITTO_A_MEDIAS"])
def test_si_la_copia_falla_la_vieja_se_queda_y_se_avisa(escena, fallo):
    r = lanzar_script(escena, **{fallo: "1"})
    assert r.returncode == 1
    assert version_instalada(escena) == "0.2.0" and hermanas(escena) == ["Programaciones.app"]
    llamadas = escena["llamadas"].read_text()
    assert "osascript" in llamadas and "no se ha podido actualizar" in llamadas, "se avisa"
    assert f"hdiutil detach {escena['montaje']}" in llamadas
    assert llamadas.strip().endswith(f"open {escena['instalada']}"), "se vuelve a abrir la que había"
    assert "ERROR" in escena["log"].read_text()


def test_si_no_se_puede_poner_la_nueva_vuelve_la_vieja(escena):
    """El segundo cambio de nombre falla (mv simulado): la vieja vuelve a su sitio y no queda ninguna copia de más."""
    mv = escena["bin"] / "mv"
    mv.write_text('#!/bin/bash\ncase "$1" in *".nueva-"*) exit 1;; esac\nexec /bin/mv "$@"\n')
    mv.chmod(0o755)
    r = lanzar_script(escena, PATH=f"{escena['bin']}:{os.environ['PATH']}")
    assert r.returncode == 1
    assert version_instalada(escena) == "0.2.0" and hermanas(escena) == ["Programaciones.app"]


def test_espera_a_que_la_app_se_cierre(escena):
    import threading

    vivo = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(1.5)"])
    threading.Thread(target=vivo.wait, daemon=True).start()   # como launchd con la app: se recoge al terminar
    env = {**os.environ, "HDIUTIL": str(escena["bin"] / "hdiutil"), "DITTO": str(escena["bin"] / "ditto"),
           "ABRIR": str(escena["bin"] / "open"), "XATTR": str(escena["bin"] / "xattr"),
           "OSASCRIPT": str(escena["bin"] / "osascript")}
    subprocess.run(["bash", str(escena["script"]), str(escena["nueva"]), str(escena["instalada"]), str(vivo.pid),
                    str(escena["montaje"]), str(escena["log"])], env=env, timeout=60, check=True)
    assert vivo.poll() is not None and version_instalada(escena) == "0.3.0"


# ---------------------------------------------------------------------------------------------------------------------
# Desde la app (actualizaciones.instalar_macos)
# ---------------------------------------------------------------------------------------------------------------------
class Ordenes:
    """hdiutil simulado: «attach» devuelve el plist de un DMG montado en `montaje`."""

    def __init__(self, montaje):
        self.montaje = montaje
        self.hechas = []

    def __call__(self, orden):
        self.hechas.append(orden)
        if orden[1] == "attach":
            return plistlib.dumps({"system-entities": [{"dev-entry": "/dev/disk9"},
                                                       {"mount-point": str(self.montaje)}]}).decode()
        return ""


def test_prepara_la_sustitucion_y_lanza_el_script_aparte(escena):
    ordenes, lanzadas, abiertos = Ordenes(escena["montaje"]), [], []
    r = act.instalar_macos(escena["tmp"] / "x.dmg", app=escena["instalada"], pid=4242, logs=escena["tmp"] / "logs",
                           ejecutar=ordenes, lanzar=lanzadas.append, abrir=abiertos.append)
    assert r.modo == "sustitucion" and abiertos == []
    attach = ordenes.hechas[0]
    assert attach[:5] == [act.HDIUTIL, "attach", "-nobrowse", "-readonly", "-mountrandom"]
    orden = lanzadas[0]
    assert orden[:2] == ["/bin/bash", str(r.script)] and r.script.read_text() == act.SCRIPT_SUSTITUCION
    assert orden[2:6] == [str(escena["nueva"]), str(escena["instalada"]), "4242", str(escena["montaje"])]
    assert orden[6].startswith(str(escena["tmp"] / "logs" / "actualizacion_"))


def test_carpeta_sin_permiso_abre_el_dmg_y_dice_donde_arrastrarla(escena, monkeypatch):
    ordenes, lanzadas, abiertos = Ordenes(escena["montaje"]), [], []
    monkeypatch.setattr(act, "se_puede_sustituir", lambda app: False)
    r = act.instalar_macos(escena["tmp"] / "x.dmg", app=escena["instalada"], ejecutar=ordenes,
                           lanzar=lanzadas.append, abrir=abiertos.append)
    assert r.modo == "reserva" and lanzadas == [] and abiertos == [str(escena["tmp"] / "x.dmg")]
    assert str(escena["instalada"].parent) in r.mensaje and "arrastra" in r.mensaje
    assert ordenes.hechas == [], "ni se monta"


def test_en_desarrollo_abre_el_dmg_como_antes(escena, monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    lanzadas, abiertos = [], []
    r = act.instalar_macos(escena["tmp"] / "x.dmg", ejecutar=Ordenes(escena["montaje"]), lanzar=lanzadas.append,
                           abrir=abiertos.append)
    assert r.modo == "reserva" and lanzadas == [] and abiertos and "desarrollo" in r.mensaje


def test_un_dmg_sin_app_se_desmonta_y_va_a_la_reserva(escena):
    vacio = escena["tmp"] / "vacio"
    vacio.mkdir()
    ordenes, abiertos = Ordenes(vacio), []
    r = act.instalar_macos(escena["tmp"] / "x.dmg", app=escena["instalada"], ejecutar=ordenes, lanzar=lambda o: None,
                           abrir=abiertos.append)
    assert r.modo == "reserva" and abiertos
    assert any(o[1] == "detach" for o in ordenes.hechas)


def test_la_app_en_ejecucion_sale_de_sys_executable(tmp_path, monkeypatch):
    exe = bundle(tmp_path / "EPLA" / "Programaciones.app", "x") / "Contents" / "MacOS" / "Programaciones"
    monkeypatch.setattr(act.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    assert act.app_en_ejecucion() == (tmp_path / "EPLA" / "Programaciones.app").resolve()
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python"))
    assert act.app_en_ejecucion() is None


def test_windows_sigue_con_el_instalador_que_sustituye_en_su_carpeta(monkeypatch, qtbot):
    """En Windows no cambia nada: se abre el instalador, que con su AppId fijo instala en la carpeta de antes."""
    from pathlib import Path

    from programaciones.ui import dialogos

    iss = (Path(__file__).resolve().parents[1] / "installer_windows.iss").read_text(encoding="utf-8")
    assert "AppId={{9F472F08-FCFE-4DD9-8668-F4CC256B9E6C}" in iss and "UsePreviousAppDir=no" not in iss
    abiertos, macos = [], []
    monkeypatch.setattr(dialogos.platform, "system", lambda: "Windows")
    monkeypatch.setattr(dialogos, "abrir_instalador", abiertos.append)
    monkeypatch.setattr(dialogos, "instalar_macos", lambda *a, **k: macos.append(a))

    class Hilo:
        def __init__(self, *a):
            from PyQt6.QtCore import QObject, pyqtSignal

            class S(QObject):
                avance = pyqtSignal(int)
                listo = pyqtSignal(str)
                error = pyqtSignal(str)
            self.s = S()
            self.avance, self.listo, self.error = self.s.avance, self.s.listo, self.s.error

        def start(self):
            self.listo.emit("C:/tmp/Programaciones-9.9.9-Windows-Setup.exe")

        def terminate(self):
            pass

    monkeypatch.setattr(dialogos, "_Descargador", Hilo)
    salida = []
    monkeypatch.setattr(dialogos, "QApplication", type("A", (), {"instance": staticmethod(
        lambda: type("B", (), {"quit": lambda self: salida.append(1)})())}))
    dialogos._descargar(None, "https://github.com/x/Programaciones-9.9.9-Windows-Setup.exe", "9.9.9")
    assert abiertos == ["C:/tmp/Programaciones-9.9.9-Windows-Setup.exe"] and macos == [] and salida == [1]
