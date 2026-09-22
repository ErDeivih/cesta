"""La interfaz nueva: que el sitio donde compila y el sitio que se sirve sean el mismo.

Es la misma clase de prueba que `test_imagen_api.py`, y por el mismo motivo: el
fallo no esta en el codigo, esta en dos ficheros de configuracion que tienen que
decir lo mismo y que nadie compara.

Aqui el fallo concreto es facil de cometer y dificil de ver: Vite compila a
`plataforma/web/dist` y Caddy sirve lo que le monte docker-compose en `/srv`. Si
los dos lados se separan -- se cambia `outDir`, o se deja el montaje antiguo de
`./web` --, la aplicacion **no da error**: Caddy sirve un `index.html` que existe,
el navegador carga, y lo que sale es la interfaz vieja. O una pagina en blanco,
segun el dia. Sin un error por ningun lado.

Esto no ejecuta npm ni levanta Docker: lee los tres ficheros y comprueba que
dicen lo mismo. Tarda milisegundos.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
WEB = RAIZ / "plataforma" / "web"
APP = WEB / "app"
VITE = APP / "vite.config.ts"
COMPOSE = RAIZ / "plataforma" / "docker-compose.yml"
CADDY = RAIZ / "plataforma" / "Caddyfile"


def _out_dir() -> str | None:
    """El `build.outDir` de Vite, tal cual, sin resolverlo."""
    if not VITE.exists():
        return None
    m = re.search(r"outDir:\s*['\"]([^'\"]+)['\"]", VITE.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def _montaje_de_la_web() -> str | None:
    """La linea de docker-compose que monta la interfaz en la web."""
    if not COMPOSE.exists():
        return None
    for linea in COMPOSE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*-\s*(\S+/web[^:]*):/srv:ro", linea)
        if m:
            return m.group(1)
    return None


@pytest.mark.skipif(not VITE.exists(), reason="esta copia no trae la interfaz nueva")
def test_vite_compila_al_sitio_que_ensena_el_readme():
    """`outDir` es `../dist`, o sea `plataforma/web/dist`."""
    assert _out_dir() == "../dist"


@pytest.mark.skipif(not COMPOSE.exists(), reason="no hay docker-compose en esta copia")
def test_docker_compose_sirve_lo_que_vite_compila():
    """La comprobacion que evita servir la interfaz vieja sin que nadie se entere."""
    montaje = _montaje_de_la_web()
    assert montaje is not None, (
        "docker-compose ya no monta ninguna carpeta de `web` en /srv: Caddy no "
        "tendria que servir.")
    assert montaje.endswith("web/dist"), (
        f"docker-compose monta `{montaje}` en /srv, pero Vite compila a "
        f"`web/dist`. Caddy serviria la interfaz vieja (o una pagina en blanco) "
        f"sin dar ningun error.")


def test_la_interfaz_vieja_sigue_ahi():
    """No se borra hasta que la nueva tenga paridad: es el plan B, y es una linea."""
    if not APP.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    assert (WEB / "index.html").exists()
    assert (WEB / "app.js").exists()


def test_caddy_sirve_una_sola_pagina_y_manda_la_api_al_backend():
    """El `try_files` es lo que hace falta para una aplicacion de una sola pagina."""
    if not CADDY.exists():
        pytest.skip("no hay Caddyfile en esta copia")
    texto = CADDY.read_text(encoding="utf-8")
    assert "try_files {path} /index.html" in texto
    assert "reverse_proxy api:8000" in texto


def _sin_comentarios(texto: str) -> str:
    """Quita los comentarios de bloque y las lineas que son comentario entero.

    Hace falta porque la primera version de estas pruebas fallaba con el codigo
    BIEN: la interfaz dice en varios sitios "aqui no hay ningun boton de aprobar
    ni de rechazar", que es la regla escrita, y buscar la palabra a pelo la
    encontraba. No se quitan los `//` de dentro de una linea a proposito: eso
    romperia `http://localhost:8000`, que es justo lo que hay que detectar.
    """
    sin_bloques = re.sub(r"/\*.*?\*/", " ", texto, flags=re.S)
    return "\n".join(ln for ln in sin_bloques.splitlines()
                     if not ln.strip().startswith("//"))


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_la_interfaz_pide_la_api_por_rutas_relativas():
    """Un solo origen: nada de `http://localhost:8000`, que rompe Tailscale y CORS."""
    sospechosas = []
    for fichero in list((APP / "src").rglob("*.ts")) + list((APP / "src").rglob("*.tsx")):
        limpio = _sin_comentarios(fichero.read_text(encoding="utf-8"))
        for mal in ("localhost:8000", "127.0.0.1:8000"):
            if mal in limpio:
                sospechosas.append(f"{fichero.name}: {mal}")
    assert not sospechosas, (
        f"la interfaz llama a la API por direccion absoluta ({sospechosas}). "
        f"Tiene que ser por rutas relativas `/api/...`: Caddy manda /api al "
        f"backend en el mismo origen. El proxy de desarrollo vive en "
        f"vite.config.ts, que es el unico sitio donde esa direccion vale.")


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_la_interfaz_no_tiene_botones_de_validacion_humana():
    """La ley del encargo: no hay validacion humana, nunca.

    Se buscan **elementos de interfaz**, no palabras: la interfaz explica en
    varias pantallas que no hay botones de aprobar, y buscar la palabra a secas
    marcaba esa explicacion. Un boton es un `<button` o un `onClick`, asi que se
    exige que la palabra este cerca de uno de los dos.
    """
    prohibidas = ("aprobar", "rechazar", "validar equivalencia")
    encontradas = []
    for fichero in (APP / "src").rglob("*.tsx"):
        limpio = _sin_comentarios(fichero.read_text(encoding="utf-8"))
        bajo = limpio.lower()
        for palabra in prohibidas:
            inicio = 0
            while (pos := bajo.find(palabra, inicio)) != -1:
                ventana = bajo[max(0, pos - 300):pos + 300]
                if "<button" in ventana or "onclick" in ventana:
                    encontradas.append(f"{fichero.name}: {palabra}")
                    break
                inicio = pos + 1
    assert not encontradas, (
        f"hay botones de validacion humana ({encontradas}). El encargo dice que "
        f"el matching es automatico y que nadie valida nada.")
