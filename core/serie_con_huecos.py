"""*** UN DIA SIN CAPTURA ES UN HUECO, NO UN DIA QUE NO EXISTIO. ***

*Carrefour pierde **uno de cada cinco dias** (7 de 44 medidos entre el 7/9 y el 20/10 de 2026, y el 18 de octubre es
uno de ellos).* *El colector reintenta y el motivo esta investigado en
`docs/investigaciones/B02-carrefour-tambien-tiene-resistencia.md`.*

*Lo que faltaba era otra cosa, y es de una linea de servidor: `api/catalogo.py` devuelve la serie **solo con los dias
capturados**, asi que el cliente recibe el 17 y el 19 **como si fueran consecutivos**.*

*** Y el cliente lleva meses preparado para lo contrario: `curva.ts` y `chispa.ts` declaran `valor: number | null`, y
`chispa.ts` tiene una prueba que se llama «un dia sin valor se coloca como HUECO, no se salta», con su motivo
escrito: «saltarlo juntaria dos dias que no son seguidos, y la linea mentiria». ***

*Aqui se rellena lo que falta, **antes** de que la serie salga del servidor.*
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def _dia(texto: Any) -> date | None:
    """*`YYYY-MM-DD` a `date`, o `None` si no lo es.*"""
    if texto is None:
        return None
    try:
        return date.fromisoformat(str(texto)[:10])
    except ValueError:
        return None


def rellena_huecos(filas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """*La serie con los dias que faltan puestos a `None`, **por producto**.*

    *Cada `(producto_id, fuente)` tiene su propio rango: un producto que empezo a verse el dia 10 no tiene por que
    tener un hueco desde el 7.* *Se rellena **entre su primer y su ultimo dia**, no antes ni despues: fuera de su
    rango no estaba en el catalogo, y eso no es un hueco.*

    *Los dias que ya venian se devuelven **sin tocar** -- mismo orden, mismos valores --, y los nuevos entran en su
    sitio por fecha.*
    """
    if not filas:
        return []

    # *Una entrada por (producto, cadena).*
    por_producto: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for f in filas:
        clave = (str(f.get("producto_id")), str(f.get("fuente")))
        por_producto.setdefault(clave, []).append(f)

    salida: list[dict[str, Any]] = []
    for (producto_id, fuente), suyas in por_producto.items():
        suyas = sorted(suyas, key=lambda f: str(f.get("fecha")))
        dias = {str(f.get("fecha"))[:10] for f in suyas}
        con_dia = [d for d in (_dia(f.get("fecha")) for f in suyas) if d is not None]
        if not con_dia:
            # *Sin fechas legibles no hay rango: se devuelven tal cual, **sin perder ninguna**.*
            salida.extend(suyas)
            continue

        primera, ultima = min(con_dia), max(con_dia)
        # *Los que ya estaban, por fecha.*
        # *Las que no tienen fecha legible se apartan y se devuelven al final: no se tiran.*
        sin_fecha = [f for f in suyas if _dia(f.get("fecha")) is None]
        por_fecha = {str(f.get("fecha"))[:10]: f for f in suyas}
        d = primera
        while d <= ultima:
            clave = d.isoformat()
            if clave in por_fecha:
                salida.append(por_fecha[clave])
            elif clave not in dias:
                # *** El hueco: la fecha esta, el precio no. ***
                # *Se copia la forma de la fila vecina para no inventar campos, y se pone el precio a `None`.*
                modelo = suyas[0]
                salida.append(
                    {**modelo, "producto_id": producto_id, "fuente": fuente, "fecha": clave,
                     "precio_unidad_cent": None}
                )
            d += timedelta(days=1)
            salida.extend(sin_fecha)

    return sorted(salida, key=lambda f: (str(f.get("producto_id")), str(f.get("fecha"))))
