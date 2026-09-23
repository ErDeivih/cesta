"""Los ejes que el nombre de un producto declara, y que dos no pueden contradecir.

Esto existe por un fallo medido: el reparto hungaro es 1-a-1 **por par de cadenas**,
pero `agrupar()` une por **componentes conexas**. Con cinco cadenas hay diez pares, y
basta que en uno se una *entera* con *sin lactosa* y en otro *sin lactosa* con
*desnatada* para acabar con entera y desnatada en el mismo grupo **sin que ningun
enlace individual este mal**. Medido el 23 de septiembre de 2026: el grupo mayor
tenia 84 cervezas mezclando sin gluten y sin alcohol, y 43 aceites mezclaban virgen
con virgen extra.

**El margen de precio no puede ser el cuchillo.** `core/comparacion.py` documenta
ahorros reales de 28x entre marca blanca y marca (preservativos, cerveza, tampones):
cortar por margen borraria justo los hallazgos que esta aplicacion existe para
encontrar. El margen sirve para **detectar** el grupo sospechoso; lo que corta es lo
que el nombre **declara**.

Y la regla que lo hace honesto: **si uno de los dos no declara nada, no bloquea**.
Un producto que no dice si es entera o desnatada no esta afirmando que sea igual: es
que no lo sabemos. Eso no es tolerancia, es ausencia de prueba.
"""
from __future__ import annotations

import unicodedata

# Cada eje es una lista de (valor, patrones). **El orden importa**: se comprueba en
# este orden y gana el primero que encaje, asi que lo especifico va antes que lo
# general (`virgen extra` antes que `virgen`, `sin lactosa` antes que `entera`...).
#
# Solo se ponen ejes donde el nombre es explicito y las dos opciones existen de
# verdad en el catalogo. Un eje inventado bloquea productos que si son comparables,
# y eso es peor que no tenerlo: quita ahorros reales.
EJES: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "grasa": [
        # `semidesnatada` **antes** que `desnatada`: `desnatad` casa dentro de
        # `semidesnatad`, y al reves la leche semidesnatada se leeria como sin
        # grasa. Es el mismo fallo de subcadenas que la auditoria del 17 de
        # septiembre encontro dos veces ("champu" empieza como "champan"), y lo
        # caza `tests/test_atributos.py`.
        ("semidesnatada", ("semidesnatad", "semi-desnatad", "semi desnatad")),
        ("sin grasa", ("desnatad", "descremad", "0% de grasa", "cero por ciento")),
        ("entera", ("entera",)),
    ],
    "aceite": [
        ("virgen extra", ("virgen extra", "v.extra", "v. extra")),
        ("orujo", ("orujo", "bagazo", "aceite de oliva 0,4", "oliva 1o")),
        ("virgen", ("virgen",)),
        ("oliva suave", ("oliva suave", "sabor suave", "oliva intenso")),
    ],
    "gas": [
        ("sin gas", ("sin gas", "no gas")),
        ("con gas", ("con gas",)),
    ],
    "alcohol": [
        ("sin alcohol", ("sin alcohol", "0,0", "0.0%", "cero cero", "no alcohol")),
        ("con alcohol", ("con alcohol",)),
    ],
    "cafeina": [
        ("descafeinado", ("descafeinad", "descafeinat")),
        ("natural", ("natural",)),
    ],
    "azucar": [
        ("sin azucar", ("sin azucar", "zero", "cero azucar", "0% azucar")),
        ("con azucar", ("azucar", "azucarado")),
    ],
    "integral": [
        ("integral", ("integral", "entero de trigo", "grano entero")),
        ("blanco", ("blanco",)),
    ],
    "lactosa": [
        ("sin lactosa", ("sin lactosa", "deslactosad", "0% lactosa")),
    ],
    "gluten": [
        ("sin gluten", ("sin gluten", "gluten free", "0% gluten")),
    ],
    "formato": [
        # **`concentrado` estuvo aqui y se quito el 23 de septiembre de 2026**, y el
        # motivo es que no es una opcion del mismo eje que las otras dos: el estado
        # (polvo o liquido) y la concentracion son dos cosas distintas, y un producto
        # puede ser las dos a la vez. Medido: se llevaba por delante pares **ciertos
        # por codigo de barras** --
        #
        #     «Cafe liquido espresso concentrado black Nescafe 500 ml»   (Carrefour)
        #     «Cafe espresso concentrado black Nescafe 500 ml»           (DIA)
        #     «Ambientador liquido concentrado Foresan deluxe»            (Mercadona)
        #     «Ambientador concentrado Deluxe Foresan 125 ml»            (Carrefour)
        #
        # --, que son el mismo producto con el nombre escrito de dos maneras. Un eje
        # que dice que esas dos fichas no son el mismo producto esta simplemente
        # equivocado, y la regla del proyecto es que **un eje inventado es peor que
        # no tenerlo**, porque quita comparaciones que si valian. Para separar un
        # concentrado de uno que no lo es haria falta un eje propio con su opcion
        # "normal", y esa no existe en los nombres del catalogo: nadie escribe
        # "no concentrado".
        ("en polvo", ("en polvo", "polvo soluble")),
        ("liquido", ("liquido",)),
    ],
    "cafe": [
        ("molido", ("molido",)),
        ("grano", ("en grano", "grano natural")),
        ("capsula", ("capsula", "capsulas", "monodosis", "pastilla")),
        ("soluble", ("soluble", "instantaneo", "instant")),
    ],
    "leche": [
        ("leche de vaca", ("leche de vaca", "leche entera", "leche desnatada",
                           "leche semidesnatada")),
        ("bebida vegetal", ("bebida de", "bebida vegetal", "avena", "soja",
                            "almendra", "arroz")),
    ],
}


def _plano(texto: str) -> str:
    """Minusculas y sin acentos: `Atún` y `atun` son la misma palabra."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()


def valores(nombre: str | None) -> dict[str, str]:
    """Lo que el nombre declara, eje a eje. Los que no declara **no aparecen**.

    Un eje que no sale de aqui es un eje sobre el que este producto no dice nada, y
    sobre el que por tanto no puede contradecir a nadie.
    """
    texto = _plano(nombre or "")
    if not texto:
        return {}
    dicho: dict[str, str] = {}
    for eje, opciones in EJES.items():
        for valor, patrones in opciones:
            if any(p in texto for p in patrones):
                dicho[eje] = valor
                break
    return dicho


def contradicciones(nombres: list[str | None]) -> dict[str, list[str]]:
    """Los ejes en los que estos nombres se contradicen, y con que valores.

    Devuelve solo los ejes con **dos o mas valores distintos**. Un eje donde uno
    declara y otro calla no sale: no hay contradiccion, hay silencio.

        >>> contradicciones(["Leche entera 1 l", "Leche desnatada 1 l"])
        {'grasa': ['entera', 'sin grasa']}
        >>> contradicciones(["Leche entera 1 l", "Leche 1 l"])
        {}
    """
    por_eje: dict[str, set[str]] = {}
    for nombre in nombres:
        for eje, valor in valores(nombre).items():
            por_eje.setdefault(eje, set()).add(valor)
    return {eje: sorted(vs) for eje, vs in por_eje.items() if len(vs) > 1}


def ejes_declarados(nombre: str | None) -> int:
    """Cuantos ejes declara un nombre. Sirve para ordenar por lo explicito que es."""
    return len(valores(nombre))
