"""Diseño del documento (ADR-044): el de la app PCCF aplicado a la plantilla ya marcada.

Lo llama `scripts/plantilla.py crear` al final, en las dos plantillas (módulos y proyectos, y ámbitos). No cambia
ningún texto fijo ni ninguna marca: cambia el aspecto. Lo que la app lee sigue igual:
- Los títulos siguen siendo párrafos con estilo Título 2 y Título 3 de Word, y el índice, el campo TOC que Word rehace.
  Su número lo pone la numeración automática del estilo (el número grande de cada apartado, en la columna de margen):
  así el índice no copia su tamaño. `contenido.leer` cuenta los títulos para saber su número.
- La portada es una sección sin márgenes con el bloque verde a sangre y, debajo, la ficha (cada etiqueta con su valor
  debajo, en la misma celda: `importar_docx.leer_portada` la lee así).
- Barlow va incrustada en el .docx (licencia OFL, `scripts/recursos_diseno/`; el escudo, en `imagenes/`): Word y LibreOffice la usan sin tenerla
  instalada.

Tokens y medidas: los de DESIGN.md § Documento de PCCF, copiados aquí (docs/DOCUMENTO_GENERADO.md, «Diseño»).
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from lxml import etree

from programaciones import ooxml
from programaciones.ooxml import W, normal, texto

RECURSOS = Path(__file__).resolve().parent / "recursos_diseno"
ESCUDO = Path(__file__).resolve().parents[1] / "imagenes" / "escudo.png"

# -- tokens ----------------------------------------------------------------------------------------------------------
C = {"v9": "14401A", "v7": "206028", "oro": "C98A1E", "t": "1E2420", "t2": "47504A", "t3": "6E7771",
     "l": "D5DBD6", "l2": "ECEFEC", "blanco": "FFFFFF", "claro": "CFE0D0", "claro2": "E3EDE3"}
#: (archivo, familia de Word, ranura de incrustación)
FUENTES = [("Barlow-Regular.ttf", "Barlow", "Regular"), ("Barlow-Bold.ttf", "Barlow", "Bold"),
           ("Barlow-Italic.ttf", "Barlow", "Italic"), ("Barlow-SemiBold.ttf", "Barlow SemiBold", "Regular"),
           ("BarlowCondensed-SemiBold.ttf", "Barlow Condensed SemiBold", "Regular"),
           ("BarlowCondensed-Bold.ttf", "Barlow Condensed", "Bold"),
           ("BarlowCondensed-ExtraBold.ttf", "Barlow Condensed ExtraBold", "Regular")]
TEXTO, SEMI, COND, COND_SEMI, COND_EXTRA = ("Barlow", "Barlow SemiBold", "Barlow Condensed",
                                            "Barlow Condensed SemiBold", "Barlow Condensed ExtraBold")

# -- página (twips: 1 mm = 56,7) -------------------------------------------------------------------------------------
A4 = (11906, 16838)
MARGENES = {"top": 1361, "right": 1021, "bottom": 1361, "left": 1134, "header": 624, "footer": 567}
ANCHO = A4[0] - MARGENES["left"] - MARGENES["right"]   # 9751: 172 mm
COL_MARGEN = 1928                                      # 34 mm: columna de los números de apartado
SANGRIA = 2268                                         # 34 + 6 mm: columna de texto
ANCHO_TEXTO = ANCHO - SANGRIA                          # 7483
VINETA = 227                                           # 4 mm

NS_DECL = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
NS_DIBUJO = ('xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
             'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
             'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')
TIPO_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
CT_FUENTE = "application/vnd.openxmlformats-officedocument.obfuscatedFont"
NUM_TITULOS = "900"   # numId (y abstractNumId) de la numeración de los títulos

#: Títulos con el texto del diseño (en minúsculas y sin número: el número lo pone Word). Clave: el texto sin número.
TITULOS = [
    "Datos identificativos: marco normativo y contextualización del módulo", "Normativa básica estatal",
    "Normativa autonómica (Comunidad Valenciana)",
    "Relación entre estándares de competencia y los módulos del ciclo formativo",
    "Competencias profesionales, personales y sociales", "Módulos optativos ofertados",
    "Contribución de los RA a las competencias generales",
    "Esquema general y secuenciación de las unidades de programación", "Ponderación de cada RA",
    "Metodología del proceso de enseñanza-aprendizaje", "Principios generales y pedagógicos", "Recursos",
    "Uso de espacios y equipamientos", "Medidas de atención a la diversidad", "Evaluación del aprendizaje",
    "Períodos Formación en Empresa", "Actividades complementarias y extraescolares",
    "Criterios y procedimientos para la evaluación", "Instrumentos y procedimiento de evaluación",
    "Elementos de evaluación", "Actividades de recuperación",
    # ámbitos de Grado Básico
    "Contribución de las competencias específicas a las competencias clave",
    "Temporalización y distribución de competencias específicas", "Ponderación de cada competencia específica",
]
RE_NUMERO = re.compile(r"^(\d{1,2}(?:\.\d{1,2})?)\.?\s*-?\s*")


def clave_titulo(t: str) -> str:
    return RE_NUMERO.sub("", normal(t)).casefold().rstrip(" .:")


TITULO_NUEVO = {clave_titulo(t): t for t in TITULOS}


# -- utilidades de XML ------------------------------------------------------------------------------------------------
def rpr(fuente: str | None = None, sz: float | None = None, color: str | None = None, b: bool | None = None,
        i: bool = False, caps: bool = False, esp: int | None = None, u: str | None = None) -> str:
    """rPr en el orden del esquema. `sz` en puntos; `esp`: espaciado entre letras en veinteavos de punto."""
    x = ""
    if fuente:
        x += f'<w:rFonts w:ascii="{fuente}" w:hAnsi="{fuente}" w:eastAsia="{fuente}" w:cs="{fuente}"/>'
    if b is not None:
        x += "<w:b/><w:bCs/>" if b else '<w:b w:val="0"/><w:bCs w:val="0"/>'
    x += "<w:i/><w:iCs/>" if i else ""
    x += "<w:caps/>" if caps else ""
    x += f'<w:color w:val="{C.get(color, color)}"/>' if color else ""
    x += f'<w:spacing w:val="{esp}"/>' if esp else ""
    if sz:
        x += f'<w:sz w:val="{round(sz * 2)}"/><w:szCs w:val="{round(sz * 2)}"/>'
    x += u or ""
    return f"<w:rPr>{x}</w:rPr>" if x else ""


def ppr(antes: int | None = 0, despues: int | None = 0, linea: int | None = None, ind: tuple | None = None,
        tabs: list | None = None, keep: bool = False, nivel: int | None = None, borde: str = "",
        jc: str | None = None, sin_guiones: bool = False, num: tuple | None = None) -> str:
    """pPr en el orden del esquema. `linea`: interlineado en 240avos; `ind`: (izquierda, francesa[, derecha])."""
    x = "<w:keepNext/>" if keep else ""
    if num:
        x += f'<w:numPr><w:ilvl w:val="{num[1]}"/><w:numId w:val="{num[0]}"/></w:numPr>'
    x += borde
    if tabs:
        x += "<w:tabs>" + "".join(f'<w:tab w:val="{v}" w:pos="{p}"/>' for v, p in tabs) + "</w:tabs>"
    x += "<w:suppressAutoHyphens/>" if sin_guiones else ""
    if antes is not None or despues is not None or linea:
        x += "<w:spacing"
        x += f' w:before="{antes}"' if antes is not None else ""
        x += f' w:after="{despues}"' if despues is not None else ""
        x += f' w:line="{linea}" w:lineRule="auto"/>' if linea else "/>"
    if ind:
        x += f'<w:ind w:left="{ind[0]}"'
        x += f' w:right="{ind[2]}"' if len(ind) > 2 else ""
        x += f' w:hanging="{ind[1]}"/>' if ind[1] else ' w:firstLine="0"/>'
    x += f'<w:jc w:val="{jc}"/>' if jc else ""
    x += f'<w:outlineLvl w:val="{nivel}"/>' if nivel is not None else ""
    return f"<w:pPr>{x}</w:pPr>"


def estilo_p(sid: str, nombre: str, p: str, r: str, base: str | None = "Normal", sig: str | None = None,
             propio: bool = True) -> str:
    cs = ' w:customStyle="1"' if propio else ""
    s = f'<w:style w:type="paragraph"{cs} w:styleId="{sid}">'
    s += f'<w:name w:val="{nombre}"/>'
    s += f'<w:basedOn w:val="{base}"/>' if base else ""
    s += f'<w:next w:val="{sig}"/>' if sig else ""
    return s + f"<w:qFormat/>{p}{r}</w:style>"


def estilo_c(sid: str, nombre: str, r: str, propio: bool = True) -> str:
    cs = ' w:customStyle="1"' if propio else ""
    return f'<w:style w:type="character"{cs} w:styleId="{sid}"><w:name w:val="{nombre}"/>{r}</w:style>'


def frag(xml: str) -> etree._Element:
    return etree.fromstring(f"<w:raiz {NS_DECL} {NS_DIBUJO}>{xml}</w:raiz>")[0]


def clave_fuente(archivo: str) -> str:
    """GUID fijo por archivo: la misma plantilla da los mismos bytes."""
    return "{%s}" % str(uuid.uuid5(uuid.NAMESPACE_URL, f"programaciones/fuentes/{archivo}")).upper()


def ofuscar(datos: bytes, clave: str) -> bytes:
    """Fuente incrustada de Word (ECMA-376, parte 1, 17.8.1): los 32 primeros bytes, XOR con la clave al revés."""
    k = bytes.fromhex(clave.strip("{}").replace("-", ""))[::-1]
    b = bytearray(datos)
    for i in range(32):
        b[i] ^= k[i % 16]
    return bytes(b)


# -- estilos ---------------------------------------------------------------------------------------------------------
def estilos() -> str:
    linea_inf = f'<w:pBdr><w:bottom w:val="single" w:sz="4" w:space="3" w:color="{C["l2"]}"/></w:pBdr>'
    out = [
        '<w:docDefaults><w:rPrDefault>' + rpr(TEXTO, 9.5, "t")[:-8] +
        '<w:lang w:val="es-ES" w:eastAsia="es-ES" w:bidi="ar-SA"/></w:rPr></w:rPrDefault>'
        '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
        '</w:docDefaults>',
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:widowControl/></w:pPr></w:style>',
        '<w:style w:type="character" w:default="1" w:styleId="Fuentedeprrafopredeter">'
        '<w:name w:val="Default Paragraph Font"/><w:uiPriority w:val="1"/><w:semiHidden/></w:style>',
        '<w:style w:type="table" w:default="1" w:styleId="Tablanormal"><w:name w:val="Normal Table"/>'
        '<w:semiHidden/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar>'
        '<w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/>'
        '<w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>',
        '<w:style w:type="numbering" w:default="1" w:styleId="Sinlista"><w:name w:val="No List"/>'
        '<w:semiHidden/></w:style>',
        # títulos: número de la numeración del estilo (columna de margen) y texto en la columna de texto
        estilo_p("Ttulo2", "heading 2", ppr(antes=520, despues=300, linea=240, keep=True, nivel=1, sin_guiones=True,
                                            ind=(SANGRIA, SANGRIA), tabs=[("left", SANGRIA)],
                                            num=(NUM_TITULOS, 0)),
                 rpr(COND, 19, "v9", b=True), sig="Texto", propio=False),
        estilo_p("Ttulo3", "heading 3", ppr(antes=340, despues=130, keep=True, nivel=2, sin_guiones=True,
                                            ind=(SANGRIA, SANGRIA - COL_MARGEN), tabs=[("left", SANGRIA)],
                                            num=(NUM_TITULOS, 1)),
                 rpr(SEMI, 11, "t"), sig="Texto", propio=False),
        # índice
        estilo_p("Ttulodelatabla", "Título de la tabla", ppr(antes=0, despues=420, keep=True, ind=(SANGRIA, 0)),
                 rpr(COND, 19, "v9", b=True)),
        estilo_p("TDC2", "toc 2", ppr(antes=150, despues=40, linea=252, ind=(SANGRIA, SANGRIA - COL_MARGEN + 340),
                                       tabs=[("left", SANGRIA), ("right", ANCHO)], borde=linea_inf),
                 rpr(sz=9.5, color="t"), sig="Normal", propio=False),
        estilo_p("TDC3", "toc 3", ppr(antes=0, despues=40, linea=252, ind=(SANGRIA, SANGRIA - COL_MARGEN + 340),
                                       tabs=[("left", SANGRIA), ("right", ANCHO)]),
                 rpr(sz=9, color="t2"), sig="Normal", propio=False),
        # texto
        estilo_p("Texto", "Texto", ppr(despues=150, linea=348, ind=(SANGRIA, 0)), ""),
        estilo_p("Prrafodelista", "List Paragraph", ppr(despues=70, linea=336, ind=(SANGRIA + VINETA, VINETA)), "",
                 base="Texto", propio=False),
        estilo_p("Fuente", "Fuente de los datos", ppr(antes=60, despues=200, linea=264), rpr(sz=7.5, color="t3")),
        # tablas
        estilo_p("TablaTexto", "Texto de tabla", ppr(linea=252), rpr(sz=8.5)),
        estilo_p("TablaCabecera", "Cabecera de tabla", ppr(linea=240, sin_guiones=True),
                 rpr(COND_SEMI, 7.5, "v9", caps=True, esp=12)),
        estilo_p("TablaEtiqueta", "Etiqueta de ficha", ppr(linea=240, sin_guiones=True),
                 rpr(COND_SEMI, 7.5, "v7", caps=True, esp=12)),
        # encabezado y pie
        estilo_p("Encabezado", "header", ppr(), rpr(COND_SEMI, 7.5, "v7", caps=True, esp=14), propio=False),
        estilo_p("Piedepgina", "footer", ppr(), rpr(sz=7.4, color="t3"), propio=False),
        # caracteres
        estilo_c("Hipervnculo", "Hyperlink",
                 rpr(color="t")[:-8] + '<w:u w:val="single" w:color="9CC2A1"/></w:rPr>', propio=False),
        estilo_c("PieNumero", "Número de página", rpr(COND, 15, "v7", b=True)),
        estilo_c("PieTotal", "Total de páginas", rpr(COND_SEMI, 8, "t3")),
    ]
    return XML + f"<w:styles {NS_DECL}>" + "".join(out) + "</w:styles>"




# -- numeración ------------------------------------------------------------------------------------------------------
def numeracion(pq: ooxml.Paquete) -> None:
    """Viñetas «•» verdes en la columna de texto; letras de los criterios en verde; y la numeración de los títulos."""
    n = pq.xml("word/numbering.xml")
    for lvl in n.iter(W + "lvl"):
        nivel = int(lvl.get(W + "ilvl"))
        fmt = lvl.find(W + "numFmt")
        fmt = fmt.get(W + "val") if fmt is not None else "decimal"
        for e in [e for e in lvl if e.tag in (W + "pPr", W + "rPr")]:
            lvl.remove(e)
        if fmt == "bullet":
            lvl.find(W + "lvlText").set(W + "val", "•" if nivel % 2 == 0 else "–")
            sangria, colgado, r = SANGRIA + VINETA + nivel * 340, VINETA, rpr(TEXTO, color="v7", b=False)
        else:
            sangria, colgado, r = SANGRIA + 340 + nivel * 340, 340, rpr(COND, 8.5, "v7", b=True)
        lvl.append(frag(f'<w:pPr><w:ind w:left="{sangria}" w:hanging="{colgado}"/></w:pPr>'))
        lvl.append(frag(r))
    # los títulos: «1» grande en la columna de margen (Título 2) y «1.1» alineado a su derecha (Título 3)
    numero2 = rpr(COND_EXTRA, 40, "v7", b=False)
    numero3 = rpr(COND, 11, "v7", b=True)
    absn = frag(
        f'<w:abstractNum w:abstractNumId="{NUM_TITULOS}"><w:multiLevelType w:val="multilevel"/>'
        f'<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:pStyle w:val="Ttulo2"/>'
        f'<w:lvlText w:val="%1"/><w:lvlJc w:val="left"/>'
        f'<w:pPr><w:tabs><w:tab w:val="num" w:pos="{SANGRIA}"/></w:tabs><w:ind w:left="{SANGRIA}" '
        f'w:hanging="{SANGRIA}"/></w:pPr>{numero2}</w:lvl>'
        f'<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:pStyle w:val="Ttulo3"/>'
        f'<w:lvlText w:val="%1.%2"/><w:lvlJc w:val="right"/>'
        f'<w:pPr><w:tabs><w:tab w:val="num" w:pos="{SANGRIA}"/></w:tabs><w:ind w:left="{SANGRIA}" '
        f'w:hanging="{SANGRIA - COL_MARGEN}"/></w:pPr>{numero3}</w:lvl></w:abstractNum>')
    num = frag(f'<w:num w:numId="{NUM_TITULOS}"><w:abstractNumId w:val="{NUM_TITULOS}"/></w:num>')
    for e in n.findall(W + "abstractNum"):
        if e.get(W + "abstractNumId") == NUM_TITULOS:
            n.remove(e)
    for e in n.findall(W + "num"):
        if e.get(W + "numId") == NUM_TITULOS:
            n.remove(e)
    abstractos, nums = n.findall(W + "abstractNum"), n.findall(W + "num")
    (abstractos[-1].addnext(absn) if abstractos else n.insert(0, absn))
    (nums[-1].addnext(num) if nums else absn.addnext(num))


# -- encabezado, pies y portada ---------------------------------------------------------------------------------------
SIN_BORDES = ('<w:tcBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/>'
              '</w:tcBorders>')


def _p(texto_p: str, estilo: str | None = None, r: str = "", p_extra: str = "") -> str:
    ps = f'<w:pStyle w:val="{estilo}"/>' if estilo else ""
    pp = f"<w:pPr>{ps}{p_extra}</w:pPr>" if ps or p_extra else ""
    t = f'<w:r>{r}<w:t xml:space="preserve">{texto_p}</w:t></w:r>' if texto_p else ""
    return f"<w:p>{pp}{t}</w:p>"


def _campo(instr: str, r: str = "", muestra: str = "1") -> str:
    return (f'<w:r>{r}<w:fldChar w:fldCharType="begin"/></w:r><w:r>{r}<w:instrText xml:space="preserve"> {instr} '
            f'</w:instrText></w:r><w:r>{r}<w:fldChar w:fldCharType="separate"/></w:r><w:r>{r}<w:t>{muestra}</w:t></w:r>'
            f'<w:r>{r}<w:fldChar w:fldCharType="end"/></w:r>')


def _tabla_2(c1: str, c2: str, ancho2: int, abajo: bool = False, borde_inf: bool = False) -> str:
    bi = (f'<w:tcBorders><w:bottom w:val="single" w:sz="4" w:space="0" w:color="{C["l"]}"/></w:tcBorders>'
          if borde_inf else "")
    va = '<w:vAlign w:val="bottom"/>' if abajo else ""
    mar = '<w:tcMar><w:bottom w:w="45" w:type="dxa"/></w:tcMar>' if borde_inf else ""
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{ANCHO}" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblCellMar>'
            '<w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar></w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{ANCHO - ancho2}"/><w:gridCol w:w="{ancho2}"/></w:tblGrid><w:tr>'
            f'<w:tc><w:tcPr><w:tcW w:w="{ANCHO - ancho2}" w:type="dxa"/>{bi}{mar}{va}</w:tcPr>{c1}</w:tc>'
            f'<w:tc><w:tcPr><w:tcW w:w="{ancho2}" w:type="dxa"/>{bi}{mar}{va}</w:tcPr>{c2}</w:tc></w:tr></w:tbl>')


def encabezado() -> str:
    c1 = _p("Programación didáctica · {{portada_codigo}} · {{curso_escolar}}", "Encabezado")
    return (XML + f"<w:hdr {NS_DECL}>" + _tabla_2(c1, _p("", "Encabezado"), 2835, borde_inf=True) +
            _p("", None, "", '<w:spacing w:after="0" w:line="120" w:lineRule="exact"/>') + "</w:hdr>")


def pie() -> str:
    """Título del apartado en curso (STYLEREF 2: el Título 2 en cualquier idioma de Word) y «N / total» con un filete de oro encima."""
    r_pie = '<w:rPr><w:rStyle w:val="PieNumero"/></w:rPr>'
    r_tot = '<w:rPr><w:rStyle w:val="PieTotal"/></w:rPr>'
    c1 = '<w:p><w:pPr><w:pStyle w:val="Piedepgina"/></w:pPr>' + _campo("STYLEREF 2", "", " ") + "</w:p>"
    regla = (f'<w:p><w:pPr><w:pStyle w:val="Piedepgina"/><w:pBdr><w:top w:val="single" w:sz="7" w:space="1" '
             f'w:color="{C["oro"]}"/></w:pBdr><w:spacing w:before="0" w:after="0" w:line="60" w:lineRule="exact"/>'
             f'<w:ind w:left="{SANGRIA - 510}"/></w:pPr></w:p>')
    numero = ('<w:p><w:pPr><w:pStyle w:val="Piedepgina"/><w:jc w:val="right"/></w:pPr>' + _campo("PAGE", r_pie, "1")
              + f'<w:r>{r_tot}<w:t xml:space="preserve"> / </w:t></w:r>' + _campo("NUMPAGES", r_tot, "1") + "</w:p>")
    return XML + f"<w:ftr {NS_DECL}>" + _tabla_2(c1, regla + numero, SANGRIA, abajo=True) + "</w:ftr>"


def pie_indice() -> str:
    """El pie de la página del índice: «Índice» en lugar del título del apartado."""
    return pie().replace(_campo("STYLEREF 2", "", " "), '<w:r><w:t>Índice</w:t></w:r>')


def pie_portada(rid_escudo: str) -> str:
    """Escudo y centro al pie de la portada (sección sin márgenes: la tabla lleva su sangría); a la derecha, el correo
    del departamento si está en Ajustes (`correo_pie`)."""
    alto = 964   # 17 mm
    ancho = round(alto * 580 / 600)
    emu = lambda tw: tw * 635  # noqa: E731
    dibujo = (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
              f'<wp:extent cx="{emu(ancho)}" cy="{emu(alto)}"/><wp:docPr id="1" name="Escudo"/>'
              '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
              '<pic:nvPicPr><pic:cNvPr id="1" name="escudo.png"/><pic:cNvPicPr/></pic:nvPicPr>'
              f'<pic:blipFill><a:blip r:embed="{rid_escudo}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
              f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu(ancho)}" cy="{emu(alto)}"/></a:xfrm>'
              '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
              '</wp:inline></w:drawing></w:r>')
    r_nom = rpr(COND, 9, "v9", b=True, caps=True, esp=10)
    r_txt = rpr(sz=7.5, color="t3")
    centro = (f'<w:p>{ppr(linea=252)}<w:r>{r_nom}<w:t>Escuelas Profesionales Luis Amigó</w:t></w:r></w:p>'
              f'<w:p>{ppr(linea=252)}<w:r>{r_txt}<w:t xml:space="preserve">Carretera de Bétera s/n · 46110 Godella '
              f'(Valencia)</w:t></w:r></w:p><w:p>{ppr(linea=252)}<w:r>{r_txt}<w:t xml:space="preserve">Centro '
              'concertado · Formación Profesional</w:t></w:r></w:p>')
    correo = f'<w:p>{ppr(linea=252, jc="right")}<w:r>{r_txt}<w:t>{{{{correo_pie}}}}</w:t></w:r></w:p>'
    celdas = [(ancho + 227, f"<w:p>{ppr()}{dibujo}</w:p>"), (4400, centro), (ANCHO - ancho - 227 - 4400, correo)]
    tc = "".join(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{SIN_BORDES}<w:vAlign w:val="bottom"/></w:tcPr>{x}'
                 "</w:tc>" for w, x in celdas)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w, _ in celdas)
    return (XML + f"<w:ftr {NS_DECL} {NS_DIBUJO}><w:tbl><w:tblPr><w:tblW w:w=\"{ANCHO}\" w:type=\"dxa\"/>"
            f'<w:tblInd w:w="{MARGENES["left"]}" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblCellMar>'
            '<w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar></w:tblPr>'
            f"<w:tblGrid>{grid}</w:tblGrid><w:tr>{tc}</w:tr></w:tbl>"
            + _p("", None, "", '<w:spacing w:after="0" w:line="120" w:lineRule="exact"/>') + "</w:ftr>")


def _celda(ancho: int, contenido: str, fondo: str | None = None, mar: str = "", va: str = "top",
           span: int = 1) -> str:
    sp = f'<w:gridSpan w:val="{span}"/>' if span > 1 else ""
    shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{C[fondo]}"/>' if fondo else ""
    m = f"<w:tcMar>{mar}</w:tcMar>" if mar else ""
    return (f'<w:tc><w:tcPr><w:tcW w:w="{ancho}" w:type="dxa"/>{sp}{SIN_BORDES}{shd}{m}<w:vAlign w:val="{va}"/>'
            f"</w:tcPr>{contenido}</w:tc>")


def _fila(alto: int | None, celdas: str) -> str:
    h = f'<w:trHeight w:val="{alto}" w:hRule="exact"/>' if alto else ""
    return f"<w:tr><w:trPr><w:cantSplit/>{h}</w:trPr>{celdas}</w:tr>"


def portada(sect: str, ambito: bool) -> list[etree._Element]:
    """Bloque verde a sangre (centro, curso, «Programación didáctica», el código enorme y el nombre) y la ficha."""
    izq, der = 6237, A4[0] - 6237
    sin = '<w:spacing w:before="0" w:after="0"/>'
    r_cab = rpr(COND_SEMI, 8.5, "claro", caps=True, esp=24)
    bloque = (
        f'<w:tbl><w:tblPr><w:tblW w:w="{A4[0]}" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblCellMar>'
        '<w:top w:w="70" w:type="dxa"/><w:left w:w="0" w:type="dxa"/><w:bottom w:w="70" w:type="dxa"/>'
        f'<w:right w:w="113" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid><w:gridCol w:w="{izq}"/>'
        f'<w:gridCol w:w="{der}"/></w:tblGrid>'
        + _fila(1701, _celda(izq, _p("Escuelas Profesionales Luis Amigó", None, r_cab, f"<w:suppressAutoHyphens/>{sin}"),
                             "v9", '<w:top w:w="850" w:type="dxa"/><w:left w:w="1134" w:type="dxa"/>')
                + _celda(der, _p("Curso {{curso_escolar}}", None, r_cab,
                                 f'<w:suppressAutoHyphens/>{sin}<w:jc w:val="right"/>'),
                         "v9", '<w:top w:w="850" w:type="dxa"/><w:right w:w="1021" w:type="dxa"/>'))
        + _fila(3402, _celda(A4[0], _p("Programación didáctica", None, rpr(COND_SEMI, 23, "blanco"),
                                       '<w:suppressAutoHyphens/><w:spacing w:line="250" w:lineRule="auto"/>')
                             + _p("", None, "", f'<w:pBdr><w:top w:val="single" w:sz="12" w:space="1" '
                                  f'w:color="{C["oro"]}"/></w:pBdr><w:suppressAutoHyphens/><w:spacing w:before="300"/>'
                                  '<w:ind w:left="0" w:right="8277"/>'),
                             "v9", '<w:top w:w="1250" w:type="dxa"/><w:left w:w="1134" w:type="dxa"/>', span=2))
        + _fila(4536, _celda(izq, _p("{{portada_codigo}}", None, rpr(COND_EXTRA, 150, "blanco"),
                                     f"<w:suppressAutoHyphens/>{sin}"),
                             "v9", '<w:left w:w="936" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/>', "bottom")
                + _celda(der, _p("{{portada_nombre}}", None, rpr(COND_SEMI, 13, "claro2"),
                                 f'<w:suppressAutoHyphens/>{sin}<w:jc w:val="right"/>'),
                         "v9", '<w:bottom w:w="680" w:type="dxa"/><w:right w:w="1021" w:type="dxa"/>', "bottom"))
        + _fila(113, _celda(A4[0], _p("", None, "", '<w:suppressAutoHyphens/><w:spacing w:before="0" w:after="0" '
                                     'w:line="40" w:lineRule="exact"/>'), "oro", span=2))
        + "</w:tbl>")
    hueco = _p("", None, "", '<w:spacing w:before="0" w:after="400" w:line="40" w:lineRule="exact"/>')

    def campo(etiqueta: str, valor: str) -> str:
        et = _p(etiqueta, "TablaEtiqueta", "", f'<w:pBdr><w:bottom w:val="single" w:sz="4" w:space="3" '
                f'w:color="{C["l"]}"/></w:pBdr><w:spacing w:after="80"/>')
        va = "".join(f'<w:r>{rpr(sz=9.5)}<w:t xml:space="preserve">{v}</w:t></w:r>' for v in valor.split("|"))
        return et + (f'<w:p><w:pPr><w:pStyle w:val="TablaTexto"/><w:suppressAutoHyphens/><w:spacing w:after="220"/>'
                     f"</w:pPr>{va}</w:p>")

    anchos = (3800, 2976, 2975)
    mar = '<w:right w:w="397" w:type="dxa"/>'
    filas = [[("Familia profesional", "{{familia}}"), ("Ciclo formativo", "{{grado}}|{{ciclo}}"),
              ("Ámbito" if ambito else "Módulo profesional", "{{modulo_portada}}")],
             [("Nº horas del módulo", "{{horas}}"), ("{{profesorado_etiqueta}}", "{{*profesorado}}"),
              ("Curso académico", "{{curso_escolar}}")]]
    ficha = (f'<w:tbl><w:tblPr><w:tblW w:w="{ANCHO}" w:type="dxa"/><w:tblInd w:w="{MARGENES["left"]}" w:type="dxa"/>'
             '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="70" w:type="dxa"/><w:left w:w="0" w:type="dxa"/>'
             '<w:bottom w:w="70" w:type="dxa"/><w:right w:w="113" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>'
             + "".join(f'<w:gridCol w:w="{a}"/>' for a in anchos) + "</w:tblGrid>"
             + "".join(_fila(None, "".join(_celda(a, campo(e, v), mar=mar) for a, (e, v) in zip(anchos, f, strict=True)))
                       for f in filas) + "</w:tbl>")
    final = f"<w:p><w:pPr>{sect}</w:pPr></w:p>"
    return [frag(x) for x in (bloque, hueco, ficha, final)]


# -- cuerpo ----------------------------------------------------------------------------------------------------------
QUITAR_RPR = ("rFonts", "sz", "szCs", "color", "kern", "lang", "w", "spacing", "position", "highlight", "shd")
QUITAR_PPR = ("ind", "spacing", "jc", "rPr", "contextualSpacing", "snapToGrid", "adjustRightInd", "autoSpaceDE",
              "autoSpaceDN", "textAlignment", "widowControl", "tabs", "pBdr", "shd")


def limpiar_rpr(r: etree._Element, en_enlace: bool = False) -> None:
    rp = r.find(W + "rPr")
    if rp is None:
        return
    for e in list(rp):
        nombre = etree.QName(e).localname
        enlace = en_enlace and nombre in ("u", "rStyle", "i", "iCs")   # los enlaces, solo con su estilo
        otro_estilo = nombre == "rStyle" and e.get(W + "val") != "Hipervnculo"
        if nombre in QUITAR_RPR or enlace or otro_estilo:
            rp.remove(e)
    if en_enlace:
        ooxml.hijo(rp, "rStyle", ooxml.ORDEN_RPR, val="Hipervnculo")


def limpiar_ppr(p: etree._Element, estilo: str | None, conservar: tuple[str, ...] = ()) -> etree._Element:
    pp = ooxml.ppr(p)
    for e in list(pp):
        nombre = etree.QName(e).localname
        if nombre in QUITAR_PPR and nombre not in conservar:
            pp.remove(e)
    if estilo is not None:
        if estilo:
            ooxml.hijo(pp, "pStyle", ooxml.ORDEN_PPR, val=estilo)
        elif pp.find(W + "pStyle") is not None:
            pp.remove(pp.find(W + "pStyle"))
    return pp


def runs(e: etree._Element) -> None:
    for r in e.iter(W + "r"):
        limpiar_rpr(r, en_enlace=any(a.tag == W + "hyperlink" for a in r.iterancestors()))


def numero_de(titulos: list[etree._Element]) -> list[str]:
    """El número que pondrá Word a cada título (Título 2 cuenta; Título 3 cuenta dentro de su Título 2)."""
    out, n2, n3 = [], 0, 0
    for p in titulos:
        if ooxml.estilo(p) == "Ttulo2":
            n2, n3 = n2 + 1, 0
            out.append(str(n2))
        else:
            n3 += 1
            out.append(f"{n2}.{n3}")
    return out


def titulos(body: etree._Element) -> None:
    """Cada título: el texto del diseño sin número (lo pone la numeración del estilo), comprobando que ese número es el
    que llevaba escrito. Un título ya sin número (la plantilla con el diseño, al volver a pasarla) se queda con el de
    Word."""
    ts = [p for p in body if ooxml.es_titulo(p)]
    for p, numero in zip(ts, numero_de(ts), strict=True):
        viejo = normal(texto(p))
        m = re.match(r"^(\d{1,2}(?:\.\d{1,2})?)[.\-\s]", viejo)
        if m and m.group(1) != numero:
            raise SystemExit(f"título «{viejo}»: la numeración automática le daría {numero}")
        nuevo = TITULO_NUEVO.get(clave_titulo(viejo))
        if nuevo is None:
            raise SystemExit(f"título sin texto del diseño: «{viejo}» (scripts/diseno.py, TITULOS)")
        estilo = ooxml.estilo(p)
        for e in list(p):
            p.remove(e)
        p.append(frag(f'<w:pPr><w:pStyle w:val="{estilo}"/></w:pPr>'))
        p.append(ooxml.run(nuevo))


def indice(body: etree._Element) -> None:
    """El índice desde los títulos: «número ⇥ título ⇥ página», con el campo TOC que Word rehace al abrir y los
    hipervínculos y PAGEREF que la app enlaza (`documento.enlazar_indice`)."""
    entradas = [p for p in body if p.tag == W + "p" and ooxml.estilo(p) in ("TDC1", "TDC2", "TDC3")]
    cab = next(p for p in body if p.tag == W + "p" and ooxml.estilo(p) == "Ttulodelatabla")
    for p in entradas:
        body.remove(p)
    for e in list(cab):
        cab.remove(e)
    cab.append(frag('<w:pPr><w:pStyle w:val="Ttulodelatabla"/></w:pPr>'))
    cab.append(ooxml.run("Índice"))
    ts = [p for p in body if ooxml.es_titulo(p)]
    ancla = cab
    for k, (p, numero) in enumerate(zip(ts, numero_de(ts), strict=True)):
        estilo = "TDC2" if ooxml.estilo(p) == "Ttulo2" else "TDC3"
        marca = f"_TocProg{k + 1:02d}"
        inicio = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \\o "2-3" '
                  '\\h \\z \\u </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>') if k == 0 else ""
        titulo = normal(texto(p)).replace("&", "&amp;").replace("<", "&lt;")
        entrada = frag(
            f'<w:p><w:pPr><w:pStyle w:val="{estilo}"/></w:pPr>{inicio}<w:hyperlink w:anchor="{marca}" w:history="1">'
            f'<w:r><w:t>{numero}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t xml:space="preserve">{titulo}</w:t></w:r>'
            '<w:r><w:tab/></w:r><w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r><w:instrText xml:space="preserve"> PAGEREF {marca} \\h </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>3</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:hyperlink></w:p>')
        ancla.addnext(entrada)
        ancla = entrada
    fin = frag('<w:p><w:pPr><w:pStyle w:val="TDC2"/></w:pPr><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')
    ancla.addnext(fin)
    # el salto de página tras el índice pasa a salto de sección: la del índice lleva «Índice» en el pie
    sig = fin.getnext()
    while sig is not None and sig.tag == W + "p" and not ooxml.es_titulo(sig) and not normal(texto(sig)):
        siguiente = sig.getnext()
        body.remove(sig)
        sig = siguiente
    fin.addnext(frag(f"<w:p><w:pPr>{seccion('rIdPieIndice')}</w:pPr></w:p>"))


def seccion(pie_rid: str, final: bool = False) -> str:
    """La sección de las páginas interiores (A4 vertical) con el encabezado común y el pie `pie_rid`."""
    m = MARGENES
    tipo = "" if final else '<w:type w:val="nextPage"/>'
    return (f'<w:sectPr><w:headerReference w:type="default" r:id="rIdEncabezado"/>'
            f'<w:footerReference w:type="default" r:id="{pie_rid}"/>{tipo}<w:pgSz w:w="{A4[0]}" w:h="{A4[1]}"/>'
            f'<w:pgMar w:top="{m["top"]}" w:right="{m["right"]}" w:bottom="{m["bottom"]}" w:left="{m["left"]}" '
            f'w:header="{m["header"]}" w:footer="{m["footer"]}" w:gutter="0"/><w:cols w:space="708"/></w:sectPr>')


#: Tabla 4: unidad, sesiones, trimestre, elemento, peso y RA; en los proyectos, tarea, sesiones, trimestre, peso,
#: elemento y RA. Suman ANCHO.
ANCHOS_T4 = [3650, 900, 560, 1760, 1060, 1821]
ANCHOS_T4_PROYECTO = [3250, 900, 560, 1000, 1950, 2091]
#: Columnas de cifras (por el principio de su cabecera): a la derecha; las demás, a la izquierda
RE_CIFRAS = re.compile(r"(?i)^(sesiones|horas|trim|peso|%|curso$)")


def _cabeceras(t: etree._Element) -> list[str]:
    """La cabecera de cada columna de la rejilla (las celdas combinadas en horizontal, en todas las que ocupan)."""
    out = []
    for tc in t.find(W + "tr").findall(W + "tc"):
        span = tc.find(f"{W}tcPr/{W}gridSpan")
        out += [normal(texto(tc))] * (int(span.get(W + "val")) if span is not None else 1)
    return out


def _ancho_tabla(t: etree._Element) -> list[int]:
    return [int(g.get(W + "w")) for g in t.find(W + "tblGrid").findall(W + "gridCol")]


def tabla(t: etree._Element) -> None:
    """Sin líneas verticales ni fondos: cabecera en versalitas con filete verde, filas con filete fino y, en las filas
    de horas y de total, filete verde encima. Anchas (más de tres columnas), a todo el ancho; el resto, en la columna
    de texto."""
    tblpr = t.find(W + "tblPr")
    for e in list(tblpr):
        if etree.QName(e).localname in ("tblStyle", "tblBorders", "tblW", "tblInd", "jc", "tblCellMar", "tblLook",
                                        "tblLayout"):
            tblpr.remove(e)
    anchos = _ancho_tabla(t)
    estrecha = len(anchos) <= 3
    destino = ANCHO_TEXTO if estrecha else ANCHO
    total = sum(anchos)
    nuevos = [round(a * destino / total) for a in anchos]
    nuevos[-1] += destino - sum(nuevos)
    cabeceras = _cabeceras(t)
    if len(anchos) == 6 and RE_CIFRAS.match(cabeceras[1]):   # la tabla 4 (cabeceras: unidad o tarea, sesiones…)
        nuevos = ANCHOS_T4_PROYECTO if cabeceras[3].lower().startswith("peso") else ANCHOS_T4
    for g, a in zip(t.find(W + "tblGrid").findall(W + "gridCol"), nuevos, strict=True):
        g.set(W + "w", str(a))
    linea = f'w:sz="4" w:space="0" w:color="{C["l"]}"'
    tblpr.append(frag(f'<w:tblW w:w="{destino}" w:type="dxa"/>'))
    if estrecha:
        tblpr.append(frag(f'<w:tblInd w:w="{SANGRIA}" w:type="dxa"/>'))
    tblpr.append(frag(f'<w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="single" {linea}/>'
                      f'<w:right w:val="nil"/><w:insideH w:val="single" {linea}/><w:insideV w:val="nil"/>'
                      "</w:tblBorders>"))
    tblpr.append(frag('<w:tblLayout w:type="fixed"/>'))
    tblpr.append(frag('<w:tblCellMar><w:top w:w="62" w:type="dxa"/><w:left w:w="57" w:type="dxa"/>'
                      '<w:bottom w:w="62" w:type="dxa"/><w:right w:w="113" w:type="dxa"/></w:tblCellMar>'))
    ooxml.ordenar(tblpr, ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
                          "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd",
                          "tblLayout", "tblCellMar", "tblLook"])
    filas = t.findall(W + "tr")
    primera_total = next((f for f in filas[1:] if re.match(r"(?i)^(horas|total)", normal(texto(f)))), None)
    for k, fila in enumerate(filas):
        cab = k == 0
        trpr = fila.find(W + "trPr")
        if cab:
            if trpr is None:
                trpr = etree.Element(W + "trPr")
                fila.insert(0, trpr)
            if trpr.find(W + "tblHeader") is None:
                trpr.append(etree.Element(W + "tblHeader"))
        col = 0
        for tc in fila.findall(W + "tc"):
            tcpr = ooxml.tcpr(tc)
            span = int(tcpr.find(W + "gridSpan").get(W + "val")) if tcpr.find(W + "gridSpan") is not None else 1
            ooxml.hijo(tcpr, "tcW", ooxml.ORDEN_TCPR, w=str(sum(nuevos[col:col + span])), type="dxa")
            for e in list(tcpr):
                if etree.QName(e).localname in ("tcBorders", "shd", "tcMar"):
                    tcpr.remove(e)
            borde = ""
            if cab:
                borde = f'<w:bottom w:val="single" w:sz="10" w:space="0" w:color="{C["v7"]}"/>'
            elif fila is primera_total:
                borde = f'<w:top w:val="single" w:sz="8" w:space="0" w:color="{C["v7"]}"/>'
            if borde:
                tcpr.append(frag(f"<w:tcBorders>{borde}</w:tcBorders>"))
            ooxml.ordenar(tcpr, ooxml.ORDEN_TCPR)
            if cab:   # la letra de la cabecera ya es la de la cabecera: sin negrita ni cursiva
                for b in list(tc.iter(W + "b", W + "bCs", W + "i", W + "iCs")):
                    b.getparent().remove(b)
            cifras = 0 < col < len(cabeceras) and bool(RE_CIFRAS.match(cabeceras[col]))
            for p in tc.iter(W + "p"):
                lista = p.find(f"{W}pPr/{W}numPr") is not None
                pp = limpiar_ppr(p, "TablaCabecera" if cab else "TablaTexto", conservar=("numPr",))
                if cifras:
                    ooxml.hijo(pp, "jc", ooxml.ORDEN_PPR, val="right")
                if lista:
                    ooxml.hijo(pp, "ind", ooxml.ORDEN_PPR, left=str(VINETA), hanging=str(VINETA))
            col += span


def cuerpo(body: etree._Element, ambito: bool, nota: str) -> None:
    els = list(body)
    primer_titulo = next(i for i, e in enumerate(els) if ooxml.es_titulo(e))
    indice_i = next(i for i, e in enumerate(els) if e.tag == W + "p" and ooxml.estilo(e) == "Ttulodelatabla")
    # portada: todo hasta el párrafo con la primera sección; se rehace entera
    corte = next(i for i, e in enumerate(els) if e.tag == W + "p" and e.find(f"{W}pPr/{W}sectPr") is not None)
    assert corte < indice_i < primer_titulo, "la plantilla no empieza por portada, índice y apartados"
    sect_portada = (f'<w:sectPr><w:headerReference w:type="default" r:id="rIdEncPortada"/>'
                    f'<w:footerReference w:type="default" r:id="rIdPiePortada"/><w:type w:val="nextPage"/>'
                    f'<w:pgSz w:w="{A4[0]}" w:h="{A4[1]}"/><w:pgMar w:top="0" w:right="0" w:bottom="0" w:left="0" '
                    f'w:header="0" w:footer="680" w:gutter="0"/><w:cols w:space="708"/></w:sectPr>')
    for e in els[:corte + 1]:
        body.remove(e)
    nuevos = portada(sect_portada, ambito)
    for e in reversed(nuevos):
        body.insert(0, e)
    titulos(body)
    indice(body)
    # párrafos y tablas del cuerpo (después de la portada, que ya va con su diseño)
    ts = [p for p in body if ooxml.es_titulo(p)]
    numero = dict(zip(ts, numero_de(ts), strict=True))
    apartado = ""
    for e in list(body)[len(nuevos):]:
        apartado = numero.get(e, apartado)
        if apartado in ("1.1", "1.2") and e.tag == W + "p":   # las normas, sin cursiva: el enlace ya se distingue
            for x in list(e.iter(W + "i", W + "iCs")):
                x.getparent().remove(x)
        if e.tag == W + "tbl":
            tabla(e)
            runs(e)
            continue
        if e.tag != W + "p" or ooxml.es_titulo(e) or ooxml.estilo(e) in ("TDC2", "TDC3", "Ttulodelatabla"):
            continue
        if e.find(f"{W}pPr/{W}sectPr") is not None:
            continue
        runs(e)
        tab = e.find(f"{W}r/{W}tab") is not None
        if normal(texto(e)) == normal(nota):
            limpiar_ppr(e, "Fuente")
        elif e.find(f"{W}pPr/{W}numPr") is not None:
            limpiar_ppr(e, "Prrafodelista", conservar=("numPr",))
        else:   # párrafos de PIICT (Normal, p1…) y cualquier otro: texto del cuerpo
            limpiar_ppr(e, "Texto")
        if tab:   # «Evaluación inicial: ⇥ 30/09/2026»
            ooxml.hijo(ooxml.ppr(e), "tabs", ooxml.ORDEN_PPR).append(
                frag(f'<w:tab w:val="left" w:pos="{SANGRIA + VINETA + 1701}"/>'))
    # sección del cuerpo
    body.remove(body.find(W + "sectPr"))
    body.append(frag(seccion("rIdPie", final=True)))


# -- ajustes y fuentes ------------------------------------------------------------------------------------------------
ORDEN_AJUSTES = ["writeProtection", "view", "zoom", "removePersonalInformation", "removeDateAndTime",
                 "doNotDisplayPageBoundaries", "displayBackgroundShape", "printPostScriptOverText",
                 "printFractionalCharacterWidth", "printFormsData", "embedTrueTypeFonts", "embedSystemFonts",
                 "saveSubsetFonts", "saveFormsData", "mirrorMargins", "alignBordersAndEdges",
                 "bordersDoNotSurroundHeader", "bordersDoNotSurroundFooter", "gutterAtTop", "hideSpellingErrors",
                 "hideGrammaticalErrors", "activeWritingStyle", "proofState", "formsDesign", "attachedTemplate",
                 "linkStyles", "stylePaneFormatFilter", "stylePaneSortMethod", "documentType", "mailMerge",
                 "revisionView", "trackRevisions", "doNotTrackMoves", "doNotTrackFormatting", "documentProtection",
                 "autoFormatOverride", "styleLockTheme", "styleLockQFSet", "defaultTabStop", "autoHyphenation",
                 "consecutiveHyphenLimit", "hyphenationZone"]


def ajustes(pq: ooxml.Paquete) -> None:
    s = pq.xml("word/settings.xml")
    for nombre, attrs in (("embedTrueTypeFonts", {}), ("autoHyphenation", {}), ("hyphenationZone", {"val": "425"})):
        e = s.find(W + nombre)
        if e is None:
            e = etree.Element(W + nombre)
            previos = ORDEN_AJUSTES[:ORDEN_AJUSTES.index(nombre)]
            ancla = None
            for x in s:
                if isinstance(x.tag, str) and etree.QName(x).localname in previos:
                    ancla = x
            (ancla.addnext(e) if ancla is not None else s.insert(0, e))
        for a, v in attrs.items():
            e.set(W + a, v)
    for e in list(s.iter(W + "doNotHyphenateCaps")):
        e.getparent().remove(e)


def fuentes(pq: ooxml.Paquete) -> None:
    ids: dict[str, list[tuple[str, str, str]]] = {}
    rels = []
    for n, (archivo, familia, ranura) in enumerate(FUENTES, 1):
        clave = clave_fuente(archivo)
        pq.partes[f"word/fonts/font{n}.odttf"] = ofuscar((RECURSOS / archivo).read_bytes(), clave)
        rels.append(f'<Relationship Id="rIdF{n}" Type="{TIPO_REL}font" Target="fonts/font{n}.odttf"/>')
        ids.setdefault(familia, []).append((ranura, f"rIdF{n}", clave))
    out = []
    for familia, lista in ids.items():
        x = f'<w:font w:name="{familia}"><w:charset w:val="00"/><w:family w:val="swiss"/><w:pitch w:val="variable"/>'
        for ranura in ("Regular", "Bold", "Italic", "BoldItalic"):
            for r, rid, clave in lista:
                if r == ranura:
                    x += f'<w:embed{ranura} r:id="{rid}" w:fontKey="{clave}"/>'
        out.append(x + "</w:font>")
    pq.poner_xml("word/fontTable.xml", etree.fromstring((XML + f"<w:fonts {NS_DECL}>" + "".join(out)
                                                         + "</w:fonts>").encode()))
    pq.poner_xml("word/_rels/fontTable.xml.rels", etree.fromstring((
        XML + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(rels) + "</Relationships>").encode()))


def tipos(pq: ooxml.Paquete) -> None:
    ct = pq.xml("[Content_Types].xml")
    exts = {e.get("Extension") for e in ct.findall(ooxml.CT + "Default")}
    if "odttf" not in exts:
        etree.SubElement(ct, ooxml.CT + "Default", Extension="odttf", ContentType=CT_FUENTE)
        ct[:] = sorted(ct, key=lambda e: 0 if etree.QName(e).localname == "Default" else 1)
    for n in ("word/header1.xml", "word/header2.xml", "word/footer1.xml", "word/footer2.xml", "word/footer3.xml"):
        tipo = "header" if "header" in n else "footer"
        pq.tipo_override(n, f"application/vnd.openxmlformats-officedocument.wordprocessingml.{tipo}+xml")


# -- todo -------------------------------------------------------------------------------------------------------------
def aplicar(pq: ooxml.Paquete, nota: str, ambito: bool = False) -> ooxml.Paquete:
    """La plantilla marcada (ya limpia) con el diseño. `nota`: la de Educamos bajo la 4.1. Devuelve la misma."""
    doc = pq.xml("word/document.xml")
    cuerpo(doc.find(W + "body"), ambito, nota)
    pq.poner_xml("word/styles.xml", etree.fromstring(estilos().encode()))
    numeracion(pq)
    # encabezados y pies: header1/footer1, portada; header2/footer2, el resto
    for viejo in [n for n in pq.partes if n.startswith("word/media/")]:
        pq.quitar(viejo)
    for n in ("word/_rels/header1.xml.rels", "word/_rels/header2.xml.rels", "word/_rels/footer1.xml.rels",
              "word/_rels/footer2.xml.rels"):
        if pq.existe(n):
            pq.quitar(n)
    pq.partes["word/media/escudo.png"] = ESCUDO.read_bytes()
    pq.poner_xml("word/header1.xml", etree.fromstring((XML + f"<w:hdr {NS_DECL}>{_p('')}</w:hdr>").encode()))
    pq.poner_xml("word/footer1.xml", etree.fromstring(pie_portada("rIdEscudo").encode()))
    pq.poner_xml("word/header2.xml", etree.fromstring(encabezado().encode()))
    pq.poner_xml("word/footer2.xml", etree.fromstring(pie().encode()))
    pq.poner_xml("word/footer3.xml", etree.fromstring(pie_indice().encode()))
    pq.poner_xml("word/_rels/footer1.xml.rels", etree.fromstring((
        XML + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'<Relationship Id="rIdEscudo" Type="{TIPO_REL}image" Target="media/escudo.png"/></Relationships>').encode()))
    rels = pq.rels("word/document.xml")
    for r in list(rels):
        if r.get("Type").rsplit("/", 1)[-1] in ("header", "footer"):
            rels.remove(r)
    for rid, tipo, destino in (("rIdEncPortada", "header", "header1.xml"), ("rIdPiePortada", "footer", "footer1.xml"),
                               ("rIdEncabezado", "header", "header2.xml"), ("rIdPie", "footer", "footer2.xml"),
                               ("rIdPieIndice", "footer", "footer3.xml")):
        etree.SubElement(rels, "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship",
                         Id=rid, Type=TIPO_REL + tipo, Target=destino)
    # notas al pie y al final: sin formato propio
    for n in ("word/footnotes.xml", "word/endnotes.xml"):
        if pq.existe(n):
            runs(pq.xml(n))
    ajustes(pq)
    fuentes(pq)
    tipos(pq)
    return pq


def comprobar(pq: ooxml.Paquete) -> list[str]:
    """Fuentes incrustadas que se recuperan con su clave, ningún tipo del sistema y la numeración de los títulos."""
    errores = []
    tf = pq.xml("word/fontTable.xml")
    rels = {r.get("Id"): r.get("Target") for r in pq.rels("word/fontTable.xml")}
    incrustadas = 0
    for e in tf.iter():
        if isinstance(e.tag, str) and etree.QName(e).localname.startswith("embed"):
            rid, clave = e.get(ooxml.R + "id"), e.get(W + "fontKey")
            if ofuscar(pq.partes["word/" + rels[rid]], clave)[:4] != b"\x00\x01\x00\x00":
                errores.append(f"fuente {rels[rid]}: no se recupera con su clave")
            incrustadas += 1
    if incrustadas != len(FUENTES):
        errores.append(f"fuentes incrustadas: {incrustadas} de {len(FUENTES)}")
    for n in pq.partes:
        if n.startswith("word/") and n.endswith(".xml") and n != "word/fontTable.xml":
            for f in pq.xml(n).iter(W + "rFonts"):
                for v in f.attrib.values():
                    if not v.startswith("Barlow"):
                        errores.append(f"{n}: fuente fuera del diseño «{v}»")
    estilos_ = pq.xml("word/styles.xml")
    for sid in ("Ttulo2", "Ttulo3"):
        st = estilos_.find(f"{W}style[@{W}styleId='{sid}']")
        if st is None or st.find(f"{W}pPr/{W}numPr/{W}numId") is None:
            errores.append(f"el estilo {sid} no lleva la numeración de los títulos")
    return sorted(set(errores))

