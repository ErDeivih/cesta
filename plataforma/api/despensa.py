"""La API de la despensa: **lo que hay en casa, declarado -- y nada que lo deduzca de una compra**.

Criterio de `F11` (`docs/SUPERAPP-COMPETENCIA-Y-REA.md:108`): *«**Existencias declaradas**, ubicacion/caducidad
**opcional**; **compra no acredita consumo ni stock restante**.»*

**Cada endpoint depende de `usuario_actual`, y el propietario sale **solo de la sesion**.**
*Como en `recetas.py` y en `diario.py`: **nunca del cuerpo de la peticion**.* *Y cuando algo no es tuyo se responde
**404 y no 403**, porque un 403 confirmaria que ese identificador existe y es de otra persona.*

## Y lo que **no** hay, que es la mitad de lo que este modulo dice

**No hay ninguna ruta que sume una compra a la despensa.** *No es un olvido: **es la regla del criterio, y esta
en el camino** -- *si la ruta no existe, **no se puede llamar**.* **Es la misma forma que el `raise` de
`diario.py:154`** (*una receta sin version no entra*) **y que el `rechaza compra` de `diario.py:140`**
(*«comprar no es comer»*).

**Y la logica esta aparte**, en `core/despensa.py`, con sus 9 pruebas y los cuatro casos de la aceptacion: *esta
capa solo lee y escribe filas, y **no decide nada**.*
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core import despensa as reglas

from . import almacen
from .sesion import usuario_actual

rutas = APIRouter(prefix="/api/despensa", tags=["despensa"])


class ExistenciaIn(BaseModel):
    """**Lo que manda el cliente al declarar.** *El propietario **no** va aqui: sale de la sesion.*"""

    texto: str = Field(min_length=1)
    #: *`None` es **«no se sabe cuanto»** -- y **no es un cero**.* *Ver la migracion `017`.*
    cantidad: float | None = None
    unidad: str = ""
    donde: str = ""
    caduca: str = ""


class ConsumoIn(BaseModel):
    """**Lo que se gasta.** *Y nada mas: **no hay campo de «de donde viene»*** -- *una compra no entra por aqui.*"""

    texto: str = Field(min_length=1)
    cantidad: float = Field(gt=0)
    unidad: str = ""


def _fila(f) -> dict:
    """*Una fila de la tabla, como la pantalla la necesita.*"""
    return {
        "texto": f["texto"],
        # **`None` viaja como `None`**: *que es «no se sabe», y **convertirlo a `0` seria afirmar que no queda
        # nada** -- la decision de la migracion `017`, respetada hasta la pantalla.*
        "cantidad": f["cantidad"],
        "unidad": f["unidad"],
        "donde": f["donde"],
        "caduca": f["caduca"],
        "se_sabe": f["cantidad"] is not None,
    }


@rutas.get("")
def lo_que_hay(usuario: dict = Depends(usuario_actual)) -> dict:
    """**Lo que hay en casa.** *Lo de esta persona, y solo lo suyo.*"""
    with almacen.cursor() as cur:
        cur.execute("SELECT texto, cantidad, unidad, donde, caduca FROM despensa "
                    "WHERE usuario_id = %s ORDER BY texto", (usuario["id"],))
        existencias = [_fila(f) for f in cur.fetchall()]
    return {"existencias": existencias,
            # **Y se dice cuantas no se sabe cuanto.** *Es el caso «stock desconocido» de la aceptacion, y
            # contarlo es lo que permite enseñarlo en vez de dejar que parezca un cero.*
            "sin_saber_cuanto": sum(1 for e in existencias if not e["se_sabe"])}


@rutas.post("", status_code=201)
def declara(datos: ExistenciaIn, usuario: dict = Depends(usuario_actual)) -> dict:
    """**Declarar lo que hay.** *Y **sobrescribe**, porque declarar es decir lo que hay **ahora*** -- *no sumar a
    lo que habia.* **Es la diferencia entre «tengo 2 kg de harina» y «he comprado 2 kg mas»**, y solo la primera
    es una despensa.
    """
    texto = datos.texto.strip()
    with almacen.cursor() as cur:
        cur.execute(
            "INSERT INTO despensa (usuario_id, texto, cantidad, unidad, donde, caduca, actualizado_en) "
            "VALUES (%s, %s, %s, %s, %s, %s, now()) "
            "ON CONFLICT (usuario_id, texto) DO UPDATE SET "
            "  cantidad = EXCLUDED.cantidad, unidad = EXCLUDED.unidad, "
            "  donde = EXCLUDED.donde, caduca = EXCLUDED.caduca, actualizado_en = now()",
            (usuario["id"], texto, datos.cantidad, datos.unidad.strip().lower(),
             datos.donde, datos.caduca))
    return {"texto": texto, "cantidad": datos.cantidad, "unidad": datos.unidad.strip().lower()}


@rutas.post("/consumir", status_code=200)
def consume(datos: ConsumoIn, usuario: dict = Depends(usuario_actual)) -> dict:
    """**Descontar lo que se gasta.** *El caso «consumo parcial» de la aceptacion.*

    **Y la cuenta la hace `core.despensa`**, no esta capa: *aqui solo se lee, se aplica la regla y se escribe el
    resultado.* **Cuando la regla dice que no se puede** -- *no esta declarado, no se sabe cuanto, o las unidades
    no se pueden convertir* --, **se devuelve el motivo y la existencia se queda como estaba**; *no se resta a
    ciegas ni se inventa un numero.*
    """
    with almacen.cursor() as cur:
        cur.execute("SELECT texto, cantidad, unidad, donde, caduca FROM despensa "
                    "WHERE usuario_id = %s AND texto = %s", (usuario["id"], datos.texto.strip()))
        f = cur.fetchone()
        if f is None:
            raise HTTPException(404, "Eso no esta en la despensa.")

        # **La regla, aplicada sobre una despensa de una sola linea.** *El modulo esta probado con sus cuatro
        # casos; aqui se usa, no se reimplementa.*
        mia = reglas.Despensa()
        mia.declara(f["texto"], f["cantidad"], f["unidad"], f["donde"], f["caduca"])
        queda, motivo = mia.consume(f["texto"], datos.cantidad, datos.unidad)

        if queda is not None and queda.cantidad == 0.0 and motivo == "se acabo":
            # *Se acabo: **se borra la linea**, no se deja un cero -- que afirmaria que hay «cero kg».*
            cur.execute("DELETE FROM despensa WHERE usuario_id = %s AND texto = %s",
                        (usuario["id"], f["texto"]))
        elif queda is not None:
            # **`None` se escribe como `None`**: *es «no se sabe», y es una respuesta valida.*
            cur.execute("UPDATE despensa SET cantidad = %s, unidad = %s, actualizado_en = now() "
                        "WHERE usuario_id = %s AND texto = %s",
                        (queda.cantidad, queda.unidad, usuario["id"], f["texto"]))

    return {"texto": f["texto"], "motivo": motivo,
            "cantidad": queda.cantidad if queda is not None else None,
            "unidad": queda.unidad if queda is not None else ""}
