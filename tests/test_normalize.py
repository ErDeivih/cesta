"""El normalizador es lo que hace comparables a las seis cadenas."""
import pytest

from core.normalize import (
    lecturas_referencia,
    nombre_limpio,
    normaliza_referencia,
    parse_formato,
    precio_por_unidad,
    unidad_por_100,
)


@pytest.mark.parametrize("texto,esperado", [
    ("Pack 6 x 1 L", (6.0, "l", 6)),        # Carrefour
    ("500 g unidad", (0.5, "kg", 1)),       # Aldi
    ("5000ml", (5.0, "l", 1)),              # Alcampo
    ("Botella 1,5 L", (1.5, "l", 1)),       # coma decimal espanola
    ("2 kg.", (2.0, "kg", 1)),
    ("Bandeja 2 x 150 g", (0.3, "kg", 2)),
    ("12 ud", (12.0, "ud", 1)),
    ("40 lavados", (40.0, "ud", 1)),        # detergente: EUR por lavado
    ("", (None, None, 1)),
    (None, (None, None, 1)),
])
def test_parse_formato(texto, esperado):
    assert parse_formato(texto) == esperado


def test_precio_por_unidad():
    assert precio_por_unidad(1725, 5.0, "l") == (345, "l")
    assert precio_por_unidad(None, 5.0, "l") == (None, None)
    assert precio_por_unidad(1725, 0, "l") == (None, None)


def test_nombre_limpio_quita_marca_y_formato():
    n = nombre_limpio("Leche entera Hacendado brik 1 L", "Hacendado")
    assert "hacendado" not in n
    assert "brik" not in n
    assert "leche entera" in n


@pytest.mark.parametrize("etiqueta,esperado", [
    ("100 ml", "l"), ("100ml", "l"), ("100-ml", "l"), ("100 ml.", "l"),
    ("100 gr.", "kg"), ("100 g", "kg"), ("100g", "kg"), ("100-G", "kg"),
    ("100", None), ("kg", None), ("l", None), ("unidad", None), (None, None),
])
def test_unidad_por_100(etiqueta, esperado):
    assert unidad_por_100(etiqueta) == esperado


def test_normaliza_referencia_no_multiplica_por_diez():
    """La referencia se guarda como la publica la cadena; el x10 lo decide el pipeline.

    Es lo que permite elegir la lectura buena mirando el precio del producto: si
    aqui se multiplicara a ciegas, Mercadona quedaria con un precio por litro diez
    veces mayor que el real en 488 productos.
    """
    assert normaliza_referencia("carrefour", 498, "100ml") == (498.0, "l")
    assert normaliza_referencia("mercadona", 250, "100 ml") == (250.0, "l")
    assert normaliza_referencia("carrefour", 1200, "kg") == (1200.0, "kg")
    assert normaliza_referencia("dia", 5, "lavado") == (5.0, "ud")
    assert normaliza_referencia("aldi", 188, "g") == (188.0, "kg")
    assert normaliza_referencia("dia", None, "kg") == (None, None)


def test_lecturas_referencia_usa_la_convencion_de_cada_cadena():
    """DIA y Aldi publican por 100; Mercadona y Carrefour, ya por kilo o litro."""
    assert lecturas_referencia("dia", 12, "100 g") == ((120.0, "kg"), (12.0, "kg"))
    assert lecturas_referencia("aldi", 188, "100-ml") == ((1880.0, "l"), (188.0, "l"))
    assert lecturas_referencia("mercadona", 250, "100 ml") == ((250.0, "l"), (2500.0, "l"))
    assert lecturas_referencia("carrefour", 498, "100ml") == ((498.0, "l"), (4980.0, "l"))
    # Una etiqueta normal tiene una sola lectura, y sin referencia no hay ninguna.
    assert lecturas_referencia("dia", 1200, "kg") == ((1200.0, "kg"),)
    assert lecturas_referencia("dia", None, "kg") == ()
