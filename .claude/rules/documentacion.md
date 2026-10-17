---
paths:
  - "*.md"
  - "docs/**"
  - ".claude/**"
  - ".github/*.md"
  - ".github/ISSUE_TEMPLATE/**"
---

# Documentación

Mapa de documentos: `docs/README.md`. No crear documentos paralelos ni fechados: se actualizan los que hay.

| Cambio | Documento que se toca en la misma tarea |
| --- | --- |
| Cualquier versión publicada | `CHANGELOG.md` (entrada arriba; es la nota del release y lo que ve el profesor en la ventana de novedades) |
| Comportamiento o pantalla | `PRD.md` si cambia un requisito; si es visual, `DESIGN.md` |
| Estructura, módulo nuevo, flujo de datos | `TRD.md` §3 |
| Documento generado o validaciones | `docs/DOCUMENTO_GENERADO.md` |
| Catálogo, archivo de trabajo o cálculos | `docs/MODELO_DE_DATOS.md` · fuentes: `docs/CATALOGO_Y_FUENTES.md` |
| Decisión con alternativas | nueva entrada en `docs/DECISIONES.md` (ADR numerado; los anteriores no se reescriben: se marcan como sustituidos) |
| Datos personales, secretos, correo | `docs/SEGURIDAD_Y_DATOS.md` |
| Compilación, publicación, restauración | `docs/OPERACIONES.md` |
| Fase cerrada o avanzada | `docs/HOJA_DE_RUTA.md` |
| Dato que falta, idea o fallo detectado | `docs/PENDIENTE.md` |

- Si solo cambia implementación interna: «sin impacto documental», dicho en el commit.
- Fuentes de verdad (no copiar cifras vivas en documentos): versión → `pyproject.toml`; tokens → `ui/estilo.py`; catálogo → `catalogo/`.
- Instrucciones para agentes: `AGENTS.md` es el principal (por debajo de 8 KB); `CLAUDE.md` solo lo importa; el detalle por zona va en `.claude/rules/` con `paths:`.
- Ficha en la bóveda: `../PROGRAMACIONES — Índice.md` (fuera del repositorio): la skill `publicar` añade allí cada versión publicada.
