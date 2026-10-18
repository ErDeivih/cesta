"""*** LA MEDIDA DEL BANCO: que cuente lo que dice contar, y que no publique cifras vacias. ***

*Pruebas del medidor, no del banco.* *El banco son pares etiquetados; lo que aqui se comprueba es que
`banco_identidad.mide()` cuenta bien lo que `identidad.decide()` hace -- incluido el caso que la
especificacion prohibe publicar: **una precision sobre cero decisiones**.*
"""

from __future__ import annotations

from core import banco_identidad, identidad


def _p(nombre: str, gtin: str | None = None, marca: str | None = None,
       fuente: str = "ensayo", id_fuente: str = "x") -> identidad.Producto:
    return identidad.Producto(fuente=fuente, id_fuente=id_fuente, nombre=nombre,
                              marca=marca, gtin=gtin)


def test_un_par_igual_con_el_mismo_gtin_cuenta_como_acierto():
    a = _p("Leche entera 1 l", gtin="8412345678905", marca="Marca A")
    b = _p("Leche entera 1 l", gtin="8412345678905", marca="Marca A")
    r = banco_identidad.mide([{"a": a, "b": b, "cierto": True, "estrato": "dia/lacteo",
                               "quien": "prueba"}])
    g = r["global"]
    assert g["total"] == 1
    assert g["exactos"] == 1
    assert g["exactos_bien"] == 1
    # *Ningun falso exacto: la cifra que la especificacion pone por delante.*
    assert g["exactos_mal"] == 0
    assert g["precision"] == 1.0


def test_un_falso_exacto_se_cuenta_aparte_y_no_se_diluye():
    """*** El error caro: dos productos distintos dados por el mismo. ***

    *La especificacion pide «prioridad a evitar falsos exactos», asi que tiene su propio contador y no
    se mezcla con la precision general.*
    """
    a = _p("Arroz redondo 1 kg", gtin="8412345678905", marca="Marca A")
    b = _p("Arroz redondo 1 kg", gtin="8412345678905", marca="Marca A")
    r = banco_identidad.mide([{"a": a, "b": b, "cierto": False, "estrato": "dia/arroz",
                               "quien": "prueba"}])
    g = r["global"]
    assert g["exactos"] == 1
    assert g["exactos_bien"] == 0
    assert g["exactos_mal"] == 1, "un falso exacto no se conto"
    assert g["precision"] == 0.0


def test_la_abstencion_no_es_un_fallo_pero_se_publica_con_la_cobertura():
    """*Decir «no lo se» no es acertar ni fallar: es no mojarse.* *Y por eso la cobertura va al lado.*"""
    a = _p("Leche entera 1 l", gtin=None, marca="Marca A")
    b = _p("Leche semidesnatada 1 l", gtin=None, marca="Marca A")
    r = banco_identidad.mide([{"a": a, "b": b, "cierto": False, "estrato": "dia/lacteo",
                               "quien": "prueba"}])
    g = r["global"]
    assert g["exactos"] == 0
    # *Sin decisiones, la precision es `None` y NO `0.0`: no es que acierte el 0 %, es que no opino.*
    assert g["precision"] is None
    assert g["cobertura"] is not None


def test_la_medida_dice_cuando_no_sirve():
    """*Un banco vacio, o con todo en cuarentena, da cifras que no valen.* *Y se dice en palabras.*"""
    vacio = banco_identidad.mide([])
    assert vacio["sirve"]["vale"] is False
    assert "vacio" in vacio["sirve"]["motivo"]

    a = _p("Leche entera 1 l", gtin=None, marca="Marca A")
    b = _p("Leche semidesnatada 1 l", gtin=None, marca="Marca A")
    todo_abstiene = banco_identidad.mide(
        [{"a": a, "b": b, "cierto": False, "estrato": "e", "quien": "prueba"} for _ in range(10)])
    assert todo_abstiene["sirve"]["vale"] is False
    assert "no dijo" in todo_abstiene["sirve"]["motivo"]


def test_la_matriz_y_los_estratos_se_publican_por_separado():
    """*Una media sola esconde que casi todos los pares son faciles.*"""
    facil_a = _p("Leche 1 l", gtin="8412345678905", marca="M")
    facil_b = _p("Leche 1 l", gtin="8412345678905", marca="M")
    pares = [
        {"a": facil_a, "b": facil_b, "cierto": True, "estrato": "facil", "quien": "prueba"},
        {"a": facil_a, "b": facil_b, "cierto": True, "estrato": "facil", "quien": "prueba"},
        {"a": _p("Pan", gtin=None, marca=None), "b": _p("Pan integral", gtin=None, marca=None),
         "cierto": False, "estrato": "dificil", "quien": "prueba"},
    ]
    r = banco_identidad.mide(pares)
    assert r["global"]["total"] == 3
    assert set(r["por_estrato"]) == {"facil", "dificil"}
    assert r["por_estrato"]["facil"]["total"] == 2
    assert r["por_estrato"]["dificil"]["total"] == 1
    # *Y la procedencia, que la especificacion exige.*
    assert r["procedencias"] == {"prueba": 3}
    # *La matriz dice que estados salieron en cada estrato, no solo cuantos acerto.*
    assert r["por_estrato"]["facil"]["matriz"]
