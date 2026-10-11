"""G12, punto 221: **la transferencia de una receta a la lista, idempotente por operacion.**

G12 lo pide asi: *«Receta→lista: previa de cantidades, consolidacion compatible, distincion
g/ml/unidades y envases enteros necesarios. **Repetir la misma transferencia no duplica; otra
semana/operacion legitima si.** Descontar despensa solo si esta modelada y la persona lo elige, **no
por haber comprado antes**.»*

**Y la frase que decide el diseno es la de en medio.** *«Repetir no duplica» y «otra semana si» no se
pueden cumplir a la vez mirando las lineas de la lista* -- *dos semanas distintas con los mismos
ingredientes producen lineas identicas, y no hay forma de distinguirlas por su contenido*. **Asi que
la identidad tiene que ser de la operacion, no del resultado**, y eso es una clave: **receta +
version + semana**.

**La clave la calcula el servidor, y la semana tambien.** *Si la mandara el cliente, dos pestañas con
fechas distintas escribirian dos veces, y el 223 de G12 y el 227 de G13 prohben confiar en lo que
manda el cliente como identidad o como propietario.* **La fecha de hoy es del servidor**, como en
`cesta._fecha_de_hoy`.

**Y el dueño se comprueba aqui, no en la pantalla.** *La puerta es `recetas._de_quien`, que ya existe
y ya lanza: «una receta necesita dueno: el recetario es personal».*
"""
from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from core import previa_compra


@dataclass(frozen=True)
class Operacion:
    """**La identidad del traspaso.** *Repetirla es la misma operacion; otra semana es otra.*"""
    propietario: str
    receta_id: int
    version: int
    semana: str          # el lunes de la semana, en ISO. *La calcula el servidor.*

    @property
    def clave(self) -> str:
        return f"{self.propietario}|{self.receta_id}|{self.version}|{self.semana}"


def semana_de(hoy: date | None = None) -> str:
    """**El lunes de la semana de `hoy`**, en ISO. *La semana empieza el lunes, que es cuando se
    compra para los dias siguientes.*

    *Se calcula y no se recibe*: si el cliente manda la fecha, dos pestañas abiertas con dias
    distintos --o una con la fecha cambiada a mano-- escriben dos veces la misma compra.
    """
    hoy = hoy or date.today()
    return (hoy - timedelta(days=hoy.weekday())).isoformat()


def _migra(con: sqlite3.Connection) -> None:
    """La tabla de operaciones. *Con la clave unica: es ella la que impide el duplicado.*"""
    con.execute("""
        CREATE TABLE IF NOT EXISTS traspaso (
            clave       TEXT PRIMARY KEY,
            propietario TEXT NOT NULL,
            receta_id   INTEGER NOT NULL,
            version     INTEGER NOT NULL,
            semana      TEXT NOT NULL,
            lista_id    TEXT,
            lineas      INTEGER NOT NULL,
            creado      TEXT NOT NULL
        )""")
    con.commit()


def pasar_a_lista(
    con: sqlite3.Connection,
    propietario: str,
    receta_id: int,
    *,
    version: int | None = None,
    hoy: date | None = None,
    insertar: Callable[[list[previa_compra.LineaDeCompra]], int] | None = None,
) -> dict:
    """**Pasa la receta a la lista, y repetir no duplica.**

    Devuelve `{lineas, ya_estaba, semana, version, clave}`.

    **El orden importa**: primero se comprueba si la operacion ya se hizo -- *y si se hizo, se
    devuelve lo que paso sin volver a escribir* --; y solo despues se escribe. *Con `insertar=None`
    -- que es como se prueba -- se calcula la previa y se registra la operacion **sin escribir en
    ninguna lista**, que es lo que permite probar la idempotencia sin tocar datos de nadie.*
    """
    from core import recetas

    if not propietario:
        raise ValueError("un traspaso necesita dueno: el recetario es personal")
    _migra(con)

    # **La version se resuelve aqui si no viene**: la ultima de la receta. *Y si la receta no es del
    # que pregunta, `_de_quien` devuelve `None` y esto no sigue.*
    if recetas._de_quien(con, propietario, receta_id) is None:
        raise ValueError(f"no hay receta {receta_id} de quien pregunta")

    hallada = recetas.leer(con, propietario, receta_id, version=version)
    if hallada is None:
        raise ValueError(f"no hay receta {receta_id} en la version {version}")
    numero = int(hallada["version"])

    op = Operacion(propietario=propietario, receta_id=receta_id, version=numero,
                   semana=semana_de(hoy))

    # **Y aqui esta el 221**: si la operacion ya consta, no se vuelve a escribir.
    ya = con.execute("SELECT lineas, lista_id FROM traspaso WHERE clave = ?", (op.clave,)).fetchone()
    if ya is not None:
        return {"lineas": int(ya[0]), "ya_estaba": True, "semana": op.semana,
                "version": numero, "clave": op.clave, "lista_id": ya[1]}

    previa = previa_compra.previa_de_compra(hallada["ingredientes"] or [])
    lista_id = None
    if insertar is not None and previa.lineas:
        lista_id = str(insertar(previa.lineas))

    con.execute("""INSERT INTO traspaso
                     (clave, propietario, receta_id, version, semana, lista_id, lineas, creado)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (op.clave, propietario, receta_id, numero, op.semana, lista_id,
                 len(previa.lineas), date.today().isoformat()))
    con.commit()
    return {"lineas": len(previa.lineas), "ya_estaba": False, "semana": op.semana,
            "version": numero, "clave": op.clave, "lista_id": lista_id,
            "sin_cantidad": previa.sin_cantidad, "sin_consolidar": previa.sin_consolidar}
