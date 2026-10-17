"""Firma Ed25519 del catálogo publicado: en la app, solo verificación (TRD §2, ADR-027).

La clave privada está únicamente en el secreto `CATALOGO_CLAVE` de GitHub y la usa `scripts/catalogo.py publicar` en
`catalogo.yml`. La pública va dentro de la app, en `recursos/clave_catalogo.txt`, para que se pueda comprobar también en
los instaladores compilados. Lo firmado es el JSON canónico de `datos` (claves ordenadas, sin espacios, UTF-8).
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json

from .rutas import recursos


def canonico(datos) -> bytes:
    return json.dumps(datos, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def clave_publica() -> bytes:
    """La clave pública que lleva la app (32 bytes)."""
    lineas = [x.strip() for x in (recursos() / "clave_catalogo.txt").read_text(encoding="utf-8").splitlines()]
    return base64.b64decode(next(x for x in lineas if x and not x.startswith("#")), validate=True)


def id_clave(publica: bytes) -> str:
    return hashlib.sha256(publica).hexdigest()[:8].upper()


def verificar(datos, firma_b64: str, publica: bytes | None = None) -> bool:
    """True solo si `firma_b64` es la firma Ed25519 de `datos` con la clave pública de la app (o la que se pase)."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    try:
        firma = base64.b64decode(firma_b64 or "", validate=True)
        Ed25519PublicKey.from_public_bytes(publica or clave_publica()).verify(firma, canonico(datos))
    except (InvalidSignature, ValueError, TypeError, binascii.Error):
        return False
    return True
