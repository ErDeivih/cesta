"""La marca de minimo en las lineas de la lista: el campo `minimo` de `ver_lista`.

La cadena diaria deja `data/minimos.parquet` (`projects/cesta/minimos.py`) con el
minimo visto de cada producto, su fecha y dos marcas: si el precio **vuelve** al
minimo (`vuelve_al_minimo`) o si **estrena** minimo (`nuevo_minimo`). Este modulo
lo lee y se lo cuelga a cada linea de la lista. Nada mas: no hay avisos
emergentes, es una marca visual y un fichero de resumen.

Tres reglas, y las tres son de la casa:

  - **Si el artefacto no esta, no se marca nada.** La web que lo consume no puede
    depender de que la cadena haya pasado ya; una lista sin marcas es una lista.
  - **Si la fecha del artefacto no es la de gold, tampoco.** *Mejor no marcar que
    mentir*: un minimo de ayer al lado de un precio de hoy es una afirmacion que
    nadie ha medido. Se degrada en silencio, que es lo que pide el contrato.
  - **El producto de la linea manda.** Si la linea dice de que producto habla
    (`autorizado_producto`, luego `producto_id`), se marca **ese**. Solo cuando no
    lo dice se busca **el mas barato de hoy de su `grupo_id`**, y con las mismas
    reglas que `alertas._mejor_de_cada_grupo`: ni ofertas de tarjeta ni de solo
    internet, y una sola unidad por grupo. Una linea movida (su `grupo_id` ya no
    es su producto) **no** cae al grupo: ahi el grupo es otro producto.

Se lee con DuckDB **solo para leer**: no se escribe ni se crea nada en la carpeta
de datos, que en el contenedor va montada en modo lectura.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from . import cache, catalogo

# El artefacto que deja la cadena, al lado de gold. El contenedor monta `data/`
# como `/datos` y `CESTA_GOLD=/datos/gold`, asi que la carpeta que lo contiene es
# `Path(gold).parent`.
NOMBRE = "minimos.parquet"

# Las columnas que se leen del artefacto. Explicitas: el parquet lo escribe otro
# paso, y pedir de mas obligaria a migrar los dos a la vez.
COLUMNAS = ("producto_id", "fuente", "id_fuente", "fecha_datos",
            "precio_hoy_cent", "precio_hoy_unidad_cent", "unidad_canon",
            "minimo_cent", "minimo_fecha", "minimo_previo_cent",
            "minimo_previo_fecha", "dias_por_encima", "ultima_por_encima",
            "vuelve_al_minimo", "nuevo_minimo")


def ruta_artefacto() -> Path:
    """Donde vive `minimos.parquet` segun el gold que sirve esta API.

    **La ruta de gold se pregunta a `catalogo`**, que es quien la resuelve y
    quien la tiene parcheada en las pruebas. Tenerla importada aparte seria una
    segunda copia del mismo ajuste, y dos copias de una ruta acaban diciendo
    cosas distintas -- con un artefacto en un sitio y la fecha de otro.
    """
    return Path(catalogo.AJUSTES.gold).parent / NOMBRE


def _lee_de_verdad(ruta: Path, fecha: str) -> dict[str, dict]:
    """La lectura de verdad, con DuckDB y **solo lectura**: el SELECT no escribe nada."""
    con = duckdb.connect(database=":memory:")
    try:
        filas = con.execute(
            f"SELECT {', '.join(COLUMNAS)} FROM read_parquet(?) "
            "WHERE fecha_datos::VARCHAR = ? AND precio_hoy_cent IS NOT NULL",
            [str(ruta).replace("\\", "/"), fecha]).fetchall()
    finally:
        con.close()
    return {fila[0]: dict(zip(COLUMNAS, fila, strict=True)) for fila in filas}


def lee() -> dict[str, dict]:
    """El artefacto indexado por `producto_id`, o `{}` si no sirve para hoy.

    Devuelve solo productos **con precio hoy**: sin precio no hay nada que
    comparar, y una marca sin precio no se puede ensenar. El minimo viejo de un
    producto que hoy no tiene precio sigue en el artefacto; lo que no hace es
    marcar nada.

    **Se recuerda mientras no cambie el fichero.** Medido el 9/11/2026 sobre el
    gold real: leer las quince columnas de las 52.106 filas con precio hoy cuesta
    ~260 ms, y `/api/listas/{id}` se pide en cada visita. La clave lleva la
    version de gold (`cache.recuerda`), el `mtime` del propio artefacto y la fecha
    de datos: publicar otro gold, reescribir el artefacto o cambiar el dia tiran
    la entrada. *No se cachea una respuesta por persona: esto no lleva nada de
    nadie.*

    Nunca levanta: un artefacto ausente, truncado, de otro dia o con columnas de
    una version anterior se trata igual -- no se marca y la pantalla sigue.
    """
    ruta = ruta_artefacto()
    try:
        info = ruta.stat()
        fecha_gold = catalogo.fecha_de_gold()
    except Exception:  # noqa: BLE001  (sin artefacto o sin gold no hay con que comparar)
        return {}
    if not fecha_gold:
        return {}
    try:
        return cache.recuerda(
            "minimos.artefacto",
            (ruta.as_posix(), info.st_mtime_ns, info.st_size, str(fecha_gold)),
            lambda: _lee_de_verdad(ruta, str(fecha_gold)))
    except Exception:  # noqa: BLE001  (artefacto de otra forma: no se marca)
        return {}


def _marca(fila: dict) -> dict | None:
    """Una fila del artefacto -> el campo `minimo` de la linea, con su forma exacta."""
    if fila.get("minimo_cent") is None:
        return None
    return {
        "producto_id": fila["producto_id"],
        # `cadena` es el nombre que usa la pantalla para una fuente; el artefacto
        # la guarda como `fuente`, que es el nombre del colector.
        "cadena": fila["fuente"],
        # El precio que se juzgo, que es el del dia de datos: el mismo con el que
        # se midio el minimo. Si la pantalla pintara otro, la marca no cuadraria.
        "precio_cent": fila["precio_hoy_cent"],
        "precio_unidad_cent": fila["precio_hoy_unidad_cent"],
        "unidad": fila["unidad_canon"],
        "minimo_cent": fila["minimo_cent"],
        "minimo_fecha": fila["minimo_fecha"],
        "vuelve_al_minimo": bool(fila["vuelve_al_minimo"]),
        "nuevo_minimo": bool(fila["nuevo_minimo"]),
    }


def _de_la_linea(linea: dict, artefacto: dict[str, dict]) -> dict | None:
    """La marca del producto que la linea dice ser, si lo dice y hay datos.

    `autorizado_producto` va antes que `producto_id` porque es **lo que la
    persona confirmo** cuando acepto una sustitucion; si los dos existen y no
    coinciden, manda lo confirmado.
    """
    for clave in ("autorizado_producto", "producto_id"):
        producto = linea.get(clave)
        if not producto:
            continue
        fila = artefacto.get(str(producto))
        if fila is not None:
            return _marca(fila)
    return None


def _marcas_por_grupo(lineas: list[dict], artefacto: dict[str, dict]) -> dict[int, dict]:
    """La marca del producto mas barato de hoy de cada grupo que la necesita.

    `alertas._mejor_de_cada_grupo` **se importa, no se copia**: sus reglas (nada
    de tarjeta ni de solo internet, una unidad dominante por grupo) son las que
    deciden de que producto habla una linea sin producto, y una segunda copia de
    esas reglas acabaria diciendo otra cosa. Se llama solo con los grupos que de
    verdad no tienen producto propio: es la consulta cara del proyecto.
    """
    from . import alertas

    grupos = sorted({
        int(linea["grupo_id"]) for linea in lineas
        if linea.get("grupo_id") is not None
        and not linea.get("producto_movido")
        and _de_la_linea(linea, artefacto) is None
    })
    if not grupos:
        return {}
    try:
        mejores = alertas._mejor_de_cada_grupo(grupos)
    except Exception:  # noqa: BLE001  (sin gold legible no se marca, no se cae la lista)
        return {}
    marcas: dict[int, dict] = {}
    for grupo, mejor in mejores.items():
        fila = artefacto.get(f"{mejor['cadena']}:{mejor['id_fuente']}")
        if fila is not None:
            marca = _marca(fila)
            if marca is not None:
                marcas[grupo] = marca
    return marcas


def con_minimos(lineas: list[dict]) -> list[dict]:
    """Las lineas, cada una con su `minimo` **si lo hay**. No reordena ni muta.

    El campo no viaja vacio ni a `None`: la linea que no tiene minimo sale sin la
    clave, que es lo que la pantalla usa para distinguir «no lo se» de un dato.
    Los diccionarios que llegan no se tocan; sale una lista nueva.
    """
    if not lineas:
        return lineas
    artefacto = lee()
    if not artefacto:
        return lineas

    # Primero el producto propio: es el caso bueno y el que no cuesta una consulta.
    propias = [_de_la_linea(linea, artefacto) for linea in lineas]
    por_grupo = _marcas_por_grupo(
        [linea for linea, marca in zip(lineas, propias, strict=True) if marca is None],
        artefacto)

    salida = []
    for linea, marca in zip(lineas, propias, strict=True):
        if marca is None:
            marca = por_grupo.get(int(linea["grupo_id"])) \
                if linea.get("grupo_id") is not None else None
        salida.append(linea | {"minimo": marca} if marca is not None else linea)
    return salida
