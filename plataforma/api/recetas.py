"""La API de recetas: **personal, y con la sesion delante de todo**.

Cada endpoint depende de `usuario_actual`, y el propietario sale **solo de la sesion**: nunca del cuerpo
de la peticion. Cuando algo no es tuyo se responde **404 y no 403**, porque un 403 confirmaria que ese
identificador existe y es de otra persona.

Los manejadores no usan `Depends` para la conexion, para poder llamarse directamente desde una prueba;
la sesion, en cambio, **si** es una dependencia, y por eso la prueba del anonimo recibe 401 de verdad.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core import recetas

from .sesion import usuario_actual

rutas = APIRouter(prefix="/api/recetas", tags=["recetas"])

_ruta_base: Path | None = None


def ruta_base(ruta: Path | str | None = None) -> Path | None:
    """Donde vive el fichero de recetas. Se puede fijar para que las pruebas no toquen el de verdad."""
    global _ruta_base
    if ruta is not None:
        _ruta_base = Path(ruta)
    return _ruta_base


def _con():
    return recetas.conecta(_ruta_base)


class IngredienteIn(BaseModel):
    texto: str = Field(min_length=1)
    cantidad: float | None = None
    unidad: str | None = None
    producto_id: str | None = None
    grupo_id: int | None = None
    fuente: str | None = None


class RecetaIn(BaseModel):
    nombre: str = Field(min_length=1)
    raciones: int = Field(default=2, ge=1)
    preparacion: str = ""
    ingredientes: list[IngredienteIn] = []
    minutos: int | None = Field(default=None, ge=0)
    etiquetas: str = ""


class CambioIn(BaseModel):
    """Todo opcional: lo que no se manda se hereda de la version anterior, **copiado**."""
    nombre: str | None = None
    raciones: int | None = Field(default=None, ge=1)
    preparacion: str | None = None
    ingredientes: list[IngredienteIn] | None = None
    minutos: int | None = Field(default=None, ge=0)
    etiquetas: str | None = None


class PlanIn(BaseModel):
    fecha: str
    receta_id: int
    comensales: int = Field(default=2, ge=1)
    version: int | None = None


def _como_filas(ingredientes: list[IngredienteIn] | None) -> list[dict] | None:
    if ingredientes is None:
        return None
    return [i.model_dump(exclude_none=True) for i in ingredientes]


@rutas.get("")
def listar(incluir_archivadas: bool = False,
           usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        return {"recetas": recetas.listar(con, usuario["id"], incluir_archivadas=incluir_archivadas)}
    finally:
        con.close()


@rutas.post("", status_code=201)
def crear(datos: RecetaIn, usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        rid = recetas.crear(con, usuario["id"], datos.nombre, raciones=datos.raciones,
                            preparacion=datos.preparacion,
                            ingredientes=_como_filas(datos.ingredientes),
                            minutos=datos.minutos, etiquetas=datos.etiquetas)
        return {"id": rid, "receta": recetas.leer(con, usuario["id"], rid)}
    finally:
        con.close()


@rutas.get("/plan")
def plan(desde: str = Query(...), hasta: str = Query(...),
         usuario: dict = Depends(usuario_actual)) -> dict:
    """Va **antes** que `/{receta_id}`: si no, FastAPI leeria "plan" como un identificador."""
    con = _con()
    try:
        return {"plan": recetas.plan(con, usuario["id"], desde, hasta)}
    finally:
        con.close()


@rutas.post("/plan", status_code=201)
def planificar(datos: PlanIn, usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        recetas.planificar(con, usuario["id"], datos.fecha, datos.receta_id,
                           comensales=datos.comensales, version=datos.version)
        return {"plan": recetas.plan(con, usuario["id"], datos.fecha, datos.fecha)}
    except ValueError as fallo:
        raise HTTPException(status_code=404, detail=str(fallo)) from fallo
    finally:
        con.close()


@rutas.get("/{receta_id}")
def leer(receta_id: int, version: int | None = None,
         usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        hallada = recetas.leer(con, usuario["id"], receta_id, version=version)
    finally:
        con.close()
    if hallada is None:
        raise HTTPException(status_code=404, detail=f"no hay receta {receta_id}"
                            + (f" en la version {version}" if version else ""))
    return hallada


@rutas.get("/{receta_id}/versiones")
def versiones(receta_id: int, usuario: dict = Depends(usuario_actual)) -> dict:
    """Las versiones de una receta tuya. De una que no lo es, **404 y no una lista vacia**: una lista
    vacia diria "existe y no tiene versiones", que es informacion que no te toca."""
    con = _con()
    try:
        if recetas.leer(con, usuario["id"], receta_id) is None:
            raise HTTPException(status_code=404, detail=f"no hay receta {receta_id}")
        return {"versiones": recetas.versiones(con, usuario["id"], receta_id)}
    finally:
        con.close()


@rutas.put("/{receta_id}")
def cambiar(receta_id: int, datos: CambioIn, usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        numero = recetas.actualizar(con, usuario["id"], receta_id, nombre=datos.nombre,
                                    raciones=datos.raciones, preparacion=datos.preparacion,
                                    ingredientes=_como_filas(datos.ingredientes),
                                    minutos=datos.minutos, etiquetas=datos.etiquetas)
        return {"version": numero,
                "receta": recetas.leer(con, usuario["id"], receta_id, version=numero)}
    except ValueError as fallo:
        raise HTTPException(status_code=404, detail=str(fallo)) from fallo
    finally:
        con.close()


@rutas.post("/{receta_id}/archivar")
def archivar(receta_id: int, archivada: bool = True,
             usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        if not recetas.archivar(con, usuario["id"], receta_id, archivada=archivada):
            raise HTTPException(status_code=404, detail=f"no hay receta {receta_id}")
        return {"id": receta_id, "archivada": archivada}
    finally:
        con.close()
