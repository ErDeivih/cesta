"""Los embeddings como generador de candidatos (Fase 3).

Lo que se prueba aqui no necesita red ni GPU: el texto que se embebe, el coseno en
SQL y el tope de vecinos. La medida de si separa aciertos de errores esta en
`docs/DIAGNOSTICO-MATCHING.md` §22 y se corre con
`uv run python -m projects.cesta.embeddings`.
"""
from core.embeddings import candidatos, carga, texto_de


def producto(fuente, id_fuente, nombre, cantidad=1.0, unidad="l", seccion="bebidas"):
    return {"fuente": fuente, "id_fuente": id_fuente, "nombre": nombre,
            "marca": None, "cantidad": cantidad, "unidad_canon": unidad,
            "seccion": seccion}


def test_el_texto_que_se_embebe_lleva_lo_que_identifica_al_producto():
    texto = texto_de({"nombre": "Leche entera", "marca": "Puleva",
                      "cantidad": 1.0, "unidad_canon": "l"})
    assert texto.startswith("Leche entera")
    assert "Puleva" in texto
    assert "1.0 l" in texto
    # Lo que no hay, no se inventa.
    assert texto_de({"nombre": "Pan", "marca": None, "cantidad": None,
                     "unidad_canon": None}) == "Pan"


def test_los_candidatos_salen_del_mismo_bloque_y_de_otra_cadena():
    """El bloque canonico es seccion + formato: un litro no se compara con medio.

    Y no se compara un producto consigo mismo ni dos de la misma cadena.
    """
    filas = [
        producto("dia", "1", "Agua mineral"),          # 0
        producto("alcampo", "2", "Agua mineral"),      # 1  parecido
        producto("dia", "3", "Agua mineral 1,5 l"),    # 2  misma cadena que 0
        producto("aldi", "4", "Agua mineral", cantidad=0.5),   # 3  otro bloque
    ]
    vectores = {
        "dia:1": [1.0, 0.0],
        "alcampo:2": [0.99, 0.01],       # coseno ~1
        "dia:3": [1.0, 0.0],
        "aldi:4": [1.0, 0.0],
    }
    pares = candidatos(filas, vectores, umbral=0.76)
    # (0,1) y (1,2): el 1 se parece a los dos. Lo que NO sale es (0,2), que son
    # de la misma cadena, ni (0,3), que es otro formato.
    assert sorted((i, j) for i, j, _s in pares) == [(0, 1), (1, 2)]


def test_el_umbral_corta_los_que_no_se_parecen():
    filas = [producto("dia", "1", "A"), producto("alcampo", "2", "B")]
    vectores = {"dia:1": [1.0, 0.0], "alcampo:2": [0.0, 1.0]}
    assert candidatos(filas, vectores, umbral=0.76) == []
    assert len(candidatos(filas, vectores, umbral=0.0)) == 1


def test_el_tope_de_vecinos_recorta_los_mas_flojos():
    """Un bloque gordo no puede meter miles de pares en la asignacion."""
    filas = [producto("dia", "1", "A")] + [
        producto("alcampo", str(n), f"A{n}") for n in range(2, 9)]
    vectores = {"dia:1": [1.0, 0.0]}
    for n in range(2, 9):
        vectores[f"alcampo:{n}"] = [1.0, 0.01 * n]     # todos por encima de 0,76
    todos = candidatos(filas, vectores, umbral=0.76, tope_por_producto=99)
    pocos = candidatos(filas, vectores, umbral=0.76, tope_por_producto=3)
    assert len(todos) == 7
    assert len(pocos) == 3
    # Y los que se quedan son los mas parecidos.
    assert min(s for _i, _j, s in pocos) >= max(s for _i, _j, s in todos
                                                if (_i, _j) not in
                                                {(a, b) for a, b, _ in pocos})


def test_sin_vectores_no_hay_candidatos_y_no_revienta():
    assert candidatos([], {}) == []
    assert candidatos([producto("dia", "1", "A")], {}) == []


def test_sin_cache_no_devuelve_nada(tmp_path):
    """Antes de calcularlos, `carga` devuelve vacio y nadie se entera."""
    assert carga(tmp_path / "no_existe.parquet") == {}
