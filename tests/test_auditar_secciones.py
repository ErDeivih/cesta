"""El mapa de secciones no puede volver a mandar los pañales a la panadería."""
from core.secciones import _mapa
from projects.cesta import auditar_secciones as aud


def test_ninguna_clave_contradice_su_propia_rama():
    """Un producto de `mascotas/` no puede acabar en `aperitivos`.

    Asi estaba el 20 de septiembre de 2026: los snacks del perro en el pasillo
    de los aperitivos, los pañales en panadería (porque "panales" contiene
    "pan"), y los aperitivos de Alcampo en despensa, lo que dejaba a la cadena
    con **cero productos** en la sección aperitivos teniendo 658.
    """
    malas = aud.contradice_su_rama(_mapa())
    assert malas == [], "\n".join(
        f"{f} {c!r}: dice {d}, su rama pide {p}" for f, c, d, p in malas)


def test_el_convenio_del_congelado_se_aplica_igual_en_todas_las_cadenas():
    """El pescado congelado va con el pescado, y eso vale para las cinco.

    Si una cadena lo manda a `congelados` y otra a `pescaderia`, los dos
    precios dejan de encontrarse y la comparación pierde justo los productos
    que más se parecen entre sí.
    """
    rotas = [c for c in aud.convenio_del_congelado(_mapa()) if c[2] != c[3]]
    assert rotas == [], "\n".join(
        f"{f} {c!r}: dice {d}, el espejo pide {e}" for f, c, d, e in rotas)


def test_los_panales_no_estan_en_panaderia():
    """La prueba tonta que habria pillado el fallo de raíz."""
    mapa = _mapa()
    for (fuente, clave), seccion in mapa.items():
        if "anales" in clave or "ampañas" in clave or "ampanas" in clave:
            assert seccion != "panaderia", f"{fuente} {clave!r} -> panaderia"


def test_una_seccion_vacia_en_una_cadena_se_detecta():
    import collections
    conteo = {
        "a": collections.Counter({"aperitivos": 10}),
        "b": collections.Counter({"aperitivos": 5}),
        "c": collections.Counter({"aperitivos": 7}),
        "d": collections.Counter({"despensa": 3}),
    }
    assert ("d", "aperitivos") in aud.secciones_vacias(conteo)


def test_una_seccion_que_casi_nadie_usa_no_acusa_a_nadie():
    import collections
    conteo = {
        "a": collections.Counter({"hogar": 10}),
        "b": collections.Counter({"despensa": 5}),
        "c": collections.Counter({"despensa": 7}),
    }
    assert aud.secciones_vacias(conteo) == []


def test_ninguna_hoja_se_sale_de_lo_que_hace_su_rama():
    """Once hojas de `cervezas-vinos-y-licores/` iban a bebidas y tres no.

    La regla que menos opina y mas fallos encuentra: no hace falta saber qué es
    un vermouth para ver que se ha quedado solo. Encontró 20 claves de golpe,
    entre ellas siete de la rama de higiene de Carrefour que vivían en
    `desayuno-dulces` -- desodorantes, aftershave, limpiadores de prótesis.
    """
    fuera = aud.disidentes_de_su_rama(_mapa())
    assert fuera == [], "\n".join(
        f"{f} {c!r}: dice {d}, su rama hace {m}" for f, c, d, m in fuera)


# --- las ramas nuevas de cada semana ---------------------------------------

def test_una_hoja_nueva_hereda_la_disidencia_declarada_de_su_padre():
    """El 23 y el 25 de septiembre estas dos pruebas fallaron por lo mismo, dos veces.

    Carrefour abrió `drogueria-y-limpieza/papeleria/colorear` y `.../cartuchos-de-tinta`, el
    pipeline les dio la sección de su padre (`hogar`, declarado a mano desde el 20 porque un
    bolígrafo no es un producto de limpieza) y las dos salieron acusadas de contradecir su
    rama. La decisión ya estaba tomada; lo que faltaba era que cubriera a las hojas que
    cuelgan de ella.
    """
    mapa = {
        ("carrefour", "drogueria-y-limpieza/papeleria"): "hogar",
        ("carrefour", "drogueria-y-limpieza/papeleria/cartuchos-de-tinta"): "hogar",
        ("carrefour", "drogueria-y-limpieza/papeleria/colorear"): "hogar",
    }
    assert aud.contradice_su_rama(mapa) == []
    # Y en el mapa de verdad, que es donde fallaba:
    for clave in ("colorear", "cartuchos-de-tinta"):
        assert aud.disidencia_declarada(
            "carrefour", f"drogueria-y-limpieza/papeleria/{clave}", "hogar", _mapa())


def test_la_herencia_no_tapa_una_hoja_que_se_va_a_otro_sitio():
    """Cubre a las hojas que hacen lo mismo que el padre, y a nadie más.

    Una hoja nueva dentro de una rama declarada que se fuera a otro pasillo no es una
    excepción conocida: es una hoja que se ha ido, y tiene que saltar.
    """
    mapa = {
        ("carrefour", "drogueria-y-limpieza/papeleria"): "hogar",
        ("carrefour", "drogueria-y-limpieza/papeleria/grapadoras"): "desayuno-dulces",
    }
    assert aud.disidencia_declarada("carrefour",
                                    "drogueria-y-limpieza/papeleria/grapadoras",
                                    "desayuno-dulces", mapa) is False
    assert aud.contradice_su_rama(mapa) == [
        ("carrefour", "drogueria-y-limpieza/papeleria/grapadoras",
         "desayuno-dulces", "droguería-limpieza")]


def test_una_hoja_nueva_hereda_la_seccion_de_su_padre(tmp_path, monkeypatch):
    """El 21 de septiembre Carrefour trajo 24 productos en 16 categorías nuevas.

    Sandías y melones, fiambre de pavo, bollería tradicional: ramas que el día
    anterior no existían, y que sin mapear se quedan sin pasillo — al final de
    la lista y fuera de la pantalla de secciones. Pasa cada semana y no lo
    detectaba nadie.
    """
    import polars as pl
    monkeypatch.setattr(aud.config, "DATA", tmp_path)
    carpeta = tmp_path / "bronze" / "fuente=carrefour" / "fecha=2026-09-21"
    carpeta.mkdir(parents=True)
    pl.DataFrame({"categoria": ["frescos/charcuteria/morcilla-de-prueba"] * 3,
                  }).write_parquet(carpeta / "part.parquet")

    nuevas = aud.sin_mapear()
    assert nuevas, "la categoría nueva tiene que salir"
    _fuente, clave, n, propuesta = nuevas[0]
    assert (clave, n) == ("frescos/charcuteria/morcilla-de-prueba", 3)
    # `frescos/charcuteria` va a carnicería, así que su hoja también.
    assert propuesta == "carniceria"


def test_una_hoja_sin_padre_claro_no_se_propone_a_ojo(tmp_path, monkeypatch):
    """Una sección puesta a ojo es lo que mandó los pañales a la panadería."""
    import polars as pl
    monkeypatch.setattr(aud.config, "DATA", tmp_path)
    carpeta = tmp_path / "bronze" / "fuente=carrefour" / "fecha=2026-09-21"
    carpeta.mkdir(parents=True)
    pl.DataFrame({"categoria": ["rama-que-no-existe-de-nada"]}).write_parquet(
        carpeta / "part.parquet")
    assert aud.sin_mapear()[0][3] is None
