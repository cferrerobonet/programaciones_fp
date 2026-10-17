# Modelo de datos

La app maneja tres conjuntos de datos, cada uno con su dueño:

| Conjunto | Dueño | Dónde vive | Cambia… |
| --- | --- | --- | --- |
| **Catálogo curricular** | CarlosFB, con la ayuda del vigía | `catalogo/` del repositorio → empaquetado y publicado firmado | Cuando cambia una norma |
| **Curso escolar** | CarlosFB | `catalogo/cursos/AAAA-AAAA.yaml` | Una vez por curso |
| **Programación** | Cada profesor | Archivo `.programacion` (la app lo guarda solo en la carpeta de datos, `almacen.py`) y copia dentro del `.docx` exportado | Cuando el profesor quiere |

Todo lleva esquema JSON (`src/programaciones/esquemas/`) y número de formato.

**Idiomas (ADR-013).** Todo texto del catálogo que irá al documento (nombres de módulo, RA, criterios, competencias, títulos de normas) se guarda como objeto por idioma: `texto: {es: "…"}`. Al principio solo hay `es`; `va` y `en` se añadirán en la fase F10. En las tablas de abajo se escribe `texto` por brevedad.

## 1. Catálogo

Lo genera `scripts/catalogo.py construir` desde el BOE y el DOGV ([CATALOGO_Y_FUENTES.md](CATALOGO_Y_FUENTES.md)): no se edita a mano. Formato `catalogo/1`; esquemas en `src/programaciones/esquemas/catalogo_*.schema.json`.

```
catalogo/
├── fuentes.yaml                cada documento oficial leído: URL, enlace, publicación, consulta y huella SHA-256
├── normativa.yaml              normas de los apartados 1.1 y 1.2, con título oficial, fecha, enlace y a qué se aplican
├── ciclos/<SIGLA>.yaml         un archivo por ciclo (11)
├── modulos/<id>.yaml           RA y criterios de cada módulo
├── cursos/2026-2027.yaml       fechas y periodos del curso escolar (CarlosFB, ADR-023)
├── version.yaml                versión AAAA.MM.DD[.n], fecha y huella del contenido (ADR-027)
└── vigia.yaml                  lo que el vigía ya ha visto (no va en la app ni en el paquete publicado)
```

Publicado (ADR-027), en la rama `catalogo-publicado`, lo genera `catalogo.yml`:

```
indice.json                     {datos: {formato: catalogo-indice/1, formato_catalogo, version, fecha, publicado, archivo,
                                 sha256, tamano, novedades, anterior, versiones}, clave, firma}
catalogo-<versión>.json.gz      {formato: catalogo-paquete/1, version, fecha, archivos: {ruta: texto YAML}}
```

Los códigos van siempre entre comillas en el YAML («'0518'»): con un lector YAML 1.2, una cifra con cero delante sería un número.

### `ciclos/<SIGLA>.yaml`

| Campo | Ejemplo (SEA) | Fuente |
| --- | --- | --- |
| `sigla`, `grado`, `familia`, `nombre`, `titulo` | `SEA`, `GS`, `Electricidad y Electrónica`, «Sistemas electrotécnicos y automatizados», «Técnico Superior en …» | Receta, art. 2 y título del RD, Decreto 95/2026 |
| `rd` | `{id: BOE-A-2010-15355, nombre, enlace, modificado_por: [BOE-A-2024-10685, BOE-A-2023-13217], correcciones: [], posteriores: […]}` | Análisis del BOE |
| `competencia_general` | Texto del art. 4 (literal). Con una errata del BOE, además `competencia_general_corregida` y `competencia_general_correccion` (el motivo): la corregida va al documento | RD (en ISO, RD 289/2023) |
| `competencias` | `[{letra: a, texto: …}, …]` (art. 5). En GA e IT, que numeran, la letra que corresponde (1 = a, con la ñ) y el número del BOE en `numero_boe` (ADR-018) | RD |
| `correspondencias_ecp` | `[{modulos: ['0602'], ecp: [{codigo: ECP1180_3, texto: …, uc: UC1180_3}], fuente: BOE-A-2023-13217}, …]`. Si el anexo imprime mal la UC, la buena en `uc` y la impresa en `uc_boe`, con su `correccion` | Anexo V B) vigente + RD 532/2025 |
| `modulos` | `[{codigo: '0526p', modulo: '0526', nombre, curso: 1, h_sem: 1, h_anuales: 35, tipo: proyecto}, …]` | Decreto 95/2026, anexo IV |
| `optativos_ofertados` | `[{codigo: CVOPS031, modulo: OPT-EE-IA, nombre, curso: 2, fuente}, …]` | Oferta del centro |
| `proyecto` | Código del Proyecto intermodular de 2.º | Decreto 95/2026 |
| `fuentes` | Documento de cada dato y huella del bloque del horario | — |

- `modulo` es el archivo de `modulos/` con los RA: `1665031` → `1665`, `0526p` → `0526`, `0237` → `0237-IT`. Es `null` en el hueco del optativo (CVOP…) y en lo pendiente, que lleva `pendiente` con su motivo.
- `tipo` de módulo: `propio` · `proyecto` · `ingles` · `empleabilidad` · `digitalizacion` · `sostenibilidad` · `autonomico` (CV0014, CV0015) · `optativo`.

### `modulos/<id>.yaml`

| Campo | Contenido |
| --- | --- |
| `id`, `codigo`, `nombre`, `tipo` | `0517`, `0517`, nombre oficial (el del RD; en el Proyecto, el del Decreto 95/2026) |
| `competencias_modulo` | Por ciclo: `{SEA: [a, b, d, …]}`, según las orientaciones pedagógicas. En el Proyecto, todas (el BOE dice «la totalidad de … las competencias … del título»). Vacío en los comunes |
| `contenidos` | Contenidos básicos por bloques, en el orden de la fuente: `[{titulo: {es}, puntos: [{es}, …]}]`. Una programación nueva lleva una unidad por bloque (ADR-031). No los tienen los proyectos |
| `contenidos_pendiente` | Motivo si la fuente no se puede leer por bloques con seguridad (texto pegado de los BOE de 2008, comunes del DOGV sin numerar): sin propuesta de unidades |
| `propuesta_ra_competencias` | **Propuesta de IA, no oficial** (ADR-031): `{SEA: {"1": [a, d], …}}`, las competencias de cada RA en cada ciclo. Sale de `scripts/propuestas/ra_competencias.yaml`, que guarda la huella de los RA: si el BOE cambia un RA, la propuesta del módulo se descarta |
| `ra` | `[{n: 1, texto: …, criterios: [{letra: a, texto: «Se han identificado…»}, …]}, …]`. Con erratas de numeración, `n_boe` o `letra_boe`. Con una errata de texto, además `corregido` (el que va al documento) y `correccion` (el motivo); el literal se queda en `texto` (ADR-018) |
| `fuente` | `{norma: BOE-A-2010-15355, tambien: […], bloque: «Anexo I, módulo 0517», version: 2010-10-08, huella: sha256:…, comprobado: 2026-10-17}` |

- Un módulo que está en dos ciclos se guarda **una vez** si el texto es idéntico en los dos reales decretos. Si no, va **uno por título** (`0237-IT` y `0237-IEA`, `0238-…`, `0260-CAR` y `0260-EMV`).
- Los optativos tienen `id` propio (`OPT-INGLES-ORAL`, `OPT-EE-IA`, `OPT-EE-FV`): el decreto no les da código y el del centro puede repetirse (0179).

### `normativa.yaml`

`[{id, ambito: estatal|autonomico, titulo, fecha, diario: BOE|DOGV, enlace, aplica: todos|GM|GS|[siglas], curso_escolar?, pendiente?}, …]`, por fecha creciente, como la lista del documento. Incluye el real decreto de cada título, las normas que lo modifican y sus correcciones de errores.

### `version.yaml`

`{formato: catalogo/1, version: 'AAAA.MM.DD[.n]', fecha, huella: sha256:…}` (esquema `catalogo_version.schema.json`). La huella es la de todos los archivos del catálogo salvo este y `vigia.yaml`; la escriben `construir` y `catalogo.py version`, y `comprobar` falla si no casa. Es la versión que guarda cada programación en `catalogo` (ADR-027).

### `cursos/AAAA-AAAA.yaml`

Lo da de alta CarlosFB (no lo genera `scripts/catalogo.py`), con su fuente; esquema `catalogo_curso.schema.json`, formato `curso/1`. El de 2026-2027 sale de las notas del curso en la bóveda (ADR-023). Sin el archivo de un curso, o con un dato en `pendiente`, el documento enseña «pendiente» y la definitiva espera (V-11).

| Campo | Valor 2026-2027 |
| --- | --- |
| `fuente` | `{documentos: […], confirmado: 2026-10-17}` |
| `evaluaciones` | `{inicial: 2026-09-30, primera: 2026-11-20, segunda: 2027-02-26, tercera: 2027-05-28}` |
| `ordinaria` | `{desde: 2027-05-31, hasta: 2027-06-03}` |
| `extraordinaria_desde` | 2027-06-14 |
| `formacion_empresa` | Por grado y curso: `{GS: {2: [{jornada: 8, dias: 43, desde: 2027-03-08, hasta: 2027-05-21}, {jornada: 7, dias: 50, desde: 2027-03-03, hasta: 2027-05-21}], 1: […]}, GM: {…}}` |
| `formacion_empresa_ciclo` | Excepciones de un ciclo a la de su grado: `{GA: {1: [{jornada: 8, dias: 20, desde: 2027-02-01, hasta: 2027-02-26}, …]}}` |
| `pendiente` | `[{ciclo: GA, curso: 2, motivo: …}]`: lo que las fuentes no dan |
| `proyecto` | Días de Proyecto intermodular por curso (`[{desde, hasta}]`); informativo, no sale en el documento |

- La resolución de instrucciones del curso no va aquí: es la norma de `normativa.yaml` con `curso_escolar: 2026-2027`.
- La 3.ª evaluación acaba el 28/05 aunque el calendario escolar diga el 27 (CarlosFB, 2026-10-11, confirmado el 2026-10-17: ADR-023), como las programaciones de referencia.
- FE de 2.º a 7 h: 50 días, como sale de la propuesta del centro (CarlosFB, 2026-10-17).

## 2. Programación (archivo `.programacion`)

JSON, formato `programaciones/1`, con esquema en `src/programaciones/esquemas/programacion.schema.json` (`programacion.py`: lectura, validación, migraciones y escritura atómica). Ejemplo con datos ficticios:

```json
{
  "formato": "programaciones/1",
  "app": "1.0.0",
  "catalogo": "2026.10.17",
  "plantilla": "2026-10-06",
  "idioma": "es",
  "curso_escolar": "2026-2027",
  "ciclo": "SEA", "curso": 2, "modulo": "0517",
  "profesorado": ["Profesora Ficticia"],
  "unidades": [
    {"id": "u1", "titulo": "UD01. Unidad ficticia", "descripcion": ["Lo que incluye, si hace falta."],
     "horas": 10, "trimestre": 1, "elemento": "e1"},
    {"id": "u2", "titulo": "Práctica 1: Práctica ficticia", "horas": 7, "trimestre": [1, 2], "elemento": "e2"}
  ],
  "elementos": [
    {"id": "e1", "tipo": "E", "nombre": "EXAMEN 1", "ra": [1, 2]},
    {"id": "e2", "tipo": "P", "nombre": "PRÁCTICA 1", "ra": [3, 4, 6], "detalle": ["(16 prácticas)"],
     "peso_ajustado": {"valor": 20, "texto": "1,25 % / x práctica"}}
  ],
  "empresa": {"2": 12, "3": 13, "4": 13, "5": 13, "6": 12},
  "centro_ajustado": {"3": 8, "4": 10, "6": 10},
  "modalidad": {"1": "Centro", "2": "Mixto", "5": "Empresa"},
  "columna_pct_curso": false,
  "ra_competencias": {"1": ["a", "d"], "2": ["a", "b", "d"]},
  "contenidos": [],
  "notas_tabla4": [{"texto": "Nota bajo la tabla 4."}],
  "notas_tabla41": [],
  "metodologia": [{"texto": "Párrafo propio con el **cuaderno de apuntes** en negrita."}],
  "metodologia_final": [{"texto": "Finalmente, …"}],
  "recursos": [{"texto": "Cuaderno ficticio.", "nivel": 0}, {"texto": "Detalle del recurso.", "nivel": 1}],
  "espacios": [{"texto": "**Aula ficticia** con su material.", "nivel": 0}],
  "actividades": [],
  "textos_propios": {},
  "bloques": {"profesorado": "confirmado", "unidades": "heredado", "empresa": "heredado"},
  "heredada_de": {"profesor": "…", "curso_escolar": "2025-2026", "archivo": "…"},
  "historial": [{"fecha": "2026-10-14T10:00", "accion": "exportada"}]
}
```

- **Estado de cada bloque:** `vacio` · `heredado` · `confirmado`. Lo importado de un .docx queda `heredado` (ADR-008).
- **Párrafos del profesor** (`contenidos`, notas de las tablas, metodología, recursos, espacios, actividades y textos propios): `{texto, nivel}`. Sin `nivel`, párrafo normal; `0`, viñeta; `1` y `2`, viñetas anidadas. En el texto, `**…**` es negrita. Las normas del catálogo que se citen salen con su enlace.
- **Unidades:** `trimestre` es un número o una lista (`[1, 2]` → «1 y 2»). `descripcion`, líneas bajo el título en la tabla 4.
- **Elementos:** `tipo` E, P o T (apartado 11.2). `detalle`, las líneas bajo el nombre; por defecto, «(Nh)». `peso_ajustado`, el peso que fija el profesor en vez del calculado: `valor` (% del módulo, el que cuenta para V-12) y, si lo escribe de otra forma, `texto` (ADR-018, punto 9).
- **`columna_pct_curso`:** con `true`, la tabla 4.1 lleva la columna «% del curso (aprox.)».
- **`textos_propios`:** bloques fijos de la plantilla que el profesor sustituye (ADR-020): `calificacion`, `instrumentos`, `elementos` y `asistencia_y_pruebas`.
- **Lo que no se guarda:** nada de lo que se puede calcular o sacar del catálogo (pesos sin ajustar, tabla 4.1, textos).

## 3. Cálculos (`calculos.py`)

Con `H` = horas del módulo, `h(e)` = suma de las horas de las unidades del elemento `e` y `R(e)` = sus RA:

| Resultado | Fórmula | Comprobación con PIICT |
| --- | --- | --- |
| Peso del elemento | `h(e) / H`, con un decimal, o el `peso_ajustado` del profesor; con ajustes, los pesos suman el % de centro (V-12) | EXAMEN 1: 24 / 166 = 14,5 % |
| Horas de centro del RA `r` (propuesta) | `Σ h(e) / |R(e)|` sobre los elementos que contienen `r`, redondeado con la regla de abajo | RA1 = 24/2 + 16/2 + 12/2 + 16/2 = 34 ✓ · RA2 = 41 ✓ |
| Horas de centro del RA `r` (definitiva) | La propuesta, o la que fije el profesor en `centro_ajustado`, siempre entre el mínimo (elementos exclusivos de `r`) y el máximo (todos los que lo incluyen), y con la suma igual a las horas de centro | RA3: propuesta 7,33 → ajustada a 8 · RA4: 9,33 → 10 · RA6: 11,33 → 10 (suma 103 ✓) |
| Horas totales del RA | centro + `empresa[r]` | RA2 = 41 + 12 = 53 |
| Modalidad | La que elige el profesor (`modalidad`, ADR-030; V-13 si no casa con las horas). Sin elegir: `Centro` si empresa = 0 · `Empresa` si centro = 0 · si no, `Mixto` · sin horas (0/0, V-10), «-» | RA5: 0 + 13 → Empresa |
| % de empresa y de centro de un RA mixto (tabla 4.1, ADR-025) | empresa al entero más cercano (,5 hacia arriba) de `100 · empresa / total`; centro = 100 − empresa. En Centro o Empresa, «-» | RA3: 8 + 13 → 38 % y 62 % · 21 + 3 → 87 % y 13 % |
| % de empresa | `ceil(100 · Σ empresa / H)` | 63 / 166 = 37,95 → 38 % |
| % de centro | `100 − % empresa` | 62 % |

El reparto a partes iguales (el de `curriculo.py`) reproduce RA1 y RA2 de PIICT, pero no RA3, RA4 y RA6, que CarlosFB ajustó a mano en enteros dentro de los límites (regla 3 de la guía `programacion-didactica`). Por eso la app **propone** el reparto y deja **ajustarlo** en el bloque «Empresa por RA», con la validación V-04.

**Regla de la propuesta** (CarlosFB, 2026-10-17, ADR-018): cada reparto al entero más cercano (,5 hacia arriba) y lo que sobre o falte para cuadrar las horas de centro va al RA con más horas de los que se han redondeado. En PIICT: 7,33 / 9,33 / 11,33 → 7 / 9 / 12; la programación lleva 8 / 10 / 10, el ajuste del profesor (`centro_ajustado`).

## 4. Migraciones

Un cambio incompatible sube el formato (`programaciones/2`) y añade su función en `programacion.py`. La app abre siempre los formatos anteriores.
