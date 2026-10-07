"""S08, superficie de API: el recetario, para que la pantalla tenga de donde leer.

**Por que los manejadores no usan `Depends` para la conexion.** Porque asi se pueden **llamar
directamente** desde una prueba, sin levantar un servidor ni un cliente HTTP. El proyecto ya prueba asi
lo demas, y una funcion que solo se puede probar arrancando la aplicacion entera es una funcion que se
prueba menos.

**Que expone, y con que reglas:**

  - `GET /api/recetas` -- el recetario, sin el contenido entero.
  - `POST /api/recetas` -- una receta nueva, con su version 1.
  - `GET /api/recetas/{id}?version=N` -- la receta; sin `version`, la ultima. **Con `version`, esa**,
    que es lo que permite releer lo de la semana pasada igual que estaba.
  - `PUT /api/recetas/{id}` -- cambiar: **crea version nueva**, no reescribe. Lo que no se manda se
    hereda copiado.
  - `POST /api/recetas/{id}/archivar` -- sale del recetario sin borrarse.
  - `GET /api/recetas/plan?desde&hasta` y `POST /api/recetas/plan` -- el plan semanal, que **fija la
    version** al ponerlo.

**La puerta de la base se puede cambiar** (`ruta_base`). No es un adorno de testabilidad: es lo que
permite que las pruebas usen su propio fichero y no toquen el de verdad.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core import recetas

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
def listar(incluir_archivadas: bool = False) -> dict:
    con = _con()
    try:
        return {"recetas": recetas.listar(con, incluir_archivadas=incluir_archivadas)}
    finally:
        con.close()


@rutas.post("", status_code=201)
def crear(datos: RecetaIn) -> dict:
    con = _con()
    try:
        rid = recetas.crear(con, datos.nombre, raciones=datos.raciones,
                            preparacion=datos.preparacion,
                            ingredientes=_como_filas(datos.ingredientes),
                            minutos=datos.minutos, etiquetas=datos.etiquetas)
        return {"id": rid, "receta": recetas.leer(con, rid)}
    finally:
        con.close()


@rutas.get("/plan")
def plan(desde: str = Query(...), hasta: str = Query(...)) -> dict:
    """Va **antes** que `/{receta_id}`: si no, FastAPI leeria "plan" como un identificador."""
    con = _con()
    try:
        return {"plan": recetas.plan(con, desde, hasta)}
    finally:
        con.close()


@rutas.post("/plan", status_code=201)
def planificar(datos: PlanIn) -> dict:
    con = _con()
    try:
        recetas.planificar(con, datos.fecha, datos.receta_id, comensales=datos.comensales,
                           version=datos.version)
        return {"plan": recetas.plan(con, datos.fecha, datos.fecha)}
    except ValueError as fallo:
        raise HTTPException(status_code=400, detail=str(fallo)) from fallo
    finally:
        con.close()


@rutas.get("/{receta_id}")
def leer(receta_id: int, version: int | None = None) -> dict:
    con = _con()
    try:
        hallada = recetas.leer(con, receta_id, version=version)
    finally:
        con.close()
    if hallada is None:
        raise HTTPException(status_code=404, detail=f"no hay receta {receta_id}"
                            + (f" en la version {version}" if version else ""))
    return hallada


@rutas.put("/{receta_id}")
def cambiar(receta_id: int, datos: CambioIn) -> dict:
    con = _con()
    try:
        numero = recetas.actualizar(con, receta_id, nombre=datos.nombre, raciones=datos.raciones,
                                    preparacion=datos.preparacion,
                                    ingredientes=_como_filas(datos.ingredientes),
                                    minutos=datos.minutos, etiquetas=datos.etiquetas)
        return {"version": numero, "receta": recetas.leer(con, receta_id, version=numero)}
    except ValueError as fallo:
        raise HTTPException(status_code=404, detail=str(fallo)) from fallo
    finally:
        con.close()


@rutas.post("/{receta_id}/archivar")
def archivar(receta_id: int, archivada: bool = True) -> dict:
    con = _con()
    try:
        if recetas.leer(con, receta_id) is None:
            raise HTTPException(status_code=404, detail=f"no hay receta {receta_id}")
        recetas.archivar(con, receta_id, archivada=archivada)
        return {"id": receta_id, "archivada": archivada}
    finally:
        con.close()
