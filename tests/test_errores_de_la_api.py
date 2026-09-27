"""Cuando la API falla: una frase, y una forma de reintentar sin recargar la pagina.

Es la fila «errores + reintentar» del §8 del encargo de UX, y **no la habia mirado un
navegador**: se probaba el endpoint que devuelve 500, no la pantalla que lo recibe. Al
mirarla salio un hueco de verdad y dos fallos de instrumento, y los tres estan aqui escritos
porque los tres se pueden repetir.

El hueco: **la cesta era la unica pantalla que escribia su error a mano** (`Vacio` +
`textoDeError`) en vez de usar `Fallo`, y por eso era la unica **sin «Volver a intentarlo»**.
Medido el 23 de septiembre de 2026 con `/api/listas` devolviendo 500: «No he podido traer tus
listas» y **ni un boton** -- habia que recargar la pagina, que en el movil no es evidente.
Usar `Fallo` arregla ademas el tono, que es lo otro que `Fallo` decide: sin cobertura no es
rojo (`ui.tsx`), y esa decision tiene que estar en un sitio y no repetida en cada pantalla.

El primer fallo de instrumento: el patron `**/api/alertas*` no coge solo el endpoint, coge
tambien **`/src/api/alertas.ts`** del servidor de desarrollo, porque la cadena `/api/alertas`
esta dentro de esa ruta. El modulo se quedaba con un 500, la aplicacion no llegaba a montarse
y la pantalla se veia en blanco: se habria escrito «un 500 en los avisos deja la aplicacion en
blanco», y era mentira. Lo delato el control.

El segundo: `unroute` quita **la ruta que se registro**, y para eso necesita el mismo objeto.
Con un filtro nuevo en cada llamada, la intercepcion se quedaba puesta y las pantallas
siguientes seguian recibiendo 500: el fallo aparecia tres secciones mas tarde y parecia otra
cosa.

Y el tercero, el de siempre: leer la pantalla nada mas cargar mide «Cargando…», porque React
Query reintenta antes de darse por vencida. Ahora se espera al boton, no a un numero de
milisegundos.
"""
from __future__ import annotations

import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]
CESTA = RAIZ / "plataforma" / "web" / "app" / "src" / "paginas" / "Cesta.tsx"
PUERTA = RAIZ / "plataforma" / "prueba_navegador.py"


def test_la_cesta_deja_reintentar_cuando_no_puede_traer_las_listas():
    """El unico sitio donde el error se escribia a mano, y el unico sin boton."""
    cesta = CESTA.read_text(encoding="utf-8")
    assert "listas.isError" in cesta, "no encuentro el caso de error de las listas"
    assert 'reintentar={() => void listas.refetch()}' in cesta, (
        "la cesta no deja reintentar: hay que recargar la pagina a mano")
    # Y no vuelve a escribirlo a mano: eso es lo que le quito el boton y el tono.
    assert 'titulo="No he podido traer tus listas"' not in cesta, (
        "la cesta vuelve a escribir su error con un `Vacio` en vez de usar `Fallo`")


def test_el_filtro_de_la_api_no_coge_los_modulos_del_front():
    """`/api/...` es la API; `/src/...` es el front, y no se pueden confundir.

    Con un patron de glob, un 500 puesto para medir el error de los avisos le llegaba al
    modulo `src/api/alertas.ts`, y la aplicacion se quedaba sin montar: la pantalla en
    blanco parecia un fallo de la aplicacion y era del instrumento.
    """
    puerta = PUERTA.read_text(encoding="utf-8")
    assert "def _solo_el_endpoint(" in puerta, "no hay filtro que separe la API del front"
    assert 'if "/api/" not in sin_parametros' in puerta, (
        "el filtro tiene que mirar la ruta despues del host")
    assert "antes.endswith(BASE.removesuffix" in puerta, (
        "el filtro no comprueba que la ruta cuelgue de la raiz del front")
    # Y la razon, escrita donde se lee.
    assert "src/api/alertas.ts" in puerta, (
        "el caso que lo destapo tiene que estar contado al lado del filtro")


def test_la_intercepcion_se_quita_con_el_mismo_filtro():
    """Un filtro nuevo no quita nada: la ruta se queda puesta y rompe lo de despues."""
    puerta = PUERTA.read_text(encoding="utf-8")
    assert "filtro = _contesta_mal(pagina, endpoint)" in puerta, (
        "la intercepcion no se guarda, asi que no se puede quitar")
    assert "pagina.unroute(filtro)" in puerta, "la intercepcion no se quita con su filtro"
    assert "pagina.unroute(_solo_el_endpoint(endpoint))" not in puerta, (
        "se esta intentando quitar con un filtro nuevo, que no quita nada")


def test_los_errores_se_miden_en_las_cuatro_pantallas_y_esperando_al_boton():
    """Cuatro pantallas, y esperando al estado de error: `Cargando…` no es un error.

    Y **el buscador se mide en `/buscar` desde el 27 de septiembre de 2026**: desde ese dia
    `/` es la pantalla de entrada (`Inicio`) y su buscador no navega a ningun sitio -- busca
    ahi mismo, y con la API caida lo dice con palabras sin echarle la culpa a quien escribe
    («nada con esas palabras»). Eso se comprueba aparte, en la puerta, con su propio filtro.
    """
    puerta = PUERTA.read_text(encoding="utf-8")
    for que in ('("la cesta", "listas", "/cesta"', '("los avisos", "alertas", "/avisos"',
                '("lo mio que ha bajado", "bajadas"',
                '("el buscador", "buscar", "/buscar"'):
        assert que in puerta, f"la puerta no mide el error de {que}"
    assert "el buscador de la primera pantalla, con la API a 500, lo dice con" in puerta, (
        "la puerta no mide el buscador de la primera pantalla, que es donde se escribe")
    assert "No he podido buscar" in puerta and "Nada con esas palabras" in puerta, (
        "el buscador de Inicio no distingue «no he podido» de «no hay nada»")
    assert 'get_by_role("button", name="Volver a intentarlo").first.wait_for' in puerta, (
        "la puerta no espera a que aparezca el estado de error: mide «Cargando…»")
    assert "lo dice con palabras" in puerta and "deja reintentar" in puerta, (
        "las dos mitades de la fila «errores + reintentar» tienen que estar comprobadas")
