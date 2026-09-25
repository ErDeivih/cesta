"""El arranque del almacen: cuanto se espera a la base y por que.

Un solo asunto, y salio de una medicion: **el pool no puede tener el mismo plazo que
un intento de conexion**. El 25 de septiembre de 2026, con la recoleccion diaria
escribiendo en el mismo disco, cada conexion a PostgreSQL tardaba 10,1 s contra un
tope de 10 s, asi que el pool se rendia por una decima justo cuando la conexion
llegaba: `arranca()` fallaba una y otra vez mientras una conexion suelta entraba sin
problema. En la cadena diaria eso es el paso de los avisos de las 06:00 cayendose y un
resumen que dice que no sabe cuantos saltaron.
"""
from unittest import mock

from plataforma.api import almacen


class PoolFalso:
    """Se queda con lo que se le pide, en vez de conectar con nadie."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.plazo = None
        PoolFalso.ultimo = self

    def wait(self, timeout=None):
        self.plazo = timeout

    def close(self):
        pass


def _arranca(espera):
    almacen._pool = None
    with mock.patch.object(almacen, "ConnectionPool", PoolFalso), \
            mock.patch.object(almacen.psycopg, "connect") as suelta, \
            mock.patch.object(almacen, "migra") as migra:
        almacen.arranca(espera=espera)
    return PoolFalso.ultimo, suelta, migra


def test_el_pool_espera_mas_que_un_intento_de_conexion():
    pool, _suelta, _migra = _arranca(espera=10)
    tope = pool.kwargs["kwargs"]["connect_timeout"]
    assert pool.plazo > tope, (
        f"el pool espera {pool.plazo}s y cada intento puede tardar {tope}s: se rinde "
        f"justo cuando la conexion esta llegando (medido: 10,1s contra 10)")


def test_la_conexion_suelta_sigue_siendo_el_que_corta():
    """El plazo corto sigue estando donde tiene que estar: en la prueba previa, que es
    la que decide si la base esta o no. Asi, con la base caida, esto no espera de mas."""
    _pool, suelta, migra = _arranca(espera=10)
    assert suelta.call_args.kwargs["connect_timeout"] == 10
    migra.assert_called_once()


def test_con_la_base_caida_no_se_crea_ningun_pool():
    almacen._pool = None
    with mock.patch.object(almacen, "ConnectionPool", PoolFalso), \
            mock.patch.object(almacen.psycopg, "connect",
                              side_effect=RuntimeError("no hay base")):
        try:
            almacen.arranca(espera=5)
        except RuntimeError:
            pass
        else:
            raise AssertionError("tenia que fallar")
    assert almacen._pool is None, "se ha creado un pool sin saber si la base estaba"
