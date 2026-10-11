"""La plataforma: el calculo de la cesta y las reglas que no se pueden romper.

Estas pruebas no tocan PostgreSQL ni la red: prueban la parte que decide cuanto
cuesta la compra, que es donde un error se traduce en dinero.
"""
from unittest import mock

from plataforma.api import cesta


def _pet(grupo_id, cantidad=1, nombre="algo"):
    return cesta.Peticion(grupo_id, None, cantidad, nombre)


def _catalogo(filas, promos=None):
    """Sustituye la lectura de gold por unas cuantas filas a mano.

    filas: (grupo_id, fuente, producto_id, nombre, precio_cent)
    """
    def candidatos(peticiones, fecha):
        mejor = {}
        for gid, fuente, pid, nombre, precio in filas:
            clave = (gid, fuente)
            if clave not in mejor or precio < mejor[clave][1]:
                mejor[clave] = (pid, precio, nombre, (promos or {}).get(pid))
        return mejor
    return mock.patch.object(cesta, "_candidatos", candidatos)


def test_cada_cadena_suma_lo_suyo():
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100),
             (1, "dia", "dia:a", "Leche", 120),
             (2, "alcampo", "alcampo:b", "Pan", 200),
             (2, "dia", "dia:b", "Pan", 180)]
    with _catalogo(filas):
        r = cesta.donde_comprar([_pet(1), _pet(2)], ["alcampo", "dia"])
    totales = {t["cadena"]: t["total_cent"] for t in r["una_tienda"]}
    assert totales == {"alcampo": 300, "dia": 300}


def test_lo_que_falta_se_dice_por_su_nombre():
    # Un numero ("le faltan 2") no sirve: hay que saber cuales para decidir.
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100)]
    with _catalogo(filas):
        r = cesta.donde_comprar([_pet(1, nombre="Leche entera 1 L"),
                                 _pet(9, nombre="Cafe en grano 1 kg")], ["alcampo"])
    assert r["una_tienda"][0]["faltan"] == ["Cafe en grano 1 kg"]


def test_la_que_lo_tiene_todo_va_antes_que_la_barata_incompleta():
    filas = [(1, "alcampo", "alcampo:a", "Leche", 500),
             (1, "dia", "dia:a", "Leche", 100),
             (2, "alcampo", "alcampo:b", "Pan", 100)]
    with _catalogo(filas):
        r = cesta.donde_comprar([_pet(1), _pet(2)], ["alcampo", "dia"])
    assert r["una_tienda"][0]["cadena"] == "alcampo"      # cara pero completa


def test_el_reparto_coge_lo_barato_de_cada_una():
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100),
             (1, "dia", "dia:a", "Leche", 300),
             (2, "alcampo", "alcampo:b", "Pan", 300),
             (2, "dia", "dia:b", "Pan", 100)]
    with _catalogo(filas):
        r = cesta.donde_comprar([_pet(1), _pet(2)], ["alcampo", "dia"])
    assert r["repartido"]["total_cent"] == 200
    assert r["repartido"]["ahorro_cent"] == 200          # 400 en una, 200 repartido


def test_un_ahorro_ridiculo_no_merece_el_viaje():
    # Ir a dos tiendas cuesta media hora. Ahorrar treinta centimos no lo paga.
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100),
             (1, "dia", "dia:a", "Leche", 130),
             (2, "alcampo", "alcampo:b", "Pan", 100),
             (2, "dia", "dia:b", "Pan", 100)]
    with _catalogo(filas):
        r = cesta.donde_comprar([_pet(1), _pet(2)], ["alcampo", "dia"])
    assert r["repartido"] is None or not r["repartido"]["merece_la_pena"]


def test_no_se_propone_un_reparto_de_una_sola_tienda():
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100),
             (2, "alcampo", "alcampo:b", "Pan", 100)]
    with _catalogo(filas):
        r = cesta.donde_comprar([_pet(1), _pet(2)], ["alcampo", "dia"])
    assert r["repartido"] is None


# --- las ofertas, que es lo que de verdad cambia el total ----------------

def test_la_segunda_unidad_al_50_no_es_la_mitad_de_todo():
    filas = [(1, "alcampo", "alcampo:a", "Champu", 630)]
    with _catalogo(filas, {"alcampo:a": "2ª unidad -50%"}):
        r = cesta.donde_comprar([_pet(1, cantidad=2)], ["alcampo"])
    t = r["una_tienda"][0]
    assert t["total_sin_ofertas_cent"] == 1260
    assert t["total_cent"] == 945                      # 6,30 + 3,15


def test_el_3x2_regala_la_tercera():
    filas = [(1, "alcampo", "alcampo:a", "Yogur", 100)]
    with _catalogo(filas, {"alcampo:a": "3x2"}):
        r = cesta.donde_comprar([_pet(1, cantidad=3)], ["alcampo"])
    assert r["una_tienda"][0]["total_cent"] == 200


def test_el_descuento_de_tarjeta_no_baja_lo_que_pagas_hoy():
    # Se acumula en un monedero, no se descuenta en caja. Restarlo seria mentir.
    filas = [(1, "alcampo", "alcampo:a", "Cafe", 500)]
    with _catalogo(filas, {"alcampo:a": "Club Alcampo 2ª unidad -50% acum en tu tarjeta"}):
        r = cesta.donde_comprar([_pet(1, cantidad=2)], ["alcampo"])
    t = r["una_tienda"][0]
    assert t["total_cent"] == 1000
    assert t["productos"][0]["promo"] is None          # no se ensena como oferta


def test_sugiere_llevar_una_mas_solo_si_baja_el_precio_por_unidad():
    filas = [(1, "alcampo", "alcampo:a", "Yogur", 100)]
    with _catalogo(filas, {"alcampo:a": "3x2"}):
        r = cesta.donde_comprar([_pet(1, cantidad=2)], ["alcampo"])
    assert "3" in (r["una_tienda"][0]["productos"][0]["sugerencia"] or "")

    with _catalogo(filas, {"alcampo:a": "-30%"}):
        r = cesta.donde_comprar([_pet(1, cantidad=2)], ["alcampo"])
    assert r["una_tienda"][0]["productos"][0]["sugerencia"] is None


def test_la_oferta_cuenta_al_elegir_tienda():
    # Sin la mecanica, alcampo parece mas cara y el reparto sale mal.
    filas = [(1, "alcampo", "alcampo:a", "Gel", 300),
             (1, "dia", "dia:a", "Gel", 260)]
    with _catalogo(filas, {"alcampo:a": "2ª unidad -50%"}):
        r = cesta.donde_comprar([_pet(1, cantidad=2)], ["alcampo", "dia"])
    totales = {t["cadena"]: t["total_cent"] for t in r["una_tienda"]}
    assert totales["alcampo"] == 450                  # 3,00 + 1,50
    assert totales["dia"] == 520
    assert r["una_tienda"][0]["cadena"] == "alcampo"  # gana por la oferta


def test_una_lista_vacia_no_revienta():
    assert cesta.donde_comprar([])["una_tienda"] == []


# --- el reparto por tiendas: la lista partida por lo que se ha decidido ----

def _pet_tienda(grupo_id, elegida, cantidad=1, nombre="algo", linea_id="L1"):
    return cesta.Peticion(grupo_id, None, cantidad, nombre, linea_id), elegida


def _reparto(filas, decisiones, promos=None, cadenas=("alcampo", "dia")):
    peticiones = [p for p, _ in decisiones]
    elegidas = [e for _, e in decisiones]
    with _catalogo(filas, promos):
        return cesta.reparto_por_tienda(peticiones, elegidas, list(cadenas))


def test_cada_sublista_suma_lo_suyo_y_el_total_es_la_suma():
    """La pregunta del 25 de septiembre: «¿cuánto me cuesta así, tienda por tienda?»"""
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100),
             (1, "dia", "dia:a", "Leche", 120),
             (2, "alcampo", "alcampo:b", "Pan", 200),
             (2, "dia", "dia:b", "Pan", 180)]
    r = _reparto(filas, [_pet_tienda(1, "dia"), _pet_tienda(2, "alcampo")])

    totales = {s["cadena"]: s["total_cent"] for s in r["sublistas"]}
    assert totales == {"dia": 120, "alcampo": 200}
    assert r["total_cent"] == 320                 # 1,20 + 2,00
    assert r["decididas"] == 2 and r["sin_asignar"] == []
    # Cada linea sabe de qué linea viene: es lo que permite quitarla o moverla.
    assert [f["linea_id"] for s in r["sublistas"] for f in s["lineas"]] == ["L1", "L1"]


def test_lo_que_no_esta_decidido_no_suma_pero_dice_donde_esta_mas_barato():
    """Sumarlo por lo mas barato daria un total que no corresponde a ninguna compra."""
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100),
             (1, "dia", "dia:a", "Leche", 120),
             (2, "alcampo", "alcampo:b", "Pan", 200),
             (2, "dia", "dia:b", "Pan", 180)]
    r = _reparto(filas, [_pet_tienda(1, "dia"), _pet_tienda(2, None, nombre="Pan")])

    assert r["total_cent"] == 120
    assert [x["nombre"] for x in r["sin_asignar"]] == ["Pan"]
    sin = r["sin_asignar"][0]
    assert sin["mas_barata"] == "dia" and sin["coste_cent"] == 180
    # Y con las opciones ordenadas: la pantalla puede enseñar dónde cambiarla.
    assert [o["cadena"] for o in sin["opciones"]] == ["dia", "alcampo"]


def test_una_linea_asignada_a_una_tienda_donde_no_esta_se_dice_por_su_nombre():
    """Si no, la linea desaparece de la pantalla y parece que se ha borrado sola."""
    filas = [(1, "dia", "dia:a", "Leche", 120)]
    r = _reparto(filas, [_pet_tienda(1, "alcampo", nombre="Leche entera 1 L")])

    assert r["total_cent"] == 0
    assert r["sublistas"][0]["cadena"] == "alcampo"
    assert r["sublistas"][0]["total_cent"] == 0
    assert r["sublistas"][0]["sin_encontrar"] == ["Leche entera 1 L"]
    assert r["sin_encontrar"] == [{"cadena": "alcampo",
                                   "nombres": ["Leche entera 1 L"]}]


def test_las_ofertas_se_aplican_y_se_explican_en_su_sublista():
    """«Explicando también la aplicación de descuentos»: el total y lo que ahorran."""
    filas = [(1, "alcampo", "alcampo:a", "Champú", 630),
             (2, "alcampo", "alcampo:b", "Pan", 100)]
    r = _reparto(filas, [_pet_tienda(1, "alcampo", cantidad=2),
                         _pet_tienda(2, "alcampo")],
                 promos={"alcampo:a": "2ª unidad -50%"})

    sub = r["sublistas"][0]
    assert sub["total_cent"] == 945 + 100          # 6,30 + 3,15 + 1,00
    assert sub["total_sin_ofertas_cent"] == 1260 + 100
    assert sub["ahorro_cent"] == 315               # 3,15 de la segunda unidad
    assert [o["promo"] for o in sub["ofertas"]] == ["2ª unidad -50%"]
    # La oferta es una regla sobre cuantas compras: con una unidad no se aplica.
    r1 = _reparto(filas, [_pet_tienda(1, "alcampo", cantidad=1),
                          _pet_tienda(2, "alcampo")],
                  promos={"alcampo:a": "2ª unidad -50%"})
    assert r1["sublistas"][0]["ahorro_cent"] == 0


def test_se_compara_con_lo_que_costaria_sin_decidir_nada():
    """La comparación honesta: «así pagas 3,00; repartiendo en dos, 2,80»."""
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100),
             (1, "dia", "dia:a", "Leche", 120),
             (2, "alcampo", "alcampo:b", "Pan", 200),
             (2, "dia", "dia:b", "Pan", 180)]
    r = _reparto(filas, [_pet_tienda(1, "dia"), _pet_tienda(2, "dia", nombre="Pan")])

    assert r["total_cent"] == 300                  # lo decidido: todo en DIA
    una = {t["cadena"]: t["total_cent"] for t in r["una_tienda"]}
    assert una == {"dia": 300, "alcampo": 300}
    # Y el reparto que la aplicación propone, para poder compararlo de un vistazo.
    assert r["repartido"]["total_cent"] == 280
    assert r["repartido"]["ahorro_cent"] == 20


# --- el total en vivo, que es lo que se mira al ir anadiendo --------------

def _linea(grupo_id, cantidad=1, carro=False, nombre="algo", **extra):
    """Una linea, con lo que traiga la prueba de mas: `id`, `cadena_elegida`, `producto_movido`…"""
    return {"grupo_id": grupo_id, "producto_id": None, "cantidad": cantidad,
            "nombre_visto": nombre, "en_carrito": carro, "tachado_en": None} | extra


def test_la_estimacion_coge_cada_cosa_donde_este_mas_barata():
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100),
             (1, "dia", "dia:a", "Leche", 130),
             (2, "carrefour", "carrefour:b", "Pan", 200)]
    with _catalogo(filas):
        e = cesta.estimacion([_linea(1, 2), _linea(2)])
    assert e["total_cent"] == 400          # 2x100 + 200, no 2x130
    assert e["lineas"] == 2


def test_la_estimacion_separa_el_carro_de_lo_que_falta():
    # Es la barra de progreso de la lista: cuanto llevas y cuanto te queda.
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100),
             (2, "alcampo", "alcampo:b", "Pan", 300)]
    with _catalogo(filas):
        e = cesta.estimacion([_linea(1, carro=True), _linea(2)])
    assert e["en_carrito_cent"] == 100
    assert e["por_recoger_cent"] == 300
    assert e["total_cent"] == 400


def test_una_linea_tachada_cuenta_como_metida_en_el_carro():
    # El movil viejo manda 'tachado' y el nuevo 'en_carrito': son lo mismo.
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100)]
    linea = _linea(1)
    linea["tachado_en"] = "2026-09-17T10:00:00Z"
    with _catalogo(filas):
        e = cesta.estimacion([linea])
    assert e["en_carrito_cent"] == 100


def test_lo_que_no_tiene_precio_se_cuenta_aparte_y_no_se_inventa():
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100)]
    with _catalogo(filas):
        e = cesta.estimacion([_linea(1), _linea(77, nombre="algo raro")])
    assert e["total_cent"] == 100
    assert e["sin_precio"] == 1


def test_la_estimacion_de_una_lista_vacia_es_cero_y_no_revienta():
    e = cesta.estimacion([])
    assert e == {"total_cent": 0, "en_carrito_cent": 0, "por_recoger_cent": 0,
                 "lineas": 0, "sin_precio": 0}


# --- el precio de cada linea, para guardarlo al cerrar la compra -------------
# `coste_por_linea` existe por «He terminado la compra» (tarea 10): la compra se guarda **con
# sus precios**, porque gold se reescribe cada dia y una compra sin su precio no se puede
# volver a mirar. Lo que se vigila aqui es de quien es el precio que se guarda.
#
# **La forma que devuelve tiene cuatro claves desde el 13 de octubre de 2026 (fase 2, F01)**:
# `cadena`, `precio_cent`, `promo` y `producto_id` -- mas `coste_cent`, que anade el reparto. *Las dos
# ultimas son lo que el cierre necesita para guardar **el producto efectivo**: sin `producto_id` una
# linea de grupo se archivaba sin identidad, y sin `promo` el reparto adivinaba la oferta buscando un
# candidato de esa cadena con ese precio exacto.* Se afirma la forma entera a proposito: **una clave de
# mas es un cambio de contrato, y tiene que doler.**

def test_el_precio_de_una_linea_es_el_de_la_cadena_mas_barata():
    filas = [(1, "alcampo", "alcampo:a", "Leche", 120),
             (1, "dia", "dia:a", "Leche", 100)]
    with _catalogo(filas):
        c = cesta.coste_por_linea([_linea(1, id="l1")])
    assert c["l1"] == {"cadena": "dia", "precio_cent": 100, "coste_cent": 100,
                       "promo": None, "producto_id": "dia:a"}, c["l1"]


def test_si_la_linea_tiene_tienda_decidida_se_guarda_ese_precio():
    """**No es el mas barato: es el que se pago.** Si alguien decidio comprarlo en Alcampo
    aunque en DIA este mas barato, apuntar el de DIA seria apuntar un precio que no se pago."""
    filas = [(1, "alcampo", "alcampo:a", "Leche", 120),
             (1, "dia", "dia:a", "Leche", 100)]
    with _catalogo(filas):
        c = cesta.coste_por_linea([_linea(1, id="l1", cadena_elegida="alcampo")])
    assert c["l1"] == {"cadena": "alcampo", "precio_cent": 120, "coste_cent": 120,
                       "promo": None, "producto_id": "alcampo:a"}, c["l1"]


def test_una_linea_que_apunta_a_otro_producto_no_tiene_precio():
    """Sumarle el precio del grupo al que apunta seria meter un numero falso en la compra."""
    filas = [(1, "dia", "dia:a", "Pintalabios", 1066)]
    with _catalogo(filas):
        c = cesta.coste_por_linea([_linea(1, id="l1", nombre="Leche entera",
                                          producto_movido=True)])
    assert c["l1"] == {"cadena": None, "precio_cent": None,
                       "promo": None, "producto_id": None}


def test_una_linea_que_no_esta_en_el_catalogo_no_tiene_precio_y_no_es_un_cero():
    with _catalogo([(1, "dia", "dia:a", "Leche", 100)]):
        c = cesta.coste_por_linea([_linea(77, id="suelta", nombre="algo raro")])
    assert c["suelta"] == {"cadena": None, "precio_cent": None,
                           "promo": None, "producto_id": None}


def test_sin_lineas_no_hay_precios_que_dar():
    assert cesta.coste_por_linea([]) == {}


# --- lo que cambia cuando entran amigos ---------------------------------
# El esquema asumia dos personas. Estas pruebas cierran las tres puertas que se
# abren al entrar la tercera: la lista de casa unica en todo el sistema, las
# invitaciones sin tope, y no poder darse de baja.

def test_el_tope_de_invitaciones_es_de_tres():
    from plataforma.api.almacen import MAX_INVITACIONES_VIVAS
    # Bastantes para invitar a quien quieras, pocos para que se te escape uno
    # reenviado en un grupo que no era.
    assert MAX_INVITACIONES_VIVAS == 3


def test_la_migracion_arregla_el_indice_de_la_lista_de_casa():
    # Era UNICO EN TODA LA BASE: el segundo usuario que creara su lista de casa
    # se llevaria un error de clave duplicada que no entiende nadie.
    from pathlib import Path
    sql = (Path(__file__).resolve().parents[1] / "plataforma" / "sql"
           / "003_mas_de_dos.sql").read_text(encoding="utf-8")
    assert "DROP INDEX IF EXISTS lista_de_casa_unica" in sql
    assert "ON lista(dueno_id) WHERE es_de_casa" in sql


def test_borrarse_conserva_lo_que_anadio_en_listas_de_otros():
    # Borrar sus lineas vaciaria la lista de la compra de alguien que no ha
    # pedido nada. Se quedan sin autor, que es lo honesto.
    from pathlib import Path
    sql = (Path(__file__).resolve().parents[1] / "plataforma" / "sql"
           / "003_mas_de_dos.sql").read_text(encoding="utf-8")
    assert "UPDATE lista_linea SET anadido_por = NULL" in sql
    assert "ALTER COLUMN anadido_por DROP NOT NULL" in sql
