---
paths:
  - "src/programaciones/recursos/plantilla/**"
  - "src/programaciones/documento.py"
  - "src/programaciones/incrustar.py"
  - "src/programaciones/pdf.py"
  - "src/programaciones/importar_docx.py"
  - "src/programaciones/contenido.py"
  - "src/programaciones/ooxml.py"
  - "scripts/plantilla.py"
  - "scripts/regenerar.py"
---

# Documento

Qué lleva cada apartado, marcas, formato y validaciones: `docs/DOCUMENTO_GENERADO.md`. Decisiones: ADR-006, ADR-018, ADR-019 y ADR-020. Reglas de redacción: la skill de la bóveda `programacion-didactica`.

- **La plantilla no se edita a mano.** Sale de `scripts/plantilla.py crear <programación de PIICT> --proyecto <programación de 0526>`; si hay que cambiar una marca o un bloque, se cambia el script y se vuelve a crear. `scripts/plantilla.py comprobar` limpio, sin partes personales ni correos.
- **Repositorio público:** la plantilla va sin nombres, correos, comentarios ni metadatos de SharePoint. Las programaciones de la bóveda se leen en local (`PROGRAMACIONES_REFERENCIAS`) y nada de ellas entra en el repositorio, ni en las pruebas: solo posiciones y el principio del texto generado (plantilla o catálogo).
- **Sin datos, no se implementa:** una fecha, un periodo o una norma que falta no se inventa en el documento; va a `docs/PENDIENTE.md` y, si es del catálogo, a V-11.
- **Cierre de cada cambio del documento:**
  - `pytest` y, en local, `pytest -m referencias`: las seis referencias, con solo las diferencias aceptadas de `tests/test_regeneracion.py`. Una diferencia nueva se corrige o se acepta con su motivo y su pendiente para CarlosFB.
  - Render a PDF con LibreOffice (`pdf.exportar_pdf`) y mirar todas las páginas de, al menos, una referencia.
  - `validate.py` de la skill `docx` sobre los regenerados.
- **Datos incrustados (R1):** cualquier cambio en `incrustar.py` o en lo que firma la huella del texto (`contenido.texto_cuerpo`) repite la prueba con LibreOffice (automática) y la manual de Word (`scripts/prueba_word.py`).
