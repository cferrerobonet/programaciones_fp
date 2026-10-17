# Cambios

Formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y [SemVer](https://semver.org/lang/es/). Cada entrada `## [X.Y.Z] - AAAA-MM-DD` es también la nota del release y **lo que ve el profesorado en la ventana de novedades**: se escribe para ellos, sin jerga técnica.

## [Sin publicar]

## [0.2.0] - 2026-10-17

### Añadido

- **Enviar por correo** una o varias programaciones: en «Programaciones», márcalas y pulsa «Enviar por correo…». Eliges los destinatarios (los habituales y otros), si van en Word, en PDF o en los dos, y revisas el asunto y el mensaje, que ya vienen escritos. La app abre un correo nuevo en tu Outlook o en Mail con los archivos adjuntos y **tú lo envías desde tu cuenta**: la app no guarda contraseñas ni envía nada por su cuenta. Si alguna no estaba exportada, la exporta antes. Si los adjuntos pasan de 20 MB, te avisa.
- **Ajustes → Correo:** tus destinatarios habituales, el programa de correo que se usa y el texto del asunto y del mensaje.
- **Más cosas en «Programaciones»:** con las que marques, «Abrir» (una), «Vista previa» (si son varias, eliges cuál ves), «Exportar a carpeta…» (eliges la carpeta y si Word, PDF o los dos; nunca sustituye un archivo sin preguntarte) y «Borrar…». Con botones abajo o con el botón derecho.
- **Borrar** quita la programación de la lista de este equipo y manda su archivo de trabajo a la papelera, de donde la puedes recuperar. Los Word y PDF que exportaste y la carpeta de Teams no se tocan.
- **Favoritos:** pulsa la estrella de un módulo (o el botón derecho, o ⌘D / Ctrl+D) y con el filtro «Favoritos» verás solo los tuyos.

### Cambiado

- **La tabla 4.1 «Ponderación de cada RA»** tiene otro formato: modalidad, horas de centro y de empresa (con «-» cuando no hay) y el porcentaje de centro y de empresa de los RA mixtos, que suman siempre 100. La fila TOTAL suma las horas de centro y de empresa. Si usas la columna «% del curso», va al final.
- **El curso escolar está en Ajustes → Curso escolar**, con sus fechas y la carpeta de entrega; el botón del curso de arriba a la derecha desaparece. También se abre desde el menú, «Curso escolar…».

### Corregido

- En Word, la columna de los RA de la tabla 4 (por ejemplo, «RA1 → RA6») salía en Times New Roman. Ahora todo el documento sale con la letra de la plantilla.

## [0.1.2] - 2026-10-17

### Corregido

- La 3.ª evaluación acaba el 28 de mayo de 2027, como decidió el centro (la 0.1.1 decía el 27).

## [0.1.1] - 2026-10-17

### Añadido

- Las fechas del curso 2026-2027 ya están dentro: evaluaciones, convocatorias ordinaria y extraordinaria y los periodos de formación en empresa de cada ciclo y curso (1.º de Gestión Administrativa, en febrero). Con ellas ya puedes exportar la programación definitiva.

### Pendiente

- La formación en empresa de 2.º de Gestión Administrativa: hasta tenerla, sale como «pendiente» y esa programación no se puede exportar como definitiva.

## [0.1.0] - 2026-10-17

Primera versión, para probarla antes del piloto con el departamento.

### Añadido

- Eliges tu módulo buscándolo por código o nombre, o filtrando por grado, ciclo y curso. La ficha enseña sus datos oficiales (resultados de aprendizaje, criterios, competencias y normativa, con su fuente) sin que tengas que tocarlos.
- Empiezas la programación en blanco o «Nueva a partir de…» la del curso pasado, tuya o de otro profesor, desde su Word o su archivo `.programacion`: lo tuyo llega como «heredado» y lo confirmas bloque a bloque.
- Cinco bloques con lo que solo sabes tú: profesorado; unidades y elementos de evaluación (arrastrar para ordenar, pesos calculados y, si quieres, puestos a mano); horas de empresa por RA con el reparto de centro que propone la app y que puedes ajustar; competencias de cada RA; y metodología, recursos, espacios, actividades y, si hace falta, tus propios textos para los bloques fijos.
- A la derecha ves en todo momento el estado de cada bloque, las horas de centro y de empresa y los avisos de lo que no cuadra, cada uno con «Ir» al sitio donde se arregla.
- Vista previa en PDF con la marca «BORRADOR» y su miniatura.
- «Exportar» guarda el Word y el PDF con el nombre de siempre en la carpeta de Teams del curso; nunca sustituye un archivo sin preguntarte. Al abrir ese Word con la app recuperas todo, y te avisa si se cambió en Word después.
- Tus programaciones se guardan solas en este equipo (con las diez últimas copias) y las tienes todas en «Programaciones».
- Si cambia el currículo de tu módulo, la app te enseña qué cambia y qué bloques tuyos afecta; tú decides cuándo aceptarlo.
- La primera vez de cada curso solo te pide tu nombre y la carpeta de Teams.
- La programación se genera con la plantilla del departamento (la de PIICT): portada, normativa ordenada por fecha y con enlaces, estándares de competencia, competencias, tablas de secuenciación y de ponderación de los RA que cuadran solas, fechas del curso, formación en empresa y criterios de evaluación de cada RA.
- Las erratas del BOE en los criterios salen corregidas y los nombres de los módulos son los del Decreto 95/2026.
- El documento exportado lleva dentro todos los datos de la programación: al abrirlo se recuperan, y la app avisa si se cambió en Word.
- Se pueden importar las programaciones que ya existen en Word como punto de partida.
- La app propone el peso de cada elemento de evaluación y el profesor lo puede cambiar; avisa si los pesos no suman lo que deben. La tabla de ponderación de los RA puede llevar el «% del curso».
- Los proyectos intermodulares salen con su propia tabla de tareas y sus criterios de calificación, sin exámenes.
- PDF con el Word del equipo o, si no hay, con LibreOffice; vista previa con la marca «BORRADOR».
- La app de escritorio para macOS (Mac con chip de Apple) y Windows, con instalador y versión portable que no necesita instalarse. Mismo aspecto que Partes de salida: pantalla de presentación, ventana con los módulos a la izquierda, la ficha en el centro y el estado y «Exportar» a la derecha, en modo claro y oscuro.
- Ajustes: tu nombre para la portada, la carpeta de entrega del curso (la de Teams sincronizada con OneDrive o su enlace), con una ayuda para añadirla a OneDrive, los formatos y el programa del PDF, y el correo del departamento que sale en el pie del documento.
- Aviso de versión nueva con sus novedades y actualización con un clic: el instalador se descarga solo y se comprueba antes de abrirlo.
- Catálogo de los 11 ciclos del centro: sus módulos con curso y horas (Decreto 95/2026) y, de cada módulo, los resultados de aprendizaje y criterios de evaluación oficiales, las competencias del título, los estándares de competencia y la normativa, con su fuente en el BOE o el DOGV. Faltan el Proyecto intermodular de grado medio y los optativos que el centro aún no ha indicado.
- Icono de la app.

### Corregido

- El texto vertical del margen izquierdo ya no se monta sobre el escudo de la esquina superior.

### Pendiente

- Las fechas de evaluación y de formación en empresa del curso 2026-2027: mientras no estén, la vista previa las enseña como «pendiente» y la exportación definitiva espera.
- Enviar las programaciones por correo: falta decidir cómo se envía.
