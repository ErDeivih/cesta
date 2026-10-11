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


# --- Los cuatro falsos descartes medidos el 6 de octubre de 2026 (ampliacion) ------------------
# Casos **reales del catalogo**, con la cadena y su pasillo tal y como los publica. Cada uno con su
# negativo: la leccion es que arreglar un falso descarte no puede abrir la puerta a lo que si es
# bazar.


def test_una_frase_de_la_politica_tiene_que_ser_contigua():
    """`cubo de basura` es una frase, no las palabras cubo+de+basura en cualquier orden.

    Antes casaba con "Bolsa de basura para cubo alto" (DIA): las palabras estaban todas, pero la
    frase no. Y la bolsa de basura es cesta; el cubo, no.
    """
    assert alcance.clasificar_alcance(
        "Bolsa de basura para cubo alto 30 l.", "Drogueria > Bolsas de basura").entra
    # Y el cubo de verdad sigue fuera: ahi la frase si esta, al principio del titulo.
    assert alcance.clasificar_alcance("Cubo de basura 10 l.", "").estado == alcance.EXCLUIDO


def test_un_aparato_mencionado_como_uso_no_excluye_el_producto():
    """El absorbeolores es para el frigorifico; no es un frigorifico."""
    d = alcance.clasificar_alcance("Absorbeolores frigorífico XL Croc Odor 140 g.",
                                  "drogueria-y-limpieza/ambientadores")
    assert d.entra, f"un consumible de limpieza salio {d.estado} por la palabra del aparato"
    # El aparato de verdad sigue fuera, por su pasillo.
    assert alcance.clasificar_alcance(
        "Frigorífico combi no frost 300 l.", "Electrodomesticos > Gran electrodomestico"
    ).estado == alcance.EXCLUIDO


def test_la_dietetica_es_comida_de_reposicion():
    """Medido: la barrita proteica de Aldi salia excluida por estar en parafarmacia."""
    for nombre, categoria in (
        ("Barrita proteica sabor brownie", "parafarmacia"),
        ("BICENTURY Barrita proteica de chocolate brownie 57 g.",
         "Sin Gluten / Sin Lactosa, Nutrición deportiva"),
        ("Batido de proteína sabor vainilla", "Parafarmacia > Dietética y control de peso"),
    ):
        d = alcance.clasificar_alcance(nombre, categoria)
        assert d.entra, f"{nombre} ({categoria}) salio {d.estado}"
    # Y un medicamento sigue fuera.
    assert alcance.clasificar_alcance(
        "Ibuprofeno 400 mg 20 comprimidos", "Parafarmacia > Medicamentos").estado == alcance.EXCLUIDO


def test_el_calzado_no_es_cesta_ni_aunque_la_cadena_no_diga_su_rama():
    """Aldi publica "Botas de trekking" sin categoria: por titulo tiene que salir fuera."""
    assert alcance.clasificar_alcance("Botas de trekking", "").estado == alcance.EXCLUIDO
    assert alcance.clasificar_alcance("Zapatillas de deporte júnior", "").estado == alcance.EXCLUIDO
    # Negativo: la bota de vino no es calzado, y una palomita de maiz menos.
    assert alcance.clasificar_alcance("Palomitas de maíz con mantequilla", "").estado != alcance.EXCLUIDO


def test_el_bebe_durable_no_entra_pero_su_consumible_si():
    """Medido: 233 accesorios duraderos de bebe entraban por la familia "Bebe" (prioridad 35).

    Nombres reales del catalogo del 6 de octubre de 2026. Y el negativo importa tanto como el
    positivo: la alimentacion, las toallitas y los pañales de bebe tienen que seguir entrando.
    """
    for nombre, categoria in (
        ("Cuna de viaje plegable, color gris grafito", "Bebé > Cunas > Cunas"),
        ("Cochecito de paseo Versa combi dúo INTERBABY", "Bebé > Paseo del bebé > Sillas"),
        ("Sábana bajera para cochecito bebé, 40x80cm", "Bebé > Paseo del bebé > Accesorios"),
        ("Protector de cuna liso, color blanco, INTERBABY", "Bebé > Cunas > Ropa de cuna"),
        ("Mochila portabebé, entre 3,5 y 15 kg, Go4 BEBE", "Bebé > Paseo del bebé > Mochilas"),
        ("Trona evolutiva de madera", ""),
    ):
        d = alcance.clasificar_alcance(nombre, categoria)
        assert d.estado == alcance.EXCLUIDO, f"{nombre} ({categoria}) salio {d.estado}"

    for nombre, categoria in (
        ("Papilla de frutas variadas 250 g", "Bebé > Alimentación infantil"),
        ("Toallitas húmedas sin perfume 72 unidades", "Bebé > Higiene y cuidado bebé"),
        ("Pañales talla 4, 40 unidades", "Bebé > Higiene y cuidado bebé"),
        ("Leche de continuación etapa 2, 800 g", "Bebé > Alimentación infantil"),
    ):
        d = alcance.clasificar_alcance(nombre, categoria)
        assert d.entra, f"un consumible de bebe salio {d.estado}: {nombre} ({categoria})"


def test_la_cuna_de_queso_no_es_una_cuna():
    """La trampa de las tildes, otra vez: "cuña" -> "cuna" al normalizar. Por eso van frases."""
    d = alcance.clasificar_alcance("AUCHAN Queso de cabra tierno cuña 500 g",
                                   "Frescos > Quesos > Queso de cabra")
    assert d.entra, "un queso salio del catalogo por la palabra cuna"


# --- Hallazgos del banco de verdad, 6 de octubre de 2026 ---------------------------------------
# Cada caso es una ficha real, etiquetada a mano, que estaba mal clasificada: los cuatro falsos
# descartes y el hueco de vocabulario que destaparon las 37 primeras etiquetas.


def test_los_cuatro_falsos_descartes_del_banco():
    """Lo que el banco midio: 4 de 20 etiquetadas como cesta salian del catalogo."""
    casos = [
        ("Albahaca ecológica Carrefour Bio maceta 1 ud",
         "frescos/verduras-y-hortalizas/hierbas-aromaticas", "hierba fresca en maceta"),
        ("Apósitos hidrocoloides adhesivos para ampollas y rozaduras",
         "Fitoterapia y parafarmacia", "botiquin de reposicion"),
        ("Preservativos sensitive On", "Fitoterapia y parafarmacia", "higiene de reposicion"),
        ("Cambiador multiusos desechable Deliplus", "Bebé", "desechable, se gasta"),
    ]
    for nombre, categoria, porque in casos:
        d = alcance.clasificar_alcance(nombre, categoria)
        assert d.entra, f"{porque}: {nombre} salio {d.estado} ({d.regla_id})"


def test_los_negativos_de_esos_cuatro_casos():
    """Arreglar un falso descarte no puede abrir la puerta a lo que si es bazar o medicina."""
    fuera = [
        ("Maceta de cerámica blanca 20 cm", "Hogar y Decoración > Jardín"),
        ("Sustrato universal 25 l", "drogueria-y-limpieza/bazar"),
        ("Ibuprofeno 400 mg 20 comprimidos", "Parafarmacia > Medicamentos"),
        ("Gasas estériles 10x10 cm 20 unidades", "Parafarmacia > Botiquín"),
        ("Cambiador de bebé de tela lavable", "Bebé > Cambiadores"),
    ]
    for nombre, categoria in fuera:
        d = alcance.clasificar_alcance(nombre, categoria)
        assert d.estado == alcance.EXCLUIDO, f"{nombre} ({categoria}) salio {d.estado}"


def test_la_politica_entiende_plurales():
    """El hueco que destapo el banco: 16 fichas de comida esperaban en revision por una "s".

    La politica tiene los terminos en singular y las cadenas nombran sus pasillos en plural.
    """
    for nombre, categoria, familia in (
        ("Palitos de surimi refrigerados Krissia 180 g",
         "https://www.dia.es/pescados-y-mariscos/...", "frescos"),
        ("Golosinas ositos de oro Haribo 150 g", "infantil/golosinas-y-caramelos", "despensa"),
        ("Caramelos blandos con forma de cherries", "golosinas-y-caramelos", "despensa"),
        ("Trozos en salsa para gatos con pescado", "comida-de-gato", "mascotas"),
        ("Vino blanco El Coto DO Rioja", "Bodega", "alcohol"),
        ("Gel extra fuerte", "cuidado-del-cabello", "higiene"),
    ):
        d = alcance.clasificar_alcance(nombre, categoria)
        assert d.entra, f"{nombre} ({categoria}) salio {d.estado}"
        assert d.familia_id == familia, f"{nombre}: familia {d.familia_id}, esperada {familia}"


def test_quitar_el_plural_no_destroza_palabras_cortas():
    """El corte de la "s" solo en palabras largas: "pan" no es "pa"."""
    assert alcance._raiz("pan") == "pan"
    assert alcance._raiz("mes") == "mes"
    assert alcance._raiz("pescados") == "pescado"
    assert alcance._raiz("golosinas") == "golosina"
    assert alcance._raiz("carnes") == "carne"
    assert alcance._raiz("gato") == "gato"


def test_los_huevos_en_jaulas_no_son_una_jaula_de_mascota():
    """Regresion que introdujo el arreglo de plurales y cazo el control de seguridad.

    Al entender plurales, "jaula" (accesorios de mascota) empezo a casar con "en jaulas" del titulo
    de los huevos: seis fichas de huevos salieron del catalogo. La palabra suelta se cambio por
    frases.
    """
    for nombre, categoria in (
        ("GRANJAS VILLARREAL Huevos de gallina en jaulas acondicionadas, 12 uds",
         "Leche, Huevos, Lácteos, Yogures y Bebidas vegetales"),
        ("PITAS Huevos de gallinas en jaulas acondicionadas, 30 uds",
         "Campañas > Todo a un EURO > Leche, huevos, y lácteos"),
    ):
        d = alcance.clasificar_alcance(nombre, categoria)
        assert d.entra, f"huevos fuera del catalogo por la palabra jaula: {d.regla_id}"
    # Y una jaula de mascota de verdad sigue fuera.
    assert alcance.clasificar_alcance(
        "Jaula para conejo con bandeja, 80 cm", "").estado == alcance.EXCLUIDO


def test_el_bazar_que_menciona_comida_cae_por_su_compuesto_no_por_la_palabra():
    """**Medido el 11 de octubre de 2026 sobre 26 fichas reales de Lidl.**

    El slug de una ficha viaja **como nombre y como categoria**, asi que la palabra «agua» de un
    deposito de jardin casaba con el pasillo `cat-bebidas` y **entraba como bebida**. *Quitar «agua»
    de `cat-bebidas` habria roto el agua de verdad, asi que el arreglo va donde toca: en
    `excluye_producto`, que se prueba **antes** que la categoria.*
    """
    from projects.cesta import descubrir_lidl

    def clasifica(slug: str) -> str:
        return descubrir_lidl.clasifica(f"https://www.lidl.es/p/{slug}/p1")[0]

    assert clasifica("4rain-deposito-de-agua-vaso-2in1-decor-volum") == "excluido"
    assert clasifica("step-2-mesa-de-agua-para-juegos-summer-showers") == "excluido"
    assert clasifica("fisher-price-peluche-nutria-sonadora") == "excluido"
    assert clasifica("gsw-wok-de-hierro-fundido-con-rejilla-o-32-cm-5-piezas") == "excluido"


def test_la_regla_no_se_lleva_comida_por_delante():
    """**Y esta es la mitad que hace valida a la otra.** *G09: «seguridad para no excluir alimentos
    por coincidencias de palabras».*

    «sierra de mano» excluye la herramienta; **«Sierra de lomo de cerdo» no es una sierra**. *Si la
    regla se hubiera escrito con la palabra suelta, se habria llevado el lomo por delante.*
    """
    from core import alcance

    assert alcance.clasificar_alcance("Sierra de lomo de cerdo", "Frescos > Carne").estado != "excluido"
    assert alcance.clasificar_alcance("Agua mineral natural 1,5 l", "Bebidas > Aguas").estado != "excluido"
    assert alcance.clasificar_alcance("Agua de coco", "Bebidas > Aguas").estado != "excluido"
    assert alcance.clasificar_alcance("Caja de galletas", "Dulces").estado != "excluido"
