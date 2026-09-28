"""Que un grupo conserve su numero entre pasadas: las cuatro formas de perderlo.

**Esto guarda el fallo mas caro que ha tenido la aplicacion.** El emparejador numera los grupos en
el orden en que aparecen los productos, y ese numero lo guardan las listas, los favoritos y los
avisos de PostgreSQL. Medido el 28 de septiembre de 2026: de las 54 lineas de la lista de la cuenta
de pruebas, **43** apuntaban a un grupo que ya no era su producto, la leche entera salia en el
pasillo «Higiene y belleza» (el grupo 526 es hoy un pintalabios) y la estimacion decia 298,71 EUR
cuando lo contable eran 10,56.

Los casos que se prueban son los cuatro que pueden romper la herencia:
1. el mismo agrupamiento, con el catalogo en otro orden (lo que pasa cada dia);
2. un grupo que crece o mengua un poco;
3. un grupo que se parte en dos (uno se queda el numero, el otro estrena);
4. un grupo nuevo y uno que desaparece (y el hueco no se reutiliza).
"""
from __future__ import annotations

import polars as pl

from core import grupos_ids


def _tabla(pares: list[tuple[str, int]]) -> pl.DataFrame:
    """(clave, grupo): como se numera un dia."""
    return pl.DataFrame({"clave": [p[0] for p in pares],
                         "grupo": pl.Series([p[1] for p in pares], dtype=pl.Int32)})


def _ayer(pares: list[tuple[str, int]]) -> pl.DataFrame:
    """(clave, grupo_id): lo que se guardo de la pasada anterior."""
    return pl.DataFrame({"clave": [p[0] for p in pares],
                         "grupo_id": pl.Series([p[1] for p in pares], dtype=pl.Int32)})


def _ids(tabla: pl.DataFrame) -> dict[str, int]:
    return dict(zip(tabla["clave"].to_list(), tabla["grupo_id"].to_list(), strict=True))


def test_el_mismo_agrupamiento_con_el_catalogo_en_otro_orden_da_los_mismos_ids():
    """El caso que rompia todo: el orden de los productos cambia y los numeros se mueven."""
    ayer = _ayer([("a:1", 0), ("a:2", 0), ("b:3", 1), ("b:4", 1)])
    # Hoy el catalogo viene al reves, asi que la numeracion "de siempre" daria 1 y 0.
    hoy_crudo = _tabla([("b:3", 0), ("b:4", 0), ("a:1", 1), ("a:2", 1)])
    assert _ids(grupos_ids.estabiliza(hoy_crudo, ayer)) == {
        "a:1": 0, "a:2": 0, "b:3": 1, "b:4": 1}


def test_un_grupo_que_crece_o_mengua_un_poco_conserva_su_numero():
    ayer = _ayer([("a:1", 0), ("a:2", 0), ("b:3", 7)])
    hoy = _tabla([("a:1", 0), ("a:2", 0), ("a:5", 0), ("b:3", 1)])
    ids = _ids(grupos_ids.estabiliza(hoy, ayer))
    assert ids["a:1"] == ids["a:2"] == ids["a:5"] == 0
    assert ids["b:3"] == 7, "el grupo que mengua conserva su numero"
    # Y el 1 del reparto de hoy no se le queda a nadie mas: los ids no se repiten.
    assert list(ids.values()).count(0) == 3


def test_un_grupo_que_se_parte_en_dos_le_deja_el_numero_al_mas_grande():
    ayer = _ayer([("a:1", 0), ("a:2", 0), ("a:3", 0)])
    hoy = _tabla([("a:1", 0), ("a:2", 0), ("a:3", 1)])
    ids = _ids(grupos_ids.estabiliza(hoy, ayer))
    assert ids["a:1"] == ids["a:2"] == 0, "la parte grande conserva el numero de ayer"
    assert ids["a:3"] == 1, "la parte que se separa estrena numero"
    assert len(set(ids.values())) == 2, "dos grupos no pueden compartir numero"


def test_un_grupo_nuevo_estrena_numero_y_el_hueco_no_se_reutiliza():
    ayer = _ayer([("a:1", 0), ("a:2", 0), ("b:3", 5)])
    hoy = _tabla([("a:1", 0), ("a:2", 0), ("c:9", 1)])   # `b:3` desaparece
    ids = _ids(grupos_ids.estabiliza(hoy, ayer))
    assert ids["a:1"] == ids["a:2"] == 0
    assert ids["c:9"] == 6, "el nuevo estrena por encima del mayor de ayer, no hereda el 5"
    assert 5 not in ids.values()


def test_sin_tabla_de_ayer_se_numera_como_siempre():
    """Mirar hacia atras no puede ser una condicion para que la pasada del dia funcione."""
    hoy = _tabla([("a:1", 0), ("a:2", 0), ("b:3", 1)])
    assert _ids(grupos_ids.estabiliza(hoy, None)) == {"a:1": 0, "a:2": 0, "b:3": 1}
    vacia = pl.DataFrame({"clave": [], "grupo_id": pl.Series([], dtype=pl.Int32)})
    assert _ids(grupos_ids.estabiliza(hoy, vacia)) == {"a:1": 0, "a:2": 0, "b:3": 1}


def test_un_empate_se_rompe_siempre_igual():
    """Dos grupos de hoy que se solapan igual con el mismo de ayer: gana el id mas bajo."""
    ayer = _ayer([("a:1", 3), ("a:2", 3), ("a:3", 3), ("a:4", 3)])
    # Se parte en dos mitades iguales; el reparto de hoy numera 10 y 11.
    hoy = _tabla([("a:1", 10), ("a:2", 10), ("a:3", 11), ("a:4", 11)])
    ids = _ids(grupos_ids.estabiliza(hoy, ayer))
    assert ids["a:1"] == ids["a:2"] == 3, "una mitad se queda con el numero de ayer"
    assert ids["a:3"] == ids["a:4"] == 4, "y la otra estrena, sin repetir"
    # Y dos veces lo mismo da lo mismo, que es lo que permite reproducirlo.
    assert _ids(grupos_ids.estabiliza(hoy, ayer)) == ids


def test_la_tabla_que_se_guarda_es_la_clave_del_producto():
    """Lo que se guarda para mañana: la clave estable del producto y su grupo."""
    filas = [{"fuente": "dia", "id_fuente": 147509}, {"fuente": "aldi", "id_fuente": "80000"}]
    tabla = grupos_ids.tabla_de(filas, pl.Series([0, 1], dtype=pl.Int32))
    assert tabla["clave"].to_list() == ["dia:147509", "aldi:80000"]
    assert tabla["grupo_id"].to_list() == [0, 1]
