"""La web de aprendizaje: que se genere entera y que no se rompa al crecer.

Son tres clases de comprobacion, y las tres existen por lo mismo: **el sitio no es la
fuente**. La fuente son los documentos de `docs/`, y lo que puede fallar es el conversor:

1. **Que no se pierda nada.** Un documento nuevo tiene que aparecer solo, sin tocar codigo.
   Si hay que anadir una linea para que un capitulo salga, alguien se olvidara.
2. **Que los enlaces no mientan.** Los documentos se enlazan entre si por nombre
   (`docs/BACKLOG.md`); en el sitio son paginas planas, asi que el conversor tiene que
   reescribir esos enlaces. Un enlace roto en un material de estudio es peor que no tenerlo.
3. **Que el markdown de verdad se pinte.** Tablas, bloques de codigo y encabezados con ancla:
   es lo que usan los documentos y lo que hace falta para leerlos.

**Se mira el HTML escrito, no las estructuras de dentro.** La primera version de estas pruebas
miraba los objetos que el conversor deja en memoria, y estaban vacios: `recoge()` devuelve
paginas sin pintar y las pinta `genera()` sobre *otras* que se quedan dentro. Las pruebas
pasaban por el sitio equivocado -- fallaban con el sitio bien y habrian pasado con el sitio
roto. Ahora se lee el fichero que abriria una persona.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from plataforma import aprende

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
CURSO = DOCS / "aprende"


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


def test_lo_que_hay_en_la_carpeta_del_curso_es_del_curso():
    """Guarda de la guarda: si `docs/aprende/` se vacia, estas pruebas no mirarian nada."""
    assert CURSO.exists(), "no existe docs/aprende/"
    capitulos = sorted(CURSO.glob("*.md"))
    assert len(capitulos) >= 5, f"solo hay {len(capitulos)} capitulos: revisa esta prueba"
    for ruta in capitulos:
        texto = ruta.read_text(encoding="utf-8")
        assert texto.startswith("# "), f"{ruta.name} no empieza por un encabezado de nivel 1"


def test_una_pagina_por_documento(sitio):
    """Todos los `.md` de `docs/` (curso y referencia), y ninguno de mas."""
    salida, paginas = sitio
    documentos = {f"{r.stem}.html" for r in [*CURSO.glob("*.md"), *DOCS.glob("*.md")]}
    assert set(paginas) - {"index.html"} == documentos, (
        f"faltan {sorted(documentos - set(paginas))[:5]} o sobran "
        f"{sorted(set(paginas) - documentos - {'index.html'})[:5]}")
    for nombre in paginas:
        texto = _leer(salida, nombre)
        if nombre == "index.html":
            continue
        assert "<title>" in texto and "<h1" in texto, f"{nombre} no tiene titulo"
        assert "Fuente: <code>" in texto, f"{nombre} no dice de que documento sale"


def test_el_curso_va_en_orden_y_la_referencia_detras(sitio):
    """Los capitulos salen en el orden del nombre (`00-`, `01-`, ...), que es el de lectura."""
    salida, _ = sitio
    indice = _leer(salida, "index.html")
    curso = re.findall(r'<li><a href="(\d\d-[^"]+)\.html"', indice)
    assert curso == sorted(curso), f"el curso no esta en orden: {curso}"
    assert curso[0].startswith("00-"), f"el primer capitulo es {curso[0]}"
    assert indice.index("El curso, en orden") < indice.index("La referencia")
    # Y cada capitulo esta tambien dentro de la pagina, para poder saltar de uno a otro.
    for slug in curso:
        texto = _leer(salida, f"{slug}.html")
        assert f'href="{slug}.html"' in texto, f"{slug}.html no se enlaza a si mismo en el menu"


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
            # Las **citas** son enlaces de salida y muchas acaban en `.html` (papers, manuales,
            # documentacion de librerias). Solo se comprueban los enlaces de dentro del sitio.
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
    """Tablas, codigo y encabezados con ancla: lo que usan los documentos."""
    salida, paginas = sitio
    con_tabla = [n for n in paginas if "<table>" in _leer(salida, n)]
    con_codigo = [n for n in paginas if "<pre><code>" in _leer(salida, n)]
    assert len(con_tabla) >= 10, f"solo {len(con_tabla)} paginas con tabla"
    assert len(con_codigo) >= 10, f"solo {len(con_codigo)} paginas con bloque de codigo"
    # Los capitulos llevan ancla en los encabezados, que es lo que usa el indice lateral.
    for nombre in [n for n in paginas if n[:2].isdigit()]:
        texto = _leer(salida, nombre)
        secciones = re.findall(r'<li><a href="#([^"]+)"', texto)
        anclas = re.findall(r'<h2 id="([^"]+)"', texto)
        assert secciones, f"{nombre} no tiene indice lateral"
        for ancla in secciones:
            assert ancla in anclas, f"{nombre}: el indice apunta a #{ancla}, que no existe"


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


def test_el_indice_lleva_el_buscador_dentro(sitio):
    """El buscador va con su indice embebido: asi funciona tambien sin servidor."""
    salida, paginas = sitio
    indice = _leer(salida, "index.html")
    assert "const INDICE = [" in indice, "el buscador no tiene indice embebido"
    assert "addEventListener('input'" in indice, "el buscador no escucha"
    for nombre in paginas:
        if nombre == "index.html":
            continue
        assert f'"{nombre}"' in indice, f"{nombre} no esta en el buscador"


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
