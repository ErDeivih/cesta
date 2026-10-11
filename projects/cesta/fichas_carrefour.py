"""**Pedir fichas de Carrefour: su URL sale del catalogo, y se lee con `ficha_carrefour`.**

Por que existe
--------------
Medido en F05: **Carrefour publica la tabla de nutricion en la pagina de producto** -- *comprobado pidiendo
una, con `robots.txt` comprobado: `kcal` seis veces, «por 100 g» una, y los numeros cuadran (aceite de oliva,
900 kcal y 100 g de grasa).* **Y sus 2.004 crudos son paginas de categoria, que no la traen.**

*Asi que hay que **pedir** la ficha, una por producto, como Lidl.*

**Y una pieza mas que el ejecutor de Lidl no necesita**, medida antes de escribirlo:
**la cola solo trae URL para Lidl.**

```
cola de fichas, por cadena:
    carrefour   17.283 pendientes  ·      0 con url     <- NO HAY URL
    lidl         5.026 pendientes  ·  5.026 con url
```

*Y tiene su explicacion*: **`inventario.enganche` levanta la cola de bronze leyendo solo `id_fuente`, y de
bronze no sale una direccion.** *Las URL de Lidl se rellenaron para su ejecutor, que es el unico que habia.*

**Asi que aqui la URL se resuelve del catalogo** (`grupos.url`), y **si el producto no esta en el catalogo de
hoy, no hay nada que pedir** -- *que es un resultado, no un fallo.*

Lo que hace, y lo que no
------------------------
**Procesa hasta `limite` fichas** -- *con presupuesto, como el de Lidl: no hay bucle hasta agotar* --, **y
`fetch` es inyectable para poder probarlo sin red.**

*No baja nada en las pruebas, no inventa el dato, y **no da por buena una pagina sin tabla**:* `lee` devuelve
`{}` y eso se marca `NO_PUBLICA` -- *un dato sobre la fuente, no un fallo nuestro.*
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from core import config, inventario  # noqa: E402
from core.fetch import Fetcher  # noqa: E402
from projects.cesta import ficha_carrefour  # noqa: E402

FUENTE = "carrefour"

# **La version del parser, como en Lidl.** *Lo que permite saber con que codigo se leyo cada ficha, y volver
# a leerla cuando cambie.*
PARSER_VERSION = "carrefour-nutrition-1"

# **Cuantas fichas por ejecucion.** *Pedir 17.283 de golpe es una operacion de red de verdad: el limite es el
# presupuesto, y `--limite` lo cambia.*
LIMITE_POR_EJECUCION = 100


def urls_del_catalogo(fuente: str = FUENTE) -> dict[str, str]:
    """**De `id_fuente` a su URL, por el catalogo.** *La cola no la trae: se resuelve aqui.*

    *Es la pieza que el ejecutor de Lidl no necesita, y la que hacia falta para no fallar en la primera fila
    con `fila["url"] is None`.*
    """
    from plataforma.api import catalogo

    filas = catalogo.conexion().execute(
        "SELECT DISTINCT id_fuente, url FROM grupos "
        "WHERE fuente = ? AND url IS NOT NULL AND url != ''", [fuente]).fetchall()
    return {str(ident): str(url) for ident, url in filas}


def procesa(con, limite: int = 3, *, fetch=None, urls: dict[str, str] | None = None,
            ahora: datetime | None = None) -> dict:
    """Procesa hasta `limite` fichas de la cola. Devuelve el recuento por resultado.

    *`fetch` y `urls` son inyectables para poder probarlo **sin red y sin catalogo**: en produccion son la
    descarga real y las URL del catalogo; en las pruebas, lo que devuelva el ensayo.*
    """
    traer = fetch or (lambda url: ficha_carrefour_descarga(url))
    mapa = urls if urls is not None else urls_del_catalogo()
    cuenta = {"leidas": 0, "correctas": 0, "no_publicado": 0, "error_temporal": 0, "sin_url": 0}

    for fila in inventario.tomar(con, limite, fuentes=[FUENTE], ahora=ahora):
        cuenta["leidas"] += 1
        clave = (fila["fuente"], fila["id_fuente"], fila["variante"], fila["ambito"])
        # **La URL, del catalogo.** *Y si no esta, se dice: es un resultado, no un fallo.*
        url = fila["url"] or mapa.get(str(fila["id_fuente"]))
        if not url:
            inventario.terminar(con, clave, inventario.NO_PUBLICADO,
                                resultado="sin url en el catalogo: no hay nada que pedir", ahora=ahora)
            cuenta["sin_url"] += 1
            continue
        try:
            html = traer(url)
        except Exception as exc:  # noqa: BLE001  (red: se reintenta, no es culpa del producto)
            inventario.terminar(con, clave, inventario.ERROR_TEMPORAL,
                                resultado=f"{type(exc).__name__}: {exc}"[:180], ahora=ahora)
            cuenta["error_temporal"] += 1
            continue
        # **Una pagina sin tabla no es un fallo nuestro**: es que esa fuente no la publica.
        datos = ficha_carrefour.lee(html)
        if not [k for k in datos if k != "por"]:
            inventario.terminar(con, clave, inventario.NO_PUBLICADO,
                                resultado="la pagina no trae tabla nutricional",
                                parser_version=PARSER_VERSION, ahora=ahora)
            cuenta["no_publicado"] += 1
            continue
        inventario.terminar(con, clave, inventario.CORRECTO,
                            resultado=f"nutricion por {datos.get('por') or 'base desconocida'}",
                            hash_util=ficha_carrefour.hash_util(datos),
                            parser_version=PARSER_VERSION, evidencia=url, ahora=ahora)
        cuenta["correctas"] += 1
    return cuenta


def ficha_carrefour_descarga(url: str) -> str:
    """**La descarga de verdad** -- *una peticion, con el fetcher del proyecto y su ritmo.*

    *Se separa para que `procesa` pueda probarse sin red: es lo unico que toca la red en todo el modulo.*
    """
    from projects.cesta import ficha_carrefour as fc  # noqa: F401  (por si el nombre cambia)

    f = Fetcher(rate_per_sec=config.RITMO.get(FUENTE, 1.0))
    r = f.get(url)
    return r.body.decode("utf-8", "replace")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pedir fichas de Carrefour desde la cola.")
    ap.add_argument("--limite", type=int, default=LIMITE_POR_EJECUCION,
                    help=f"cuantas fichas por ejecucion (por defecto {LIMITE_POR_EJECUCION}; "
                         f"no hay bucle hasta agotar)")
    a = ap.parse_args(argv)

    con = inventario.conecta(config.DATA / "inventario.sqlite")
    try:
        cuenta = procesa(con, a.limite)
        con.commit()
    finally:
        con.close()

    print(f"  carrefour: {cuenta}")
    # **Y cuanto queda**, que es lo que decide si merece la pena seguir: *el ejecutor de Lidl lo dice, y esa
    # linea es la que convierte el limite en un presupuesto.*
    con = inventario.conecta(config.DATA / "inventario.sqlite")
    try:
        pendientes = inventario.resumen(con).get(FUENTE, {}).get(inventario.PENDIENTE, 0)
    finally:
        con.close()
    if pendientes and a.limite > 0:
        dias = -(-pendientes // max(a.limite, 1))
        print(f"  quedan {pendientes:,} fichas de Carrefour: a {a.limite} por ejecucion son {dias:,} "
              f"ejecuciones".replace(",", "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
