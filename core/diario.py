"""S09: el diario. Lo que se comio, con lo que se sabe y lo que no, y sin confundir las dos cosas.

**Las tres reglas del encargo, y como se cumplen aqui:**

  1. *"Conservara alimentos y recetas versionados."* Cada entrada guarda **de donde sale y con que
     version**: un alimento, con su ficha y su fecha; una receta, con el numero de version. Asi, releer
     el diario de la semana pasada da exactamente lo que se anoto, aunque la receta haya cambiado.
  2. *"Distinguir subtotales conocidos de nutricion completa."* Cada entrada dice **de donde viene su
     dato** -- etiqueta, ficha, estimacion o desconocido -- y el resumen del dia separa dos cosas:
     **lo que se sabe** (la suma de las entradas que traen datos) y **cuantas entradas no traen
     ninguno**. Un dia no esta "completo" porque la suma cuadre: esta completo cuando **todas** las
     entradas traen dato. Y si falta, se dice **cuantas faltan**, no se rellena con un cero.
  3. *"Las compras no se registran como consumo."* Esto no se deja escrito en un comentario: `apunta`
     **rechaza** el tipo `compra` con un error. Comprar no es comer, y un diario que suma lo que se
     compra engaña con numeros que parecen medidos.

**Ausencia no es cero, y por eso hay un estado para cada cosa.** Una entrada sin dato nutricional no
aporta `0 kcal`: aporta **nada**, y el dia lo cuenta como entrada pendiente. Es la misma distincion que
el proyecto ya hace entre "no hay dato" y "el dato es cero" en la cobertura y en las ofertas.

**Privacidad:** fichero local (`data/diario.sqlite`), no sale de la maquina, y el modulo no escribe en
ningun registro lo que alguien come.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime
from math import isfinite
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "data" / "diario.sqlite"

# Los tipos de entrada. **`compra` no esta**, y no es un olvido: es la regla del encargo.
ALIMENTO = "alimento"
RECETA = "receta"
TIPOS = (ALIMENTO, RECETA)

# De donde sale el dato. `desconocido` existe para poder anotar algo que se comio sin saber que era.
ETIQUETA = "etiqueta"
FICHA = "ficha"
ESTIMADO = "estimado"
DESCONOCIDO = "desconocido"
FUENTES = (ETIQUETA, FICHA, ESTIMADO, DESCONOCIDO)

COMIDAS = ("desayuno", "media manana", "comida", "merienda", "cena", "otras")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS entrada (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha     TEXT NOT NULL,
    comida    TEXT NOT NULL,
    tipo      TEXT NOT NULL,
    referencia TEXT,
    version   TEXT,
    cantidad_g REAL,
    unidad    TEXT,
    kcal      REAL,
    proteinas_g REAL,
    grasas_g  REAL,
    hidratos_g REAL,
    fuente_dato TEXT NOT NULL,
    nota      TEXT,
    creada    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS entrada_por_fecha ON entrada (fecha, comida, id);
"""


def conecta(ruta: Path | str | None = None) -> sqlite3.Connection:
    destino = Path(ruta) if ruta else BASE
    destino.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(destino)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con


def apunta(con: sqlite3.Connection, fecha: str, comida: str, *, tipo: str = ALIMENTO,
           referencia: str | None = None, version: str | None = None, cantidad_g: float | None = None,
           kcal: float | None = None, proteinas_g: float | None = None, grasas_g: float | None = None,
           hidratos_g: float | None = None, fuente_dato: str = DESCONOCIDO, nota: str = "",
           ahora: datetime | None = None) -> int:
    """Anota lo que se comio. Devuelve el identificador de la entrada.

    **Rechaza `compra` a proposito.** Comprar no es comer: si una compra entrara aqui, el diario
    sumaria como ingerido algo que quiza ni se ha abierto, y el error no se notaria porque el numero
    seguiria cuadrando por dentro.
    """
    if tipo not in TIPOS:
        if tipo == "compra":
            raise ValueError("una compra no es consumo: no se registra en el diario")
        raise ValueError(f"tipo de entrada desconocido: {tipo}")
    if comida not in COMIDAS:
        raise ValueError(f"comida desconocida: {comida}")
    if fuente_dato not in FUENTES:
        raise ValueError(f"fuente de dato desconocida: {fuente_dato}")
    date.fromisoformat(fecha)
    if tipo == RECETA and version is None:
        raise ValueError("una receta se anota con su version: sin ella no se puede releer")
    if any(v is not None and (not isfinite(v) or v < 0)
           for v in (kcal, cantidad_g, proteinas_g, grasas_g, hidratos_g)):
        raise ValueError("las cantidades y la energia deben ser finitas y no negativas")
    cur = con.execute(
        """INSERT INTO entrada (fecha, comida, tipo, referencia, version, cantidad_g, kcal,
                                proteinas_g, grasas_g, hidratos_g, fuente_dato, nota, creada)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (fecha, comida, tipo, referencia, version, cantidad_g, kcal, proteinas_g, grasas_g,
         hidratos_g, fuente_dato, nota, (ahora or datetime.now()).isoformat(timespec="seconds")))
    con.commit()
    return int(cur.lastrowid)


def borrar(con: sqlite3.Connection, entrada_id: int) -> bool:
    """Quitar una entrada. Anotar de mas es lo mas facil del mundo y hay que poder deshacerlo."""
    cur = con.execute("DELETE FROM entrada WHERE id = ?", (entrada_id,))
    con.commit()
    return cur.rowcount > 0


def _trae_dato(fila: sqlite3.Row) -> bool:
    """Si esa entrada aporta algo al total. **Sin dato no es cero**: es que no se sabe."""
    return fila["kcal"] is not None


def dia(con: sqlite3.Connection, fecha: str) -> dict:
    """El dia entero: las entradas, el subtotal **conocido** y cuantas faltan por saber.

    `completo` conserva el contrato de cobertura energetica de las entradas
    registradas. No certifica que se haya anotado toda la ingesta del dia.
    Cada nutriente tiene cobertura propia, independiente de las calorias.
    """
    filas = con.execute("SELECT * FROM entrada WHERE fecha = ? ORDER BY comida, id",
                        (fecha,)).fetchall()
    entradas = [dict(f) for f in filas]
    con_dato = [f for f in filas if _trae_dato(f)]
    campos = ("kcal", "proteinas_g", "grasas_g", "hidratos_g")
    conocidos = {campo: [f[campo] for f in filas if f[campo] is not None] for campo in campos}
    return {
        "fecha": fecha,
        "entradas": entradas,
        "comidas": {c: [e for e in entradas if e["comida"] == c]
                    for c in COMIDAS if any(e["comida"] == c for e in entradas)},
        "conocido": {
            "entradas": len(con_dato),
            **{campo: round(sum(valores), 1) if valores else None
               for campo, valores in conocidos.items()},
        },
        "cobertura": {campo: {"con_dato": len(valores), "total": len(entradas),
                              "completa": bool(entradas) and len(valores) == len(entradas)}
                      for campo, valores in conocidos.items()},
        # **Lo que no se sabe, contado.** Es la mitad de la respuesta que un total esconde.
        "sin_dato": [e["id"] for e in entradas if not _trae_dato(e)],
        "completo": bool(entradas) and all(_trae_dato(f) for f in filas),
    }


def rango(con: sqlite3.Connection, desde: str, hasta: str) -> list[dict]:
    """Los dias con algo anotado entre dos fechas, para las tendencias."""
    filas = con.execute(
        """SELECT fecha, count(*) AS entradas,
                  sum(CASE WHEN kcal IS NOT NULL THEN 1 ELSE 0 END) AS con_dato,
                  sum(kcal) AS kcal_conocida
             FROM entrada WHERE fecha BETWEEN ? AND ?
            GROUP BY fecha ORDER BY fecha""", (desde, hasta)).fetchall()
    return [{"fecha": f["fecha"], "entradas": f["entradas"], "con_dato": f["con_dato"],
             "kcal_conocida": (round(f["kcal_conocida"], 1)
                               if f["kcal_conocida"] is not None else None),
             "completo": f["con_dato"] == f["entradas"]} for f in filas]
