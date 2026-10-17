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

**Maqueta v0** (aprobada por CarlosFB el 2026-10-17): `../Maqueta v0 (2026-10-14)/` en la bóveda, con `Maqueta interactiva.html` y una captura por pantalla.

Tokens: `src/programaciones/ui/estilo.py`, copia del de Partes de salida.

## Familia de apps de CarlosFB

**Requisito de CarlosFB (2026-10-14):** todas sus apps se notan hechas por la misma mente, con el mismo diseño. Partes de salida es la referencia; Programaciones **no tiene variaciones propias** en lo que comparten todas.

| Invariante de la familia | Cómo es (igual en todas) |
| --- | --- |
| Paleta | Verde EPLA y dorado, neutros verdosos, claro y oscuro según el sistema: tokens de `estilo.py` |
| Ventana principal | Las tres zonas, con el botón grande verde abajo a la derecha (The Three Zones Rule) |
| Barra superior | Nombre en Barlow Condensed 20 px + « · área» en gris; a la derecha, estado, recuentos, botón verde, aviso dorado de actualización y «Ajustes» |
| Presentación, novedades, Ajustes, listados y avisos | Los de Partes de salida, sin cambios (más abajo, solo lo propio) |
| Textos | Castellano, frases cortas, sin jerga técnica; los botones dicen lo que hacen («Exportar», «Aceptar cambios») |

Lo propio es el contenido de las tres zonas; un componente nuevo se diseña para toda la familia (y va a Partes de salida).

## Overview

**Creative North Star: «La mesa del profesor».** Se usa pocas veces al año, con calma y con mucho que comprobar. Todo está a la vista y en orden: **elegir módulo → revisar lo oficial → rellenar lo propio → vista previa → exportar.**

### Named Rules

- **The Three Zones Rule** (heredada): módulos (300 px) · ficha y bloques (flexible) · estado, vista previa y exportar (340 px), con exportar siempre abajo a la derecha.
- **The Only-What-He-Knows Rule.** Solo se pide lo que únicamente sabe el profesor: un campo nuevo demuestra que no sale del catálogo ni se calcula.
- **The Hidden Boilerplate Rule.** Los textos fijos de la plantilla **no aparecen nunca** en la interfaz: solo en la vista previa y en el documento (CarlosFB).
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
- Estado del catálogo: «Catálogo al día · 2026-10-14» en `accent`, o «Cambios en el currículo» en `warn`.
- Recuento «Curso 2026-2027 · N módulos · N programaciones». El curso y su carpeta, en Ajustes → Curso escolar (y menú «Curso escolar…»).
- Avisos dorados (`zona_avisos`): «↑ Actualizar a X.Y.Z» y «§  Cambios en el currículo · N» (F5: catálogo publicado con cambios; N, programaciones con cambios por aceptar). Los dos con el mismo botón dorado pequeño y el mismo comportamiento: fijo mientras haya algo y, la primera vez, la ventana de novedades por encima (círculo dorado con «↑» o «§»).
- «Programaciones · N» (verde) y «Ajustes». «Abrir…» y «Nueva a partir de…», en el estado vacío y en el menú.

**Columna izquierda (300 px):**
- Buscador con lupa («Código o nombre del módulo»).
- Chips de grado (GB · GM · GS); en la lista, el Proyecto de GB con su código del RD (3160) en el cuadro, «★ Favoritos», de ciclo (`FlujoLayout`) y de curso, y «Limpiar» (también quita «Favoritos»).
- Filas de 58 px: código en `gold_soft`, nombre en dos líneas, «2.º SEA · G. Superior», icono de estado y la estrella (`gold` rellena si es favorito; clic, clic derecho o ⌘D; nombre accesible y estado).

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

**Estados vacíos** (como «Busca un alumno»): «Elige un módulo» y «Empieza esta programación o hereda la del curso pasado», con dos botones.

## Bloques del profesor

| Bloque | Control |
| --- | --- |
| Profesorado | Lista de nombres (el del profesor, rellenado desde Ajustes) con «Añadir» |
| Unidades y evaluación | Chips «Unidades», «Elementos» y «Notas». Unidades (filas de 30 px): título, horas, trimestre y elemento; RA y peso en gris. Elementos: tipo, nombre, RA (menú), horas y peso en gris y «A mano». Arrastrar o Alt+↑/↓ ordena; Supr quita |
| Empresa por RA | Las columnas de la 4.1 (ADR-030): RA · Modalidad (desplegable con su color: Centro `surface2`, Mixto `accent_soft`, Empresa `gold_soft`) · Horas centro (ajustable; `gold_soft` si no es la propuesta, que va en la ayuda) · Horas empresa · % centro y % empresa en gris, calculados. «—» donde no aplica. «Volver a la propuesta», «% del curso» y notas de la 4.1 |
| Ámbitos de GB (ADR-032) | Solo tres pasos (Profesorado · Unidades · Metodología). En «Unidades y evaluación», «CE» donde dice «RA», la columna «Parte» en lugar de «Peso» (desplegable) y el chip «Partes» (tabla nombre y horas; en Comunicación y Ciencias Sociales, las del currículo y de solo lectura). Sin pesos en los elementos |
| RA y competencias | Rejilla de RA × letras de competencia del módulo, con casillas. Las letras posibles salen del catálogo. Si lo marcado no coincide con la propuesta de IA del catálogo, botón pequeño «Proponer corrección con IA» bajo el estado: diálogo de aviso (círculo `accent` con «✦») con las diferencias RA por RA y «Mantener las mías» · «Aplicar la propuesta» (ADR-031) |
| Metodología y recursos | Recursos y espacios con chips habituales (Teams, CYPE, taller…); metodología propia (600 caracteres), final, actividades y «Usar un texto propio». Párrafos como texto: «- » viñeta, `**negrita**` |

Un bloque heredado muestra arriba la banda `warn_soft`: «Heredado de *Nombre* (2026-2027) · revisa y confirma», con «Confirmar bloque», que la quita.

## Ventanas modales

Como en Partes de salida: márgenes 26/22 px, título condensado y botones abajo a la derecha.

| Ventana | Contenido |
| --- | --- |
| **Actualización disponible** | **La de Partes de salida** (`DialogoActualizacion`): «↑» dorado, «Hay una versión nueva: X.Y.Z», «NOVEDADES» (su entrada del `CHANGELOG.md`), «Más tarde» / «Actualizar ahora» y descarga con progreso |
| **Cambios en el currículo** | El mismo diálogo, con el círculo dorado «§» y el título «Ha cambiado el currículo de este módulo». Norma de origen con enlace, lista en Markdown de lo que cambia y qué bloques suyos quedan afectados. Botones «Más tarde» y «Aceptar cambios» (verde): **lo aprueba cada profesor** (ADR-015) |
| **Nueva a partir de…** | Zona de soltar (`ZonaSoltar`) para el `.docx` o `.programacion` anterior. Resumen en cifras de lo que se hereda (unidades, elementos, bloques), aviso de los RA que han cambiado y «Cancelar» / «Heredar» |
| **Exportando** | Barra de progreso: «Rellenando la plantilla» → «Comprobando» → «Convirtiendo a PDF»; al terminar, aviso «Exportada en …» con «Mostrar en la carpeta» |
| **Vista previa** | 900 × 700, `QPdfView` con «BORRADOR»; con varias, un desplegable elige cuál |
| **Abierto con cambios de Word** | Aviso: los cambios hechos en Word tras exportar no se recuperan |
| **Ayuda** | Como `ui/ayuda.py`: añadir la carpeta de Teams a OneDrive |
| **Programaciones** (940 × 600) | `TablaPaginada` con casilla por fila. Abajo y con clic derecho, sobre las marcadas: «Abrir» (solo una), «Vista previa», «Exportar N a carpeta…», «Enviar N por correo…» y «Borrar N…» (`peligro`), activos según cuántas hay |
| **Exportar a una carpeta** | Carpeta, «Word» y «PDF» y cada una con «se exporta», «ya está: se preguntará» (`warn`) o «avisos en rojo» (`danger`) |
| **Enviar por correo** | Programa que se abrirá, destinatarios (chips de Ajustes y otros), «Word» y «PDF», adjuntos con tamaño o «se exporta antes», total (`warn` si pasa de 20 MB), asunto, mensaje y «Crear correo». En `Tarea` |
| **Borrar** | Dice qué va a la papelera y que lo exportado se queda |

**Ajustes** (como en Partes de salida): Profesor · Curso escolar (curso, fechas y carpeta de entrega) · Exportación (formatos, programa del PDF, idioma y correo del pie) · Correo (destinatarios, programa de correo y plantilla) · Catálogo · Acerca de. Lo que no tiene datos sale «pendiente».

## Componentes heredados sin cambios

Botones, campos, casillas, `QProgressBar`, aviso flotante, zona de soltar, barras de desplazamiento y tooltips, como en Partes de salida. Los listados usan `TablaPaginada` (patrón de Web Pedidos: buscador, 5/10/15/20/50 por página, «Limpiar filtros», cabeceras ordenables, pie «Mostrando 1–10 de N» con los extremos desactivados).

## Presentación y «Acerca de»

La tarjeta de Partes de salida (588 × 348): «FORMACIÓN PROFESIONAL · EPLA», «Programaciones», sin lema (CarlosFB, 2026-10-14), pastilla de versión y pasos «Cargando el catálogo…» y «Comprobando el currículo…». Mismos logos. **Icono** (`imagenes/`; `.ico` e `.icns` con `scripts/crear_icono.sh`): tablilla con la tabla de RA y sello verde de visto bueno sobre violeta, de la familia de Partes de salida. Paleta: violeta `#5E4B9C` y `#E3DDF2`, verde `#2E7A3A`, dorado `#E3A84B`, tinta `#1C2A20`.

## Do's and Don'ts

**Do:** copiar el componente de Partes de salida antes de dibujar uno nuevo; regenerar `docs/capturas/` tras un cambio visible; mantener el flujo con teclado (⌘S, ⌘P, ⌘E).

**Don't:** poner diálogos de confirmación en el camino de exportar (excepción: sustituir un archivo del mismo nombre).
