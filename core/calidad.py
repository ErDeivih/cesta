"""Calidad A / B / C dentro de un grupo de productos equivalentes.

La pregunta que hay detras es la de David: "estoy dispuesto a pagar mas por un
producto mejor, pero quiero saber cual es mejor". Aqui "mejor" no es una opinion:
se lee de la lista de ingredientes, que es un dato publicado.

Cuatro senales, todas verificables en la etiqueta:

  aditivos          cuantos codigos E-xxx aparecen
  aceite de palma   presente o no
  ingrediente 1     su porcentaje declarado, cuando lo declara
  longitud          cuantos ingredientes tiene la lista

No todas las cadenas publican ingredientes: Mercadona y DIA si, Carrefour, Aldi y
Alcampo no. Por eso cada producto lleva ademas de la letra el ORIGEN de esa letra,
y nunca se presenta como analisis de etiqueta lo que en realidad es una posicion
de precio. Un dato flojo etiquetado como flojo es utilizable; disfrazado, no.
"""
from __future__ import annotations

import re
import unicodedata

# E-numbers: "E-330", "E330", "E 471". Solo tres o cuatro digitos, para no
# confundirlos con codigos de lote ni con "E" de otra cosa.
_ADITIVO = re.compile(r"\bE\s?-?\s?(\d{3}[a-z]?)\b", re.IGNORECASE)
_PORCENTAJE = re.compile(r"(\d{1,3}(?:[.,]\d+)?)\s*%")
_PALMA = re.compile(r"\bpalma\b|\bpalmiste\b")

ORIGENES = ("ingredientes", "precio", "sin_datos")


def _plano(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower())
                   if unicodedata.category(c) != "Mn")


def analiza(ingredientes: str | None) -> dict | None:
    """Senales medibles de una lista de ingredientes. None si no hay lista."""
    if not ingredientes or len(ingredientes.strip()) < 8:
        return None
    t = _plano(ingredientes)
    partes = [p for p in re.split(r"[,;()]", t) if p.strip()]
    porcentajes = [float(m.replace(",", ".")) for m in _PORCENTAJE.findall(t)]
    return {
        "aditivos": len({m.lower() for m in _ADITIVO.findall(t)}),
        "palma": bool(_PALMA.search(t)),
        "pct_principal": max(porcentajes) if porcentajes else None,
        "n_ingredientes": len(partes),
    }


def puntua(ingredientes: str | None) -> float | None:
    """0 (peor) a 100 (mejor). None si el producto no publica ingredientes.

    Los pesos son deliberadamente simples y estan a la vista: un numero que no se
    puede explicar no sirve para decidir una compra.
    """
    s = analiza(ingredientes)
    if s is None:
        return None
    nota = 100.0
    nota -= min(s["aditivos"], 10) * 6.0          # cada aditivo resta, hasta -60
    if s["palma"]:
        nota -= 15.0
    nota -= min(max(s["n_ingredientes"] - 5, 0), 15) * 1.5   # listas largas, hasta -22,5
    if s["pct_principal"] is not None:
        # 100 % del ingrediente principal suma 15; 50 % no suma nada.
        nota += max(0.0, (s["pct_principal"] - 50.0)) * 0.3
    return max(0.0, min(100.0, nota))


def letras(puntuaciones: list[float | None]) -> list[str | None]:
    """Reparte A/B/C por terciles DENTRO del grupo, no en abstracto.

    Una letra absoluta no significa nada: un aceite de oliva virgen extra y un
    refresco no compiten. Lo util es "de estos seis yogures, este es de los
    mejores". Con menos de tres productos con datos no se reparte nada: inventar
    un tercil sobre dos productos es ruido con aspecto de dato.
    """
    validas = sorted(p for p in puntuaciones if p is not None)
    if len(validas) < 3:
        return [None] * len(puntuaciones)
    corte_a = validas[int(len(validas) * 2 / 3)]
    corte_b = validas[int(len(validas) / 3)]
    salida: list[str | None] = []
    for p in puntuaciones:
        if p is None:
            salida.append(None)
        elif p >= corte_a:
            salida.append("A")
        elif p >= corte_b:
            salida.append("B")
        else:
            salida.append("C")
    return salida


def por_precio(precios_unidad: list[float | None]) -> list[str | None]:
    """Respaldo cuando NINGUN producto del grupo publica ingredientes.

    El precio por unidad no mide calidad, mide precio. Dentro de un grupo que ya
    es comparable, el mas caro suele ser la gama alta, asi que A va al mas caro.
    Es una correlacion, no una medida, y por eso el resultado siempre viaja con
    origen "precio": nadie debe confundirlo con haber leido una etiqueta.
    """
    return letras(list(precios_unidad))
