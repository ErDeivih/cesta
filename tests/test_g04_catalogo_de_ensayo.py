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

import polars as pl
import pytest

from core import publicacion

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
