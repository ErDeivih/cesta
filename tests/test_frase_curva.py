"""La curva con su frase debajo, y el ahorro medido dentro de una sola unidad.

Dos cosas del §4 del encargo, y las dos salieron de mirar la pantalla en un navegador:

  - *"La curva, que ya existe, **con una frase debajo**: «lleva 14 dias a este precio» o
    «esta mas barato que en los ultimos 90 dias»"*. La curva estaba desde el primer dia y
    no decia nada.
  - *"**Donde esta mas barato** y cuanto se ahorra en euros por unidad de uso"*.

Y una tercera que no estaba en el encargo y aparecio al medir la segunda: **el ahorro no
puede cruzar unidades**. El 23 de septiembre de 2026 la ficha de un azafran de 0,4 g decia
«te ahorras 6.872,01 EUR/kg» comparando su precio por kilo con el de un bote medido en
unidades, y la pantalla del grupo decia «+229.833,1 % frente al mas barato». La regla
-- comparar solo dentro de la misma unidad -- lleva escrita en el proyecto desde el primer
dia (`core/comparacion.py`, `resumen.ahorro()`, `api/alertas.py`); lo que pasaba es que la
interfaz se la saltaba en tres sitios.

Las pruebas de la parte de interfaz miran el **codigo fuente**, que es como se prueba el
front en este proyecto (no hay ejecutor de JavaScript): lo que se pinta de verdad lo
comprueba `plataforma/prueba_navegador.py` en un movil, y ahi estan las tres medidas
nuevas (la frase, el ahorro y el tope de "esto ya no es una oferta").
"""
from __future__ import annotations

import pathlib
from dataclasses import replace

import duckdb
import pytest

from plataforma.api import alertas as avisos  # noqa: F401  (nombra el modulo en el docstring)
from plataforma.api import catalogo

RAIZ = pathlib.Path(__file__).resolve().parent.parent
APP = RAIZ / "plataforma" / "web" / "app" / "src"


def _fuente(*trozos: str) -> str:
    return (APP.joinpath(*trozos)).read_text(encoding="utf-8")


# --------------------------------------------------------------- la API ---

# Un grupo de mentira con **unidades mezcladas**, que es el caso que destapo el fallo:
# dos cadenas miden el mismo producto en kg y una tercera en ud.
MIEMBROS = [
    # (fuente, id, nombre, unidad, precio_unidad_cent, comparable)
    ("dia", "1", "Azafran en hebras", "kg", 687500.0, True),
    ("mercadona", "2", "Azafran Hacendado", "kg", 487500.0, True),
    ("carrefour", "3", "Azafran en bote", "ud", 299.0, False),
]


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Un gold minimo con un grupo de unidades mezcladas y tres dias de serie.

    Las columnas son las mismas que usa `tests/test_catalogo.py`, con `promo_hasta` como
    `TIMESTAMPTZ` de verdad: `catalogo.grupo()` la pide ya convertida a texto y sin esa
    columna la consulta ni arranca (`BinderException` de DuckDB), que es un fallo de la
    prueba de mentira, no de lo que se quiere medir.
    """
    con = duckdb.connect()
    filas = ",".join(
        f"('{fuente}','{ident}','{nombre}','{fuente.title()}',1.0,'{unidad}','84123{i}',"
        f"{int(precio)},{precio},{int(precio)},'{unidad}',NULL,NULL,NULL,NULL,NULL,"
        f"'despensa','http://x',7,NULL,NULL,NULL,NULL,{str(fiable).lower()},NULL)"
        for i, (fuente, ident, nombre, unidad, precio, fiable) in enumerate(MIEMBROS))
    con.execute(f"""
        CREATE TABLE g AS SELECT * FROM (VALUES {filas}) AS t(
            fuente, id_fuente, nombre, marca, cantidad, unidad_canon, ean,
            precio_cent, precio_unidad_cent, precio_ref_canon_cent,
            unidad_ref_canon, imagen, alergenos, ingredientes, origen,
            promo_txt, categoria, url, grupo_id, calidad, calidad_origen,
            calidad_nota, nutriscore, comparacion_fiable, nova)
    """)
    # Las columnas que van todas a NULL salen de `VALUES` como numeros, y luego la API
    # devolveria un 0 donde va un texto. Se declaran de su tipo, que es lo que hace el
    # pipeline de verdad.
    con.execute("""
        ALTER TABLE g ALTER COLUMN imagen TYPE VARCHAR;
        ALTER TABLE g ALTER COLUMN alergenos TYPE VARCHAR;
        ALTER TABLE g ALTER COLUMN ingredientes TYPE VARCHAR;
        ALTER TABLE g ALTER COLUMN origen TYPE VARCHAR;
        ALTER TABLE g ALTER COLUMN promo_txt TYPE VARCHAR;
        ALTER TABLE g ALTER COLUMN calidad TYPE VARCHAR;
        ALTER TABLE g ALTER COLUMN calidad_origen TYPE VARCHAR;
        ALTER TABLE g ALTER COLUMN calidad_nota TYPE DOUBLE;
        ALTER TABLE g ALTER COLUMN nutriscore TYPE VARCHAR;
        ALTER TABLE g ALTER COLUMN nova TYPE BIGINT;
    """)
    con.execute("""
        ALTER TABLE g ADD COLUMN promo_hasta TIMESTAMPTZ;
        UPDATE g SET promo_hasta = TIMESTAMPTZ '2026-09-25 00:00:00+02';
    """)
    con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")

    # La serie: **tres dias** del producto de dia, con su unidad en cada punto.
    con.execute(f"""
        COPY (SELECT * FROM (VALUES
            ('dia:1','dia',DATE '2026-09-21',700000,700000.0,'kg'),
            ('dia:1','dia',DATE '2026-09-22',690000,690000.0,'kg'),
            ('dia:1','dia',DATE '2026-09-23',687500,687500.0,'kg')
        ) AS t(producto_id, fuente, fecha, precio_cent, precio_unidad_cent, unidad_canon))
        TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)
    """)
    for otro in ("enlaces", "resumen", "precio_derivado", "equivalencia"):
        con.execute(f"COPY (SELECT 1 AS x) TO '{tmp_path / (otro + '.parquet')}' "
                    f"(FORMAT PARQUET)")
    con.close()
    monkeypatch.setattr(catalogo, "AJUSTES", replace(catalogo.AJUSTES, gold=tmp_path))
    catalogo.reiniciar()
    yield
    catalogo.reiniciar()


def test_la_unidad_que_decide_es_la_que_comparten_mas_cadenas(gold):
    """`unidad` no es la del primer producto: es la que se puede comparar entre cadenas.

    Con la del primero (`ud`, el bote de carrefour, que ademas es el mas barato en
    absoluto y por eso salia el primero) la tarjeta del historico pedia «EUR/ud» de una
    serie que va en kg.
    """
    g = catalogo.grupo(7)
    assert g is not None
    assert g["unidad"] == "kg", f"la unidad que decide es la de una sola cadena: {g['unidad']}"
    assert g["cadenas"] == 3
    assert g["cadenas_comparables"] == 2, (
        "solo dos cadenas miden este producto en la unidad que decide")


def test_el_ahorro_no_cruza_unidades(gold):
    """El ahorro sale de los dos productos en kg (487.500 y 687.500), no del bote en ud.

    Cruzando unidades salia 6.875 frente a 2,99: un 229.833 % que la pantalla ensenaba
    como si fuera una oferta.
    """
    g = catalogo.grupo(7)
    assert g is not None
    assert g["ahorro_cent"] == pytest.approx(200000.0), (
        f"el ahorro mezcla unidades: {g['ahorro_cent']} centimos")
    assert g["ahorro_pct"] == pytest.approx(41.0), f"el porcentaje mezcla unidades: {g['ahorro_pct']}"
    assert g["ahorro_pct"] < 2900, (
        "el tope de `core/comparacion.py`: mas de 29 veces no es una oferta, es una unidad "
        "mal leida")


def test_los_puntos_del_historico_llevan_su_unidad(gold):
    """Sin la unidad en cada punto, la frase de la curva no puede comparar dias."""
    g = catalogo.grupo(7)
    assert g is not None
    assert g["serie"], "no hay serie que pintar"
    for punto in g["serie"]:
        assert punto["unidad_canon"] == "kg", (
            f"un punto del historico sin su unidad: {punto}")


def test_el_ahorro_solo_cuenta_precios_fiables(gold, tmp_path, monkeypatch):
    """Un producto marcado como no fiable no entra en la cuenta, igual que en el resumen.

    Es la regla de `resumen.ahorro()` (`comparacion_fiable`): una fila en la que el precio
    por unidad y el de venta se contradicen no puede decidir donde esta mas barato.
    """
    con = duckdb.connect()
    con.execute(f"CREATE TABLE g AS SELECT * FROM '{tmp_path / 'grupos.parquet'}'")
    con.execute("UPDATE g SET comparacion_fiable = false WHERE fuente = 'mercadona'")
    con.execute(f"COPY g TO '{tmp_path / 'grupos.parquet'}' (FORMAT PARQUET)")
    con.close()
    catalogo.reiniciar()

    g = catalogo.grupo(7)
    assert g is not None
    assert g["cadenas_comparables"] == 1, (
        "cuenta cadenas cuyo precio no es de fiar")
    assert g["ahorro_cent"] == 0, (
        f"con un solo precio fiable no hay ahorro que anunciar: {g['ahorro_cent']}")


# ------------------------------------------------------------- la pantalla ---

def test_la_frase_de_la_curva_existe_y_dice_el_plazo_de_verdad():
    """La frase, y su regla mas importante: **no promete 90 dias si no los hay**.

    El encargo pone ese ejemplo con 90 dias porque es lo que suena bien. Hoy el historico
    son 18: decir 90 seria una mentira tranquila.
    """
    curva = _fuente("logica", "curva.ts")
    assert "export function loQueDiceLaCurva" in curva, "no hay funcion que decida la frase"
    assert "días que tenemos" in curva, (
        "la frase no dice cuantos dias hay de verdad")
    for forma in ("Es el precio más bajo", "Es el precio más alto", "Lleva ",
                  "por encima del más bajo"):
        assert forma in curva, f"falta la forma «{forma}» de la frase"
    # Y la guarda de la unidad, que es lo que impide comparar kg con ud.
    assert "unidad_canon" in curva and "unidades.size > 1" in curva, (
        "la frase no comprueba que todos los dias se midan en la misma unidad")


def test_la_frase_se_pinta_debajo_de_la_curva_y_antes_que_la_tabla():
    """El orden que pide el §4: curva, su frase, y la tabla al final."""
    ficha = _fuente("paginas", "Producto.tsx")
    assert "loQueDiceLaCurva(" in ficha, "la ficha no usa la frase de la curva"
    assert ficha.index("<Chispa") < ficha.index("curva.frase"), (
        "la frase sale antes que la curva")
    assert ficha.index("curva.frase") < ficha.index("Su grupo de equivalencias"), (
        "la frase sale despues que la tabla de equivalencias")


def test_el_ahorro_en_euros_no_cruza_unidades():
    """«Mas barato en ... te ahorras ...» solo compara productos de la misma unidad.

    La primera version de este dato salio en pantalla diciendo «te ahorras 6872,01 EUR/kg»
    en un azafran de 0,4 g. Lo encontro la puerta del navegador.
    """
    ficha = _fuente("paginas", "Producto.tsx")
    assert "más barato en" in ficha.lower(), "la ficha no dice donde esta mas barato"
    assert "te ahorras" in ficha
    assert "p.unidad === producto.unidad" in ficha, (
        "el ahorro se calcula entre productos de distinta unidad")
    assert "p.comparable &&" in ficha, (
        "el ahorro cuenta precios que el catalogo marca como no fiables")


def test_la_pantalla_del_grupo_no_compara_unidades_distintas():
    """El minimo del grupo, por unidad: ni el porcentaje ni la nota de cada alternativa.

    Aqui estaba el «+229.833,1 % frente al mas barato» de la pantalla del grupo.
    """
    pesos = _fuente("logica", "pesos.ts")
    assert "minimos" in pesos and "minimoDe" in pesos, (
        "los pesos siguen calculando un unico minimo para todo el grupo")
    assert "p.precio_unidad_cent" in pesos and "p.unidad" in pesos, (
        "el minimo no se separa por unidad")
    assert pesos.count("minimoDe(p)") >= 1, "la alternativa no usa el minimo de su unidad"

    grupo = _fuente("paginas", "Grupo.tsx")
    assert "sin otra cadena que lo mida igual" in grupo, (
        "la pantalla no distingue 'sin precio' de 'sin con que compararlo'")


def test_con_un_gold_viejo_sin_unidad_la_ficha_responde_igual(gold, tmp_path):
    """Un gold escrito antes de que la serie llevara la unidad no puede tumbar la ficha.

    La API sirve el gold de ayer cuando el scraper falla (esta escrito en
    `docker-compose.yml`), asi que la consulta de la serie tolera que la columna no este.
    Y lo que pasa entonces es lo honesto: el punto viaja **sin unidad** y la pantalla no
    dice la frase, porque no puede (`logica/curva.ts`).
    """
    con = duckdb.connect()
    con.execute(f"""COPY (SELECT * FROM (VALUES
        ('dia:1','dia',DATE '2026-09-22',690000,690000.0),
        ('dia:1','dia',DATE '2026-09-23',687500,687500.0)
    ) AS t(producto_id, fuente, fecha, precio_cent, precio_unidad_cent))
    TO '{tmp_path / 'precio_diario.parquet'}' (FORMAT PARQUET)""")
    con.close()
    catalogo.reiniciar()

    g = catalogo.grupo(7)
    assert g is not None, "la ficha se ha caido con un gold viejo"
    assert g["serie"], "sin serie no hay historico que pintar"
    assert all(p["unidad_canon"] is None for p in g["serie"]), (
        "un gold viejo no tiene unidad en la serie: tiene que viajar como None, no "
        "inventarse una")


def test_la_puerta_mira_los_porcentajes_imposibles():
    """El tope de «esto ya no es una oferta» tambien se mide en la pantalla.

    El numero gordo del azafran se calculaba en el JSX, asi que ninguna prueba de codigo
    lo veia: se ve mirando lo que hay pintado.
    """
    puerta = (RAIZ / "plataforma" / "prueba_navegador.py").read_text(encoding="utf-8")
    assert "_porcentajes_gordos" in puerta, "la puerta no mide los porcentajes pintados"
    assert "2900.0" in puerta, "el tope no es el del proyecto (`core/comparacion.py`)"
    assert "con el tope a 0 encuentra algo" in puerta, (
        "la medida de los porcentajes no demuestra que mira")
