---
name: Programaciones
description: Herramienta de escritorio del profesorado de FP para generar la programación didáctica de un módulo; mismo sistema de diseño que Partes de salida (tres zonas, verde EPLA y dorado, claro y oscuro).
colors:
  accent: "#2c7a3a"
  accent_soft: "#e2f0e3"
  gold: "#b97a12"
  gold_soft: "#fbf0d9"
  bg: "#f3f5f1"
  surface: "#ffffff"
  surface2: "#eef2ec"
  line: "#d9e0d5"
  fg: "#1d2a20"
  muted: "#5d6b60"
  warn: "#9a5b00"
  danger: "#a32d2d"
typography:
  display: { fontFamily: "Barlow Condensed", weights: [600, 700, 800] }
  body: { fontFamily: "Barlow", weights: [400, 500, 600, 700] }
  mono: { fontFamily: "JetBrains Mono", use: "códigos de módulo, RA y horas" }
---

# Design System: Programaciones

**Regla madre:** la interfaz es **idéntica en diseño a Partes de salida** (CarlosFB, 2026-10-14). Mismos colores, tipografías, barra superior, logos, ventanas modales, barras de progreso, campos, botones, chips, avisos, listados y presentación. Lo que este documento no cambia es igual que en `../../PARTES DE SALIDA (python)/PARTES DE SALIDA - CÓDIGO FUENTE/DESIGN.md`.

**Maqueta v0** (pendiente de aprobar): `../Maqueta v0 (2026-10-14)/` en la bóveda, fuera del repositorio, con `Maqueta interactiva.html` y una captura por pantalla.

Fuente de verdad en el código: `src/programaciones/ui/estilo.py`, copiado de Partes de salida. Si Partes cambia un token, se cambia aquí igual.

## Familia de apps de CarlosFB

**Requisito de CarlosFB (2026-10-14):** todas sus apps se notan hechas por la misma mente, con el mismo diseño. Partes de salida es la referencia; Programaciones **no tiene variaciones propias** en lo que comparten todas.

| Invariante de la familia | Cómo es (igual en todas) |
| --- | --- |
| Paleta | Verde EPLA y dorado, neutros verdosos, claro y oscuro según el sistema: tokens de `estilo.py` |
| Tipografía | Barlow (texto), Barlow Condensed (títulos y cifras), JetBrains Mono (datos) |
| Barra superior | Nombre de la app en Barlow Condensed 20 px + « · área» en gris; a la derecha, estado, recuentos, botón de estado en verde, botón dorado de actualización y «Ajustes» |
| Ventana principal | Tres zonas (300 px · flexible · 340 px) con el botón grande verde abajo a la derecha y su atajo |
| Presentación, novedades, Ajustes, listados y avisos | Los de Partes de salida, sin cambios (más abajo, solo lo propio) |
| Textos | Castellano, frases cortas, sin jerga técnica; los botones dicen lo que hacen («Exportar», «Aceptar cambios») |

Lo único propio es el contenido de las tres zonas. Un componente nuevo se diseña para toda la familia y se lleva también a Partes de salida.

## Overview

**Creative North Star: «La mesa del profesor».** Se usa pocas veces al año, con calma y con mucho que comprobar. Todo está a la vista y en orden: **elegir módulo → revisar lo oficial → rellenar lo propio → vista previa → exportar.**

### Named Rules

- **The Three Zones Rule** (heredada). Tres columnas fijas:
  - **Módulos** (300 px).
  - **Ficha y bloques** (flexible).
  - **Estado, vista previa y exportar** (340 px). El botón de exportar está siempre en el mismo sitio, abajo a la derecha.
- **The Only-What-He-Knows Rule.** La interfaz solo pide lo que únicamente sabe el profesor. Un campo nuevo necesita demostrar que no se puede sacar del catálogo ni calcular.
- **The Hidden Boilerplate Rule.** Los textos fijos de la plantilla **no aparecen nunca** en la interfaz: solo en la vista previa y en el documento (requisito de CarlosFB).
- **The Read-Only Official Rule.** Lo que viene del catálogo se ve en gris de solo lectura, con su fuente («BOE · comprobado el …»), y no se puede editar.
- **The Token Rule** (heredada). Todo color sale de `T[...]`.
- **The Paper Rule** (heredada). El documento generado es la plantilla del departamento, no el tema.
- **The What-You-See Rule** (heredada). La vista previa es el mismo `.docx` convertido a PDF, con la marca «BORRADOR».

## Colors

Los mismos tokens que Partes de salida, en claro y en oscuro (tabla completa en su `DESIGN.md`). Uso propio en esta app:

| Token | Uso en Programaciones |
| --- | --- |
| `accent` / `accent_soft` | Exportar, paso actual, bloque confirmado, módulo elegido |
| `gold` / `gold_soft` | Etiqueta de ciclo y grado, botón de actualización y ventana de novedades |
| `warn` / `warn_soft` | Bloque **heredado sin revisar**, avisos de validación que no bloquean y catálogo con cambios |
| `danger` | Validación que bloquea la definitiva («La tabla 4.1 no cuadra: faltan 4 h») y acciones destructivas |
| `surface2` | Datos oficiales de solo lectura, barra superior y menú lateral de Ajustes |

## Typography

| Rol | Familia | Tamaño | Dónde |
| --- | --- | --- | --- |
| Nombre del módulo | Barlow Condensed Bold | 30 px | Ficha |
| Títulos | Barlow Condensed Bold | 19–26 px | Bloques, apartados de Ajustes, estados vacíos |
| Cifras grandes | Barlow Condensed Bold | 40 px | Horas totales y % de empresa en «Estado» |
| Cuerpo | Barlow | 14 px (13 y 12 secundarios) | Todo lo demás |
| Etiquetas | Barlow Bold, mayúsculas, espaciado 0,9 px | 12 px | «DEL CURRÍCULO», «ESTADO», «VISTA PREVIA» |
| Datos | JetBrains Mono | 14 px | Código del módulo, RA1…RA6, horas en tablas |

## Layout

**Ventana principal:** 1100 × 700 (mínimo 980 × 620).
**Barra superior:**
- Título «Programaciones».
- Curso escolar en chip (`2026-2027`).
- Estado del catálogo: «Catálogo al día · 2026-10-14» en `accent`, o «Cambios en el currículo» en `warn`.
- Botón dorado «↑ Actualizar a X.Y.Z» cuando hay versión nueva.
- Botón verde «Programaciones · N» (como «Partes recurrentes» en Partes de salida), que abre el listado, y «Ajustes». «Abrir…» y «Nueva a partir de…» están en el estado vacío y en el menú de la app.

**Columna izquierda (300 px):**
- Buscador con lupa («Código o nombre del módulo»).
- Chips de grado (GM · GS), de ciclo (en filas, `FlujoLayout`) y de curso (1.º · 2.º), y «Limpiar».
- Lista de módulos en filas de 58 px: código en mono, nombre en dos líneas, etiqueta ciclo · curso en `gold_soft` e icono de estado (sin empezar · en curso · exportada).

**Centro:**
- Cabecera de la ficha: nombre del módulo (30 px), etiquetas de ciclo, curso y grado, código en mono, horas y h/semana.
- Caja **«DEL CURRÍCULO»** (`surface2`, solo lectura y plegable): RA con sus criterios, competencias del módulo, normativa y «Fuente: BOE … · comprobado el …».
- Debajo, la **barra de pasos** (chips) con los bloques del profesor: Profesorado · Unidades y evaluación · Empresa por RA · RA y competencias · Metodología y recursos. Cada chip lleva su estado: verde confirmado, ámbar heredado o vacío. El contenido del paso elegido va en una caja.

**Columna derecha (340 px):**
- «ESTADO»: lista de bloques con su icono, barra de progreso (bloques confirmados de 5) y las cifras grandes: horas de centro + empresa = total y % de empresa.
- Avisos de validación (`aviso` ámbar o rojo), cada uno con el enlace «Ir» a su campo.
- «VISTA PREVIA»: miniatura de la portada con sombra (máx. 320 px de alto) y el botón «Vista previa ⌘P».
- «EXPORTAR» con dos chips, «Word» y «PDF».
- «Exportar ⌘E» (verde, grande, 18 px), con la carpeta de destino en gris debajo; desactivado mientras haya validaciones rojas o bloques heredados sin confirmar.

**Estados vacíos** (como «Busca un alumno»):
- «Elige un módulo».
- «Empieza esta programación o hereda la del curso pasado», con dos botones.

## Bloques del profesor

| Bloque | Control |
| --- | --- |
| Profesorado | Lista de nombres (el del profesor, rellenado desde Ajustes) con «Añadir» |
| Unidades y evaluación | Tabla editable de filas de 30 px: tipo (UD · Práctica · Otro), título, horas (mono), trimestre (chips 1 · 2 · 3) y elemento de evaluación (desplegable). Debajo, una tabla de elementos: tipo (Examen · Práctica · Trabajo), nombre y RA (chips RA1…RAn). Arrastrar para ordenar; peso calculado en gris |
| Empresa por RA | Una fila por RA: casilla «va a empresa», horas en mono y modalidad calculada (Centro · Mixto · Empresa) |
| RA y competencias | Rejilla de RA × letras de competencia del módulo, con casillas. Las letras posibles salen del catálogo |
| Metodología y recursos | Preguntas cortas: material de referencia (cuaderno o libro), plataformas (chips: Teams, Educamos…), software (chips y campo libre; «CYPE» como nombre de la suite), aulas y talleres, y un texto libre de metodología propia de 600 caracteres como máximo |

Un bloque heredado muestra arriba la banda `warn_soft`: «Heredado de *Nombre* (2026-2027) · revisa y confirma». Y el botón «Confirmar bloque», que la quita.

## Ventanas modales

Estilo de Partes de salida: márgenes 26/22 px, título condensado y botones abajo a la derecha (principal verde, peligro rojo).

| Ventana | Contenido |
| --- | --- |
| **Actualización disponible** | **La misma de Partes de salida** (`DialogoActualizacion`): círculo dorado «↑», «Hay una versión nueva: X.Y.Z», «NOVEDADES» en Markdown (la entrada del `CHANGELOG.md`), «Más tarde» y «Actualizar ahora». Descarga con barra de progreso |
| **Cambios en el currículo** | El mismo diálogo, con el círculo dorado «§» y el título «Ha cambiado el currículo de este módulo». Norma de origen con enlace, lista en Markdown de lo que cambia y qué bloques suyos quedan afectados. Botones «Más tarde» y «Aceptar cambios» (verde): **lo aprueba cada profesor** (ADR-015) |
| **Nueva a partir de…** | Zona de soltar (`ZonaSoltar`) para el `.docx` o `.programacion` anterior. Resumen en cifras de lo que se hereda (unidades, elementos, bloques), aviso de los RA que han cambiado y «Cancelar» / «Heredar» |
| **Exportando** | Barra de progreso: «Rellenando la plantilla» → «Comprobando» → «Convirtiendo a PDF»; al terminar, aviso «Exportada en …» con «Mostrar en la carpeta» |
| **Vista previa** | 900 × 700, `QPdfView` con la marca «BORRADOR» |
| **Abierto con cambios de Word** | «Este documento se ha modificado en Word después de exportarlo; esos cambios no se recuperan.» |
| **Ayuda** | Como `ui/ayuda.py`: añadir la carpeta de Teams a OneDrive |
| **Programaciones** (940 × 600) | Como «Partes recurrentes» de Partes de salida: `TablaPaginada` con casilla por fila (módulo, ciclo y curso, curso escolar, estado, última exportación); abajo, «Abrir» y «Enviar N por correo…» |
| **Enviar por correo** | Destinatarios (chips con los recordados), «Word» y «PDF», asunto ya escrito, adjuntos con su tamaño y total (aviso `warn` si pasa del límite), «Cancelar» y «Crear correo» (opción A) o «Enviar» (opción B). Va en `Tarea`, como en Partes de salida |

**Ajustes** (como en Partes de salida): Profesor · Carpeta de entrega · Exportación (formatos, programa para el PDF, idioma del documento) · Correo · Catálogo (versión, firma, «Comprobar ahora», cambios por aceptar) · Acerca de.

## Componentes heredados sin cambios

Botones, campos, casillas, `QProgressBar`, aviso flotante, zona de soltar, barras de desplazamiento y tooltips, como en Partes de salida. Los listados usan `TablaPaginada` (patrón de Web Pedidos: buscador, 5/10/15/20/50 por página, «Limpiar filtros», cabeceras ordenables, pie «Mostrando 1–10 de N» con los extremos desactivados).

## Presentación y «Acerca de»

La misma tarjeta de Partes de salida (588 × 348). Textos:
- «FORMACIÓN PROFESIONAL · EPLA».
- El título «Programaciones».
- Sin lema (CarlosFB, 2026-10-14).
- La pastilla de versión.
- Pasos de carga: «Cargando el catálogo…» y «Comprobando el currículo…».

Mismos logos. El icono sigue el estilo del de Partes de salida y se dibuja en la maqueta.

## Do's and Don'ts

**Do:** copiar el componente de Partes de salida antes de dibujar uno nuevo; regenerar `docs/capturas/` tras un cambio visible; mantener el flujo con teclado (⌘S, ⌘P, ⌘E).

**Don't:** poner diálogos de confirmación en el camino de exportar (excepción: sustituir un archivo del mismo nombre); lo demás, ya está en las reglas de arriba.
