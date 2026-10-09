"""Open Food Facts: la fuente externa que iguala ingredientes y nutricion.

Ninguna cadena da Nutri-Score ni NOVA, y Aldi y Lidl no dan ni ingredientes.
OFF cubre ese hueco para todas por igual.

NO usar la API para uso masivo: limita a 15 req/min (producto) y 10 (busqueda).
Usar el volcado en Parquet, que se regenera cada noche y DuckDB lee directamente:

    https://huggingface.co/datasets/openfoodfacts/product-database
    -> food.parquet

Licencia ODbL: se puede usar, incluso comercialmente, citando la fuente y
compartiendo igual las bases derivadas. Hay que atribuir en la web.
"""
from __future__ import annotations

import contextlib
from pathlib import Path

import duckdb

PARQUET = ("https://huggingface.co/datasets/openfoodfacts/product-database/"
           "resolve/main/food.parquet")
LOCAL = Path(__file__).resolve().parents[1] / "data" / "externo" / "off_es.parquet"
# Copia entera del volcado, cuando leerlo por HTTP no sale bien (ver mas abajo).
VOLCADO = LOCAL.with_name("food.parquet")

# Lo que queremos, y los nombres con los que Open Food Facts lo ha llamado a lo
# largo del tiempo. El volcado cambia de esquema sin avisar: "ecoscore_grade" paso
# a llamarse "environmental_score_grade" y la consulta reventaba entera por una
# columna accesoria. Se pide el primer nombre que exista de verdad y se renombra
# al nuestro, para que lo de aguas abajo no se entere de estos cambios.
CAMPOS = {
    "code": ("code",),
    "product_name": ("product_name",),
    "brands": ("brands",),
    "quantity": ("quantity",),
    "categories_tags": ("categories_tags",),
    "ingredients_text": ("ingredients_text", "ingredients_text_es"),
    "nutriscore_grade": ("nutriscore_grade", "nutrition_grade_fr"),
    "nova_group": ("nova_group",),
    "ecoscore_grade": ("environmental_score_grade", "ecoscore_grade"),
    "image_url": ("image_url",),
    "nutriments": ("nutriments",),
}
# Sin estas no hay nada que cruzar; el resto son un extra.
IMPRESCINDIBLES = ("code",)


def _texto_por_idioma(columna: str, minimo: int = 0) -> str:
    """OFF ya no guarda texto plano: guarda una lista {lang, text} por idioma.

    Sin desenrollarla, `ingredients_text` es un STRUCT y cualquier cuenta sobre
    ella miente: parecia que los 357.698 productos traian ingredientes cuando los
    que los traen de verdad son 51.561. Se coge el espanol, y si no lo hay el
    principal, y si tampoco el primero que diga algo.
    """
    largo = f" AND length(trim(x.text)) > {minimo}" if minimo else \
            " AND length(trim(x.text)) > 0"
    return f"""coalesce(
        list_filter({columna}, x -> x.lang = 'es'{largo})[1].text,
        list_filter({columna}, x -> x.lang = 'main'{largo})[1].text,
        list_filter({columna}, x -> true{largo})[1].text)"""


# 'unknown' y 'not-applicable' NO son un Nutri-Score: son la ausencia de uno.
# Contarlos como dato daba un 99,9% de cobertura donde la real es del 29%.
GRADOS = "('a','b','c','d','e')"


def _columnas_reales(con: duckdb.DuckDBPyConnection, origen: str) -> dict[str, str]:
    """Nombre -> tipo. El tipo importa: OFF convirtio texto plano en listas."""
    filas = con.execute(
        f"DESCRIBE SELECT * FROM read_parquet('{origen}') LIMIT 0").fetchall()
    return {fila[0]: str(fila[1]) for fila in filas}


def _seleccion(disponibles) -> tuple[str, list[str]]:
    """(lista SELECT, campos que no estan). Cada campo se renombra al nuestro."""
    trozos, ausentes = [], []
    for nuestro, candidatos in CAMPOS.items():
        real = next((c for c in candidatos if c in disponibles), None)
        if real is None:
            ausentes.append(nuestro)
            continue
        tipo = disponibles.get(real, "") if isinstance(disponibles, dict) else ""
        if "STRUCT" in tipo.upper() and nuestro in ("ingredients_text",
                                                    "product_name"):
            # listas por idioma: se aplanan al castellano aqui, una sola vez, y
            # no en cada consulta de aguas abajo. Si algun dia vuelven a ser
            # texto plano, este camino no se toma y sigue funcionando.
            minimo = 8 if nuestro == "ingredients_text" else 0
            trozos.append(f'{_texto_por_idioma(real, minimo)} AS {nuestro}')
        elif nuestro == "nutriscore_grade":
            trozos.append(f'CASE WHEN "{real}" IN {GRADOS} THEN "{real}" END '
                          f'AS {nuestro}')
        else:
            trozos.append(real if real == nuestro else f'"{real}" AS {nuestro}')
    faltan = [c for c in IMPRESCINDIBLES if c in ausentes]
    if faltan:
        raise RuntimeError(
            f"el volcado de Open Food Facts ya no trae {', '.join(faltan)}: "
            f"hay que revisar core/off.py contra el esquema nuevo")
    return ", ".join(trozos), ausentes


def _filtro_espana(disponibles) -> str:
    if "countries_tags" in disponibles:
        return "list_contains(countries_tags, 'en:spain')"
    if "countries" in disponibles:
        return "lower(countries) LIKE '%spain%' OR lower(countries) LIKE '%espa%'"
    raise RuntimeError("el volcado no trae pais: no se puede acotar a Espana")


def _ir_despacio(con: duckdb.DuckDBPyConnection) -> None:
    """Menos peticiones a la vez y reintentos con espera.

    Leer un parquet remoto significa cientos de peticiones de rango en paralelo,
    una por trozo de columna. Hugging Face responde 429 a quien no va firmado, y
    la descarga muere a mitad. Con un solo hilo y reintentos con espera creciente
    la cosa suele pasar; si aun asi corta, se baja el fichero entero de una vez.
    """
    for sentencia in ("SET threads TO 1",
                      "SET http_keep_alive=true",
                      "SET http_retries=10",
                      "SET http_retry_wait_ms=3000",
                      "SET http_retry_backoff=2"):
        # Las opciones de red cambian entre versiones de DuckDB; la que no
        # exista se ignora en vez de tumbar la descarga entera.
        with contextlib.suppress(Exception):
            con.execute(sentencia)


def descargar_volcado(destino: Path = VOLCADO) -> Path:
    """Trae el fichero entero, de una sola peticion y reanudable.

    Es mas bruto que leerlo por HTTP a trozos, pero es UNA peticion en vez de
    cientos, que es justo lo que evita el 429. Si se corta a mitad, la siguiente
    vez sigue por donde iba en lugar de empezar de cero.
    """
    import urllib.error
    import urllib.request

    destino.parent.mkdir(parents=True, exist_ok=True)
    hechos = destino.stat().st_size if destino.exists() else 0
    peticion = urllib.request.Request(
        PARQUET, headers={"User-Agent": "cesta/1.0 (proyecto personal)"})
    if hechos:
        peticion.add_header("Range", f"bytes={hechos}-")
        print(f"  reanudando en {hechos / 1e9:.2f} GB")

    try:
        respuesta = urllib.request.urlopen(peticion, timeout=120)
    except urllib.error.HTTPError as exc:
        if exc.code == 416:
            # "Range Not Satisfiable": el fichero ya estaba entero. Pasa al
            # relanzar con --entero cuando la descarga anterior si termino.
            print("  el volcado ya estaba completo; no hay nada que bajar")
            return destino
        raise

    with respuesta:
        parcial = respuesta.status == 206
        total = int(respuesta.headers.get("Content-Length") or 0) + (
            hechos if parcial else 0)
        if hechos and not parcial:
            hechos = 0        # el servidor no admite reanudar: se empieza de nuevo
        print(f"  fichero completo: {total / 1e9:.2f} GB")
        with open(destino, "ab" if hechos else "wb") as fh:
            ultimo = hechos
            while trozo := respuesta.read(8 << 20):
                fh.write(trozo)
                hechos += len(trozo)
                if hechos - ultimo >= 250e6:
                    ultimo = hechos
                    porcentaje = f" ({100 * hechos / total:.0f}%)" if total else ""
                    print(f"  {hechos / 1e9:.2f} GB{porcentaje}", flush=True)
    return destino


def preparar_subconjunto_es(con: duckdb.DuckDBPyConnection | None = None,
                            origen: str | Path | None = None) -> Path:
    """Descarga UNA vez el subconjunto espanol. Unos GB -> pocas decenas de MB.

    Se refresca cuando interese, no a diario: los ingredientes no cambian.
    """
    con = con or duckdb.connect()
    origen = str(origen or (VOLCADO if VOLCADO.exists() else PARQUET))
    # httpfs solo hace falta para leer por HTTP. Pedirlo siempre hacia que
    # filtrar un fichero que ya esta en el disco fallara en cualquier maquina sin
    # acceso al repositorio de extensiones de DuckDB.
    if origen.startswith(("http://", "https://", "s3://")):
        con.execute("INSTALL httpfs; LOAD httpfs;")
        _ir_despacio(con)
    disponibles = _columnas_reales(con, origen)
    campos, ausentes = _seleccion(disponibles)
    if ausentes:
        print(f"  aviso: el volcado ya no trae {', '.join(ausentes)}; "
              f"se sigue sin esos campos")
    LOCAL.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"""
        COPY (
            SELECT {campos}
            FROM read_parquet('{origen}')
            WHERE {_filtro_espana(disponibles)}
        ) TO '{LOCAL}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    return LOCAL


def enriquecer_por_ean(con: duckdb.DuckDBPyConnection, tabla_productos: str) -> None:
    """Cruza por EAN. Cubre Mercadona, DIA y Carrefour de golpe."""
    con.execute(f"""
        CREATE OR REPLACE TABLE producto_enriquecido AS
        SELECT p.*,
               o.ingredients_text        AS off_ingredientes,
               -- **La imagen de OFF no se trae**: las cinco cadenas ya publican la suya
               -- (100 % de cobertura, medido el 8 de octubre), asi que no rellena ningun hueco -- y
               -- era lo unico que rompia esta consulta: el subconjunto espanol no tiene esa columna
               -- y la funcion se caia al ejecutarse. Por eso nadie la llamaba.
               o.nutriscore_grade        AS off_nutriscore,
               o.nova_group              AS off_nova,
               o.ecoscore_grade          AS off_ecoscore,
               CASE WHEN o.code IS NULL THEN NULL ELSE 'externo' END AS proc_nutricion
        FROM {tabla_productos} p
        LEFT JOIN read_parquet('{LOCAL}') o
          -- Los dos lados se normalizan: OFF guarda el codigo como texto y a
          -- veces con ceros por delante, y nosotros los quitamos al limpiar.
          -- Comparar en crudo perdia emparejamientos buenos sin avisar.
          ON ltrim(regexp_replace(o.code, '[^0-9]', '', 'g'), '0')
           = ltrim(regexp_replace(CAST(p.ean AS VARCHAR), '[^0-9]', '', 'g'), '0')
    """)


def candidatos_por_nombre(con: duckdb.DuckDBPyConnection, nombre_limpio: str,
                          marca: str | None = None, limite: int = 5):
    """Para Aldi y Lidl, que no dan EAN: buscar por marca + nombre.

    Devuelve candidatos; la asignacion pasa por el mismo umbral y la misma cola
    de revision que el matching entre cadenas. Nunca se acepta a ciegas.
    """
    filtro = f"AND lower(brands) LIKE '%{marca.lower()}%'" if marca else ""
    return con.execute(f"""
        SELECT code, product_name, brands, quantity, nutriscore_grade,
               jaro_winkler_similarity(lower(product_name), ?) AS score
        FROM read_parquet('{LOCAL}')
        WHERE product_name IS NOT NULL {filtro}
        ORDER BY score DESC
        LIMIT {limite}
    """, [nombre_limpio]).fetchall()


if __name__ == "__main__":
    # Un solo comando para traerse el volcado espanol:
    #     uv run python -m core.off
    #
    # Se descarga UNA vez y se refresca cuando interese, no a diario: los
    # ingredientes y el Nutri-Score de un producto no cambian de un dia para otro.
    # Ojo con la conexion: el fichero de origen ocupa varios GB y, aunque DuckDB
    # solo se trae las columnas que se le piden, la primera pasada tarda.
    import sys
    import time

    # --entero: ir directo al plan B, sin intentar antes la lectura por trozos.
    # Cuando ya sabes que tu conexion no la pasa, esperar al fallo es tiempo
    # tirado.
    entero = "--entero" in sys.argv

    print("descargando el subconjunto espanol de Open Food Facts...")
    print("  (varios minutos; el resultado se queda en data/externo/off_es.parquet)")
    t0 = time.time()
    try:
        if entero:
            raise RuntimeError("--entero")
        destino = preparar_subconjunto_es()
    except Exception as exc:  # noqa: BLE001
        # Hugging Face limita a quien lee el parquet a trozos sin firmar, y ese
        # limite llega de varias formas: HTTPException con un 429, o directamente
        # UnicodeDecodeError, porque DuckDB intenta leer en UTF-8 el mensaje de
        # error del servidor, que no viene en UTF-8, y revienta al contarlo. Da
        # igual cual sea: si la lectura remota falla, se baja el fichero entero.
        # Es una peticion en vez de cientos, ocupa disco, y disco es lo que sobra.
        if not entero:
            print(f"  la lectura por trozos no ha podido ser ({type(exc).__name__})")
        print("  se baja el volcado entero de una vez y se filtra aqui")
        descargar_volcado()
        destino = preparar_subconjunto_es(origen=VOLCADO)
    con = duckdb.connect()
    filas = con.execute(
        f"SELECT count(*) FROM read_parquet('{destino}')").fetchone()[0]
    megas = destino.stat().st_size / 1e6
    print(f"listo en {time.time() - t0:.0f}s: {filas} productos espanoles, "
          f"{megas:.0f} MB")
    # count() cuenta lo que no es nulo, y en OFF "unknown" no es nulo. Contarlo
    # daba un 99,9% de cobertura donde la real es del 29%: cada cuenta lleva su
    # condicion de "esto es un dato de verdad".
    cuentas = (("nutriscore_grade", "Nutri-Score",
                f"nutriscore_grade IN {GRADOS}"),
               ("nova_group", "NOVA", "nova_group IS NOT NULL"),
               ("ingredients_text", "ingredientes",
                "length(trim(ingredients_text)) > 8"))
    for _columna, etiqueta, condicion in cuentas:
        try:
            n = con.execute(f"SELECT count(*) FROM read_parquet('{destino}') "
                            f"WHERE {condicion}").fetchone()[0]
            print(f"  con {etiqueta}: {n} ({100 * n / filas:.0f}%)")
        except Exception:  # noqa: BLE001
            print(f"  sin {etiqueta}: el volcado ya no trae esa columna")
    if VOLCADO.exists():
        print(f"  ({VOLCADO.name} ocupa {VOLCADO.stat().st_size / 1e9:.1f} GB y ya "
              f"no hace falta: se puede borrar, o dejar para el proximo refresco)")
    print("Fuente: Open Food Facts, licencia ODbL. Hay que citarla en la web.")
