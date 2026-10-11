"""El diario: lo que se comio, con lo que se sabe y lo que no. **Y de quien es.**

**Privacidad, implementada y no prometida.** Cada entrada tiene **propietario**, y **todas** las
operaciones lo exigen: anotar, leer el dia, borrar y el rango. El propietario viene de la sesion; este
modulo no acepta que se lo dicta el cuerpo de una peticion.

**Los registros antiguos, sin dueno, quedan conservados e inaccesibles.** La migracion añade la columna
y deja NULL lo anterior. Como cada consulta exige coincidencia con el propietario, **NULL nunca casa**:
no aparecen, no se pueden cambiar y no se borran, hasta que alguien decida a proposito a quien
pertenecen. No se le asignan al primero que entre: eso seria inventarse una propiedad.

**Ausencia no es cero.** Una entrada sin dato nutricional no aporta 0 kcal: aporta nada, aparece en
`sin_dato` y el dia no esta `completo`. Y los macronutrientes se suman con independencia de si la
entrada publica calorias: 12 g de proteina son 12 g de proteina aunque la energia no se sepa.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "data" / "diario.sqlite"
TABLA = "entrada"

ALIMENTO = "alimento"
RECETA = "receta"
TIPOS = (ALIMENTO, RECETA)

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
    creada    TEXT NOT NULL,
    propietario TEXT,
    clave_operacion TEXT
);
"""


def _migra(con: sqlite3.Connection) -> None:
    """Anade la columna de propietario **si falta**, sin tocar los datos que ya haya.

    Repetirla no hace nada: se pregunta antes por las columnas. `ALTER TABLE ... ADD COLUMN` no reescribe
    la tabla y deja en NULL lo anterior, que es justo lo que se quiere: esos registros no tienen dueno
    conocido y se quedan asi hasta que alguien lo decida.
    """
    columnas = {f[1] for f in con.execute(f"PRAGMA table_info({TABLA})").fetchall()}
    if "propietario" not in columnas:
        con.execute(f"ALTER TABLE {TABLA} ADD COLUMN propietario TEXT")
    if "clave_operacion" not in columnas:
        con.execute(f"ALTER TABLE {TABLA} ADD COLUMN clave_operacion TEXT")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS entrada_por_clave ON entrada "
                "(propietario, clave_operacion) WHERE clave_operacion IS NOT NULL")
    con.execute("CREATE INDEX IF NOT EXISTS entrada_por_dueno ON entrada "
                "(propietario, fecha, comida, id)")
    con.commit()


def conecta(ruta: Path | str | None = None) -> sqlite3.Connection:
    destino = Path(ruta) if ruta else BASE
    destino.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(destino)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    _migra(con)
    return con


def apunta(con: sqlite3.Connection, propietario: str, fecha: str, comida: str, *,
            clave_operacion: str | None = None,
           tipo: str = ALIMENTO, referencia: str | None = None, version: str | None = None,
           cantidad_g: float | None = None, kcal: float | None = None,
           proteinas_g: float | None = None, grasas_g: float | None = None,
           hidratos_g: float | None = None, fuente_dato: str = DESCONOCIDO, nota: str = "",
           ahora: datetime | None = None) -> int:
    """Anota lo que se comio **para quien lo anota**.

    **Rechaza `compra` a proposito.** Comprar no es comer: si una compra entrara aqui, el diario sumaria
    como ingerido algo que quiza ni se ha abierto.
    """
    if not propietario:
        raise ValueError("una entrada necesita dueno: el diario es personal")
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
    for valor in (kcal, cantidad_g, proteinas_g, grasas_g, hidratos_g):
        if valor is None:
            continue
        if valor != valor or valor in (float("inf"), float("-inf")):
            raise ValueError("ni las cantidades ni la energia pueden ser no finitas")
        if valor < 0:
            raise ValueError("ni las cantidades ni la energia pueden ser negativas")

    # **Si esa operacion ya se hizo, se devuelve la entrada que hay.** No se busca por nombre, fecha
    # ni nutrientes -- eso prohibiria dos meriendas iguales --, sino por **la clave que manda quien
    # envia**, que es la unica que distingue un reintento de una comida nueva.
    if clave_operacion:
        previa = con.execute(
            f"SELECT id FROM {TABLA} WHERE propietario = ? AND clave_operacion = ?",
            (propietario, clave_operacion)).fetchone()
        if previa is not None:
            return int(previa[0])

    cur = con.execute(
        """INSERT INTO entrada (fecha, comida, tipo, referencia, version, cantidad_g, kcal,
                                proteinas_g, grasas_g, hidratos_g, fuente_dato, nota, creada,
                                propietario)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (fecha, comida, tipo, referencia, version, cantidad_g, kcal, proteinas_g, grasas_g,
         hidratos_g, fuente_dato, nota, (ahora or datetime.now()).isoformat(timespec="seconds"),
         propietario))
    if clave_operacion:
        con.execute(f"UPDATE {TABLA} SET clave_operacion = ? WHERE id = ?",
                    (clave_operacion, cur.lastrowid))
    con.commit()
    return int(cur.lastrowid)


# Los nutrientes que la ficha trae por 100 g, y el campo del diario al que van. El orden es el de una
# etiqueta de verdad, y la clave es la de `ProductoSuelto` en el cliente.
NUTRIENTES_DE_FICHA = (
    ("kcal_100g", "kcal"),
    ("proteinas_100g", "proteinas_g"),
    ("grasas_100g", "grasas_g"),
    ("hidratos_100g", "hidratos_g"),
)


def de_ficha(producto: dict, gramos: float) -> dict:
    """Los nutrientes de una cantidad, a partir de los valores por 100 g del producto.

    **Se calcula nutriente a nutriente, no en bloque.** Si el producto trae kilocalorias pero no proteinas,
    la entrada lleva las kilocalorias y deja las proteinas en `None`: es lo que sabe. Rellenar con ceros
    seria afirmar que no lleva proteina, y eso no lo sabemos.

    De una cantidad negativa o no finita no se calcula nada: son las mismas reglas que `apunta` comprueba,
    y aqui se paran antes.
    """
    if gramos is None or gramos != gramos or gramos in (float("inf"), float("-inf")) or gramos < 0:
        raise ValueError("los gramos tienen que ser un numero finito y no negativo")
    valores = {}
    for campo_100g, campo_diario in NUTRIENTES_DE_FICHA:
        por_100 = producto.get(campo_100g)
        if por_100 is None or por_100 != por_100 or por_100 < 0:
            valores[campo_diario] = None        # no es cero: es que no lo sabemos
        else:
            valores[campo_diario] = round(float(por_100) * gramos / 100, 1)
    if all(v is None for v in valores.values()):
        raise ValueError("el producto no trae ningun nutriente: no hay nada que anotar")
    return valores


def apunta_de_ficha(con: sqlite3.Connection, propietario: str, fecha: str, comida: str, *,
                    producto: dict, gramos: float, referencia: str,
                    nota: str = "", ahora: datetime | None = None) -> int:
    """Anota lo que se comio de un producto del catalogo, con lo que la ficha sabe de el.

    La fuente es `ficha`, que ya estaba en el vocabulario: lo que se anota **no se ha leido de una
    etiqueta a mano**, viene de los valores por 100 g del producto -- los de la cadena o los de Open Food
    Facts. La `nota` deja dicho sobre cuantos gramos se ha calculado, para poder releerlo.
    """
    valores = de_ficha(producto, gramos)
    return apunta(con, propietario, fecha, comida, referencia=referencia, cantidad_g=gramos,
                  fuente_dato=FICHA, ahora=ahora,
                  nota=(nota or f"{gramos:g} g, calculado de los valores por 100 g").strip(), **valores)


def borrar(con: sqlite3.Connection, propietario: str, entrada_id: int) -> bool:
    """Quitar una entrada **solo si es tuya**. Si no lo es, no se borra y se dice que no estaba."""
    cur = con.execute("DELETE FROM entrada WHERE id = ? AND propietario = ?",
                      (entrada_id, propietario))
    con.commit()
    return cur.rowcount > 0


def _trae_dato(fila: sqlite3.Row) -> bool:
    """Si esa entrada aporta energia al total. **Sin dato no es cero**: es que no se sabe."""
    return fila["kcal"] is not None


def _cobertura(filas: list[sqlite3.Row], columna: str, total: int) -> dict:
    """Cuantas entradas traen ESE nutriente, de cuantas hay. La cobertura es por nutriente."""
    con_dato = sum(1 for f in filas if f[columna] is not None)
    return {"con_dato": con_dato, "total": total, "completa": con_dato == total and total > 0}


def dia(con: sqlite3.Connection, propietario: str, fecha: str) -> dict:
    """El dia entero **de quien pregunta**: entradas, subtotal conocido y lo que no se sabe.

    El subtotal se llama `conocido` y no `total` a proposito. Y `completo` es la cobertura energetica de
    las entradas **registradas**: no representa toda la ingesta real del dia, porque solo cuenta lo que
    se anoto.
    """
    filas = con.execute(
        "SELECT * FROM entrada WHERE fecha = ? AND propietario = ? ORDER BY comida, id",
        (fecha, propietario)).fetchall()
    entradas = [dict(f) for f in filas]
    total = len(filas)
    con_kcal = [f for f in filas if _trae_dato(f)]

    def suma(columna: str) -> float | None:
        valores = [f[columna] for f in filas if f[columna] is not None]
        return round(sum(valores), 1) if valores else None

    return {
        "fecha": fecha,
        "entradas": entradas,
        "comidas": {c: [e for e in entradas if e["comida"] == c]
                    for c in COMIDAS if any(e["comida"] == c for e in entradas)},
        "conocido": {
            "entradas": len(con_kcal),
            "kcal": round(sum(f["kcal"] for f in con_kcal), 1) if con_kcal else None,
            "proteinas_g": suma("proteinas_g"),
            "grasas_g": suma("grasas_g"),
            "hidratos_g": suma("hidratos_g"),
        },
        # **La cobertura, por nutriente.** Sin esto, una entrada con proteina y sin energia perderia su
        # proteina en el subtotal, o peor: se leeria como que el dia esta cubierto.
        "cobertura": {n: _cobertura(filas, c, total) for n, c in
                      (("kcal", "kcal"), ("proteinas_g", "proteinas_g"),
                       ("grasas_g", "grasas_g"), ("hidratos_g", "hidratos_g"))},
        "sin_dato": [e["id"] for e in entradas if not _trae_dato(e)],
        # `completo` se conserva por compatibilidad, y significa: **todas las entradas registradas
        # traen energia**. No significa "esto es todo lo que comi".
        "completo": bool(entradas) and all(_trae_dato(f) for f in filas),
    }


def rango(con: sqlite3.Connection, propietario: str, desde: str, hasta: str) -> list[dict]:
    """Los dias con algo anotado **tuyo**, entre dos fechas. La energia desconocida va como null."""
    filas = con.execute(
        """SELECT fecha, count(*) AS entradas,
                  sum(CASE WHEN kcal IS NOT NULL THEN 1 ELSE 0 END) AS con_dato,
                  sum(CASE WHEN kcal IS NOT NULL THEN kcal ELSE 0 END) AS kcal_conocida,
                  sum(CASE WHEN kcal IS NULL THEN 1 ELSE 0 END) AS sin_dato
             FROM entrada WHERE fecha BETWEEN ? AND ? AND propietario = ?
            GROUP BY fecha ORDER BY fecha""", (desde, hasta, propietario)).fetchall()
    return [{"fecha": f["fecha"], "entradas": f["entradas"], "con_dato": f["con_dato"],
             # Si ninguna entrada del dia trae energia, el dia NO tiene cero: no tiene dato.
             "kcal_conocida": round(f["kcal_conocida"], 1) if f["con_dato"] else None,
             "sin_dato": f["sin_dato"],
             "completo": f["con_dato"] == f["entradas"] and f["entradas"] > 0} for f in filas]
