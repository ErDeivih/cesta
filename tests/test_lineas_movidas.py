"""La linea de una lista y su grupo: ¿siguen siendo el mismo producto?

**Esto guarda el fallo mas caro que ha tenido la aplicacion, y el mas silencioso.** El emparejador
numera los grupos **en el orden en que aparecen los productos** (`core.matching.agrupar_enlaces`,
el `renombre.setdefault(raiz(i), len(renombre))`), asi que cada pasada puede renumerarlos. Las
listas, los favoritos y los avisos de PostgreSQL guardan ese numero.

Medido el 28 de septiembre de 2026, con los datos de casa y la lista de la cuenta de pruebas:

    54 lineas en la lista, 43 apuntando a un grupo que ya no es su producto
    la leche entera salia en el pasillo «Higiene y belleza» (el grupo 526 es hoy un pintalabios)
    la estimacion decia 298,71 EUR: eran 43 lineas de pintalabios a 10,66 EUR/ud
    la estimacion de verdad, con lo que se puede contar: 10,56 EUR

Lo que se comprueba aqui es la parte que no necesita gold: el juicio de «este grupo es este
producto», que es lo que decide si una linea se pinta con su pasillo y su precio o se dice que se
ha movido. La migracion de verdad -- guardar el producto estable en vez del numero -- esta apuntada
desde el 22 de septiembre (`docs/MODELO.md`, `docs/DIAGNOSTICO-MATCHING.md` §21).
"""
from __future__ import annotations

import pathlib

from plataforma.api import catalogo, cesta

CESTA = pathlib.Path(__file__).resolve().parents[1] / "plataforma" / "api" / "cesta.py"


def test_el_mismo_producto_con_marca_o_formato_de_mas_sigue_siendo_el_mismo():
    """Lo que se anade al nombre no cambia el producto: marca, formato, cantidad."""
    assert catalogo._mismo_producto("Leche entera", ["Leche entera Hacendado"])
    assert catalogo._mismo_producto("Leche entera Hacendado", ["Leche entera"])
    assert catalogo._mismo_producto("Leche entera", ["Leche entera brick 1 l", "Otra cosa"])
    assert catalogo._mismo_producto("Atún claro en aceite", ["ATUN CLARO EN ACEITE OLIVA"])


def test_dos_productos_distintos_no_pasan_por_el_mismo():
    """Y el caso del fallo: el grupo es hoy una barra de labios."""
    assert not catalogo._mismo_producto(
        "Leche entera", ["REVLON Colorstay suede ink Tono 018 Barra de labios"])
    assert not catalogo._mismo_producto("Leche entera", ["TWIX Barritas de chocolate"])


def test_una_linea_sin_nombre_no_se_acusa():
    """Sin palabras con las que comparar, no se dice que se ha movido: eso seria una acusacion."""
    assert catalogo._mismo_producto("", ["Leche entera"])
    assert catalogo._mismo_producto("1 l", ["Leche entera"])


def test_la_estimacion_no_cuenta_las_lineas_movidas():
    """Una linea movida suma **cero** y cuenta como «sin precio», no como el precio de otro."""
    lineas = [
        {"id": "a", "grupo_id": 1, "cantidad": 1, "nombre_visto": "Leche"},
        {"id": "b", "grupo_id": 2, "cantidad": 1, "nombre_visto": "Pan",
         "producto_movido": True},
    ]
    filas = [(1, "alcampo", "alcampo:a", "Leche", 100),
             (2, "alcampo", "alcampo:b", "Pintalabios", 1066)]

    def candidatos(peticiones, fecha):
        return {(f[0], f[1]): (f[2], f[4], f[3], None) for f in filas}

    import unittest.mock as mock

    with mock.patch.object(cesta, "_candidatos", candidatos):
        r = cesta.estimacion(lineas)

    assert r["total_cent"] == 100, "la linea movida esta metiendo el precio de otro producto"
    assert r["sin_precio"] == 1


def test_la_linea_movida_viaja_sin_pasillo_y_marcada():
    """El pasillo tambien es del grupo: el de una linea movida es el de otro producto.

    Medido: la leche entera salia bajo «Higiene y belleza». La marca y la falta de pasillo las pone
    `main._linea_movida`; esto comprueba que ese es el contrato (una prueba de la API de verdad
    vive en `plataforma/prueba_e2e.py`, que es lo unico que ejecuta el SQL y lee gold).
    """
    from plataforma.api import main

    limpia = main._linea_movida({"id": "x", "nombre_visto": "Leche entera", "grupo_id": 526,
                                 "pasillo": "Higiene y belleza", "pasillo_orden": 12,
                                 "seccion": "higiene-belleza", "cantidad": 1})
    assert limpia["producto_movido"] is True
    assert "pasillo" not in limpia and "pasillo_orden" not in limpia and "seccion" not in limpia
    assert limpia["cantidad"] == 1 and limpia["grupo_id"] == 526


def test_la_puerta_del_navegador_no_reparte_las_lineas_movidas():
    """Lo que se puede contar de una lista con lineas movidas no las incluye.

    Se mira en el codigo y no solo en la respuesta porque hay **dos** caminos que reparten
    (`/donde` y `/reparto`) y los dos tienen que filtrarlas: dejar una fuera seria decidir la
    tienda de un producto por el precio de otro.
    """
    fuente = CESTA.read_text(encoding="utf-8")
    assert "producto_movido" in fuente, (
        "la estimacion no mira si la linea se ha movido: sumaria el precio de otro producto")
    main = (CESTA.parent / "main.py").read_text(encoding="utf-8")
    assert main.count("catalogo.lineas_movidas(") >= 3, (
        "hay caminos que reparten la lista sin quitar las lineas movidas: ver `/listas/{id}`, "
        "`/donde` y `/reparto`")
