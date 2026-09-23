"""Encontrar con faltas de ortografia: lo que el encargo pide y no habia.

`docs/ENCARGO-UX-23SEP.md` §8, «los detalles que hacen que parezca terminada»: *"que
encuentre con faltas de ortografia y sin tildes (ya se normaliza en el dato)"*. Las tildes
y las mayusculas si se normalizaban; **una letra cambiada devolvia cero resultados**.
Medido contra la API viva el 23 de septiembre de 2026:

    leche entera   -> 3 resultados
    lece entera    -> 0
    leche entea    -> 0
    detergnete     -> 0
    asucar         -> 0

Lo que se vigila aqui, y cada cosa por su motivo:

  - **Que corrija** lo que tiene un arreglo: `lece entera` -> `leche entera`, `asucar` ->
    `azucar`, `detergnete` -> `detergente`.
  - **Que no toque lo que ya esta bien**, ni se invente nada cuando no hay un candidato
    razonable. Un buscador que "arregla" `xyzzy` a lo que sea es peor que uno que dice que
    no encuentra.
  - **Que el mismo tamano y la frecuencia decidan**, que son las dos reglas que evitan
    los dos fallos medidos: `asucar` -> `asua` (una palabra mas corta que empieza igual) y
    `natral` -> `natrual` (una errata que existe una vez en una ficha del catalogo).
  - **Que sea el ultimo recurso**: primero se busca lo escrito, y la correccion solo entra
    cuando no hay nada. Ademas de no gastar, evita el disparate de "corregir" una palabra
    que si tenia resultados.
  - **Que la respuesta diga lo que se ha entendido**, y **solo si ha servido**: anunciar
    una correccion que tampoco encuentra nada seria culpar a quien escribe.

El gold es de mentira: una prueba que dependa del catalogo del dia mide el calendario.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

from plataforma.api import catalogo, main

RAIZ = Path(__file__).resolve().parents[1]
BUSCAR = RAIZ / "plataforma" / "web" / "app" / "src" / "paginas" / "Buscar.tsx"

# `natural` aparece cuatro veces y `natrual` **una**: esa errata existe de verdad en el
# catalogo, y es la que hace falta para probar el desempate por frecuencia.
PRODUCTOS = [
    "Yogur natural azucarado",
    "Yogur natural desnatado",
    "Yogur natural sin lactosa",
    "Yogur natural entero",
    "Yogur natrual de fresa",
    "Leche entera",
    "Leche entera brik",
    "Azucar blanquilla",
    "Detergente liquido",
]


@pytest.fixture
def gold(tmp_path, monkeypatch):
    def escribe(productos=PRODUCTOS):
        con = duckdb.connect()
        con.execute("""CREATE TABLE g (
            grupo_id BIGINT, fuente VARCHAR, id_fuente VARCHAR, nombre VARCHAR,
            marca VARCHAR, cantidad DOUBLE, unidad_canon VARCHAR, precio_cent BIGINT,
            precio_unidad_cent DOUBLE, comparacion_fiable BOOLEAN, calidad VARCHAR,
            calidad_origen VARCHAR, nutriscore VARCHAR, nova BIGINT, ean VARCHAR,
            imagen VARCHAR, promo_txt VARCHAR)""")
        for i, nombre in enumerate(productos):
            con.execute("INSERT INTO g VALUES (?, 'aldi', ?, ?, NULL, 1.0, 'l', 100,"
                        " 100.0, true, NULL, NULL, NULL, NULL, NULL, NULL, NULL)",
                        [i + 1, str(i), nombre])
        con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
        for otro in ("precio_diario", "enlaces", "resumen", "precio_derivado"):
            con.execute(f"COPY (SELECT DATE '2026-09-23' AS fecha) "
                        f"TO '{tmp_path / (otro + '.parquet')}' (FORMAT PARQUET)")
        con.close()
        catalogo.reiniciar()

    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    yield escribe
    catalogo.reiniciar()


# ------------------------------------------------------------ la correccion ---

def test_arregla_las_palabras_que_tienen_arreglo(gold):
    gold()
    assert catalogo.corregir("lece entera") == "leche entera"
    assert catalogo.corregir("leche entea") == "leche entera"
    assert catalogo.corregir("detergnete") == "detergente"
    assert catalogo.corregir("azucar blanqulla") == "azucar blanquilla"


def test_no_toca_lo_que_ya_esta_bien(gold):
    """Corregir es idempotente: lo que existe no se cambia."""
    gold()
    for bien in ("leche entera", "detergente", "azucar"):
        assert catalogo.corregir(bien) is None, f"ha tocado {bien!r}, que esta bien escrito"


def test_no_se_inventa_nada_cuando_no_hay_candidato(gold):
    gold()
    assert catalogo.corregir("xyzzy") is None
    assert catalogo.corregir("qwertyuiop") is None
    # Y una palabra corta no se toca: con tres letras, un cambio de letra es otra
    # palabra cualquiera, y acertar es cuestion de suerte.
    assert catalogo.corregir("pan") is None


def test_el_mismo_tamano_evita_la_palabra_corta_que_empieza_igual(gold):
    """`asucar` -> `azucar`, y **no** `asua`.

    El parecido de Jaro-Winkler premia los prefijos, asi que sin exigir el mismo tamano
    gana la palabra corta que empieza igual. Medido sobre el catalogo de verdad:
    `asua` 0,922, `asar` 0,911, `azucar` 0,900. Cambiar `asucar` por `asua` es peor que
    no corregir.
    """
    gold()
    assert catalogo.corregir("asucar") == "azucar"


def test_a_igualdad_de_parecido_gana_la_palabra_que_mas_aparece(gold):
    """`natral` -> `natural`, y no `natrual`.

    `natrual` existe en el catalogo **una** vez (alguien la escribio mal en su ficha) y
    empata casi exacto con `natural`, que aparece cuatro. El parecido redondeado a dos
    decimales agrupa a los que empatan de verdad y ahi manda la frecuencia: es lo que
    distingue una palabra de la errata de una tienda.
    """
    gold()
    assert catalogo.corregir("yogur natral") == "yogur natural"


# --------------------------------------------------------------- la ruta ---

def test_la_correccion_es_el_ultimo_recurso_y_solo_si_sirve(gold, monkeypatch):
    """Primero lo escrito; y si tampoco, se dice -- pero solo si ha servido."""
    gold()
    llamadas: list[str] = []

    def falso_buscar(q, *a, **k):
        llamadas.append(q)
        return [{"grupo_id": 1, "nombre": "Leche entera"}] if q == "leche entera" else []

    monkeypatch.setattr(catalogo, "buscar", falso_buscar)
    monkeypatch.setattr(catalogo, "corregir", lambda q: "leche entera")
    cliente = TestClient(main.app)

    cuerpo = cliente.get("/api/buscar", params={"q": "lece entera"}).json()
    assert llamadas == ["lece entera", "leche entera"], (
        "hay que buscar primero lo escrito y solo despues lo corregido")
    assert cuerpo["corregido"] == "leche entera"
    assert cuerpo["resultados"]


def test_si_lo_corregido_tampoco_encuentra_nada_no_se_anuncia(gold, monkeypatch):
    """Anunciar una correccion que no sirve es culpar a quien escribe."""
    gold()
    monkeypatch.setattr(catalogo, "buscar", lambda q, *a, **k: [])
    monkeypatch.setattr(catalogo, "corregir", lambda q: "otra cosa")
    cliente = TestClient(main.app)

    cuerpo = cliente.get("/api/buscar", params={"q": "xyzzy"}).json()
    assert cuerpo["resultados"] == []
    assert "corregido" not in cuerpo


def test_si_lo_escrito_encuentra_algo_no_se_corrige_nada(gold, monkeypatch):
    gold()
    llamadas: list[str] = []

    def falso_buscar(q, *a, **k):
        llamadas.append(q)
        return [{"grupo_id": 1, "nombre": "Lo que sea"}]

    monkeypatch.setattr(catalogo, "buscar", falso_buscar)
    monkeypatch.setattr(catalogo, "corregir",
                        lambda q: pytest.fail("no se puede corregir si ya hay resultados"))
    cliente = TestClient(main.app)

    cuerpo = cliente.get("/api/buscar", params={"q": "leche"}).json()
    assert llamadas == ["leche"]
    assert "corregido" not in cuerpo


# ------------------------------------------------------------ la pantalla ---

def test_la_pantalla_dice_lo_que_ha_entendido():
    buscar = BUSCAR.read_text(encoding="utf-8")
    assert "resultados.data.corregido" in buscar, \
        "sin decirlo, quien escribe 'asucar' no sabe si le han entendido"
    assert "Esto es lo que" in buscar
    # Y se ensenan las dos cosas: lo que se escribio y lo que se ha entendido.
    assert "filtros.q.trim()" in buscar
