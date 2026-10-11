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
    # **La clave de la operacion.** El cliente la genera al enviar y la repite si reintenta: un
    # doble clic o una respuesta perdida devuelven **la entrada que ya hay** en vez de crear otra.
    # Dos comidas legitimas llevan claves distintas y se registran las dos.
    clave_operacion: str | None = None


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
        # **La receta se comprueba ANTES de guardarla.** Una version que no existe, o de otra persona, no se
        # anota: se dice que no. Es lo que cierra las referencias inventadas, y el propietario sale de la
        # sesion como en todo lo demas.
        if datos.tipo == diario.RECETA:
            from core import recetas as _recetas

            from .recetas import ruta_base as _ruta_recetario

            if not str(datos.referencia or "").isdigit():
                raise HTTPException(status_code=400,
                                    detail="una receta se anota con el numero de su receta")
            recetario = _recetas.conecta(_ruta_recetario())
            try:
                version = int(datos.version) if str(datos.version or "").isdigit() else None
                hallada = _recetas.leer(recetario, usuario["id"], int(str(datos.referencia)),
                                        version=version)
            finally:
                recetario.close()
            if hallada is None:
                raise HTTPException(
                    status_code=400,
                    detail="esa receta o esa version no existe para ti: no se anota una referencia "
                           "inventada")

        entrada_id = diario.apunta(
            con, usuario["id"], datos.fecha, datos.comida, tipo=datos.tipo,
            referencia=datos.referencia, version=datos.version, cantidad_g=datos.cantidad_g,
            kcal=datos.kcal, proteinas_g=datos.proteinas_g, grasas_g=datos.grasas_g,
            hidratos_g=datos.hidratos_g, fuente_dato=datos.fuente_dato, nota=datos.nota,
            clave_operacion=datos.clave_operacion)
        return {"id": entrada_id, "dia": diario.dia(con, usuario["id"], datos.fecha)}
    except ValueError as fallo:
        raise HTTPException(status_code=400, detail=str(fallo)) from fallo
    finally:
        con.close()


class FichaIn(BaseModel):
    """Una cantidad de un producto, con lo que la ficha dice de el por 100 g.

    Los valores van en el cuerpo porque el cliente ya los tiene de la ficha; **la cuenta la hace el
    servidor**, para que la regla de "lo que no se sabe no es cero" viva en un solo sitio.
    """

    fecha: str
    comida: str
    referencia: str
    gramos: float = Field(gt=0)
    producto: dict
    nota: str = ""


@rutas.post("/desde-ficha", status_code=201)
def desde_ficha(datos: FichaIn, usuario: dict = Depends(usuario_actual)) -> dict:
    """Anota una cantidad de un producto del catalogo, calculada de sus valores por 100 g.

    De los nutrientes que la ficha no traiga **no se anota cero**: se anota `None`, y el dia lo cuenta
    como desconocido. Es lo mismo que hace el diario con una entrada tecleada a mano.
    """
    try:
        entrada = diario.apunta_de_ficha(
            _con(), usuario["id"], datos.fecha, datos.comida, producto=datos.producto,
            gramos=datos.gramos, referencia=datos.referencia, nota=datos.nota)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    return {"entrada": entrada}


@rutas.get("/{fecha}")
def dia(fecha: str, usuario: dict = Depends(usuario_actual)) -> dict:
    con = _con()
    try:
        return _con_procedencia(diario.dia(con, usuario["id"], fecha), usuario["id"])
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


def _con_procedencia(dia: dict, propietario: str) -> dict:
    """Marca cada entrada con **de donde viene**, comprobando el enlace ahora mismo.

    Tres valores, y los tres dicen algo distinto:

      - `manual`: no es una receta; es lo que alguien anoto.
      - `vinculada`: es una receta y **su version existe y es tuya**: el enlace esta vivo.
      - `perdida`: es una receta y esa version **ya no esta**. Entonces se dice, en vez de seguir contando
        como si el enlace valiera.

    Se calcula al leer a proposito. Guardarlo en una columna obligaria a mantenerlo, y una columna que se
    queda vieja dice "vinculada" de algo que ya no lo esta.
    """
    entradas = dia.get("entradas") or []
    recetas_usadas = {str(e.get("referencia")) for e in entradas if e.get("tipo") == "receta"}
    if not recetas_usadas:
        for entrada in entradas:
            entrada["procedencia"] = "manual"
        return dia

    from core import recetas as _recetas

    from .recetas import ruta_base as _ruta_recetario

    con = _recetas.conecta(_ruta_recetario())
    try:
        for entrada in entradas:
            if entrada.get("tipo") != "receta":
                entrada["procedencia"] = "manual"
                continue
            referencia = str(entrada.get("referencia") or "")
            version = entrada.get("version")
            viva = False
            if referencia.isdigit():
                viva = _recetas.leer(con, propietario, int(referencia),
                                     version=int(version) if str(version or "").isdigit() else None)
            entrada["procedencia"] = "vinculada" if viva else "perdida"
    finally:
        con.close()
    return dia
