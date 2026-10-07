"""S08: las recetas, guardadas y versionadas. La base que Recetas y Calorias comparten.

**Por que versionado y no "editar".** El encargo lo pide para el diario -- *"conservara alimentos y
recetas versionados"* -- y la razon es de sentido comun: si una receta se puede reescribir, el dia que
alguien cambio la cantidad de azucar **cambia lo que comiste el mes pasado**. Con versiones, cada
version es **autocontenida**: guarda sus raciones, su preparacion y sus ingredientes copiados, no una
referencia a los de ahora. El diario cita una version y esa version ya no se mueve.

**Que se guarda, y por que asi:**

  - **La receta** es la identidad (el nombre, cuando nacio, si esta archivada).
  - **La version** es el contenido (raciones, preparacion, minutos, etiquetas, ingredientes). Se lee
    siempre por version, y "la ultima" es una consulta, no un campo que haya que ir manteniendo.
  - **Los ingredientes** se guardan como JSON dentro de la version, y llevan texto y cantidad propias
    porque una receta se escribe antes de saber en que cadena se comprara. Cuando se enlacen a un
    producto, se guardara el enlace **y** el texto: si el catalogo cambia, la receta sigue diciendo lo
    que decia.
  - **El plan** es una fecha, una receta, una version y cuantos comen. Fijar la version permite que el
    plan de la semana pasada se pueda releer tal cual.

**Privacidad, que es requisito y no adorno:** esto vive en un fichero local (`data/recetas.sqlite`),
no sale de la maquina, y el modulo no escribe en ningun registro el contenido de una receta. Nada de
esto viaja a ningun servicio.

**Lo que NO hace todavia, y se dice:** no hay pantalla propia -- eso es la mitad visible de S08 -- ni
puente con la lista de la compra, ni diario de consumo. Lo que hay es el almacenamiento, con sus
pruebas, que es lo que las tres cosas necesitan debajo.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "data" / "recetas.sqlite"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS receta (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT NOT NULL,
    creada    TEXT NOT NULL,
    archivada INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS version (
    receta_id   INTEGER NOT NULL REFERENCES receta(id),
    numero      INTEGER NOT NULL,
    raciones    INTEGER NOT NULL,
    preparacion TEXT NOT NULL DEFAULT '',
    minutos     INTEGER,
    etiquetas   TEXT NOT NULL DEFAULT '',
    ingredientes TEXT NOT NULL DEFAULT '[]',
    creada      TEXT NOT NULL,
    PRIMARY KEY (receta_id, numero)
);
CREATE TABLE IF NOT EXISTS plan (
    fecha      TEXT NOT NULL,
    receta_id  INTEGER NOT NULL REFERENCES receta(id),
    version    INTEGER NOT NULL,
    comensales INTEGER NOT NULL,
    PRIMARY KEY (fecha, receta_id)
);
"""


def conecta(ruta: Path | str | None = None) -> sqlite3.Connection:
    """Abre (y crea si hace falta) el fichero local de recetas."""
    destino = Path(ruta) if ruta else BASE
    destino.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(destino)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con


def _ahora(ahora: datetime | None = None) -> str:
    return (ahora or datetime.now()).isoformat(timespec="seconds")


def _ingredientes_para_guardar(ingredientes: list[dict] | None) -> str:
    limpios = []
    for uno in ingredientes or []:
        if not isinstance(uno, dict) or not str(uno.get("texto", "")).strip():
            raise ValueError("un ingrediente necesita al menos su texto")
        limpios.append({
            "texto": str(uno["texto"]).strip(),
            "cantidad": uno.get("cantidad"),
            "unidad": uno.get("unidad"),
            # El enlace al catalogo es opcional: la receta se escribe antes de saber donde se compra.
            "producto_id": uno.get("producto_id"),
            "grupo_id": uno.get("grupo_id"),
            "fuente": uno.get("fuente"),
        })
    return json.dumps(limpios, ensure_ascii=False)


def crear(con: sqlite3.Connection, nombre: str, raciones: int = 2, preparacion: str = "",
          ingredientes: list[dict] | None = None, minutos: int | None = None,
          etiquetas: str = "", ahora: datetime | None = None) -> int:
    """Una receta nueva, con su version 1. Devuelve su identificador."""
    if not nombre.strip():
        raise ValueError("una receta sin nombre no se puede buscar despues")
    if raciones < 1:
        raise ValueError("las raciones son al menos una")
    momento = _ahora(ahora)
    cur = con.execute("INSERT INTO receta (nombre, creada) VALUES (?, ?)", (nombre.strip(), momento))
    receta_id = int(cur.lastrowid)
    con.execute(
        """INSERT INTO version (receta_id, numero, raciones, preparacion, minutos, etiquetas,
                                ingredientes, creada)
           VALUES (?, 1, ?, ?, ?, ?, ?, ?)""",
        (receta_id, raciones, preparacion, minutos, etiquetas,
         _ingredientes_para_guardar(ingredientes), momento))
    con.commit()
    return receta_id


def leer(con: sqlite3.Connection, receta_id: int, version: int | None = None) -> dict | None:
    """La receta con su contenido. Sin numero de version, la ultima; con el, **esa** version."""
    receta = con.execute("SELECT * FROM receta WHERE id = ?", (receta_id,)).fetchone()
    if receta is None:
        return None
    if version is None:
        fila = con.execute(
            "SELECT * FROM version WHERE receta_id = ? ORDER BY numero DESC LIMIT 1",
            (receta_id,)).fetchone()
    else:
        fila = con.execute("SELECT * FROM version WHERE receta_id = ? AND numero = ?",
                           (receta_id, version)).fetchone()
    if fila is None:
        return None
    return {
        "id": receta["id"], "nombre": receta["nombre"], "creada": receta["creada"],
        "archivada": bool(receta["archivada"]), "version": fila["numero"],
        "raciones": fila["raciones"], "preparacion": fila["preparacion"],
        "minutos": fila["minutos"], "etiquetas": fila["etiquetas"],
        "ingredientes": json.loads(fila["ingredientes"]), "version_creada": fila["creada"],
    }


def versiones(con: sqlite3.Connection, receta_id: int) -> list[int]:
    return [f[0] for f in con.execute(
        "SELECT numero FROM version WHERE receta_id = ? ORDER BY numero", (receta_id,)).fetchall()]


def actualizar(con: sqlite3.Connection, receta_id: int, *, nombre: str | None = None,
               raciones: int | None = None, preparacion: str | None = None,
               ingredientes: list[dict] | None = None, minutos: int | None = None,
               etiquetas: str | None = None, ahora: datetime | None = None) -> int:
    """Cambiar una receta **crea una version nueva**. Devuelve el numero de la version creada.

    Lo que no se dice se hereda de la version anterior, y se **copia**: la version nueva queda
    completa por si misma. Asi, el dia que el diario cite la version 2, la 2 seguira diciendo lo mismo
    aunque manana se cambie la 3.
    """
    anterior = leer(con, receta_id)
    if anterior is None:
        raise ValueError(f"no hay receta {receta_id}")
    if nombre is not None:
        if not nombre.strip():
            raise ValueError("una receta sin nombre no se puede buscar despues")
        con.execute("UPDATE receta SET nombre = ? WHERE id = ?", (nombre.strip(), receta_id))
    siguiente = max(versiones(con, receta_id), default=0) + 1
    con.execute(
        """INSERT INTO version (receta_id, numero, raciones, preparacion, minutos, etiquetas,
                                ingredientes, creada)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (receta_id, siguiente,
         raciones if raciones is not None else anterior["raciones"],
         preparacion if preparacion is not None else anterior["preparacion"],
         minutos if minutos is not None else anterior["minutos"],
         etiquetas if etiquetas is not None else anterior["etiquetas"],
         _ingredientes_para_guardar(ingredientes) if ingredientes is not None
         else json.dumps(anterior["ingredientes"], ensure_ascii=False),
         _ahora(ahora)))
    con.commit()
    return siguiente


def listar(con: sqlite3.Connection, incluir_archivadas: bool = False) -> list[dict]:
    """El recetario: nombre, ultima version y raciones, sin traer el contenido entero."""
    sql = """SELECT r.id, r.nombre, r.creada, r.archivada, v.numero, v.raciones, v.minutos,
                    v.etiquetas
               FROM receta r
               JOIN version v ON v.receta_id = r.id
              WHERE v.numero = (SELECT max(numero) FROM version WHERE receta_id = r.id)"""
    if not incluir_archivadas:
        sql += " AND r.archivada = 0"
    return [{"id": f["id"], "nombre": f["nombre"], "creada": f["creada"],
             "archivada": bool(f["archivada"]), "version": f["numero"],
             "raciones": f["raciones"], "minutos": f["minutos"], "etiquetas": f["etiquetas"]}
            for f in con.execute(sql + " ORDER BY r.nombre").fetchall()]


def archivar(con: sqlite3.Connection, receta_id: int, archivada: bool = True) -> None:
    """Archivar no borra: una receta que se comio sigue existiendo para el diario que la cita."""
    con.execute("UPDATE receta SET archivada = ? WHERE id = ?", (1 if archivada else 0, receta_id))
    con.commit()


def planificar(con: sqlite3.Connection, fecha: str, receta_id: int, comensales: int = 2,
               version: int | None = None) -> None:
    """Poner una receta en un dia. **Se fija la version**: el plan viejo se relee tal cual."""
    if comensales < 1:
        raise ValueError("los comensales son al menos uno")
    date.fromisoformat(fecha)  # una fecha que no es fecha es un error que se ve aqui y no en la pantalla
    actual = leer(con, receta_id)
    if actual is None:
        raise ValueError(f"no hay receta {receta_id}")
    con.execute("INSERT OR REPLACE INTO plan (fecha, receta_id, version, comensales) VALUES (?,?,?,?)",
                (fecha, receta_id, version or actual["version"], comensales))
    con.commit()


def plan(con: sqlite3.Connection, desde: str, hasta: str) -> list[dict]:
    """Lo planificado entre dos fechas, con la receta y la version que se fijo."""
    filas = con.execute(
        """SELECT p.fecha, p.comensales, p.version, r.id, r.nombre
             FROM plan p JOIN receta r ON r.id = p.receta_id
            WHERE p.fecha BETWEEN ? AND ?
            ORDER BY p.fecha, r.nombre""", (desde, hasta)).fetchall()
    return [{"fecha": f[0], "comensales": f[1], "version": f[2], "receta_id": f[3],
             "nombre": f[4]} for f in filas]
