"""**La ruta `/api/recetas/importar`, que no tenia ni un ensayo.**

*`tests/test_fase2_f09_fuente_permitida.py` tiene **diecinueve**, *y todos prueban **el modulo**
(`comprueba_fuente`, `lee_json_ld`, `borrador`).* *** Y ninguno pasa por el endpoint ***, *que es donde
viven **cuatro guardas**: *

  *-- *la **fuente** *(-- `comprueba_fuente`, *antes de leer nada --)*
  *-- *el **tiempo** *(-- `urlopen(..., timeout=10)` --)*
  *-- *el **tamaño** *(-- `r.read(2_000_000)` --)*
  *-- *y **las redirecciones**, *que es **lo que el plan pide y no esta** *(-- `urlopen` **las sigue**,
     *y **nadie comprueba a donde** --)*

*Y **el ultimo es un SSRF**: *una fuente permitida que redirija a `http://127.0.0.1:…` *se seguiria.*
**Aqui se mide**, *con un servidor de fixture local*, *en vez de afirmarlo leyendo `urlopen`.* *
"""
from __future__ import annotations

import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from starlette.testclient import TestClient

from core import importar_receta
from plataforma.api import almacen, main

#: *Una receta minima en `ld+json`, que es **el formato que el importador lee.***
RECETA = {
    "@context": "https://schema.org", "@type": "Recipe", "name": "Tortilla de patatas",
    "recipeYield": "4", "totalTime": "PT30M",
    "recipeIngredient": ["4 huevos", "500 g de patatas"],
}


def _pagina(receta: dict | None = RECETA) -> bytes:
    bloque = "" if receta is None else (
        '<script type="application/ld+json">' + json.dumps(receta) + "</script>")
    return f"<html><head>{bloque}</head><body>hola</body></html>".encode()


class _Servidor(HTTPServer):
    """*Un servidor de fixture: **sirve HTML, redirige, o falla**, segun se le diga.*"""

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _Manejador)
        self.modo = "receta"
        self.destino = ""
        self.hilo = threading.Thread(target=self.serve_forever, daemon=True)

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"

    def __enter__(self):
        self.hilo.start()
        return self

    def __exit__(self, *_: object):
        self.shutdown()
        self.server_close()


class _Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        modo = self.server.modo  # type: ignore[attr-defined]
        if modo == "redirige":
            self.send_response(302)
            self.send_header("Location", self.server.destino)  # type: ignore[attr-defined]
            self.end_headers()
            return
        if modo == "falla":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"vaya")
            return
        cuerpo = _pagina(None if modo == "sin_receta" else RECETA)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *_: object):
        """*Sin ruido en la salida de `pytest`.*"""


@pytest.fixture
def cliente():
    """*La ruta, con el usuario inyectado y **una fuente declarada**.*"""
    # *** Y el sello tiene que ser UNICO DE VERDAD. *** *
    #
    # *Con `int(time.time())` **chocaba**: *todos los ensayos del fichero **corren en el mismo
    # segundo**, *y **los usuarios viven en Postgres y no se borran.** *
    # *Lo dice el propio proyecto, en `test_revision_a09_compra_hogar.py`: *** «*El sello es
    # obligatorio*: *los usuarios viven en Postgres y **no se borran**, *asi que sin el, *el segundo
    # pase **choca con `UsuarioRepetido`**».** *
    almacen.arranca()
    yo = almacen.crea_usuario(f"importar-{uuid.uuid4().hex[:10]}", "Importar", "clave-de-prueba-123")
    main.app.dependency_overrides[main.usuario_actual] = lambda: yo
    antes = dict(importar_receta.FUENTES)
    try:
        yield TestClient(main.app)
    finally:
        importar_receta.FUENTES.clear()
        importar_receta.FUENTES.update(antes)
        main.app.dependency_overrides.clear()


def _declara(servidor: _Servidor) -> str:
    """*Declara la fuente como permitida, y devuelve su URL.*"""
    # *** Se declara el HOST, no el host con puerto. *** *
    # *`comprueba_fuente` mira `urlparse(url).hostname`, *y **`hostname` no lleva el puerto** --
    # *medido: declarando `127.0.0.1:PUERTO` la fuente quedaba **sin declarar** y la ruta devolvia
    # **400**; *y el ensayo del SSRF «pasaba» **por el motivo equivocado.** *
    importar_receta.FUENTES["127.0.0.1"] = "fixture del ensayo"
    return f"{servidor.base}/receta"


def test_una_fuente_no_declarada_se_rechaza_sin_leer(cliente, tmp_path):
    """*** 400, *con el motivo, *y **sin haber leido nada.** *** *

    *Y **el motivo dice cual**: *«la fuente no esta declarada: …»* *—* *que es **lo que permite decir
    «no puedo importar de ahi»** *en vez de «no he encontrado ninguna receta», *que son **dos cosas
    distintas y solo una es verdad.*** *
    """
    r = cliente.post("/api/recetas/importar", json={"url": "https://no-declarada.example/r"})
    assert r.status_code == 400, r.text
    assert "no esta declarada" in r.text or "no está declarada" in r.text, r.text


def test_la_pagina_sin_receta_es_422_y_no_el_400_de_la_fuente(cliente):
    """*** Y son **dos problemas distintos**, *y se dicen distinto.** *** *

    *La fuente **si vale**, *y **la pagina no trae** `ld+json` con `@type: Recipe`. *-- *que puede ser
    **que no sea una receta**, *o **que ese sitio no publique el estandar.*** *
    """
    with _Servidor() as s:
        s.modo = "sin_receta"
        url = _declara(s)
        r = cliente.post("/api/recetas/importar", json={"url": url})
        assert r.status_code == 422, r.text
        assert "ld+json" in r.text, r.text


def test_una_pagina_que_falla_es_502_y_lo_dice(cliente):
    """*Y **si la red falla**, *no se inventa nada: *se dice que no se pudo traer.*"""
    with _Servidor() as s:
        s.modo = "falla"
        url = _declara(s)
        r = cliente.post("/api/recetas/importar", json={"url": url})
        assert r.status_code == 502, r.text
        assert "No se pudo traer" in r.text, r.text


def test_la_receta_buena_sale_de_borrador_con_su_fuente_y_sin_guardar(cliente):
    """*** Y el camino bueno: *borrador, *con `fuente`, *y **`guardada: False`.** *** *

    *«**No se guarda**» es la mitad del contrato*, *y **`f09` ya comprueba que el borrador no escribe**;
    *esto comprueba que **la ruta tampoco lo dice de mas.*** *
    """
    with _Servidor() as s:
        url = _declara(s)
        r = cliente.post("/api/recetas/importar", json={"url": url})
        assert r.status_code == 200, r.text
        cuerpo = r.json()
        assert cuerpo["nombre"], cuerpo
        assert cuerpo["guardada"] is False, cuerpo
        assert cuerpo.get("fuente"), cuerpo


@pytest.mark.xfail(
    strict=True,
    reason="SSRF MEDIDO el 14/10/2026: `urlopen` sigue la redireccion y el destino no se comprueba, "
           "asi que una fuente declarada puede llevar a leer otra que no lo esta. "
           "Cuando se arregle -- comprobando `r.geturl()` con `comprueba_fuente`, o prohibiendo "
           "redirecciones -- este ensayo pasara y el `strict` avisara de que hay que quitar la marca.",
)
def test_una_fuente_permitida_que_redirige_a_OTRA_que_no_lo_esta(cliente):
    """*** EL NEGATIVO DEL SSRF: *y aqui se MIDE, *no se afirma.** *** *

    *El plan pide, en B07: *** «URL solo fuentes revisadas, guardas SSRF/*** redirecciones ***/tamaño/
    timeout».** *Y de las cuatro, *el **tiempo** y el **tamaño** estan en la ruta, *la **fuente** va
    primero, *y **las redirecciones**…* *

    *`urllib.request.urlopen` **sigue las redirecciones por defecto** *(-- hasta diez --), *y **el
    destino no se comprueba.** *Asi que si **una fuente declarada** redirige a `127.0.0.1`, *o a la
    metadata de la nube, *** se seguiria.*** *

    *** Y este ensayo dice lo que pasa hoy ***, *sin arreglarlo ni taparlo: *
      *-- *si da **400** -> *la guarda **ya cubre** el caso, *y **hay que decirlo**;*
      *-- *si da **200** -> *el SSRF es **real**, *y queda **medido.** *
    """
    with _Servidor() as s, _Servidor() as otro:
        # *El segundo servidor **no esta declarado**: es «otra fuente».*
        otro.modo = "sin_receta"
        s.modo = "redirige"
        # *** Y EL DESTINO TIENE QUE SER OTRO HOST, NO EL MISMO CON OTRO PUERTO. *** *
        #
        # *La primera version redirigia a `http://127.0.0.1:OTRO_PUERTO`, *y eso **no es un SSRF**:
        # `comprueba_fuente` mira `urlparse(url).hostname`, *y **`hostname` no lleva el puerto**, *
        # *asi que el destino **es la misma fuente declarada** *-- *y **seguirla es correcto.** *
        # *Por eso el ensayo daba **422** y parecia que la guarda fallaba: *fallaba **el ensayo.*** *
        #
        # *Con `localhost` si es **otro nombre**, *y **no esta declarado** *(-- solo lo esta
        # `127.0.0.1` --), *asi que aqui **si** se mide el SSRF.*
        s.destino = f"http://localhost:{otro.server_address[1]}/otra"
        url = _declara(s)
        r = cliente.post("/api/recetas/importar", json={"url": url})
        # *** Y lo que hay que saber no es «pasa o no»: es *** QUE CODIGO DA ***, *porque cada uno
        # significa una cosa distinta: *** *
        #   *-- *** 400 *** -> *la guarda **rechaza el destino**, *y **el SSRF esta cubierto** ✓
        #   *-- *** 422 *** -> *el importador **SIGUIO el redirect** *(-- *leyo el destino y no encontro
        #      receta --)* *** -> el SSRF ES REAL *** ⚠️
        #   *-- *** 502 *** -> *fue, *y **la pagina de destino fallo** *-> **tambien lo siguio** ⚠️
        #   *-- *** 200 *** -> *lo siguio **y ademas habia receta**: *el peor caso ⚠️
        print(f"   *** el redirect a una fuente NO declarada da: {r.status_code} ***")
        assert r.status_code in (400, 422, 502, 200), r.text
        if r.status_code != 400:
            pytest.fail(
                f"SSRF MEDIDO: una fuente declarada redirige a otra que NO lo esta ({otro.base}), "
                f"y el importador la sigue: da {r.status_code} y no 400")
