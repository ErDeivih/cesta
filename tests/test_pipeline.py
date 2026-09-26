"""Capa silver: comparabilidad. Los casos vienen de datos reales del 6 sep 2026."""
from datetime import datetime, timezone

import polars as pl
import pytest

from projects.cesta import pipeline
from projects.cesta.pipeline import a_silver


def _frame(**extra):
    base = {
        "fuente": ["mercadona"] * 6,
        "id_fuente": ["1", "2", "3", "4", "5", "6"],
        "nombre": ["Aceite de oliva Hacendado", "Leche entera", "Uva roja",
                   "Oregano Hacendado", "Recambios maquinilla", "Gambon congelado"],
        "marca": [None] * 6,
        #                                          oregano: su etiqueta va en 100 g
        "formato_txt": ["5 l", "Pack 6 x 1 L", "500 g unidad", "0.025 kg", "1.0 ud", ""],
        "cantidad_declarada": [5.0, 6.0, 0.5, 0.025, 1.0, None],
        "unidad_declarada": ["l", "l", "kg", "kg", "ud", "kg"],
        "precio_cent": [1725, 594, 149, 100, 1490, 128205],  # el ultimo es el 99x
        "precio_ref_nativo_cent": [345, 99, 298, 4000, 497, 1295],
        "unidad_ref_nativa": ["l", "l", "kg", "100 g", "ud", "kg"],
        "peso_variable": [False] * 5 + [True],
        "capturado_en": [datetime.now(timezone.utc)] * 6,  # con zona horaria a proposito
    }
    base.update(extra)
    return pl.DataFrame(base)


def _fila(out, id_):
    return out.filter(pl.col("id_fuente") == id_)


def test_no_explota_con_fecha_con_zona_horaria():
    assert a_silver(_frame()).height == 6


def test_unidad_canonica_nunca_es_la_etiqueta_de_la_cadena():
    """El bug grave: 'Oregano' venia con unidad '100 g' y precio por kg.

    Mezclar EUR/100 g con EUR/kg en la misma columna da un error de 10x invisible.
    """
    out = a_silver(_frame())
    assert set(out["unidad_canon"].to_list()) <= {"kg", "l", "ud", "m"}
    o = _fila(out, "4")
    assert o["unidad_canon"][0] == "kg"
    assert o["precio_unidad_cent"][0] == 4000.0     # 1,00 EUR / 0,025 kg = 40 EUR/kg


def test_precio_por_unidad_siempre_calculado_por_nosotros():
    out = a_silver(_frame())
    assert _fila(out, "1")["precio_unidad_cent"][0] == 345.0     # 17,25 / 5 L
    assert _fila(out, "2")["precio_unidad_cent"][0] == 99.0      # 5,94 / 6 L
    assert _fila(out, "3")["precio_unidad_cent"][0] == 298.0     # 1,49 / 0,5 kg
    assert _fila(out, "1")["proc_precio_unidad"][0] == "derivado"


def test_precio_por_unidad_admite_decimales():
    """1,15 EUR entre 300 bastoncillos son 0,38 centimos: en enteros se perdia."""
    f = _frame(formato_txt=["300.0 ud"] + ["5 l"] * 5,
               precio_cent=[115] + [1725] * 5,
               precio_ref_nativo_cent=[0] + [345] * 5,
               unidad_ref_nativa=["ud"] + ["l"] * 5,
               cantidad_declarada=[300.0] + [5.0] * 5,
               unidad_declarada=["ud"] + ["l"] * 5)
    assert _fila(a_silver(f), "1")["precio_unidad_cent"][0] > 0


def test_el_precio_por_kilo_va_sobre_el_peso_escurrido_cuando_la_cadena_lo_da():
    """**El arreglo del 26 de septiembre de 2026, con su medición.**

    La ventresca de atún de Mercadona declara 0,111 kg (neto, con el aceite) y las otras
    cuatro cadenas declaran 0,073 kg (escurrido, que es lo que se come). Con el neto, nuestro
    precio por kilo de Mercadona salía casi la mitad y **parecía la más barata sin serlo**.
    El precio de referencia que publica cada cadena lo confirma: las otras cuatro coinciden
    con nuestro cálculo al 99,4-99,8 % (porque su cantidad declarada ya es el escurrido), y
    Mercadona solo al 94,3 %, y la diferencia son justo las conservas.
    """
    f = _frame(formato_txt=["400 g"] + ["5 l"] * 5,
               cantidad_declarada=[0.4] + [5.0] * 5,
               unidad_declarada=["kg"] + ["l"] * 5,
               precio_cent=[810] + [1725] * 5,
               precio_ref_nativo_cent=[2025] + [345] * 5,
               unidad_ref_nativa=["kg"] + ["l"] * 5,
               peso_escurrido_g=[280] + [None] * 5)
    out = a_silver(f)
    # 8,10 EUR entre 0,28 kg escurridos = 28,93 EUR/kg, no 20,25
    assert _fila(out, "1")["precio_unidad_cent"][0] == pytest.approx(2892.8571, rel=1e-4)
    # Y sin escurrido declarado, se sigue usando la cantidad del nombre.
    assert _fila(out, "2")["precio_unidad_cent"][0] == 345.0


def test_el_escurrido_no_cambia_nada_si_no_es_menor_que_lo_declarado():
    """Un escurrido igual (o mayor) que la cantidad declarada no es información nueva: se
    ignora. Así no se puede inflar un precio por unidad con un dato raro."""
    f = _frame(formato_txt=["5 l"] * 6, cantidad_declarada=[5.0] * 6,
               unidad_declarada=["l"] * 6, precio_cent=[1725] * 6,
               precio_ref_nativo_cent=[345] * 6, unidad_ref_nativa=["l"] * 6,
               peso_escurrido_g=[5000, 6000, None, 0, 5000, 5000])
    out = a_silver(f)
    for i in ("1", "2", "3", "4", "5", "6"):
        assert _fila(out, i)["precio_unidad_cent"][0] == 345.0


def test_peso_variable_usa_el_precio_por_kilo_y_descarta_el_total():
    """Sin tamano declarado, el 'precio total' de Mercadona es 99x el del kilo."""
    g = _fila(a_silver(_frame()), "6")
    assert g["precio_cent"][0] is None
    assert g["precio_unidad_cent"][0] == 1295.0
    assert g["unidad_canon"][0] == "kg"
    assert g["proc_precio_unidad"][0] == "nativo"


def test_recupera_las_unidades_que_el_formato_esconde():
    """'1 ud' a 14,90 EUR con etiqueta de 4,97 EUR/ud son 3 recambios."""
    assert _fila(a_silver(_frame()), "5")["unidades_inferidas"][0] == 3


def test_marca_la_discrepancia_con_la_etiqueta_de_la_cadena():
    out = a_silver(_frame())
    assert _fila(out, "1")["desviacion_ref"][0] < 0.02      # coinciden
    assert _fila(out, "4")["desviacion_ref"][0] == 0.0      # 4000 vs 4000
    assert _fila(out, "5")["desviacion_ref"][0] > 0.05      # 1490 vs 497


def test_sin_formato_es_un_articulo_y_no_interpreta_especificaciones_del_nombre():
    """Un movil 5G no puede convertirse silenciosamente en un producto de 5 g."""
    f = _frame(
        fuente=["alcampo"] * 6,
        nombre=['Smartphone 5G, 256 GB, pantalla 15,49 cm'] + ["Producto"] * 5,
        formato_txt=[None] * 6,
        precio_cent=[67900] + [100] * 5,
        precio_ref_nativo_cent=[67900] + [100] * 5,
        unidad_ref_nativa=[None] * 6,
        peso_variable=[False] * 6,
    )
    movil = _fila(a_silver(f), "1")
    assert movil["cantidad"][0] == 1.0
    assert movil["unidad_canon"][0] == "ud"
    assert movil["precio_unidad_cent"][0] == 67900.0


def test_sin_formato_usa_referencia_nativa_canonica():
    f = _frame(
        fuente=["alcampo"] * 6,
        formato_txt=[None] * 6,
        precio_ref_nativo_cent=[345] * 6,
        unidad_ref_nativa=["kg"] * 6,
        peso_variable=[False] * 6,
    )
    fila = _fila(a_silver(f), "1")
    assert fila["unidad_canon"][0] == "kg"
    assert fila["precio_unidad_cent"][0] == 345.0
    assert fila["precio_cent"][0] == 1725


def test_aldi_canoniza_unidades_de_etiqueta_y_corrige_350_kg():
    f = _frame(
        fuente=["aldi"] * 6,
        nombre=["Bizcocho carrot cake"] + ["Producto"] * 5,
        formato_txt=["350 kg unidad"] + ["pack de 80 toallitas"] * 5,
        precio_cent=[235] + [199] * 5,
        precio_ref_nativo_cent=[671] + [2] * 5,
        unidad_ref_nativa=["g"] + ["toallita"] * 5,
        peso_variable=[False] * 6,
    )
    bizcocho = _fila(a_silver(f), "1")
    assert bizcocho["cantidad"][0] == 0.35
    assert bizcocho["precio_unidad_cent"][0] == pytest.approx(671.4286)
    assert set(a_silver(f)["unidad_canon"].to_list()) <= {"kg", "ud"}


def test_producto_sin_precio_sigue_en_catalogo_pero_no_es_comparable():
    f = _frame(
        precio_cent=[None] + [1725] * 5,
        precio_ref_nativo_cent=[None] + [345] * 5,
        formato_txt=[None] + ["5 l"] * 5,
        peso_variable=[False] * 6,
    )
    out = a_silver(f)
    assert out.height == 6
    sin_precio = _fila(out, "1")
    assert sin_precio["precio_unidad_cent"][0] is None
    assert sin_precio["precio_comparable"][0] is False


def test_aldi_con_100_ml_a_veces_ya_viene_por_litro():
    """Auditoria del 7 sep: 16 de los 173 productos de Aldi con "100-g"/"100-ml"
    publican un valor que YA es por kilo o por litro. Multiplicarlos por diez a
    ciegas les dejaba una referencia diez veces mayor que su precio real.
    """
    import polars as pl

    from core.schemas import ESQUEMA_BRONZE, vacio
    from projects.cesta.pipeline import a_silver

    def fila(nombre, formato, precio, ref):
        r = vacio()
        r.update({"fuente": "aldi", "id_fuente": nombre, "nombre": nombre,
                  "formato_txt": formato, "precio_cent": precio,
                  "precio_ref_nativo_cent": ref, "unidad_ref_nativa": "100-ml"})
        return r

    df = pl.DataFrame([
        # 1 L a 1,59 EUR: su "159" ya es por litro, no por 100 ml
        fila("gel", "1000 ml unidad", 159, 159),
        # 200 ml a 1,49 EUR: su "75" si es por 100 ml -> 7,45 EUR/L
        fila("afeitado", "200 ml unidad", 149, 75),
    ], schema_overrides=ESQUEMA_BRONZE)
    s = a_silver(df).sort("id_fuente")
    ref = dict(zip(s["id_fuente"], s["precio_ref_canon_cent"], strict=True))
    assert ref["gel"] == 159.0            # no se multiplica
    assert ref["afeitado"] == 750.0       # si se multiplica


# --- packs que solo se anuncian en el nombre ---------------------------
# DIA publica "Cerveza El Aguila pack 24 x 33 cl" con formato_txt "33 cl". Sin
# multiplicar salian 64,73 EUR/l cuando su propia web dice 2,70: un error de 24
# veces en 211 productos. Como con la regla de Carrefour, el nombre no decide
# solo: hace falta que el precio resultante cuadre con el de la cadena.

def _pack(nombre, formato, precio_cent, ref_cent, unidad="l"):
    return pl.DataFrame({
        "fuente": ["dia"], "id_fuente": ["p1"], "nombre": [nombre], "marca": [None],
        "formato_txt": [formato], "cantidad_declarada": [None], "unidad_declarada": [unidad],
        "precio_cent": [precio_cent], "precio_ref_nativo_cent": [ref_cent],
        "unidad_ref_nativa": [unidad], "peso_variable": [False],
        "capturado_en": [datetime.now(timezone.utc)],
    })


def test_multiplica_el_pack_que_solo_dice_el_nombre():
    # 24 latas de 33 cl = 7,92 l por 21,36 EUR = 2,70 EUR/l, que es lo que dice DIA.
    out = a_silver(_pack("Cerveza 0,0 El aguila pack 24 x 33 cl", "33 cl", 2136, 270))
    assert out["unidades_pack"][0] == 24
    assert out["cantidad"][0] == pytest.approx(7.92, rel=1e-3)
    assert out["precio_unidad_cent"][0] == pytest.approx(270, rel=0.01)


def test_no_multiplica_si_el_precio_no_cuadra_con_la_cadena():
    # Mismo nombre, pero la cadena dice 64,73 EUR/l: entonces el "pack 24" no se
    # refiere al contenido y multiplicar seria inventarse el formato.
    out = a_silver(_pack("Cerveza pack 24 x 33 cl", "33 cl", 2136, 6473))
    assert out["unidades_pack"][0] == 1
    assert out["cantidad"][0] == pytest.approx(0.33, rel=1e-3)


def test_no_multiplica_un_pack_absurdo():
    # "pack 500 x" no es un formato comercial; el tope esta en 48.
    out = a_silver(_pack("Tornillos pack 500 x 1 l", "1 l", 100, 100))
    assert out["unidades_pack"][0] == 1


def test_el_pack_que_ya_venia_en_el_formato_no_se_multiplica_dos_veces():
    # "Pack 6 x 1 L" en formato_txt ya lo resuelve parse_formato: 6 l, pack 6.
    # Si ademas el nombre lo dijera, no debe volver a multiplicar.
    out = a_silver(_pack("Leche pack 6 x 1 L", "Pack 6 x 1 L", 594, 99))
    assert out["unidades_pack"][0] == 6
    assert out["cantidad"][0] == pytest.approx(6.0, rel=1e-3)


# --- cuando nuestro precio por unidad no se sostiene ---------------------


def _fila_ref(cantidad, unidad, precio_cent, ref_cent, ref_unidad, nombre="X"):
    """Una fila de bronze con formato y con la etiqueta de la cadena."""
    import polars as pl

    from core.schemas import ESQUEMA_BRONZE, vacio
    r = vacio()
    r.update({"fuente": "dia", "id_fuente": "1", "nombre": nombre,
              "formato_txt": f"{cantidad} {unidad}", "precio_cent": precio_cent,
              "precio_ref_nativo_cent": ref_cent, "unidad_ref_nativa": ref_unidad,
              "disponible": True})
    return pl.DataFrame([r], schema_overrides=ESQUEMA_BRONZE)


def test_un_formato_que_su_propio_precio_desmiente_se_corrige_por_el_nombre():
    """DIA publica '0,095 g' para unas conchitas de 95 g: 15.263 EUR/kg.

    Su propia etiqueta dice 15,26 EUR/kg, y el nombre dice 95 g: 1,45 / 0,095 =
    15,26. **La cadena se contradice, y su propio precio dice cual de las dos
    lecturas vale.** Desde el 22 de septiembre de 2026 se corrige en vez de
    apartar la fila, porque decidir aqui no es adivinar: es leer el dato que la
    propia cadena publica.

    Antes quedaba en `en_disputa` y no se comparaba, que era lo correcto mientras
    no hubiera con que decidir.
    """
    from projects.cesta.pipeline import a_silver
    s = a_silver(_fila_ref("0.095", "g", 145, 1526, "kilo", "Conchitas 95 g"))
    assert s["proc_precio_unidad"][0] == "derivado"
    assert s["cantidad"][0] == 0.095           # 95 g, no 0,095 g
    # 1,45 / 0,095 = 15,263 EUR/kg, que es lo que dice su etiqueta (15,26).
    assert round(s["precio_unidad_cent"][0]) == 1526
    # El precio total se conserva: sirve para la lista de la compra.
    assert s["precio_cent"][0] == 145


def test_si_ninguna_lectura_cuadra_con_la_etiqueta_la_fila_se_aparta():
    """El caso que NO se puede decidir sigue apartandose, y eso importa.

    Hay casos reales en las dos direcciones: Aldi publica 0,03 EUR/kg de una
    barrita proteica y ahi el bueno es el nuestro. Asi que cuando ni el formato
    que trae la cadena ni el tamano del nombre cuadran con su referencia, no se
    elige ganador: la fila se aparta de las comparaciones.
    """
    from projects.cesta.pipeline import a_silver
    # La etiqueta dice 0,30 EUR/kg y ni 0,095 g ni 95 g dan eso.
    s = a_silver(_fila_ref("0.095", "g", 145, 30, "kilo", "Conchitas 95 g"))
    assert s["proc_precio_unidad"][0] == "en_disputa"
    assert s["precio_comparable"][0] is False
    assert s["precio_cent"][0] == 145


def test_una_diferencia_pequena_se_respeta():
    """Entre el 5 % y el doble estan los packs y las dosis, donde el nuestro es
    el bueno a proposito: un pack de 24 latas dividido entre 24 no es lo que la
    cadena publica."""
    from projects.cesta.pipeline import a_silver
    s = a_silver(_fila_ref("1", "l", 150, 120, "litro"))
    assert s["proc_precio_unidad"][0] == "derivado"
    assert s["precio_unidad_cent"][0] == 150


def test_las_unidades_escondidas_ganan_a_la_correccion():
    """'1 ud' a 14,90 EUR con etiqueta de 4,97 EUR/ud son tres recambios.

    El factor es 3, asi que la correccion se activaria; pero "el envase trae
    tres" es una explicacion mejor que "nos hemos equivocado", y si la
    correccion se aplicara primero borraria la cantidad y el otro mecanismo se
    quedaria ciego. El orden importa.
    """
    from projects.cesta.pipeline import a_silver
    s = a_silver(_fila_ref("1", "ud", 1490, 497, "ud"))
    assert s["unidades_inferidas"][0] == 3
    assert s["proc_precio_unidad"][0] != "en_disputa"
    assert s["precio_comparable"][0] is True


# --- rehacer el historico desde bronze -------------------------------------
#
# Hasta el 18 de septiembre de 2026 no se podia. `main()` se queda con la
# instantanea mas reciente de cada cadena y la ANADE a gold, asi que el
# historico solo vivia en `gold/precio_diario.parquet`. Se vio probando la
# cadena entera sobre una copia limpia: con los mismos trece dias de bronze en
# disco, el gold reconstruido salio con dos dias.

def _bronze_de(tmp_path, fuente, fecha, ids):
    d = tmp_path / "bronze" / f"fuente={fuente}" / f"fecha={fecha}"
    d.mkdir(parents=True, exist_ok=True)
    n = len(ids)
    pl.DataFrame({
        "fuente": [fuente] * n,
        "id_fuente": list(ids),
        "nombre": ["Leche entera"] * n,
        "marca": [None] * n,
        "formato_txt": ["1 l"] * n,
        "cantidad_declarada": [1.0] * n,
        "unidad_declarada": ["l"] * n,
        "precio_cent": [99 + i for i in range(n)],
        "precio_ref_nativo_cent": [99 + i for i in range(n)],
        "unidad_ref_nativa": ["l"] * n,
        "peso_variable": [False] * n,
        "capturado_en": [datetime.now(timezone.utc)] * n,
    }).write_parquet(d / "part.parquet")


@pytest.fixture
def datos(tmp_path, monkeypatch):
    (tmp_path / "gold").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(pipeline.config, "DATA", tmp_path)
    monkeypatch.setattr(pipeline.config, "BRONZE", tmp_path / "bronze")
    monkeypatch.setattr(pipeline.config, "GOLD", tmp_path / "gold")
    return tmp_path


def test_el_historico_se_rehace_entero_desde_bronze(datos):
    _bronze_de(datos, "aldi", "2026-09-16", ["1", "2"])
    _bronze_de(datos, "aldi", "2026-09-17", ["1", "2"])
    _bronze_de(datos, "dia", "2026-09-17", ["9"])
    assert pipeline.rehacer_historico() == 0

    hist = pl.read_parquet(datos / "gold" / "precio_diario.parquet")
    assert hist["fecha"].n_unique() == 2
    assert sorted(hist["fecha"].unique().to_list()) == ["2026-09-16", "2026-09-17"]
    assert len(hist) == 5


def test_rehacer_no_depende_de_lo_que_hubiera_en_gold(datos):
    # Un gold corrupto o de otra epoca no debe sobrevivir a la reconstruccion:
    # lo que manda es bronze.
    (datos / "gold").mkdir(exist_ok=True)
    pl.DataFrame({"fuente": ["inventada"], "id_fuente": ["x"],
                  "precio_cent": [1], "precio_unidad_cent": [1.0],
                  "unidad_canon": ["l"], "producto_id": ["inventada:x"],
                  "fecha": ["2020-01-01"]}).write_parquet(
        datos / "gold" / "precio_diario.parquet")
    _bronze_de(datos, "aldi", "2026-09-17", ["1"])
    assert pipeline.rehacer_historico() == 0

    hist = pl.read_parquet(datos / "gold" / "precio_diario.parquet")
    assert "inventada" not in hist["fuente"].to_list()
    assert hist["fecha"].to_list() == ["2026-09-17"]


def test_sin_bronze_no_se_toca_el_historico(datos):
    assert pipeline.rehacer_historico() == 1
    assert not (datos / "gold" / "precio_diario.parquet").exists()


# --- ofertas de tarjeta: 1.244 que se contaban como rebajas de verdad -------
#
# El descuento de tarjeta no baja lo que pagas en caja, y esa regla estaba
# escrita desde el principio. Lo que no estaba era aplicada a todos: solo DIA
# publica un campo para decirlo, asi que solo DIA tenia `promo_club` puesto.
# Medido el 18 de septiembre de 2026: 573 de Alcampo ("Club Alcampo 2ª unidad
# -50% acum en tu tarjeta") y 869 de Carrefour ("2x1 Acumula") se anunciaban
# como oferta y en el ticket no bajaban un centimo.

def _con_promos(textos, club=None):
    n = len(textos)
    df = pl.DataFrame({
        "promo_txt": textos,
        "promo_club": club if club is not None else [None] * n,
    }, schema={"promo_txt": pl.Utf8, "promo_club": pl.Boolean})
    return pipeline._marca_ofertas_de_tarjeta(df)


def test_el_texto_de_tarjeta_marca_la_oferta_como_de_club():
    out = _con_promos(["Club Alcampo 2ª unidad -50% acum en tu tarjeta",
                       "2x1 Acumula",
                       "2ª unidad -50%"])
    assert out["promo_club"].to_list() == [True, True, False]


def test_lo_que_declara_la_cadena_manda_sobre_el_texto():
    # DIA lo dice por su API aunque el texto no lo mencione.
    out = _con_promos(["2ª UD AL 50% DTO. JAMÓN CURADO"], club=[True])
    assert out["promo_club"].to_list() == [True]


def test_sin_texto_de_promocion_no_se_inventa_nada():
    out = _con_promos([None, ""])
    assert out["promo_club"].to_list() == [False, False]


def test_un_frame_sin_columna_de_promocion_no_revienta():
    df = pl.DataFrame({"fuente": ["aldi"]})
    assert pipeline._marca_ofertas_de_tarjeta(df).equals(df)


def test_una_oferta_de_solo_internet_se_marca_aparte():
    """397 promociones de Alcampo lo dicen en su propio texto, y hasta el 19 de
    septiembre de 2026 entraban en el total de la cesta como si fueran a bajar el
    ticket de la tienda."""
    out = _con_promos(["Cupón 1€ descuento. Solo Online. (10/09/2026-23/09/2026)",
                       "2ª unidad -50%"])
    assert out["promo_solo_online"].to_list() == [True, False]


def test_las_dos_marcas_son_independientes():
    # De tarjeta pero no de internet, y al reves.
    out = _con_promos(["Club Alcampo 20% dto acum en tu tarjeta",
                       "15% dto. Exclusivo online"])
    assert out["promo_club"].to_list() == [True, False]
    assert out["promo_solo_online"].to_list() == [False, True]
