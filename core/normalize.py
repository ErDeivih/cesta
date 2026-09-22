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


def _etiqueta_limpia(etiqueta: str | None) -> str:
    """Etiqueta de unidad comparable: sin tildes, sin puntos, sin guiones sueltos."""
    e = _sin_tildes(str(etiqueta or "").strip().lower()).replace("_", "-")
    e = re.sub(r"[.\s]+", " ", e)
    return re.sub(r"\s*-\s*", "-", e).strip()


# Etiquetas que significan "el precio es de 100 gramos" o "de 100 mililitros".
_POR_100 = re.compile(r"^100\s*-?\s*(g|gr|grs|gramo|gramos|ml|mls|mililitro|mililitros|cc)$")

# Cadenas cuya etiqueta de 100 es de verdad "por 100" y hay que multiplicar por
# diez. La medicion esta en `lecturas_referencia`; el resto de cadenas publica el
# valor ya por kilo o por litro, o no tiene con que comprobarlo.
_POR_100_X10 = frozenset({"dia", "aldi"})


def unidad_por_100(etiqueta: str | None) -> str | None:
    """'100 ml' -> 'l'.  '100 gr.' -> 'kg'.  None si no es una referencia por 100.

    Hace falta porque una etiqueta de 100 no vale lo mismo en todas las cadenas, y
    tratarla como si fuera por kilo metia un error de diez veces que nadie ve.
    Carrefour lo deja claro: un desodorante de 50 ml a 2,49 EUR trae ``4,98`` con
    etiqueta ``100ml``, que es 2,49 / 0,05 * 10, o sea el precio del litro. Las
    cinco cadenas la usan (Carrefour 1.816 productos, DIA 532, Mercadona 504,
    Aldi 230), asi que el error no era de una cadena: era nuestro.
    """
    m = _POR_100.match(_etiqueta_limpia(etiqueta))
    if not m:
        return None
    return "kg" if m.group(1).startswith("g") else "l"


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
    por ejemplo, devuelve 1,88 EUR con ``100-ml`` para un envase de 200 ml: su
    valor **no** es el del litro. Su valor con etiqueta ``g``, en cambio, ya viene
    expresado por kg. Esta peculiaridad es propia de esa fuente.

    Ojo con las etiquetas de 100: aqui se devuelven **como las publica la cadena**,
    sin multiplicar por diez. Cual de las dos lecturas vale lo decide
    ``_lecturas_referencia`` en el pipeline, mirando el precio del propio
    producto; ver ``unidad_por_100``.
    """
    if precio_cent is None or not unidad:
        return None, None
    u = _etiqueta_limpia(unidad)

    if fuente == "aldi" and u == "g":
        # Aldi etiqueta 'g' pero ya publica el precio por kilo.
        return float(precio_cent), "kg"

    por100 = unidad_por_100(unidad)
    if por100:
        return float(precio_cent), por100

    if u in {"kg", "kilo", "kilos"}:
        return float(precio_cent), "kg"
    if u in {"l", "lt", "litro", "litros", "litre", "litres"}:
        return float(precio_cent), "l"
    if u in {"m", "metro", "metros", "m-(metro)"}:
        return float(precio_cent), "m"
    if u in _REFERENCIAS_UD:
        return float(precio_cent), "ud"
    return float(precio_cent), None


def lecturas_referencia(fuente: str, precio_cent: int | None,
                        unidad: str | None) -> tuple[tuple[float, str | None], ...]:
    """Las lecturas posibles de una referencia nativa, de la mas probable a la menos.

    Con una etiqueta normal hay una sola. Con una de 100 hay dos, porque ``100 g``
    puede querer decir que el precio es de 100 gramos -- hay que multiplicar por
    diez para tener el kilo -- o que ya viene por kilo con la etiqueta escrita de
    otra manera. **Las dos convenciones conviven, y no es cosa de estilo: son dos
    cadenas diciendo cosas distintas con el mismo texto.** Medido el 22 de
    septiembre sobre los productos que SI tienen formato (sin formato no hay con
    que comprobarlo), comparando el precio del producto con su referencia:

        dia        529 de 529 por 100           -> por diez
        aldi       202 de 223 por 100           -> por diez
        mercadona  488 de 488 ya por kilo/litro -> tal cual
        carrefour    0 comprobables (no publica formato) -> tal cual, y se
                     corrige producto a producto cuando el nombre lo confirma

    Cual vale lo decide el precio del propio producto (``_referencia_que_cuadra``,
    en el pipeline) y, si no hay con que comprobarlo, la convencion de su cadena.
    """
    ref_cent, ref_uni = normaliza_referencia(fuente, precio_cent, unidad)
    if ref_cent is None:
        return ()
    valor = float(ref_cent)
    if unidad_por_100(unidad):
        if fuente in _POR_100_X10:
            return ((valor * 10, ref_uni), (valor, ref_uni))
        return ((valor, ref_uni), (valor * 10, ref_uni))
    return ((valor, ref_uni),)


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
