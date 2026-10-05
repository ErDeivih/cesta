"""El alcance del catalogo: lo que el contrato exige, caso por caso.

Estas son las pruebas de aceptacion de T01 (`docs/CESTA-TAREAS-Y-ACEPTACION.md`), mas las dos
trampas que este proyecto ya se ha comido una vez:

  - los pañales acabaron en **panaderia** porque "panales" contiene "pan";
  - una funda de sofa de Alcampo entro en un catalogo que va de la lista de la compra.

Y una regla de fondo: cuando no hay nada claro, el estado es `revisar` con su motivo. **Inventar
una clasificacion para no dejar huecos es justo lo que hay que evitar.**
"""
import pytest

from core import alcance


def test_comida_de_mascota_entra_y_la_cama_no():
    """El contrato lo dice con estas dos palabras: comida si, cama no."""
    comida = alcance.clasificar_alcance("Pienso completo para perro adulto 3 kg",
                                        "Mascotas > Perros > Alimentacion")
    assert comida.estado == alcance.INCLUIDO
    assert comida.familia_id == "mascotas"
    cama = alcance.clasificar_alcance("Cama para perro mediana, color gris",
                                      "Mascotas > Perros > Camas y accesorios")
    assert cama.estado == alcance.EXCLUIDO
    assert not cama.entra


def test_panales_entran_y_el_carrito_no():
    panales = alcance.clasificar_alcance("Pañales talla 4, 12 unidades",
                                         "Bebe > Cambio del bebe")
    assert panales.estado == alcance.INCLUIDO
    carrito = alcance.clasificar_alcance("Carrito de paseo plegable",
                                         "Bebe > Puericultura > Carritos")
    assert carrito.estado == alcance.EXCLUIDO


def test_papel_higienico_entra_y_el_cuaderno_no():
    papel = alcance.clasificar_alcance("Papel higienico doble hoja, 12 rollos",
                                       "Drogueria y Limpieza > Papel")
    assert papel.estado == alcance.INCLUIDO
    cuaderno = alcance.clasificar_alcance("Cuaderno de cuadros A4 80 hojas",
                                          "Papeleria > Cuadernos")
    assert cuaderno.estado == alcance.EXCLUIDO
    assert "cuaderno" in cuaderno.evidencias["termino"]


def test_las_dos_trampas_de_siempre():
    """«Pañales» no es pan, y «pantalon» no es panal. Se compara por palabras enteras."""
    pantalon = alcance.clasificar_alcance("Pantalon vaquero infantil", "Moda infantil > Pantalones")
    assert pantalon.estado == alcance.EXCLUIDO
    assert "panal" not in (pantalon.evidencias.get("termino") or "")
    # Y el cuaderno no se cuela por "papel".
    cuaderno = alcance.clasificar_alcance("Cuaderno de papel reciclado",
                                          "Libros y papeleria > Cuadernos")
    assert cuaderno.estado == alcance.EXCLUIDO


def test_un_alimento_en_promociones_no_se_excluye():
    """Categoria mixta: no se descarta el producto entero a ciegas."""
    d = alcance.clasificar_alcance("Aceite de oliva virgen extra 1 l",
                                   "Folletos y Promociones > Ofertas de la semana")
    assert d.estado != alcance.EXCLUIDO
    assert d.regla_id in ("rev-mixtas", "sin-regla")


def test_un_televisor_en_promociones_si_se_excluye():
    """El producto gana a la categoria, y solo para excluir."""
    d = alcance.clasificar_alcance("Televisor 55 pulgadas 4K",
                                   "Folletos y Promociones > Ofertas de la semana")
    assert d.estado == alcance.EXCLUIDO
    assert d.regla_id == "prod-electronica"


def test_la_hoja_manda_sobre_la_rama():
    """El agujero real: bazar escondido dentro de una rama de promociones."""
    d = alcance.clasificar_alcance("Funda elastica para sofa de 3 plazas, color taupe",
                                   "Folleto y Promociones > Renueva la decoracion de tu hogar")
    assert d.estado == alcance.EXCLUIDO, (
        "una hoja de decoracion dentro de promociones sigue siendo bazar: es por donde se "
        "colaron los 245 productos medidos el 5 de octubre")


def test_lo_que_viene_de_la_auditoria_del_5_de_octubre():
    """Los dos ejemplos que se midieron en el catalogo de verdad."""
    funda = alcance.clasificar_alcance(
        "Funda elastica para sofa de 3 plazas, color taupe, ZEBRA.",
        "Hogar y Decoracion > Textil hogar > Textil salon > Fundas de sofa > Sofa de 3 plazas")
    assert funda.estado == alcance.EXCLUIDO
    avion = alcance.clasificar_alcance("Avion con ruedas, surtido de colores, SNC.",
                                       "Juguetes > Juguetes baratos > Juguetes por menos 20 euros")
    assert avion.estado == alcance.EXCLUIDO


def test_sin_clasificacion_suficiente_se_revisa_y_se_dice_por_que():
    d = alcance.clasificar_alcance("Producto misterioso ABC", None)
    assert d.estado == alcance.REVISAR
    assert d.regla_id == "sin-regla"
    assert "persona" in d.motivo
    assert not d.entra
    assert d.version_politica == alcance.version()


def test_toda_decision_trae_su_regla_y_su_version():
    """Sin regla y sin version no se puede auditar una decision."""
    for nombre, categoria in [
        ("Leche entera 1 l", "Lacteos > Leche"),
        ("Detergente liquido 30 lavados", "Drogueria y Limpieza > Lavado"),
        ("Cerveza rubia 6 x 33 cl", "Bebidas > Cervezas"),
        ("Algo raro", "Categoria que no existe"),
    ]:
        d = alcance.clasificar_alcance(nombre, categoria)
        assert d.regla_id and d.motivo
        assert d.version_politica == alcance.version()
        assert d.estado in (alcance.INCLUIDO, alcance.EXCLUIDO, alcance.REVISAR)


def test_las_familias_del_contrato_estan_declaradas():
    """Las nueve familias de la tabla del contrato, mas el alcohol aparte."""
    declaradas = set(alcance.familias())
    for familia in ("frescos", "despensa", "refrigerados", "bebidas", "higiene",
                    "limpieza", "bebe", "mascotas", "hogar_consumible"):
        assert familia in declaradas, f"falta la familia {familia} del contrato"


@pytest.mark.parametrize("nombre, categoria, esperado", [
    ("Leche entera Asturiana 1 l", "Lacteos > Leche", alcance.INCLUIDO),
    ("Merluza fresca al corte", "Pescaderia > Pescado fresco", alcance.INCLUIDO),
    ("Gel de ducha hidratante 750 ml", "Cuidado personal e higiene > Gel", alcance.INCLUIDO),
    ("Bolsas de basura 30 l, 20 unidades", "Drogueria > Limpieza", alcance.INCLUIDO),
    ("Sarten antiadherente 24 cm", "Menaje > Sartenes", alcance.EXCLUIDO),
    ("Taladro percutor 700 W", "Bricolaje > Herramientas electricas", alcance.EXCLUIDO),
    ("Ibuprofeno 400 mg 20 comprimidos", "Parafarmacia > Medicamentos", alcance.EXCLUIDO),
    ("Saco de dormir para camping", "Deportes > Aire libre > Camping", alcance.EXCLUIDO),
])
def test_la_tabla_del_contrato(nombre, categoria, esperado):
    assert alcance.clasificar_alcance(nombre, categoria).estado == esperado


# --- La frontera del consumible que decidio el dueno (5 de octubre de 2026) -------------------
# El criterio es **la compra habitual y reposicion del hogar**, no la seccion donde la cadena
# coloque el producto: por eso las pilas entran aunque vivan en bazar, y las bayetas entran aunque
# no sean de un solo uso.


@pytest.mark.parametrize("nombre, categoria", [
    ("Pilas alcalinas AA 8 unidades", "Hogar > Pilas y cargadores"),
    ("Bolsas de basura 30 l, 20 unidades", "Drogueria > Limpieza Hogar"),
    ("Papel de cocina jumbo 2 rollos", "Drogueria > Limpieza Hogar"),
    ("Servilletas de papel 100 unidades", "Hogar > Mesa"),
    ("Insecticida hormigas 500 ml", "Drogueria > Limpieza Hogar"),
    ("Ambientador automático naranjos", "Drogueria > Limpieza Hogar"),
    ("Bayetas de microfibra 4 unidades", "Drogueria > Utensilios de limpieza"),
    ("Vasos de plastico 50 unidades", "Hogar > Fiesta y desechables"),
    ("Comida para perro adulto 3 kg", "Mascotas > Perros"),
    ("Arena para gato aglomerante 10 l", "Mascotas > Gatos"),
])
def test_lo_que_se_repone_entra(nombre, categoria):
    assert alcance.clasificar_alcance(nombre, categoria).estado == alcance.INCLUIDO


@pytest.mark.parametrize("nombre, categoria", [
    ("Bombilla LED 9 W casquillo E27", "Hogar > Iluminacion"),
    ("Cubo de fregar con escurridor", "Hogar > Limpieza"),
    ("Vasos de cristal 6 unidades", "Hogar > Mesa"),
    ("Fiambrera hermética 1 l", "Hogar > Menaje"),
    ("Juguete para perro hueso de goma", "Mascotas > Juguetes"),
])
def test_lo_que_dura_no_entra_en_esta_version(nombre, categoria):
    assert alcance.clasificar_alcance(nombre, categoria).estado == alcance.EXCLUIDO


def test_la_frontera_esta_versionada():
    """El dueno lo pidio asi: configurable, versionada y con pruebas. Es decision de alcance, no
    una definicion universal, y se cambia en un sitio."""
    assert alcance.version() >= 2
    ids = {r["id"] for r in alcance.politica()["incluye_producto"]}
    ids |= {r["id"] for r in alcance.politica()["excluye_producto"]}
    assert "prod-menaje-de-un-solo-uso" in ids
    assert "prod-fuera-en-esta-version" in ids
