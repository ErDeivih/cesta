"""Los embeddings como generador de candidatos (Fase 3 del plan).

Lo que se prueba aqui es la parte pura: el coseno y el texto que se embebe. La
medida de verdad -- si separa aciertos de errores -- se corre con

    uv run python -m projects.cesta.embeddings

y sus numeros estan en `docs/DIAGNOSTICO-MATCHING.md` §22: mediana 0,823 en los
pares que el nombre NO encuentra, 0,680 en los negativos dificiles, 0,414 al azar,
y en el mejor umbral (0,76) precision 0,90 con recall 0,89.
"""
from projects.cesta.embeddings import coseno, texto_de


def test_el_coseno_va_de_menos_uno_a_uno():
    assert coseno([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert coseno([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert coseno([1.0, 0.0], [-1.0, 0.0]) == -1.0
    assert coseno([2.0, 0.0], [5.0, 0.0]) == 1.0      # la escala no importa


def test_el_coseno_no_revienta_con_vectores_vacios():
    """Un texto que no da vector no puede tumbar la medida entera."""
    assert coseno([], []) == 0.0
    assert coseno([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_el_texto_que_se_embebe_lleva_lo_que_identifica_al_producto():
    """Nombre, marca y formato. El formato va porque un litro no es medio litro.

    Y va en ese orden a proposito: el nombre primero, que es lo que mas dice.
    """
    texto = texto_de({"nombre": "Leche entera", "marca": "Puleva",
                      "cantidad": 1.0, "unidad_canon": "l"})
    assert texto.startswith("Leche entera")
    assert "Puleva" in texto
    assert "1.0 l" in texto


def test_lo_que_falta_no_se_inventa():
    """Sin marca o sin formato, el texto sale mas corto, no con un hueco raro."""
    assert texto_de({"nombre": "Pan", "marca": None, "cantidad": None,
                     "unidad_canon": None}) == "Pan"
    assert texto_de({"nombre": "Pan", "marca": "Bimbo", "cantidad": None,
                     "unidad_canon": None}) == "Pan | Bimbo"
