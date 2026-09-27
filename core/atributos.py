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

import re
import unicodedata

# **Las palabras del dominio de cada eje: sin ninguna de ellas, el eje no se pronuncia.**
#
# Esto es la correccion del 27 de septiembre de 2026, y sale de la auditoria de los 85
# desacuerdos del banco de ejes (`docs/LAYA.md` §5.1): de esos 85, **27 eran fallos de estas
# listas**, no del modelo. Los patrones son subcadenas sueltas aplicadas a los 52.823
# productos, y fuera de su dominio disparan en cualquier cosa:
#
#     leche     «Tostas de pan con avena», «Arroz blanco precocido», «Almendra frita y salada»
#               -> `avena`, `arroz`, `almendra` disparaban "bebida vegetal" en todo
#     cafe      «Apresto instantaneo para planchado», «Fideos instantaneos MAGGI»,
#               «Sopinstant Crema de pollo» -> `instant` disparaba "soluble"
#     aceite    «Crema de Orujo Ruavieja», «Licor de crema de orujo PANIZO»,
#               «Lazos Virgen del Brezo» -> `orujo` y `virgen` disparaban sin ser aceite
#     integral  «Vino blanco con D.O. Rias Baixas» -> `blanco` disparaba "blanco"
#     grasa     «Avellanas enteras», «Sardina entera» -> `entera` disparaba "entera"
#
# Son palabras **enteras**, y se buscan como palabras enteras a proposito: `pan` no esta
# dentro de `Panga` (un pescado) y `leche` no esta dentro de `lechecillas`.
DOMINIO: dict[str, tuple[str, ...]] = {
    "grasa": ("leche", "yogur", "yogures", "nata", "queso", "cuajada", "kefir",
              "mantequilla", "batido", "postre", "flan", "cuajado"),
    "aceite": ("aceite", "oliva", "girasol", "olivas"),
    "cafe": ("cafe", "cafes", "nescafe", "capuchino", "espresso", "expresso", "moka",
             "torrefacto", "descafeinad", "cafetera"),
    "leche": ("leche", "leches", "bebida", "bebidas", "batido", "batidos"),
    "integral": ("pan", "panes", "harina", "arroz", "pasta", "macarra", "macarrones",
                 "espagueti", "galleta", "galletas", "cereal", "cereales", "tosta",
                 "tostas", "biscote", "trigo", "centeno", "salvado", "quinoa", "maiz",
                 "avena", "fideo", "fideos", "semola", "cuscus", "copos", "muesli"),
}

# **Un valor tambien puede declararse con un patron con hueco.** La cadena no siempre es
# contigua: «Pan tostado bajo en sal y en azucares» dice lo mismo que «bajo en azucares», y
# una subcadena no lo coge. Es el cuarto caso que encontro la auditoria de Laya en el eje del
# azucar (`docs/LAYA.md` §5.1).
#
# Se resuelve **antes** que los patrones normales, y por eso el valor negado gana: en este eje
# "sin azucar" va antes que "con azucar", asi que un nombre negado no declara tener azucar.
#
# La regla general de negaciones se probo y se descarto: se llevaba por delante fichas
# legitimas («Leche sin lactosa entera» no deja de ser entera porque no tenga lactosa).
REGEX: dict[tuple[str, str], str] = {
    ("azucar", "sin azucar"): (r"(sin|bajo en|baja en|reducid\w* en|poco|libre de)"
                               r"[^,.;]{0,20}azucar"),
}

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
        # Las negaciones que de verdad declaran "sin": `sin azucar`, `zero`, `0 % azucar`.
        # Las otras formas ("sin azucares anadidos", "bajo en azucares") **no** son esta
        # opcion: son otra afirmacion, y sin patron no disparan nada.
        ("sin azucar", ("sin azucar", "zero", "cero azucar", "0% azucar", "0 % azucar",
                        "sin azucares", "sin azucares anadidos")),
        ("con azucar", ("azucar", "azucarado", "azucarada")),
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


def _palabra(texto: str, palabra: str) -> bool:
    """¿Aparece esa palabra **entera**? `pan` no esta dentro de `panga`."""
    return re.search(rf"(?<![a-z0-9]){re.escape(palabra)}(?![a-z0-9])", texto) is not None


def _dominio(texto: str, eje: str) -> bool:
    """¿El nombre habla de lo que ese eje mide? Sin esto, el eje no se pronuncia."""
    palabras = DOMINIO.get(eje)
    if not palabras:
        return True
    return any(_palabra(texto, p) for p in palabras)


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
        if not _dominio(texto, eje):
            continue
        for valor, patrones in opciones:
            hueco = REGEX.get((eje, valor))
            if hueco and re.search(hueco, texto):
                dicho[eje] = valor
                break
            donde = -1
            for p in patrones:
                donde = texto.find(p)
                if donde >= 0:
                    break
            if donde < 0:
                continue            # este valor no lo dice el nombre
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
