"""Carrefour: las categorias raras no pueden tumbar el recorrido.

Del recorrido real del 7 sep: de 650 categorias del sitemap, seis respondieron 200
pero sin rejilla de productos (KeyError 'criteo' o 'results'). Se contaban como
errores, y con `errores == 0` como condicion para guardar, eso significaba tirar
cuarenta minutos de red y no escribir bronze.
"""
import json
from typing import ClassVar
from unittest import mock

import pytest

from projects.cesta.collectors import carrefour


def _cuerpo(estado: dict) -> bytes:
    return ("window.__INITIAL_STATE__=" + json.dumps(estado) + ";").encode()


def _listado(estado: dict):
    with mock.patch.object(carrefour, "_raw", return_value=_cuerpo(estado)):
        return carrefour.listado(None, "cat1", "slug", 0)


def test_categoria_sin_criteo_no_es_un_error_fatal():
    with pytest.raises(carrefour.SinCatalogo):
        _listado({"pagination": {"total_results": 0}})


def test_categoria_sin_results_no_es_un_error_fatal():
    with pytest.raises(carrefour.SinCatalogo):
        _listado({"criteo": {"plpData": {}}, "pagination": {}})


def test_categoria_normal_devuelve_items_y_total():
    r = _listado({
        "criteo": {"plpData": {"results": {"items": [{"product_id": "1"}]}}},
        "pagination": {"total_results": 1},
    })
    assert len(r["items"]) == 1
    assert r["total"] == 1


def test_sin_paginacion_el_total_es_cero_y_no_revienta():
    r = _listado({"criteo": {"plpData": {"results": {"items": []}}}})
    assert r == {"items": [], "total": 0, "eans": {}, "promos": {},
                 "servida": None}


# El EAN no viene en los items de criteo: viene en el datalayer de analitica del
# mismo HTML, y se empareja por el slug de la url. Sin esto Carrefour no cruza con
# ninguna otra cadena, que es justo para lo que sirve el codigo de barras.
_DATALAYER = (
    'window["impressions"]=[{"item_name":"leche-entera-hacendado-1-l",'
    '"item_id":"123456","item_ean":"8480000123456","price":1.05}];'
)


def test_el_ean_sale_del_datalayer_y_se_empareja_por_slug():
    estado = {"criteo": {"plpData": {"results": {"items": []}}}}
    cuerpo = _cuerpo(estado) + _DATALAYER.encode()
    with mock.patch.object(carrefour, "_raw", return_value=cuerpo):
        r = carrefour.listado(None, "cat1", "slug", 0)
    assert r["eans"] == {"leche-entera-hacendado-1-l": "8480000123456"}

    fila = carrefour.a_registro(
        {"product_id": "9", "url": "/supermercado/leche-entera-hacendado-1-l/R-9/p"},
        "leche", r["eans"])
    assert fila["ean"] == "8480000123456"


def test_sin_datalayer_el_ean_queda_vacio_pero_la_fila_se_construye():
    fila = carrefour.a_registro({"product_id": "9", "url": "/x/y/R-9/p"}, "leche", {})
    assert fila["ean"] is None
    assert fila["id_fuente"] == "9"


def test_un_403_en_el_sitemap_no_puede_tirar_el_dia_entero():
    """El 11 y el 12 de sep Carrefour devolvio 403 al indice de secciones dos
    dias seguidos. Sin categorias no hay recorrido, asi que se perdio el
    catalogo ENTERO de ambos dias -- por un indice que es casi el mismo todas
    las semanas. El de ayer vale.
    """
    from datetime import date

    guardado = b"<loc>https://www.carrefour.es/x/cat123/c</loc>"
    with mock.patch.object(carrefour, "_raw", side_effect=RuntimeError("HTTP 403")):
        with mock.patch.object(carrefour, "load_raw_reciente",
                               return_value=(guardado, date(2026, 9, 10))):
            assert "cat123" in carrefour._sitemap(None, "http://x", "sitemap-index")


def test_si_no_hay_nada_guardado_entonces_si_se_rinde():
    # Inventarse un catalogo seria mucho peor que no tener ninguno.
    with mock.patch.object(carrefour, "_raw", side_effect=RuntimeError("HTTP 403")):
        with mock.patch.object(carrefour, "load_raw_reciente", return_value=None):
            with pytest.raises(RuntimeError):
                carrefour._sitemap(None, "http://x", "sitemap-index")


def test_si_el_sitemap_responde_bien_no_se_toca_lo_guardado():
    with mock.patch.object(carrefour, "_raw", return_value=b"<loc>hoy</loc>"):
        with mock.patch.object(carrefour, "load_raw_reciente") as viejo:
            assert carrefour._sitemap(None, "http://x", "sitemap-index") == "<loc>hoy</loc>"
            viejo.assert_not_called()


# --- las ofertas, que estaban en el HTML y no en el JSON ----------------
# Carrefour salia con cero promociones cuando en realidad las tiene en el 11,8 %
# de sus fichas: la mecanica ("2a unidad -50%", "3x2") vive en el `title` de la
# insignia de la tarjeta, no en `__INITIAL_STATE__`, que es lo unico que leiamos.

_TARJETAS = (
    '<a href="/supermercado/alitas-de-pollo/R-VC4AECOMM-111/p" class="x">'
    '<div class="badge badge-promotions" data-v-1>'
    '<div title="2ª unidad -50%" class="badge__name"></div></div>'
    '<a href="/supermercado/pan-de-molde/R-VC4AECOMM-222/p" class="x">'
    '<span>sin oferta</span>'
    '<a href="/supermercado/cerveza-lata/R-VC4AECOMM-333/p" class="x">'
    '<div class="badge badge-promotions" data-v-1>'
    '<div title="3x2" class="badge__name"></div></div>'
)


def test_saca_la_mecanica_de_la_oferta_de_cada_tarjeta():
    from projects.cesta.collectors import carrefour
    p = carrefour._promos_del_html(_TARJETAS)
    assert p == {"alitas-de-pollo": "2ª unidad -50%", "cerveza-lata": "3x2"}


def test_la_oferta_no_se_pega_al_producto_de_al_lado():
    # El fallo que acecha aqui: que la insignia de un producto acabe asignada al
    # anterior o al siguiente. Por eso la tarjeta se corta en el enlace siguiente.
    from projects.cesta.collectors import carrefour
    assert "pan-de-molde" not in carrefour._promos_del_html(_TARJETAS)


def test_sin_insignias_no_inventa_promociones():
    from projects.cesta.collectors import carrefour
    assert carrefour._promos_del_html('<a href="/supermercado/x/R-1/p">nada</a>') == {}


def test_el_registro_marca_promo_cuando_hay_insignia():
    from projects.cesta.collectors import carrefour
    p = {"product_id": "111", "name": "Alitas", "price": 3.5,
         "url": "/supermercado/alitas-de-pollo/R-VC4AECOMM-111/p"}
    promos = {"alitas-de-pollo": "2ª unidad -50%"}
    r = carrefour.a_registro(p, "aves", None, promos)
    assert r["promo"] is True
    assert r["promo_txt"] == "2ª unidad -50%"


def test_el_registro_sin_promocion_sigue_sin_ella():
    from projects.cesta.collectors import carrefour
    p = {"product_id": "222", "name": "Pan", "price": 1.0,
         "url": "/supermercado/pan-de-molde/R-VC4AECOMM-222/p"}
    r = carrefour.a_registro(p, "panaderia", None, {"otro": "3x2"})
    assert r["promo"] is False
    assert r["promo_txt"] is None


# --- la promocion estructurada, con su fecha de fin ---------------------
# El JSON del listado trae `badge_map.promotions` con el nombre de la mecanica
# Y su fecha de fin. Medido el 17 de septiembre: 1.032 promociones y las 1.032
# con fecha. Antes se sacaba el `title` del HTML y se perdia la fecha.

def _item(**extra):
    base = {"product_id": "VC4AECOMM-1", "name": "Atun", "price": "3,19 €",
            "url": "/supermercado/atun/R-VC4AECOMM-1/p"}
    base.update(extra)
    return base


def test_la_promocion_sale_del_json_con_su_fecha():
    from projects.cesta.collectors import carrefour
    r = carrefour.a_registro(_item(badge_map={"promotions": [
        {"name": "2ª unidad -50%", "end_date": "21/09/2026"}]}))
    assert r["promo_txt"] == "2ª unidad -50%"
    assert r["promo_hasta"].strftime("%Y-%m-%d") == "2026-09-21"
    assert r["promo"] is True


def test_una_fecha_que_no_se_entiende_no_se_inventa():
    from projects.cesta.collectors import carrefour
    r = carrefour.a_registro(_item(badge_map={"promotions": [
        {"name": "3x2", "end_date": "próximamente"}]}))
    assert r["promo_txt"] == "3x2"
    assert r["promo_hasta"] is None


def test_si_el_json_no_trae_promocion_se_usa_el_respaldo_del_html():
    from projects.cesta.collectors import carrefour
    r = carrefour.a_registro(_item(), None, None, {"atun": "3x2"})
    assert r["promo_txt"] == "3x2"


def test_los_sellos_salen_de_info_tags():
    from projects.cesta.collectors import carrefour
    r = carrefour.a_registro(_item(info_tags=[
        {"message": "Sin gluten"}, {"message": "Bio"}, {"message": "Congelado"}]))
    assert r["sellos"] == "ecologico,sin-gluten"
    assert r["conservacion"] == "congelado"


def test_carrefour_dice_cuando_algo_es_un_pack():
    from projects.cesta.collectors import carrefour
    assert carrefour.a_registro(_item(sell_pack_unit=6))["es_pack"] is True
    assert carrefour.a_registro(_item(sell_pack_unit=1))["es_pack"] is None


# --- bloqueo total: enterarse a la vez, no 653 veces ------------------------
#
# El 19 de septiembre de 2026 Cloudflare bloqueo desde la peticion numero 1: a
# los catorce minutos la ejecucion llevaba 383 respuestas 403 y 2.563 productos
# de los 16.416 de un dia normal. Una de esas 403 fue a la portada
# `https://www.carrefour.es/` a secas, que es la prueba de que el bloqueo no era
# de una categoria: eramos nosotros.
#
# Recorrer las 653 categorias asi es coleccionar 653 fallos identicos: no se
# recoge nada, se tarda media hora y cada peticion de mas alarga el bloqueo.

def _fetcher_que_bloquea(fallos_seguidos, total=40):
    """Un `listado` que devuelve 403 las primeras `fallos_seguidos` veces."""
    llamadas = {"n": 0}

    def listado(f, cat_id, slug, offset):
        llamadas["n"] += 1
        if llamadas["n"] <= fallos_seguidos:
            raise carrefour.HTTPStatusError(f"http://x/{cat_id}", 403, b"blocked")
        return {"total": 0, "items": [], "eans": {}, "promos": {}}

    return listado, llamadas


def _corre(monkeypatch, cuantas, umbral, fallos_seguidos):
    cats = [(f"cat{i}", "slug") for i in range(cuantas)]
    listado, llamadas = _fetcher_que_bloquea(fallos_seguidos)
    monkeypatch.setattr(carrefour, "listado", listado)
    monkeypatch.setattr(carrefour, "UMBRAL_BLOQUEO_TOTAL", umbral)
    monkeypatch.setattr(carrefour, "VUELTAS_DE_RESCATE", 0)
    monkeypatch.setattr(carrefour, "categorias", lambda f: cats)
    monkeypatch.setattr(carrefour, "Fetcher", _FetcherDePrueba)
    monkeypatch.setattr(carrefour, "log_run", lambda *a, **k: None)
    monkeypatch.setattr(carrefour, "write_parquet", lambda *a, **k: None)
    monkeypatch.setattr(carrefour.cobertura, "revisa", lambda *a, **k: [])
    return llamadas


def test_a_los_25_bloqueos_seguidos_se_deja_de_recorrer(monkeypatch, capsys):
    llamadas = _corre(monkeypatch, cuantas=200, umbral=25, fallos_seguidos=999)
    carrefour.main()
    # 25 peticiones, no 200: el resto pasa al rescate sin volver a pedirlas.
    assert llamadas["n"] == 25
    assert "el bloqueo es total" in capsys.readouterr().out


def test_un_403_suelto_no_para_el_recorrido(monkeypatch):
    # Una categoria que falla y las demas bien: eso no es un bloqueo, es una
    # categoria. Se apunta y se sigue.
    llamadas = _corre(monkeypatch, cuantas=200, umbral=25, fallos_seguidos=1)
    carrefour.main()
    assert llamadas["n"] == 200


def test_los_bloqueos_seguidos_se_cuentan_desde_cero_tras_un_acierto(monkeypatch):
    # 24 fallos, uno bueno, y a partir de ahi todo bien: no se para nunca.
    llamadas = _corre(monkeypatch, cuantas=200, umbral=25, fallos_seguidos=24)
    carrefour.main()
    assert llamadas["n"] == 200


class _FetcherDePrueba:
    """Un fetcher de mentira que apunta cuantas veces le cambian el ritmo.

    Que sea **uno** y no varios es justo lo que se quiere comprobar: el rescate
    no puede estrenar sesion, porque estrenar sesion es tirar las cookies.
    """

    creados: ClassVar[list["_FetcherDePrueba"]] = []

    def __init__(self, **kw):
        self.ritmos = [kw.get("rate_per_sec")]
        _FetcherDePrueba.creados.append(self)

    def cambia_ritmo(self, rate_per_sec):
        self.ritmos.append(rate_per_sec)


def _corre_rescate(monkeypatch, estado, veces=999, cuantas=3):
    """Una categoria que falla con `estado` las primeras `veces` peticiones.

    Devuelve la lista de esperas que el rescate llego a pedir, para poder mirar
    cuanto tiempo se ha ido en `sleep` sin gastarlo de verdad.
    """
    _FetcherDePrueba.creados.clear()
    cats = [(f"cat{i}", "slug") for i in range(cuantas)]
    llamadas = {"n": 0}
    esperas: list[int] = []

    def listado(f, cat_id, slug, offset):
        if cat_id == "cat0":
            llamadas["n"] += 1
            if llamadas["n"] <= veces:
                raise carrefour.HTTPStatusError(f"http://x/{cat_id}", estado, b"")
        # Un producto por categoria: sin filas, `main` ni llega a imprimir el
        # recuento de errores y las pruebas de ese mensaje no medirian nada.
        return {"total": 1, "items": [{"product_id": f"p-{cat_id}"}],
                "eans": {}, "promos": {}}

    monkeypatch.setattr(carrefour, "listado", listado)
    monkeypatch.setattr(carrefour, "categorias", lambda f: cats)
    monkeypatch.setattr(carrefour, "Fetcher", _FetcherDePrueba)
    monkeypatch.setattr(carrefour, "log_run", lambda *a, **k: None)
    monkeypatch.setattr(carrefour.time, "sleep", esperas.append)
    # El control de ramas caidas tiene su propia prueba y aqui solo hace ruido:
    # compara contra el bronze de verdad que haya en el disco de quien ejecute.
    monkeypatch.setattr(carrefour.cobertura, "revisa", lambda *a, **k: [])
    # Y sobre todo: **no se escribe nada**. Estas pruebas llaman a `main()`, y
    # `main()` guarda bronze cuando da el dia por bueno. El 21 de septiembre de
    # 2026 eso reemplazo los 16.560 productos de Carrefour por 199 de mentira
    # con la categoria "slug". Ahora `core.storage` lo impide ademas por su
    # cuenta, pero una prueba tampoco tiene por que intentarlo.
    monkeypatch.setattr(carrefour, "write_parquet", lambda *a, **k: None)
    return esperas, llamadas


def test_un_500_que_no_se_cura_no_se_lleva_media_hora_de_espera(monkeypatch, capsys):
    """El 20 de septiembre de 2026: cero 403 y tres categorias rotas.

    `papeleria/colorear`, `papeleria/pequeno-accesorio` y `papeleria/archivadores`
    dieron HTTP 500 las tres. Con la regla de antes se llevaban las cuatro
    vueltas enteras -- 120+240+480+960, media hora de `sleep` -- para volver a
    dar 500 las cuatro veces. Esperar no cura una pagina rota.
    """
    esperas, _ = _corre_rescate(monkeypatch, estado=500)
    carrefour.main()
    assert esperas == [carrefour.ESPERA_SIN_BLOQUEO]
    salida = capsys.readouterr().out
    assert "ninguna esta bloqueada" in salida
    assert "1 con HTTP 500" in salida


def test_un_500_pasajero_si_tiene_su_segunda_oportunidad(monkeypatch):
    # Ese mismo dia un 520 de Cloudflare se recupero al primer reintento. La
    # vuelta corta existe para eso.
    esperas, llamadas = _corre_rescate(monkeypatch, estado=520, veces=1)
    carrefour.main()
    assert esperas == [carrefour.ESPERA_SIN_BLOQUEO]
    assert llamadas["n"] == 2          # la mala y la buena


def test_un_bloqueo_de_verdad_si_se_espera_con_paciencia(monkeypatch):
    # Un 403 es un muro, y un muro se levanta solo: ahi la media hora vale.
    esperas, _ = _corre_rescate(monkeypatch, estado=403)
    carrefour.main()
    assert esperas == [120, 240, 480, 960]


def test_las_que_quedan_por_un_bloqueo_total_cuentan_como_bloqueadas(monkeypatch):
    """Las que ni se llegan a pedir tambien merecen la espera larga.

    Al cortar el recorrido por bloqueo total, las categorias restantes pasan al
    rescate sin haber fallado por su cuenta. Si se tomaran por "no bloqueadas",
    el corte del bloqueo se castigaria a si mismo con una espera de 30 segundos.
    """
    cats = [(f"cat{i}", "slug") for i in range(200)]
    esperas: list[int] = []

    def listado(f, cat_id, slug, offset):
        raise carrefour.HTTPStatusError(f"http://x/{cat_id}", 403, b"blocked")

    monkeypatch.setattr(carrefour, "listado", listado)
    monkeypatch.setattr(carrefour, "UMBRAL_BLOQUEO_TOTAL", 25)
    monkeypatch.setattr(carrefour, "categorias", lambda f: cats)
    monkeypatch.setattr(carrefour, "Fetcher", _FetcherDePrueba)
    monkeypatch.setattr(carrefour, "log_run", lambda *a, **k: None)
    monkeypatch.setattr(carrefour.time, "sleep", esperas.append)
    carrefour.main()
    assert esperas == [120, 240, 480, 960]


def test_el_reparto_de_motivos_se_lee_de_un_vistazo():
    fallidas = [("a", "s"), ("b", "s"), ("c", "s"), ("d", "s")]
    motivos = {"a": 500, "b": 500, "c": 500, "d": 0}
    assert carrefour._por_que_fallan(fallidas, motivos) == (
        "3 con HTTP 500, 1 sin respuesta")


def test_el_rescate_no_estrena_sesion(monkeypatch):
    """El rescate hereda la sesion del recorrido, no estrena una.

    El 20 de septiembre de 2026 el recorrido entero fue limpio (cero 403) y la
    primera vuelta del rescate, con sesion nueva y dos minutos despues, se
    llevo 403 en las cuatro categorias. La segunda vuelta, tambien con sesion
    nueva pero mas tarde y mas despacio, paso sin problema: o sea que estrenar
    sesion no basta por si solo para que te bloqueen y la causa no quedo
    probada.

    Aun asi, las cookies que el recorrido se gana solo pueden ayudar, y tirarlas
    para ir mas despacio no tiene ninguna logica. Esta prueba fija eso como
    invariante: una sesion por ejecucion.
    """
    _corre_rescate(monkeypatch, estado=403)
    carrefour.main()
    assert len(_FetcherDePrueba.creados) == 1, "el rescate ha estrenado sesion"
    fetcher = _FetcherDePrueba.creados[0]
    # El ritmo si baja en cada vuelta: la mitad, un cuarto, un octavo...
    assert fetcher.ritmos[1:] == [carrefour.config.RITMO["carrefour"] / 2 ** v
                                  for v in range(1, 5)]


def test_el_rescate_espera_el_doble_cada_vuelta(monkeypatch):
    """Media hora de margen en total, porque doce minutos no daban.

    Medido los dos dias que Cloudflare bloqueo de verdad: 20 minutos el 18 de
    septiembre de 2026 y 15 el 19. Con las tres vueltas de antes (2, 4 y 6
    minutos) el rescate se acababa con el muro todavia puesto las dos veces.
    """
    esperas = [carrefour.ESPERA_ENTRE_VUELTAS * 2 ** (v - 1)
               for v in range(1, carrefour.VUELTAS_DE_RESCATE + 1)]
    assert esperas == [120, 240, 480, 960]
    assert sum(esperas) / 60 == 30


# --- categorias que ya no existen y sirven la de su padre ------------------
#
# Una categoria difunta de Carrefour no da 404: devuelve **el catalogo de su
# padre**, con su navigation_id dentro y su paginacion entera. Sin mirarlo, se
# recorren las 42 paginas del padre otra vez, y otra por cada hija difunta.
#
# Medido sobre el crudo del 19 de septiembre de 2026: **531 de 2.634 paginas, el
# 20 % de todo lo que se pidio ese dia**. El caso gordo, `cat20001`: 462 paginas
# servidas para 1.008 productos, o sea 420 repetidas.

def _html_con_navegacion(nav_id, items=1, total=1000):
    estado = {"criteo": {"plpData": {"results": {
                  "items": [{"product_id": f"p{i}"} for i in range(items)]}}},
              "pagination": {"total_results": total}}
    return (f'<script>window.__INITIAL_STATE__={json.dumps(estado)}</script>'
            f'<script>var x={{"navigation_id":"{nav_id}"}};</script>').encode()


def test_se_lee_la_categoria_que_de_verdad_han_servido():
    r = carrefour._lee_listado(_html_con_navegacion("cat20013"), "cat21635562", 0)
    assert r["servida"] == "cat20013"


def test_si_coincide_no_hay_redireccion():
    r = carrefour._lee_listado(_html_con_navegacion("cat20013"), "cat20013", 0)
    assert r["servida"] == "cat20013"


def test_una_pagina_sin_navigation_id_no_inventa_redireccion():
    estado = {"criteo": {"plpData": {"results": {"items": []}}}}
    cuerpo = f'window.__INITIAL_STATE__={json.dumps(estado)}'.encode()
    assert carrefour._lee_listado(cuerpo, "cat20013", 0)["servida"] is None


def test_la_redirigida_se_deja_de_paginar(monkeypatch, capsys):
    """462 paginas para 1.008 productos: el caso real de cat20001."""
    pedidas = []

    def listado(f, cat_id, slug, offset):
        pedidas.append((cat_id, offset))
        # todo lo que se pida bajo cat99 lo sirve cat20013
        servida = "cat20013" if cat_id == "cat99" else cat_id
        return {"items": [{"product_id": f"{servida}-{offset}"}], "total": 1000,
                "eans": {}, "promos": {}, "servida": servida}

    monkeypatch.setattr(carrefour, "listado", listado)
    monkeypatch.setattr(carrefour, "categorias", lambda f: [("cat99", "slug")])
    monkeypatch.setattr(carrefour, "Fetcher", _FetcherDePrueba)
    monkeypatch.setattr(carrefour, "log_run", lambda *a, **k: None)
    monkeypatch.setattr(carrefour, "VUELTAS_DE_RESCATE", 0)
    carrefour.main()

    # Una sola peticion, no las 42 que diria `total`.
    assert pedidas == [("cat99", 0)]
    assert "redirigen a la de su padre" in capsys.readouterr().out


def test_un_cuerpo_cortado_se_vuelve_a_pedir_sin_cache(monkeypatch):
    """El fallo del 19 de septiembre: una pagina llego cortada (220.978 de los
    ~468.000 caracteres), el objeto de JavaScript no cerraba, y el cuerpo malo
    **se habia guardado en el crudo del dia**. Las tres vueltas de rescate lo
    releyeron de disco y fallaron igual, sin tocar la red. La categoria se perdio
    por una descarga cortada que nadie volvio a pedir."""
    llamadas = []
    cortado = b'window.__INITIAL_STATE__={"criteo":{"plpData":{"results":{"items":['
    entero = _html_con_navegacion("cat20013", items=2)

    def raw(f, url, clave, *, sin_cache=False):
        llamadas.append(sin_cache)
        return entero if sin_cache else cortado

    monkeypatch.setattr(carrefour, "_raw", raw)
    r = carrefour.listado(object(), "cat20013", "slug", 0)

    assert llamadas == [False, True], "tiene que reintentar saltandose la cache"
    assert len(r["items"]) == 2


def test_si_tambien_falla_sin_cache_se_da_por_perdida(monkeypatch):
    cortado = b'window.__INITIAL_STATE__={"a":'
    monkeypatch.setattr(carrefour, "_raw",
                        lambda f, url, clave, *, sin_cache=False: cortado)
    with pytest.raises(ValueError):
        carrefour.listado(object(), "cat20013", "slug", 0)


def test_el_log_cuenta_las_vueltas_que_dio_no_las_que_caben(monkeypatch, capsys):
    """El 21 de septiembre de 2026 dio una vuelta y el log dijo cuatro.

    El mensaje leia `VUELTAS_DE_RESCATE` en vez de contar, y desde que el
    rescate puede pararse pronto eso es una cifra inventada dentro de un log de
    operacion, que es de donde se sacan las conclusiones del dia siguiente.
    """
    esperas, _ = _corre_rescate(monkeypatch, estado=500)
    carrefour.main()
    salida = capsys.readouterr().out
    assert "despues de 1 vuelta de rescate" in salida
    assert "4 vueltas" not in salida
    assert len(esperas) == 1


def test_sin_fallos_no_se_habla_de_vueltas(monkeypatch, capsys):
    _corre_rescate(monkeypatch, estado=500, veces=0)
    carrefour.main()
    assert "de rescate" not in capsys.readouterr().out


def test_un_bloqueo_largo_cuenta_sus_cuatro_vueltas(monkeypatch, capsys):
    _corre_rescate(monkeypatch, estado=403)
    carrefour.main()
    assert "despues de 4 vueltas de rescate" in capsys.readouterr().out


# --- se acabaron las tolerancias ------------------------------------------
#
# Antes: hasta el 2 % de las categorías podía fallar y el día se daba por bueno.
# "3 errores dentro de la tolerancia de 13" no dice si el catálogo está entero,
# dice que hemos decidido no mirar.

def test_una_categoria_que_falla_y_no_esta_declarada_deja_la_captura_incompleta(
        monkeypatch, capsys):
    _corre_rescate(monkeypatch, estado=500, cuantas=200)
    assert carrefour.main() == 1, "una captura con huecos no puede salir a gold"
    salida = capsys.readouterr().out
    assert "NO esta completa" in salida
    assert "tolerancia" not in salida


def test_una_rota_declarada_no_hace_fallar_el_dia(monkeypatch, capsys):
    """Papelería lleva rota en el propio Carrefour desde el 20 de septiembre.

    Exigir cero errores ahí congelaría el catálogo para siempre, que es peor
    que el problema. Se perdona **esa**, con su nombre y su fecha, no "hasta N".
    """
    monkeypatch.setattr(carrefour, "ROTAS_EN_ORIGEN",
                        {"cat0": "de prueba, rota desde siempre"})
    _corre_rescate(monkeypatch, estado=500, cuantas=200)
    assert carrefour.main() == 0
    salida = capsys.readouterr().out
    assert "rotas en el propio Carrefour" in salida
    assert "NO esta completa" not in salida


def test_perdonar_una_no_es_perdonar_cualquiera(monkeypatch, capsys):
    """La diferencia entre una excepción declarada y una franquicia anónima."""
    monkeypatch.setattr(carrefour, "ROTAS_EN_ORIGEN",
                        {"cat99": "otra distinta, no la que falla"})
    _corre_rescate(monkeypatch, estado=500, cuantas=200)
    assert carrefour.main() == 1
    assert "NO esta completa" in capsys.readouterr().out


def test_una_rota_que_revive_se_manda_quitar_de_la_lista(monkeypatch, capsys):
    """Una lista de excepciones donde nada sale nunca acaba siendo una excusa."""
    monkeypatch.setattr(carrefour, "ROTAS_EN_ORIGEN",
                        {"cat1": "ya no falla, tendria que salir"})
    _corre_rescate(monkeypatch, estado=500, cuantas=200)
    carrefour.main()
    assert "ya funcionan" in capsys.readouterr().out
