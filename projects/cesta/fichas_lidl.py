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

from core import config, inventario
from projects.cesta import ficha_lidl

PARSER_VERSION = "lidl-jsonld-2"

# **Cuantas fichas por ejecucion, y por que ese numero.** El limite era 3, y con la cola real
# -- **5.026 pendientes de Lidl** -- eso son **1.677 dias: cuatro anos y medio** para cubrir una
# sola cadena. *Tres fichas por ejecucion no acreditan cobertura: es la «cifra artificial» que
# G09 nombra en su titulo y lo que G08 pide calcular en su punto 179.*
#
# A 1 peticion por segundo (el ritmo declarado en `config.RITMO`), 1.000 fichas son ~17 minutos
# de red. *La recoleccion diaria entera dura unos 90, asi que esto es una quinta parte y cabe.*
# **Y el plazo se dice en vez de suponerlo**: `--limite` lo cambia, y el resumen imprime lo que
# queda y los dias que faltan al ritmo actual.
LIMITE_POR_EJECUCION = 1000


# **Que campos vigila el hash, y por que esos.** El hash existe para detectar que **la ficha**
# cambio. Antes hasheaba `precio_cent`, que **no es parte de la ficha** -- un producto estable con una
# oferta nueva marcaba «la ficha cambio» -- y dejaba fuera `gtin_invalido`, `url` e `imagen`, que si
# lo son. *Y `ean` a secas no bastaba: cuando el codigo no valida, `ean` es `None` y el codigo vive en
# `gtin_invalido`, asi que dos fichas con GTIN invalido **distinto** daban el mismo hash.*
#
# **Y lo que este hash NO puede vigilar, medido.** El bloque `@type=Product` de Lidl trae nueve
# claves -- `@type, brand, description, gtin13, image, name, offers, sku, url` -- y **no publica
# ingredientes, nutricion ni alergenos**, ni siquiera en un alimento: comprobado sobre una ficha de
# galletas. *Asi que no hay campos de contenido que hashear: no es un parser incompleto, es una fuente
# que no los da.* Para tenerlos hay que **parsear el HTML** de la ficha o ir a **fuente
# complementaria** (G08, puntos 176 y 181: GTIN y presentacion compatibles antes de vincular).
CAMPOS_DE_FICHA = ("nombre", "marca", "ean", "gtin_invalido", "descripcion", "url", "imagen")


def _hash_util(datos: dict) -> str:
    util = "|".join(str(datos.get(k) or "") for k in CAMPOS_DE_FICHA)
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
    ap.add_argument("--limite", type=int, default=LIMITE_POR_EJECUCION,
                    help=f"cuantas fichas como maximo en esta ejecucion (por defecto "
                         f"{LIMITE_POR_EJECUCION}; no hay bucle hasta agotar)")
    a = ap.parse_args(argv)
    con = inventario.conecta()
    cuenta = procesa(con, a.limite)
    print(f"fichas procesadas: {cuenta['leidas']} · correctas {cuenta['correctas']} · "
          f"sin publicar {cuenta['no_publicado']} · error de red {cuenta['error_temporal']}")
    res = inventario.resumen(con).get("lidl", {})
    print("  cola de Lidl: " + "  ".join(f"{k}={v}" for k, v in sorted(res.items())))
    # **Y lo que falta, con su plazo.** *Un contador sin fecha no dice si el trabajo avanza.*
    pendientes = int(res.get("pendiente", 0) or 0)
    if pendientes and a.limite > 0:
        dias = -(-pendientes // max(a.limite, 1))          # techo, sin decimales
        ritmo = config.RITMO.get("lidl", 1.0)
        print(f"  quedan {pendientes:,} fichas de Lidl: a {a.limite} por ejecucion son {dias:,} "
              f"ejecuciones (~{dias * (a.limite / ritmo) / 3600:.1f} h de red)".replace(",", "."))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
