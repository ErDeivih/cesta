"""El envase de un producto, dicho igual venga de donde venga.

Para que sirve saber el envase
------------------------------
Para tres cosas que la gente hace de verdad:

  * **Comparar sin trampa.** Un pack de seis latas y una botella de dos litros
    del mismo refresco no son el mismo producto aunque el emparejador los junte
    por el nombre. El envase es la senal mas barata para separarlos.
  * **Filtrar por lo que cabe en casa.** "Botella de cristal no, que pesa";
    "brik, que va al armario".
  * **Contar envases.** Cuantas latas y cuantos briks lleva la compra del mes.

Las dos cadenas que lo publican lo escriben distinto: DIA dice "bote" y "frasco",
Mercadona dice "Bote" y "Tarro", y ademas Mercadona mete el numero de unidades
en el mismo campo ("Pack-6"), que no es un envase sino una cantidad.

Medido el 17 de septiembre de 2026 sobre las fichas guardadas:

    dia         5.410 productos, 21 formas distintas
    mercadona   4.317 productos, 35 formas distintas (el 86 % lo trae)
    aldi        no lo publica
    alcampo     no lo publica
    carrefour   no lo publica
"""
from __future__ import annotations

import re
import unicodedata

# Nuestro vocabulario. Corto a proposito: si hay treinta opciones en un filtro,
# nadie lo usa.
ENVASES = ("bolsa", "botella", "brik", "lata", "caja", "bandeja", "bote",
           "tarro", "tarrina", "sobre", "vaso", "paquete", "blister", "tubo",
           "garrafa", "malla", "estuche", "spray", "sin-envase")

_TRADUCCION = {
    "bolsa": "bolsa", "bolsita": "bolsa", "malla": "malla", "red": "malla",
    "botella": "botella", "botellin": "botella", "garrafa": "garrafa",
    "brik": "brik", "tetrabrik": "brik", "baginbox": "garrafa",
    "lata": "lata", "bote": "bote", "frasco": "tarro", "tarro": "tarro",
    "caja": "caja", "estuche": "estuche", "cajita": "caja",
    "bandeja": "bandeja", "barqueta": "bandeja", "tarrina": "tarrina",
    "sobre": "sobre", "sobrecito": "sobre", "vaso": "vaso", "copa": "vaso",
    "paquete": "paquete", "blister": "blister", "tubo": "tubo",
    "spray": "spray", "aerosol": "spray", "pulverizador": "spray",
    "sin envase": "sin-envase", "sin-envase": "sin-envase", "granel": "sin-envase", "pieza": "sin-envase",
    "a granel": "sin-envase",
}

# Mercadona mete la cantidad dentro del campo del envase: "Pack-6", "Pack-4".
_PACK = re.compile(r"^pack[\s\-]*(\d+)?$")


def _plano(texto: str) -> str:
    sin = "".join(c for c in unicodedata.normalize("NFD", texto or "")
                  if unicodedata.category(c) != "Mn")
    return " ".join(sin.lower().split())


def lee(bruto) -> tuple[str | None, int | None]:
    """Lo que escribe la cadena -> (envase nuestro, unidades del pack).

    Devuelve dos cosas porque el campo trae dos: "Pack-6" dice que van seis, y
    no dice en que. Las unidades vuelven aparte para que el emparejador pueda
    usarlas y el filtro de envase no acabe con una opcion llamada "Pack-6".
    """
    t = _plano(str(bruto or ""))
    if not t:
        return None, None
    m = _PACK.match(t)
    if m:
        return None, int(m.group(1)) if m.group(1) else None
    if t in _TRADUCCION:
        return _TRADUCCION[t], None
    # "Botella de cristal", "Caja de carton": la primera palabra manda.
    primera = t.split()[0]
    return _TRADUCCION.get(primera), None
