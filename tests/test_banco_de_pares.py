"""El banco de pares: la verdad la da el codigo de barras, no una persona.

Lo que se prueba aqui es que las dos clases sean las que dicen ser. Si los
positivos o los negativos se colaran, todas las medidas que se hagan con ellos
estarian mal y nadie lo notaria: son numeros que se miran, no que se ejecutan.

Y desde el 26 de septiembre de 2026 tambien se prueba **la cuenta de precision**,
que es la que dice si el emparejador acierta: 91,1 % sobre el banco de verdad.
"""
import polars as pl
import pytest

from core import config
from projects.cesta.banco_de_pares import (
    banco,
    pares_negativos,
    pares_positivos,
    precision,
)


@pytest.fixture
def gold(tmp_path, monkeypatch):
    """Un gold de mentira: `precision` lee `grupos.parquet` y `enlaces.parquet` de ahi."""
    monkeypatch.setattr(config, "GOLD", tmp_path)
    return tmp_path


def _escribe_gold(carpeta, filas, enlaces):
    pl.DataFrame({
        "fuente": [f["fuente"] for f in filas],
        "nombre": [f["nombre"] for f in filas],
        "grupo_id": [f.get("grupo_id") for f in filas],
    }).write_parquet(carpeta / "grupos.parquet")
    pl.DataFrame({
        "i": [i for i, _ in enlaces], "j": [j for _, j in enlaces],
        "parecido": [1.0] * len(enlaces), "nivel": ["identico"] * len(enlaces),
    }, schema={"i": pl.Int32, "j": pl.Int32, "parecido": pl.Float64, "nivel": pl.Utf8}
    ).write_parquet(carpeta / "enlaces.parquet")


def ficha(fuente, nombre, marca=None, ean=None, unidad="l"):
    return {"fuente": fuente, "nombre": nombre, "marca": marca, "unidad_canon": unidad,
            "cantidad": 1.0, "ean": ean,
            "ean_n": ean, "marca_n": marca.lower() if marca else None}


def test_los_positivos_son_el_mismo_codigo_en_dos_cadenas():
    filas = [
        ficha("dia", "Leche Puleva", "Puleva", "8410000000001"),
        ficha("alcampo", "Leche Puleva 1 L", "Puleva", "8410000000001"),
        # Mismo codigo en dia otra vez: contra `alcampo` si es un par entre
        # cadenas, contra `dia` (indice 0) no, porque es la misma cadena.
        ficha("dia", "Leche Puleva otra", "Puleva", "8410000000001"),
        # Sin codigo no hay verdad que dar.
        ficha("carrefour", "Leche suelta", "Marca", None),
    ]
    assert pares_positivos(filas) == [(0, 1), (1, 2)]


def test_los_negativos_son_misma_marca_y_codigo_distinto():
    """El par dificil: se parece tanto que el emparejador por nombre lo junta.

    "San Miguel" y "San Miguel sin gluten" comparten marca y texto, y son dos
    productos distintos. Es exactamente el caso que hay que NO juntar.
    """
    filas = [
        ficha("dia", "Cerveza San Miguel 33 cl", "San Miguel", "8410655000010"),
        ficha("carrefour", "Cerveza San Miguel sin gluten 33 cl", "San Miguel",
              "8410655002410"),
        # El mismo que el 0 pero en otra cadena: tambien es un par dificil, los
        # dos son San Miguel con codigos distintos.
        ficha("alcampo", "San Miguel 33 cl", "San Miguel", "8410655000010"),
        # Otra marca: no es el par dificil que se busca.
        ficha("dia", "Cerveza Amstel 33 cl", "Amstel", "8410569615614"),
        # Otra unidad: se compara contra lo mismo.
        ficha("dia", "San Miguel 33 cl", "San Miguel", "8410655000999", unidad="ud"),
    ]
    assert pares_negativos(filas) == [(0, 1), (1, 2)]


def test_el_banco_mezcla_las_dos_clases_y_es_repetible():
    filas = []
    for n in range(4):
        filas.append(ficha("dia", f"Producto {n}", f"Marca{n}", f"84100000000{n:02d}"))
        filas.append(ficha("alcampo", f"Producto {n}", f"Marca{n}", f"84100000000{n:02d}"))
        # Un hermano de la misma marca con otro codigo: el negativo.
        filas.append(ficha("carrefour", f"Producto {n} variante", f"Marca{n}",
                           f"84100000009{n:02d}"))
    pares = banco(filas, cuantos=3, semilla=1)
    assert len(pares) == 6
    assert sum(1 for _p, v in pares if v) == 3
    assert sum(1 for _p, v in pares if not v) == 3
    # La misma semilla da el mismo banco: si no, dos medidas no se pueden comparar.
    assert pares == banco(filas, cuantos=3, semilla=1)


def test_el_banco_no_revienta_si_no_hay_de_una_clase():
    filas = [ficha("dia", "Solo uno", "Marca", "8410000000001")]
    pares = banco(filas, cuantos=5)
    assert pares == []


# ------------------------------------------------------------- la precision --

def test_la_precision_cuenta_los_dos_lados(gold):
    """**La cuenta que le faltaba al banco: de lo que junta, cuanto es correcto.**

    `precision` mide dos cosas y las dos importan: cuantos pares CIERTOS acaban juntos (los
    que no se pueden perder) y cuantos pares de dos productos DISTINTOS acaban juntos (el
    error). La verdad la da el codigo de barras.
    """
    filas = [
        # 0 y 1: mismo EAN, o sea el mismo producto. Estan juntos en el grupo 10.
        ficha("dia", "Leche Puleva entera 1 l", "Puleva", "8410000000001"),
        ficha("alcampo", "Leche Puleva entera 1 l", "Puleva", "8410000000001"),
        # 2: la variante de la misma marca, con otro EAN. **Tambien** en el grupo 10: el
        # error que la cuenta tiene que ver.
        ficha("carrefour", "Leche Puleva desnatada 1 l", "Puleva", "8410000000002"),
        # 3: otro producto distinto, bien separado.
        ficha("dia", "Leche Pascual entera 1 l", "Pascual", "8410000000003"),
    ]
    for f, g in zip(filas, (10, 10, 10, 11), strict=True):
        f["grupo_id"] = g
        f["precio_unidad_cent"] = 100.0
        f["seccion"] = "lacteos-huevos"
    _escribe_gold(gold, filas, [(0, 1), (1, 2)])

    r = precision(filas, cuantos=10)
    # El par 0-1 se junta (acierto) y los pares 0-2, 1-2 tambien (dos errores).
    assert r["positivos"]["pares"] == 1 and r["positivos"]["grupo"] == 1
    assert r["negativos"]["pares"] == 2 and r["negativos"]["grupo"] == 2
    assert r["precision_grupo"] == pytest.approx(1 / 3, abs=1e-6)
    assert r["cobertura"] == 1.0


def test_un_negativo_que_el_bloqueo_descarta_no_cuenta_como_error(gold):
    """Un par que el emparejador **nunca compara** no es un falso positivo del nombre.

    Es la diferencia entre "el algoritmo lo miro y se equivoco" y "el algoritmo no lo miro":
    contarlos juntos infla la precision y esconde el error de verdad. Aqui la variante tiene
    otra cantidad, asi que su clave de bloqueo es distinta y no entra en la cuenta.
    """
    filas = [
        ficha("dia", "Leche Puleva entera 1 l", "Puleva", "8410000000001"),
        ficha("alcampo", "Leche Puleva entera 1 l", "Puleva", "8410000000001"),
        ficha("carrefour", "Leche Puleva entera 2 l", "Puleva", "8410000000002"),
    ]
    filas[2]["cantidad"] = 2.0
    for f, g in zip(filas, (10, 10, 99), strict=True):
        f["grupo_id"] = g
        f["precio_unidad_cent"] = 100.0
        f["seccion"] = "lacteos-huevos"
    _escribe_gold(gold, filas, [(0, 1)])

    r = precision(filas, cuantos=10)
    assert r["negativos"]["pares"] == 0
    assert r["precision_grupo"] == 1.0


def test_la_precision_es_repetible(gold):
    """Dos medidas que no se pueden comparar no sirven para decidir un cambio."""
    filas = []
    for n in range(6):
        filas.append(ficha("dia", f"Producto {n} uno", f"Marca{n}", f"8410000000{n}01"))
        filas.append(ficha("alcampo", f"Producto {n} uno", f"Marca{n}", f"8410000000{n}01"))
        filas.append(ficha("carrefour", f"Producto {n} dos", f"Marca{n}", f"8410000000{n}02"))
    for n, f in enumerate(filas):
        f["grupo_id"] = n // 3
        f["precio_unidad_cent"] = 100.0
        f["seccion"] = "despensa"
    _escribe_gold(gold, filas, [])

    assert precision(filas, cuantos=3, semilla=4) == precision(filas, cuantos=3, semilla=4)
