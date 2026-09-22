"""El normalizador es lo que hace comparables a las seis cadenas."""
import pytest

from core.normalize import nombre_limpio, parse_formato, precio_por_unidad


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
