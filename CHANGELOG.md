# Cambios

Formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y [SemVer](https://semver.org/lang/es/). Cada entrada `## [X.Y.Z] - AAAA-MM-DD` es también la nota del release y **lo que ve el profesorado en la ventana de novedades**: se escribe para ellos, sin jerga técnica.

## [Sin publicar]

## [0.10.0] - 2026-10-19

### Añadido

- **Programaciones del formato antiguo:** «Nueva a partir de…» lee también las programaciones del formato anterior del departamento (con «Temporalización y distribución de resultados de aprendizaje» y «Ponderación de cada RA»). La app recoge las unidades y sus elementos de evaluación, las horas en empresa y la modalidad de cada RA, la metodología, los recursos y los espacios, y lo que hayas cambiado en la evaluación. Lo demás (normativa, objetivos, competencias, resultados de aprendizaje, contenidos) lo pone, como siempre, el catálogo. El documento se exporta igual que cualquier otra programación.
- No hace falta renombrar el archivo: el módulo se saca de la portada. Solo si ese código está en varios ciclos y la portada no dice cuál, la app pide renombrarlo como «SIGLA N - código - Nombre del módulo.docx».
- El formato antiguo no relaciona cada resultado de aprendizaje con sus competencias: esa tabla queda por completar. Como siempre, todo lo importado queda «heredado» hasta que lo revises y lo confirmes.

## [0.9.1] - 2026-10-19

### Corregido

- **Windows: la vista previa y el PDF ya no fallan con «Clase no registrada».** En algunos equipos quedan restos de un Office que ya no está (o solo se usa Word en la web) y la app creía que había Word. Ahora comprueba que Word de verdad se puede abrir; si no, hace el PDF con LibreOffice.
- **Si no se puede hacer el PDF, la app dice por qué y qué hacer:** que falta Word de escritorio o LibreOffice, que LibreOffice es gratis (libreoffice.org) y, si Word está pero falla, cómo repararlo. Mientras tanto, el Word (.docx) se sigue exportando.

## [0.9.0] - 2026-10-19

### Añadido

- **Linux:** ya hay una versión de Programaciones para Linux (x86_64), como las de Windows y macOS. Se baja de las releases del repositorio, en un archivo comprimido: se extrae y se abre con «Programaciones.sh». Si quieres que salga en el menú de aplicaciones, ejecuta una vez «instalar.sh». Cuando haya una versión nueva, la app la descarga y te dice cómo ponerla en su sitio.

## [0.8.0] - 2026-10-18

### Cambiado

- **Fechas de las convocatorias de 2026-2027**, en Grado Básico, Medio y Superior: el documento dice ahora «La convocatoria ordinaria finalizará el 8 de junio de 2027 y la convocatoria extraordinaria finalizará el 22 de junio de 2027». Son fechas de fin, como las de las evaluaciones. En los ámbitos de Grado Básico, la tabla de fechas las da como las evaluaciones: 08/06/2027 y 22/06/2027.
- **Hace falta esta versión** para recibir los datos curriculares nuevos: las versiones anteriores no los aceptan y piden actualizarse.

### Añadido

- **Módulo optativo de Grado Medio** (Instalaciones Eléctricas y Automáticas, Instalaciones de Telecomunicaciones, Gestión Administrativa, Carrocería y Electromecánica de Vehículos): en 2.º, «Inglés oral para entornos profesionales» (ANEXO X-I), en el apartado 2.2 de la programación.

## [0.7.0] - 2026-10-17

### Añadido

- **Los ámbitos de Grado Básico** (Comunicación y Ciencias Sociales y Ciencias Aplicadas, I y II) ya se programan, con su propia plantilla: las competencias específicas con sus descriptores y criterios, una tabla de temporalización y otra de ponderación por cada parte del ámbito, la calificación IN, SU, BI, NT y SB, y los apartados de evaluación, criterios y recuperación del modelo del departamento.
- **Partes del ámbito:** en «Unidades y evaluación», el chip «Partes». En Comunicación y Ciencias Sociales vienen las materias del currículo con sus horas; en Ciencias Aplicadas las defines tú (por ejemplo, Matemáticas y Ciencias). Cada unidad va a una parte y el peso de cada competencia se calcula solo.
- En un ámbito solo hay tres pasos: profesorado, unidades y metodología.

### Corregido

- **Índice del documento:** sus números de página salen siempre bien, también en la vista previa.

## [0.6.0] - 2026-10-17

### Añadido

- **Grado Básico:** los cuatro ciclos del centro (Electricidad y Electrónica, Informática y Comunicaciones, Mantenimiento de Vehículos y Servicios Administrativos), con sus módulos y horas, RA, criterios, competencias y normativa. Los módulos técnicos, el Itinerario personal para la empleabilidad y el Proyecto intermodular de aprendizaje colaborativo se programan como en Grado Medio y Superior (con la misma tabla 4.1). Nuevo filtro «G. Básico».
- **Los ámbitos comunes** (Comunicación y Ciencias Sociales y Ciencias Aplicadas) ya aparecen en la lista, pero se programarán con su propia plantilla en la próxima versión.

### Corregido

- **Módulos comunes** (inglés, itinerarios para la empleabilidad, digitalización, sostenibilidad…): los apartados 3 y 11 citan el decreto que trae su currículo, no el del título.

### Pendiente

- La **formación en empresa de Grado Básico** aún no está en el calendario: sale «pendiente» y la programación definitiva espera.

## [0.5.0] - 2026-10-17

### Añadido

- **Una programación nueva ya no empieza vacía.** Al pulsar «Empezar en blanco», el apartado 4 trae una unidad por cada bloque de contenidos básicos del módulo (los del BOE o el DOGV), con las horas repartidas y el trimestre; tú añades los elementos de evaluación y ajustas lo que quieras. Y el paso «RA y competencias» trae ya marcadas las competencias de cada RA (una propuesta hecha con IA, no un dato oficial). Los dos quedan «por revisar» hasta que los confirmes.
- **«Proponer corrección con IA»** en el paso «RA y competencias»: si en una programación importada o heredada las competencias de algún RA no coinciden con la propuesta de la app, un botón te enseña las diferencias RA por RA y eliges: mantener las tuyas o aplicar la propuesta.

### Corregido

- **0959 Sistemas eléctricos, neumáticos e hidráulicos (ARI):** el enunciado del RA4 ya no acaba en «Criterios de calificación:» (una errata del BOE que se colaba en el documento).

## [0.4.2] - 2026-10-17

### Cambiado

- **Word trabaja sin que lo veas.** Para hacer la vista previa o el PDF, la app abre Word en segundo plano y, si no lo tenías abierto, lo cierra al terminar; tú solo ves la vista previa. El documento tampoco aparece en los recientes de Word.

## [0.4.1] - 2026-10-17

### Corregido

- **Vista previa, PDF y correo con Word en Mac, ahora sí.** La 0.4.0 no llegaba a hacer el PDF («Operation not permitted»). Word se quedaba esperando a que contestaras si actualizaba los campos del documento, y la app intentaba guardar el PDF antes de que Word lo tuviera abierto. Ahora el PDF sale sin preguntar nada, con las páginas del índice al día. Si alguna vez Word pide «Conceder acceso al archivo», pulsa «Seleccionar…» y «Conceder acceso»: solo lo pide la primera vez.

## [0.4.0] - 2026-10-17

### Cambiado

- **La tabla «Empresa por RA» tiene las mismas columnas que la tabla 4.1 de la programación:** RA, Modalidad, Horas centro, Horas empresa, % centro y % empresa. La modalidad la eliges tú (Centro, Mixto o Empresa) y pones las horas; los porcentajes se calculan solos. Al importar una programación, se rellenan con lo que dice su tabla. Si la modalidad no casa con las horas, sale un aviso en rojo.

### Corregido

- **Vista previa y PDF con Word en Mac:** Word ya no pide «Conceder acceso al archivo» cada vez.
- **Enviar por correo:** si un PDF no se ha podido hacer, el mensaje ya no lo nombra; y si no queda nada que adjuntar, no se abre un correo vacío y la app te dice por qué.

## [0.3.0] - 2026-10-17

### Añadido

- **Avisos de cambios en la normativa.** Igual que te avisa de una versión nueva, la app te avisa cuando cambia la normativa de su catálogo o aparece una nueva: sale el botón dorado «§ Cambios en el currículo» arriba y, la primera vez, una ventana que dice qué normas cambian, a qué módulos afectan (los tuyos, primero) y qué cambia en sus RA, criterios y horas.
- **Tú decides en cada programación.** Ninguna cambia sola: con «Revisar mis programaciones» abres la tuya, ves la diferencia y pulsas «Aceptar cambios» o «Más tarde». Mientras no aceptes, sigue con su versión y la app te lo recuerda (el botón dorado cuenta las que tienes pendientes).
- **Ajustes → Catálogo:** la versión y la fecha del catálogo que usas, cuándo se comprobó por última vez y «Comprobar ahora». La app lo comprueba sola al arrancar, como mucho una vez al día, y solo acepta un catálogo publicado con su firma comprobada. Sin conexión, todo sigue funcionando con el que tiene.

### Cambiado

- **En Mac, la actualización sustituye la app en la carpeta donde la tienes** (por ejemplo, «Aplicaciones/EPLA»): «Actualizar ahora» la descarga, cierra la app, la cambia y la vuelve a abrir, sin arrastrar nada. Si no se puede (sin permiso en esa carpeta), se abre el instalador como antes y la app te dice a qué carpeta arrastrarla. **Funciona a partir de esta versión:** para pasar a la 0.3.0 todavía se usa el instalador; arrastra «Programaciones» a la carpeta donde ya la tenías y sustituye la que hay. En Windows no cambia nada: el instalador ya sustituye la de antes.
- El instalador de macOS ya no trae el archivo «LÉEME - si dice que está dañada.txt».

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
