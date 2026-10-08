"""La API del diario: **personal, y con la sesion delante de todo**.

Cada endpoint depende de `usuario_actual`, y el propietario que se pasa al almacen sale **solo de la
sesion**: nunca del cuerpo de la peticion. Si saliera del cuerpo, el aislamiento seria decorativo --
bastaria con pedir el diario de otro poniendo su nombre en el JSON --.

Cuando algo no es tuyo se responde **404, no 403**: un 403 confirmaria que ese identificador existe y es
de otra persona, que es informacion que quien pregunta no tiene por que obtener.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core import diario

from .sesion import usuario_actual

rutas = APIRouter(prefix="/api/diario", tags=["diario"])

_ruta_base: Path | None = None


def ruta_base(ruta: Path | str | None = None) -> Path | None:
    """Donde vive el fichero del diario. Se puede fijar para que las pruebas no toquen el de verdad."""
    global _ruta_base
    if ruta is not None:
        _ruta_base = Path(ruta)
    return _ruta_base


def _con():
    return diario.conecta(_ruta_base)


class EntradaIn(BaseModel):
    fecha: str
    comida: str
    tipo: str = diario.ALIMENTO
    referencia: str | None = None
    version: str | None = None
    cantidad_g: float | None = Field(default=None, ge=0)
    kcal: float | None = Field(default=None, ge=0)
    proteinas_g: float | None = Field(default=None, ge=0)
    grasas_g: float | None = Field(default=None, ge=0)
    hidratos_g: float | None = Field(default=None, ge=0)
    fuente_dato: str = diario.DESCONOCIDO
    nota: str = ""


@rutas.get("/rango")
def rango(desde: str = Query(...), hasta: str = Query(...),
          usuario: dict = Depends(usuario_actual)) -> dict:
    """Va **antes** que `/{fecha}`: si no, FastAPI leeria "rango" como una fecha."""
    con = _con()
    try:
        return {"dias": diario.rango(con, usuario["id"], desde, hasta)}
    finally:
        con.close()


@rutas.post("", status_code=201)
def apuntar(datos: EntradaIn, usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        entrada_id = diario.apunta(
            con, usuario["id"], datos.fecha, datos.comida, tipo=datos.tipo,
            referencia=datos.referencia, version=datos.version, cantidad_g=datos.cantidad_g,
            kcal=datos.kcal, proteinas_g=datos.proteinas_g, grasas_g=datos.grasas_g,
            hidratos_g=datos.hidratos_g, fuente_dato=datos.fuente_dato, nota=datos.nota)
        return {"id": entrada_id, "dia": diario.dia(con, usuario["id"], datos.fecha)}
    except ValueError as fallo:
        raise HTTPException(status_code=400, detail=str(fallo)) from fallo
    finally:
        con.close()


@rutas.get("/{fecha}")
def dia(fecha: str, usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        return diario.dia(con, usuario["id"], fecha)
    finally:
        con.close()


@rutas.delete("/entrada/{entrada_id}")
def borrar(entrada_id: int, usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        if not diario.borrar(con, usuario["id"], entrada_id):
            raise HTTPException(status_code=404, detail=f"no hay entrada {entrada_id}")
        return {"borrada": entrada_id}
    finally:
        con.close()
