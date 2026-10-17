---
paths:
  - "src/programaciones/ui/**"
  - "src/programaciones/contexto.py"
  - "DESIGN.md"
  - "docs/capturas/**"
---

# Interfaz

Contrato visual: `DESIGN.md` y la maqueta v0 (`../Maqueta v0 (2026-10-14)/`, aprobada por CarlosFB el 2026-10-17). Leerlos antes de tocar una pantalla.

- **Interfaz idéntica a Partes de salida:** antes de crear un componente, se copia el suyo (`ui/componentes.py`, `ui/listado.py`, `ui/dialogos.py`…). Un componente nuevo se diseña para toda la familia.
- **Colores solo de los tokens** de `ui/estilo.py` (`T[...]`, claro y oscuro). Ningún hexadecimal suelto en los widgets (salvo el blanco sobre verde o dorado, como en Partes de salida).
- **Tres zonas fijas** (`ui/columnas.py`): módulos (300 px) · ficha y bloques (flexible) · estado, vista previa y exportar (340 px). El botón «Exportar» siempre abajo a la derecha.
- **Los textos fijos de la plantilla no se muestran nunca** en la interfaz (ADR-007). Lo oficial, en gris de solo lectura y con su fuente.
- **Sin datos, no se implementa:** lo que depende de algo pendiente (Proyecto intermodular de GM, FE de 2.º de GA, catálogo remoto) se enseña como «pendiente», sin inventarlo.
- Trabajo largo (documento, PDF, descargas) en `Tarea` (QThread), nunca en el hilo de la interfaz (RNF-03).
- Teclado: ⌘S, ⌘P, ⌘E y ⌘D (favorito, sobre la fila de módulo elegida; Ctrl en Windows); los botones escriben el atajo con `componentes.atajo`.
- Tras un cambio visible: revisar la pantalla con una captura sin pantalla (pytest-qt o `grab()`) y, cuando exista, `make capturas`.
