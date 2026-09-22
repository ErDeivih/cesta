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


# --- el total en vivo, que es lo que se mira al ir anadiendo --------------

def _linea(grupo_id, cantidad=1, carro=False, nombre="algo"):
    return {"grupo_id": grupo_id, "producto_id": None, "cantidad": cantidad,
            "nombre_visto": nombre, "en_carrito": carro, "tachado_en": None}


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
