"""Los minimos por producto: el artefacto de la cadena y la marca de la API.

David lo pidio asi (10/11, madrugada): *guardar el precio minimo visto y su fecha
por producto, y marcar cuando el precio vuelve a ese minimo*. Sin notificaciones
emergentes: una marca en la lista y un fichero de resumen.

Lo que estas pruebas vigilan, por orden de importancia:

  1. **Que la fecha sea la del minimo de verdad**, y que un empate se quede con la
     mas antigua. Una fecha que no es la primera vez que se alcanzo ese precio
     convierte el resumen en una anecdota que no se puede comprobar.
  2. **Que no se marque de mas**: sin precio hoy no hay marca, con un solo dia no
     hay historico, y fuera de la fecha de gold no se marca nada. Mejor no marcar
     que mentir -- es la regla de `alertas.minimo_90d`, y aqui vale igual.
  3. **Que la API no se caiga** cuando el artefacto no existe: la web que lo
     consume no puede depender de que la cadena haya pasado ya.

El gold de mentira se escribe con Polars en `tmp_path`, como manda el encargo.
"""
import ast
import importlib
from dataclasses import replace
from pathlib import Path

import polars as pl
import pytest

from plataforma import api as _api
from projects.cesta import minimos as proyecto

# **Este fichero no toca PostgreSQL.** La marca de `conftest.py` salta entero
# cualquier fichero que mencione el paquete de la API si no hay base, porque no
# puede saber si la usa. Aqui no se usa: la consulta es DuckDB sobre parquet y los
# modulos que se prueban no abren conexion ninguna. Por eso los dos modulos se
# resuelven por nombre -- para que las pruebas corran tambien sin base, que es el
# suelo medido que el propio `conftest.py` documenta.
catalogo = importlib.import_module(f"{_api.__name__}.catalogo")
api_minimos = importlib.import_module(f"{_api.__name__}.minimos")

# Las columnas del gold de verdad, con su tipo. Se declaran a mano para que una
# prueba no escriba un parquet con un tipo que la cadena nunca produce.
DIARIO = {
    "fuente": pl.Utf8,
    "id_fuente": pl.Utf8,
    "precio_cent": pl.Int64,
    "precio_unidad_cent": pl.Float64,
    "unidad_canon": pl.Utf8,
    "region": pl.Utf8,
    "fecha": pl.Utf8,
    "producto_id": pl.Utf8,
}

# Lo que la API necesita de `grupos.parquet` para montar `buscable`. Son las
# columnas obligatorias de `catalogo.conexion`, ni una mas: las opcionales las
# pone a NULL `_o_nulo`.
GRUPOS = {
    "grupo_id": pl.Int64,
    "fuente": pl.Utf8,
    "id_fuente": pl.Utf8,
    "nombre": pl.Utf8,
    "marca": pl.Utf8,
    "cantidad": pl.Float64,
    "unidad_canon": pl.Utf8,
    "precio_cent": pl.Int64,
    "precio_unidad_cent": pl.Float64,
    "comparacion_fiable": pl.Boolean,
    "calidad": pl.Utf8,
    "calidad_origen": pl.Utf8,
    "nutriscore": pl.Utf8,
    "nova": pl.Int64,
    "ean": pl.Utf8,
    "imagen": pl.Utf8,
    "promo_txt": pl.Utf8,
    "promo_club": pl.Boolean,
    "promo_solo_online": pl.Boolean,
}

DERIVADO = {
    "fuente": pl.Utf8,
    "id_fuente": pl.Utf8,
    "fecha": pl.Utf8,
    "min_90d_cent": pl.Float64,
    "precio_base_cent": pl.Float64,
}


def _precio(fuente: str, ident: str, fecha: str, venta,
            unidad: str = "ud", ud=None) -> dict:
    """Una fila del historico. `venta=None` es un dia sin importe."""
    return {
        "fuente": fuente, "id_fuente": str(ident), "precio_cent": venta,
        "precio_unidad_cent": float(ud if ud is not None else (venta or 0)),
        "unidad_canon": unidad, "region": None, "fecha": fecha,
        "producto_id": f"{fuente}:{ident}",
    }


def _producto(fuente: str, ident: str, grupo_id: int, nombre: str,
              marca: str | None, venta: int, ud: float | None = None,
              club: bool = False, online: bool = False) -> dict:
    """Un miembro del catalogo, como lo deja el emparejador en `grupos.parquet`."""
    return {
        "grupo_id": grupo_id, "fuente": fuente, "id_fuente": str(ident),
        "nombre": nombre, "marca": marca, "cantidad": 1.0,
        "unidad_canon": "l", "precio_cent": venta,
        "precio_unidad_cent": float(ud if ud is not None else venta),
        "comparacion_fiable": True, "calidad": None, "calidad_origen": None,
        "nutriscore": None, "nova": None, "ean": None, "imagen": None,
        "promo_txt": None, "promo_club": club, "promo_solo_online": online,
    }


@pytest.fixture
def oro(tmp_path):
    """Escribe un gold sintetico y devuelve su carpeta.

    `oro(diario, productos)` deja `precio_diario.parquet` y `grupos.parquet` en
    `<tmp>/gold`, mas los tres parquet vacios que `catalogo.conexion` monta como
    vistas. Todo bajo `tmp_path`: nunca se escribe en `data/gold` de verdad.
    """
    def escribe(diario=(), productos=()):
        carpeta = tmp_path / "gold"
        carpeta.mkdir(parents=True, exist_ok=True)
        pl.DataFrame(list(diario), schema=DIARIO, orient="row").write_parquet(
            carpeta / "precio_diario.parquet")
        pl.DataFrame(list(productos), schema=GRUPOS, orient="row").write_parquet(
            carpeta / "grupos.parquet")
        pl.DataFrame([], schema=DERIVADO).write_parquet(
            carpeta / "precio_derivado.parquet")
        for otro in ("enlaces", "resumen"):
            pl.DataFrame({"x": []}).write_parquet(carpeta / f"{otro}.parquet")
        catalogo.reiniciar()
        return carpeta

    yield escribe
    catalogo.reiniciar()


def _fila(tabla: pl.DataFrame, producto_id: str) -> dict:
    """La fila del artefacto de un producto, o un fallo claro si no esta."""
    mia = tabla.filter(pl.col("producto_id") == producto_id)
    assert mia.height == 1, f"{producto_id} sale {mia.height} veces en el artefacto"
    return mia.row(0, named=True)


# ------------------------------------------------------ el minimo y su fecha ---

def test_el_minimo_y_la_primera_vez_que_se_alcanzo(oro):
    """Un producto que bajo a 1,50, subio a 1,80 y hoy sigue en 1,80."""
    carpeta = oro([
        _precio("dia", "1", "2026-01-01", 200),
        _precio("dia", "1", "2026-01-02", 150),
        _precio("dia", "1", "2026-01-03", 180),
    ])
    fila = _fila(proyecto.calcula(gold=carpeta), "dia:1")

    assert fila["fecha_datos"] == "2026-01-03"
    assert fila["precio_hoy_cent"] == 180
    assert fila["minimo_cent"] == 150
    assert fila["minimo_fecha"] == "2026-01-02"
    assert fila["minimo_previo_cent"] == 150
    assert fila["minimo_previo_fecha"] == "2026-01-02"
    assert fila["dias_con_precio"] == 3
    assert fila["dias_por_encima"] == 0
    assert fila["ultima_por_encima"] is None
    assert fila["vuelve_al_minimo"] is False
    assert fila["nuevo_minimo"] is False


def test_un_empate_se_queda_con_la_fecha_mas_antigua(oro):
    """Si el minimo se alcanzo dos veces, la fecha que importa es la primera.

    La otra seria la fecha de la ultima vez, y ensenarla como «el minimo de su
    historia» es una fecha que no aguanta que nadie la compruebe.
    """
    carpeta = oro([
        _precio("dia", "1", "2026-01-01", 100),
        _precio("dia", "1", "2026-01-02", 100),
        _precio("dia", "1", "2026-01-03", 300),
    ])
    fila = _fila(proyecto.calcula(gold=carpeta), "dia:1")

    assert fila["minimo_cent"] == 100
    assert fila["minimo_fecha"] == "2026-01-01"
    assert fila["minimo_previo_fecha"] == "2026-01-01"


def test_el_precio_de_hoy_se_mide_contra_el_minimo_de_antes(oro):
    """Subio a 1,80 y volvio a 1,50: el precio vuelve al minimo de antes."""
    carpeta = oro([
        _precio("dia", "1", "2026-01-01", 200),
        _precio("dia", "1", "2026-01-02", 150),
        _precio("dia", "1", "2026-01-03", 180),
        _precio("dia", "1", "2026-01-04", 150),
    ])
    fila = _fila(proyecto.calcula(gold=carpeta), "dia:1")

    assert fila["minimo_previo_cent"] == 150
    assert fila["minimo_previo_fecha"] == "2026-01-02"
    assert fila["precio_hoy_cent"] == 150
    assert fila["dias_por_encima"] == 1
    assert fila["ultima_por_encima"] == "2026-01-03"
    assert fila["vuelve_al_minimo"] is True
    assert fila["nuevo_minimo"] is False


def test_repetir_el_mismo_precio_todos_los_dias_no_es_volver_al_minimo(oro):
    """**El ruido que esto evita, medido sobre el gold real el 9/11/2026.**

    Con la definicion vieja -- «hoy estas en el minimo» --, **25.328 de 52.106**
    productos con precio hoy salian marcados: casi la mitad, porque un producto que
    no mueve el precio esta siempre en su minimo. Marcar eso no dice nada. Volver
    al minimo es haber estado por encima y haber vuelto, no haber seguido igual.
    """
    carpeta = oro([
        _precio("dia", "1", "2026-01-01", 150),
        _precio("dia", "1", "2026-01-02", 150),
        _precio("dia", "1", "2026-01-03", 150),
    ])
    fila = _fila(proyecto.calcula(gold=carpeta), "dia:1")

    assert fila["precio_hoy_cent"] == 150
    assert fila["minimo_previo_cent"] == 150
    assert fila["dias_por_encima"] == 0
    assert fila["ultima_por_encima"] is None
    assert fila["vuelve_al_minimo"] is False


def test_los_dias_por_encima_se_cuentan_entre_el_minimo_y_hoy(oro):
    """Solo cuentan los dias **posteriores** al minimo previo: los de antes no.

    El minimo de antes se alcanzo el 01-01. Despues subio tres dias y hoy vuelve.
    Los dias anteriores al minimo (no hay) y el de hoy no cuentan.
    """
    carpeta = oro([
        _precio("dia", "1", "2026-01-01", 150),
        _precio("dia", "1", "2026-01-02", 180),
        _precio("dia", "1", "2026-01-03", 170),
        _precio("dia", "1", "2026-01-04", 200),
        _precio("dia", "1", "2026-01-05", 150),
    ])
    fila = _fila(proyecto.calcula(gold=carpeta), "dia:1")

    assert fila["minimo_previo_fecha"] == "2026-01-01"
    assert fila["dias_por_encima"] == 3
    assert fila["ultima_por_encima"] == "2026-01-04"
    assert fila["vuelve_al_minimo"] is True


def test_la_tolerancia_es_de_medio_centimo(oro):
    """La misma tolerancia que `alertas.minimo_90d`: 0,5 centimos no son una bajada."""
    carpeta = oro([
        _precio("dia", "cerca", "2026-01-01", 200),
        _precio("dia", "cerca", "2026-01-02", 250),
        _precio("dia", "cerca", "2026-01-03", 200.4),
        _precio("dia", "lejos", "2026-01-01", 200),
        _precio("dia", "lejos", "2026-01-02", 250),
        _precio("dia", "lejos", "2026-01-03", 201),
    ])
    tabla = proyecto.calcula(gold=carpeta)

    assert _fila(tabla, "dia:cerca")["vuelve_al_minimo"] is True
    assert _fila(tabla, "dia:lejos")["vuelve_al_minimo"] is False


def test_un_precio_por_debajo_del_minimo_anterior_es_un_minimo_nuevo(oro):
    """Baja por debajo de lo mas barato que se habia visto, con margen."""
    carpeta = oro([
        _precio("dia", "1", "2026-01-01", 200),
        _precio("dia", "1", "2026-01-02", 120),
    ])
    fila = _fila(proyecto.calcula(gold=carpeta), "dia:1")

    assert fila["minimo_previo_cent"] == 200
    assert fila["nuevo_minimo"] is True
    # Y el minimo de todo el historico es el de hoy, no el de antes.
    assert fila["minimo_cent"] == 120
    assert fila["minimo_fecha"] == "2026-01-02"


# ------------------------------------------ lo que no tiene con que compararse ---

def test_un_producto_sin_precio_hoy_no_se_marca(oro):
    """Sin precio hoy no hay nada que comparar: ni vuelve al minimo ni es nuevo.

    Se cubren las dos formas de no tener precio: la fila que no existe y la fila
    que existe con el importe vacio. Las dos son «hoy no lo se», no un cero.
    """
    carpeta = oro([
        _precio("dia", "sin-fila", "2026-01-01", 200),
        _precio("dia", "nulo", "2026-01-01", 200),
        _precio("dia", "nulo", "2026-01-02", None),
        # Un tercero con precio, para que la fecha de datos sea la de todos.
        _precio("dia", "con-precio", "2026-01-02", 300),
    ])
    tabla = proyecto.calcula(gold=carpeta)

    for producto_id in ("dia:sin-fila", "dia:nulo"):
        fila = _fila(tabla, producto_id)
        assert fila["precio_hoy_cent"] is None, producto_id
        assert fila["vuelve_al_minimo"] is False, producto_id
        assert fila["nuevo_minimo"] is False, producto_id
        # El historico si esta, y se guarda: manana puede volver.
        assert fila["minimo_cent"] == 200, producto_id
        assert fila["minimo_fecha"] == "2026-01-01", producto_id


def test_un_producto_con_un_solo_dia_no_tiene_minimo_previo(oro):
    """El primer dia de un producto no es «su minimo historico»: no hay historia."""
    carpeta = oro([
        _precio("dia", "1", "2026-01-01", 180),
        _precio("dia", "2", "2026-01-01", 300),
    ])
    fila = _fila(proyecto.calcula(gold=carpeta), "dia:1")

    assert fila["minimo_previo_cent"] is None
    assert fila["minimo_previo_fecha"] is None
    assert fila["minimo_cent"] == 180
    assert fila["minimo_fecha"] == "2026-01-01"
    assert fila["dias_con_precio"] == 1
    assert fila["vuelve_al_minimo"] is False
    assert fila["nuevo_minimo"] is False


# ------------------------------------------------- artefacto, resumen y nombres ---

def test_escribe_el_artefacto_y_el_resumen(oro, tmp_path):
    """Los dos ficheros, con la forma que consume la API y el nombre de cada cosa."""
    carpeta = oro([
        _precio("dia", "1", "2026-01-01", 200),
        _precio("dia", "1", "2026-01-02", 150),
    ], productos=[_producto("dia", "1", 7, "Leche entera DIA", "DIA", 150)])
    destino = tmp_path / "datos"
    destino.mkdir()

    ruta_artefacto, ruta_resumen = proyecto.escribe(gold=carpeta, datos=destino)

    assert ruta_artefacto.name == "minimos.parquet"
    assert ruta_resumen.name == "minimos-resumen.json"
    assert ruta_artefacto.exists() and ruta_resumen.exists()
    # El artefacto trae la fecha de datos en cada fila: es lo que la API compara
    # con `catalogo.fecha_de_gold()` antes de marcar nada.
    tabla = pl.read_parquet(ruta_artefacto)
    assert tabla.height == 1
    assert tabla["fecha_datos"].to_list() == ["2026-01-02"]

    resumen = proyecto.resumen(tabla, gold=carpeta)
    assert resumen["fecha_datos"] == "2026-01-02"
    assert resumen["ventana_dias"] == 2
    assert resumen["productos"] == 1
    assert resumen["con_historial"] == 1
    assert resumen["generado"]


def test_el_resumen_nombra_a_los_que_vuelven_y_a_los_nuevos(oro):
    """El fichero de resumen de David: quien vuelve al minimo, con su nombre.

    El nombre, la marca y el grupo salen de `grupos.parquet`, que es donde el
    emparejador los deja. Un `producto_id` suelto no le dice nada a nadie.
    """
    carpeta = oro([
        _precio("dia", "vuelve", "2026-01-01", 200),
        _precio("dia", "vuelve", "2026-01-02", 250),
        _precio("dia", "vuelve", "2026-01-03", 200),
        _precio("dia", "nuevo", "2026-01-01", 300),
        _precio("dia", "nuevo", "2026-01-03", 250),
        _precio("dia", "normal", "2026-01-01", 100),
        _precio("dia", "normal", "2026-01-03", 400),
    ], productos=[
        _producto("dia", "vuelve", 11, "Cafe molido DIA", "DIA", 200),
        _producto("dia", "nuevo", 12, "Aceite de oliva DIA", "DIA", 250),
        _producto("dia", "normal", 13, "Pan de molde DIA", "DIA", 400),
    ])
    tabla = proyecto.calcula(gold=carpeta)
    resumen = proyecto.resumen(tabla, gold=carpeta)

    vuelven = {x["producto_id"]: x for x in resumen["vuelven_al_minimo"]}
    nuevos = {x["producto_id"]: x for x in resumen["nuevos_minimos"]}
    assert set(vuelven) == {"dia:vuelve"}
    assert set(nuevos) == {"dia:nuevo"}

    cafe = vuelven["dia:vuelve"]
    assert cafe["nombre"] == "Cafe molido DIA"
    assert cafe["marca"] == "DIA"
    assert cafe["grupo_id"] == 11
    assert cafe["fuente"] == "dia"
    assert cafe["id_fuente"] == "vuelve"
    assert cafe["precio_hoy_cent"] == 200
    assert cafe["minimo_cent"] == 200
    assert cafe["minimo_fecha"] == "2026-01-01"
    assert cafe["minimo_previo_cent"] == 200
    assert cafe["minimo_previo_fecha"] == "2026-01-01"
    # Lo que hace que la lista sea corta y util: subio y volvio.
    assert cafe["dias_por_encima"] == 1
    assert cafe["ultima_por_encima"] == "2026-01-02"

    aceite = nuevos["dia:nuevo"]
    assert aceite["minimo_previo_cent"] == 300
    assert aceite["precio_hoy_cent"] == 250


# ------------------------------------------------------------- la marca en la API ---

def _listo_para_la_api(oro, diario, productos):
    """Gold sintetico + artefacto, con `catalogo` apuntando al gold de mentira."""
    carpeta = oro(diario, productos)
    proyecto.escribe(gold=carpeta, datos=carpeta.parent)
    return carpeta


@pytest.fixture
def api(monkeypatch):
    """La API leyendo el gold de mentira que deje cada prueba."""
    def apunta(carpeta):
        monkeypatch.setattr(catalogo, "AJUSTES",
                            replace(catalogo.AJUSTES, gold=carpeta))
        catalogo.reiniciar()
        return carpeta
    return apunta


def test_la_linea_se_marca_con_el_minimo_de_su_producto(oro, api):
    carpeta = _listo_para_la_api(oro, [
        _precio("dia", "1", "2026-01-01", 200),
        _precio("dia", "1", "2026-01-02", 250),
        _precio("dia", "1", "2026-01-03", 200),
    ], [_producto("dia", "1", 7, "Leche entera DIA", "DIA", 200)])
    api(carpeta)

    lineas = [{"id": "l1", "grupo_id": 7, "producto_id": "dia:1",
               "nombre_visto": "leche"}]
    salida = api_minimos.con_minimos(lineas)

    assert salida[0]["minimo"] == {
        "producto_id": "dia:1",
        "cadena": "dia",
        "precio_cent": 200,
        "precio_unidad_cent": 200.0,
        "unidad": "ud",
        "minimo_cent": 200,
        "minimo_fecha": "2026-01-01",
        "vuelve_al_minimo": True,
        "nuevo_minimo": False,
    }
    # Y la linea original no se toca: la lista que llega se copia, no se muta.
    assert "minimo" not in lineas[0]


def test_el_producto_de_la_linea_manda_sobre_el_mas_barato_del_grupo(oro, api):
    """Si la linea sabe de que producto habla, se marca ese y no otro del grupo."""
    carpeta = _listo_para_la_api(oro, [
        _precio("dia", "caro", "2026-01-01", 200),
        _precio("dia", "caro", "2026-01-02", 200),
        _precio("aldi", "barato", "2026-01-01", 100),
        _precio("aldi", "barato", "2026-01-02", 100),
    ], [
        _producto("dia", "caro", 7, "Leche DIA", "DIA", 200),
        _producto("aldi", "barato", 7, "Leche ALDI", "ALDI", 100),
    ])
    api(carpeta)

    lineas = [{"id": "l1", "grupo_id": 7, "producto_id": "dia:caro"}]
    salida = api_minimos.con_minimos(lineas)

    assert salida[0]["minimo"]["producto_id"] == "dia:caro"
    assert salida[0]["minimo"]["minimo_cent"] == 200


def test_una_linea_sin_producto_cae_al_mas_barato_del_grupo(oro, api):
    """Lo que no tiene producto se marca con el mejor del grupo, con las reglas de hoy.

    Y las reglas son las de `alertas._mejor_de_cada_grupo`: la oferta de tarjeta
    del `dia` no cuenta, porque no baja lo que se paga en la caja.
    """
    carpeta = _listo_para_la_api(oro, [
        _precio("dia", "club", "2026-01-01", 90),
        _precio("dia", "club", "2026-01-02", 90),
        _precio("aldi", "normal", "2026-01-01", 150),
        _precio("aldi", "normal", "2026-01-02", 130),
    ], [
        _producto("dia", "club", 7, "Leche DIA (tarjeta)", "DIA", 90, club=True),
        _producto("aldi", "normal", 7, "Leche ALDI", "ALDI", 130),
    ])
    api(carpeta)

    lineas = [{"id": "l1", "grupo_id": 7, "producto_id": None}]
    salida = api_minimos.con_minimos(lineas)

    minimo = salida[0]["minimo"]
    assert minimo["producto_id"] == "aldi:normal"
    assert minimo["cadena"] == "aldi"


def test_sin_artefacto_no_se_marca_nada_y_no_revienta(oro, api):
    """La cadena puede no haber pasado todavia: la lista se sirve sin marcas."""
    carpeta = oro([
        _precio("dia", "1", "2026-01-01", 200),
        _precio("dia", "1", "2026-01-02", 150),
    ], [_producto("dia", "1", 7, "Leche DIA", "DIA", 150)])
    api(carpeta)

    lineas = [{"id": "l1", "grupo_id": 7, "producto_id": "dia:1"}]
    salida = api_minimos.con_minimos(lineas)

    assert "minimo" not in salida[0]
    assert salida[0] == lineas[0]


def test_un_artefacto_de_otro_dia_no_marca_nada(oro, api):
    """La marca mas cara que puede dar la API es una de un precio que ya no es.

    Si el artefacto se quedo en un dia anterior al de gold, no se marca: se
    degrada en silencio y la pantalla sigue ensenando los precios de hoy.
    """
    carpeta = _listo_para_la_api(oro, [
        _precio("dia", "1", "2026-01-01", 200),
        _precio("dia", "1", "2026-01-02", 150),
    ], [_producto("dia", "1", 7, "Leche DIA", "DIA", 150)])
    api(carpeta)

    ruta = carpeta.parent / "minimos.parquet"
    vieja = pl.read_parquet(ruta).with_columns(
        pl.lit("2025-12-31").alias("fecha_datos"))
    vieja.write_parquet(ruta)

    lineas = [{"id": "l1", "grupo_id": 7, "producto_id": "dia:1"}]
    salida = api_minimos.con_minimos(lineas)

    assert "minimo" not in salida[0]


def test_una_linea_sin_producto_ni_grupo_no_se_marca(oro, api):
    """«Papel de cocina» sin identificar no tiene minimo que ensenar. Y no se cae."""
    carpeta = _listo_para_la_api(oro, [
        _precio("dia", "1", "2026-01-01", 200),
        _precio("dia", "1", "2026-01-02", 150),
    ], [_producto("dia", "1", 7, "Leche DIA", "DIA", 150)])
    api(carpeta)

    lineas = [{"id": "l1", "grupo_id": None, "producto_id": None,
               "nombre_visto": "papel de cocina"}]
    salida = api_minimos.con_minimos(lineas)

    assert "minimo" not in salida[0]


def test_una_linea_movida_no_se_marca_con_su_grupo(oro, api):
    """Si el grupo ya no es el producto, buscar el mejor del grupo seria mentir.

    La linea movida es la que `catalogo.lineas_movidas` ha marcado: su
    `grupo_id` apunta a otro producto. Se puede marcar por su `producto_id`
    -- eso si es identidad --, pero nunca por el grupo.
    """
    carpeta = _listo_para_la_api(oro, [
        _precio("dia", "1", "2026-01-01", 200),
        _precio("dia", "1", "2026-01-02", 150),
    ], [_producto("dia", "1", 7, "Leche DIA", "DIA", 150)])
    api(carpeta)

    lineas = [{"id": "l1", "grupo_id": 7, "producto_id": None,
               "producto_movido": True}]
    salida = api_minimos.con_minimos(lineas)

    assert "minimo" not in salida[0]


# --------------------------------------------------------------- el enganche ---

RAIZ = Path(__file__).resolve().parents[1]


def test_el_paso_esta_en_la_cadena_y_no_puede_tumbar_el_dia():
    """El paso de minimos, en `run.py` y dentro de un `try`.

    El contrato lo dice con esas palabras: *sin que un fallo de minimos tumbe el
    dia*. Aqui no se prueba el orden entero de la pasada -- eso lo corre el Lead
    --, sino que el paso exista y que su fallo se registre en vez de propagarse.
    """
    fuente = RAIZ / "projects" / "cesta" / "run.py"
    arbol = ast.parse(fuente.read_text(encoding="utf-8"), filename=str(fuente))
    dentro_de_try = [
        nodo for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Try)
        and any(isinstance(hijo, ast.Constant)
                and hijo.value == "projects.cesta.minimos"
                for hijo in ast.walk(nodo))]
    assert dentro_de_try, "el paso de minimos no esta en run.py"
    assert all(nodo.handlers for nodo in dentro_de_try), (
        "el paso de minimos esta fuera de un try: un fallo suyo tumbaria la pasada")


def test_la_lista_se_marca_desde_ver_lista():
    """`GET /api/listas/{lista_id}` cuelga el campo de las lineas antes de servirlas."""
    fuente = (RAIZ / "plataforma" / "api" / "main.py").read_text(encoding="utf-8")
    assert "minimos.con_minimos(lineas)" in fuente, (
        "`ver_lista` no llama a la funcion que engancha el minimo a las lineas")
    assert "    minimos,\n" in fuente, (
        "`main.py` no importa el modulo de minimos: el campo no llegaria nunca")

