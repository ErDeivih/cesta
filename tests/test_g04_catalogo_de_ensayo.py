"""G04, punto 1: **un catalogo fijo de ensayo, publicado por el mecanismo de verdad.**

**Por que asi y no con dobles.** `core/publicacion.py` publica por versiones: cada publicacion escribe
**todos** sus ficheros en `data/gold/v<sello>/`, y solo cuando estan todos mueve un **puntero**
(`actual.json`) con `os.replace`, que es atomico. Una version incompleta **no se publica**. Las
versiones anteriores **no se borran**: volver atras es apuntar a una anterior.

**Eso es exactamente lo que G04 necesita medir** -- versiones, cambio durante el uso y rollback --, y
por eso el ensayo **usa el mecanismo real** en vez de sustituirlo: *si lo sustituyera, mediria mi
doble y no el sistema.*

**Y el aislamiento no depende de la disciplina**: `GOLD` y `PUNTERO` son constantes de modulo, asi que
apuntarlas a un directorio temporal deja **todo** el mecanismo --carpetas, puntero, completitud,
rollback-- funcionando contra el catalogo de ensayo, **sin tocar el que sirve el producto**. *Hoy
importa mas que nunca: esta manana se publico la version `20261011-124542` mientras se trabajaba en
esto.*

**El contenido es mio, y por eso el ensayo dice lo que dice**: dos productos del **mismo** grupo en
**dos** cadenas, con precios distintos, los siete nutrientes, y una promocion con fecha. Nada viene del
catalogo real: *si viniera, el ensayo mediria el dia en que se ejecuta.*

    uv run pytest -q tests/test_g04_catalogo_de_ensayo.py
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from core import publicacion
from core.storage import write_parquet_file

SELLO_V1 = "20260101-000000"
SELLO_V2 = "20260102-000000"

# **El producto del ensayo.** Dos cadenas, precios distintos, y la promocion en una sola: asi el
# mismo producto es mas barato en una y se puede medir la comparacion sin depender de nada mas.
PRODUCTO = "Barrita de ensayo 100 g"
EAN = "8490000000001"
GRUPO = 900001


def _grupos_v1() -> pl.DataFrame:
    """Las dos filas del mismo producto: **una por cadena**, con el grupo compartido."""
    comun = dict(
        nombre=PRODUCTO, marca="ENSAYO", cantidad=100.0, unidad_canon="g", ean=EAN,
        cantidad_fiable=True, comparacion_fiable=True, precio_comparable=True,
        calidad="alta", es_marca_propia=False, imagen="", alergenos="", ingredientes="",
        origen="", categoria="Desayuno y dulces", url="", seccion="Desayuno y dulces",
        sellos="", sellos_origen="", certificados="", conservacion="",
        nutricion="", nutricion_por="100 g", tipo_producto="alimento", envase="",
        peso_escurrido_g=0, peso_neto_g=100, dias_caducidad=0, descripcion="",
        grado_alcohol=0.0, promo_club=False, promo_solo_online=False, es_recall=False,
        es_alcohol=False, peso_variacion_pct=0, distintivo="", advertencias="",
        proc_precio_unidad="", unidades_pack=1, promo_unidades_minimas=0,
        calidad_origen="", calidad_nota=0.0, nutriscore="", nova=0, ecoscore="",
        grupo_id=GRUPO,
        # Los siete nutrientes, **por 100 g**, que es lo que el diario convierte.
        kcal_100g=400.0, hidratos_100g=60.0, proteinas_100g=8.0, grasas_100g=12.0,
        grasas_sat_100g=4.0, azucares_100g=25.0, sal_100g=0.5,
    )
    filas = [
        # Mas barata en DIA, y con promocion: es la que tiene que ganar la comparacion.
        {"fuente": "dia", "id_fuente": "ens-dia-1", "precio_cent": 150,
         "precio_unidad_cent": 150.0, "precio_ref_canon_cent": 150.0, "unidad_ref_canon": "kg",
         "promo": True, "promo_hasta": None, "promo_txt": "2x1 de ensayo", **comun},
        # Mas cara en Alcampo, y sin promocion.
        {"fuente": "alcampo", "id_fuente": "ens-alc-1", "precio_cent": 220,
         "precio_unidad_cent": 220.0, "precio_ref_canon_cent": 220.0, "unidad_ref_canon": "kg",
         "promo": False, "promo_hasta": None, "promo_txt": "", **comun},
    ]
    return pl.DataFrame(filas)


def _enlaces() -> pl.DataFrame:
    """**El grafo que dice que las dos filas son el mismo producto.**

    `i` y `j` son **indices de fila de `grupos`**, medido el 11 de octubre de 2026 sobre el catalogo
    real: `i` llega a 50.855 con 51.609 filas, y la fila `i=0` coincide con la primera de `grupos`. Los
    pares van ordenados (`j > i`) y los niveles son `identico`, `equivalente` y `ean`.
    """
    return pl.DataFrame([{"i": 0, "j": 1, "parecido": 1.0, "nivel": "identico"}])


def _precios(fecha: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    """El precio del dia y su derivado. **El derivado es donde vive la promocion inferida.**"""
    diario = pl.DataFrame([
        {"fuente": "dia", "id_fuente": "ens-dia-1", "precio_cent": 150,
         "precio_unidad_cent": 150.0, "unidad_canon": "g", "producto_id": EAN, "fecha": fecha},
        {"fuente": "alcampo", "id_fuente": "ens-alc-1", "precio_cent": 220,
         "precio_unidad_cent": 220.0, "unidad_canon": "g", "producto_id": EAN, "fecha": fecha},
    ])
    derivado = diario.with_columns(
        pl.lit(200.0).alias("precio_anterior_cent"),
        pl.lit(-50.0).alias("variacion_cent"),
        pl.lit(True).alias("ha_bajado"),
        pl.lit(False).alias("ha_subido"),
        pl.lit(200.0).alias("precio_base_cent"),
        pl.lit(150.0).alias("min_90d_cent"),
        pl.lit(220.0).alias("max_90d_cent"),
        pl.lit(190.0).alias("media_7d_cent"),
        # **La promocion inferida**, que es la que el sistema deduce de la historia.
        pl.lit(True).alias("promo_inferida"),
        pl.lit(0.2).alias("posicion_90d"),
        pl.lit(-0.25).alias("descuento_real"),
        pl.lit(True).alias("promo_empieza"),
        pl.lit(False).alias("promo_acaba"),
        pl.lit(False).alias("oferta_sospechosa"),
    )
    return diario, derivado


def _resumen() -> pl.DataFrame:
    """**Una fila por `producto_id`**, no por cadena: agrega, y dice cuanta historia hay."""
    return pl.DataFrame([{
        "producto_id": EAN, "precio_hoy": 150.0, "posicion_90d": 0.2, "min_90d": 150.0,
        "max_90d": 220.0, "descuento_real": -0.25, "en_promo": True,
        "oferta_sospechosa": False, "dias_de_historico": 2, "tendencia_30d": -0.1,
    }])


def _promos() -> pl.DataFrame:
    """Cinco filas: **una por cadena**, y de ensayo. No son datos observados del catalogo real."""
    return pl.DataFrame([
        {"fuente": c, "duracion_mediana": 7.0, "duracion_p90": 14.0, "promos_observadas": 100}
        for c in ("alcampo", "aldi", "carrefour", "dia", "mercadona")
    ])


def publica_v1() -> dict[str, pl.DataFrame]:
    """Publica la V1 del ensayo. **Devuelve los marcos** para poder comparar con la V2."""
    datos = {
        "grupos.parquet": _grupos_v1(),
        "enlaces.parquet": _enlaces(),
        "promos_por_cadena.parquet": _promos(),
        "resumen.parquet": _resumen(),
    }
    diario, derivado = _precios("2026-01-01")
    datos["precio_diario.parquet"] = diario
    datos["precio_derivado.parquet"] = derivado
    return datos


@pytest.fixture()
def gold_de_ensayo(tmp_path, monkeypatch):
    """**El catalogo del producto no se toca.** `GOLD` y `PUNTERO` son constantes de modulo: se
    apuntan a un temporal y todo el mecanismo --carpetas, puntero atomico, completitud-- sigue
    funcionando, contra el ensayo."""
    oro = tmp_path / "gold"
    oro.mkdir()
    monkeypatch.setattr(publicacion, "GOLD", oro)
    monkeypatch.setattr(publicacion, "PUNTERO", oro / "actual.json")
    yield oro


def test_sin_publicar_no_hay_version_y_se_lee_el_catalogo_suelto(gold_de_ensayo):
    """**El estado de partida, y no es un detalle**: sin puntero, los lectores caen al catalogo suelto.
    Si el ensayo no publicara, mediria este caso en vez del de las versiones."""
    assert publicacion.version_actual() is None
    assert publicacion.versiones() == []


def test_publicar_v1_mueve_el_puntero_y_deja_los_seis(gold_de_ensayo):
    """**El punto 1 de G04**: el catalogo de ensayo existe, esta completo, y es el que se sirve."""
    version = publicacion.publicar(publica_v1(), momento=_momento(SELLO_V1))
    assert version == SELLO_V1, version
    assert publicacion.version_actual() == SELLO_V1
    assert publicacion.versiones() == [SELLO_V1]

    caminos = publicacion.rutas()
    assert len(caminos) == len(publicacion.FICHEROS), caminos
    for nombre, ruta in caminos.items():
        assert ruta.exists(), f"falta {nombre} en la version publicada"
        assert ruta.parent.name == f"v{SELLO_V1}", ruta

    # **Y lo que se lee es MIO, no los 51.609 productos del catalogo real.**
    grupos = pl.read_parquet(caminos["grupos.parquet"])
    assert grupos.height == 2, grupos.height
    assert set(grupos["nombre"].to_list()) == {PRODUCTO}, grupos["nombre"].to_list()
    assert set(grupos["fuente"].to_list()) == {"dia", "alcampo"}


def _momento(sello: str):
    """El sello, como `datetime`, para que V1 y V2 tengan nombre fijo y elegido."""
    from datetime import datetime
    return datetime.strptime(sello, "%Y%m%d-%H%M%S")

def publica_v2() -> dict[str, pl.DataFrame]:
    """La V2 del ensayo: **el mismo producto, con el precio de DIA cambiado.**

    Es lo que G04 pide en el punto 2: *cambiar el catalogo a mitad de uso*. Y el cambio es de precio
    --no de identidad-- para que lo que se mida sea **que version se sirve**, no otra cosa.
    """
    datos = publica_v1()
    grupos = datos["grupos.parquet"].with_columns(
        pl.when(pl.col("fuente") == "dia").then(pl.lit(120)).otherwise(pl.col("precio_cent"))
        .alias("precio_cent"))
    datos["grupos.parquet"] = grupos
    diario, derivado = _precios("2026-01-02")
    datos["precio_diario.parquet"] = diario.with_columns(
        pl.when(pl.col("fuente") == "dia").then(pl.lit(120)).otherwise(pl.col("precio_cent"))
        .alias("precio_cent"))
    datos["precio_derivado.parquet"] = derivado
    return datos


def _precio_de(grupos: pl.DataFrame, fuente: str) -> int:
    return int(grupos.filter(pl.col("fuente") == fuente)["precio_cent"][0])


def test_publicar_v2_mueve_el_puntero_y_no_borra_la_v1(gold_de_ensayo):
    """**El punto 2, entero, y con las dos reglas del modulo a la vista.**

    - el puntero se mueve **de una vez** (`os.replace`, atomico): antes de eso los lectores ven la
      version anterior **entera**;
    - **publicar no borra**: la V1 sigue en disco, asi que volver atras es apuntar a ella.
    """
    v1 = publicacion.publicar(publica_v1(), momento=_momento(SELLO_V1))
    assert publicacion.version_actual() == v1

    v2 = publicacion.publicar(publica_v2(), momento=_momento(SELLO_V2))
    assert v2 == SELLO_V2, v2
    assert publicacion.version_actual() == SELLO_V2, "el puntero tiene que apuntar a la nueva"
    assert publicacion.versiones() == [SELLO_V1, SELLO_V2], publicacion.versiones()

    # **Las dos siguen en disco, con sus seis ficheros cada una.**
    for sello in (SELLO_V1, SELLO_V2):
        carpeta = gold_de_ensayo / f"v{sello}"
        assert carpeta.is_dir(), f"publicar ha borrado la v{sello}"
        for nombre in publicacion.FICHEROS:
            assert (carpeta / nombre).exists(), f"falta {nombre} en la v{sello}"

    # **Y se sirve la V2**: el precio de DIA cambio de 150 a 120.
    servido = pl.read_parquet(publicacion.ruta("grupos.parquet"))
    assert _precio_de(servido, "dia") == 120, "se sigue sirviendo la V1"
    assert _precio_de(servido, "alcampo") == 220, "lo que no cambio no cambia"

    # **Y la V1 se puede seguir leyendo pidiendola por su sello**: fijar la version por peticion es
    # lo que impide que un lector vea `grupos` de una publicacion y `enlaces` de la siguiente.
    antigua = pl.read_parquet(publicacion.ruta("grupos.parquet", SELLO_V1))
    assert _precio_de(antigua, "dia") == 150, "la V1 no puede cambiar porque se publique la V2"

    # **Y `rutas()` da los seis caminos de UNA version, no una mezcla.**
    caminos = publicacion.rutas(SELLO_V1)
    assert {c.parent.name for c in caminos.values()} == {f"v{SELLO_V1}"}, caminos
    caminos_v2 = publicacion.rutas()
    assert {c.parent.name for c in caminos_v2.values()} == {f"v{SELLO_V2}"}, caminos_v2


def test_volver_a_la_v1_es_apuntar_atras_y_no_toca_los_datos(gold_de_ensayo):
    """**El rollback, que el modulo define como «apuntar a una anterior».**

    Y no se hace con una funcion propia: se hace con lo que ya hay. Aqui se comprueba que apuntar a la
    V1 la sirve entera y con los datos de la V1, sin haber tocado nada de la V2.
    """
    publicacion.publicar(publica_v1(), momento=_momento(SELLO_V1))
    publicacion.publicar(publica_v2(), momento=_momento(SELLO_V2))
    assert _precio_de(pl.read_parquet(publicacion.ruta("grupos.parquet")), "dia") == 120

    # **Volver atras con la funcion del modulo**, no escribiendo el puntero a mano: `fijar()`
    # comprueba que la version existe y que **esta completa** antes de mover nada.
    publicacion.fijar(SELLO_V1)
    assert publicacion.version_actual() == SELLO_V1
    assert _precio_de(pl.read_parquet(publicacion.ruta("grupos.parquet")), "dia") == 150
    # **Y la V2 sigue intacta**: volver atras no deshace nada, solo deja de servirla.
    assert _precio_de(pl.read_parquet(publicacion.ruta("grupos.parquet", SELLO_V2)), "dia") == 120

def test_una_publicacion_incompleta_no_se_publica_y_no_deja_restos(gold_de_ensayo):
    """**El error de publicacion del punto 4, y su regla**: «se cayo a medias» se convierte en «no
    paso nada».

    Se publica una V1 buena, y despues se intenta una V2 **a la que le falta un fichero**. Tienen que
    pasar tres cosas, y las tres importan:

    - lanza `PublicacionIncompleta`;
    - **el puntero NO se mueve**: se sigue sirviendo la V1 entera;
    - y **la carpeta a medias se retira** (`shutil.rmtree`), asi que en `versiones()` no aparece una
      version fantasma con cinco ficheros.
    """
    publicacion.publicar(publica_v1(), momento=_momento(SELLO_V1))
    incompleta = publica_v2()
    del incompleta["precio_derivado.parquet"]          # falta uno de los seis

    with pytest.raises(publicacion.PublicacionIncompleta) as fallo:
        publicacion.publicar(incompleta, momento=_momento(SELLO_V2))
    assert "precio_derivado" in str(fallo.value), fallo.value

    # **El puntero sigue en la V1, y se sirve la V1 entera.**
    assert publicacion.version_actual() == SELLO_V1
    assert publicacion.versiones() == [SELLO_V1], publicacion.versiones()
    assert not (gold_de_ensayo / f"v{SELLO_V2}").exists(), "la carpeta a medias tenia que retirarse"
    assert _precio_de(pl.read_parquet(publicacion.ruta("grupos.parquet")), "dia") == 150
    # **Y los seis ficheros de la V1 siguen ahi**, que es lo que hace que «no paso nada» sea cierto.
    for nombre in publicacion.FICHEROS:
        assert (gold_de_ensayo / f"v{SELLO_V1}" / nombre).exists(), nombre


def test_fijar_rechaza_una_version_incompleta(gold_de_ensayo):
    """**Y el rollback tampoco acepta una version a medias**: volver a una que le falta un fichero
    seria servir una mezcla con otro nombre."""
    publicacion.publicar(publica_v1(), momento=_momento(SELLO_V1))
    publicacion.publicar(publica_v2(), momento=_momento(SELLO_V2))
    # Se le quita un fichero a la V1 ya publicada, a mano: el caso de un disco a medias.
    (gold_de_ensayo / f"v{SELLO_V1}" / "resumen.parquet").unlink()

    with pytest.raises(publicacion.PublicacionIncompleta):
        publicacion.fijar(SELLO_V1)
    # **Y el puntero no se ha movido**: sigue sirviendo la V2, que esta entera.
    assert publicacion.version_actual() == SELLO_V2
    # Una version que no existe tampoco se fija.
    with pytest.raises(ValueError):
        publicacion.fijar("20990101-000000")


def test_una_v2_sin_el_producto_en_una_cadena_lo_deja_con_una(con_almacen=None):
    """**Desaparicion de candidato**: el mismo producto, una cadena menos.

    Publicar una V2 que quite el producto de Alcampo tiene que dejar **una sola fila** en `grupos`, y
    **la que queda es la de DIA**. Y la V1 -- que tenia las dos -- **sigue leyendose entera por su
    sello**: *lo que ya se miraba con la V1 no cambia porque se publique la V2.*
    """
    import tempfile

    with tempfile.TemporaryDirectory() as temporal:
        oro = Path(temporal)
        guardado = (publicacion.GOLD, publicacion.PUNTERO)
        publicacion.GOLD, publicacion.PUNTERO = oro, oro / "actual.json"
        try:
            publicacion.publicar(publica_v1(), momento=_momento(SELLO_V1))
            sin_alcampo = publica_v2()
            sin_alcampo["grupos.parquet"] = sin_alcampo["grupos.parquet"].filter(
                pl.col("fuente") != "alcampo")
            publicacion.publicar(sin_alcampo, momento=_momento(SELLO_V2))

            servido = pl.read_parquet(publicacion.ruta("grupos.parquet"))
            assert servido.height == 1, f"el candidato tenia que desaparecer: {servido.height} filas"
            assert servido["fuente"].to_list() == ["dia"], servido["fuente"].to_list()

            # **Y la V1 sigue con los dos**: no se reescribe lo que ya estaba publicado.
            v1 = pl.read_parquet(publicacion.ruta("grupos.parquet", SELLO_V1))
            assert v1.height == 2, v1.height
            assert set(v1["fuente"].to_list()) == {"dia", "alcampo"}
        finally:
            publicacion.GOLD, publicacion.PUNTERO = guardado

# --- y ahora, que la APLICACION lo lea -------------------------------------

@pytest.fixture()
def app_leyendo_el_ensayo(tmp_path, monkeypatch):
    """**La aplicacion lee el catalogo de ensayo, y esto es lo que lo consigue.**

    La API no lee por versiones: lee **DuckDB sobre los parquet de `AJUSTES.gold`** (`catalogo.py:1`)
    y deriva `buscable` de ellos en cada conexion. Asi que la palanca es `AJUSTES.gold`, **no**
    `publicacion.GOLD` -- son dos constantes en dos modulos, y la aplicacion usa la segunda.

    **`Ajustes` esta congelado** (`FrozenInstanceError` al asignar), asi que se entra por
    `object.__setattr__`, que es lo que hace falta para apuntar el ensayo sin tocar el catalogo del
    producto. Y se restaura al terminar.
    """
    from plataforma.api import catalogo
    from plataforma.api.ajustes import AJUSTES

    oro = tmp_path / "gold"
    oro.mkdir()
    original = AJUSTES.gold
    object.__setattr__(AJUSTES, "gold", oro)
    monkeypatch.setattr(publicacion, "GOLD", oro)
    monkeypatch.setattr(publicacion, "PUNTERO", oro / "actual.json")
    try:
        yield oro
    finally:
        object.__setattr__(AJUSTES, "gold", original)
        catalogo.reiniciar()


def _suelta(oro: Path, datos: dict[str, pl.DataFrame]) -> None:
    """**Deja los seis parquet sueltos donde la API los mira.** `publicar` los escribe en la carpeta
    de la version; la aplicacion lee los sueltos, asi que el ensayo se deja en las dos formas."""
    for nombre, marco in datos.items():
        marco.write_parquet(oro / nombre)


def test_la_aplicacion_busca_en_el_catalogo_de_ensayo_y_no_en_el_real(app_leyendo_el_ensayo):
    """**La puerta del recorrido.** Si esto no pasara, todo lo demas mediria el catalogo real."""
    from plataforma.api import catalogo

    oro = app_leyendo_el_ensayo
    _suelta(oro, publica_v1())
    catalogo.reiniciar()

    hallados = catalogo.buscar("Barrita de ensayo")
    assert hallados, "la busqueda no encuentra el producto del ensayo"
    # **`buscar` devuelve PRODUCTOS, no filas de cadena**: el mismo producto esta en DIA y en
    # Alcampo, y la busqueda devuelve **el producto**. Los precios por cadena salen de la ficha.
    # *Darlo por hecho al reves fue mi fallo de la ronda anterior, no del codigo.*
    assert len(hallados) == 1, f"un producto, y salieron {len(hallados)}: {hallados[:3]}"
    assert hallados[0].get("nombre") == PRODUCTO, hallados[0]
    assert hallados[0].get("precio_cent") in (150, 220), hallados[0].get("precio_cent")


def test_publicar_v2_cambia_lo_que_la_aplicacion_sirve(app_leyendo_el_ensayo):
    """**El punto 2, con la aplicacion delante**: el catalogo cambia y lo servido cambia con el.

    Y hace falta `catalogo.reiniciar()`: la conexion se cachea por el `mtime` de `grupos.parquet`, y
    **una prueba que no lo tenga en cuenta mediria la cache, no la publicacion.**
    """
    from plataforma.api import catalogo

    oro = app_leyendo_el_ensayo
    _suelta(oro, publica_v1())
    catalogo.reiniciar()
    encuentra = catalogo.buscar("Barrita de ensayo")
    assert len(encuentra) == 1, encuentra
    antes = encuentra[0].get("precio_cent")
    assert antes in (150, 220), antes

    # **V2**: el precio de DIA cambia de 150 a 120. Se deja publicado Y suelto, que es lo que la API ve.
    publicacion.publicar(publica_v1(), momento=_momento(SELLO_V1))
    datos_v2 = publica_v2()
    publicacion.publicar(datos_v2, momento=_momento(SELLO_V2))
    _suelta(oro, datos_v2)
    catalogo.reiniciar()

    despues = catalogo.buscar("Barrita de ensayo")
    assert len(despues) == 1, despues
    assert despues[0].get("precio_cent") == 120, (
        f"la aplicacion sigue sirviendo lo viejo: {despues[0].get('precio_cent')}")
    # **Y las dos versiones siguen publicadas**: publicar no borra.
    assert publicacion.versiones() == [SELLO_V1, SELLO_V2], publicacion.versiones()

    # **Los precios POR CADENA**, que es donde estan los dos: la busqueda da el producto, y la
    # ficha da lo que cuesta en cada cadena. Aqui se ve que V2 cambio **uno** y no el otro.
    ficha = catalogo.grupo(GRUPO)
    por_cadena = {}
    for fila in (ficha if isinstance(ficha, list) else ficha.get("productos", [ficha])):
        if isinstance(fila, dict) and fila.get("fuente"):
            por_cadena[fila["fuente"]] = fila.get("precio_cent")
    assert por_cadena.get("dia") == 120, f"la ficha no trae el precio nuevo de DIA: {por_cadena}"
    assert por_cadena.get("alcampo") == 220, f"y el que no cambio, no cambia: {por_cadena}"

# --- y lo ya hecho, que es la ultima clausula del punto 4 ------------------

@pytest.fixture()
def con_almacen_y_ensayo(app_leyendo_el_ensayo):
    """**El catalogo de ensayo Y el almacen de verdad**, cada uno en su sitio.

    El catalogo, apuntado a un temporal; el almacen, el PostgreSQL desechable. *El diario real y las
    compras reales no se tocan: el ensayo vive en su carpeta y las listas de esta prueba en la base de
    ensayo.* Se salta con motivo explicito si no hay motor.
    """
    import os

    from plataforma.api import almacen

    if not os.environ.get("CESTA_POSTGRES"):
        pytest.skip("sin CESTA_POSTGRES al importar: esta prueba necesita el almacen real")
    try:
        almacen.arranca(espera=10)
    except Exception as fallo:  # noqa: BLE001
        pytest.skip(f"sin almacen: {type(fallo).__name__}: {fallo}")
    yield app_leyendo_el_ensayo
    almacen.arranca(espera=10)


def _entra(cliente):
    for usuario in ("prueba-navegador", "recibo-de-prueba"):
        if cliente.post("/api/entrar", json={"usuario": usuario,
                                             "clave": "clave-de-prueba-123"}).status_code == 200:
            return usuario
    pytest.skip("no hay cuenta de prueba en el almacen")


def test_lo_cerrado_conserva_su_precio_aunque_el_catalogo_cambie(con_almacen_y_ensayo):
    """**«Mantener compras/consumos ya hechos»**, la ultima clausula del punto 4.

    Se cierra una compra con el producto del ensayo a 150, y despues **se publica V2 con el precio a
    120**. Lo que tiene que pasar es lo que hace que una compra sirva de algo:

    - **la compra cerrada conserva 150**, porque se guarda **con sus precios** -- *gold se reescribe
      cada dia, y recalcularla con los precios de hoy seria explicar una compra de ayer con los datos
      de hoy*;
    - **y la lista sigue viva**, con su linea, para poder seguir comprando.
    """
    from fastapi.testclient import TestClient

    from plataforma.api import almacen, catalogo, main

    oro = con_almacen_y_ensayo
    datos_v1 = publica_v1()
    publicacion.publicar(datos_v1, momento=_momento(SELLO_V1))
    _suelta(oro, datos_v1)
    catalogo.reiniciar()

    with TestClient(main.app) as cliente:
        _entra(cliente)
        lista = cliente.post("/api/listas", json={"nombre": "Prueba G04 lo ya hecho",
                                                  "es_de_casa": False})
        assert lista.status_code in (200, 201), lista.text
        lista_id = lista.json()["id"]

        linea = cliente.post(f"/api/listas/{lista_id}/lineas",
                             json={"nombre": PRODUCTO, "grupo_id": GRUPO, "cantidad": 1})
        assert linea.status_code == 201, f"la linea del ensayo no entra: {linea.text}"
        linea_id = linea.json()["id"]

        carro = cliente.patch(f"/api/listas/{lista_id}/lineas/{linea_id}", json={"en_carrito": True})
        assert carro.status_code < 300, carro.text
        cierre = cliente.post(f"/api/listas/{lista_id}/cerrar", json={})
        assert cierre.status_code < 300, f"el cierre falla: {cierre.status_code} {cierre.text}"

        compras = almacen.compras_de(lista_id, limite=1)
        assert compras, "el cierre no dejo compra"
        archivadas = almacen.lineas_de_compra(str(compras[0]["compra_id"]))
        assert len(archivadas) == 1, archivadas
        # **El precio de la V1**: el mas barato de las dos cadenas, que es DIA a 150.
        assert archivadas[0].get("precio_cent") in (150, 220), archivadas[0]
        guardado = archivadas[0].get("precio_cent")

        # **Y ahora se publica V2**, con DIA a 120.
        datos_v2 = publica_v2()
        publicacion.publicar(datos_v2, momento=_momento(SELLO_V2))
        _suelta(oro, datos_v2)
        catalogo.reiniciar()

        # **La compra cerrada NO se ha movido.**
        otra_vez = almacen.lineas_de_compra(str(compras[0]["compra_id"]))
        assert otra_vez[0].get("precio_cent") == guardado, (
            f"la compra cerrada ha cambiado de precio al publicar V2: {guardado} -> "
            f"{otra_vez[0].get('precio_cent')}")
        assert otra_vez[0].get("importe_cent") is not None, otra_vez[0]

        # **Y la lista sigue viva**, con la linea que quedo.
        detalle = cliente.get(f"/api/listas/{lista_id}")
        assert detalle.status_code == 200, detalle.text


def test_el_puntero_sella_el_mismo_momento_que_nombra_la_carpeta(gold_de_ensayo):
    """**Las dos mitades del sello dicen lo mismo**, que es lo que `/api/estado` compara.

    `_vigencia(catalogo.fecha_de_gold(), puntero["publicado_en"])` pone la fecha de la carpeta contra
    la del puntero. Si `publicar(momento=X)` nombrara la carpeta con `X` y sellara el puntero con la
    hora real, **una publicacion retrofechada se veria incoherente sin serlo**.
    """
    # Una fecha elegida y **muy anterior a hoy**: si el puntero sellara la hora real, se veria.
    momento = datetime(2026, 1, 1, 0, 0, 0)
    version = publicacion.publicar(publica_v1(), momento=momento)
    datos = json.loads((gold_de_ensayo / "actual.json").read_text(encoding="utf-8"))
    assert version == "20260101-000000"
    assert datos["version"] == version
    assert datos["publicado_en"].startswith("2026-01-01T00:00:00"), (
        "el puntero sella el momento que nombra la carpeta, no la hora real")


def test_publicar_de_verdad_cambia_lo_que_la_aplicacion_sirve(app_leyendo_el_ensayo):
    """**F03 (fase 2): la prueba que faltaba**, y la que el nombre de la de arriba prometia.

    *La de arriba -- `test_publicar_v2_cambia_lo_que_la_aplicacion_sirve` -- usa `_suelta`, que escribe
    el gold suelto, **no `publicar()`**: mide otra cosa.* Aqui se publica de verdad: puntero, carpeta de
    version y enlace duro. **Y es lo que hasta la ronda 17 se cumplia por trivialidad**: `catalogo` leia
    el gold suelto, asi que publicar **no cambiaba nada** de lo que se servia.

    **La prueba esta montada para discriminar, y eso es lo que hay que mirar.** Si se escribe V2 en el
    gold suelto **y se publica**, *una aplicacion que leyera el suelto tambien daria otro precio* y la
    prueba pasaria sin medir nada. **Por eso V2 se deja SOLO en el suelto, sin publicar**: si la
    aplicacion lee la version -- que es lo que ahora hace --, sigue sirviendo **V1**.
    """
    from datetime import datetime

    from plataforma.api import catalogo

    # **Se escribe con `write_parquet_file`, el escritor del proyecto, y no con `_suelta`.**
    # *`_suelta` usa `marco.write_parquet`, que escribe **en el sitio**; y `publicar()` deja un
    # **enlace duro** entre el gold suelto y la version, asi que escribir V2 ahi **mutaria tambien la
    # version publicada**. Es la invariante que fija
    # `test_fase2_f03_publicacion.py::test_una_version_publicada_no_se_muta_si_el_escritor_renombra`,
    # y aqui mordia de verdad: la primera version de esta prueba media el escritor, no la publicacion.*
    def suelta_atomico(datos):
        for nombre, marco in datos.items():
            write_parquet_file(marco, oro / nombre)

    oro = app_leyendo_el_ensayo
    suelta_atomico(publica_v1())
    v1 = publicacion.publicar(None, momento=datetime(2026, 10, 7, 10, 0, 0))
    catalogo.reiniciar()
    con_v1 = catalogo.buscar("Barrita de ensayo")[0].get("precio_cent")

    # **V2, SOLO en el gold suelto. El puntero sigue en V1.**
    suelta_atomico(publica_v2())
    catalogo.reiniciar()
    sigue = catalogo.buscar("Barrita de ensayo")[0].get("precio_cent")
    assert sigue == con_v1, (
        f"con el puntero en V1 hay que servir V1 ({con_v1}), y salio {sigue}: se esta leyendo el gold "
        f"suelto, asi que publicar no sirve para nada")

    # **Y ahora si se publica V2.** El puntero se mueve, y lo servido con el.
    v2 = publicacion.publicar(None, momento=datetime(2026, 10, 7, 10, 30, 0))
    catalogo.reiniciar()
    con_v2 = catalogo.buscar("Barrita de ensayo")[0].get("precio_cent")

    assert v2 != v1
    assert con_v2 != con_v1, (
        "publicar V2 tiene que cambiar lo que la aplicacion sirve; si no, la publicacion no llega a "
        "quien compra")


def test_una_conexion_ve_una_sola_version(app_leyendo_el_ensayo):
    """**La otra mitad de la frase de S01**: *«una peticion de dos ficheros ve una sola version»*.

    **El mecanismo**: `conexion()` resuelve el puntero **una vez** y monta las cinco vistas desde esa
    version. *Una conexion ya montada sigue leyendo **su** version aunque se publique otra cosa, y una
    nueva lee la nueva -- que es lo que hace que publicar sirva para algo.*

    **Y el limite, dicho aqui porque es donde se lee**: la unidad no es la peticion, es **la conexion**.
    *La API llama a `catalogo.conexion()` en **ocho sitios, cada uno en una funcion distinta**, asi que
    un manejador que la pida una vez esta cubierto.* **Si algun dia un manejador llama a dos de esas
    funciones -- y por tanto pide conexion dos veces -- y se publica entre las dos, vera dos versiones.**
    *Entonces habra que **pasar la conexion**, no volver a pedirla.*
    """
    from datetime import datetime

    from plataforma.api import catalogo

    def suelta_atomico(datos):
        for nombre, marco in datos.items():
            write_parquet_file(marco, oro / nombre)

    oro = app_leyendo_el_ensayo
    suelta_atomico(publica_v1())
    publicacion.publicar(None, momento=datetime(2026, 10, 7, 10, 0, 0))
    catalogo.reiniciar()
    con = catalogo.conexion()
    en_la_v1 = con.execute("SELECT precio_cent FROM grupos").fetchall()

    # **Se publica V2 a mitad de camino.**
    suelta_atomico(publica_v2())
    publicacion.publicar(None, momento=datetime(2026, 10, 7, 10, 30, 0))

    # **La conexion que ya estaba montada sigue en V1**: sus vistas apuntan a los ficheros de V1.
    assert con.execute("SELECT precio_cent FROM grupos").fetchall() == en_la_v1, (
        "una conexion ya montada no puede cambiar de version a mitad de camino")

    # **Y una nueva lee la nueva**, que es lo que hace que publicar sirva para algo.
    catalogo.reiniciar()
    otra = catalogo.conexion()
    assert otra.execute("SELECT precio_cent FROM grupos").fetchall() != en_la_v1, (
        "una conexion nueva tiene que leer la version nueva")


def test_un_recorrido_de_varias_tablas_no_mezcla_versiones(app_leyendo_el_ensayo):
    """**F03: «V1 fija y V2 publicada durante el uso; respuesta individual no mezcla versiones».**

    *Las cuatro cosas que pide la aceptación -- búsqueda, previa de lista, sustitución y alta -- leen **la
    misma conexión**, y una conexión puede leer varias tablas: `grupos`, `enlaces` y `precio_diario`.* **La
    prueba reproduce eso**: se abre la conexión con V1, se lee, **se publica V2 a mitad**, y se vuelve a
    leer.

    *Lo que tiene que pasar es que la segunda lectura siga siendo **V1**: la conexión se montó con las rutas
    de V1, y sus vistas siguen apuntando ahí.* **Si se rehiciera a mitad, un recorrido podría enseñar el
    nombre de una versión y el precio de la siguiente** -- que es exactamente lo que S01 prohíbe.

    *Y se publica en el sandbox parcheando `publicacion.GOLD` **en el proceso**: con `CESTA_GOLD` no basta,
    porque esa variable la lee el API y no los scripts de publicación. Aprenderlo costó un incidente real
    sobre el gold de producción, y está escrito en `docs/investigaciones/F03-publicacion.md` §16.*
    """
    from datetime import datetime

    from plataforma.api import catalogo

    def suelta_atomico(datos):
        for nombre, marco in datos.items():
            write_parquet_file(marco, oro / nombre)

    oro = app_leyendo_el_ensayo
    suelta_atomico(publica_v1())
    publicacion.publicar(None, momento=datetime(2026, 10, 7, 10, 0, 0))
    catalogo.reiniciar()

    con = catalogo.conexion()
    # **Las tres tablas que un recorrido real toca**, leídas con la misma conexión.
    antes = {
        "grupos": con.execute("SELECT count(*) FROM grupos").fetchone()[0],
        "enlaces": con.execute("SELECT count(*) FROM enlaces").fetchone()[0],
        "diario": con.execute("SELECT count(*) FROM diario").fetchone()[0],
        "precio": con.execute("SELECT min(precio_cent) FROM grupos").fetchone()[0],
    }

    # **Se publica V2 a mitad del recorrido.**
    suelta_atomico(publica_v2())
    publicacion.publicar(None, momento=datetime(2026, 10, 7, 10, 30, 0))

    # **Y la conexión abierta sigue viendo lo mismo, tabla por tabla.**
    despues = {
        "grupos": con.execute("SELECT count(*) FROM grupos").fetchone()[0],
        "enlaces": con.execute("SELECT count(*) FROM enlaces").fetchone()[0],
        "diario": con.execute("SELECT count(*) FROM diario").fetchone()[0],
        "precio": con.execute("SELECT min(precio_cent) FROM grupos").fetchone()[0],
    }

    assert despues == antes, (
        f"una conexion abierta no puede cambiar de version a mitad de un recorrido: {antes} -> {despues}")

    # **Y una conexión nueva sí lee V2** -- que es lo que hace que publicar sirva para algo.
    catalogo.reiniciar()
    con2 = catalogo.conexion()
    nueva = con2.execute("SELECT min(precio_cent) FROM grupos").fetchone()[0]
    assert nueva != antes["precio"], (
        "una conexion nueva tiene que leer la version nueva: si no, publicar no cambia lo que se sirve")
