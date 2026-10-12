"""A08 — Envases enteros: el ejemplo del criterio, y los tres huecos que no son el mismo hueco.

**El defecto que esto arregla, medido el 12 de octubre de 2026.** *`core/previa_compra.py` pedia el tamano
del envase a `envases.lee`, que **devuelve `(tipo de envase, unidades del pack)`*** -- *asi que el
`isinstance(leido, dict)` era falso, `getattr(tupla, "cantidad")` daba `None`, **y `ln.envases` y
`ln.sobrante` no se calculaban nunca.***

*Y aunque se hubiera arreglado el `dict`, seguiria dando `None`: **`envases.lee` nunca devolvio un
tamano**.* **El tamano tiene que venir de la ficha del articulo elegido** -- *que es lo que A08 dice con
«usar tamano neto publicado del articulo elegido».*

**El criterio, palabra por palabra:** *«1,4 kg / envase 1 kg = dos envases y 0,6 kg sobrante; ausencia de
tamano produce desconocido, **no una compra fraccionaria inventada**».*
"""
from __future__ import annotations

import pytest

from core.envases_enteros import a_canonica, envases_enteros

# ================================================== EL EJEMPLO DEL CRITERIO ===

def test_el_ejemplo_de_a08_da_dos_envases_y_seiscientos_gramos():
    """**1,4 kg con envases de 1 kg -> dos envases y 0,6 kg sobrantes.**

    *Es el ejemplo que A08 escribe con numeros*, y por eso esta el primero: **si este no sale, lo demas da
    igual.** *Y el sobrante se mide en la base canonica -- 600 g --, porque es la unidad del envase.*
    """
    r = envases_enteros(1.4, "kg", 1, "kg")
    assert r["envases"] == 2, r
    assert r["sobrante"] == 600.0, r
    assert r["unidad"] == "g"
    assert r["motivo"] is None


def test_y_el_mismo_ejemplo_escrito_en_gramos_da_lo_mismo():
    """*1400 g con envases de 1000 g.* **La unidad en la que se escriba no puede cambiar el resultado.**
    """
    r = envases_enteros(1400, "g", 1000, "g")
    assert r["envases"] == 2
    assert r["sobrante"] == 600.0
    # *Y el mismo caso con una unidad a cada lado, que es lo que pasa de verdad en una lista.*
    assert envases_enteros(1400, "g", 1, "kg")["envases"] == 2
    assert envases_enteros(1.4, "kg", 1000, "g")["sobrante"] == 600.0


def test_un_pedido_que_cabe_exacto_no_sobra_nada_y_cero_es_un_dato():
    """*Dos kilos con envases de uno: dos envases y **cero** sobrante.*

    **Cero sobrante no es un hueco**: *es «no sobra nada», que es una respuesta.* *Y por eso `sobrante`
    devuelve `0.0` y no `None` -- confundirlos seria decir que no se sabe cuando si se sabe.*
    """
    r = envases_enteros(2, "kg", 1, "kg")
    assert r["envases"] == 2
    assert r["sobrante"] == 0.0
    assert r["motivo"] is None, "cero sobrante no es un motivo de error"


def test_nunca_se_compran_medio_envase():
    """*Y un pedido mas pequeño que un envase sigue siendo **un** envase.*"""
    assert envases_enteros(200, "g", 1, "kg")["envases"] == 1
    assert envases_enteros(200, "g", 1, "kg")["sobrante"] == 800.0
    # *Un gramo tambien.*
    assert envases_enteros(1, "g", 1, "kg")["envases"] == 1


# ===================================== LOS TRES HUECOS, Y NO SON EL MISMO HUECO ===

def test_sin_tamano_de_envase_es_desconocido_y_no_una_compra_inventada():
    """**El criterio, literal**: *«ausencia de tamano produce desconocido, **no una compra fraccionaria
    inventada**».*

    *Decir «1,4 envases» es decir una cosa que no se puede comprar.* **Y decir «2» sin saber el tamano
    seria peor: seria un numero con aspecto de dato.** *Los dos a `None`, y con su motivo.*
    """
    r = envases_enteros(1.4, "kg", None, None)
    assert r["envases"] is None and r["sobrante"] is None
    assert r["motivo"] == "no se sabe cuanto trae el envase"


def test_sin_cantidad_pedida_es_otro_hueco_y_se_dice_distinto():
    """*Y no se confunden.* **«No se cuanto quiero» y «no se cuanto trae» se arreglan en sitios
    distintos** -- *uno en la lista, el otro en la ficha del articulo.* *Un solo motivo para los dos
    mandaria a mirar donde no es.*
    """
    r = envases_enteros(None, None, 1, "kg")
    assert r["envases"] is None
    assert r["motivo"] == "no se sabe cuanto se quiere"
    assert r["motivo"] != "no se sabe cuanto trae el envase"


def test_masa_contra_volumen_NO_se_convierte_y_se_dice_por_que():
    """**Sin densidad documentada, 1,4 kg y 1 l no se comparan.** *No es que sean incompatibles: es que
    **no se sabe**.*

    *Y no se elige una de las dos.* **Es la misma decision que `core/identidad.py` tomo con los gramos y
    los mililitros** -- *alli el veredicto es `ABSTIENE`, y aqui los envases son `None`.* **Una sola
    regla en dos sitios.**
    """
    r = envases_enteros(1.4, "kg", 1, "l")
    assert r["envases"] is None and r["sobrante"] is None
    assert "no se pueden comparar" in r["motivo"]
    assert "masa" in r["motivo"] and "volumen" in r["motivo"]


def test_unidades_contra_masa_tampoco_se_convierte():
    """*«Seis unidades» y «un envase de un kilo» no se comparan.* **Sin saber cuanto pesa cada una, no se
    sabe.**"""
    r = envases_enteros(6, "ud", 1, "kg")
    assert r["envases"] is None
    assert "no se pueden comparar" in r["motivo"]


# ================================================ la normalizacion, que es la base ===

def test_la_base_canonica_es_gramos_mililitros_y_unidades():
    """*Es lo que permite comparar 1,4 kg con 1000 g* **sin que la unidad escrita cambie el resultado.**
    """
    assert a_canonica(1.4, "kg") == (1400.0, "masa")
    assert a_canonica(1400, "g") == (1400.0, "masa")
    assert a_canonica(1, "l") == (1000.0, "volumen")
    assert a_canonica(500, "ml") == (500.0, "volumen")
    assert a_canonica(6, "ud") == (6.0, "unidades")
    # *Y las variantes escritas se aceptan: «kilos», «litros», «uds».*
    assert a_canonica(2, "kilos") == (2000.0, "masa")
    assert a_canonica(2, "litros") == (2000.0, "volumen")
    assert a_canonica(2, "uds") == (2.0, "unidades")


def test_una_cantidad_que_no_es_un_numero_no_pasa():
    """*Y `bool` esta aqui a proposito*: **en Python `True` es `1`, asi que sin excluirlo, «True kg» serian
    mil gramos.** *Es la misma guarda que la previa puso con el `kg/g`.*
    """
    assert a_canonica(True, "kg") is None
    assert a_canonica(False, "kg") is None
    assert a_canonica("no es un numero", "kg") is None
    assert a_canonica(float("nan"), "kg") is None
    assert a_canonica(float("inf"), "kg") is None
    assert a_canonica(0, "kg") is None, "cero no es una cantidad que se compre"
    assert a_canonica(-3, "kg") is None


def test_sin_unidad_no_se_supone_que_son_unidades():
    """**Es la decision mas facil de equivocar.** *Una linea que diga «4» sin unidad: ¿son cuatro
    unidades, cuatro gramos o cuatro litros?*

    *Suponer «unidades» daria un numero con aspecto de dato para una pregunta que no se ha contestado.*
    **`None`, y la linea se queda sin calculo de envases** -- *que es lo que ya hacia bien la previa con
    lo que no tiene cantidad.*
    """
    assert a_canonica(4, None) is None
    assert a_canonica(4, "") is None
    assert a_canonica(4, "paquete") is None, "«paquete» es un tipo de envase, no una unidad de medida"
    # *Y en la regla entera, sale como «no se sabe cuanto se quiere».*
    assert envases_enteros(4, None, 1, "kg")["envases"] is None


def test_un_tamano_de_cero_o_negativo_no_divide():
    """*Un envase de cero no existe*, y dividir por el daria `inf` -- *que es un numero con aspecto de
    dato y no lo es.*"""
    assert envases_enteros(1.4, "kg", 0, "kg")["envases"] is None
    assert envases_enteros(1.4, "kg", -1, "kg")["envases"] is None


# ============================================================ propiedades ===

@pytest.mark.parametrize("querido,por_envase,esperado", [
    (1.4, 1, 2), (2.0, 1, 2), (0.5, 1, 1), (3.0, 1, 3), (2.5, 1, 3),
    (900, 500, 2), (1000, 500, 2), (1001, 500, 3),
])
def test_los_envases_siempre_cubren_lo_pedido(querido, por_envase, esperado):
    """*La propiedad que tiene que cumplir siempre*: **lo que se compra nunca es menos de lo pedido.**

    *Se prueba con varios pares porque el redondeo hacia arriba tiene un borde -- el exacto -- que es
    justo donde se suele romper.*
    """
    r = envases_enteros(querido, "kg", por_envase, "kg")
    assert r["envases"] == esperado
    assert r["sobrante"] >= 0, "el sobrante nunca es negativo"
    # *Y lo comprado es exactamente lo pedido mas lo que sobra.*
    assert r["envases"] * por_envase * 1000 == pytest.approx(querido * 1000 + r["sobrante"])


# ============================================ LA CONEXION CON LA PREVIA ===

def test_la_previa_calcula_los_envases_cuando_el_tamano_consta():
    """**La prueba de que el calculo esta CONECTADO, y no solo escrito.**

    *Es la que faltaba, y por eso el defecto duro tanto*: `ln.envases` y `ln.sobrante` **no se calculaban
    nunca** porque `_tamano_del_envase` pedia el tamano a `envases.lee`, que nunca lo tuvo. *La regla
    estaba escrita y muerta, y **ninguna prueba lo notaba porque no fallaba: devolvia `None`.***

    *Aqui se le da a la linea el tamano que publicaria la ficha del articulo* y se comprueba que sale el
    numero del criterio: **1,4 kg con envases de 1 kg -> 2 envases y 600 g.**
    """
    from core.previa_compra import LineaDeCompra, _envases_de

    ln = LineaDeCompra(producto_id="p", clave="leche|kg", texto="Leche entera", cantidad=1.4, unidad="kg",
                       tamano_envase=1.0)
    salida = _envases_de([ln])
    assert salida[0].envases == 2, f"no se calculo: {salida[0]}"
    assert salida[0].sobrante == 600.0
    assert salida[0].tamano_envase == 1.0, "el tamano no se toca: viene de la ficha"


def test_sin_tamano_en_la_ficha_la_previa_no_inventa_nada():
    """*Y cuando la ficha no publica el tamano, los dos campos se quedan en `None`.*

    **Lo que NO puede pasar**: *que se rellene con un cero -- «no sobra nada», que seria falso -- ni con
    una compra fraccionaria.* *Y esto es lo que ya pasaba por accidente; **ahora pasa por decision**, y la
    prueba lo fija para que no se confunda con un descuido.*
    """
    from core.previa_compra import LineaDeCompra, _envases_de

    ln = LineaDeCompra(producto_id="p", clave="leche|kg", texto="Leche entera", cantidad=1.4, unidad="kg")
    salida = _envases_de([ln])
    assert salida[0].envases is None, "sin tamano no se inventa un numero de envases"
    assert salida[0].sobrante is None, "y tampoco un sobrante: no se sabe si sobra"
    assert salida[0].envases != 0 and salida[0].sobrante != 0, "None no es cero"


def test_la_previa_no_toca_las_lineas_que_no_tienen_tamano_entre_las_que_si():
    """*Y una linea sin tamano no estropea a las de al lado.* **Es lo que pasa de verdad: unas fichas lo
    publican y otras no**, y la previa tiene que aguantar las dos en la misma lista."""
    from core.previa_compra import LineaDeCompra, _envases_de

    con = LineaDeCompra(producto_id="p", clave="a|kg", texto="Con tamano", cantidad=1.4, unidad="kg", tamano_envase=1.0)
    sin = LineaDeCompra(producto_id="p", clave="b|kg", texto="Sin tamano", cantidad=2.0, unidad="kg")
    salida = _envases_de([con, sin])
    por_clave = {x.clave: x for x in salida}
    assert por_clave["a|kg"].envases == 2
    assert por_clave["a|kg"].sobrante == 600.0
    assert por_clave["b|kg"].envases is None
    assert por_clave["b|kg"].sobrante is None


# ======================================= EL RECORRIDO ENTERO: DEL INGREDIENTE AL NUMERO ===

def test_el_tamano_del_envase_entra_por_el_ingrediente_y_llega_al_numero():
    """**El eslabon que faltaba, de punta a punta.** *A08: «usar tamano neto publicado del articulo
    elegido».*

    *El ingrediente trae `cantidad` -- **cuanto se necesita** -- y, si la API lo enriquecio,
    `tamano_envase` -- **cuanto trae un envase**.* **Y sin este camino, el tamano no tenia por donde
    entrar**: *`cantidad` no es el tamano del envase, y confundirlas daria un pedido de un solo envase
    siempre.*

    *Se comprueba el ejemplo del criterio **por el recorrido**: 1,4 kg pedidos, envases de 1 kg -> **2
    envases y 600 g sobrantes**.*
    """
    from core.previa_compra import previa_de_compra

    p = previa_de_compra([
        {"texto": "Leche entera", "cantidad": 1.4, "unidad": "kg",
         "producto_id": "mercadona:1", "tamano_envase": 1, "unidad_envase": "kg"},
    ])
    assert len(p.lineas) == 1, p.lineas
    ln = p.lineas[0]
    assert ln.tamano_envase == 1, "el tamano no llego a la linea"
    assert ln.unidad_envase == "kg"
    assert ln.envases == 2, f"no se calculo por el recorrido: {ln}"
    assert ln.sobrante == 600.0


def test_sin_tamano_en_el_ingrediente_no_se_inventa_por_el_recorrido():
    """*Y cuando la API no lo enriquecio, la linea se queda sin calculo* -- **que es lo correcto**:
    *no se inventa una compra fraccionaria.*"""
    from core.previa_compra import previa_de_compra

    p = previa_de_compra([
        {"texto": "Leche entera", "cantidad": 1.4, "unidad": "kg", "producto_id": "mercadona:1"},
    ])
    ln = p.lineas[0]
    assert ln.tamano_envase is None
    assert ln.envases is None and ln.sobrante is None
    assert ln.envases != 0, "None no es cero: no sobra nada seria una afirmacion falsa"


def test_un_tamano_que_no_sirve_se_ignora_y_no_tumba_la_previa():
    """*La previa no se cae porque un campo venga mal.* **Se ignora, y se queda en «no se sabe».** *Es la
    misma guarda que con la cantidad: `bool` fuera, `nan` fuera, cero fuera.*"""
    from core.previa_compra import previa_de_compra

    for malo in (True, float("nan"), float("inf"), 0, -1, "un kilo"):
        p = previa_de_compra([
            {"texto": "Leche entera", "cantidad": 1.4, "unidad": "kg",
             "producto_id": "m:1", "tamano_envase": malo},
        ])
        assert p.lineas[0].envases is None, f"con {malo!r} no puede salir un numero"


def test_una_receta_que_pide_gramos_de_algo_que_se_vende_en_litros_lo_dice():
    """**Sin densidad documentada, 200 g y 1 l no se comparan.** *Y por eso la unidad del envase viaja
    **aparte** de la del ingrediente: si se supusieran iguales, saldria un numero.*

    *Es la misma decision que `core/identidad.py` con los gramos y los mililitros.* **Una sola regla en
    dos sitios y ahora en tres.**
    """
    from core.previa_compra import previa_de_compra

    p = previa_de_compra([
        {"texto": "Nata", "cantidad": 200, "unidad": "g",
         "producto_id": "m:2", "tamano_envase": 1, "unidad_envase": "l"},
    ])
    ln = p.lineas[0]
    assert ln.unidad == "g", "el ingrediente se sigue midiendo en gramos"
    assert ln.unidad_envase == "l", "y el envase en litros: no se suponen iguales"
    assert ln.envases is None, "gramos contra litros no dan envases: no se sabe"
    assert ln.sobrante is None
    # *Y el motivo se conserva en la regla, que es la que sabe decirlo.*
    r = envases_enteros(200, "g", 1, "l")
    assert "no se pueden comparar" in r["motivo"]


def test_dos_tamanos_distintos_para_el_mismo_producto_dejan_no_se_sabe():
    """*Y esto pasa de verdad*: dos lineas del mismo producto, una enriquecida con el tamano y otra con
    otro. **Elegir uno de los dos seria inventar cual vale**, asi que se deja en `None`."""
    from core.previa_compra import previa_de_compra

    p = previa_de_compra([
        {"texto": "Leche entera", "cantidad": 1, "unidad": "kg",
         "producto_id": "m:1", "tamano_envase": 1, "unidad_envase": "kg"},
        {"texto": "Leche entera", "cantidad": 1, "unidad": "kg",
         "producto_id": "m:1", "tamano_envase": 2, "unidad_envase": "kg"},
    ])
    ln = p.lineas[0]
    assert ln.tamano_envase is None, "dos tamanos distintos: no se sabe cual vale"
    assert ln.envases is None
    assert ln.cantidad == 2, "y la cantidad si se suma, que para eso si se sabe"


def test_si_solo_una_de_las_dos_trae_tamano_se_usa_ese():
    """*Y el caso util*: **una linea sin enriquecer y otra con el tamano** -- *el que aparece se queda.*
    *Descartarlo por prudencia dejaria sin calcular un caso que si se sabe.*"""
    from core.previa_compra import previa_de_compra

    p = previa_de_compra([
        {"texto": "Leche entera", "cantidad": 1, "unidad": "kg", "producto_id": "m:1"},
        {"texto": "Leche entera", "cantidad": 0.4, "unidad": "kg",
         "producto_id": "m:1", "tamano_envase": 1, "unidad_envase": "kg"},
    ])
    ln = p.lineas[0]
    assert ln.tamano_envase == 1
    assert ln.envases == 2, "1,4 kg con envases de 1 kg"
    assert ln.sobrante == 600.0
