"""Enviar por correo una o varias programaciones (RF-14, ADR-014). Sin Qt.

La app abre un **borrador** en el programa de correo del profesor, con los destinatarios, el asunto, el cuerpo y los
archivos adjuntos. El profesor lo revisa y lo envía desde su cuenta: la app no guarda contraseñas ni envía nada.

Por plataforma (ADR-014):
- **macOS:** Mail u Outlook con AppleScript (`osascript`): el programa de correo por defecto del equipo (LaunchServices)
  o el elegido en Ajustes → Correo.
- **Windows:** Outlook clásico por COM (PowerShell, como el PDF con Word); si no está o falla, un mensaje `.eml` con
  `X-Unsent: 1`, que el programa de correo abre como mensaje nuevo con los adjuntos.
- **Reserva, siempre disponible:** se abre la carpeta con los archivos y un `mailto:` con destinatarios, asunto y
  cuerpo; los adjuntos se añaden a mano y la app lo avisa.

Las órdenes externas pasan por `_ejecutar` y `_abrir`: las pruebas las sustituyen por un cliente de correo simulado y
nunca se abre un programa de verdad.
"""
from __future__ import annotations

import html
import json
import mimetypes
import os
import plistlib
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path
from urllib.parse import quote

from programaciones.ajustes import ASUNTO_UNA, ASUNTO_VARIAS, CUERPO_CORREO, correo_valido

LIMITE_MB = 20       # por encima, se avisa antes de crear el correo
TIEMPO_MAX = 60      # segundos para AppleScript o PowerShell
#: Programa de correo por defecto en macOS: el que LaunchServices tiene para «mailto».
LAUNCHSERVICES = Path.home() / "Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist"
NOMBRES = {"mail": "Mail", "outlook": "Outlook", "eml": "el programa de correo (mensaje .eml)",
           "mailto": "el programa de correo"}


class ErrorCorreo(RuntimeError):
    """No se ha podido abrir el borrador con un método (se prueba el siguiente)."""


@dataclass
class Borrador:
    para: list[str]
    asunto: str
    cuerpo: str
    adjuntos: list[Path]


@dataclass
class Resultado:
    metodo: str                        # «mail», «outlook», «eml» o «mailto»
    manual: bool = False               # True: los adjuntos se añaden a mano (reserva)
    errores: list[str] = field(default_factory=list)

    @property
    def texto(self) -> str:
        if self.manual:
            return ("Se ha abierto un correo nuevo y la carpeta con los archivos: adjúntalos a mano antes de "
                    "enviarlo.")
        return f"Correo creado en {NOMBRES.get(self.metodo, self.metodo)}: revísalo y envíalo desde tu cuenta."


# -- Destinatarios, plantilla y tamaño --------------------------------------------------------------------------------
def separar(texto: str) -> tuple[list[str], list[str]]:
    """«a@example.com, b@example.com; c» → (válidos sin repetir, no válidos)."""
    validos, malos = [], []
    for trozo in re.split(r"[,;\s]+", texto or ""):
        trozo = trozo.strip()
        if not trozo:
            continue
        (validos if correo_valido(trozo) else malos).append(trozo)
    return list(dict.fromkeys(validos)), malos


class _Campos(dict):
    def __missing__(self, clave):  # un campo desconocido se queda tal cual: «{otro}»
        return "{" + clave + "}"


def rellenar(plantilla: str, campos: dict, defecto: str) -> str:
    try:
        return plantilla.format_map(_Campos(campos))
    except (ValueError, IndexError, AttributeError):  # llaves sueltas en una plantilla escrita a mano
        return defecto.format_map(_Campos(campos))


def campos(modulos: list[str], cursos: list[str], archivos: list[Path], profesor: str) -> dict:
    """Los campos de las plantillas. `modulos`: «0517 Procesos en…», uno por programación."""
    n = len(modulos)
    cursos = list(dict.fromkeys(cursos))
    return {
        "n": n,
        "modulo": modulos[0] if n == 1 else ", ".join(m.split(" ", 1)[0] for m in modulos),
        "modulos": (f"la programación didáctica de {modulos[0]}" if n == 1
                    else f"las programaciones didácticas de {n} módulos"),
        "curso": " y ".join(cursos),
        "archivos": "\n".join(f"- {Path(a).name}" for a in archivos),
        "profesor": profesor.strip(),
    }


def asunto_y_cuerpo(c: dict, asunto_una: str = ASUNTO_UNA, asunto_varias: str = ASUNTO_VARIAS,
                    cuerpo: str = CUERPO_CORREO) -> tuple[str, str]:
    """Asunto y cuerpo con las plantillas de Ajustes; una plantilla vacía vuelve a la de la app."""
    if c["n"] == 1:
        asunto = rellenar(asunto_una.strip() or ASUNTO_UNA, c, ASUNTO_UNA)
    else:
        asunto = rellenar(asunto_varias.strip() or ASUNTO_VARIAS, c, ASUNTO_VARIAS)
    texto = rellenar(cuerpo.strip() or CUERPO_CORREO, c, CUERPO_CORREO).rstrip()
    return " ".join(asunto.split()), texto


def tamano(adjuntos: list[Path]) -> int:
    return sum(Path(a).stat().st_size for a in adjuntos if Path(a).is_file())


def supera_limite(total: int, limite_mb: int = LIMITE_MB) -> bool:
    return total > limite_mb * 1024 * 1024


def texto_tamano(n: int) -> str:
    """«850 KB», «1,2 MB»."""
    if n < 1024 * 1024:
        return f"{max(1, round(n / 1024))} KB"
    return f"{n / 1024 / 1024:.1f} MB".replace(".", ",")


# -- Programa de correo -----------------------------------------------------------------------------------------------
def cliente_macos(plist: Path = LAUNCHSERVICES) -> str:
    """«outlook» si Outlook es el programa de correo por defecto del Mac; si no, «mail» (el de serie)."""
    try:
        datos = plistlib.loads(Path(plist).read_bytes())
    except (OSError, ValueError, plistlib.InvalidFileException):
        return "mail"
    for h in datos.get("LSHandlers", []) if isinstance(datos, dict) else []:
        if isinstance(h, dict) and h.get("LSHandlerURLScheme") == "mailto":
            app = str(h.get("LSHandlerRoleAll", "")).lower()
            return "outlook" if "outlook" in app else "mail"
    return "mail"


def hay_outlook_clasico() -> bool:
    """Outlook clásico de Windows (el nuevo Outlook no tiene COM)."""
    if not sys.platform.startswith("win"):
        return False
    try:
        import winreg

        winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Outlook.Application")
        return True
    except OSError:
        return False


def metodos(cliente: str = "auto", plataforma: str | None = None) -> list[str]:
    """En qué orden se intenta abrir el borrador; siempre acaba en «mailto» (reserva)."""
    plataforma = plataforma or sys.platform
    if cliente == "mailto":
        return ["mailto"]
    if plataforma == "darwin":
        if cliente not in ("mail", "outlook"):
            cliente = cliente_macos()
        return [cliente, "mailto"]
    if plataforma.startswith("win"):
        if cliente == "eml":
            return ["eml", "mailto"]
        if cliente == "outlook" or hay_outlook_clasico():
            return ["outlook", "eml", "mailto"]
        return ["eml", "mailto"]
    return ["mailto"]


def que_se_abre(cliente: str = "auto", plataforma: str | None = None) -> str:
    """Para la ventana de enviar: «Se abrirá un correo nuevo en Mail con los archivos adjuntos»."""
    m = metodos(cliente, plataforma)[0]
    if m == "mailto":
        return "Se abrirá un correo nuevo y la carpeta con los archivos: tendrás que adjuntarlos tú."
    return f"Se abrirá un correo nuevo en {NOMBRES[m]} con los archivos adjuntos. Lo revisas y lo envías tú."


# -- Órdenes externas (las pruebas las sustituyen) --------------------------------------------------------------------
def _ejecutar(orden: list[str], tiempo_max: int = TIEMPO_MAX) -> None:
    try:
        r = subprocess.run(orden, capture_output=True, text=True, timeout=tiempo_max)
    except subprocess.TimeoutExpired as e:
        raise ErrorCorreo(f"{Path(orden[0]).name} tarda más de {tiempo_max} s") from e
    except OSError as e:
        raise ErrorCorreo(f"No se puede ejecutar {Path(orden[0]).name}: {e}") from e
    if r.returncode != 0:
        raise ErrorCorreo(f"{Path(orden[0]).name} ha fallado: {(r.stderr or r.stdout).strip()[:300]}")


def _abrir(destino: str) -> None:
    """Abre una carpeta, un archivo o un enlace con el programa del sistema."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(destino)  # type: ignore[attr-defined]  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", destino], check=True, timeout=TIEMPO_MAX)
        else:
            subprocess.run(["xdg-open", destino], check=True, timeout=TIEMPO_MAX)
    except (OSError, subprocess.SubprocessError) as e:
        raise ErrorCorreo(f"No se puede abrir {destino[:80]}: {e}") from e


# -- Métodos ----------------------------------------------------------------------------------------------------------
#: Los datos llegan como argumentos (`on run argv`), nunca dentro del texto del script: ni comillas ni inyección.
#: Destinatarios y adjuntos, uno por línea.
APPLESCRIPT_MAIL = '''on run argv
  set asunto to item 1 of argv
  set cuerpo to item 2 of argv
  set AppleScript's text item delimiters to linefeed
  set destinatarios to text items of (item 3 of argv)
  set adjuntos to text items of (item 4 of argv)
  set AppleScript's text item delimiters to ""
  tell application "Mail"
    set m to make new outgoing message with properties {subject:asunto, content:cuerpo & linefeed & linefeed, visible:true}
    tell m
      repeat with d in destinatarios
        if (d as text) is not "" then make new to recipient at end of to recipients with properties {address:(d as text)}
      end repeat
    end tell
    repeat with a in adjuntos
      if (a as text) is not "" then
        tell content of m to make new attachment with properties {file name:((POSIX file (a as text)) as alias)} at after last paragraph
      end if
    end repeat
    activate
  end tell
end run'''

APPLESCRIPT_OUTLOOK = '''on run argv
  set asunto to item 1 of argv
  set cuerpo to item 2 of argv
  set AppleScript's text item delimiters to linefeed
  set destinatarios to text items of (item 3 of argv)
  set adjuntos to text items of (item 4 of argv)
  set AppleScript's text item delimiters to ""
  tell application "Microsoft Outlook"
    set m to make new outgoing message with properties {subject:asunto, content:cuerpo}
    repeat with d in destinatarios
      if (d as text) is not "" then make new to recipient at m with properties {email address:{address:(d as text)}}
    end repeat
    repeat with a in adjuntos
      if (a as text) is not "" then make new attachment at m with properties {file:((POSIX file (a as text)) as alias)}
    end repeat
    open m
    activate
  end tell
end run'''

#: Outlook clásico por COM. Los datos, en un JSON aparte (UTF-8): nada del correo dentro de la orden.
POWERSHELL_OUTLOOK = ("$d = Get-Content -Raw -Encoding UTF8 -LiteralPath '{datos}' | ConvertFrom-Json; "
                      "$o = New-Object -ComObject Outlook.Application; $m = $o.CreateItem(0); "
                      "$m.To = ($d.para -join '; '); $m.Subject = $d.asunto; $m.Body = $d.cuerpo; "
                      "foreach ($a in $d.adjuntos) {{ [void]$m.Attachments.Add([string]$a) }}; $m.Display($false)")


def _argumentos(b: Borrador, cuerpo: str) -> list[str]:
    return [b.asunto, cuerpo, "\n".join(b.para), "\n".join(str(Path(a).resolve()) for a in b.adjuntos)]


def con_mail(b: Borrador) -> None:
    _ejecutar(["osascript", "-e", APPLESCRIPT_MAIL, *_argumentos(b, b.cuerpo)])


def con_outlook_mac(b: Borrador) -> None:
    cuerpo = html.escape(b.cuerpo).replace("\n", "<br>")  # Outlook toma el contenido como HTML
    _ejecutar(["osascript", "-e", APPLESCRIPT_OUTLOOK, *_argumentos(b, cuerpo)])


def con_outlook_windows(b: Borrador) -> None:
    with tempfile.TemporaryDirectory(prefix="programaciones-correo-") as tmp:
        datos = Path(tmp) / "correo.json"
        datos.write_text(json.dumps({"para": b.para, "asunto": b.asunto, "cuerpo": b.cuerpo,
                                     "adjuntos": [str(Path(a).resolve()) for a in b.adjuntos]}, ensure_ascii=False),
                         encoding="utf-8")
        orden = POWERSHELL_OUTLOOK.format(datos=str(datos).replace("'", "''"))
        _ejecutar(["powershell", "-NoProfile", "-NonInteractive", "-Command", orden])


def mensaje_eml(b: Borrador) -> bytes:
    """Mensaje sin enviar (`X-Unsent: 1`): Outlook y el correo de Windows lo abren como correo nuevo."""
    m = EmailMessage(policy=SMTP)
    if b.para:
        m["To"] = ", ".join(b.para)
    m["Subject"] = b.asunto
    m["X-Unsent"] = "1"
    m.set_content(b.cuerpo)
    for a in b.adjuntos:
        a = Path(a)
        tipo = mimetypes.guess_type(a.name)[0] or "application/octet-stream"
        principal, secundario = tipo.split("/", 1)
        m.add_attachment(a.read_bytes(), maintype=principal, subtype=secundario, filename=a.name)
    return m.as_bytes()


def con_eml(b: Borrador, carpeta: Path) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = re.sub(r'[\\/:*?"<>|]+', " ", b.asunto).strip()[:120] or "Programaciones"
    ruta = carpeta / f"{nombre}.eml"
    ruta.write_bytes(mensaje_eml(b))
    _abrir(str(ruta))
    return ruta


def enlace_mailto(b: Borrador) -> str:
    para = ",".join(quote(d, safe="@") for d in b.para)
    return f"mailto:{para}?subject={quote(b.asunto, safe='')}&body={quote(b.cuerpo, safe='')}"


def con_mailto(b: Borrador) -> None:
    for carpeta in dict.fromkeys(str(Path(a).resolve().parent) for a in b.adjuntos):
        _abrir(carpeta)
    _abrir(enlace_mailto(b))


def abrir_borrador(b: Borrador, cliente: str = "auto", carpeta_eml: Path | None = None,
                   plataforma: str | None = None) -> Resultado:
    """Abre el borrador con el primer método que funcione (`metodos`). Lanza ErrorCorreo si ni la reserva funciona."""
    faltan = [Path(a).name for a in b.adjuntos if not Path(a).is_file()]
    if faltan:
        raise ErrorCorreo("No se encuentran los archivos: " + ", ".join(faltan))
    errores: list[str] = []
    plataforma = plataforma or sys.platform
    for m in metodos(cliente, plataforma):
        try:
            if m == "mail":
                con_mail(b)
            elif m == "outlook" and plataforma == "darwin":
                con_outlook_mac(b)
            elif m == "outlook":
                con_outlook_windows(b)
            elif m == "eml":
                con_eml(b, carpeta_eml or Path(tempfile.gettempdir()) / "Programaciones")
            else:
                con_mailto(b)
                return Resultado(m, manual=bool(b.adjuntos), errores=errores)
            return Resultado(m, errores=errores)
        except ErrorCorreo as e:
            errores.append(f"{NOMBRES.get(m, m)}: {e}")
    raise ErrorCorreo("; ".join(errores))
