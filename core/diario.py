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


# Los campos que definen **que** se anoto. La clave dice **que operacion** es; esto dice **que datos**
# lleva. Los dos juntos son lo que distingue un reintento de un choque de claves.
_CAMPOS_DE_LA_OPERACION = ("fecha", "comida", "tipo", "referencia", "version", "cantidad_g", "kcal",
                           "proteinas_g", "grasas_g", "hidratos_g", "fuente_dato", "nota")


def _el_mismo_reintento(previa: tuple, contenido: dict) -> bool:
    """**¿La clave ya usada llevaba estos mismos datos?**

    *`referencia` y `nota` pueden llegar `None` o vacias segun por donde entren, asi que se comparan
    como texto -- `''` y `None` no son un cambio.* Los numeros se comparan como numeros: `100` y
    `100.0` son el mismo dato, y `0` no es lo mismo que `None`, porque *no es cero, es que no se sabe*.
    """
    for posicion, campo in enumerate(_CAMPOS_DE_LA_OPERACION, start=1):
        suyo, mio = previa[posicion], contenido[campo]
        if suyo is None or mio is None:
            if (suyo is None) != (mio is None):
                return False
        elif isinstance(suyo, float) or isinstance(mio, float):
            if float(suyo) != float(mio):
                return False
        elif (suyo or "") != (mio or ""):
            return False
    return True


def _respuesta_del_reintento(previa: tuple, contenido: dict, clave: str) -> int:
    """**La entrada que ya hay -- o el conflicto, dicho.**

    Si es el mismo reintento se devuelve su id, que es lo que hace que un envio repetido no duplique.
    **Pero si la clave se reutilizo con otros datos, devolver la vieja en silencio seria un exito que
    parece guardar otra cosa**: quien lo pidio creeria haber anotado lo suyo y en el diario estaria lo
    de antes. *Se dice, en vez de disimularlo.*
    """
    if _el_mismo_reintento(previa, contenido):
        return int(previa[0])
    raise ValueError(
        f"esa clave de operacion ya se uso con otros datos ({clave!r}): la misma clave es el mismo "
        f"reintento, no una comida nueva con otro contenido")


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
    #
    # *Esto es el camino rapido, no la garantia.* La garantia es el indice unico: ver abajo.
    contenido = {"fecha": fecha, "comida": comida, "tipo": tipo, "referencia": referencia,
                 "version": version, "cantidad_g": cantidad_g, "kcal": kcal,
                 "proteinas_g": proteinas_g, "grasas_g": grasas_g, "hidratos_g": hidratos_g,
                 "fuente_dato": fuente_dato, "nota": nota}
    por_clave = (f"SELECT id, {', '.join(_CAMPOS_DE_LA_OPERACION)} FROM {TABLA} "
                 "WHERE propietario = ? AND clave_operacion = ?")
    if clave_operacion:
        previa = con.execute(por_clave, (propietario, clave_operacion)).fetchone()
        if previa is not None:
            return _respuesta_del_reintento(previa, contenido, clave_operacion)

    # **La clave va DENTRO del INSERT, y el choque lo resuelve el indice.**
    #
    # *Antes se insertaba sin clave y se ponia despues con un `UPDATE`. Entre las dos cosas habia una
    # ventana, y con dos envios a la vez -- que es exactamente lo que hace un reintento desde dos
    # pestanas, o un doble toque con mala cobertura -- **los dos SELECT no veian nada**: ninguno habia
    # escrito todavia. Los dos insertaban su fila, y al poner la clave el indice unico parcial
    # rechazaba al segundo con `UNIQUE constraint failed`. **En vez de deduplicar, fallaba** -- y la
    # fila del que fallaba se quedaba sin clave, que es peor que fallar: una entrada que ya no se
    # puede reconocer como repetida.*
    #
    # **Ahora hay una sola escritura y el choque es la respuesta**: `DO NOTHING` deja pasar a uno, y
    # el que no inserta **lee la del otro y la devuelve**. *`WHERE clave_operacion IS NOT NULL` es
    # obligatorio: el indice es parcial, y el destino del conflicto tiene que decir el mismo predicado
    # que el indice o SQLite no lo reconoce.*
    columnas = ("fecha, comida, tipo, referencia, version, cantidad_g, kcal, proteinas_g, grasas_g, "
                "hidratos_g, fuente_dato, nota, creada, propietario")
    valores: tuple = (fecha, comida, tipo, referencia, version, cantidad_g, kcal, proteinas_g,
                      grasas_g, hidratos_g, fuente_dato, nota,
                      (ahora or datetime.now()).isoformat(timespec="seconds"), propietario)
    if clave_operacion:
        columnas += ", clave_operacion"
        valores += (clave_operacion,)
        choque = (" ON CONFLICT (propietario, clave_operacion) WHERE clave_operacion IS NOT NULL"
                  " DO NOTHING")
    else:
        choque = ""

    cur = con.execute(
        f"INSERT INTO {TABLA} ({columnas}) VALUES ({','.join('?' * len(valores))}){choque}", valores)

    if clave_operacion and cur.rowcount == 0:
        # **Otro la escribio primero, y ya esta confirmada.** Si es el mismo reintento se devuelve su
        # id -- la respuesta tiene que ser la misma que si hubiera llegado el primero --, y si la clave
        # se reutilizo con otros datos se dice, en vez de devolver una entrada que no es la suya.
        suya = con.execute(por_clave, (propietario, clave_operacion)).fetchone()
        if suya is None:                                    # pragma: no cover
            # *No deberia poder pasar: si el indice dijo que estaba, esta.* Se dice tal cual en vez
            # de inventar una entrada nueva, que seria duplicar justo lo que se quiere evitar.
            raise RuntimeError("el indice dijo que la clave estaba, y no esta")
        return _respuesta_del_reintento(suya, contenido, clave_operacion)

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


def resumen(filas: list[sqlite3.Row]) -> dict:
    """El subtotal **conocido** y su cobertura, por nutriente.

    ***Vive aqui y no dentro de `dia` porque lo usan DOS cosas***: el diario, que suma lo **registrado**, y
    la prevision, que sumara lo **planificado**. ***Y tienen que sumar IGUAL***: si cada una tuviera su
    aritmetica, los dos numeros no serian comparables, y la grafica que los pone juntos seria una mentira
    -- la mentira no estaria en los datos, sino en el codigo.

    El subtotal se llama `conocido` y no `total` a proposito. Y `completo` es la cobertura energetica de
    las filas que se le pasen: llamada desde `dia`, no representa toda la ingesta real del dia, porque
    solo cuenta lo que se anoto.
    """
    total = len(filas)
    con_kcal = [f for f in filas if _trae_dato(f)]

    def suma(columna: str) -> float | None:
        valores = [f[columna] for f in filas if f[columna] is not None]
        return round(sum(valores), 1) if valores else None

    return {
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
        # `completo` significa: **todas las filas traen energia**. No significa "esto es todo lo que comi".
        "completo": bool(filas) and all(_trae_dato(f) for f in filas),
    }


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
    return {
        "fecha": fecha,
        "entradas": entradas,
        "comidas": {c: [e for e in entradas if e["comida"] == c]
                    for c in COMIDAS if any(e["comida"] == c for e in entradas)},
        # **El subtotal y su cobertura, de `resumen`**, que es la misma aritmetica que usara la prevision.
        **resumen(filas),
        "sin_dato": [e["id"] for e in entradas if not _trae_dato(e)],
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
