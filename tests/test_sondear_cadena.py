"""El sondeo de una cadena nueva: lo que se puede, lo que se debe y si compensa.

La parte que importa de verdad es `reto_en`: distingue "esta pagina lleva un muro
anti-bot delante" de "esta pagina no me la dan desde aqui". Son dos cosas
distintas y confundirlas cuesta caro en las dos direcciones -- cerrar una cadena
que si se podia leer, o ponerse a dar vueltas alrededor de un muro.
"""
from projects.cesta import sondear_cadena
from projects.cesta.sondear_cadena import POR_UNIDAD, PRECIO, reto_en


def test_una_pagina_normal_no_tiene_reto():
    assert reto_en(b"<html><body>Leche entera 1 L  0,99</body></html>") is None


def test_se_reconoce_el_recaptcha():
    assert "reCAPTCHA" in reto_en(
        b'<script src="https://www.google.com/recaptcha/api.js"></script>')


def test_se_reconoce_el_turnstile_de_cloudflare():
    assert "Turnstile" in reto_en(b'<div data-sitekey src=challenges.cloudflare.com>')


def test_se_reconoce_el_interstitial_por_su_titulo():
    assert reto_en(b"<title>Checking your browser - reCAPTCHA</title>")


def test_se_reconoce_el_waf_de_aws():
    # El que ya conocemos: Alcampo. Aqui se detecta para poder decir que es, no
    # para pasarlo.
    assert "AWS WAF" in reto_en(b'{"token":"aws-waf-token=abc"}')


def test_una_cabecera_tambien_delata_el_reto():
    assert "cf-mitigated" in reto_en(b"<html></html>", {"cf-mitigated": "challenge"})


def test_el_euro_se_encuentra_venga_como_venga():
    # La misma pagina puede venir en UTF-8, en cp1252, en iso-8859-15 o con la
    # entidad HTML. Decodificar mal una pagina es la forma de no encontrar un
    # precio que si esta, asi que aqui se busca en bytes y sin decodificar.
    for codificacion in ("utf-8", "cp1252", "iso-8859-15"):
        assert PRECIO.findall("1,29 €".encode(codificacion)) == [b"1,29"], codificacion
    assert PRECIO.findall(b"1,29&euro;") == [b"1,29"]
    assert PRECIO.findall(b"1,29 EUR") == [b"1,29"]


def test_el_precio_por_unidad_se_distingue_del_precio():
    assert POR_UNIDAD.search("2,58 €/kg".encode())
    assert POR_UNIDAD.search("€ / litro".encode())
    assert not POR_UNIDAD.search("0,99 €".encode())


# --- que el comando se pueda escribir de memoria ----------------------------
#
# El 19 de septiembre de 2026 el comando que se dio para sondear Eroski llevaba
# una `\` de continuacion de linea, que es de bash. En PowerShell el error que
# sale es `unrecognized arguments: \`, que no dice nada de lo que pasa, y se
# intento cuatro veces seguidas. Un comando que hay que componer a mano es un
# comando que no se ejecuta: las candidatas se sondean por su nombre.

def test_las_candidatas_conocidas_traen_su_direccion_y_sus_rutas():
    for nombre, c in sondear_cadena.CANDIDATAS.items():
        assert c["base"].startswith("https://"), nombre
        assert c["categoria"] or c["ficha"], f"{nombre}: sin nada que pedir"
        assert c["nota"], f"{nombre}: sin nota de lo que ya se sabe"


def test_el_nombre_de_una_candidata_rellena_las_rutas(monkeypatch, capsys):
    visto = {}

    def falso_mira(nombre, url, f, rp, guardar=None):
        visto.setdefault("urls", []).append(url)
        return True, b""

    monkeypatch.setattr(sondear_cadena, "_robots", lambda base, f: (None, "sin robots"))
    monkeypatch.setattr(sondear_cadena, "_mira", falso_mira)
    monkeypatch.setattr(sondear_cadena, "Fetcher", lambda **kw: object())

    sondear_cadena.main(["ahorramas"])

    assert any("ahorramas.com" in u for u in visto["urls"])
    assert any("otros-desodorantes" in u for u in visto["urls"])
    assert "Salesforce" in capsys.readouterr().out


def test_una_direccion_suelta_sigue_funcionando(monkeypatch):
    visto = {}
    monkeypatch.setattr(sondear_cadena, "_robots", lambda base, f: (None, "sin robots"))
    monkeypatch.setattr(
        sondear_cadena, "_mira",
        lambda n, url, f, rp, guardar=None: (visto.setdefault("urls", []).append(url), (True, b""))[1])
    monkeypatch.setattr(sondear_cadena, "Fetcher", lambda **kw: object())
    sondear_cadena.main(["https://www.ejemplo.es", "--categoria", "/alimentacion/"])
    assert visto["urls"][-1] == "https://www.ejemplo.es/alimentacion/"


# --- el falso negativo de Eroski -------------------------------------------
#
# 19 de septiembre de 2026: Eroski contesta 200 desde una linea de casa, sin reto
# delante, con un megabyte de HTML... y cero simbolos de euro. Buscar solo el "€"
# daba un "no hay precio" que parecia un veredicto y era un falso negativo: el
# dato viaja dentro de un JSON incrustado que pinta el navegador.

def test_se_reconoce_el_json_incrustado_de_los_marcos_modernos():
    import re
    for cuerpo, espera in [
        (b'<script>window.__NEXT_DATA__={}</script>', "Next.js"),
        (b'window.__INITIAL_STATE__ = {}', "estado inicial"),
        (b'<script>window.__NUXT__=(function(){})</script>', "Nuxt"),
        (b'<script type="application/json">{}</script>', "application/json"),
    ]:
        nombres = [n for m, n in sondear_cadena.ESTADOS if re.search(m, cuerpo)]
        assert any(espera in n for n in nombres), cuerpo


def test_se_reconocen_las_claves_con_pinta_de_precio():
    cuerpo = b'{"name":"Leche","price":1.29,"unitPrice":2.58}'
    claves = [c for c in sondear_cadena.CLAVES_PRECIO if c in cuerpo]
    assert b'"price"' in claves and b'"unitPrice"' in claves


def test_un_html_sin_nada_de_eso_no_inventa_claves():
    cuerpo = b"<html><body><h1>Bienvenido</h1></body></html>"
    assert [c for c in sondear_cadena.CLAVES_PRECIO if c in cuerpo] == []


def test_la_candidata_de_eroski_apunta_a_una_hoja_y_no_a_una_rama():
    """El 19 de septiembre se sondeo `2059806-alimentacion` y devolvio un
    megabyte de menu sin un solo producto: es un nodo de navegacion. Es el mismo
    patron del nodo vacio de Alcampo, y la leccion es la misma."""
    ruta = sondear_cadena.CANDIDATAS["eroski"]["categoria"]
    assert ruta.count("/") >= 5, "tiene que ser una hoja, no una rama de primer nivel"
    assert not ruta.rstrip("/").endswith("alimentacion")


def test_se_cuentan_los_enlaces_de_categoria_de_una_pagina():
    cuerpo = b"".join(
        f'<a href="/es/supermercado/2059698-frescos/2059699-frutas/205970{i}-loquesea/">x</a>'
        .encode() for i in range(5))
    assert len(set(sondear_cadena.RUTA_CATEGORIA.findall(cuerpo))) == 5


def test_un_menu_sin_categorias_no_cuenta_enlaces():
    cuerpo = b'<a href="/es/login/">entrar</a><a href="#">nada</a>'
    assert set(sondear_cadena.RUTA_CATEGORIA.findall(cuerpo)) == set()


# --- seguir un enlace de producto desde la categoria ------------------------
#
# Es la unica forma de saber que publica una cadena por producto -- codigo de
# barras, ingredientes, nutricion -- sin adivinar su patron de URL. Cada cadena
# tiene el suyo, asi que se prueban varios.

def test_se_encuentra_la_ficha_en_los_patrones_conocidos():
    casos = [
        (b'<a href="/es/p/leche-entera/12345">Leche</a>', "/es/p/leche-entera/12345"),
        (b'<a href="/producto/aceite-de-oliva">Aceite</a>', "/producto/aceite-de-oliva"),
        (b'<a href="/miel-de-flores-800g-47.html">Miel</a>', "/miel-de-flores-800g-47.html"),
    ]
    for cuerpo, espera in casos:
        assert sondear_cadena._una_ficha(cuerpo, "https://x.es") == "https://x.es" + espera


def test_no_se_sigue_el_carro_ni_el_login():
    cuerpo = (b'<a href="/es/login/anonymousbasket/p/1234">entrar</a>'
              b'<a href="javascript:void(0)">nada</a>')
    assert sondear_cadena._una_ficha(cuerpo, "https://x.es") is None


def test_sin_enlaces_de_producto_devuelve_nada():
    cuerpo = b'<a href="/es/supermercado/2059698-frescos/">Frescos</a>'
    assert sondear_cadena._una_ficha(cuerpo, "https://x.es") is None


# --- los tres fallos que destapo Eroski el 19 de septiembre de 2026 ---------

def test_el_espacio_duro_antes_del_euro_no_esconde_el_precio():
    """El sondeo dijo "precios con simbolo de euro: 0" en una pagina que a la
    vista pone "1 KILO A 1,95 €". En bytes era:

        b'1 KILO A  1,95\\xc2\\xa0\\xe2\\x82\\xac'
                          ^^^^^^^^ espacio duro (U+00A0)

    `\\s` en un patron de **bytes** solo casa el espacio ASCII. Un falso negativo
    asi no dice "no lo he encontrado": dice "aqui no hay precios", que es un
    veredicto, y con el se cierra una cadena que si se podia leer.
    """
    assert PRECIO.findall("1,95 €".encode()) == [b"1,95"]
    assert PRECIO.findall(b"1,95&nbsp;&euro;") == [b"1,95"]
    assert PRECIO.findall("2,58 €".encode()) == [b"2,58"]


def test_el_precio_por_unidad_tambien_se_escribe_en_prosa():
    # Eroski no pone "€/kg": pone "1 KILO A 1,95 €".
    assert POR_UNIDAD.search(b"1 KILO A  1,95")
    assert POR_UNIDAD.search(b"PRECIO POR LITRO")
    assert POR_UNIDAD.search("2,58 €/kg".encode())
    assert not POR_UNIDAD.search("0,99 €".encode())


def test_no_se_sigue_una_direccion_de_evento_de_tapestry():
    """El sondeo "siguio una ficha" y lo que siguio fue el selector de idioma.

    Devolvio la misma pagina de la categoria y el sondeo dijo de ella lo mismo,
    asi que parecia que habia funcionado: un falso positivo silencioso, que es
    peor que un error.
    """
    malo = (b'<a href="https://supermercado.eroski.es:443/es/'
            b'supermarket.menulayout.menumobile.languageswitcher:changelanguage/es'
            b'?t:ac=2059698-frescos">idioma</a>')
    assert sondear_cadena._una_ficha(malo, "https://supermercado.eroski.es") is None


def test_el_puerto_en_la_direccion_no_la_descalifica():
    # `https://host:443/es/productdetail/...` lleva dos puntos en el puerto, no
    # en la ruta. Mirar la direccion entera en vez de la ruta rechazaba fichas
    # buenas.
    bueno = (b'<a href="https://supermercado.eroski.es:443/es/productdetail/'
             b'23760622-naranja-eroski-malla-3-kg/">Naranja</a>')
    assert sondear_cadena._una_ficha(bueno, "https://supermercado.eroski.es") == (
        "https://supermercado.eroski.es:443/es/productdetail/"
        "23760622-naranja-eroski-malla-3-kg/")


def test_se_busca_la_ficha_en_el_cuerpo_entero():
    # En Eroski el menu ocupa los primeros 600 KB y la rejilla empieza despues.
    relleno = b'<a href="/es/supermercado/2059698-frescos/">x</a>' * 14000
    cuerpo = relleno + b'<a href="/es/productdetail/123-naranja/">Naranja</a>'
    assert len(cuerpo) > 600_000
    assert sondear_cadena._una_ficha(cuerpo, "https://x.es").endswith("/123-naranja/")
