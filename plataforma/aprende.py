"""La web de aprendizaje: convierte los documentos del proyecto en un sitio de documentacion.

Por que existe
--------------
Este proyecto lleva **1,1 MB de documentos** escritos a lo largo de varios dias: el registro del
dia a dia (`docs/BACKLOG.md`), los informes (`docs/DIAGNOSTICO-MATCHING.md`, `docs/LAYA.md`), la
operacion (`docs/OPERACION.md`) y las decisiones (`docs/MODELO.md`). Ese material tiene dos
problemas para quien quiere **aprender** con el:

1. **No tiene orden de lectura.** Son sesenta ficheros planos: nadie sabe por donde empezar, y lo
   que explica *como se mide* esta mezclado con lo que explica *que se decidio el martes*.
2. **Vive en markdown dentro del repositorio**, que esta bien para trabajarlo y mal para
   estudiarlo: sin indice navegable, sin buscar, sin volver atras.

Asi que hay dos cosas separadas a proposito:

    docs/aprende/*.md     el **curso**: capitulos en orden, agrupados en secciones, con teoria y
                          con los numeros medidos de este proyecto como caso practico
    docs/*.md             la **referencia**: todo lo demas, tal cual se escribio

Este modulo las junta y las pinta con la forma de un sitio de documentacion: barra de arriba con
buscador, indice lateral por secciones, indice de la pagina a la derecha, migas de pan, tarjetas
de anterior/siguiente, boton de copiar en cada bloque de codigo, avisos destacados y modo oscuro.
**No inventa contenido**: convierte markdown en HTML, reescribe los enlaces entre documentos para
que funcionen dentro del sitio, y genera el indice. Si un numero esta mal, esta mal en el
markdown, que es la unica fuente.

Como se corre
-------------
    uv run --extra docs python -m plataforma.aprende
    uv run --extra docs python -m plataforma.aprende --salida otra/carpeta

Escribe `plataforma/web/aprende/`, y ese sitio:

  - **se abre sin servidor** (doble clic en `index.html`): el buscador lleva su indice en un
    fichero al lado, no pide nada por red, y no hay ni una fuente de terceros;
  - **o se sirve por Caddy** en `/aprende/` (`plataforma/docker-compose.yml`), que es como se lee
    desde el movil.

**Nada de scripts ni estilos en linea**, y no es un capricho de estilo: Caddy sirve esto con
`script-src 'self'` y `style-src 'self'`, asi que un `<script>` incrustado **no se ejecuta** (el
buscador se quedo muerto en produccion por eso, medido el 24 de septiembre de 2026). Todo el
JavaScript va en `buscar.js` y `copiar.js`.

Como se anade un capitulo
-------------------------
Un fichero nuevo en `docs/aprende/` con su cabecera:

    ---
    seccion: Algoritmos y evaluacion
    resumen: Una linea que sale en el indice y en el buscador.
    en_una_frase: La idea del capitulo, en una frase, para quien llega con prisa.
    ---

    # 16 · El titulo del capitulo

`en_una_frase` sale en un recuadro justo debajo del titulo (lo primero que se lee, sobre todo
desde el movil) y vive en la cabecera a proposito: asi no se puede quedar desfasado respecto al
capitulo. El numero del nombre del fichero manda en el orden dentro de su seccion, y la seccion
tiene que estar en `SECCIONES` (si no, el capitulo sale en «Otros» y el generador lo avisa). No
hay que tocar este fichero ni el indice: aparece solo, y `tests/test_aprende.py` lo comprueba
--incluida la frase, porque un recuadro que desaparece en silencio es peor que no tenerlo--.

Las dos dependencias (`markdown-it-py`, `linkify-it-py`) son **puras de Python**: el scraper y la
API no las necesitan, por eso van en el extra `docs`.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
CURSO = DOCS / "aprende"
SALIDA_POR_DEFECTO = RAIZ / "plataforma" / "web" / "aprende"

# El orden de las secciones **es el temario**: de lo mas general a lo mas concreto, y al final
# la referencia. Un capitulo puede llamarse como quiera mientras su `seccion` este aqui.
SECCIONES = (
    "Empieza aquí",
    "Fundamentos",
    "Ingeniería de datos",
    "Algoritmos y evaluación",
    "Medidas y agregados",
    "Análisis y decisión",
    "Práctica del análisis",
    "Investigación y anexos",
)

# Lo que se pinta cuando un capitulo no declara seccion: se ve, y se avisa por consola.
SIN_SECCION = "Otros"

# Los avisos que se destacan. La primera palabra de la cita manda, y el texto sigue igual.
AVISOS = {
    "nota": ("Nota", "nota"),
    "aviso": ("Aviso", "aviso"),
    "trampa": ("Trampa", "trampa"),
    "leccion": ("La lección", "leccion"),
    "regla": ("Regla de la casa", "regla"),
}

# El aviso que se da cuando falta el extra, con el comando exacto.
FALTA_EXTRA = (
    "Falta el extra `docs` (markdown-it-py). Se instala con:\n"
    "    uv sync --extra plataforma --extra docs\n"
    "y se corre con:\n"
    "    uv run --extra docs python -m plataforma.aprende"
)


@dataclass
class Pagina:
    """Un documento convertido en pagina, con lo que el indice necesita saber de el."""

    ruta: Path
    slug: str
    titulo: str
    seccion: str = SIN_SECCION
    resumen: str = ""
    # La frase que resume el capitulo, en la cabecera del documento (`en_una_frase:`). Sale en un
    # recuadro justo debajo del titulo: es lo que se lee cuando alguien llega con prisa o desde el
    # movil, y lo unico que hay que entender si no se lee nada mas.
    en_una_frase: str = ""
    curso: bool = False
    orden: int = 0
    # Las anclas que ha puesto el conversor, en orden: `(nivel, id, texto)`. Salen de lo que se
    # ha pintado de verdad, no de volver a calcular el slug (que fue un fallo real: el indice
    # apuntaba a `#lo-que-falta` y el encabezado era `#lo-que-falta-2`).
    anclas: list[tuple[str, str, str]] = field(default_factory=list)
    cuerpo: str = ""
    # Cuantas palabras, para poder decir el tamaño sin abrir el capitulo.
    palabras: int = 0

    @property
    def fichero(self) -> str:
        return f"{self.slug}.html"

    @property
    def secciones(self) -> list[str]:
        return [t for n, _i, t in self.anclas if n == "h2"]


def _plano(texto: str) -> str:
    """Minusculas sin tildes: para anclas y para el buscador."""
    sin = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin if not unicodedata.combining(c)).lower()


def slug_de(texto: str) -> str:
    """`01. Los datos y sus capas` -> `01-los-datos-y-sus-capas`."""
    plano = _plano(texto)
    limpio = re.sub(r"[^a-z0-9]+", "-", plano).strip("-")
    return limpio or "pagina"


def _motor():
    """El markdown, ya configurado. Con `commonmark` y dos reglas de GitHub.

    `commonmark` es el preset mas aburrido y el que menos sorpresas da. Lo unico que se activa de
    mas son las **tablas** y el tachado, que es lo que los documentos usan de verdad.
    `html=False` (por defecto) es a proposito: un `<script>` escrito en un documento se vera como
    texto y no se ejecutara.
    """
    from markdown_it import MarkdownIt

    md = MarkdownIt("commonmark")
    md.enable(["table", "strikethrough"])
    return md


def _con_anclas(md) -> None:
    """Pone `id` a los encabezados (para el indice de la pagina y los enlaces internos).

    Markdown-it no los pone solo. El ancla se repite si dos encabezados se llaman igual, y se
    resuelve numerando: en los documentos hay mas de un «Lo que falta». Las anclas se guardan en
    `env` porque el indice lateral tiene que enseñar **los que se han pintado**, no lo que
    saldria de volver a calcular el slug.
    """
    vistos: dict[str, int] = {}

    def pinta(tokens, idx, opciones, env):
        texto = tokens[idx + 1].content if idx + 1 < len(tokens) else ""
        nombre = slug_de(texto)
        vistos[nombre] = vistos.get(nombre, 0) + 1
        if vistos[nombre] > 1:
            nombre = f"{nombre}-{vistos[nombre]}"
        nivel = tokens[idx].tag
        env.setdefault("anclas", []).append({"nivel": nivel, "id": nombre, "texto": texto})
        # El `#` del final aparece al pasar por encima: es la forma de copiar el enlace a un
        # apartado concreto, que es lo primero que hace alguien que quiere pasar un dato.
        return (f'<{nivel} id="{nombre}" class="con-ancla">'
                f'<a class="ancla" href="#{nombre}" aria-label="Enlace a este apartado">#</a>')

    md.renderer.rules["heading_open"] = pinta


def _destaca_avisos(cuerpo: str) -> str:
    """Convierte `> **Nota:** …` en un aviso con su color.

    Se hace **despues** de pintar, sobre el HTML, por una razon practica: markdown no tiene
    «avisos» y meter una extension propia por cuatro etiquetas no compensa. Se mira la primera
    negrita de la cita y se le pone clase; si no es ninguna de las conocidas, se queda como cita
    normal. El texto no se toca.
    """
    def cambia(m: re.Match) -> str:
        dentro = m.group(1)
        primera = re.match(r"\s*<p>\s*<strong>([^<:]+):?</strong>", dentro)
        if not primera:
            return m.group(0)
        clave = _plano(primera.group(1).strip())
        # «**La leccion:**» y «**Leccion:**» son el mismo aviso: se quita el articulo antes de
        # buscar. La primera version no lo hacia, y no se destacaba **ni uno** de los avisos del
        # material (los capitulos dicen «La leccion:»).
        clave = re.sub(r"^(la|el|los|las)\s+", "", clave)
        if clave not in AVISOS:
            return m.group(0)
        etiqueta, clase = AVISOS[clave]
        limpio = dentro.replace(primera.group(0), "<p>", 1)
        return (f'<aside class="aviso {clase}"><p class="aviso-titulo">{etiqueta}</p>'
                f"{limpio}</aside>")

    return re.sub(r"<blockquote>(.*?)</blockquote>", cambia, cuerpo, flags=re.S)


def _reescribe_enlaces(cuerpo: str, por_nombre: dict[str, str]) -> str:
    """Cambia los enlaces a `.md` por enlaces a la pagina que les toca.

    Los documentos se enlazan entre si por nombre (`docs/BACKLOG.md`, `MODELO.md`,
    `../docs/API.md`) y el sitio es **plano**: todas las paginas estan en la misma carpeta, asi
    que basta con quedarse con el nombre del fichero. Un enlace a algo que no esta en `docs/` se
    deja como esta -- es una salida honesta a un fichero del repositorio --, y el ancla
    (`#seccion`) se conserva.
    """
    def cambia(m: re.Match) -> str:
        destino = m.group(1)
        ruta, _, ancla = destino.partition("#")
        if not ruta.endswith(".md"):
            return m.group(0)
        pagina = por_nombre.get(Path(ruta).name)
        if pagina is None:
            return m.group(0)
        return f'href="{pagina}#{ancla}"' if ancla else f'href="{pagina}"'

    return re.sub(r'href="([^"]+)"', cambia, cuerpo)


def _front_matter(texto: str) -> tuple[dict[str, str], str]:
    """La cabecera `--- clave: valor ---` de un capitulo, si la trae.

    Se admite a proposito una sola forma muy simple (clave: valor, una por linea) para no meter
    un lector de YAML por dos campos. Si el fichero no empieza por `---`, no hay cabecera.
    """
    if not texto.startswith("---"):
        return {}, texto
    fin = texto.find("\n---", 3)
    if fin == -1:
        return {}, texto
    datos: dict[str, str] = {}
    for linea in texto[3:fin].splitlines():
        if ":" in linea:
            clave, _, valor = linea.partition(":")
            datos[clave.strip().lower()] = valor.strip()
    return datos, texto[fin + 4:].lstrip("\n")


def _titulo(texto: str, id_por_defecto: str) -> str:
    """El primer encabezado de nivel 1, o el nombre del fichero si no hay."""
    for linea in texto.splitlines():
        if linea.startswith("# "):
            return linea[2:].strip()
    return id_por_defecto


def _primer_parrafo(texto: str, limite: int = 220) -> str:
    """El primer parrafo de verdad, sin encabezados ni listas, para el indice y el buscador."""
    parrafo: list[str] = []
    for linea in texto.splitlines():
        limpia = linea.strip()
        if not limpia:
            if parrafo:
                break
            continue
        if limpia.startswith(("#", ">", "|", "```", "    ")) or re.match(r"^[-*\d]", limpia):
            continue
        parrafo.append(limpia)
    return " ".join(parrafo)[:limite]


def recoge() -> list[Pagina]:
    """Todas las paginas: primero el curso (en orden), despues la referencia."""
    if not DOCS.exists():
        return []
    paginas: list[Pagina] = []
    capitulos = sorted(CURSO.glob("*.md")) if CURSO.exists() else []
    for numero, ruta in enumerate(capitulos):
        crudo = ruta.read_text(encoding="utf-8")
        datos, texto = _front_matter(crudo)
        paginas.append(Pagina(
            ruta=ruta, slug=ruta.stem, titulo=_titulo(texto, ruta.stem),
            seccion=datos.get("seccion", SIN_SECCION), curso=True, orden=numero,
            resumen=datos.get("resumen", "") or _primer_parrafo(texto),
            en_una_frase=datos.get("en_una_frase", ""),
            palabras=len(texto.split())))
    for ruta in sorted(DOCS.glob("*.md")):
        crudo = ruta.read_text(encoding="utf-8")
        _datos, texto = _front_matter(crudo)
        paginas.append(Pagina(
            ruta=ruta, slug=ruta.stem, titulo=_titulo(texto, ruta.stem), curso=False,
            resumen=_primer_parrafo(texto), palabras=len(texto.split())))
    return paginas


def _caja_frase(cuerpo: str, frase: str) -> str:
    """Pone el recuadro de `en_una_frase:` justo debajo del titulo del capitulo.

    Va **en la cabecera del documento** y no dentro del texto a proposito: asi el recuadro no se
    puede quedar desfasado respecto al capitulo (se cambia la frase donde se cambia el titulo), y
    el dia que alguien reescriba el capitulo lo tiene delante. Si el documento no declara la
    frase, no se pinta nada: es una mejora, no un requisito para escribir.
    """
    if not frase:
        return cuerpo
    caja = ('<aside class="frase"><p class="frase-titulo">En una frase</p>'
            f"<p>{html.escape(frase)}</p></aside>")
    corte = cuerpo.find("</h1>")
    if corte == -1:
        return caja + cuerpo
    fin = corte + len("</h1>")
    return cuerpo[:fin] + caja + cuerpo[fin:]


def _capitulos(paginas: list[Pagina], seccion: str) -> list[Pagina]:
    return [p for p in paginas if p.curso and p.seccion == seccion]


# --------------------------------------------------------------------------- plantillas ---

CABECERA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title>
<meta name="description" content="{descripcion}">
<meta name="color-scheme" content="light dark">
<link rel="stylesheet" href="estilo.css">
<script src="indice.js" defer></script>
<script src="buscar.js" defer></script>
<script src="copiar.js" defer></script>
</head>
<body>
<a class="saltar" href="#contenido">Saltar al contenido</a>
<header class="barra">
  <div class="barra-dentro">
    <a class="marca" href="index.html"><span class="marca-punto"></span>Cesta · aprender datos</a>
    <div class="buscador">
      <input id="buscar" type="search" placeholder="Buscar en el material…" autocomplete="off"
             aria-label="Buscar en el material" aria-expanded="false">
      <kbd>/</kbd>
      <ul id="resultados" class="resultados" hidden></ul>
    </div>
    <a class="barra-enlace" href="index.html#curso">Temario</a>
  </div>
</header>
<div class="marco">
  <aside class="lateral" aria-label="Indice del material">
    <details open>
      <summary>Indice del material</summary>
      {lateral}
    </details>
  </aside>
  <main id="contenido">
    <nav class="migas" aria-label="Migas de pan">{migas}</nav>
    {cuerpo}
    <nav class="paso" aria-label="Capitulos anteriores y siguientes">{paso}</nav>
    <footer class="pie">
      <p>Fuente: <code>{fuente}</code> · {palabras} palabras</p>
      <p>Generado por <code>plataforma/aprende.py</code>: no se edita a mano, se cambia el
      documento y se vuelve a generar.</p>
    </footer>
  </main>
  {toc}
</div>
</body>
</html>
"""


def _lateral(paginas: list[Pagina], actual: Pagina) -> str:
    """El indice de la izquierda: las secciones del curso y donde estas ahora.

    La referencia no se lista entera: son mas de sesenta documentos y taparian el curso. Va con
    su propia pagina de indice (`referencia.html`).
    """
    filas: list[str] = ['<nav class="nav-lateral">']
    for seccion in SECCIONES:
        capitulos = _capitulos(paginas, seccion)
        if not capitulos:
            continue
        filas.append(f'<p class="nav-seccion">{html.escape(seccion)}</p><ul>')
        for p in capitulos:
            marca = ' aria-current="page"' if p.slug == actual.slug else ""
            filas.append(f'<li><a href="{p.fichero}"{marca}>{html.escape(p.titulo)}</a></li>')
        filas.append("</ul>")
    otros = _capitulos(paginas, SIN_SECCION)
    if otros:
        filas.append('<p class="nav-seccion">Otros</p><ul>')
        filas.extend(f'<li><a href="{p.fichero}">{html.escape(p.titulo)}</a></li>' for p in otros)
        filas.append("</ul>")
    marca = ' aria-current="page"' if not actual.curso else ""
    filas.append('<p class="nav-seccion">Referencia</p><ul>'
                 f'<li><a href="referencia.html"{marca}>Los 60 documentos del proyecto</a></li>'
                 "</ul></nav>")
    return "".join(filas)


def _migas(pagina: Pagina, paginas: list[Pagina]) -> str:
    if not pagina.curso:
        return ('<a href="index.html">Material</a> <span>/</span> '
                '<a href="referencia.html">Referencia</a> <span>/</span> '
                f"<span>{html.escape(pagina.titulo)}</span>")
    return ('<a href="index.html">Material</a> <span>/</span> '
            f'<a href="index.html#{slug_de(pagina.seccion)}">{html.escape(pagina.seccion)}</a>'
            f' <span>/</span> <span>{html.escape(pagina.titulo)}</span>')


def _paso(pagina: Pagina, paginas: list[Pagina]) -> str:
    """Las tarjetas de anterior y siguiente, contando el curso entero en orden de temario."""
    curso = [p for s in SECCIONES for p in _capitulos(paginas, s)]
    curso += _capitulos(paginas, SIN_SECCION)
    if pagina not in curso:
        return ('<a class="paso-caja" href="referencia.html"><span>Referencia</span>'
                "<strong>Los documentos del proyecto</strong></a>")
    i = curso.index(pagina)
    cajas = []
    if i:
        antes = curso[i - 1]
        cajas.append(f'<a class="paso-caja antes" href="{antes.fichero}"><span>Anterior</span>'
                     f"<strong>{html.escape(antes.titulo)}</strong></a>")
    else:
        cajas.append('<a class="paso-caja antes" href="index.html"><span>Empezar</span>'
                     "<strong>El temario</strong></a>")
    if i + 1 < len(curso):
        despues = curso[i + 1]
        cajas.append(f'<a class="paso-caja despues" href="{despues.fichero}"><span>Siguiente</span>'
                     f"<strong>{html.escape(despues.titulo)}</strong></a>")
    return "".join(cajas)


def _toc(pagina: Pagina) -> str:
    """El indice de la pagina, a la derecha. Solo en pantallas anchas."""
    if not pagina.anclas:
        return '<aside class="toc" aria-hidden="true"></aside>'
    filas = ['<aside class="toc"><nav aria-label="En esta pagina"><p>En esta pagina</p><ul>']
    for nivel, ancla, texto in pagina.anclas:
        if nivel not in ("h2", "h3"):
            continue
        clase = ' class="nivel-3"' if nivel == "h3" else ""
        filas.append(f'<li{clase}><a href="#{ancla}">{html.escape(texto)}</a></li>')
    filas.append("</ul></nav></aside>")
    return "".join(filas)


def _portada(paginas: list[Pagina]) -> str:
    """La portada: que es esto, por donde empezar, y el temario por secciones."""
    curso = [p for p in paginas if p.curso]
    total = sum(p.palabras for p in curso)
    bloques = []
    for seccion in (*SECCIONES, SIN_SECCION):
        capitulos = _capitulos(paginas, seccion)
        if not capitulos:
            continue
        tarjetas = "".join(
            f'<li><a href="{p.fichero}"><strong>{html.escape(p.titulo)}</strong>'
            f'<span>{html.escape(p.resumen)}</span></a></li>' for p in capitulos)
        bloques.append(
            f'<section class="bloque" id="{slug_de(seccion)}">'
            f"<h2>{html.escape(seccion)}</h2><ul class=\"tarjetas\">{tarjetas}</ul></section>")
    return f"""<div class="portada">
  <h1>Aprender datos con un proyecto de verdad</h1>
  <p class="entrada">
    Este no es el manual de una aplicacion: es <strong>material de estudio</strong> sobre
    ingenieria de datos, algoritmos, estadistica y scraping, que usa un caso real -- comparar los
    precios de cinco supermercados espanoles, todos los dias, en un PC de casa -- para explicar
    cada idea <strong>con numeros medidos</strong> y el comando que los reproduce.
  </p>
  <p class="entrada-meta">{len(curso)} capitulos · {total:,} palabras · y detras, los
     documentos del proyecto que se citan uno a uno.</p>  <div class="como-empezar">
    <h2>Por donde empezar</h2>
    <ol>
      <li>Si no sabes de que va esto: <a href="00-como-usar-este-material.html">Como usar este
          material</a>.</li>
      <li>Si vienes a por scraping: <a href="15-scraping.html">Como se recoge el dato</a>.</li>
      <li>Si estas empezando con datos: <a href="13-fundamentos-del-dato.html">Que es un dato</a>
          (valor, grano, clave y ausencia).</li>
      <li>Si vienes a por algoritmos: <a href="04-emparejar-productos.html">Emparejar
          productos</a> y <a href="05-medir-el-emparejador.html">como se mide</a>.</li>
      <li>Si vas a montar lo tuyo: <a href="14-el-stack-explicado.html">el stack</a>, pieza a
          pieza y con lo que costaria quitarlas.</li>
      <li>Y si vienes a aprender a medir: <a href="12-medir-sin-enganarse.html">los instrumentos
          que mienten</a>.</li>
    </ol>
  </div>
  {''.join(bloques)}
  <section class="bloque">
    <h2>Referencia</h2>
    <p class="nota">Todo lo demas que se ha escrito: <a href="referencia.html">los documentos
    del proyecto</a> (decisiones, informes, operacion y el registro del dia a dia). No es un
    curso; es donde se comprueba de donde sale cada cosa.</p>
  </section>
</div>
"""


def _indice_referencia(paginas: list[Pagina]) -> str:
    """El listado de la referencia, con el primer parrafo de cada documento."""
    docs = sorted([p for p in paginas if not p.curso], key=lambda p: p.titulo)
    letra = ""
    filas: list[str] = []
    for p in docs:
        inicial = p.titulo[:1].upper()
        if inicial != letra:
            letra = inicial
            filas.append(f'<h2 id="letra-{slug_de(letra)}">{html.escape(letra)}</h2>')
        filas.append(f'<article class="referencia-doc"><h3><a href="{p.fichero}">'
                     f"{html.escape(p.titulo)}</a></h3>"
                     f'<p>{html.escape(p.resumen)}</p>'
                     f'<p class="nota"><code>{p.ruta.relative_to(RAIZ).as_posix()}</code> · '
                     f"{p.palabras:,} palabras</p></article>")
    return ('<h1>Referencia: los documentos del proyecto</h1>'
            "<p class=\"entrada\">Los documentos de trabajo, tal y como se escribieron: el "
            "registro del dia a dia, los informes, la operacion y las decisiones. Estan aqui "
            "porque el curso los cita continuamente y conviene poder abrirlos.</p>"
            + "".join(filas))


ESTILO = """/* El material, con la forma de un sitio de documentacion: barra arriba, indice lateral,
   indice de la pagina a la derecha, y el contenido en una columna que no pasa de 74 caracteres
   por linea (que es lo que se lee comodo). Los colores son los mismos nombres que usa la
   aplicacion (`plataforma/web/app/src/estilos.css`), para que las dos cosas se lean igual.
   Claro y oscuro por `prefers-color-scheme`, sin interruptor: el sistema ya lo sabe. */
:root {
  --fondo: #ffffff; --fondo-suave: #f7f8fa; --panel: #ffffff; --tinta: #16181b;
  --tinta-suave: #5b6169; --borde: #e4e6ea; --borde-fuerte: #cfd3d9;
  --acento: #0b5cab; --acento-suave: #eef5fd; --codigo: #f6f7f9; --codigo-tinta: #24313f;
  --nota: #eef5fd; --aviso: #fff7e6; --trampa: #fdecec; --leccion: #ecf8f1; --regla: #f2effd;
  --ancho: 74ch;
}
@media (prefers-color-scheme: dark) {
  :root {
    --fondo: #131518; --fondo-suave: #16181b; --panel: #1a1d21; --tinta: #eceef0;
    --tinta-suave: #a3aab2; --borde: #2b2f35; --borde-fuerte: #3a3f46;
    --acento: #7cc2ff; --acento-suave: #12283c; --codigo: #1f2328; --codigo-tinta: #dfe4ea;
    --nota: #12283c; --aviso: #33270f; --trampa: #3a1d1d; --leccion: #123023; --regla: #241f3d;
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 5rem; }
body {
  margin: 0; background: var(--fondo); color: var(--tinta);
  font: 16px/1.7 ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.saltar { position: absolute; left: -9999px; }
.saltar:focus { left: 1rem; top: .5rem; background: var(--acento); color: #fff; padding: .5rem 1rem; border-radius: .4rem; z-index: 50; }
a { color: var(--acento); text-underline-offset: 2px; }
a:hover { text-decoration: underline; }

/* ---------------------------------------------------------------- barra de arriba --- */
.barra {
  position: sticky; top: 0; z-index: 30; background: color-mix(in srgb, var(--panel) 92%, transparent);
  backdrop-filter: blur(8px); border-bottom: 1px solid var(--borde);
}
.barra-dentro {
  display: flex; align-items: center; gap: 1rem; max-width: 1500px; margin: 0 auto;
  padding: .6rem 1rem; flex-wrap: wrap;
}
.marca { display: inline-flex; align-items: center; gap: .5rem; font-weight: 700; color: var(--tinta); text-decoration: none; white-space: nowrap; }
.marca-punto { width: .6rem; height: .6rem; border-radius: 999px; background: var(--acento); display: inline-block; }
.buscador { position: relative; flex: 1 1 18rem; max-width: 34rem; }
.buscador input {
  width: 100%; padding: .5rem .75rem; font-size: .95rem; color: var(--tinta);
  background: var(--fondo-suave); border: 1px solid var(--borde); border-radius: .5rem;
}
.buscador input:focus { outline: 2px solid var(--acento); outline-offset: 1px; background: var(--panel); }
.buscador kbd {
  position: absolute; right: .5rem; top: 50%; transform: translateY(-50%);
  font: .75rem/1 ui-monospace, monospace; color: var(--tinta-suave);
  border: 1px solid var(--borde-fuerte); border-radius: .3rem; padding: .2rem .35rem;
}
.barra-enlace { color: var(--tinta-suave); text-decoration: none; font-size: .92rem; }
.resultados {
  position: absolute; inset: calc(100% + .4rem) 0 auto 0; list-style: none; margin: 0; padding: .25rem;
  background: var(--panel); border: 1px solid var(--borde); border-radius: .6rem; max-height: 60vh;
  overflow-y: auto; box-shadow: 0 12px 28px rgb(0 0 0 / .14);
}
.resultados li { padding: .45rem .55rem; border-radius: .4rem; }
.resultados li:hover { background: var(--fondo-suave); }
.resultados a { font-weight: 600; text-decoration: none; }
.resultados .tipo { color: var(--tinta-suave); font-size: .74rem; text-transform: uppercase; letter-spacing: .04em; margin-left: .4rem; }
.resultados .secs, .resultados .vacio { color: var(--tinta-suave); font-size: .84rem; }

/* ------------------------------------------------------------------------- columnas --- */
.marco {
  display: grid; grid-template-columns: 1fr; gap: 2.5rem; max-width: 1500px; margin: 0 auto;
  padding: 1.5rem 1rem 4rem;
}
@media (min-width: 1024px) { .marco { grid-template-columns: 17rem minmax(0, 1fr); } }
@media (min-width: 1360px) { .marco { grid-template-columns: 17rem minmax(0, 1fr) 15rem; } }
main { min-width: 0; }
.contenido-ancho { grid-column: 1 / -1; }

.lateral details { border: 0; }
.lateral summary {
  cursor: pointer; font-weight: 600; font-size: .9rem; padding: .5rem 0; color: var(--tinta-suave);
  border-bottom: 1px solid var(--borde); margin-bottom: .5rem;
}
@media (min-width: 1024px) {
  .lateral { position: sticky; top: 4.2rem; align-self: start; max-height: calc(100vh - 5rem); overflow-y: auto; }
  .lateral summary { display: none; }
  .lateral details > .nav-lateral { display: block; }
}
.nav-seccion {
  margin: 1.1rem 0 .35rem; font-size: .72rem; font-weight: 700; letter-spacing: .07em;
  text-transform: uppercase; color: var(--tinta-suave);
}
.nav-lateral ul { list-style: none; margin: 0; padding: 0; }
.nav-lateral li { margin: .1rem 0; }
.nav-lateral a {
  display: block; padding: .3rem .5rem; border-radius: .4rem; font-size: .9rem;
  color: var(--tinta); text-decoration: none; border-left: 2px solid transparent;
}
.nav-lateral a:hover { background: var(--fondo-suave); }
.nav-lateral a[aria-current="page"] { background: var(--acento-suave); border-left-color: var(--acento); font-weight: 600; }

.toc { display: none; }
@media (min-width: 1360px) {
  .toc { display: block; position: sticky; top: 4.2rem; align-self: start; font-size: .86rem; max-height: calc(100vh - 5rem); overflow-y: auto; }
}
.toc p { margin: 0 0 .4rem; font-size: .72rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; color: var(--tinta-suave); }
.toc ul { list-style: none; margin: 0; padding: 0; border-left: 1px solid var(--borde); }
.toc li { margin: .15rem 0; }
.toc a { display: block; padding: .15rem .6rem; color: var(--tinta-suave); text-decoration: none; border-left: 2px solid transparent; margin-left: -1px; }
.toc a:hover { color: var(--acento); border-left-color: var(--borde-fuerte); }
.toc li.nivel-3 a { padding-left: 1.3rem; font-size: .82rem; }

.migas { font-size: .84rem; color: var(--tinta-suave); margin-bottom: 1.2rem; }
.migas a { color: var(--tinta-suave); }
.migas span { margin: 0 .3rem; }

/* ------------------------------------------------------------------------ contenido --- */
article { max-width: var(--ancho); }
article h1 { font-size: 2rem; line-height: 1.2; letter-spacing: -.01em; margin: .2rem 0 1rem; }
article h2 { font-size: 1.35rem; margin: 2.6rem 0 .8rem; padding-top: .6rem; border-top: 1px solid var(--borde); }
article h3 { font-size: 1.08rem; margin: 1.8rem 0 .5rem; }
article p, article li { max-width: var(--ancho); }
article ul, article ol { padding-left: 1.3rem; }
article li { margin: .3rem 0; }
article hr { border: 0; border-top: 1px solid var(--borde); margin: 2.5rem 0; }
article strong { font-weight: 650; }
.con-ancla { position: relative; }
.con-ancla .ancla {
  position: absolute; left: -1.1rem; top: 0; opacity: 0; text-decoration: none;
  color: var(--tinta-suave); font-weight: 400;
}
.con-ancla:hover .ancla, .ancla:focus { opacity: 1; }
@media (max-width: 1100px) { .con-ancla .ancla { display: none; } }

code { background: var(--codigo); color: var(--codigo-tinta); padding: .12rem .35rem; border-radius: .3rem; font-size: .89em; }
pre {
  position: relative; background: var(--codigo); border: 1px solid var(--borde); border-radius: .6rem;
  padding: .9rem 1rem; overflow-x: auto; margin: 1.2rem 0;
}
pre code { background: none; padding: 0; font: 0.86rem/1.6 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.copiar {
  position: absolute; top: .5rem; right: .5rem; font: .74rem/1 ui-sans-serif, system-ui, sans-serif;
  padding: .35rem .55rem; border: 1px solid var(--borde-fuerte); border-radius: .4rem;
  background: var(--panel); color: var(--tinta-suave); cursor: pointer;
}
.copiar:hover { color: var(--tinta); }
.copiar.hecho { border-color: var(--acento); color: var(--acento); }

table { border-collapse: collapse; width: 100%; margin: 1.4rem 0; font-size: .92rem; display: block; overflow-x: auto; }
th, td { border-bottom: 1px solid var(--borde); padding: .55rem .7rem; text-align: left; vertical-align: top; }
thead th { border-bottom: 2px solid var(--borde-fuerte); background: var(--fondo-suave); font-weight: 650; }
tbody tr:hover { background: var(--fondo-suave); }
/* Los numeros, con cifras de ancho fijo: aqui se comparan columnas de precios y porcentajes, y
   con cifras proporcionales no se alinean. */
td.num, .cifra { font-variant-numeric: tabular-nums; }

/* El recuadro de «en una frase»: la cabecera del capitulo, en una linea. Va aparte de `.aviso`
   porque no avisa de nada: resume. */
.frase { border: 1px solid var(--borde); border-left: 3px solid var(--acento); border-radius: .5rem; padding: .2rem .9rem .6rem; margin: 1rem 0 1.8rem; background: var(--panel); }
.frase p { margin: .5rem 0; font-size: 1.02rem; }
.frase-titulo { font-size: .74rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--tinta-suave); }
.aviso { border: 1px solid var(--borde); border-left-width: 3px; border-radius: .5rem; padding: .2rem .9rem .6rem; margin: 1.4rem 0; background: var(--fondo-suave); }
.aviso p { margin: .5rem 0; }
.aviso-titulo { font-size: .74rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--tinta-suave); }
.aviso.nota { background: var(--nota); border-left-color: var(--acento); }
.aviso.aviso { background: var(--aviso); border-left-color: #b45309; }
.aviso.trampa { background: var(--trampa); border-left-color: #b91c1c; }
.aviso.leccion { background: var(--leccion); border-left-color: #047857; }
.aviso.regla { background: var(--regla); border-left-color: #6d28d9; }
blockquote { margin: 1.2rem 0; padding: .2rem 1rem; border-left: 3px solid var(--borde-fuerte); color: var(--tinta-suave); }
blockquote p { max-width: var(--ancho); }

.paso { display: grid; gap: 1rem; grid-template-columns: 1fr; margin: 3rem 0 1.5rem; }
@media (min-width: 700px) { .paso { grid-template-columns: 1fr 1fr; } }
.paso-caja {
  display: flex; flex-direction: column; gap: .2rem; padding: .9rem 1rem; text-decoration: none;
  border: 1px solid var(--borde); border-radius: .7rem; background: var(--panel);
}
.paso-caja:hover { border-color: var(--acento); background: var(--fondo-suave); }
.paso-caja span { font-size: .76rem; text-transform: uppercase; letter-spacing: .05em; color: var(--tinta-suave); }
.paso-caja strong { color: var(--tinta); font-weight: 600; }
.paso-caja.despues { text-align: right; }
.pie { border-top: 1px solid var(--borde); margin-top: 2rem; padding-top: 1rem; color: var(--tinta-suave); font-size: .84rem; }
.pie p { margin: .3rem 0; }

/* ------------------------------------------------------------------------- portada --- */
.portada { max-width: 60rem; }
.portada h1 { font-size: 2.3rem; line-height: 1.15; letter-spacing: -.02em; margin: .4rem 0 1rem; }
.entrada { font-size: 1.1rem; color: var(--tinta-suave); }
.entrada-meta { color: var(--tinta-suave); font-size: .9rem; }
.como-empezar { background: var(--fondo-suave); border: 1px solid var(--borde); border-radius: .8rem; padding: 1rem 1.4rem 1.4rem; margin: 2rem 0; }
.como-empezar h2 { margin: .2rem 0 .6rem; font-size: 1.1rem; border: 0; padding: 0; }
.bloque { margin: 2.5rem 0; }
.bloque h2 { font-size: 1.2rem; border-top: 1px solid var(--borde); padding-top: 1.2rem; }
.tarjetas { list-style: none; padding: 0; margin: 0; display: grid; gap: .7rem; grid-template-columns: 1fr; }
@media (min-width: 800px) { .tarjetas { grid-template-columns: 1fr 1fr; } }
.tarjetas li a { display: block; padding: .9rem 1rem; border: 1px solid var(--borde); border-radius: .7rem; text-decoration: none; background: var(--panel); }
.tarjetas li a:hover { border-color: var(--acento); background: var(--fondo-suave); }
.tarjetas strong { display: block; color: var(--tinta); margin-bottom: .25rem; }
.tarjetas span { color: var(--tinta-suave); font-size: .9rem; }
.nota { color: var(--tinta-suave); font-size: .92rem; }
.referencia-doc { padding: .8rem 0; border-bottom: 1px solid var(--borde); }
.referencia-doc h3 { margin: 0 0 .2rem; }
.referencia-doc p { margin: .2rem 0; }
.resultados .secs { margin-top: .15rem; }
"""

GUION_BUSCADOR = """// El buscador del material: filtra el indice que va en `indice.js` (al lado, no por red).
// En el navegador y no en un servidor, para que el sitio se pueda abrir con doble clic.
const caja = document.getElementById('buscar');
const lista = document.getElementById('resultados');
const plano = (t) => t.normalize('NFKD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();
const pinta = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function cierra() { lista.hidden = true; caja.setAttribute('aria-expanded', 'false'); }

function busca() {
  const q = plano(caja.value.trim());
  if (q.length < 2) { cierra(); return; }
  const trozos = q.split(/\\s+/);
  const dentro = INDICE.filter((p) => {
    const texto = plano(p.t + ' ' + p.s.join(' ') + ' ' + p.r);
    return trozos.every((t) => texto.includes(t));
  }).slice(0, 30);
  lista.innerHTML = dentro.length
    ? dentro.map((p) =>
        `<li><a href="${p.u}">${pinta(p.t)}</a>` +
        `<span class="tipo">${p.c ? p.sec : 'referencia'}</span>` +
        (p.s.length ? `<div class="secs">${pinta(p.s.slice(0, 3).join(' · '))}</div>` : '')).join('')
    : '<li class="vacio">Nada con esas palabras.</li>';
  lista.hidden = false;
  caja.setAttribute('aria-expanded', 'true');
}

caja.addEventListener('input', busca);
caja.addEventListener('focus', () => { if (caja.value.trim().length >= 2) busca(); });
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') { cierra(); caja.blur(); }
  if (e.key === '/' && document.activeElement !== caja) { e.preventDefault(); caja.focus(); }
});
document.addEventListener('click', (e) => { if (!e.target.closest('.buscador')) cierra(); });
"""

GUION_COPIAR = """// Un boton de copiar en cada bloque de codigo. Es lo primero que hace alguien que viene a
// aprender: copiar el comando y correrlo. En un fichero y no en linea porque el CSP de Caddy
// prohibe los scripts incrustados (`script-src 'self'`).
for (const bloque of document.querySelectorAll('pre')) {
  const boton = document.createElement('button');
  boton.type = 'button';
  boton.className = 'copiar';
  boton.textContent = 'Copiar';
  boton.addEventListener('click', async () => {
    const codigo = bloque.querySelector('code');
    try {
      await navigator.clipboard.writeText(codigo ? codigo.innerText : bloque.innerText);
      boton.textContent = 'Copiado';
      boton.classList.add('hecho');
      setTimeout(() => { boton.textContent = 'Copiar'; boton.classList.remove('hecho'); }, 1500);
    } catch (e) {
      boton.textContent = 'No puedo';
    }
  });
  bloque.appendChild(boton);
}
"""


def genera(salida: Path = SALIDA_POR_DEFECTO) -> int:
    """Escribe el sitio entero. Devuelve cuantas paginas ha hecho (0 si no hay documentos)."""
    try:
        motor = _motor()
    except ImportError:
        print(FALTA_EXTRA)
        return -1

    paginas = recoge()
    if not paginas:
        print("No hay documentos en docs/. Nada que generar.")
        return 0

    _con_anclas(motor)
    por_nombre = {p.ruta.name: p.fichero for p in paginas}
    sin_seccion = sorted(p.slug for p in paginas if p.curso and p.seccion == SIN_SECCION)
    if sin_seccion:
        print(f"  aviso: {len(sin_seccion)} capitulo(s) sin `seccion:` en la cabecera "
              f"-> salen en «{SIN_SECCION}»: {', '.join(sin_seccion)}")
    desconocidas = sorted({p.seccion for p in paginas if p.curso} - set(SECCIONES) - {SIN_SECCION})
    if desconocidas:
        print(f"  aviso: secciones que no estan en SECCIONES: {desconocidas}")

    if salida.exists():
        shutil.rmtree(salida)
    salida.mkdir(parents=True)

    for pagina in paginas:
        crudo = pagina.ruta.read_text(encoding="utf-8")
        _datos, texto = _front_matter(crudo)
        env: dict = {}
        cuerpo = _reescribe_enlaces(motor.render(texto, env), por_nombre)
        pagina.cuerpo = _caja_frase(cuerpo, pagina.en_una_frase)
        pagina.cuerpo = _destaca_avisos(pagina.cuerpo)
        pagina.anclas = [(a["nivel"], a["id"], a["texto"]) for a in env.get("anclas", [])]

    for pagina in paginas:
        (salida / pagina.fichero).write_text(
            CABECERA.format(
                titulo=f"{pagina.titulo} · Cesta, aprender datos",
                descripcion=html.escape(pagina.resumen[:150]),
                lateral=_lateral(paginas, pagina),
                migas=_migas(pagina, paginas),
                cuerpo=f"<article>{pagina.cuerpo}</article>",
                paso=_paso(pagina, paginas),
                toc=_toc(pagina),
                fuente=pagina.ruta.relative_to(RAIZ).as_posix(),
                palabras=f"{pagina.palabras:,}",
            ),
            encoding="utf-8", newline="\n")

    curso = [p for p in paginas if p.curso]
    referencia = [p for p in paginas if not p.curso]
    portada = _portada(paginas)
    (salida / "index.html").write_text(
        CABECERA.format(
            titulo="Aprender datos con un proyecto de verdad · Cesta",
            descripcion="Material de estudio sobre ingenieria de datos, algoritmos, estadistica "
                        "y scraping, con un proyecto real como caso practico.",
            lateral=_lateral(paginas, Pagina(ruta=Path("index.md"), slug="index",
                                             titulo="Portada")),
            migas='<span>Material</span>',
            cuerpo=portada,
            paso="", toc="", fuente="plataforma/aprende.py",
            palabras=f"{sum(p.palabras for p in curso):,}"),
        encoding="utf-8", newline="\n")
    (salida / "referencia.html").write_text(
        CABECERA.format(
            titulo="Referencia · Cesta, aprender datos",
            descripcion="Los documentos de trabajo del proyecto: decisiones, informes y operacion.",
            lateral=_lateral(paginas, Pagina(ruta=Path("referencia.md"), slug="referencia",
                                             titulo="Referencia")),
            migas='<a href="index.html">Material</a> <span>/</span> <span>Referencia</span>',
            cuerpo=f"<article>{_indice_referencia(paginas)}</article>",
            paso='<a class="paso-caja antes" href="index.html"><span>Volver</span>'
                 "<strong>El temario</strong></a>",
            toc="", fuente="docs/*.md", palabras=f"{sum(p.palabras for p in referencia):,}"),
        encoding="utf-8", newline="\n")

    indice = [{"t": p.titulo, "u": p.fichero, "c": p.curso, "sec": p.seccion, "s": p.secciones,
               "r": p.resumen} for p in paginas]
    (salida / "estilo.css").write_text(ESTILO, encoding="utf-8", newline="\n")
    (salida / "indice.js").write_text(
        "// El indice del buscador: una linea por pagina, generada desde los documentos.\n"
        f"const INDICE = {json.dumps(indice, ensure_ascii=False)};\n",
        encoding="utf-8", newline="\n")
    (salida / "buscar.js").write_text(GUION_BUSCADOR, encoding="utf-8", newline="\n")
    (salida / "copiar.js").write_text(GUION_COPIAR, encoding="utf-8", newline="\n")

    print(f"  capitulos del curso   {len(curso):>4}   en {len(SECCIONES)} secciones")
    print(f"  documentos de la ref. {len(referencia):>4}   (+ una pagina de indice)")
    print(f"  palabras del curso    {sum(p.palabras for p in curso):>7,}")
    try:
        donde = salida.relative_to(RAIZ).as_posix()
    except ValueError:
        donde = salida.as_posix()
    print(f"  escrito en            {donde}")
    print(f"  abrelo en            {salida.as_posix()}/index.html")
    return len(paginas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="aprende", description=__doc__.split("\n")[0])
    ap.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO,
                    help="carpeta donde escribir el sitio")
    a = ap.parse_args(argv)
    hechas = genera(a.salida)
    return 1 if hechas < 0 else 0


if __name__ == "__main__":
    sys.exit(main())
