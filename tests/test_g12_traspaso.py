"""G12, punto 221: **repetir la misma transferencia no duplica; otra semana si.**

*La frase que decide el diseno*: si la identidad fuera el contenido de las lineas, dos semanas
distintas con los mismos ingredientes serian indistinguibles. **Asi que la identidad es de la
operacion -- receta + version + semana -- y la semana la calcula el servidor.**

*Todo con base temporal: `recetas.ruta_base` existe justo para esto («se puede fijar para que las
pruebas no toquen el de verdad»).*
"""
from __future__ import annotations

from datetime import date

import pytest

from core import recetas, traspaso


@pytest.fixture()
def con(tmp_path):
    """Un recetario de mentira, con una receta de dos ingredientes."""
    ruta = tmp_path / "recetas.sqlite"
    # **`conecta(ruta)` acepta la ruta**: no hay `recetas.ruta_base` -- eso vive en
    # `plataforma/api/recetas.py`, y darlo por hecho fue leer una capa y concluir sobre otra.
    conexion = recetas.conecta(ruta)
    receta_id = recetas.crear(conexion, "dueno-a", "Tortilla")
    recetas.actualizar(conexion, "dueno-a", receta_id, raciones=4, preparacion="Batir y cuajar",
                       ingredientes=[{"texto": "huevo", "cantidad": 4, "unidad": "ud"},
                                     {"texto": "patata", "cantidad": 500, "unidad": "g"},
                                     {"texto": "sal"}])
    yield conexion, receta_id
    conexion.close()


def test_la_misma_operacion_no_duplica(con):
    """**Repetir es no hacer nada.** *Y se dice que ya estaba, en vez de devolver un exito mudo.*"""
    conexion, receta_id = con
    hoy = date(2026, 10, 14)          # un miercoles
    primera = traspaso.pasar_a_lista(conexion, "dueno-a", receta_id, hoy=hoy)
    segunda = traspaso.pasar_a_lista(conexion, "dueno-a", receta_id, hoy=hoy)

    assert primera["ya_estaba"] is False and segunda["ya_estaba"] is True
    assert primera["clave"] == segunda["clave"], "la clave de la operacion es la misma"
    assert primera["lineas"] == segunda["lineas"]
    # Y solo hay UNA operacion registrada, que es lo que impide el duplicado.
    n = conexion.execute("SELECT count(*) FROM traspaso").fetchone()[0]
    assert n == 1, "repetir no puede dejar dos operaciones"


def test_dentro_de_la_misma_semana_tambien_es_la_misma_operacion(con):
    """**Lunes y miercoles de la misma semana son la misma compra.** *Se compra una vez.*"""
    conexion, receta_id = con
    lunes = traspaso.pasar_a_lista(conexion, "dueno-a", receta_id, hoy=date(2026, 10, 12))
    miercoles = traspaso.pasar_a_lista(conexion, "dueno-a", receta_id, hoy=date(2026, 10, 14))
    assert miercoles["ya_estaba"] is True
    assert lunes["semana"] == miercoles["semana"] == "2026-10-12"


def test_otra_semana_si_es_otra_operacion(con):
    """**«Otra semana/operacion legitima si».** *La misma receta, la semana siguiente, se compra.*"""
    conexion, receta_id = con
    esta = traspaso.pasar_a_lista(conexion, "dueno-a", receta_id, hoy=date(2026, 10, 14))
    siguiente = traspaso.pasar_a_lista(conexion, "dueno-a", receta_id, hoy=date(2026, 10, 21))
    assert esta["ya_estaba"] is False and siguiente["ya_estaba"] is False
    assert esta["semana"] != siguiente["semana"]


def test_otra_version_de_la_receta_es_otra_operacion(con):
    """*Cambiar la receta es cambiar lo que se compra, y por eso es una operacion distinta.*"""
    conexion, receta_id = con
    hoy = date(2026, 10, 14)
    v1 = traspaso.pasar_a_lista(conexion, "dueno-a", receta_id, hoy=hoy)
    recetas.actualizar(conexion, "dueno-a", receta_id, raciones=6,
                       ingredientes=[{"texto": "huevo", "cantidad": 6, "unidad": "ud"}])
    v2 = traspaso.pasar_a_lista(conexion, "dueno-a", receta_id, hoy=hoy)
    assert v1["version"] != v2["version"]
    assert v2["ya_estaba"] is False, "la version nueva si se traspasa"


def test_la_receta_de_otro_no_se_traspasa(con):
    """**La puerta es el dueno, y quien la comprueba es el servidor.** *`_de_quien` ya lo hace.*"""
    conexion, receta_id = con
    with pytest.raises(ValueError, match="no hay receta"):
        traspaso.pasar_a_lista(conexion, "dueno-b", receta_id, hoy=date(2026, 10, 14))


def test_sin_dueno_no_hay_traspaso(con):
    """*«Una receta necesita dueno: el recetario es personal.»*"""
    conexion, receta_id = con
    with pytest.raises(ValueError, match="dueno"):
        traspaso.pasar_a_lista(conexion, "", receta_id)


def test_la_semana_la_calcula_el_servidor_y_es_el_lunes():
    """*Si la mandara el cliente, dos pestañas con fechas distintas escribirian dos veces.*"""
    assert traspaso.semana_de(date(2026, 10, 14)) == "2026-10-12"   # miercoles -> lunes
    assert traspaso.semana_de(date(2026, 10, 12)) == "2026-10-12"   # lunes -> lunes
    assert traspaso.semana_de(date(2026, 10, 18)) == "2026-10-12"   # domingo -> el lunes anterior


def test_el_id_de_la_linea_es_determinista_y_distingue():
    """**La segunda red del 221.** *Si el id sale de la operacion, repetirla actualiza en vez de anadir.*

    *Y no se prueba con base de datos ni servidor: es una funcion pura, y un id que cambia entre dos
    llamadas iguales seria justo el fallo que esto tiene que impedir.*
    """
    a = traspaso.id_de_linea("lista-1", "p1|g")
    b = traspaso.id_de_linea("lista-1", "p1|g")
    assert a == b, "el mismo dato da el mismo id"
    # Y distingue lo que tiene que distinguir: la lista y el ingrediente.
    assert a != traspaso.id_de_linea("lista-2", "p1|g"), "otra lista es otra linea"
    assert a != traspaso.id_de_linea("lista-1", "p2|g"), "otro ingrediente es otra linea"
    assert len(a) == 36, "y tiene forma de uuid"
