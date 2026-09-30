"""La única comprobación que mira hacia fuera: ¿nuestro precio está en su web?

Todos los demás controles del proyecto miran hacia dentro. Un catálogo
internamente coherente con un error de lectura sistemático es un catálogo
coherentemente equivocado, y no hay control interno que lo vea.
"""

import polars as pl

from core.fetch import HTTPStatusError, RawResponse
from projects.cesta import verificar_precios as vp


def _fila(fuente="dia", id_fuente="1", precio=199, nombre="Algo",
          url="https://x/p/1"):
    return {"fuente": fuente, "id_fuente": id_fuente, "nombre": nombre,
            "precio_cent": precio, "url": url}


class _Fetcher:
    def __init__(self, cuerpo=b"", error=None):
        self.cuerpo, self.error = cuerpo, error

    def get(self, url, **kw):
        if self.error:
            raise self.error
        return RawResponse(url=url, status=200, body=self.cuerpo, fetched_at="")


# ---------------------------------------------------- leer el precio de la web --

def test_el_precio_se_lee_aunque_lleve_un_espacio_duro_delante_del_euro():
    """Lo que dio por muerta a Eroski dos veces. `\\s` en bytes no lo ve."""
    assert vp.precios_en(b"1 KILO A  1,95\xc2\xa0\xe2\x82\xac") == [195]


def test_se_leen_las_entidades_html_del_euro():
    assert vp.precios_en(b"<span>2,45&nbsp;&euro;</span>") == [245]


def test_una_pagina_sin_precios_no_inventa_ninguno():
    assert vp.precios_en(b"<p>Producto no disponible</p>") == []


# ------------------------------------------------------------- el veredicto --

def test_nuestro_precio_esta_en_su_pagina():
    v = vp.comprueba(_fila(precio=245), _Fetcher(b"ahora 2,45 &euro; IVA incl."))
    assert v.estado == "coincide"
    assert v.bien


def test_un_precio_que_no_esta_en_su_pagina_se_canta_con_las_dos_cifras():
    v = vp.comprueba(_fila(precio=245), _Fetcher(b"precio 3,10 &euro;"))
    assert v.estado == "no aparece"
    assert v.visto == [310]


def test_un_enlace_roto_se_distingue_de_un_precio_mal():
    """El fallo de Alcampo del 21 de septiembre de 2026: 23.776 enlaces a 404.

    El precio estaba bien; lo que estaba mal era la URL, y ningún control
    interno podía verlo porque un enlace roto sólo se nota al pulsarlo.
    """
    f = _Fetcher(error=HTTPStatusError("https://x", 404, b""))
    assert vp.comprueba(_fila(), f).estado == "404"


def test_una_pagina_sin_precio_no_se_cuenta_como_precio_mal():
    """Agotado, con login o de otra región: no dice nada de nuestro dato."""
    assert vp.comprueba(_fila(), _Fetcher(b"<p>Sin stock</p>")).estado == "sin precio"


def test_un_fallo_de_red_no_acusa_al_dato():
    f = _Fetcher(error=RuntimeError("timeout"))
    assert vp.comprueba(_fila(), f).estado == "no se pudo"


def test_un_403_de_alcampo_es_el_waf_y_no_la_red():
    """El 29 de septiembre de 2026 el resumen decía `alcampo 0/8 coinciden (8 no se pudo)`.

    Y remataba con «8 sin comprobar: es la conexion, no el dato». Lo que pasaba es que la
    sesión cacheada ya no valía para las fichas y Alcampo contestaba 403. Alcampo es el 45 %
    del catálogo: contar ese 403 como un problema de red esconde que su precio lleva días sin
    comprobarse contra su propia página.
    """
    f = _Fetcher(error=HTTPStatusError("https://x", 403, b""))
    v = vp.comprueba(_fila(fuente="alcampo", url="https://www.compraonline.alcampo.es/p/1"), f)
    assert v.estado == "reto"
    assert v.detalle == "HTTP 403 (WAF)"
    assert not v.bien


def test_un_403_de_otra_cadena_sigue_siendo_un_fallo_de_red():
    """El 403 solo es el WAF donde hay WAF. En las demás, un 403 es un 403."""
    f = _Fetcher(error=HTTPStatusError("https://x", 403, b""))
    v = vp.comprueba(_fila(fuente="dia"), f)
    assert v.estado == "no se pudo"
    assert v.detalle == "HTTP 403"


def test_mercadona_se_pregunta_a_su_ficha_en_json():
    """Su tienda no trae precios en el HTML: los pide aparte."""
    cuerpo = b'{"id":"13294","price_instructions":{"unit_price":"1.60"}}'
    v = vp.comprueba(_fila(fuente="mercadona", id_fuente="13294", precio=160),
                     _Fetcher(cuerpo))
    assert v.estado == "coincide"
    assert v.url == "https://tienda.mercadona.es/api/products/13294/"


# ------------------------------------- los dos puntos ciegos, cerrados el 26 sep --

def test_aldi_se_pregunta_a_su_api_y_no_a_su_pagina():
    """El 24 de septiembre Aldi dio **0/10 sin precio** y no era el dato.

    Su pagina de producto (70 KB de HTML) no trae ni una cifra con simbolo de euro: el
    precio lo pinta el navegador pidiendoselo a su API. Se lee esa API, que es la misma que
    usa su web, y el resultado del dia fue 10 de 10 coincidiendo.
    """
    cuerpo = (b'{"productId":"123","currentPrice":{"priceValue":1.19,'
              b'"basePrice":[{"basePriceValue":2.38,"basePriceScale":"KG"}]}}')
    v = vp.comprueba(_fila(fuente="aldi", id_fuente="123", precio=119), _Fetcher(cuerpo))
    assert v.estado == "coincide"
    assert "aldi.es/api/product/pds/123" in v.url


def test_aldi_sigue_sabiendo_decir_que_no_cuadra():
    """Que se lea por API no lo vuelve indulgente: si no esta, se canta."""
    cuerpo = b'{"currentPrice":{"priceValue":1.49}}'
    v = vp.comprueba(_fila(fuente="aldi", id_fuente="123", precio=119), _Fetcher(cuerpo))
    assert v.estado == "no aparece"
    assert v.visto == [149]


def test_el_reto_del_waf_es_un_punto_ciego_y_no_un_precio_que_falta():
    """Alcampo contestaba el reto de AWS WAF (2.491 bytes) y se contaba como `sin precio`.

    Con eso, el 24 de septiembre Alcampo salio 3/10 y parecia un suspenso de sus precios
    cuando era un suspenso del comprobador. Ahora se dice con su nombre, y no cuenta como
    fallo del dato.
    """
    reto = b'<html><script>window.gokuProps = {"key":"x"}</script></html>'
    v = vp.comprueba(_fila(fuente="alcampo"), _Fetcher(reto))
    assert v.estado == "reto"
    assert v.detalle == "AWS WAF"


def test_alcampo_se_pide_con_la_sesion_del_waf(monkeypatch):
    """Sin la cookie que ya tiene el colector, su pagina de producto no llega."""
    from core import waf

    monkeypatch.setattr(waf, "para", lambda *a, **k: {
        "cookies": {"aws-waf-token": "abc"}, "user_agent": "agente-de-prueba"})
    f = vp.fetcher_de("alcampo")
    assert f.session.cookies.get("aws-waf-token") == "abc"
    assert f.headers.get("User-Agent") == "agente-de-prueba"
    # Y a las demás no se les mete la sesión de Alcampo
    assert not vp.fetcher_de("dia").session.cookies.get("aws-waf-token")


def test_el_reto_no_entra_en_el_recuento_de_fallos(capsys):
    """Un punto ciego se cuenta aparte; si contara, taparia un fallo de verdad."""
    veredictos = [
        vp.Veredicto("alcampo", "1", "Uno", "u", 100, "reto", [], "AWS WAF"),
        vp.Veredicto("dia", "2", "Dos", "u", 100, "coincide", [100]),
    ]
    assert vp.informe(veredictos) == 0
    salida = capsys.readouterr().out
    assert "reto del WAF" in salida and "no dice nada de su precio" in salida


# ------------------------------------------------------------- sin umbrales --

def test_no_hay_porcentaje_de_aprobado_cada_fallo_sale_con_su_nombre(capsys):
    """«O están bien o están mal»: un 95 % de aciertos no es un aprobado."""
    veredictos = [
        vp.Veredicto("dia", "1", "Bien", "u", 100, "coincide", [100]),
        vp.Veredicto("dia", "2", "Mal", "u", 200, "no aparece", [999]),
    ]
    assert vp.informe(veredictos) == 1
    salida = capsys.readouterr().out
    assert "1/2 coinciden" in salida
    assert "Mal" in salida and "9.99" in salida


def test_la_muestra_es_al_azar_y_no_los_raros_a_proposito(tmp_path, monkeypatch):
    """Elegir los raros encontraría más fallos y no diría nada del catálogo."""
    monkeypatch.setattr(vp.config, "DATA", tmp_path)
    carpeta = tmp_path / "bronze" / "fuente=dia" / "fecha=2026-09-21"
    carpeta.mkdir(parents=True)
    pl.DataFrame({
        "fuente": ["dia"] * 50, "id_fuente": [str(i) for i in range(50)],
        "nombre": [f"p{i}" for i in range(50)], "precio_cent": list(range(1, 51)),
        "url": [f"https://x/{i}" for i in range(50)],
    }).write_parquet(carpeta / "part.parquet")

    a = [f["id_fuente"] for f in vp.muestra(por_cadena=5, semilla=1)]
    b = [f["id_fuente"] for f in vp.muestra(por_cadena=5, semilla=2)]
    assert len(a) == 5
    assert a != b, "con semillas distintas la muestra tiene que cambiar"
    assert a == [f["id_fuente"] for f in vp.muestra(por_cadena=5, semilla=1)]


def test_sin_precio_o_sin_url_no_entra_en_la_muestra(tmp_path, monkeypatch):
    monkeypatch.setattr(vp.config, "DATA", tmp_path)
    carpeta = tmp_path / "bronze" / "fuente=dia" / "fecha=2026-09-21"
    carpeta.mkdir(parents=True)
    pl.DataFrame({
        "fuente": ["dia"] * 3, "id_fuente": ["1", "2", "3"],
        "nombre": ["a", "b", "c"], "precio_cent": [100, None, 300],
        "url": ["https://x/1", "https://x/2", None],
    }).write_parquet(carpeta / "part.parquet")
    assert [f["id_fuente"] for f in vp.muestra(por_cadena=9)] == ["1"]


def test_si_no_hubo_conexion_se_dice_en_una_linea(capsys):
    """Quince productos diciendo quince veces «no hubo red» entierran el día
    siguiente que sí tenga algo que contar."""
    veredictos = [vp.Veredicto("dia", str(i), f"p{i}", "u", 100, "no se pudo", [])
                  for i in range(5)]
    assert vp.informe(veredictos) == 0
    salida = capsys.readouterr().out
    assert "es la conexion, no el dato" in salida
    assert "uno por uno" not in salida


def test_una_pagina_sin_precio_no_se_lista_como_fallo(capsys):
    """Agotado o con login no acusa al dato: sale en el recuento, no en la lista."""
    veredictos = [
        vp.Veredicto("dia", "1", "Bien", "u", 100, "coincide", [100]),
        vp.Veredicto("dia", "2", "Agotado", "u", 200, "sin precio", []),
    ]
    assert vp.informe(veredictos) == 0
    salida = capsys.readouterr().out
    assert "1 sin precio" in salida
    assert "uno por uno" not in salida
