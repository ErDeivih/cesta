"""Si un producto lleva alcohol.

Por que hace falta deducirlo
----------------------------
Solo dos cadenas lo dicen: Alcampo marca 1.589 productos con `alcohol` y
`ageRestriction`, y Mercadona 223 con `badges.requires_age_check`. Las otras
tres -- Aldi, Carrefour y DIA -- no lo dicen en ningun campo. Un filtro "sin
alcohol" que solo funcionara en dos cadenas de cinco es peor que no tenerlo:
devolveria vino de DIA a alguien que no bebe.

Y del nombre no se saca a ojo: "cerveza 0,0" lleva la palabra cerveza.

La asimetria que hace esto seguro
---------------------------------
Este es un filtro de **exclusion**, y eso cambia por completo qué error se puede
permitir. Comparado con el filtro "sin gluten", que es de **inclusion**:

    sin gluten (incluir)   marcar de mas es PELIGROSO: un celiaco ve unas
                           galletas con gluten porque creimos que no lo llevaban
    sin alcohol (excluir)  marcar de mas solo es MOLESTO: desaparece de la lista
                           un vinagre de Jerez que si se podia comprar.
                           Marcar de MENOS es lo peligroso.

Asi que aqui se afina al contrario que en los sellos: se prefiere pasarse. Y los
pocos que se escapan se llaman "Cerveza" o "Vino" en el propio nombre, o sea que
quien mira el resultado los ve.

Medido el 17 de septiembre de 2026 contra lo que declaran las dos cadenas que lo
declaran:

    alcampo     precision 96 %   cobertura 98 %
    mercadona   precision 97 %   cobertura 89 %

Y la precision real es mas alta que esa: entre los "falsos positivos" de
Mercadona hay una "Cerveza Clasica Steinburg" y un "Vino tinto tempranillo
crianza". Llevan alcohol; el que no los marca es Mercadona.

La cobertura que falta son, casi toda, cervezas 0,0 que Mercadona marca como
alcohol aunque no lo lleven: ahi el equivocado es Mercadona, no nosotros.

El tropiezo de siempre
----------------------
La primera version daba un 77 % de precision por una sola razon: el patron de
champan decia `champ`, y **champu** empieza igual. Es el mismo error que "eco"
dentro de "seco" en core/sellos.py, cometido el mismo dia. Por eso todos los
patrones de aqui van con limites de palabra.
"""
from __future__ import annotations

import re
import unicodedata

# Bebidas con alcohol, por su nombre. Palabras enteras, nunca prefijos.
_BEBIDAS = re.compile(
    r"\b(cerveza|cervezas|birra|vino|vinos|tinto de verano|clarete|"
    r"champan|champagne|cava|sidra|cider|vermut|vermouth|"
    r"ron|rones|ginebra|gin|whisky|whiskey|bourbon|vodka|tequila|mezcal|"
    r"licor|licores|orujo|pacharan|brandy|conac|cognac|armagnac|grappa|"
    r"sangria|mistela|moscatel|oporto|jerez|lager|pilsen|pilsener|ipa|"
    r"radler|hidromiel|absenta|anisette|aguardiente|calvados|sake)\b",
    re.IGNORECASE)

# Lo que dice que NO lleva, y manda sobre lo anterior.
_SIN = re.compile(
    r"(0\s*[,.]\s*0|sin alcohol|desalcoholiz|\b0\s*%|\bzero\b|\bcero\b|"
    r"\bsin gas y sin alcohol\b)", re.IGNORECASE)

# Comida que lleva el nombre de una bebida. "Vinagre de Jerez" no emborracha, y
# un coctel de frutos secos tampoco.
_COMIDA = re.compile(
    # Con `s?` al final de cada palabra: "Carrilladas de cerdo al vino dulce"
    # es comida, y sin el plural se colaba como bebida.
    r"\b(vinagres?|cocteles?|coctel|cocktails?|salsas?|carrilladas?|guisos?|"
    r"pates?|queso al|mostazas?|mejillones|berberechos|hielos?|caramelos?|"
    r"bombones|helados?|"
    # "Aceite de orujo de oliva" no es orujo de beber, y "espumoso" resulto
    # ser un limpiador facial: los dos salieron al medir.
    r"aceite de orujo|limpiadores?|geles?|gel|cremas?|pasas|mostos?|"
    r"malta maltin)\b",
    re.IGNORECASE)

# Categorias de la cadena que son, enteras, de bebida alcoholica.
_CATEGORIAS = re.compile(
    r"(bebidas?[\-\s]alcoholica|vinos|cervezas?|licores|espirituos|bodega|"
    r"destilados|vinoteca)", re.IGNORECASE)


def _plano(texto) -> str:
    sin = "".join(c for c in unicodedata.normalize("NFD", str(texto or ""))
                  if unicodedata.category(c) != "Mn")
    return sin.lower()


def deduce(nombre, categoria=None, grado=None) -> bool:
    """Si creemos que lleva alcohol, por el nombre, la categoria o el grado."""
    if grado is not None:
        try:
            return float(grado) > 0.5
        except (TypeError, ValueError):
            pass
    t = _plano(nombre)
    if _SIN.search(t):
        return False
    if _COMIDA.search(t):
        return False
    return bool(_BEBIDAS.search(t)) or bool(_CATEGORIAS.search(_plano(categoria)))
