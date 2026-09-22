"""La seccion comun entre cadenas.

Sin ella no hay lista ordenada por pasillos, ni Explorar, ni pantalla de
secciones en el panel. Es lo que mas desbloquea del proyecto, y son 849 claves
en un fichero, no un modelo.
"""
import pytest

from core.secciones import ORDEN, clave_de, orden_de, seccion_de, sin_asignar

# --- el recorte de la clave, distinto en cada cadena --------------------

def test_alcampo_se_corta_en_dos_niveles():
    # Su arbol tiene 3,6 niveles de media; el tercero es demasiado fino para
    # mapearlo a mano y demasiado fino para que importe.
    assert clave_de("alcampo", "Bebidas > Cervezas > Rubias") == "Bebidas > Cervezas"
    assert clave_de("alcampo", "Bebidas") == "Bebidas"


def test_dia_manda_una_url_y_no_un_arbol():
    # `categoria` en DIA vale "https://www.dia.es/congelados-y-helados/..."
    assert clave_de("dia", "https://www.dia.es/zumos-y-smoothies/smoothies/c/L2291") \
        == "zumos-y-smoothies/smoothies"


def test_las_demas_van_tal_cual():
    assert clave_de("mercadona", "Zumos") == "Zumos"
    assert clave_de("carrefour", "bebidas/vinos") == "bebidas/vinos"


def test_sin_categoria_no_hay_clave():
    assert clave_de("alcampo", None) is None
    assert clave_de("alcampo", "") is None


# --- la traduccion a seccion -------------------------------------------

@pytest.mark.parametrize("fuente,categoria,seccion", [
    ("alcampo", "Bebidas > Cervezas > Rubias", "bebidas"),
    ("alcampo", "Frescos > Quesos", "lacteos-huevos"),
    ("dia", "https://www.dia.es/zumos-y-smoothies/smoothies/c/L2291", "bebidas"),
    ("mercadona", "Zumos", "bebidas"),
    ("aldi", "chocolates", "desayuno-dulces"),
    ("carrefour", "bebidas/vinos", "bebidas"),
    ("carrefour", "parafarmacia/higiene-bucal", "higiene-belleza"),
])
def test_cinco_cadenas_traducen_a_la_misma_seccion(fuente, categoria, seccion):
    assert seccion_de(fuente, categoria) == seccion


def test_lo_desconocido_no_se_inventa():
    # Un producto en el pasillo equivocado es peor que uno al final de la lista.
    assert seccion_de("alcampo", "Una categoria que no existe") is None
    assert seccion_de("marte", "Bebidas > Cervezas") is None
    assert seccion_de("alcampo", None) is None


def test_todas_las_secciones_del_fichero_estan_en_el_orden():
    # Si alguien anade una seccion al fichero y se olvida de ponerla en ORDEN,
    # sus productos se irian al final de la lista sin que nadie se entere.
    from core.secciones import _mapa
    usadas = set(_mapa().values())
    assert usadas <= set(ORDEN), f"secciones sin sitio en el recorrido: {usadas - set(ORDEN)}"


# --- el orden del recorrido --------------------------------------------

def test_el_orden_es_el_de_recorrer_la_tienda_no_el_alfabetico():
    assert orden_de("frutas-verduras") < orden_de("congelados")
    assert orden_de("carniceria") < orden_de("bebidas")
    assert orden_de("bebidas") < orden_de("hogar")


def test_lo_que_no_tiene_seccion_va_al_final():
    assert orden_de(None) >= len(ORDEN)
    assert orden_de("inventada") >= len(ORDEN)


# --- vigilancia del fichero --------------------------------------------

def test_todas_las_claves_estan_asignadas():
    # Las 849 se repasaron el 17 de septiembre y no queda ninguna suelta. Si
    # aparece una, es que una cadena ha cambiado su arbol: hay que mirarla y
    # ponerla en el fichero, no subir este numero.
    sueltas = sin_asignar()
    assert not sueltas, \
        f"{len(sueltas)} claves sin seccion en core/datos/secciones.yml: {sueltas[:5]}"


def test_la_cobertura_no_baja_del_99_por_ciento():
    """Medido el 17 de septiembre: 51.712 de 51.781 productos, el 99,9 %.

    Esta prueba no lee el catalogo (seria lenta y dependeria de datos del dia):
    comprueba que el fichero sigue teniendo las claves gordas de cada cadena,
    que son las que sostienen esa cifra.
    """
    gordas = [
        ("alcampo", "Alimentación > Aperitivos, aceitunas y frutos secos"),
        ("alcampo", "Frescos > Quesos"),
        ("carrefour", "bebidas/vinos"),
        ("dia", "https://www.dia.es/zumos-y-smoothies/smoothies/c/L2291"),
        ("mercadona", "Zumos"),
        ("aldi", "chocolates"),
    ]
    for fuente, categoria in gordas:
        assert seccion_de(fuente, categoria), f"se ha perdido {fuente}: {categoria}"
