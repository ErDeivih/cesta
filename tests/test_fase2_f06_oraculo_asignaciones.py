"""F06 (fase 2): **el oraculo exhaustivo de asignaciones**, contra el optimizador.

Por que existe
--------------
Es lo que pide el hallazgo: *«oraculo exhaustivo independiente de asignaciones y promociones
condicionadas al conjunto»*. Y lo que F06 exige de el: *«casos combinatorios con contraejemplos,
**discrepancias cero** para escenarios cubiertos, **suma de partes igual al total**»*.

El oraculo es `core/oraculo_reparto.py`. **No importa nada de `cesta.py`**: ni el optimizador, ni la
aritmetica de promociones, ni la agrupacion. *Si los dos coinciden, es porque los dos calculan bien.*

*Y se prueba primero el oraculo solo.* **Un oraculo que no se comprueba no es un oraculo: es otra
opinion.** Si el oraculo se equivoca, la discrepancia que encuentre no dice nada del motor.
"""
from __future__ import annotations

import random

import pytest

from core.oraculo_reparto import SIN_OFERTA, Linea, Oferta, coste_del_conjunto, oraculo
from core.promos import lee as lee_promo
from plataforma.api import cesta

# ---------------------------------------------------------------------------------------------
# 1. El oraculo, contra cuentas hechas a mano.
# ---------------------------------------------------------------------------------------------


def test_la_aritmetica_del_oraculo_es_la_que_se_le_pide():
    """**Sin esto, lo demas no vale.** *Las mismas cuentas que `core/promos.py` documenta.*

    3x2 sobre 3 unidades a 1 EUR son 2,00; la 2a unidad al 50 % sobre 2 son 1,50; y el lote de dos
    por tres euros, 3,00.
    """
    assert Oferta("nxm", 3, 2).coste(3, 100) == 200
    assert Oferta("nxm", 3, 2).coste(6, 100) == 400
    assert Oferta("nxm", 3, 2).coste(2, 100) == 200, "sin llegar a tres no hay oferta"
    assert Oferta("enesima", 2, 50).coste(2, 100) == 150
    assert Oferta("porcentaje", 0, 25).coste(4, 100) == 300
    assert Oferta("lote", 2, 300).coste(2, 100) == 300
    assert Oferta("lote", 2, 300).coste(3, 100) == 400, "dos por tres euros, y la tercera suelta"
    assert Oferta("precio_fijo", 129).coste(3, 200) == 387
    assert Oferta("descuento_fijo", 50).coste(3, 100) == 150
    assert SIN_OFERTA.coste(3, 100) == 300


def test_el_parser_del_motor_y_el_oraculo_hablan_de_la_misma_oferta():
    """*El oraculo no lee castellano de folleto: recibe la mecanica ya leida.*

    Por eso hay que comprobar que **la mecanica que se le da es la que el motor lee del texto**; si no,
    la comparacion estaria enfrentando dos ofertas distintas y llamandolo discrepancia.
    """
    iguales = {
        "3x2": Oferta("nxm", 3, 2),
        "2a unidad -50%": Oferta("enesima", 2, 50),
        "-25%": Oferta("porcentaje", 0, 25),
        "2 UDS POR 3 EUR": Oferta("lote", 2, 300),
    }
    for texto, esperada in iguales.items():
        leida = lee_promo(texto)
        assert (leida.tipo, leida.a, leida.b) == (esperada.tipo, esperada.a, esperada.b), (
            f"el motor lee {texto!r} como {(leida.tipo, leida.a, leida.b)} y el oraculo usa "
            f"{(esperada.tipo, esperada.a, esperada.b)}")


def test_el_oraculo_agrupa_por_producto_dentro_de_la_tienda():
    """**La propiedad que F06 exige: la suma de las partes es el total.**

    *Cuatro unidades del mismo producto con 3x2 son 3,00 EUR, no dos lineas de 2,00.*
    """
    lineas = [(Linea("l1", "p1", 2), 100, Oferta("nxm", 3, 2)),
              (Linea("l2", "p1", 2), 100, Oferta("nxm", 3, 2))]
    assert coste_del_conjunto(lineas) == 300

    # Y dos productos distintos **no** se agrupan entre si: cada uno con su oferta.
    distintas = [(Linea("l1", "p1", 2), 100, Oferta("nxm", 3, 2)),
                 (Linea("l2", "p2", 2), 100, Oferta("nxm", 3, 2))]
    assert coste_del_conjunto(distintas) == 400, " 2 + 2 unidades no hacen un grupo de tres"


def test_el_oraculo_enumera_todas_las_asignaciones():
    """*Dos lineas y dos tiendas son cuatro asignaciones; con tope de una tienda, dos.*"""
    peticiones = [Linea("l1", "p1", 1), Linea("l2", "p2", 1)]
    oferta = {"alcampo": {"l1": (100, SIN_OFERTA), "l2": (100, SIN_OFERTA)},
              "dia": {"l1": (80, SIN_OFERTA), "l2": (80, SIN_OFERTA)}}

    con_dos = oraculo(peticiones, oferta, max_tiendas=2)
    assert con_dos["exhaustivo"] is True
    assert con_dos["asignaciones_vistas"] == 4, "2 lineas x 2 tiendas"
    assert con_dos["total_cent"] == 160, "las dos en dia, a 0,80"

    con_una = oraculo(peticiones, oferta, max_tiendas=1)
    assert con_una["asignaciones_vistas"] == 2, "solo las dos de una tienda"
    assert con_una["total_cent"] == 160
    assert con_una["reparto_dos_o_mas"] is None, "con tope de una tienda no hay reparto"


def test_una_linea_que_no_esta_en_una_tienda_no_se_puede_asignar_ahi():
    """*Un total al que le falta una linea no es un total: es otro numero.*

    **Y la respuesta del oraculo es 110, no 160**, que es justo lo que hay que ver: `l2` no esta en
    alcampo, asi que *no se puede* mandar alli; pero `l1` si, y el trozo mas barato es **partir** --
    l1 a alcampo por 1,00 y l2 a dia por 0,10.
    """
    peticiones = [Linea("l1", "p1", 1), Linea("l2", "p2", 1)]
    oferta = {"alcampo": {"l1": (100, SIN_OFERTA)},          # l2 no esta en alcampo
              "dia": {"l1": (150, SIN_OFERTA), "l2": (10, SIN_OFERTA)}}

    salida = oraculo(peticiones, oferta, max_tiendas=2)
    assert salida["total_cent"] == 110, "l1 a alcampo (1,00) y l2 a dia (0,10)"
    assert salida["asignacion"] == {"l1": "alcampo", "l2": "dia"}
    # **Ninguna asignacion manda l2 a alcampo**: no es que salga caro, es que no se puede comprar.
    assert salida["asignacion"]["l2"] != "alcampo"

    # Y con tope de una sola tienda, el unico sitio donde caben las dos es dia.
    con_una = oraculo(peticiones, oferta, max_tiendas=1)
    assert con_una["total_cent"] == 160, "las dos en dia: 1,50 + 0,10"
    assert con_una["cadenas"] == ["dia"]


# ---------------------------------------------------------------------------------------------
# 2. El oraculo contra el optimizador.
# ---------------------------------------------------------------------------------------------


def _eleccion(linea_id, producto_id, fuente, cantidad, precio, texto_promo):
    """Una eleccion como la que devuelve `_resolver`: **coste de la linea, sin agrupar**."""
    oferta = lee_promo(texto_promo) if texto_promo else None
    propio = oferta.coste(cantidad, precio) if oferta else cantidad * precio
    return cesta.Eleccion(producto_id, f"Producto {producto_id}", fuente, cantidad, propio,
                          cantidad * precio, texto_promo, None, linea_id=linea_id,
                          identidad="exacto", autorizada=True)


def _compara(monkeypatch, peticiones, oferta, max_tiendas=2):
    """Corre los dos y devuelve **la misma pregunta contestada por cada uno**.

    No se compara «el reparto del motor» contra «el mejor reparto posible»: son preguntas distintas, y
    el motor puede -- y debe -- devolver `None` cuando partir no ahorra. *La pregunta que importa es
    **si el motor propone el optimo de verdad**, que es lo que F06 exige con «discrepancias cero».*
    """
    def resuelve(p, fuente, mejor):
        """El `_resolver` de verdad: **`None` cuando esa linea no esta en esa tienda**."""
        sitio = oferta.get(fuente, {}).get(p.id)
        if sitio is None:
            return None
        return _eleccion(p.id, p.nombre, fuente, p.cantidad, sitio[0], _TEXTOS[sitio[1].tipo])

    monkeypatch.setattr(cesta, "_candidatos", lambda *a, **k: {})
    monkeypatch.setattr(cesta, "_resolver", resuelve)
    motor = cesta.donde_comprar(peticiones, sorted(oferta), max_tiendas=max_tiendas)

    lineas = [Linea(p.id, p.nombre, p.cantidad) for p in peticiones]
    verdad = oraculo(lineas, oferta, max_tiendas=max_tiendas)

    # La mejor tienda sola, segun el oraculo: solo donde quepan **todas** las lineas.
    unas_verdad = [coste_del_conjunto([(ln, oferta[cadena][ln.linea_id][0],
                                        oferta[cadena][ln.linea_id][1]) for ln in lineas])
                   for cadena in sorted(oferta)
                   if all(ln.linea_id in oferta[cadena] for ln in lineas)]

    unas_motor = [x["total_cent"] for x in motor["una_tienda"] if not x["faltan"]]
    dos_motor = motor["repartido"]["total_cent"] if motor["repartido"] else None
    candidatos = unas_motor + ([dos_motor] if dos_motor is not None else [])

    return {
        "motor_mejor": min(candidatos) if candidatos else None,
        "motor_una": min(unas_motor) if unas_motor else None,
        "motor_dos": dos_motor,
        "verdad_mejor": verdad["total_cent"],
        "verdad_una": min(unas_verdad) if unas_verdad else None,
        "verdad_dos": verdad["reparto_dos_o_mas"]["total_cent"] if verdad["reparto_dos_o_mas"] else None,
        "motor": motor, "oraculo": verdad,
    }


# El texto que el motor lee para cada mecanica del oraculo.
_TEXTOS = {"nxm": "3x2", "enesima": "2a unidad -50%", "porcentaje": "-25%", "lote": "2 UDS POR 3 EUR",
           "sin_regla": "", "precio_fijo": "Todo a 1,29 EUR", "descuento_fijo": "50 EUR dto"}


def _peticion(pid, cantidad):
    return cesta.Peticion(grupo_id=1, producto_id=None, cantidad=cantidad, nombre=pid, id=pid)


# **Los escenarios.** Cada uno con su oferta por tienda y linea, y el oraculo los recorre todos.
ESCENARIOS = {
    "oferta_en_una_tienda_y_precio_en_la_otra": {
        "peticiones": [("p1", 2), ("p2", 1)],
        "oferta": {"alcampo": {"p1": (100, Oferta("nxm", 3, 2)), "p2": (100, Oferta("nxm", 3, 2))},
                   "dia": {"p1": (80, SIN_OFERTA), "p2": (50, SIN_OFERTA)}},
    },
    "el_mismo_producto_en_dos_lineas": {
        "peticiones": [("p1", 2), ("p1", 2), ("p2", 1)],
        "oferta": {"alcampo": {"p1": (100, Oferta("nxm", 3, 2)), "p2": (100, Oferta("nxm", 3, 2))},
                   "dia": {"p1": (70, SIN_OFERTA), "p2": (50, SIN_OFERTA)}},
    },
    "tres_tiendas_y_una_linea_que_falta_en_una": {
        "peticiones": [("p1", 2), ("p2", 1)],
        "oferta": {"alcampo": {"p1": (100, Oferta("nxm", 3, 2)), "p2": (100, SIN_OFERTA)},
                   "dia": {"p1": (80, SIN_OFERTA), "p2": (50, SIN_OFERTA)},
                   "aldi": {"p1": (90, Oferta("enesima", 2, 50))}},
    },
    "descuento_por_porcentaje_contra_oferta_de_cantidad": {
        "peticiones": [("p1", 3), ("p2", 2)],
        "oferta": {"alcampo": {"p1": (120, Oferta("nxm", 3, 2)), "p2": (200, Oferta("porcentaje", 0, 25))},
                   "dia": {"p1": (100, SIN_OFERTA), "p2": (180, SIN_OFERTA)}},
    },
}


def _monta(escenario):
    peticiones = [_peticion(pid, cantidad) for pid, cantidad in escenario["peticiones"]]
    # **Dos lineas del mismo producto se distinguen por su id**, y el oraculo las trata por separado.
    vistos: dict[str, int] = {}
    for p in peticiones:
        vistos[p.id] = vistos.get(p.id, 0) + 1
        if vistos[p.id] > 1:
            p.id = f"{p.id}#{vistos[p.id]}"
    oferta: dict[str, dict[str, tuple[int, Oferta]]] = {}
    for cadena, por_linea in escenario["oferta"].items():
        oferta[cadena] = {}
        for clave, (precio, mecanica) in por_linea.items():
            for p in peticiones:
                if p.id.split("#")[0] == clave:
                    oferta[cadena][p.id] = (precio, mecanica)
    return peticiones, oferta


def test_una_sola_tienda_coincide(monkeypatch):
    """*El caso facil primero.* Con una sola tienda el motor ya recorria todas y agrupaba."""
    for nombre, escenario in ESCENARIOS.items():
        peticiones, oferta = _monta(escenario)
        salida = _compara(monkeypatch, peticiones, oferta)
        assert salida["motor_una"] == salida["verdad_una"], (
            f"[{nombre}] una tienda: el motor dice {salida['motor_una']} y la verdad es "
            f"{salida['verdad_una']}")


def test_el_motor_propone_el_optimo(monkeypatch):
    """**El criterio de F06**: discrepancias cero contra un oraculo exhaustivo.

    *No se compara el reparto del motor contra el mejor reparto posible* -- son preguntas distintas, y
    el motor debe devolver `None` cuando partir no ahorra --, **sino su mejor propuesta contra el
    optimo de verdad.** Si el motor propone algo mas caro que lo que existe, se le esta diciendo a
    quien compra que pague mas.
    """
    discrepancias = []
    for nombre, escenario in ESCENARIOS.items():
        peticiones, oferta = _monta(escenario)
        salida = _compara(monkeypatch, peticiones, oferta)
        if salida["motor_mejor"] != salida["verdad_mejor"]:
            discrepancias.append(
                f"[{nombre}] el motor propone {salida['motor_mejor']} y el optimo es "
                f"{salida['verdad_mejor']} (una tienda {salida['motor_una']}, reparto "
                f"{salida['motor_dos']}; verdad una tienda {salida['verdad_una']}, reparto "
                f"{salida['verdad_dos']})")

    assert not discrepancias, "discrepancias contra el oraculo:\n  " + "\n  ".join(discrepancias)


# ---------------------------------------------------------------------------------------------
# 3. Y no cuatro casos hechos a mano: un barrido con semilla fija.
# ---------------------------------------------------------------------------------------------

# **El precio y la oferta van por tienda y producto, no por linea.** *Dos lineas del mismo producto en
# la misma tienda cuestan lo mismo -- es lo real --, y ademas quita de en medio la ambiguedad de que el
# motor y el oraculo pudieran estar leyendo precios distintos para el mismo grupo.*
_MECANICAS = [SIN_OFERTA, Oferta("nxm", 3, 2), Oferta("enesima", 2, 50), Oferta("porcentaje", 0, 25),
              Oferta("lote", 2, 300)]
_PRECIOS = [50, 70, 80, 100, 120, 150, 200]


def _al_azar(rnd):
    cadenas = ["alcampo", "dia", "aldi"][:rnd.randint(2, 3)]
    lineas = [(f"l{i + 1}", rnd.choice(["p1", "p2"]), rnd.randint(1, 3))
              for i in range(rnd.randint(2, 3))]

    oferta: dict[str, dict[str, tuple[int, Oferta]]] = {}
    for cadena in cadenas:
        oferta[cadena] = {}
        for pid in sorted({p for _l, p, _c in lineas}):
            if rnd.random() < 0.15:
                continue                      # ese producto no esta en esa tienda
            precio, mecanica = rnd.choice(_PRECIOS), rnd.choice(_MECANICAS)
            for lid, p, _c in lineas:
                if p == pid:
                    oferta[cadena][lid] = (precio, mecanica)

    peticiones = [cesta.Peticion(grupo_id=1, producto_id=None, cantidad=cantidad, nombre=pid, id=lid)
                  for lid, pid, cantidad in lineas]
    return peticiones, oferta


@pytest.mark.xfail(
    strict=True,
    reason=(
        "F06 (fase 2), hallazgo abierto: `_mejor_reparto` reparte con la **parte** que a cada linea le "
        "toca **suponiendo que todas las lineas van a esa tienda**, y esa parte solo existe si se "
        "queda. Medido el 13 de octubre de 2026: **9 discrepancias en 176 escenarios** (5%), todas con "
        "el motor mas caro que el optimo. El caso minimo: l1(p2,2u) a aldi, l2(p1,3u) y l3(p1,1u) en "
        "alcampo a 1,20 con 3x2 -- la parte de l3 en alcampo es 90 (frente a 100 en aldi) y por eso el "
        "motor la manda alli, pero esa parte de 90 sale de un grupo de 4 unidades que **solo se forma "
        "si l3 se queda**: con l3 fuera, alcampo son 240 y aldi 100, total 415 contra los 435 que "
        "propone. *Es la frase de F06 al pie de la letra: «no elegir partes de un descuento calculado "
        "sobre una cesta que al final no se compra en esa tienda»*. **Cuando se arregle -- enumerando "
        "asignaciones en cestas pequenas, o llamando heuristica a la heuristica -- esta prueba pasara "
        "y el `strict` obligara a quitar la marca.**"
    ),
)
def test_doscientos_escenarios_al_azar_coinciden(monkeypatch):
    """**«Discrepancias cero» con mayusculas.** *Cuatro casos elegidos a mano no demuestran nada: se
    eligen los que uno ya sabe que pasan.* Con semilla fija, para que un fallo se pueda reproducir.

    **Y es la prueba que encontro el defecto**: 9 escenarios de 176 donde el motor propone pagar mas de
    lo que hay. *Se deja marcada, no borrada ni rebajada: el criterio de F06 sigue siendo el criterio.*
    """
    rnd = random.Random(20261013)
    discrepancias = []
    casos = 0
    for _ in range(200):
        peticiones, oferta = _al_azar(rnd)
        if not oferta or any(not por_linea for por_linea in oferta.values()):
            continue
        casos += 1
        salida = _compara(monkeypatch, peticiones, oferta)
        if salida["motor_mejor"] != salida["verdad_mejor"]:
            discrepancias.append(
                f"lineas={[(p.id, p.nombre, p.cantidad) for p in peticiones]} oferta="
                f"{ {c: sorted(m) for c, m in oferta.items()} } -> motor {salida['motor_mejor']}, "
                f"optimo {salida['verdad_mejor']}")

    assert casos > 150, f"el barrido tiene que llegar a los casos: {casos}"
    assert not discrepancias, (
        f"{len(discrepancias)} discrepancias en {casos} escenarios:\n  " + "\n  ".join(discrepancias[:6]))
