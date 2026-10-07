"""Pedir fichas desde la cola: con presupuesto, con hash y dejando la proxima revision puesta.

**Por que es la pieza que cierra S02 y S03.** La cola sabe a quien le falta ficha; el lector sabe leer
una ficha. Lo que faltaba es quien las junte **sin romper nada**: coger unos pocos candidatos con su
*lease*, pedir su ficha, leerla, y cerrar la ficha en la cola con el hash del contenido util, la
version del parser y la fecha de la proxima revision.

**Las reglas, que son las del contrato:**

  - **Presupuesto**: se procesan como mucho `limite` fichas por ejecucion. No hay bucle hasta agotar:
    una ejecucion que no termina no es progreso, es un rastro que se queda a medias.
  - **El *lease* manda**: si el proceso se muere a mitad, la ficha vuelve sola a la cola (S02). Aqui no
    hay que hacer nada especial, y eso es lo que se gana por haberlo hecho bien alli.
  - **Fallo de red y dato que falta son estados distintos**: un error de red deja la ficha en
    `error_temporal` (se reintenta, **no cuenta como intento fallido del producto**); que la ficha no
    publique el detalle la deja en `no_publicado`, que es un dato sobre la fuente, no un fallo nuestro.
  - **El hash se guarda siempre que se lee algo**: es lo que permitira detectar que la ficha cambio sin
    volver a leerla entera.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime

from core import inventario
from projects.cesta import ficha_lidl

PARSER_VERSION = "lidl-jsonld-1"


def _hash_util(datos: dict) -> str:
    util = "|".join(str(datos.get(k) or "") for k in
                    ("nombre", "marca", "ean", "precio_cent", "descripcion"))
    return hashlib.sha256(util.encode()).hexdigest()[:16]


def procesa(con, limite: int = 3, *, fetch=None, ahora: datetime | None = None) -> dict:
    """Procesa hasta `limite` fichas de la cola. Devuelve el recuento por resultado.

    `fetch` es inyectable para poder probar **sin red**: en produccion es la descarga real, y en las
    pruebas una funcion que devuelve el fixture.
    """
    traer = fetch or (lambda url: ficha_lidl.descarga(url))
    cuenta = {"leidas": 0, "correctas": 0, "no_publicado": 0, "error_temporal": 0}
    for fila in inventario.tomar(con, limite, fuentes=["lidl"], ahora=ahora):
        cuenta["leidas"] += 1
        clave = (fila["fuente"], fila["id_fuente"], fila["variante"], fila["ambito"])
        try:
            html = traer(fila["url"] or "")
        except Exception as exc:  # noqa: BLE001  (red: se reintenta, no es culpa del producto)
            inventario.terminar(con, clave, inventario.ERROR_TEMPORAL,
                                resultado=f"{type(exc).__name__}: {exc}"[:180], ahora=ahora)
            cuenta["error_temporal"] += 1
            continue
        try:
            datos = ficha_lidl.lee(html, url=fila["url"])
        except ValueError as exc:
            # La pagina vive pero no publica la ficha: es un dato sobre la fuente, no un fallo nuestro.
            inventario.terminar(con, clave, inventario.NO_PUBLICADO, resultado=str(exc),
                                parser_version=PARSER_VERSION, ahora=ahora)
            cuenta["no_publicado"] += 1
            continue
        inventario.terminar(con, clave, inventario.CORRECTO,
                            resultado=f"ean={datos['ean'] or 'sin GTIN valido'}",
                            hash_util=_hash_util(datos), parser_version=PARSER_VERSION,
                            evidencia=datos.get("url"), ahora=ahora)
        cuenta["correctas"] += 1
    return cuenta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--limite", type=int, default=3,
                    help="cuantas fichas como maximo en esta ejecucion (no hay bucle hasta agotar)")
    a = ap.parse_args(argv)
    con = inventario.conecta()
    cuenta = procesa(con, a.limite)
    print(f"fichas procesadas: {cuenta['leidas']} · correctas {cuenta['correctas']} · "
          f"sin publicar {cuenta['no_publicado']} · error de red {cuenta['error_temporal']}")
    res = inventario.resumen(con).get("lidl", {})
    print("  cola de Lidl: " + "  ".join(f"{k}={v}" for k, v in sorted(res.items())))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
