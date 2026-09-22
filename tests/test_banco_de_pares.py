"""El banco de pares: la verdad la da el codigo de barras, no una persona.

Lo que se prueba aqui es que las dos clases sean las que dicen ser. Si los
positivos o los negativos se colaran, todas las medidas que se hagan con ellos
estarian mal y nadie lo notaria: son numeros que se miran, no que se ejecutan.
"""
from projects.cesta.banco_de_pares import (
    banco,
    pares_negativos,
    pares_positivos,
)


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
