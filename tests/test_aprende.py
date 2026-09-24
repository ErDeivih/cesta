"""La web de aprendizaje: que se genere entera y que no se rompa al crecer.

Son tres clases de comprobacion, y las tres existen por lo mismo: **el sitio no es la
fuente**. La fuente son los documentos de `docs/`, y lo que puede fallar es el conversor:

1. **Que no se pierda nada.** Un capitulo nuevo tiene que aparecer solo --en su seccion, en el
   indice y en el buscador-- sin tocar codigo. Si hay que anadir una linea para que salga,
   alguien se olvidara.
2. **Que los enlaces no mientan.** Los documentos se enlazan entre si por nombre
   (`docs/BACKLOG.md`); en el sitio son paginas planas, asi que el conversor tiene que
   reescribir esos enlaces. Un enlace roto en un material de estudio es peor que no tenerlo.
3. **Que el markdown de verdad se pinte**, y con la forma de un sitio de documentacion:
   secciones en el indice lateral, indice de la pagina, avisos destacados, boton de copiar.

**Se mira el HTML escrito, no las estructuras de dentro.** La primera version de estas pruebas
miraba los objetos que el conversor deja en memoria, y estaban vacios: `recoge()` devuelve
paginas sin pintar y las pinta `genera()` sobre *otras* que se quedan dentro. Las pruebas
pasaban por el sitio equivocado -- fallaban con el sitio bien y habrian pasado con el sitio
roto. Ahora se lee el fichero que abriria una persona.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

import pytest

from plataforma import aprende

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
CURSO = DOCS / "aprende"

# Las paginas que no salen de un documento: el temario y el indice de la referencia.
EXTRA = {"index.html", "referencia.html"}


@pytest.fixture(scope="module")
def sitio(tmp_path_factory) -> tuple[Path, list[str]]:
    """El sitio generado una vez para todas las pruebas de este fichero."""
    pytest.importorskip("markdown_it", reason="falta el extra `docs`")
    salida = tmp_path_factory.mktemp("aprende")
    assert aprende.genera(salida) > 0, "no ha generado ninguna pagina"
    paginas = sorted(p.name for p in salida.glob("*.html"))
    return salida, paginas


def _leer(salida: Path, nombre: str) -> str:
    return (salida / nombre).read_text(encoding="utf-8")


def _sin_front_matter(texto: str) -> str:
    if texto.startswith("---"):
        fin = texto.find("\n---", 3)
        if fin != -1:
            return texto[fin + 4:].lstrip("\n")
    return texto


def test_lo_que_hay_en_la_carpeta_del_curso_es_del_curso():
    """Guarda de la guarda: si `docs/aprende/` se vacia, estas pruebas no mirarian nada."""
    assert CURSO.exists(), "no existe docs/aprende/"
    capitulos = sorted(CURSO.glob("*.md"))
    assert len(capitulos) >= 10, f"solo hay {len(capitulos)} capitulos: revisa esta prueba"
    for ruta in capitulos:
        texto = ruta.read_text(encoding="utf-8")
        assert texto.startswith("# ") or texto.startswith("---"), (
            f"{ruta.name} no empieza ni por la cabecera ni por un titulo de nivel 1")
        assert _sin_front_matter(texto).startswith("# "), (
            f"{ruta.name} no tiene titulo de nivel 1 despues de la cabecera")


def test_cada_capitulo_declara_una_seccion_conocida():
    """La cabecera es lo que coloca el capitulo en el temario: sin ella, no aparece bien."""
    for ruta in sorted(CURSO.glob("*.md")):
        datos, _ = aprende._front_matter(ruta.read_text(encoding="utf-8"))
        seccion = datos.get("seccion")
        assert seccion, f"{ruta.name} no declara `seccion:` en su cabecera"
        assert seccion in aprende.SECCIONES, (
            f"{ruta.name} declara la seccion {seccion!r}, que no esta en `SECCIONES`: "
            f"saldria en «{aprende.SIN_SECCION}»")


def test_cada_capitulo_lleva_su_frase_en_una_frase(sitio):
    """La idea del capitulo, en un recuadro y debajo del titulo.

    Existe por legibilidad: alguien llega desde el movil o con prisa, lee esa linea y decide si
    sigue. Por eso se vigila: si un capitulo se escribe sin ella, el recuadro desaparece **sin
    que nada avise**, y una pagina sin resumen se lee peor que una con resumen malo. La frase
    sale de la cabecera del documento (no del texto) para que no se pueda quedar desfasada.
    """
    salida, _ = sitio
    faltan: list[str] = []
    for ruta in sorted(CURSO.glob("*.md")):
        datos, _texto = aprende._front_matter(ruta.read_text(encoding="utf-8"))
        frase = datos.get("en_una_frase", "")
        if not frase:
            faltan.append(ruta.name)
            continue
        assert len(frase) <= 200, (
            f"{ruta.name}: la frase tiene {len(frase)} caracteres, y es para leerla de un tiron")
        pagina = _leer(salida, f"{ruta.stem}.html")
        assert 'class="frase"' in pagina, f"{ruta.name}: la frase no se pinta"
        # Debajo del titulo y **antes** del primer apartado: es lo primero que se lee.
        assert pagina.index("</h1>") < pagina.index('class="frase"') < pagina.index("<h2"), (
            f"{ruta.name}: el recuadro de la frase no esta debajo del titulo")
        assert html.escape(frase) in pagina, f"{ruta.name}: la frase no sale tal cual"
    assert not faltan, f"capitulos sin `en_una_frase:` en la cabecera: {faltan}"
    # Los documentos de la referencia no llevan cabecera de curso: no se les pone recuadro.
    for nombre in ("BACKLOG.html", "OPERACION.html"):
        if (salida / nombre).exists():
            assert 'class="frase"' not in _leer(salida, nombre), (
                f"{nombre} es de la referencia y no deberia llevar el recuadro del curso")


def test_una_pagina_por_documento_y_las_dos_de_estructura(sitio):
    """Todos los `.md` de `docs/` (curso y referencia), mas el temario y el indice."""
    salida, paginas = sitio
    documentos = {f"{r.stem}.html" for r in [*CURSO.glob("*.md"), *DOCS.glob("*.md")]}
    assert set(paginas) - EXTRA == documentos, (
        f"faltan {sorted(documentos - set(paginas))[:5]} o sobran "
        f"{sorted(set(paginas) - documentos - EXTRA)[:5]}")
    for nombre in paginas:
        if nombre in EXTRA:
            continue
        texto = _leer(salida, nombre)
        assert "<title>" in texto and "<h1" in texto, f"{nombre} no tiene titulo"
        assert "Fuente: <code>" in texto, f"{nombre} no dice de que documento sale"


def test_el_temario_agrupa_por_secciones_y_en_orden(sitio):
    """El indice lateral y la portada siguen el temario: secciones y capitulos en orden."""
    salida, _ = sitio
    portada = _leer(salida, "index.html")
    # Las secciones salen en el orden de `SECCIONES`, no en el alfabetico.
    vistas = [s for s in aprende.SECCIONES if f'id="{aprende.slug_de(s)}"' in portada]
    assert len(vistas) >= 5, f"solo {len(vistas)} secciones en la portada"
    posiciones = [portada.index(f'id="{aprende.slug_de(s)}"') for s in vistas]
    assert posiciones == sorted(posiciones), "las secciones no salen en el orden del temario"
    # Y en el indice lateral de cualquier pagina estan todas.
    lateral = _leer(salida, "04-emparejar-productos.html")
    for seccion in vistas:
        assert f'<p class="nav-seccion">{seccion}</p>' in lateral, (
            f"{seccion!r} no sale en el indice lateral")
    # Un capitulo, en su seccion, con su enlace.
    assert 'aria-current="page"' in lateral, "no se marca el capitulo en el que estas"


def test_cada_capitulo_lleva_su_indice_de_pagina(sitio):
    """El indice de la derecha apunta a los encabezados que de verdad se han pintado."""
    salida, paginas = sitio
    for nombre in [n for n in paginas if n[:2].isdigit()]:
        texto = _leer(salida, nombre)
        anclas = set(re.findall(r'<h[23] id="([^"]+)"', texto))
        assert anclas, f"{nombre} no tiene encabezados con ancla"
        toc = re.search(r'<aside class="toc">(.*?)</aside>', texto, re.S)
        assert toc, f"{nombre} no tiene indice de pagina"
        for destino in re.findall(r'href="#([^"]+)"', toc.group(1)):
            assert destino in anclas, (
                f"{nombre}: el indice de la pagina apunta a #{destino}, que no existe")


def test_los_enlaces_entre_documentos_apuntan_a_las_paginas(sitio):
    """Un enlace a `algo.md` **que exista en `docs/`** sale como `algo.html`, y funciona.

    Los enlaces a markdown que no estan en `docs/` se dejan como estan a proposito: son
    punteros honestos a un fichero del repositorio, y convertirlos en un 404 seria peor. Lo
    que no puede quedar es un enlace a un documento que **si** esta y no se ha convertido.
    """
    salida, paginas = sitio
    existentes = set(paginas)
    conocidos = {r.name for r in [*CURSO.glob("*.md"), *DOCS.glob("*.md")]}
    rotos: list[str] = []
    quedan_md: list[str] = []
    for nombre in paginas:
        texto = _leer(salida, nombre)
        for destino in re.findall(r'href="([^"]+\.html)"', texto):
            # Las **citas** son enlaces de salida y muchas acaban en `.html` (papers,
            # manuales, documentacion de librerias). Solo se miran los de dentro.
            if "://" in destino:
                continue
            if destino not in existentes:
                rotos.append(f"{nombre} -> {destino}")
        for resto in re.findall(r'href="([^"]+\.md)"', texto):
            if Path(resto).name in conocidos:
                quedan_md.append(f"{nombre} -> {resto}")
    assert not rotos, f"enlaces a paginas que no existen: {rotos[:5]}"
    assert not quedan_md, f"documentos que si existen y no se han convertido: {quedan_md[:5]}"


def test_el_markdown_de_verdad_se_pinta(sitio):
    """Tablas, codigo, avisos destacados y boton de copiar: lo que hace legible el material."""
    salida, paginas = sitio
    con_tabla = [n for n in paginas if "<table>" in _leer(salida, n)]
    con_codigo = [n for n in paginas if "<pre><code>" in _leer(salida, n)]
    assert len(con_tabla) >= 10, f"solo {len(con_tabla)} paginas con tabla"
    assert len(con_codigo) >= 10, f"solo {len(con_codigo)} paginas con bloque de codigo"
    # Los avisos (`> **Leccion:** …`) salen con su clase, y hay unos cuantos repartidos.
    avisos = [n for n in paginas if 'class="aviso ' in _leer(salida, n)]
    assert len(avisos) >= 4, f"solo {len(avisos)} paginas con avisos destacados"
    # Y el boton de copiar se pone desde un fichero, no en linea.
    assert "document.querySelectorAll('pre')" in _leer(salida, "copiar.js"), (
        "copiar.js no esta buscando los bloques de codigo")


def test_el_sitio_no_pide_nada_por_red(sitio):
    """Se tiene que poder abrir con doble clic: ni fuentes, ni CDN, ni imagenes de fuera.

    Las **citas** a fuentes externas son otra cosa: el material cita papers y manuales, y un
    enlace de salida no rompe nada. Lo que no puede haber es un recurso que el navegador tenga
    que ir a buscar para que la pagina se vea.
    """
    salida, paginas = sitio
    assert (salida / "estilo.css").exists(), "falta la hoja de estilo"
    for nombre in paginas:
        texto = _leer(salida, nombre)
        assert 'href="estilo.css"' in texto, f"{nombre} no carga el estilo"
        for patron in (r'src="https?://', r'<link[^>]+href="https?://', r'@import'):
            assert not re.search(patron, texto), (
                f"{nombre} carga un recurso de fuera ({patron}): el sitio tiene que verse sin red")


def test_nada_en_linea_porque_el_csp_de_caddy_lo_prohibe(sitio):
    """El buscador funcionaba en local y estaba muerto en produccion por esto.

    Caddy sirve el material con `script-src 'self'` y `style-src 'self'`: un `<script>` o un
    `<style>` incrustado **no se ejecuta**, y no da ningun error visible. Se descubrio al
    desplegarlo, y lo caza `plataforma/prueba_produccion.py`; aqui se vigila que el generador
    no vuelva a escribirlo.
    """
    salida, paginas = sitio
    for nombre in paginas:
        texto = _leer(salida, nombre)
        # Los comentarios se quitan antes de mirar: un `<script>` **dentro de un comentario** no
        # se ejecuta, y el primero que salto fue justo eso -- el comentario que explica esta
        # regla. Es la misma trampa que ya tuvo `test_interfaz.py` con las palabras prohibidas.
        sin_comentarios = re.sub(r"<!--.*?-->", " ", texto, flags=re.S)
        en_linea = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", sin_comentarios)
        assert not en_linea, f"{nombre} lleva un script en linea: el CSP no lo dejaria correr"
        assert not re.search(r"<style[\s>]", sin_comentarios), (
            f"{nombre} lleva un estilo en linea: el CSP no lo aplicaria")


def test_el_buscador_va_en_ficheros_y_lleva_todo_dentro(sitio):
    """El buscador funciona sin servidor: su indice va en un fichero de al lado."""
    salida, paginas = sitio
    for nombre in paginas:
        texto = _leer(salida, nombre)
        assert 'src="indice.js"' in texto and 'src="buscar.js"' in texto, (
            f"{nombre} no carga el buscador desde ficheros")
    assert "addEventListener('input'" in _leer(salida, "buscar.js"), "el buscador no escucha"
    datos = _leer(salida, "indice.js")
    assert datos.startswith("//") and "const INDICE = [" in datos, "el indice no es un fichero"
    for nombre in paginas:
        if nombre in EXTRA:
            continue
        assert f'"{nombre}"' in datos, f"{nombre} no esta en el indice del buscador"


def test_la_referencia_tiene_su_pagina_de_indice(sitio):
    """Los 60 documentos no caben en el indice lateral: van en su propia pagina, con resumen."""
    salida, _ = sitio
    texto = _leer(salida, "referencia.html")
    documentos = [p for p in DOCS.glob("*.md")]
    assert 'class="referencia-doc"' in texto, "la referencia no lista los documentos"
    for ruta in documentos:
        assert f'href="{ruta.stem}.html"' in texto, f"{ruta.name} no sale en la referencia"


def test_el_sitio_esta_montado_donde_el_servidor_lo_busca():
    """El generador escribe `plataforma/web/aprende`; el servidor tiene que servir eso.

    Es la misma clase de prueba que `test_interfaz.py` hace para la aplicacion: el fallo no
    esta en el codigo, esta en dos ficheros de configuracion que tienen que decir lo mismo. Y
    aqui ya paso una: el primer montaje fue `/srv/aprende`, **anidado dentro de `/srv`**, que
    esta montado de solo lectura; Docker no puede crear el punto de montaje y el contenedor
    **no arranca**. Se ve en `docker compose ps`, no en el codigo.
    """
    compose = (RAIZ / "plataforma" / "docker-compose.yml").read_text(encoding="utf-8")
    caddy = (RAIZ / "plataforma" / "Caddyfile").read_text(encoding="utf-8")
    # Solo las lineas de montaje: el fichero **cuenta** el intento fallido en un comentario, y
    # buscar el texto a secas marcaba esa explicacion (el mismo error que ya tuvo
    # `test_interfaz.py`, que tenia que quitar los comentarios antes de mirar).
    montajes = [ln.strip() for ln in compose.splitlines()
                if ln.strip().startswith("- ./web/") or ln.strip().startswith("- ${")]
    assert any(m == "- ./web/aprende:/aprende:ro" for m in montajes), (
        f"docker-compose ya no monta el material de aprendizaje en `/aprende`: {montajes}")
    assert not any(m.endswith(":/srv/aprende:ro") for m in montajes), (
        f"el material se monta dentro de `/srv`, que es de solo lectura: el contenedor no "
        f"arrancaria (read-only file system) -- {montajes}")
    assert "handle_path /aprende/*" in caddy and "root * /aprende" in caddy, (
        "Caddy no sirve `/aprende`: el material estaria generado pero nadie lo veria")
    assert aprende.SALIDA_POR_DEFECTO == RAIZ / "plataforma" / "web" / "aprende", (
        "el generador escribe en otro sitio del que se monta")
