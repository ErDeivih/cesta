"""S09, superficie de API: el diario, para que la pantalla de Calorias tenga de donde leer.

**Las reglas del encargo, traducidas a respuestas HTTP**, que es donde se pueden cumplir de verdad:

  - **Una compra no se registra como consumo**: responde 400 con su motivo. No es una validacion de
    formulario, es la regla escrita en el codigo.
  - **Una receta se anota con su version**: sin ella, releer el diario de la semana pasada no seria
    posible, asi que se rechaza.
  - **El dia devuelve el subtotal `conocido` y las entradas `sin_dato` por separado**, para que la
    pantalla pueda decir "esto es lo que se sabe" en vez de enseñar un total que parece completo.

**Privacidad:** la base es local y este modulo no registra en ningun sitio lo que alguien come.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core import diario

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
def rango(desde: str = Query(...), hasta: str = Query(...)) -> dict:
    """Va **antes** que `/{fecha}`: si no, FastAPI leeria "rango" como una fecha."""
    con = _con()
    try:
        return {"dias": diario.rango(con, desde, hasta)}
    finally:
        con.close()


@rutas.post("", status_code=201)
def apuntar(datos: EntradaIn) -> dict:
    con = _con()
    try:
        entrada_id = diario.apunta(
            con, datos.fecha, datos.comida, tipo=datos.tipo, referencia=datos.referencia,
            version=datos.version, cantidad_g=datos.cantidad_g, kcal=datos.kcal,
            proteinas_g=datos.proteinas_g, grasas_g=datos.grasas_g,
            hidratos_g=datos.hidratos_g, fuente_dato=datos.fuente_dato, nota=datos.nota)
        return {"id": entrada_id, "dia": diario.dia(con, datos.fecha)}
    except ValueError as fallo:
        # 400 y no 500: lo que ha fallado es lo que se ha pedido, y el motivo se devuelve entero para
        # que la pantalla pueda explicarlo (una compra no es consumo, o falta la version de la receta).
        raise HTTPException(status_code=400, detail=str(fallo)) from fallo
    finally:
        con.close()


@rutas.get("/{fecha}")
def dia(fecha: str) -> dict:
    con = _con()
    try:
        return diario.dia(con, fecha)
    finally:
        con.close()


@rutas.delete("/entrada/{entrada_id}")
def borrar(entrada_id: int) -> dict:
    con = _con()
    try:
        if not diario.borrar(con, entrada_id):
            raise HTTPException(status_code=404, detail=f"no hay entrada {entrada_id}")
        return {"borrada": entrada_id}
    finally:
        con.close()
