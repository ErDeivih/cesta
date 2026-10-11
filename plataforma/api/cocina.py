"""La API del modo cocina: **por donde ibas, y temporizadores que sobreviven a la pantalla**.

Criterio de `F10` (`docs/SUPERAPP-COMPETENCIA-Y-REA.md:105`): *«**Paso actual, ingredientes usados,
temporizadores** y **reanudacion sin conexion cuando sea viable**.»*

**Cada endpoint depende de `usuario_actual`, y el propietario sale solo de la sesion** -- *como en `recetas.py`,
`diario.py` y `despensa.py`.*

## Y lo que hace que este modulo sea distinto de un contador

**`reanudar` no guarda nada y no cambia nada: solo lee y calcula.** *Devuelve el paso, los usados y **los
temporizadores con lo que queda ya calculado*** -- *asi que **se puede llamar sin conexion**, porque **no hay
nada que consultar del servidor**: el reloj lo lleva el aparato.*

**Es la decision de `core/cocina.py` y de la migracion `018`**: *un temporizador **no es una cuenta atras, es una
hora de fin**.* *Lo unico que se guarda es **cuando empezo**.*
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core import cocina as reglas

from . import almacen
from .sesion import usuario_actual

rutas = APIRouter(prefix="/api/cocina", tags=["cocina"])


class PasoIn(BaseModel):
    """*El paso al que se va.* **No se manda el estado: se manda la intencion.**"""

    receta_id: int
    version: int
    paso: int = Field(ge=0)


class UsadoIn(BaseModel):
    receta_id: int
    version: int
    texto: str = Field(min_length=1)


class TemporizadorIn(BaseModel):
    """**Y lo que se manda es la DURACION, no lo que queda.** *El servidor guarda **cuando empezo**.*"""

    receta_id: int
    version: int
    minutos: int = Field(gt=0)
    paso: int | None = None


def _de_la_sesion(usuario: dict, receta_id: int, version: int) -> dict:
    """*La sesion de cocina de esta persona, o 404 -- **404 y no 403**, como en todo lo demas.*"""
    with almacen.cursor() as cur:
        cur.execute("SELECT receta_id, version, paso, usados, temporizadores FROM cocina "
                    "WHERE usuario_id = %s AND receta_id = %s", (usuario["id"], receta_id))
        f = cur.fetchone()
    if f is None:
        raise HTTPException(404, "No hay ninguna cocina empezada para esa receta.")
    return f


def _cocina_de(f, pasos: list[str] | None = None) -> reglas.Cocina:
    """**La sesion de la base, como la entiende el modulo.** *Y de aqui sale todo lo demas.*"""
    c = reglas.Cocina(receta_id=f["receta_id"], version=f["version"], pasos=pasos or [])
    c.paso = f["paso"]
    c.usados = list(f["usados"] or [])
    for t in f["temporizadores"] or []:
        c.temporizadores.append(reglas.Temporizador(
            paso=t["paso"], minutos=t["minutos"],
            # **El instante, tal cual se guardo.** *De aqui sale «cuanto queda», y por eso reanudar funciona.*
            empezo_en=datetime.fromisoformat(t["empezo_en"])))
    return c


def _guarda(usuario: dict, c: reglas.Cocina) -> None:
    """*Escribe el estado.* **Lo que se guarda de un temporizador es `empezo_en`, nunca lo que queda.**"""
    import json

    with almacen.cursor() as cur:
        cur.execute("SELECT 1 FROM cocina WHERE usuario_id = %s AND receta_id = %s",
                    (usuario["id"], c.receta_id))
        existe = cur.fetchone() is not None
        temporizadores = json.dumps(
            [{"paso": t.paso, "minutos": t.minutos, "empezo_en": t.empezo_en.isoformat()}
             for t in c.temporizadores])
        if existe:
            cur.execute("UPDATE cocina SET version = %s, paso = %s, usados = %s, temporizadores = %s, "
                        "actualizado_en = now() WHERE usuario_id = %s AND receta_id = %s",
                        (c.version, c.paso, c.usados, temporizadores, usuario["id"], c.receta_id))
        else:
            cur.execute("INSERT INTO cocina (usuario_id, receta_id, version, paso, usados, temporizadores) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (usuario["id"], c.receta_id, c.version, c.paso, c.usados, temporizadores))


@rutas.post("", status_code=201)
def empieza(datos: PasoIn, usuario: dict = Depends(usuario_actual)) -> dict:
    """**Ponerse a cocinar** -- *y el paso 0 **solo existe cuando se ha empezado**.*"""
    c = reglas.Cocina(receta_id=datos.receta_id, version=datos.version)
    c.empieza()
    _guarda(usuario, c)
    return {"receta_id": c.receta_id, "version": c.version, "paso": c.paso}


@rutas.get("/{receta_id}")
def reanuda(receta_id: int, version: int = Query(...),
            usuario: dict = Depends(usuario_actual)) -> dict:
    """**Volver a la cocina.** *Y **esto es lo que funciona sin conexion**: no guarda nada y no cambia nada --
    **solo lee y calcula**, asi que el tiempo no se ha perdido porque **nunca se estaba contando**.*
    """
    f = _de_la_sesion(usuario, receta_id, version)
    return _cocina_de(f).reanuda()


@rutas.post("/paso", status_code=200)
def avanza(datos: PasoIn, usuario: dict = Depends(usuario_actual)) -> dict:
    """**Ir a un paso.** *Y si el paso no es de esta receta, **no se inventa**: se guarda lo que se manda, que es
    lo que la pantalla sabe.*"""
    f = _de_la_sesion(usuario, datos.receta_id, datos.version)
    c = _cocina_de(f)
    if datos.paso >= 0:
        c.paso = datos.paso
    _guarda(usuario, c)
    return {"receta_id": c.receta_id, "version": c.version, "paso": c.paso}


@rutas.post("/usado", status_code=200)
def usa(datos: UsadoIn, usuario: dict = Depends(usuario_actual)) -> dict:
    """**Apunta un ingrediente usado.** *El modulo **no lo cuenta dos veces** -- echar la sal en dos pasos no es
    echar el doble.*"""
    f = _de_la_sesion(usuario, datos.receta_id, datos.version)
    c = _cocina_de(f)
    c.usa(datos.texto)
    _guarda(usuario, c)
    return {"receta_id": c.receta_id, "usados": c.usados, "hechos": len(c.usados)}


@rutas.post("/temporizador", status_code=201)
def pon_temporizador(datos: TemporizadorIn, usuario: dict = Depends(usuario_actual)) -> dict:
    """**Poner un temporizador.** *Y lo que se guarda es **cuando empezo** -- *que es lo unico que hace falta para
    poder reanudar.* **El «cuanto queda» se calcula al leer, no se guarda.**"""
    f = _de_la_sesion(usuario, datos.receta_id, datos.version)
    c = _cocina_de(f)
    t = c.pon_temporizador(datos.minutos, ahora=datetime.now(timezone.utc), paso=datos.paso)
    _guarda(usuario, c)
    return {"paso": t.paso, "minutos": t.minutos,
            "empezo_en": t.empezo_en.isoformat(), "acaba_en": t.acaba_en.isoformat()}
