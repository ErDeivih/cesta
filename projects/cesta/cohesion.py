"""La cohesion de cada grupo contra su medoide. La segunda red del encargo, medida.

Es el punto 5 del encargo de Claude: *"La cohesion contra el medoide como SEGUNDA RED,
con su papel claro y sin sustituir a la invariante: la invariante caza lo que se funde
**entre** cadenas, el medoide lo que se funde **dentro** de un grupo legitimo. **El
umbral se calibra contra el banco de pares, no se elige a ojo.**"*

Que mide esto, y por que asi
---------------------------
Para cada grupo con dos o mas miembros:

    medoide    el miembro con la **media de parecido mas alta** al resto. Es el centro
               del grupo, medido con los datos y no elegido.
    cohesion   el parecido **mas bajo** del medoide con cualquier otro miembro. O sea:
               lo lejos que esta el miembro que peor encaja. Un grupo donde todos se
               parecen mucho tiene cohesion alta; un grupo con un intruso tiene
               cohesion baja, y el intruso es el que la baja.

Se usa el minimo y no la media a proposito: la media esconde al intruso cuando el grupo
es grande, que es justo cuando mas falta hace verlo.

**Esto no decide nada por si solo.** El encargo pide el umbral calibrado contra el banco
de pares (`projects/cesta/banco_de_pares.py`, 1.809 pares ciertos por codigo de barras
en dos cadenas), y eso es lo que imprime `--banco`: el parecido de los pares que **ya
sabemos** que son el mismo producto. **Un umbral por encima de ese suelo rompe pares
ciertos**, y eso es el error caro: quita comparaciones que si valian.

Lo que se midio el 23 de septiembre de 2026, y es la respuesta al punto 5
------------------------------------------------------------------------
Medido sobre el gold de ese dia (52.417 productos, 8.756 grupos con dos o mas miembros
con vector), con `--banco`:

    grupos cuya cohesion es menor que:      0,50 -> 0      0,60 ->  84      0,70 -> 1.244
                                            0,75 -> 2.865  0,85 -> 5.925    0,95 -> 8.456
    pares CIERTOS: 1.791      minimo 0,511   p1 0,617   p5 0,725   mediana 0,874

**El suelo del banco (0,511) cae dentro del mismo tramo que los grupos peores del
catalogo**, asi que no hay umbral que separe: o no corta nada (por debajo de 0,51), o se
lleva por delante pares ciertos y grupos legitimos a la vez.

Y mirando los grupos peores uno a uno se ve por que. Los cuatro de cohesion mas baja, con
nombres de verdad:

    grupo 24370   0,500   'Boniato'                          (aldi)
                          'Boniato Carrefour 1 kg aprox'     (carrefour)
    grupo 7096    0,513   'CILLIT BANG Multiusos 750ml'      (alcampo)
                          'Multisusos cocina Bosque Verde'   (mercadona)
    grupo 2750    0,537   'TENDILLA Torrezno frito lima-chili'  (alcampo)
                          'Rolls picantes sabor chili-lima'     (aldi)
    grupo 2393    0,719   'VICTORIA Cerveza pack 6 x 20 cl'     (alcampo)
                          'Cerveza Estrella Galicia pack 24 latas'  (carrefour)
                          'Cerveza Estrella Galicia pack 6 x 20 cl' (dia)

Los dos primeros son **comparaciones legitimas y valiosas** -- el mismo producto con marca
blanca y con marca nacional, y con el nombre escrito de dos maneras --; el tercero mezcla
dos aperitivos distintos, y el cuarto dos cervezas distintas. Los cuatro tienen el mismo
parecido. **Un umbral no puede distinguir "mismo producto, otro nombre" de "otro
producto"**: el texto es justo lo que cambia cuando la comparacion vale mas. Y el grupo
2393, que si esta mal, esta en 0,719 -- por encima del p5 del banco (0,725 casi lo toca)
--, asi que para cazarlo habria que cortar un tercio del catalogo.

Conclusion, dicha como es: **la cohesion contra el medoide sirve para MIRAR, no para
cortar**. Este instrumento se queda para lo primero, y no se pone como guarda en
`agrupar_enlaces`. Lo que separa de verdad en ese grupo de cervezas no es la cohesion: es
que son **formatos distintos** (6 x 20 cl frente a 24 x 33 cl), o sea la dimension del
pack, que se mide aparte en `projects/cesta/ejes.py`.

Los vectores son `bge-m3` (1024 dimensiones) y se leen **en SQL**, del cache de
`data/gold/embedding.parquet`: traerlos a Python fue lo que hizo que el canal de
vectores no terminara en 62 minutos (ver `core/embeddings.py`).

    uv run python -m projects.cesta.cohesion
    uv run python -m projects.cesta.cohesion --banco
    uv run python -m projects.cesta.cohesion --peores 10
"""
from __future__ import annotations

import argparse

import duckdb

from core import config

# Los cortes que se miran, de mas exigente a menos. No son el umbral: son la tabla con
# la que se decide, y por eso se imprimen todos.
CORTES = (0.99, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.60, 0.50)


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect()


def _hay_vectores(con: duckdb.DuckDBPyConnection) -> bool:
    camino = config.GOLD / "embedding.parquet"
    if not camino.exists():
        return False
    # Sin los vectores de hoy la medida no vale: el cache es incremental y puede
    # tener solo una parte del catalogo (ver `core.embeddings.calcula`).
    n = con.execute(
        f"SELECT count(*) FROM read_parquet('{camino.as_posix()}')").fetchone()[0]
    return n > 0


def cohesion(con: duckdb.DuckDBPyConnection) -> dict:
    """Cohesion de cada grupo, con su medoide y el miembro que peor encaja."""
    grupos = (config.GOLD / "grupos.parquet").as_posix()
    vectores = (config.GOLD / "embedding.parquet").as_posix()
    filas = con.execute(f"""
        WITH mios AS (
            SELECT grupo_id, fuente || ':' || id_fuente AS pid, nombre
              FROM read_parquet('{grupos}')
             WHERE grupo_id IS NOT NULL),
        miembros AS (
            SELECT m.grupo_id, m.pid, m.nombre, v.e
              FROM mios m JOIN read_parquet('{vectores}') v ON v.producto_id = m.pid),
        pares AS (
            SELECT a.grupo_id, a.pid AS uno, b.pid AS otro,
                   list_cosine_similarity(a.e, b.e) AS s
              FROM miembros a JOIN miembros b
                ON a.grupo_id = b.grupo_id AND a.pid < b.pid),
        media AS (
            SELECT grupo_id, uno AS pid, avg(s) AS media FROM pares GROUP BY grupo_id, uno
            UNION ALL
            SELECT grupo_id, otro, avg(s) FROM pares GROUP BY grupo_id, otro),
        medoide AS (
            SELECT grupo_id, arg_max(pid, media) AS pid FROM media GROUP BY grupo_id),
        coh AS (
            SELECT p.grupo_id,
                   min(p.s) FILTER (WHERE p.uno = m.pid OR p.otro = m.pid) AS cohesion
              FROM pares p JOIN medoide m USING (grupo_id)
             GROUP BY p.grupo_id)
        SELECT c.grupo_id, m.pid AS medoide, c.cohesion, t.n
          FROM coh c
          JOIN medoide m USING (grupo_id)
          JOIN (SELECT grupo_id, count(*) AS n FROM mios GROUP BY grupo_id) t
            USING (grupo_id)
    """).fetchall()
    return {int(f[0]): {"medoide": f[1], "cohesion": float(f[2]), "miembros": int(f[3])}
            for f in filas}


def banco(con: duckdb.DuckDBPyConnection) -> dict:
    """El parecido de los pares **ciertos**: el suelo que ningun umbral puede pisar."""
    grupos = (config.GOLD / "grupos.parquet").as_posix()
    vectores = (config.GOLD / "embedding.parquet").as_posix()
    filas = con.execute(f"""
        WITH ciertos AS (
            SELECT a.ean, a.fuente || ':' || a.id_fuente AS uno,
                   b.fuente || ':' || b.id_fuente AS otro
              FROM read_parquet('{grupos}') a JOIN read_parquet('{grupos}') b
                ON a.ean = b.ean AND a.fuente < b.fuente
             WHERE a.ean IS NOT NULL AND a.ean <> ''),
        v AS (SELECT producto_id, e FROM read_parquet('{vectores}'))
        SELECT count(*) AS pares,
               min(list_cosine_similarity(u.e, d.e)) AS minimo,
               quantile_cont(list_cosine_similarity(u.e, d.e), 0.01) AS p1,
               quantile_cont(list_cosine_similarity(u.e, d.e), 0.05) AS p5,
               median(list_cosine_similarity(u.e, d.e)) AS mediana
          FROM ciertos c JOIN v u ON u.producto_id = c.uno
                        JOIN v d ON d.producto_id = c.otro
    """).fetchone()
    return {"pares": int(filas[0]), "minimo": float(filas[1]), "p1": float(filas[2]),
            "p5": float(filas[3]), "mediana": float(filas[4])}


def resumen(con: duckdb.DuckDBPyConnection, peores: int = 0) -> dict:
    coh = cohesion(con)
    por_corte = {c: sum(1 for d in coh.values() if d["cohesion"] < c) for c in CORTES}
    return {
        "grupos_con_medoide": len(coh),
        "por_corte": por_corte,
        "peores": sorted(
            ((d["cohesion"], g, d) for g, d in coh.items()))[:peores] if peores else [],
    }


def _nombres(con: duckdb.DuckDBPyConnection, grupo_ids: list[int]) -> dict[int, list[str]]:
    """Los nombres de los miembros de cada grupo, para poder leer el numero."""
    if not grupo_ids:
        return {}
    grupos = (config.GOLD / "grupos.parquet").as_posix()
    filas = con.execute(f"""
        SELECT grupo_id, fuente, nombre FROM read_parquet('{grupos}')
         WHERE grupo_id IN ({','.join('?' * len(grupo_ids))})
         ORDER BY grupo_id, fuente""", grupo_ids).fetchall()
    salida: dict[int, list[str]] = {}
    for grupo_id, fuente, nombre in filas:
        salida.setdefault(int(grupo_id), []).append(f"{fuente}: {nombre}")
    return salida


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cohesion")
    ap.add_argument("--peores", type=int, default=0)
    ap.add_argument("--banco", action="store_true",
                    help="el suelo de los pares ciertos, que es lo que calibra el umbral")
    a = ap.parse_args(argv)

    con = _con()
    if not _hay_vectores(con):
        print("  no hay vectores en data/gold/embedding.parquet: no se puede medir")
        print("  (se calculan con `core.embeddings.calcula`, incremental)")
        return 0

    r = resumen(con, peores=a.peores)
    print(f"  grupos con dos o mas miembros con vector   {r['grupos_con_medoide']:>7,}")
    print("  grupos cuya cohesion es MENOR que:")
    for corte, n in r["por_corte"].items():
        print(f"      {corte:.2f}                                {n:>7,}")

    if r["peores"]:
        nombres = _nombres(con, [g for _c, g, _d in r["peores"]])
        for coh, grupo_id, d in r["peores"]:
            print(f"\n    peor: grupo {grupo_id} ({d['miembros']} miembros) "
                  f"cohesion {coh:.3f}  medoide {d['medoide']}")
            for nombre in nombres.get(grupo_id, []):
                print(f"          {nombre}")

    if a.banco:
        b = banco(con)
        print()
        print(f"  pares CIERTOS por codigo de barras        {b['pares']:>7,}")
        print(f"      su parecido minimo                    {b['minimo']:>7.3f}"
              f"   <- un umbral por encima de esto rompe pares ciertos")
        print(f"      percentil 1                           {b['p1']:>7.3f}")
        print(f"      percentil 5                           {b['p5']:>7.3f}")
        print(f"      mediana                               {b['mediana']:>7.3f}")
        print()
        print("  Y el suelo del banco cae en el mismo tramo que los grupos peores del")
        print("  catalogo: no hay umbral que separe 'mismo producto, otro nombre' de")
        print("  'otro producto'. Por eso esto mira y no corta (ver el porque arriba).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
