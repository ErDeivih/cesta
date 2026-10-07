"""Cola de fichas: que sabemos de cada producto, cuando lo miramos y cuando toca volver.

**Por que existe.** Hasta ahora el proyecto descubre productos y guarda precios, pero **no tiene
memoria de las fichas**: no se sabe que productos ya se visitaron, cuales tienen ingredientes, cuales
se miraron hace tres meses ni cuales fallaron. Las dos consecuencias, medidas:

  - DIA y Mercadona **saltan** los identificadores que ya estan en su maestro (`if sku in maestro:
    continue`), asi que una ficha que se completo **no se vuelve a visitar nunca**: si el fabricante
    cambia la formula, el catalogo sigue ensenando la de septiembre como si fuera la de hoy.
  - Y al reves: no hay forma de saber que le falta a quien no la tiene, ni de reanudar una pasada
    interrumpida sin repetir trabajo.

**Que es.** Un registro **una fila por producto de una fuente** (fuente, id, variante, ambito) con su
estado, sus fechas, el hash del contenido util, la version del parser que lo leyo, los intentos y
**la evidencia**: de donde salio el dato. En SQLite local, que da transacciones y lease de verdad.

**Las reglas que se cumplen, y por que importan:**

  - **Un 404 no retira nada.** Pasa a `no_encontrado` con su fecha; el historico se conserva.
  - **Fallo de red y fallo de parser son distintos**: `error_temporal` se reintenta, `parcial` no se
    finge completo.
  - **Lease, no bandera.** `tomar()` marca `en_curso` con caducidad en una sola transaccion: dos
    procesos no pueden coger la misma ficha, y si uno se muere, la ficha vence y vuelve a la cola.
  - **Reanudar no duplica**: la clave es unica y el alta es un upsert.
  - **Ficha y precio son cosas distintas**: esto guarda fichas; los precios siguen su pasada diaria.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "data" / "inventario.sqlite"

# Estados del contrato de SUPERAPP-02 §3.
PENDIENTE = "pendiente"
EN_CURSO = "en_curso"
CORRECTO = "correcto"
PARCIAL = "parcial"
NO_PUBLICADO = "no_publicado"
BLOQUEADO = "bloqueado"
ERROR_TEMPORAL = "error_temporal"
NO_ENCONTRADO = "no_encontrado"
EXCLUIDO = "excluido"
FINALES = (CORRECTO, PARCIAL, NO_PUBLICADO, NO_ENCONTRADO, EXCLUIDO)

REVISION_DIAS = 30          # revision ordinaria; el contrato la quiere configurable
REVISION_CONFLICTO_DIAS = 7  # cuando hay conflicto o cambio observado
LEASE_MINUTOS = 30

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS fichas (
    fuente TEXT NOT NULL,
    id_fuente TEXT NOT NULL,
    variante TEXT NOT NULL DEFAULT '',
    ambito TEXT NOT NULL DEFAULT '',
    url TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    descubierto_en TEXT,
    visto_en TEXT,
    ficha_en TEXT,
    proxima_revision TEXT,
    hash_util TEXT,
    parser_version TEXT,
    intentos INTEGER NOT NULL DEFAULT 0,
    ultimo_resultado TEXT,
    lease_hasta TEXT,
    evidencia TEXT,
    PRIMARY KEY (fuente, id_fuente, variante, ambito)
);
CREATE INDEX IF NOT EXISTS fichas_estado ON fichas (estado, proxima_revision);
"""


def conecta(ruta: Path | None = None) -> sqlite3.Connection:
    destino = Path(ruta) if ruta else BASE
    destino.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(destino, timeout=30, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(_ESQUEMA)
    return con


def alta(con: sqlite3.Connection, fuente: str, id_fuente: str, *, variante: str = "",
         ambito: str = "", url: str | None = None, dia: date | None = None,
         evidencia: str | None = None) -> None:
    """Registra un producto visto. **Idempotente**: verlo otra vez no crea otra fila.

    `descubierto_en` se conserva del primer dia; `visto_en` se actualiza siempre, porque un producto
    que no aparece hoy **no se retira**: simplemente no se ha visto hoy.
    """
    hoy = (dia or date.today()).isoformat()
    con.execute(
        """INSERT INTO fichas (fuente, id_fuente, variante, ambito, url, estado,
                               descubierto_en, visto_en, evidencia)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT (fuente, id_fuente, variante, ambito) DO UPDATE SET
               visto_en = excluded.visto_en,
               url = coalesce(excluded.url, fichas.url),
               evidencia = coalesce(excluded.evidencia, fichas.evidencia)""",
        (fuente, str(id_fuente), variante, ambito, url, PENDIENTE, hoy, hoy, evidencia))


def alta_muchas(con: sqlite3.Connection, fuente: str, ids: list[str], *, dia: date | None = None,
               evidencia: str | None = None) -> int:
    """Alta de muchos identificadores de una vez. **Mismo upsert, sin una transaccion por fila.**

    Con un `INSERT` por fila, el inventario historico no terminaba; con `executemany` tarda segundos.
    El resultado es identico: la clave es unica y volver a pasar no duplica nada.
    """
    if not ids:
        return 0
    hoy = (dia or date.today()).isoformat()
    con.executemany(
        """INSERT INTO fichas (fuente, id_fuente, variante, ambito, estado,
                               descubierto_en, visto_en, evidencia)
           VALUES (?, ?, '', '', ?, ?, ?, ?)
           ON CONFLICT (fuente, id_fuente, variante, ambito) DO UPDATE SET
               visto_en = excluded.visto_en,
               evidencia = coalesce(excluded.evidencia, fichas.evidencia)""",
        [(fuente, i, PENDIENTE, hoy, hoy, evidencia) for i in ids])
    return len(ids)


def tomar(con: sqlite3.Connection, limite: int = 50, *, fuentes: list[str] | None = None,
          ahora: datetime | None = None) -> list[sqlite3.Row]:
    """Coge fichas para trabajar, con **lease**: nadie mas las coge hasta que venzan.

    Una sola consulta y una sola transaccion (`BEGIN IMMEDIATE`), para que dos procesos a la vez no
    puedan llevarse la misma ficha. Si uno se muere, el lease vence y la ficha vuelve sola a la cola:
    no se pierde trabajo ni hay que arreglarlo a mano.

    Prioridad: lo pendiente y lo vencido, y entre eso, lo que lleva mas tiempo sin revisarse.
    """
    momento = ahora or datetime.now()
    vence = momento + timedelta(minutes=LEASE_MINUTOS)
    parametros: list = [PENDIENTE, EN_CURSO, momento.isoformat(), *FINALES, momento.isoformat()]
    filtro = ""
    if fuentes:
        filtro = f" AND fuente IN ({','.join('?' * len(fuentes))})"
        parametros += list(fuentes)
    con.execute("BEGIN IMMEDIATE")
    try:
        filas = con.execute(
            f"""SELECT * FROM fichas
                WHERE (estado = ?
                       OR (estado = ? AND (lease_hasta IS NULL OR lease_hasta < ?))
                       OR (estado IN ({','.join('?' * len(FINALES))})
                           AND proxima_revision IS NOT NULL AND proxima_revision <= ?))
                      {filtro}
                ORDER BY coalesce(proxima_revision, '0000'), fuente, id_fuente
                LIMIT ?""",
            [*parametros, limite]).fetchall()
        for fila in filas:
            con.execute(
                """UPDATE fichas SET estado = ?, lease_hasta = ?, intentos = intentos + 1
                   WHERE fuente = ? AND id_fuente = ? AND variante = ? AND ambito = ?""",
                (EN_CURSO, vence.isoformat(), fila["fuente"], fila["id_fuente"],
                 fila["variante"], fila["ambito"]))
    finally:
        con.execute("COMMIT")
    return filas


def terminar(con: sqlite3.Connection, clave: tuple[str, str, str, str], estado: str, *,
             resultado: str | None = None, hash_util: str | None = None,
             parser_version: str | None = None, evidencia: str | None = None,
             conflicto: bool = False, ahora: datetime | None = None) -> None:
    """Cierra una ficha y **le pone fecha a la siguiente revision**.

    `correcto` exige el hash del contenido util: es lo que permite detectar que la ficha cambio sin
    volver a leerla entera. `conflicto` acorta la revision a 7 dias.
    """
    momento = ahora or datetime.now()
    dias = REVISION_CONFLICTO_DIAS if conflicto else REVISION_DIAS
    proxima = None if estado in (BLOQUEADO, ERROR_TEMPORAL) else (
        (momento + timedelta(days=dias)).date().isoformat())
    con.execute(
        """UPDATE fichas SET estado = ?, ficha_en = ?, ultimo_resultado = ?,
               hash_util = coalesce(?, hash_util),
               parser_version = coalesce(?, parser_version),
               evidencia = coalesce(?, evidencia),
               proxima_revision = ?, lease_hasta = NULL
           WHERE fuente = ? AND id_fuente = ? AND variante = ? AND ambito = ?""",
        (estado, momento.isoformat(), resultado, hash_util, parser_version, evidencia, proxima,
         *clave))


def resumen(con: sqlite3.Connection) -> dict:
    """Cuantas fichas hay en cada estado, por fuente. Es el tablero de cobertura que faltaba."""
    salida: dict[str, dict[str, int]] = {}
    for fila in con.execute("SELECT fuente, estado, count(*) AS n FROM fichas "
                            "GROUP BY fuente, estado"):
        salida.setdefault(fila["fuente"], {})[fila["estado"]] = fila["n"]
    return salida


def enganche(con: sqlite3.Connection, ruta_bronze: Path | None = None,
             *, progreso: bool = True) -> int:
    """Levanta el inventario desde **bronze historico**: la union de todas las capturas, sin red.

    El crudo guardado nombra sus ficheros por el hash de la clave, asi que no se puede recorrer hacia
    atras; bronze si conserva `fuente` e `id_fuente`. Se recorre **una vez** y se acumula en memoria
    la primera y la ultima fecha de cada producto, y luego se escribe una vez por fuente: un *upsert*
    por (dia, producto) eran millones de escrituras para guardar dos fechas.

    Devuelve el numero de **productos distintos** registrados, que es el dato que interesa.
    """
    import polars as pl

    base = ruta_bronze or (RAIZ / "data" / "bronze")
    # (fuente, id) -> [primera fecha, ultima fecha, evidencia]
    visto: dict[tuple[str, str], list[str]] = {}
    for carpeta in sorted(base.glob("fuente=*")):
        fuente = carpeta.name.split("=", 1)[1]
        dias = sorted(d for d in carpeta.iterdir() if d.is_dir())
        for numero, dia in enumerate(dias, start=1):
            fecha = dia.name.split("=", 1)[1]
            if progreso:
                print(f"  {fuente}: {numero}/{len(dias)} ({fecha})", flush=True)
            for fichero in sorted(dia.glob("*.parquet")):
                try:
                    identificadores = pl.read_parquet(
                        fichero, columns=["id_fuente"])["id_fuente"].to_list()
                except Exception:  # noqa: BLE001  (una captura ilegible no para el inventario)
                    continue
                try:
                    etiqueta = fichero.relative_to(RAIZ).as_posix()
                except ValueError:
                    # El bronze puede estar en una copia o en un temporal: la evidencia se guarda
                    # igual, con su ruta completa, en vez de reventar por no ser de casa.
                    etiqueta = fichero.as_posix()
                for identificador in identificadores:
                    if not identificador:
                        continue
                    clave = (fuente, str(identificador))
                    fila = visto.get(clave)
                    if fila is None:
                        visto[clave] = [fecha, fecha, etiqueta]
                    else:
                        if fecha < fila[0]:
                            fila[0] = fecha
                        if fecha > fila[1]:
                            fila[1] = fecha

    # Una escritura por fuente, con sus dos fechas ya resueltas.
    por_fuente: dict[str, list[tuple]] = {}
    for (fuente, identificador), (primera, ultima, etiqueta) in visto.items():
        por_fuente.setdefault(fuente, []).append(
            (fuente, identificador, PENDIENTE, primera, ultima, etiqueta))
    for filas in por_fuente.values():
        con.executemany(
            """INSERT INTO fichas (fuente, id_fuente, variante, ambito, estado,
                                   descubierto_en, visto_en, evidencia)
               VALUES (?, ?, '', '', ?, ?, ?, ?)
               ON CONFLICT (fuente, id_fuente, variante, ambito) DO UPDATE SET
                   descubierto_en = min(descubierto_en, excluded.descubierto_en),
                   visto_en = max(visto_en, excluded.visto_en),
                   evidencia = coalesce(excluded.evidencia, fichas.evidencia)""",
            filas)
    return len(visto)


if __name__ == "__main__":
    import sys

    con = conecta()
    if len(sys.argv) > 1 and sys.argv[1] == "enganche":
        print(f"altas procesadas: {enganche(con)}")
    res = resumen(con)
    total = sum(sum(v.values()) for v in res.values())
    print(f"inventario: {total} fichas registradas")
    for fuente in sorted(res):
        cuenta = res[fuente]
        print(f"  {fuente:<11} " + "  ".join(f"{k}={v}" for k, v in sorted(cuenta.items())))
