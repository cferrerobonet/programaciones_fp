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

**Maqueta v0** (2026-10-14, pendiente de aprobar): `../Maqueta v0 (2026-10-14)/` en la bóveda, fuera del repositorio. Contiene `Maqueta interactiva.html` y una captura por pantalla, con datos de ejemplo de PIICT.

Fuente de verdad en el código: `src/programaciones/ui/estilo.py`, copiado de Partes de salida (tokens `CLARO` y `OSCURO`, hoja de estilos, tipografías e iconos). Si Partes de salida cambia un token, se cambia aquí igual.

## Familia de apps de CarlosFB

**Requisito de CarlosFB (2026-10-14):** todas sus apps tienen que notarse hechas por la misma mente y con el mismo diseño, sin diferencias, como si fueran de una sola empresa. Partes de salida es la referencia, y Guardias de patio ya la sigue desde su 7.0.0. Programaciones **no tiene variaciones propias** en lo que comparten todas.

| Invariante de la familia | Cómo es (igual en todas) |
| --- | --- |
| Paleta | Verde EPLA y dorado, neutros verdosos, claro y oscuro según el sistema: tokens de `estilo.py` |
| Tipografía | Barlow (texto), Barlow Condensed (títulos y cifras), JetBrains Mono (datos) |
| Barra superior | Nombre de la app en Barlow Condensed 20 px + « · área» en gris. A la derecha: estado en verde con icono, recuentos en gris, botón de estado en verde si hay algo pendiente, botón dorado de actualización y «Ajustes» |
| Ventana principal | Tres zonas: buscar a la izquierda (300 px), ficha en el centro, acción principal a la derecha (340 px), con el botón grande verde abajo a la derecha y su atajo (⌘P, ⌘E…) |
| Presentación y «Acerca de» | La misma tarjeta: banda verde con el engranaje del escudo, filete dorado, escudo en medallón, «ÁREA · EPLA», nombre de la app, pastilla de versión, barra dorada de carga y pie «Escuelas Profesionales Luis Amigó · Godella / Diseño y desarrollo: Carlos Ferrero Bonet · © año» con el logo de Colegios Amigó |
| Ventana de novedades | Círculo dorado, título condensado, «NOVEDADES» en Markdown, «Más tarde» / acción principal verde |
| Ajustes | 980 × 640, menú lateral de 220 px en `surface2`, apartado elegido en blanco con texto verde, filas «etiqueta | control» con ayuda en gris |
| Listados | `TablaPaginada` (patrón de Web Pedidos) |
| Avisos | Banda oscura flotante abajo que se va sola; ámbar para lo pendiente; diálogo solo para lo que exige actuar |
| Textos | Castellano, frases cortas, sin jerga técnica; los botones dicen lo que hacen («Exportar», «Aceptar cambios») |

Lo que cambia de una app a otra es solo el contenido de las tres zonas. Si alguna vez hace falta un componente nuevo, se diseña para que lo pueda usar cualquier app de la familia y se lleva también a Partes de salida.

## Overview

**Creative North Star: «La mesa del profesor».** Una herramienta que se usa pocas veces al año, pero con calma y con mucho que comprobar. Todo está a la vista y en el orden en que se hace: **elegir módulo → revisar lo oficial → rellenar lo propio → vista previa → exportar.**

### Named Rules

- **The Three Zones Rule** (heredada). Tres columnas fijas:
  - **Módulos** (300 px).
  - **Ficha y bloques** (flexible).
  - **Estado, vista previa y exportar** (340 px). El botón de exportar está siempre en el mismo sitio, abajo a la derecha.
- **The Only-What-He-Knows Rule.** La interfaz solo pide lo que únicamente sabe el profesor. Un campo nuevo necesita demostrar que no se puede sacar del catálogo ni calcular.
- **The Hidden Boilerplate Rule.** Los textos fijos de la plantilla **no aparecen nunca** en la interfaz: solo en la vista previa y en el documento (requisito de CarlosFB).
- **The Read-Only Official Rule.** Lo que viene del catálogo se ve en gris de solo lectura, con su fuente («BOE · comprobado el …»), y no se puede editar.
- **The Token Rule** (heredada). Todo color sale de `T[...]`.
- **The Paper Rule** (heredada). El documento generado no sigue el tema: es la plantilla del departamento.
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
| Cuerpo | Barlow | 14 px (13 secundario, 12 pequeño) | Todo lo demás |
| Etiquetas | Barlow Bold, mayúsculas, espaciado 0,9 px | 12 px | «DEL CURRÍCULO», «ESTADO», «VISTA PREVIA» |
| Datos | JetBrains Mono | 14 px | Código del módulo, RA1…RA6, horas en tablas |

Las mismas tres familias (OFL) van dentro de la app: `src/programaciones/recursos/fuentes/`.

## Layout

**Ventana principal:** 1100 × 700 (mínimo 980 × 620).

**Barra superior** (como en Partes de salida):
- Título «Programaciones».
- Curso escolar en chip (`2026-2027`).
- Estado del catálogo: «Catálogo al día · 2026-10-14» en `accent`, o «Cambios en el currículo» en `warn`.
- Botón dorado «↑ Actualizar a X.Y.Z» cuando hay versión nueva.
- Botón verde «Programaciones · N» (como «Partes recurrentes» en Partes de salida), que abre el listado, y «Ajustes». «Abrir…» y «Nueva a partir de…» están en el estado vacío y en el menú de la app.

**Columna izquierda (300 px):**
- Buscador con lupa («Código o nombre del módulo»).
- Chips de grado (GM · GS) y, debajo, chips de ciclo que se parten en filas (`FlujoLayout`).
- Chips de curso (1.º · 2.º) y «Limpiar».
- Recuento y lista de módulos en filas de 58 px: código en mono, nombre en dos líneas, etiqueta ciclo · curso en `gold_soft` e icono de estado (sin empezar · en curso · exportada).

**Centro:**
- Cabecera de la ficha: nombre del módulo (30 px), etiquetas de ciclo, curso y grado, código en mono, horas y h/semana.
- Caja **«DEL CURRÍCULO»** (`surface2`, solo lectura y plegable): RA con sus criterios, competencias del módulo, normativa y «Fuente: BOE … · comprobado el …».
- Debajo, la **barra de pasos** (chips) con los bloques del profesor: Profesorado · Unidades y evaluación · Empresa por RA · RA y competencias · Metodología y recursos. Cada chip lleva su estado: verde confirmado, ámbar heredado o vacío. El contenido del paso elegido va en una caja.

**Columna derecha (340 px):**
- «ESTADO»: lista de bloques con su icono, barra de progreso (bloques confirmados de 5) y las cifras grandes: horas de centro + empresa = total y % de empresa.
- Avisos de validación (`aviso` ámbar o rojo), cada uno con el enlace «Ir» a su campo.
- «VISTA PREVIA»: miniatura de la portada con sombra (máx. 320 px de alto) y el botón «Vista previa ⌘P».
- Hueco flexible.
- «EXPORTAR» con dos chips, «Word» y «PDF».
- «Exportar ⌘E» (verde, grande, 18 px), desactivado mientras haya validaciones rojas o bloques heredados sin confirmar.
- Debajo, la carpeta de destino en gris.

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

Todas con el estilo de Partes de salida: márgenes de 26/22 px, título en Barlow Condensed y botones abajo a la derecha (principal verde, el resto blancos, peligro en rojo).

| Ventana | Contenido |
| --- | --- |
| **Actualización disponible** | **La misma de Partes de salida** (`DialogoActualizacion`): círculo dorado «↑», «Hay una versión nueva: X.Y.Z», «NOVEDADES» en Markdown (la entrada del `CHANGELOG.md`), «Más tarde» y «Actualizar ahora». Descarga con barra de progreso |
| **Cambios en el currículo** | El mismo diálogo, con el círculo dorado «§» y el título «Ha cambiado el currículo de este módulo». Norma de origen con enlace, lista en Markdown de lo que cambia y qué bloques suyos quedan afectados. Botones «Más tarde» y «Aceptar cambios» (verde): **lo aprueba cada profesor** (ADR-015) |
| **Nueva a partir de…** | Zona de soltar (`ZonaSoltar`) para el `.docx` o `.programacion` anterior. Resumen en cifras de lo que se hereda (unidades, elementos, bloques), aviso de los RA que han cambiado y «Cancelar» / «Heredar» |
| **Exportando** | Barra de progreso con los pasos: «Rellenando la plantilla» → «Comprobando» → «Convirtiendo a PDF». Al terminar, un aviso flotante «Exportada en …» con «Mostrar en la carpeta» |
| **Vista previa** | 900 × 700, `QPdfView` con la marca «BORRADOR», zoom y página, y «Cerrar» |
| **Abierto con cambios de Word** | Aviso: «Este documento se ha modificado en Word después de exportarlo; esos cambios no se recuperan.» |
| **Ayuda** | Como `ui/ayuda.py`: pasos con capturas para añadir la carpeta de Teams a OneDrive |
| **Programaciones** (940 × 600) | Como «Partes recurrentes» de Partes de salida: `TablaPaginada` con casilla por fila (módulo, ciclo y curso, curso escolar, estado, última exportación). Abajo, «Abrir» y el botón verde «Enviar N por correo…» |
| **Enviar por correo** | Destinatarios (campo con los recordados en chips), chips «Word» y «PDF», asunto ya escrito, lista de adjuntos con su tamaño y total (aviso `warn` si se pasa del límite), «Cancelar» y «Crear correo» (opción A) o «Enviar» (opción B). Al terminar, aviso flotante. Los envíos van en `Tarea`, con su estado como en Partes de salida |

**Ajustes** (980 × 640, menú lateral de 220 px): Profesor · Carpeta de entrega · Exportación (formatos, programa para el PDF, idioma del documento) · Correo · Catálogo (versión, firma, «Comprobar ahora», cambios por aceptar) · Acerca de.

## Componentes heredados sin cambios

Botones (`primario`, `pequeno`, `peligro`, `grande`, `chip`), campos (radio 7 px, foco verde), casillas, `QProgressBar` (borde `line`, fondo `surface2`, bloque `accent`, 14 px), aviso flotante oscuro que se va solo, zona de soltar con borde discontinuo, `TablaPaginada` para «Programaciones recientes» (patrón de listados de Web Pedidos: buscador, 5/10/15/20/50 por página, «Limpiar filtros», cabeceras ordenables y pie «Mostrando 1–10 de N» con los extremos desactivados), barras de desplazamiento y tooltips.

## Presentación y «Acerca de»

La misma tarjeta de Partes de salida (588 × 348, banda verde en degradado con el engranaje del escudo, filete dorado, escudo en medallón y barra dorada de 6 px). Textos:
- «FORMACIÓN PROFESIONAL · EPLA».
- El título «Programaciones».
- Sin lema: las plantillas nuevas no lo usan (CarlosFB, 2026-10-14).
- La pastilla de versión.
- Pasos de carga: «Cargando el catálogo…» y «Comprobando el currículo…».

Mismos logos (escudo y Colegios Amigó). El icono de la app sigue el estilo del de Partes de salida y se dibuja en la maqueta.

## Do's and Don'ts

**Do:**
- Copiar el componente de Partes de salida antes de dibujar uno nuevo.
- Regenerar `docs/capturas/` tras un cambio visible.
- Mantener el flujo con teclado (⌘S guardar, ⌘P vista previa, ⌘E exportar).

**Don't:**
- Enseñar textos fijos de la plantilla.
- Dejar editar datos oficiales.
- Añadir campos «por si acaso».
- Usar colores fuera de los tokens.
- Poner diálogos de confirmación en el camino de exportar. La única excepción es sustituir un archivo que ya existe con el mismo nombre.
