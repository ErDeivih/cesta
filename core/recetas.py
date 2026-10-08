"""Las recetas, guardadas, versionadas **y de quien son**.

**Privacidad, implementada.** Cada receta tiene propietario, y **todas** las operaciones lo exigen:
crear, leer, listar, ver sus versiones, cambiar, archivar, planificar y leer el plan. El propietario
viene de la sesion; este modulo no acepta que se lo dicte el cuerpo de una peticion.

**Versiones y plan heredan el permiso de la receta.** No se guardan permisos aparte: se llega a ellos
por `receta_id` y lo primero es comprobar que la receta es tuya. Dos reglas separadas acabarian
discrepando el dia que alguien toque una.

**Lo historico, sin dueno, queda conservado e inaccesible.** La migracion anade la columna y deja NULL
lo anterior; como toda consulta exige coincidencia, NULL nunca casa. No se le asigna al primero que
entre: eso seria inventarse una propiedad.

**Cada version es autocontenida**: guarda sus raciones, su preparacion y sus ingredientes **copiados**,
para que el diario pueda citar una version y esa version no se mueva nunca.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "data" / "recetas.sqlite"
TABLA = "receta"

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


def _migra(con: sqlite3.Connection) -> None:
    """Anade la columna de propietario **si falta**, sin tocar los datos que ya haya.

    El indice se crea **aqui y no en el esquema**: en una base antigua la columna todavia no existe, y
    un `CREATE INDEX` sobre ella reventaria antes de que este `ALTER TABLE` pudiera anadirla. Es el fallo
    que cazo la prueba de migracion del diario, aplicado ahora desde el principio.
    """
    columnas = {f[1] for f in con.execute(f"PRAGMA table_info({TABLA})").fetchall()}
    if "propietario" not in columnas:
        con.execute(f"ALTER TABLE {TABLA} ADD COLUMN propietario TEXT")
    con.execute("CREATE INDEX IF NOT EXISTS receta_por_dueno ON receta (propietario, archivada, nombre)")
    con.commit()


def conecta(ruta: Path | str | None = None) -> sqlite3.Connection:
    """Abre (y crea si hace falta) el fichero local de recetas."""
    destino = Path(ruta) if ruta else BASE
    destino.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(destino)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    _migra(con)
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
            "producto_id": uno.get("producto_id"),
            "grupo_id": uno.get("grupo_id"),
            "fuente": uno.get("fuente"),
        })
    return json.dumps(limpios, ensure_ascii=False)


def _de_quien(con: sqlite3.Connection, propietario: str, receta_id: int) -> sqlite3.Row | None:
    """La receta **si es de quien pregunta**. Es la puerta de todo lo demas."""
    if not propietario:
        raise ValueError("una receta necesita dueno: el recetario es personal")
    return con.execute("SELECT * FROM receta WHERE id = ? AND propietario = ?",
                       (receta_id, propietario)).fetchone()


def crear(con: sqlite3.Connection, propietario: str, nombre: str, raciones: int = 2,
          preparacion: str = "", ingredientes: list[dict] | None = None, minutos: int | None = None,
          etiquetas: str = "", ahora: datetime | None = None) -> int:
    """Una receta nueva, con su version 1, **de quien la crea**."""
    if not propietario:
        raise ValueError("una receta necesita dueno: el recetario es personal")
    if not nombre.strip():
        raise ValueError("una receta sin nombre no se puede buscar despues")
    if raciones < 1:
        raise ValueError("las raciones son al menos una")
    momento = _ahora(ahora)
    cur = con.execute("INSERT INTO receta (nombre, creada, propietario) VALUES (?, ?, ?)",
                      (nombre.strip(), momento, propietario))
    receta_id = int(cur.lastrowid)
    con.execute(
        """INSERT INTO version (receta_id, numero, raciones, preparacion, minutos, etiquetas,
                                ingredientes, creada)
           VALUES (?, 1, ?, ?, ?, ?, ?, ?)""",
        (receta_id, raciones, preparacion, minutos, etiquetas,
         _ingredientes_para_guardar(ingredientes), momento))
    con.commit()
    return receta_id


def leer(con: sqlite3.Connection, propietario: str, receta_id: int,
         version: int | None = None) -> dict | None:
    """La receta **si es tuya**, con su contenido. Sin version, la ultima; con ella, **esa**."""
    receta = _de_quien(con, propietario, receta_id)
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


def versiones(con: sqlite3.Connection, propietario: str, receta_id: int) -> list[int]:
    """Las versiones de una receta tuya. De una que no lo es, ninguna."""
    if _de_quien(con, propietario, receta_id) is None:
        return []
    return [f[0] for f in con.execute(
        "SELECT numero FROM version WHERE receta_id = ? ORDER BY numero", (receta_id,)).fetchall()]


def actualizar(con: sqlite3.Connection, propietario: str, receta_id: int, *, nombre: str | None = None,
               raciones: int | None = None, preparacion: str | None = None,
               ingredientes: list[dict] | None = None, minutos: int | None = None,
               etiquetas: str | None = None, ahora: datetime | None = None) -> int:
    """Cambiar una receta tuya **crea una version nueva**. Devuelve el numero de la version creada."""
    anterior = leer(con, propietario, receta_id)
    if anterior is None:
        raise ValueError(f"no hay receta {receta_id}")
    if nombre is not None:
        if not nombre.strip():
            raise ValueError("una receta sin nombre no se puede buscar despues")
        con.execute("UPDATE receta SET nombre = ? WHERE id = ? AND propietario = ?",
                    (nombre.strip(), receta_id, propietario))
    siguiente = max(versiones(con, propietario, receta_id), default=0) + 1
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


def listar(con: sqlite3.Connection, propietario: str,
           incluir_archivadas: bool = False) -> list[dict]:
    """El recetario **de quien pregunta**: nombre, ultima version y raciones, sin el contenido entero."""
    sql = """SELECT r.id, r.nombre, r.creada, r.archivada, v.numero, v.raciones, v.minutos,
                    v.etiquetas
               FROM receta r
               JOIN version v ON v.receta_id = r.id
              WHERE v.numero = (SELECT max(numero) FROM version WHERE receta_id = r.id)
                AND r.propietario = ?"""
    if not incluir_archivadas:
        sql += " AND r.archivada = 0"
    return [{"id": f["id"], "nombre": f["nombre"], "creada": f["creada"],
             "archivada": bool(f["archivada"]), "version": f["numero"],
             "raciones": f["raciones"], "minutos": f["minutos"], "etiquetas": f["etiquetas"]}
            for f in con.execute(sql + " ORDER BY r.nombre", (propietario,)).fetchall()]


def archivar(con: sqlite3.Connection, propietario: str, receta_id: int,
             archivada: bool = True) -> bool:
    """Archivar **la tuya**. Archivar no borra: el diario que la cita sigue teniendo que poder leerla."""
    cur = con.execute("UPDATE receta SET archivada = ? WHERE id = ? AND propietario = ?",
                      (1 if archivada else 0, receta_id, propietario))
    con.commit()
    return cur.rowcount > 0


def planificar(con: sqlite3.Connection, propietario: str, fecha: str, receta_id: int,
               comensales: int = 2, version: int | None = None) -> None:
    """Poner **una receta tuya** en un dia. Se fija la version: el plan viejo se relee tal cual."""
    if comensales < 1:
        raise ValueError("los comensales son al menos uno")
    date.fromisoformat(fecha)
    actual = leer(con, propietario, receta_id)
    if actual is None:
        raise ValueError(f"no hay receta {receta_id}")
    con.execute("INSERT OR REPLACE INTO plan (fecha, receta_id, version, comensales) VALUES (?,?,?,?)",
                (fecha, receta_id, version or actual["version"], comensales))
    con.commit()


def plan(con: sqlite3.Connection, propietario: str, desde: str, hasta: str) -> list[dict]:
    """Lo planificado **por ti** entre dos fechas. El JOIN con la receta es lo que aplica el permiso."""
    filas = con.execute(
        """SELECT p.fecha, p.comensales, p.version, r.id, r.nombre
             FROM plan p JOIN receta r ON r.id = p.receta_id
            WHERE p.fecha BETWEEN ? AND ? AND r.propietario = ?
            ORDER BY p.fecha, r.nombre""", (desde, hasta, propietario)).fetchall()
    return [{"fecha": f[0], "comensales": f[1], "version": f[2], "receta_id": f[3],
             "nombre": f[4]} for f in filas]
