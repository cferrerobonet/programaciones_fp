# Modelo de datos

La app maneja tres conjuntos de datos, cada uno con su dueño:

| Conjunto | Dueño | Dónde vive | Cambia… |
| --- | --- | --- | --- |
| **Catálogo curricular** | CarlosFB, con la ayuda del vigía | `catalogo/` del repositorio → empaquetado y publicado firmado | Cuando cambia una norma |
| **Curso escolar** | CarlosFB | `catalogo/cursos/AAAA-AAAA.yaml` | Una vez por curso |
| **Programación** | Cada profesor | Archivo `.programacion` y copia dentro del `.docx` exportado | Cuando el profesor quiere |

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
├── cursos/2026-2027.yaml       fechas y periodos del curso escolar (previsto: faltan los datos de GM y de 1.º)
├── plantilla.yaml              versión de la plantilla y qué apartados lleva (F2)
└── publicado/                  generado por catalogo.yml: indice.json, catalogo-<versión>.json y su firma (F5)
```

Los códigos van siempre entre comillas en el YAML («'0518'»): con un lector YAML 1.2, una cifra con cero delante sería un número.

### `ciclos/<SIGLA>.yaml`

| Campo | Ejemplo (SEA) | Fuente |
| --- | --- | --- |
| `sigla`, `grado`, `familia`, `nombre`, `titulo` | `SEA`, `GS`, `Electricidad y Electrónica`, «Sistemas electrotécnicos y automatizados», «Técnico Superior en …» | Receta, art. 2 y título del RD, Decreto 95/2026 |
| `rd` | `{id: BOE-A-2010-15355, nombre, enlace, modificado_por: [BOE-A-2024-10685, BOE-A-2023-13217], correcciones: [], posteriores: […]}` | Análisis del BOE |
| `competencia_general` | Texto del art. 4 | RD (en ISO, RD 289/2023) |
| `competencias` | `[{letra: a, texto: …}, …]` (art. 5). En GA e IT, `letra: '1'`, `'2'`… y `pendiente_competencias` | RD |
| `correspondencias_ecp` | `[{modulos: ['0602'], ecp: [{codigo: ECP1180_3, texto: …, uc: UC1180_3}], fuente: BOE-A-2023-13217}, …]` | Anexo V B) vigente + RD 532/2025 |
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
| `competencias_modulo` | Por ciclo: `{SEA: [a, b, d, …]}`, según las orientaciones pedagógicas. Vacío en el Proyecto y en los comunes |
| `ra` | `[{n: 1, texto: …, criterios: [{letra: a, texto: «Se han identificado…»}, …]}, …]`. Con erratas de numeración, `n_boe` o `letra_boe` |
| `fuente` | `{norma: BOE-A-2010-15355, tambien: […], bloque: «Anexo I, módulo 0517», version: 2010-10-08, huella: sha256:…, comprobado: 2026-10-17}` |

- Un módulo que está en dos ciclos se guarda **una vez** si el texto es idéntico en los dos reales decretos. Si no, va **uno por título** (`0237-IT` y `0237-IEA`, `0238-…`, `0260-CAR` y `0260-EMV`).
- Los optativos tienen `id` propio (`OPT-INGLES-ORAL`, `OPT-EE-IA`, `OPT-EE-FV`): el decreto no les da código y el del centro puede repetirse (0179).

### `normativa.yaml`

`[{id, ambito: estatal|autonomico, titulo, fecha, diario: BOE|DOGV, enlace, aplica: todos|GM|GS|[siglas], curso_escolar?, pendiente?}, …]`, por fecha creciente, como la lista del documento. Incluye el real decreto de cada título, las normas que lo modifican y sus correcciones de errores.

### `cursos/2026-2027.yaml`

| Campo | Valor 2026-2027 (de la plantilla vigente) |
| --- | --- |
| `evaluaciones` | inicial 2026-09-30 · 1.ª 2026-11-20 · 2.ª 2027-02-26 · 3.ª 2027-05-28 |
| `ordinaria` | 2027-05-31 → 2027-06-03 |
| `extraordinaria_desde` | 2027-06-14 |
| `resolucion_instrucciones` | Resolución de 16 de julio de 2026 (DOGV, enlace) |
| `formacion_empresa` | Por curso (1.º / 2.º) y jornada (7 h / 8 h): días y periodo. En 2.º de SEA: 8 h → 43 días, 2027-03-02 → 2027-05-28 · 7 h → 49 días, 2027-02-25 → 2027-06-03 |

La 3.ª evaluación se mantiene el 28/05 aunque el calendario escolar diga el 27 (CarlosFB, 2026-10-11).

## 2. Programación (archivo `.programacion`)

JSON, formato `programaciones/1`:

```json
{
  "formato": "programaciones/1",
  "app": "1.0.0",
  "catalogo": "2026.10.14",
  "plantilla": "2026-10-06",
  "curso_escolar": "2026-2027",
  "ciclo": "SEA", "curso": 2, "modulo": "0517",
  "profesorado": ["Carlos M. Ferrero Bonet"],
  "unidades": [
    {"id": "u1", "tipo": "UD", "titulo": "UD01. Recepción terrestre. La señal de TV", "horas": 10, "trimestre": 1, "elemento": "e1"}
  ],
  "elementos": [
    {"id": "e1", "tipo": "E", "nombre": "EXAMEN 1", "ra": [1, 2]}
  ],
  "empresa": {"2": 12, "3": 13, "4": 13, "5": 13, "6": 12},
  "centro_ajustado": {"3": 8, "4": 10, "6": 10},
  "ra_competencias": {"1": ["a", "d"], "2": ["a", "b", "d"]},
  "metodologia": {"material": "…", "plataformas": ["Teams", "Educamos"], "texto_propio": "…"},
  "recursos": {"cuaderno": "CF-185 …", "libro": "RICT", "software": ["Microsoft Office 365", "AutoCAD", "iT-Calc", "CYPE"]},
  "espacios": ["Aula de informática y taller …"],
  "actividades": [],
  "bloques": {"profesorado": "confirmado", "unidades": "heredado", "empresa": "heredado", "ra_competencias": "confirmado", "metodologia": "heredado"},
  "heredada_de": {"profesor": "…", "curso_escolar": "2025-2026", "archivo": "…"},
  "historial": [{"fecha": "2026-10-14T10:00", "accion": "exportada"}]
}
```

- **Estado de cada bloque:** `vacio` · `heredado` · `confirmado`.
- **Lo que no se guarda:** nada de lo que se puede calcular o sacar del catálogo (pesos, tabla 4.1, textos).

## 3. Cálculos (`calculos.py`)

Con `H` = horas del módulo, `h(e)` = suma de las horas de las unidades del elemento `e` y `R(e)` = sus RA:

| Resultado | Fórmula | Comprobación con PIICT |
| --- | --- | --- |
| Peso del elemento | `h(e) / H`, con un decimal | EXAMEN 1: 24 / 166 = 14,5 % |
| Horas de centro del RA `r` (propuesta) | `Σ h(e) / |R(e)|` sobre los elementos que contienen `r`, redondeado a entero | RA1 = 24/2 + 16/2 + 12/2 + 16/2 = 34 ✓ · RA2 = 41 ✓ |
| Horas de centro del RA `r` (definitiva) | La propuesta, o la que fije el profesor en `centro_ajustado`, siempre entre el mínimo (elementos exclusivos de `r`) y el máximo (todos los que lo incluyen), y con la suma igual a las horas de centro | RA3: propuesta 7,33 → ajustada a 8 · RA4: 9,33 → 10 · RA6: 11,33 → 10 (suma 103 ✓) |
| Horas totales del RA | centro + `empresa[r]` | RA2 = 41 + 12 = 53 |
| Modalidad | `Centro` si empresa = 0 · `Empresa` si centro = 0 · si no, `Mixto` | RA5: 0 + 13 → Empresa |
| % de empresa | `ceil(100 · Σ empresa / H)` | 63 / 166 = 37,95 → 38 % |
| % de centro | `100 − % empresa` | 62 % |

El reparto a partes iguales (el de `curriculo.py`) reproduce RA1 y RA2 de PIICT, pero no RA3, RA4 y RA6, que CarlosFB ajustó a mano en enteros dentro de los límites (regla 3 de la skill `programacion-didactica`). Por eso la app **propone** el reparto y deja **ajustarlo** en el bloque «Empresa por RA», con la validación V-04. El redondeo exacto de la propuesta está pendiente de confirmar ([PENDIENTE.md](PENDIENTE.md)).

## 4. Migraciones

Un cambio incompatible sube el formato (`programaciones/2`) y añade su función en `programacion.py`. La app abre siempre los formatos anteriores.
