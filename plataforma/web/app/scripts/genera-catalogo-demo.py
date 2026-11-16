#!/usr/bin/env python3
"""Genera el catálogo real que lleva dentro la demo publicada.

*** POR QUÉ EXISTE ESTE FICHERO. ***

Hasta el 16/11/2026 la demo llevaba `datos.json` con **120 filas capturadas de tres
búsquedas de ejemplo** («leche entera», «papel de cocina», «atún en aceite»). Servía
para enseñar la pantalla, no para usarla: quien buscaba «arroz», «pollo» o «huevos»
—lo que se compra cualquier semana— recibía «Nada con …». Está medido en
`INFORMES/FALLO-DEMO.md`.

Esto no inventa un catálogo: **selecciona grupos reales de gold** (la captura del
15/11/2026), con sus precios, su unidad, su supermercado y su imagen, y escribe
`src/demo/catalogo.json` para que la compilación `build:demo` los incruste.

La selección es determinista y se puede repetir:

    cd plataforma/web/app
    python scripts/genera-catalogo-demo.py

Reglas de la selección, y por qué:

- **Solo grupos con dos cadenas o más.** La demo existe para comparar; un grupo de una
  sola cadena no tiene comparación y ocuparía el sitio de uno que sí.
- **Primero lo que se compra**: una lista de términos de uso diario (arroz, pollo,
  huevos, leche, pan, tomate, aceite…). De cada término se elige el grupo con más
  cadenas y el nombre más corto, y se exige que la sección encaje (los huevos de la
  sección de huevos, no un flan).
- **Después, surtido por pasillos**, con cupos, para que la demo no sea veinte
  variedades de leche y nada de limpieza.
- **Nada de alcohol, mascotas, bebé ni parafarmacia**: no es lo que enseña la demo y
  alarga el catálogo sin aportar a la comparación.
- **Una sola oferta por cadena y grupo** (la más barata por unidad): es lo que enseña
  el panel «Ver ofertas por supermercado», y dos filas de la misma cadena parecen un
  duplicado.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
GOLD = RAIZ / "data" / "gold" / "v20261115-184138" / "grupos.parquet"
SALIDA = Path(__file__).resolve().parents[1] / "src" / "demo" / "catalogo.json"
FECHA = "2026-11-15"
MAXIMO = 100

# *Los pasillos que entran, y cuántos productos aporta cada uno al surtido. La suma de
# cupos es mayor que MAXIMO a propósito: los términos de uso diario ya cubren parte, y
# el relleno para cuando se acaban los candidatos de un pasillo.*
CUPOS = {
    "despensa": 24,
    "lacteos-huevos": 16,
    "carniceria": 9,
    "pescaderia": 7,
    "frutas-verduras": 11,
    "panaderia": 9,
    "desayuno-dulces": 8,
    "bebidas": 5,
    "droguería-limpieza": 6,
    "congelados": 3,
    "aperitivos": 2,
}
ORDEN_SECCIONES = list(CUPOS)

# *Lo que se compra: (sección, término). El término se busca en el nombre normalizado.*
DIARIOS = [
    ("despensa", "arroz"),
    ("despensa", "pasta"),
    ("despensa", "aceite de oliva"),
    ("despensa", "atun"),
    ("despensa", "garbanzo"),
    ("despensa", "lenteja"),
    ("despensa", "harina"),
    ("despensa", "azucar"),
    ("despensa", "sal"),
    ("despensa", "tomate frito"),
    ("despensa", "conserva"),
    ("lacteos-huevos", "leche entera"),
    ("lacteos-huevos", "leche semidesnatada"),
    ("lacteos-huevos", "huevo"),
    ("lacteos-huevos", "yogur"),
    ("lacteos-huevos", "queso"),
    ("lacteos-huevos", "mantequilla"),
    ("carniceria", "pollo"),
    ("carniceria", "jamon"),
    ("carniceria", "salchicha"),
    ("carniceria", "cerdo"),
    ("carniceria", "ternera"),
    ("pescaderia", "salmon"),
    ("pescaderia", "merluza"),
    ("pescaderia", "atun"),
    ("pescaderia", "gamba"),
    ("frutas-verduras", "manzana"),
    ("frutas-verduras", "platano"),
    ("frutas-verduras", "patata"),
    ("frutas-verduras", "tomate"),
    ("frutas-verduras", "cebolla"),
    ("frutas-verduras", "zanahoria"),
    ("frutas-verduras", "naranja"),
    ("panaderia", "pan de molde"),
    ("panaderia", "barra de pan"),
    ("panaderia", "pan rallado"),
    ("desayuno-dulces", "galleta"),
    ("desayuno-dulces", "chocolate"),
    ("desayuno-dulces", "cafe"),
    ("desayuno-dulces", "cereal"),
    ("bebidas", "agua"),
    ("bebidas", "zumo"),
    ("bebidas", "cerveza"),
    ("droguería-limpieza", "detergente"),
    ("droguería-limpieza", "papel"),
    ("droguería-limpieza", "limpiador"),
    ("congelados", "congelado"),
    ("aperitivos", "patatas fritas"),
]

# *Los términos que necesitan una regla más fina que «contiene». «Huevo» a secas
# encontraba el flan de huevo (que tiene más cadenas que los huevos), y una demo de la
# compra sin huevos no vale. La regla pide la palabra entera, y el plural puntúa más.*
REGEX = {
    "huevo": r"\bhuevos?\b",
    "pan de molde": r"\bpan de molde\b",
    "barra de pan": r"\bbarra de pan\b",
}

# *Grupos que tienen que estar sí o sí, aunque no ganen por número de cadenas. Los
# huevos ecológicos de Alcampo son el único grupo de huevos con dos cadenas en la
# captura del 15/11; sin ellos, «huevos» no encuentra nada.*
IMPRESCINDIBLES = [4373]

# *Secciones que no entran aunque tengan grupos comparables: no son la compra de la
# semana y llenan el catálogo de cosas que nadie busca en una demo de la cesta.*
FUERA = {"mascotas", "bebe", "parafarmacia", "higiene-belleza", "hogar", "ecologico", "promociones"}


def norm(texto: str) -> str:
    """Minúsculas sin tildes: la misma regla que el buscador de la demo."""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto).lower()) if unicodedata.category(c) != "Mn"
    )


def main() -> None:
    # *La consola de Windows abre en cp1252 y este guion imprime flechas y acentos: sin
    # esto, el catálogo se escribe bien y el guion termina con un UnicodeEncodeError que
    # parece un fallo de los datos.*
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if not GOLD.exists():
        raise SystemExit(f"No está el gold: {GOLD}")

    df = pd.read_parquet(GOLD)
    df = df[
        df.grupo_id.notna()
        & df.precio_cent.notna()
        & (df.precio_cent > 0)
        & df.precio_unidad_cent.notna()
        & (df.precio_unidad_cent > 0)
        & df.imagen.notna()
        & df.nombre.notna()
        & df.unidad_canon.isin(["kg", "l", "ud", "m"])
        & df.seccion.isin(list(CUPOS))
        & ~df.seccion.isin(FUERA)
        & ~df.es_alcohol.fillna(False)
    ].copy()
    df["nombre_norm"] = df.nombre.map(norm)

    # *** UNA OFERTA POR CADENA: la más barata por unidad. *** *
    df = df.sort_values(["grupo_id", "precio_unidad_cent"])
    ofertas = (
        df.drop_duplicates(subset=["grupo_id", "fuente"], keep="first")
        .sort_values(["grupo_id", "precio_unidad_cent"])
        .groupby("grupo_id")
        .head(6)
    )

    meta = df.groupby("grupo_id").agg(
        nombre=("nombre", "first"),
        seccion=("seccion", "first"),
        unidad=("unidad_canon", "first"),
        cadenas=("fuente", "nunique"),
    )
    meta = meta[meta.cadenas >= 2]
    candidatos = set(meta.index)
    filas = {gid: grupo for gid, grupo in ofertas.groupby("grupo_id") if gid in candidatos}

    elegidos: list[int] = []
    usados: set[int] = set()
    nombres_usados: set[str] = set()

    def elige(candidatos_grupo: list[int]) -> None:
        """El primero que quepa: sin repetir grupo y sin repetir nombre.

        *Dos grupos distintos con el mismo nombre («Miel de flores») son dos fichas que
        parecen un duplicado en la demo, y la comparación entre ellas no aporta nada.*
        """
        for gid in candidatos_grupo:
            if gid in usados:
                continue
            nombre = norm(meta.at[gid, "nombre"])
            if nombre in nombres_usados:
                continue
            usados.add(gid)
            nombres_usados.add(nombre)
            elegidos.append(gid)
            return

    def puntua(gid: int) -> tuple[int, int]:
        """Más cadenas primero; a igualdad, nombre más corto y plural antes que singular."""
        nombre = norm(meta.at[gid, "nombre"])
        plural = 0 if re.search(r"\w+s\b", nombre) else 1
        return (-int(meta.at[gid, "cadenas"]), len(nombre) + plural)

    # 0) Los imprescindibles, antes que nada.
    for gid in IMPRESCINDIBLES:
        if gid in candidatos:
            elige([gid])

    # 1) Los términos de uso diario, por orden: el grupo con más cadenas y nombre más corto.
    for seccion, termino in DIARIOS:
        if len(elegidos) >= MAXIMO:
            break
        patron = REGEX.get(termino)
        posibles = []
        for gid in candidatos - usados:
            if meta.at[gid, "seccion"] != seccion:
                continue
            nombre = norm(meta.at[gid, "nombre"])
            if patron:
                if not re.search(patron, nombre):
                    continue
            elif termino not in nombre:
                continue
            if len(str(meta.at[gid, "nombre"])) > 110:
                continue
            posibles.append(gid)
        posibles.sort(key=puntua)
        elige(posibles)

    # 2) Relleno por pasillos, con el cupo de cada uno y los mismos criterios de calidad.
    for seccion, cupo in CUPOS.items():
        ya = sum(1 for gid in elegidos if meta.at[gid, "seccion"] == seccion)
        faltan = min(cupo - ya, MAXIMO - len(elegidos))
        if faltan <= 0:
            continue
        posibles = [
            gid for gid in candidatos - usados
            if meta.at[gid, "seccion"] == seccion
            and len(str(meta.at[gid, "nombre"])) <= 110
        ]
        posibles.sort(key=puntua)
        for gid in posibles[:faltan]:
            elige([gid])

    elegidos = elegidos[:MAXIMO]
    if not 80 <= len(elegidos) <= 120:
        raise SystemExit(f"Salieron {len(elegidos)} productos; tienen que ser entre 80 y 120")

    productos = []
    for gid in sorted(elegidos, key=lambda g: (ORDEN_SECCIONES.index(meta.at[g, "seccion"]),
                                                norm(meta.at[g, "nombre"]))):
        grupo = filas[gid]
        primera = grupo.iloc[0]
        ofertas_json = []
        for _, fila in grupo.iterrows():
            ofertas_json.append({
                "cadena": str(fila.fuente),
                "producto_id": f"{fila.fuente}:{fila.id_fuente}",
                "id_fuente": str(fila.id_fuente),
                "nombre": str(fila.nombre),
                "marca": None if pd.isna(fila.marca) else str(fila.marca),
                "precio_cent": round(float(fila.precio_cent), 2),
                "precio_unidad_cent": round(float(fila.precio_unidad_cent), 4),
                "unidad": str(fila.unidad_canon),
                "imagen": str(fila.imagen),
                "oferta": bool(str(fila.promo_txt).strip()) if not pd.isna(fila.promo_txt) else False,
                "promocion": None if pd.isna(fila.promo_txt) else str(fila.promo_txt),
                "es_marca_propia": bool(fila.es_marca_propia) if not pd.isna(fila.es_marca_propia) else False,
            })
        ofertas_json.sort(key=lambda o: o["precio_unidad_cent"])
        minimo = ofertas_json[0]
        maximo = ofertas_json[-1]
        unidad = str(primera.unidad_canon)
        # *Comparable de verdad: dos cadenas o más y ninguna fila con la comparación
        # desmentida. Si alguna lo está, se marca dudosa y la pantalla no promete ahorro.*
        dudoso = bool((grupo.comparacion_fiable == False).any())  # noqa: E712
        productos.append({
            "grupo_id": int(gid),
            "nombre": str(primera.nombre),
            "marca": None if pd.isna(primera.marca) else str(primera.marca),
            "imagen": str(primera.imagen),
            "unidad": unidad,
            "seccion": str(primera.seccion),
            "categoria": None if pd.isna(primera.categoria) else str(primera.categoria),
            "precio_cent": round(float(minimo["precio_cent"]), 2),
            "precio_unidad_cent": round(float(minimo["precio_unidad_cent"]), 4),
            "precio_unidad_max_cent": round(float(maximo["precio_unidad_cent"]), 4),
            "cadenas": len({o["cadena"] for o in ofertas_json}),
            "productos": len(ofertas_json),
            "ahorro_pct": round(
                (maximo["precio_unidad_cent"] - minimo["precio_unidad_cent"])
                / maximo["precio_unidad_cent"] * 100,
                1,
            ) if maximo["precio_unidad_cent"] else 0,
            "comparable": len({o["cadena"] for o in ofertas_json}) >= 2 and not dudoso,
            "dudoso": dudoso,
            "ofertas": ofertas_json,
        })

    salida = {
        "fecha_datos": FECHA,
        "fuente": "data/gold/v20261115-184138/grupos.parquet",
        "generado_por": "plataforma/web/app/scripts/genera-catalogo-demo.py",
        "productos": productos,
    }
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"{len(productos)} productos → {SALIDA}")
    por_seccion: dict[str, int] = {}
    for p in productos:
        por_seccion[p["seccion"]] = por_seccion.get(p["seccion"], 0) + 1
    for seccion in ORDEN_SECCIONES:
        if seccion in por_seccion:
            print(f"  {seccion}: {por_seccion[seccion]}")
    print(f"  comparables (2+ cadenas): {sum(1 for p in productos if p['cadenas'] >= 2)}")
    print(f"  con abanico de €/unidad: {sum(1 for p in productos if p['precio_unidad_max_cent'] > p['precio_unidad_cent'])}")


if __name__ == "__main__":
    main()
