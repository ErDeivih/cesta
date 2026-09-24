"""La web de aprendizaje: convierte los documentos del proyecto en un sitio que se lee.

Por que existe
--------------
Este proyecto lleva **1,1 MB de documentos** escritos a lo largo de varios dias: el registro
del dia a dia (`docs/BACKLOG.md`), los informes (`docs/DIAGNOSTICO-MATCHING.md`,
`docs/LAYA.md`), la operacion (`docs/OPERACION.md`) y las decisiones (`docs/MODELO.md`).
Ese material tiene dos problemas para quien quiere **aprender** con el:

1. **No tiene orden de lectura.** Son sesenta ficheros planos: nadie sabe por donde empezar,
   y lo que explica *como se mide* esta mezclado con lo que explica *que se decidio el martes*.
2. **Vive en markdown dentro del repositorio**, que esta bien para trabajarlo y mal para
   estudiarlo: sin indice navegable, sin buscar, sin volver atras.

Asi que hay dos cosas separadas a proposito:

    docs/aprende/*.md     el **curso**: capitulos en orden, con teoria y con los numeros
                          medidos de este proyecto como caso practico
    docs/*.md             la **referencia**: todo lo demas, tal cual se escribio

Este modulo es el que las junta y las pinta. **No inventa contenido**: convierte markdown en
HTML, reescribe los enlaces entre documentos para que funcionen dentro del sitio, y genera un
indice con buscador. Si un numero esta mal, esta mal en el markdown, que es la unica fuente.

Como se corre
-------------
    uv run --extra docs python -m plataforma.aprende
    uv run --extra docs python -m plataforma.aprende --salida otra/carpeta

Escribe `plataforma/web/aprende/`, y ese sitio:

  - **se abre sin servidor** (doble clic en `index.html`): el buscador lleva su indice
    embebido, no pide nada por red, y no hay ni una fuente de terceros;
  - **o se sirve por Caddy** en `/aprende/` (`plataforma/docker-compose.yml`), que es como
    se lee desde el movil.

Las dos dependencias (`markdown-it-py`, `linkify-it-py`) son **puras de Python**: el scraper
y la API no las necesitan, por eso van en el extra `docs` y aqui se avisa si faltan en vez de
reventar con un `ImportError` de tres lineas.

Lo que este modulo NO hace, y es a proposito
--------------------------------------------
No copia los documentos: **los lee de `docs/`**. Un sitio generado que se queda con una copia
es un sitio que miente a la semana siguiente. Se regenera cuando cambian los documentos, y
`tests/test_aprende.py` comprueba que un documento nuevo aparece sin tocar nada.
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

# El aviso que se da cuando falta el extra, con el comando exacto.
FALTA_EXTRA = (
    "Falta el extra `docs` (markdown-it-py). Se instala con:\n"
    "    uv sync --extra docs\n"
    "y se corre con:\n"
    "    uv run --extra docs python -m plataforma.aprende"
)


@dataclass
class Pagina:
    """Un documento convertido en pagina, con lo que el indice necesita saber de el."""

    ruta: Path
    slug: str
    titulo: str
    curso: bool
    orden: int = 0
    secciones: list[str] = field(default_factory=list)
    # Las anclas que ha puesto el conversor, en orden: `(id, texto)`. Se usan para el indice
    # lateral, y salen de lo que se ha pintado de verdad, no de volver a calcular el slug.
    anclas: list[tuple[str, str]] = field(default_factory=list)
    cuerpo: str = ""
    resumen: str = ""

    @property
    def fichero(self) -> str:
        return f"{self.slug}.html"


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

    `commonmark` es el preset mas aburrido y el que menos sorpresas da, y ademas no trae
    linkify ni plugins: lo unico que se activa de mas son las **tablas** y el tachado, que
    es lo que los documentos usan de verdad. `html=False` (por defecto) es a proposito:
    un `<script>` escrito en un documento se vera como texto y no se ejecutara.
    """
    from markdown_it import MarkdownIt

    md = MarkdownIt("commonmark")
    md.enable(["table", "strikethrough"])
    return md


def _con_anclas(md) -> None:
    """Pone `id` a los encabezados y **apunta los que ha puesto**, para el indice lateral.

    Markdown-it no los pone solo: hay que decirle como. Se hace con una regla de pintado
    sobre `heading_open`, mirando el token siguiente (el texto) para sacar el ancla. El ancla
    se repite si dos encabezados se llaman igual, y se resuelve numerando: en los documentos
    hay mas de un «Lo que falta».

    **Las anclas se guardan en `env`**, y esto no es un detalle: el indice lateral se construia
    volviendo a calcular el ancla a partir del titulo, asi que en cuanto habia dos secciones
    con el mismo nombre el indice apuntaba a `#lo-que-falta` y el encabezado era
    `#lo-que-falta-2`. Un enlace roto en la propia pagina, que solo se ve mirando el HTML.
    Lo encontro `tests/test_aprende.py`.
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
        return f'<{nivel} id="{nombre}">'

    md.renderer.rules["heading_open"] = pinta


def _reescribe_enlaces(cuerpo: str, por_nombre: dict[str, str]) -> str:
    """Cambia los enlaces a `.md` por enlaces a la pagina que les toca.

    Los documentos se enlazan entre si por nombre (`docs/BACKLOG.md`, `MODELO.md`,
    `../docs/API.md`) y el sitio es **plano**: todas las paginas estan en la misma carpeta,
    asi que basta con quedarse con el nombre del fichero. Un enlace a algo que no esta en
    `docs/` se deja como esta -- es una salida honesta a un fichero del repositorio --, y
    el ancla (`#seccion`) se conserva.
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


def _titulo(texto: str, id_por_defecto: str) -> str:
    """El primer encabezado de nivel 1, o el nombre del fichero si no hay."""
    for linea in texto.splitlines():
        if linea.startswith("# "):
            return linea[2:].strip()
    return id_por_defecto


def _resumen(texto: str, limite: int = 240) -> str:
    """El primer parrafo de verdad, sin encabezados ni listas, para el buscador."""
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


def _secciones(texto: str) -> list[str]:
    return [ln.lstrip("# ").strip() for ln in texto.splitlines() if ln.startswith("## ")]


def recoge() -> list[Pagina]:
    """Todas las paginas: primero el curso (en orden), despues la referencia."""
    if not DOCS.exists():
        return []
    paginas: list[Pagina] = []
    for numero, ruta in enumerate(sorted(CURSO.glob("*.md")) if CURSO.exists() else []):
        texto = ruta.read_text(encoding="utf-8")
        # El nombre del fichero manda para el orden (`00-`, `01-`, ...) y para el ancla.
        nombre = ruta.stem
        paginas.append(Pagina(ruta=ruta, slug=nombre, titulo=_titulo(texto, nombre),
                              curso=True, orden=numero, secciones=_secciones(texto),
                              resumen=_resumen(texto)))
    for ruta in sorted(DOCS.glob("*.md")):
        texto = ruta.read_text(encoding="utf-8")
        paginas.append(Pagina(ruta=ruta, slug=ruta.stem, titulo=_titulo(texto, ruta.stem),
                              curso=False, secciones=_secciones(texto),
                              resumen=_resumen(texto)))
    return paginas


PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo} · Cesta, aprender datos con un proyecto de verdad</title>
<meta name="color-scheme" content="light dark">
<link rel="stylesheet" href="estilo.css">
</head>
<body>
<header class="barra">
  <a class="marca" href="index.html">Cesta · aprender datos</a>
  <nav class="menu" aria-label="Secciones">
    <a href="index.html">Temario</a>
    {menu}
  </nav>
</header>
<div class="marco">
  <aside class="lateral">
    {indice_lateral}
  </aside>
  <main>
    <article>{cuerpo}</article>
    <nav class="paso" aria-label="Capitulos">
      {paso}
    </nav>
    <footer class="pie">
      Fuente: <code>{fuente}</code> · generado por <code>plataforma/aprende.py</code>
      (no se edita a mano: se cambia el documento y se vuelve a generar)
    </footer>
  </main>
</div>
</body>
</html>
"""

PLANTILLA_INDICE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aprender datos con un proyecto de verdad · Cesta</title>
<meta name="color-scheme" content="light dark">
<link rel="stylesheet" href="estilo.css">
</head>
<body>
<header class="barra">
  <a class="marca" href="index.html">Cesta · aprender datos</a>
</header>
<div class="marco">
  <main class="ancho">
    <h1>Aprender datos con un proyecto de verdad</h1>
    <p class="entrada">
      Esto no es la documentacion de una aplicacion: es el <strong>material de un curso</strong>
      que usa un proyecto real -- comparar los precios de cinco supermercados espanoles,
      todos los dias, en un PC de casa -- como caso practico. Cada numero que sale aqui esta
      <strong>medido</strong>, y cada afirmacion trae el comando que la reproduce.
    </p>
    <input id="buscar" type="search" placeholder="Buscar en todo el material…"
           aria-label="Buscar en todo el material" autocomplete="off">
    <ul id="resultados" class="resultados" hidden></ul>

    <h2 id="curso">El curso, en orden</h2>
    <p class="nota">Los capitulos de <code>docs/aprende/</code>. Se leen de arriba abajo:
    cada uno da la teoria y despues la ensena con lo que este proyecto mide de verdad.</p>
    <ol class="temario">
      {curso}
    </ol>

    <h2 id="referencia">La referencia</h2>
    <p class="nota">Todo lo demas que se ha escrito en este proyecto: las decisiones, los
    informes, la operacion y el registro del dia a dia. No es un curso; es donde se comprueba
    de donde sale cada cosa.</p>
    <ul class="temario ref">
      {referencia}
    </ul>
    <!-- **Nada de scripts en linea**: Caddy sirve esto con `script-src 'self'`, asi que un
         `<script>` incrustado no se ejecuta y el buscador se queda muerto sin dar ningun
         error visible. Paso al desplegarlo (lo caza `plataforma/prueba_produccion.py`) y por
         eso el indice y el codigo van en ficheros aparte. -->
    <script src="indice.js" defer></script>
    <script src="buscar.js" defer></script>
  </main>
</div>
</body>
</html>
"""

GUION_BUSCADOR = """// El buscador del material: filtra el indice que va en `indice.js` (al lado, no por red).
// Filtrar en el navegador y no en un servidor es lo que hace que el sitio se pueda abrir con
// doble clic, sin levantar nada, y que la busqueda sea instantanea.
const caja = document.getElementById('buscar');
const lista = document.getElementById('resultados');
const plano = (t) => t.normalize('NFKD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();
caja.addEventListener('input', () => {
  const q = plano(caja.value.trim());
  lista.innerHTML = '';
  if (q.length < 2) { lista.hidden = true; return; }
  const trozos = q.split(/\\s+/);
  const dentro = INDICE.filter((p) => {
    const texto = plano(p.t + ' ' + p.s.join(' ') + ' ' + p.r);
    return trozos.every((t) => texto.includes(t));
  }).slice(0, 40);
  if (!dentro.length) {
    lista.innerHTML = '<li class="vacio">Nada con esas palabras.</li>';
    lista.hidden = false;
    return;
  }
  lista.innerHTML = dentro.map((p) =>
    `<li><a href="${p.u}">${p.t}</a> <span class="tipo">${p.c ? 'curso' : 'referencia'}</span>` +
    (p.s.length ? `<div class="secs">${p.s.slice(0, 4).join(' · ')}</div>` : '')).join('');
  lista.hidden = false;
});
"""

ESTILO = """/* Los colores del proyecto, en variables: los mismos nombres que usa la aplicacion
   (`plataforma/web/app/src/estilos.css`), para que el material y la aplicacion se lean
   igual. Claro y oscuro por `prefers-color-scheme`, sin interruptor: el sistema ya lo sabe. */
:root {
  --fondo: #f7f7f8; --panel: #ffffff; --tinta: #16181b; --tinta-suave: #5b6169;
  --borde: #e2e4e8; --acento: #0369a1; --acento-suave: #e0f2fe;
  --codigo: #f2f3f5; --cita: #f8fafc;
}
@media (prefers-color-scheme: dark) {
  :root {
    --fondo: #141618; --panel: #1c1f22; --tinta: #ecedee; --tinta-suave: #a5abb3;
    --borde: #2c3035; --acento: #7dd3fc; --acento-suave: #0c2a3d;
    --codigo: #22262a; --cita: #1a1e22;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--fondo); color: var(--tinta);
  font: 16px/1.65 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
.barra {
  position: sticky; top: 0; z-index: 10; display: flex; flex-wrap: wrap; gap: .25rem 1rem;
  align-items: baseline; padding: .5rem 1rem; background: var(--panel);
  border-bottom: 1px solid var(--borde);
}
.marca { font-weight: 700; text-decoration: none; color: var(--tinta); }
.menu a { color: var(--tinta-suave); text-decoration: none; font-size: .9rem; }
.menu a:hover { color: var(--acento); }
.marco { display: grid; grid-template-columns: 1fr; gap: 1rem; max-width: 1180px; margin: 0 auto; padding: 1rem; }
@media (min-width: 1000px) { .marco { grid-template-columns: 15rem 1fr; } }
main { background: var(--panel); border: 1px solid var(--borde); border-radius: .75rem; padding: 1.25rem 1.25rem 2rem; }
.ancho { grid-column: 1 / -1; }
article h1 { font-size: 1.6rem; line-height: 1.25; margin: .2rem 0 1rem; }
article h2 { font-size: 1.2rem; margin: 2rem 0 .6rem; padding-top: .4rem; border-top: 1px solid var(--borde); }
article h3 { font-size: 1.02rem; margin: 1.4rem 0 .4rem; }
article p, article li { max-width: 72ch; }
a { color: var(--acento); }
code { background: var(--codigo); padding: .1rem .3rem; border-radius: .25rem; font-size: .92em; }
pre { background: var(--codigo); padding: .75rem 1rem; border-radius: .5rem; overflow-x: auto; }
pre code { background: none; padding: 0; font-size: .86rem; line-height: 1.45; }
blockquote { margin: 1rem 0; padding: .5rem 1rem; border-left: 3px solid var(--acento); background: var(--cita); color: var(--tinta-suave); }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: .92rem; display: block; overflow-x: auto; }
th, td { border: 1px solid var(--borde); padding: .35rem .6rem; text-align: left; vertical-align: top; }
th { background: var(--cita); }
/* Los numeros, con cifras de ancho fijo: en las tablas de este material se comparan
   columnas de precios y porcentajes, y con cifras proporcionales no se alinean. */
td.num, .cifra { font-variant-numeric: tabular-nums; }
.lateral { font-size: .92rem; }
.lateral nav { position: sticky; top: 3.2rem; background: var(--panel); border: 1px solid var(--borde); border-radius: .75rem; padding: .75rem 1rem; max-height: calc(100vh - 4rem); overflow-y: auto; }
.lateral h2 { font-size: .8rem; text-transform: uppercase; letter-spacing: .04em; color: var(--tinta-suave); margin: .2rem 0 .5rem; }
.lateral ol { margin: 0; padding-left: 1.1rem; }
.lateral li { margin: .2rem 0; }
.lateral a { text-decoration: none; }
.lateral a[aria-current="page"] { font-weight: 700; color: var(--tinta); }
.paso { display: flex; justify-content: space-between; gap: 1rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--borde); font-size: .95rem; }
.pie { margin-top: 1.5rem; color: var(--tinta-suave); font-size: .82rem; }
.entrada { font-size: 1.05rem; color: var(--tinta-suave); max-width: 70ch; }
.nota { color: var(--tinta-suave); font-size: .92rem; }
input[type=search] { width: 100%; max-width: 40rem; padding: .6rem .8rem; font-size: 1rem; margin: .5rem 0 1rem;
  border: 1px solid var(--borde); border-radius: .5rem; background: var(--panel); color: var(--tinta); }
.resultados { list-style: none; padding: 0; margin: 0 0 1.5rem; border: 1px solid var(--borde); border-radius: .5rem; }
.resultados li { padding: .5rem .75rem; border-bottom: 1px solid var(--borde); }
.resultados li:last-child { border-bottom: 0; }
.resultados a { text-decoration: none; font-weight: 600; }
.resultados .tipo { color: var(--tinta-suave); font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; }
.resultados .secs, .resultados .vacio { color: var(--tinta-suave); font-size: .84rem; }
.temario { padding-left: 1.2rem; }
.temario li { margin: .35rem 0; }
.temario .resumen { display: block; color: var(--tinta-suave); font-size: .88rem; }
"""


def _indice_lateral(pagina: Pagina, paginas: list[Pagina]) -> str:
    """El indice de la izquierda: el capitulo de ahora y todos los demas del curso."""
    filas: list[str] = []
    if pagina.anclas:
        filas.append("<h2>En este capitulo</h2><ol>")
        for ancla, texto in pagina.anclas:
            filas.append(f'<li><a href="#{ancla}">{html.escape(texto)}</a></li>')
        filas.append("</ol>")
    curso = [p for p in paginas if p.curso]
    if len(curso) > 1:
        filas.append("<h2>El curso</h2><ol>")
        for otra in curso:
            actual = ' aria-current="page"' if otra.slug == pagina.slug else ""
            filas.append(f'<li><a href="{otra.fichero}"{actual}>{html.escape(otra.titulo)}</a></li>')
        filas.append("</ol>")
    filas.append('<h2>Referencia</h2><p><a href="index.html#referencia">'
                 "Los documentos del proyecto</a></p>")
    return "<nav>" + "".join(filas) + "</nav>"


def _paso(pagina: Pagina, paginas: list[Pagina]) -> str:
    """Los enlaces de «anterior» y «siguiente», solo dentro del curso."""
    curso = [p for p in paginas if p.curso]
    if pagina not in curso:
        return '<a href="index.html">Volver al temario</a><span></span>'
    i = curso.index(pagina)
    antes = (f'<a href="{curso[i - 1].fichero}">← {html.escape(curso[i - 1].titulo)}</a>'
             if i else '<a href="index.html">Temario</a>')
    despues = (f'<a href="{curso[i + 1].fichero}">{html.escape(curso[i + 1].titulo)} →</a>'
               if i + 1 < len(curso) else '<a href="index.html#referencia">La referencia →</a>')
    return antes + despues


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

    if salida.exists():
        shutil.rmtree(salida)
    salida.mkdir(parents=True)

    for pagina in paginas:
        texto = pagina.ruta.read_text(encoding="utf-8")
        env: dict = {}
        cuerpo = _reescribe_enlaces(motor.render(texto, env), por_nombre)
        pagina.cuerpo = cuerpo
        pagina.secciones = _secciones(texto)
        # Solo los de nivel 2 van al indice lateral: los de nivel 3 son demasiado finos y
        # el indice deja de caber en un movil.
        pagina.anclas = [(a["id"], a["texto"]) for a in env.get("anclas", [])
                         if a["nivel"] == "h2"]

    for pagina in paginas:
        curso = [p for p in paginas if p.curso]
        menu = "".join(f'<a href="{p.fichero}">{i + 1}. {html.escape(p.titulo)}</a> '
                       for i, p in enumerate(curso[:4]))
        (salida / pagina.fichero).write_text(
            PLANTILLA.format(
                titulo=html.escape(pagina.titulo),
                menu=menu,
                indice_lateral=_indice_lateral(pagina, paginas),
                cuerpo=pagina.cuerpo,
                paso=_paso(pagina, paginas),
                fuente=pagina.ruta.relative_to(RAIZ).as_posix(),
            ),
            encoding="utf-8", newline="\n")

    curso = [p for p in paginas if p.curso]
    referencia = [p for p in paginas if not p.curso]
    indice = [{"t": p.titulo, "u": p.fichero, "c": p.curso, "s": p.secciones,
               "r": p.resumen} for p in paginas]
    (salida / "index.html").write_text(
        PLANTILLA_INDICE.format(
            curso="".join(
                f'<li><a href="{p.fichero}">{html.escape(p.titulo)}</a>'
                f'<span class="resumen">{html.escape(p.resumen)}</span></li>'
                for p in curso),
            referencia="".join(
                f'<li><a href="{p.fichero}">{html.escape(p.titulo)}</a>'
                f'<span class="resumen">{html.escape(p.resumen)}</span></li>'
                for p in referencia),
        ),
        encoding="utf-8", newline="\n")
    (salida / "estilo.css").write_text(ESTILO, encoding="utf-8", newline="\n")
    # El indice y el buscador, en ficheros aparte: con `script-src 'self'` (el CSP de Caddy)
    # un script en linea NO se ejecuta, y el buscador se quedaria muerto sin avisar.
    (salida / "indice.js").write_text(
        "// El indice del buscador: una linea por pagina, generada desde los documentos.\n"
        f"const INDICE = {json.dumps(indice, ensure_ascii=False)};\n",
        encoding="utf-8", newline="\n")
    (salida / "buscar.js").write_text(GUION_BUSCADOR, encoding="utf-8", newline="\n")

    print(f"  capitulos del curso   {len(curso):>4}")
    print(f"  documentos de la ref. {len(referencia):>4}")
    # `--salida` puede apuntar fuera del repositorio (una prueba, una copia temporal), y
    # entonces `relative_to` revienta: se enseña la ruta entera y ya esta.
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
