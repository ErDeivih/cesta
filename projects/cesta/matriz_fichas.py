"""Matriz de fichas: que publica cada cadena, que se extrae y que se pierde por el camino.

**Por que existe.** La ampliacion pide, para las fichas de producto, la secuencia contraria a la
intuicion: *"Matriz por fuente/campo: publicado y extraido / publicado no extraido / no localizado
en la muestra / no aplicable / fallo de extraccion. No convertir todos estos estados en `null` sin
motivo."* Antes de programar nuevas extracciones hay que saber **que ya viene en la respuesta y no
se esta guardando**, que es trabajo tirado si se pide otra vez a la cadena.

**Como lo mide, y que no promete.**

  - **Extraido**: se mira lo que hay en bronze, columna a columna, con su porcentaje de relleno.
  - **En el crudo**: se busca la señal del campo en la **respuesta guardada** de esa cadena (muestra
    determinista). Es una **cota inferior**: que aparezca la palabra `ingredientes` en el HTML no
    demuestra que haya una tabla del producto -- lo dice la propia ampliacion -- asi que esto sirve
    para **descartar** ("no viene") y para priorizar, no para afirmar que el dato esta.
  - **No en la muestra**: ni extraido ni visto en el crudo de la muestra. Puede ser que la cadena no
    lo publique, o que la muestra no lo coja: con 40 respuestas por cadena, eso no se distingue.

Y no toca la red, ni los colectores, ni la tarea de las 06:00: lee lo que ya esta en `data/`.
"""
from __future__ import annotations

import argparse
import gzip
import random
import sys
from pathlib import Path

import polars as pl

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw"
BRONZE = RAIZ / "data" / "bronze"
SEMILLA = 20261006

# Campos de la ficha completa (T11), con las señales que se buscan en el crudo. Las señales van en
# minusculas y sin tildes: se comparan contra el texto normalizado.
CAMPOS: dict[str, list[str]] = {
    "denominacion": ["name", "title", "nombre"],
    "descripcion": ["description", "descripcion"],
    "marca": ["brand", "marca", "supplier"],
    "gtin": ["ean", "gtin", "barcode", "sku"],
    "ingredientes": ["ingredient", "ingrediente"],
    "alergenos": ["allergen", "alergeno"],
    "traza": ["trace", "traza"],
    "nutrientes": ["nutrient", "nutriente", "nutrition", "nutricional"],
    "energia_kcal": ["kcal", "kilocalor", "energy"],
    "base_nutricional": ["per_100", "por 100", "100 g", "100g", "100 ml"],
    "racion": ["serving", "racion", "portion"],
    "peso_neto": ["net_weight", "netweight", "peso neto", "weight_in_grams", "weight"],
    "peso_escurrido": ["drained", "escurrido"],
    "piezas": ["pieces", "piezas", "unidades"],
    "envase": ["packaging", "envase", "package"],
    "origen": ["origin", "origen", "pais"],
    "conservacion": ["storage", "conservacion", "conservar"],
    "preparacion": ["preparation", "preparacion", "modo de uso"],
    "certificaciones": ["certification", "certificado", "eco", "bio"],
    "advertencias": ["warning", "advertencia", "aviso"],
}


CLAVES_NOMBRE = ("name", "title", "nombre", "product_name", "description")
CLAVES_ID = ("id", "sku", "ean", "gtin", "barcode", "objectID", "productId", "retailerProductId")


def objetos_de_producto(dato, salida: list | None = None, limite: int = 4000) -> list[dict]:
    """Los objetos de un JSON que parecen **un producto** y no una categoria o un listado.

    Un producto tiene nombre y algo que lo identifique; una categoria tambien puede tener nombre,
    asi que se pide ademas que traiga alguna señal de producto (precio, identificador de barras,
    unidad de medida). No pretende ser exacto: pretende que el denominador sean productos y no
    respuestas, que era el error de la primera version.
    """
    salida = [] if salida is None else salida
    if len(salida) >= limite:
        return salida
    if isinstance(dato, dict):
        tiene_nombre = any(k in dato for k in CLAVES_NOMBRE)
        tiene_id = any(k in dato for k in CLAVES_ID)
        señales = ("price", "precio", "unit", "unidad", "ean", "gtin", "barcode", "pack")
        if tiene_nombre and tiene_id and any(k in dato for k in señales):
            salida.append(dato)
        for valor in dato.values():
            objetos_de_producto(valor, salida, limite)
    elif isinstance(dato, list):
        for valor in dato:
            objetos_de_producto(valor, salida, limite)
    return salida


def _json_de(texto: str):
    import json

    try:
        return json.loads(texto)
    except Exception:  # noqa: BLE001
        return None


def _normaliza(texto: str) -> str:
    reemplazos = str.maketrans("áéíóúàèìòùäëïöüñç", "aeiouaeiouaeiounc")
    return texto.lower().translate(reemplazos)


def _respuestas(fuente: str, dia: str | None) -> list[Path]:
    base = RAW / f"fuente={fuente}"
    if not base.exists():
        return []
    dias = sorted(d for d in base.iterdir() if d.is_dir() and (dia is None or d.name.endswith(dia)))
    if not dias:
        return []
    return sorted((dias[-1]).glob("*.json.gz"))


def _muestra(ficheros: list[Path], cuantas: int) -> list[Path]:
    """Muestra determinista: la misma hoy y manana, para poder comparar dos mediciones."""
    if len(ficheros) <= cuantas:
        return ficheros
    azar = random.Random(SEMILLA)
    return sorted(azar.sample(sorted(ficheros), cuantas))


def _texto_de(ruta: Path) -> str:
    try:
        return gzip.decompress(ruta.read_bytes()).decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return f"__error__ {type(exc).__name__}"


def columnas_bronze(fuente: str) -> tuple[list[str], int]:
    """Las columnas que existen en bronze y cuantas filas tiene (la ultima captura)."""
    base = BRONZE / f"fuente={fuente}"
    if not base.exists():
        return [], 0
    dias = sorted(d for d in base.iterdir() if d.is_dir())
    if not dias:
        return [], 0
    ficheros = sorted(dias[-1].glob("*.parquet"))
    if not ficheros:
        return [], 0
    try:
        marco = pl.read_parquet(ficheros[0])
    except Exception:  # noqa: BLE001
        return [], 0
    rellenas = [c for c in marco.columns
                if marco[c].null_count() < marco.height and marco[c].dtype != pl.Null]
    return rellenas, marco.height


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fuente", help="mirar solo una cadena")
    ap.add_argument("--muestra", type=int, default=40, help="respuestas crudas por cadena")
    ap.add_argument("--dia", help="dia de raw a mirar (por defecto, el ultimo)")
    a = ap.parse_args(argv)

    fuentes = [a.fuente] if a.fuente else sorted(
        d.name.split("=")[1] for d in RAW.iterdir() if d.is_dir() and d.name.startswith("fuente="))
    if not fuentes:
        print("No hay respuestas crudas que mirar en data/raw.")
        return 0

    for fuente in fuentes:
        ficheros = _respuestas(fuente, a.dia)
        if not ficheros:
            print(f"\n=== {fuente} ===\n  sin respuestas crudas guardadas")
            continue
        muestra = _muestra(ficheros, a.muestra)
        textos = [_texto_de(f) for f in muestra]
        errores = sum(1 for t in textos if t.startswith("__error__"))
        # **Sobre productos, si el crudo es JSON.** Los textos se guardan normalizados para buscar
        # las señales; los productos se buscan en el JSON, que es donde hay objetos que comparar.
        import json as _json

        productos: list[str] = []
        es_html = 0
        for texto in textos:
            if texto.startswith("__error__"):
                continue
            if texto.lstrip()[:1] in "{[":
                dato = _json_de(texto)
                objetos = objetos_de_producto(dato) if dato is not None else []
                if objetos:
                    productos.extend(_json.dumps(o, ensure_ascii=False) for o in objetos)
                else:
                    productos.append(texto)
            else:
                es_html += 1
                productos.append(texto)
        if es_html and not productos:
            print("  (crudo HTML: la cuenta va por respuesta, no por producto)")
        columnas, filas = columnas_bronze(fuente)
        print(f"\n=== {fuente} ===")
        cual = "productos" if len(productos) != len(muestra) else "respuestas"
        print(f"  crudo: {len(ficheros):,} respuestas, miradas {len(muestra)}"
              f" -> {len(productos):,} {cual} (denominador)"
              f"{f', {errores} ilegibles' if errores else ''}"
              f" · bronze: {filas:,} filas, {len(columnas)} columnas con algun valor"
              .replace(",", "."))
        print(f"  {'campo':<17}{'en crudo':>10}{'en bronze':>11}   estado")
        for campo, señales in CAMPOS.items():
            vistas = sum(1 for t in productos if any(s in _normaliza(t) for s in señales))
            extraido = any(_normaliza(c).replace("_", " ") in " ".join(
                _normaliza(x) for x in señales) or _normaliza(c) in señales for c in columnas)
            pct = 100 * vistas / max(len(productos), 1)
            if extraido:
                estado = "publicado y extraido"
            elif vistas:
                estado = "**PUBLICADO Y NO EXTRAIDO**"
            else:
                estado = "no en la muestra"
            print(f"  {campo:<17}{pct:>9.0f}%{('si' if extraido else 'no'):>11}   {estado}")
    print("\n  Como se lee: 'en crudo' es la proporcion de respuestas de la muestra donde aparece la\n"
          "  señal del campo. Es una COTA INFERIOR: ver la palabra no prueba que exista el dato, y su\n"
          "  ausencia puede ser de la muestra (40 respuestas) y no de la cadena. 'En bronze' es lo que\n"
          "  de verdad se esta guardando hoy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
