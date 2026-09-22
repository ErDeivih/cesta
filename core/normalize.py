"""Normalizador universal de formatos. La pieza que iguala a las seis cadenas.

Cada cadena escribe el formato a su manera:
    Mercadona  unit_size=5, size_format='l'
    Aldi       "500 g unidad"
    Alcampo    "5000ml"
    DIA        measure_unit='LITRO' + quantity_per_unit
    Carrefour  "0,47 €" / measure_unit='kg'   (solo texto)
    Lidl       "Bandeja 2 x 150 g"

Todo acaba en (cantidad, unidad_canon, unidades_pack) y en precio por kg / L / ud.
Sin esto no se puede comparar nada.
"""
from __future__ import annotations

import re
import unicodedata

# factor a la unidad canonica: kg, l, ud
_UNIDADES = {
    "kg": ("kg", 1.0), "kilo": ("kg", 1.0), "kilos": ("kg", 1.0), "kgs": ("kg", 1.0),
    "g": ("kg", 0.001), "gr": ("kg", 0.001), "gramo": ("kg", 0.001), "gramos": ("kg", 0.001),
    "mg": ("kg", 1e-6),
    "l": ("l", 1.0), "lt": ("l", 1.0), "litro": ("l", 1.0), "litros": ("l", 1.0),
    "ml": ("l", 0.001), "cl": ("l", 0.01), "dl": ("l", 0.1),
    "cc": ("l", 0.001),
    "ud": ("ud", 1.0), "uds": ("ud", 1.0), "unidad": ("ud", 1.0), "unidades": ("ud", 1.0),
    "u": ("ud", 1.0), "pieza": ("ud", 1.0), "piezas": ("ud", 1.0),
    "dosis": ("ud", 1.0), "lavado": ("ud", 1.0), "lavados": ("ud", 1.0),
    "m": ("m", 1.0), "metro": ("m", 1.0), "metros": ("m", 1.0), "cm": ("m", 0.01),
    # etiquetas sueltas que usan las cadenas para cosas que se cuentan
    "panuelo": ("ud", 1.0), "panuelos": ("ud", 1.0), "pastilla": ("ud", 1.0),
    "pastillas": ("ud", 1.0), "toallita": ("ud", 1.0), "toallitas": ("ud", 1.0),
    "rollos": ("ud", 1.0), "sobre": ("ud", 1.0), "sobres": ("ud", 1.0),
    "bolsa": ("ud", 1.0), "bolsas": ("ud", 1.0), "racion": ("ud", 1.0),
    "raciones": ("ud", 1.0), "porcion": ("ud", 1.0), "porciones": ("ud", 1.0),
    "pack": ("ud", 1.0), "lote": ("ud", 1.0), "par": ("ud", 1.0),
    # abreviaturas de etiqueta de estante de Mercadona
    "lv": ("ud", 1.0), "dc": ("ud", 1.0), "dz": ("ud", 1.0), "docena": ("ud", 1.0),
    "pza": ("ud", 1.0), "capsula": ("ud", 1.0), "capsulas": ("ud", 1.0),
    "rollo": ("ud", 1.0),
}

# unidades canonicas del proyecto: todo acaba en una de estas
CANONICAS = ("kg", "l", "ud", "m")

_NUM = r"(\d+(?:[.,]\d+)?)"
# "6x1 L", "2 x 150 g", "pack 4 x 33 cl"
_PACK = re.compile(rf"{_NUM}\s*[x×]\s*{_NUM}\s*([a-zA-Zñ]+)", re.IGNORECASE)
# "500 g", "1,5 L", "450ml"
_SIMPLE = re.compile(rf"{_NUM}\s*([a-zA-Zñ]+)", re.IGNORECASE)

_REFERENCIAS_UD = {
    "ud", "uds", "unidad", "unidades", "pieza", "piezas", "lavado", "lavados",
    "dosis", "capsula", "capsulas", "pastilla", "pastillas", "toallita", "toallitas",
    "panuelo", "panuelos", "rollo", "rollos",
}


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def parse_formato(texto: str | None) -> tuple[float | None, str | None, int]:
    """'Pack 6 x 1 L' -> (6.0, 'l', 6).  '500 g unidad' -> (0.5, 'kg', 1).

    Devuelve (cantidad_total_en_unidad_canon, unidad_canon, unidades_del_pack).
    """
    if not texto:
        return None, None, 1
    t = _sin_tildes(str(texto).lower())

    m = _PACK.search(t)
    if m:
        n, cant, uni = _num(m.group(1)), _num(m.group(2)), m.group(3)
        if uni in _UNIDADES:
            canon, factor = _UNIDADES[uni]
            return round(n * cant * factor, 6), canon, int(n)

    mejor = None
    for m in _SIMPLE.finditer(t):
        uni = m.group(2)
        if uni in _UNIDADES:
            canon, factor = _UNIDADES[uni]
            cand = (round(_num(m.group(1)) * factor, 6), canon)
            # nos quedamos con la primera coincidencia con unidad de peso/volumen
            if mejor is None or (mejor[1] == "ud" and canon != "ud"):
                mejor = cand
    if mejor:
        return mejor[0], mejor[1], 1
    return None, None, 1


def canonizar_unidad(etiqueta: str | None) -> str | None:
    """Cualquier etiqueta de unidad -> kg / l / ud / m, o None si no se reconoce.

    Hace falta porque cada cadena escribe la suya: Aldi manda 'panuelo', 'pastilla'
    o 'toallita' como escala de su precio por unidad, y sin traducir se colaban tal
    cual en la columna canonica y rompian la comparacion.
    """
    if not etiqueta:
        return None
    e = _sin_tildes(str(etiqueta).strip().lower())
    if e in CANONICAS:
        return e
    if e in _UNIDADES:
        return _UNIDADES[e][0]
    for palabra in re.findall(r"[a-z]+", e):
        if palabra in _UNIDADES:
            return _UNIDADES[palabra][0]
    return None


def precio_por_unidad(precio_cent: int | None, cantidad: float | None,
                      unidad: str | None) -> tuple[int | None, str | None]:
    """precio total + cantidad canonica -> centimos por kg / L / ud."""
    if not precio_cent or not cantidad or cantidad <= 0 or not unidad:
        return None, None
    return round(precio_cent / cantidad), unidad


def normaliza_referencia(fuente: str, precio_cent: int | None,
                         unidad: str | None) -> tuple[float | None, str | None]:
    """Convierte una referencia nativa a EUR/kg, EUR/L, EUR/ud o EUR/m.

    Algunas APIs describen la etiqueta mostrada, no la magnitud matematica. Aldi,
    por ejemplo, devuelve 1,88 EUR con ``100-ml`` para un envase de 200 ml: para
    comparar hay que convertirlo a 18,80 EUR/L. Su valor con etiqueta ``g``, en
    cambio, ya viene expresado por kg. Esta peculiaridad es propia de esa fuente.
    """
    if precio_cent is None or not unidad:
        return None, None
    u = _sin_tildes(str(unidad).lower()).strip().replace("_", "-")
    u = re.sub(r"\s+", " ", u)

    if fuente == "aldi":
        if u in {"100-ml", "100 ml", "100ml"}:
            return float(precio_cent) * 10, "l"
        if u in {"100-g", "100 g", "100g"}:
            return float(precio_cent) * 10, "kg"
        if u == "g":
            return float(precio_cent), "kg"

    if u in {"kg", "kilo", "kilos", "100 g", "100-g", "100g"}:
        return float(precio_cent), "kg"
    if u in {"l", "lt", "litro", "litros", "litre", "litres"}:
        return float(precio_cent), "l"
    if u in {"m", "metro", "metros", "m-(metro)"}:
        return float(precio_cent), "m"
    if u in _REFERENCIAS_UD:
        return float(precio_cent), "ud"
    return float(precio_cent), None


def nombre_limpio(nombre: str, marca: str | None = None) -> str:
    """Quita marca, formato y ruido. Base para el matching por nombre."""
    t = _sin_tildes(str(nombre).lower())
    if marca:
        t = t.replace(_sin_tildes(marca.lower()), " ")
    t = re.sub(rf"{_NUM}\s*[x×]\s*{_NUM}\s*[a-z]+", " ", t)
    t = re.sub(rf"{_NUM}\s*(?:{'|'.join(_UNIDADES)})\b", " ", t)
    t = re.sub(r"\b(pack|bandeja|botella|garrafa|brik|bolsa|caja|tarrina|lata|"
               r"envase|formato|ahorro|familiar)\b", " ", t)
    t = re.sub(r"[^a-z0-9ñ ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


if __name__ == "__main__":
    for s in ["Pack 6 x 1 L", "500 g unidad", "5000ml", "Botella 1,5 L",
              "2 kg.", "Bandeja 2 x 150 g", "12 ud", "450 ml", "40 lavados"]:
        print(f"{s:22} -> {parse_formato(s)}")
    print(nombre_limpio("Aceite de oliva 0,4º Hacendado garrafa 5 L", "Hacendado"))
