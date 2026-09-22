"""Lee la mecanica de una oferta escrita en castellano de folleto.

Para que sirve
--------------
Una oferta no es un precio: es una **regla sobre cuantas unidades compras**. "2a
unidad -50%" no abarata el producto, abarata el par. Mientras la promocion sea
una cadena de texto, el calculo de "donde sale mas barata la lista" no puede
tenerla en cuenta y da un resultado peor que el real.

Esto convierte el texto en algo con lo que se puede multiplicar:

    >>> lee("2a unidad -50%").coste(2, 100)
    150
    >>> lee("3x2").coste(3, 100)
    200

Medido el 16 de septiembre sobre lo que publican las cadenas: 3.045 productos de
Alcampo con texto de promocion y 97 de cada 60 ficheros de Carrefour. Las
mecanicas de abajo cubren la gran mayoria; lo que no encaja se queda en
`Mecanica.SIN_REGLA` y se trata como si no hubiera oferta, que es el error
seguro.

Ampliado el 17 de septiembre, al aparecer el texto de oferta de DIA (221
productos, que antes no teniamos). De esos 221, las reglas de entonces solo
entendian la mitad; las dos formas que faltaban eran suyas:

    "SOLO 2,59 EUR ACTIVIA PERA"   el precio final de la unidad, no un descuento
    "25% DTO CERVEZA MAHOU"        el porcentaje escrito sin el signo menos

Con ellas se entiende el 91 % de lo que escribe DIA.

Lo que NO hace, a proposito
---------------------------
No aplica descuentos de tarjeta de fidelizacion ("Club Alcampo 15 % dto acum en
tu tarjeta"). Se reconocen y se marcan como `acumulable`, pero no bajan el precio
del calculo: ese dinero no se descuenta en caja, se acumula en un monedero. Un
comparador que lo reste esta mintiendo sobre lo que vas a pagar hoy.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date


def _limpio(texto: str) -> str:
    # El indicador ordinal ("2a" escrito con el simbolo) no es un acento: NFD no
    # lo descompone y "2a unidad" no casaba con nada. Se traduce a mano, que es
    # justo el caso mas frecuente de todos.
    texto = texto.replace("\u00aa", "a").replace("\u00ba", "o")
    sin = "".join(c for c in unicodedata.normalize("NFD", texto)
                  if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sin).strip().lower()


# Se prueban en orden: la primera que encaje manda.
_NxM = re.compile(r"\b(\d+)\s*x\s*(\d+)\b")
_SEGUNDA = re.compile(r"\b([2-9])[ao]?\s*(?:unidad|ud)\b[^%]{0,12}?(\d{1,3})\s*%")
_PORCENTAJE = re.compile(r"-\s*(\d{1,3})\s*%")
_UMBRAL = re.compile(r"(\d{1,3})\s*(?:eur|euros|€)\s*(?:de\s*)?dto\.?\s*"
                     r"compr\w*\s*(\d{1,4})\s*(?:eur|euros|€)")
# "Todo a 1 EUR", pero tambien la forma que usa DIA en la mitad de sus ofertas:
# "SOLO 2,59 EUR ACTIVIA PERA", "SOLO A 1,29 EU LECHE CALCIO", "CAMPAÑA VERANO %
# MAS BARATO PRECIO FINAL 4,59". Las tres dicen lo mismo: mientras dure la
# oferta, cada unidad cuesta eso.
#
# Dos patrones y no uno, por una razon concreta: con decimales la moneda puede
# faltar ("PRECIO FINAL 4,59"), pero con un entero **hay que exigirla**, o
# "SOLO 3 UNIDADES POR CLIENTE" se leeria como "cada unidad a 3 EUR".
# "precio" suelto entra, pero no cuando lo siguen "por kilo", "por litro" o
# "por unidad": eso es un precio de referencia, no una oferta.
_ANUNCIO = (r"(?:todo a|solo\s*a|solo|precio final|precio unico|precio especial"
            r"|precio(?!\s*(?:por|kilo|litro|unidad|ud)))")
_PRECIO_FIJO = re.compile(rf"\b{_ANUNCIO}\s*(\d{{1,3}})[.,](\d{{1,2}})\s*(?:eur|euros|€|eu)?\b")
# Sin \b al final: el simbolo del euro no es un caracter de palabra, asi que
# "Todo a 1€ (14/09/2026 - 08/10/2026)" no casaba y Alcampo perdia 1.701 ofertas.
_PRECIO_FIJO_ENTERO = re.compile(rf"\b{_ANUNCIO}\s*(\d{{1,3}})\s*(?:eur|euros|€)")

# El porcentaje escrito sin signo, que es como lo escribe DIA: "25% DTO CERVEZA
# MAHOU". Se exige la palabra (dto, descuento, rebaja) para no confundirlo con
# un "0,0 %" del nombre del producto ni con un "12 X 22 CL" de formato.
_PORCENTAJE_DTO = re.compile(
    r"(\d{1,3})\s*%\s*(?:de\s*)?(?:dto|descuento|desc|rebaja|en cupon|en vale|"
    r"en tarjeta|acum)")

# "5€ dto.": un descuento en euros sobre la unidad, no un porcentaje.
_DESCUENTO_FIJO = re.compile(r"\b(\d{1,3})(?:[.,](\d{1,2}))?\s*(?:eur|euros|€)\s*"
                             r"(?:de\s*)?(?:dto|descuento)")

# "2 UDS SOLO 4 EURO GALLETAS", "2 UD POR 3 EUR MINI WAFERS": el lote entero
# cuesta eso. Es la oferta de toda la vida del "dos por tres euros", y se lee
# distinto de un precio unitario: aqui hay que llevarse las dos.
_LOTE = re.compile(r"\b([2-9])\s*(?:uds?|unidades|unidad|packs?|botellas?|latas?|"
                   r"piezas?|bolsas?)\b[^0-9]{0,14}?"
                   r"(\d{1,3})(?:[.,](\d{1,2}))?\s*(?:eur|euros|euro|€)")
_ACUMULA = re.compile(r"acum|tarjeta|club|monedero|cheque|cupon|vale")

# Descuentos que solo existen comprando por internet. Medido el 19 de septiembre
# de 2026 sobre el catalogo entero: **397 promociones de Alcampo** lo dicen en su
# propio texto ("Cupon 1€ descuento. Solo Online.") y hasta hoy entraban en el
# total de la cesta como si fueran a bajar el ticket de la tienda.
#
# Y son solo las que se leen: Carrefour lo dice en `badge.description` y DIA en
# `headband_promotion`, dos campos que todavia no pedimos (backlog N17 y N18).
_SOLO_ONLINE = re.compile(
    r"exclusiv\w*\s+(?:en\s+)?online|s[oó]lo\s+online|solo\s+online|"
    r"online\s+exclusiv|exclusiva?\s+web|s[oó]lo\s+en\s+(?:la\s+)?web|"
    r"s[oó]lo\s+en\s+internet")


@dataclass(frozen=True)
class Mecanica:
    """Como se comporta el precio segun cuantas unidades lleves."""

    tipo: str
    a: int = 0
    b: int = 0
    acumulable: bool = False
    solo_online: bool = False
    texto: str = ""

    def coste(self, unidades: int, precio_cent: int) -> int:
        """Lo que pagas HOY en caja por esas unidades, en centimos."""
        if unidades <= 0 or precio_cent <= 0:
            return 0
        lleno = unidades * precio_cent
        if self.acumulable or self.solo_online or self.tipo == "sin_regla":
            return lleno
        if self.tipo == "nxm":                      # 3x2: pagas b de cada a
            grupos, sueltas = divmod(unidades, self.a)
            return grupos * self.b * precio_cent + sueltas * precio_cent
        if self.tipo == "enesima":                  # 2a unidad -50%
            grupos, sueltas = divmod(unidades, self.a)
            rebajadas = grupos                       # una por grupo completo
            enteras = unidades - rebajadas
            return round(enteras * precio_cent
                         + rebajadas * precio_cent * (100 - self.b) / 100)
        if self.tipo == "porcentaje":
            return round(lleno * (100 - self.b) / 100)
        if self.tipo == "precio_fijo":
            return unidades * self.a
        if self.tipo == "lote":                     # 2 unidades por 3 EUR
            lotes, sueltas = divmod(unidades, self.a)
            return lotes * self.b + sueltas * precio_cent
        if self.tipo == "descuento_fijo":           # 5 EUR de descuento
            # Nunca por debajo de cero: un descuento mayor que el precio no
            # significa que te paguen por llevartelo.
            return max(0, lleno - unidades * self.a)
        if self.tipo == "umbral":                   # 5 EUR dto comprando 20 EUR
            veces = lleno // (self.b * 100) if self.b else 0
            return max(0, lleno - veces * self.a * 100)
        return lleno

    @property
    def util(self) -> bool:
        """Si de verdad cambia lo que pagas HOY, en la tienda. Lo demas no resta.

        Dos clases de "oferta" quedan fuera, y por la misma razon:

            acumulable     el descuento va a la tarjeta, no al ticket
            solo_online    el descuento no existe si vas a la tienda

        Las dos se ensenan -- son informacion util -- pero ninguna se resta del
        total de una cesta que se va a comprar a pie. La comparacion entre
        cadenas tiene que poder hacerse sin ellas, porque no todo el mundo tiene
        la tarjeta ni compra por internet.
        """
        return (self.tipo != "sin_regla" and not self.acumulable
                and not self.solo_online)


SIN_REGLA = Mecanica("sin_regla")


def lee(texto: str | None) -> Mecanica:
    """El texto de la cadena -> una regla con la que se puede calcular."""
    if not texto:
        return SIN_REGLA
    t = _limpio(texto)
    acum = bool(_ACUMULA.search(t))
    online = bool(_SOLO_ONLINE.search(t))

    # El lote va antes del precio unitario: "2 UD POR 3 EUR" contiene un
    # "3 EUR" que el otro patron leeria como precio de una unidad.
    if m := _LOTE.search(t):
        cent = int(m.group(2)) * 100 + int((m.group(3) or "0").ljust(2, "0"))
        return Mecanica("lote", a=int(m.group(1)), b=cent,
                        acumulable=acum, solo_online=online, texto=texto)

    if m := _PRECIO_FIJO.search(t):
        euros, cent = int(m.group(1)), int((m.group(2) or "0").ljust(2, "0"))
        return Mecanica("precio_fijo", a=euros * 100 + cent,
                        acumulable=acum, solo_online=online, texto=texto)

    if m := _PRECIO_FIJO_ENTERO.search(t):
        return Mecanica("precio_fijo", a=int(m.group(1)) * 100,
                        acumulable=acum, solo_online=online, texto=texto)

    if m := _UMBRAL.search(t):
        return Mecanica("umbral", a=int(m.group(1)), b=int(m.group(2)),
                        acumulable=acum, solo_online=online, texto=texto)

    # "2a unidad -50%" antes que el porcentaje suelto, que si no se come el 50.
    if m := _SEGUNDA.search(t):
        return Mecanica("enesima", a=int(m.group(1)), b=int(m.group(2)),
                        acumulable=acum, solo_online=online, texto=texto)

    if m := _NxM.search(t):
        a, b = int(m.group(1)), int(m.group(2))
        if a > b > 0 and a <= 12:
            return Mecanica("nxm", a=a, b=b, acumulable=acum, solo_online=online, texto=texto)

    if m := _DESCUENTO_FIJO.search(t):
        cent = int(m.group(1)) * 100 + int((m.group(2) or "0").ljust(2, "0"))
        return Mecanica("descuento_fijo", a=cent, acumulable=acum, solo_online=online, texto=texto)

    for patron in (_PORCENTAJE, _PORCENTAJE_DTO):
        if m := patron.search(t):
            p = int(m.group(1))
            if 0 < p < 100:
                return Mecanica("porcentaje", b=p, acumulable=acum, solo_online=online, texto=texto)

    return Mecanica("sin_regla", acumulable=acum, solo_online=online, texto=texto)


# La ventana de validez, que las cadenas meten en el propio texto de la oferta:
#
#   Alcampo    "Producto en Folleto (10/09/26_23/09/26)"
#              "Todo a 1€ (14/09/2026 - 08/10/2026)"
#              "Ofertones de la Semana, del 15/09/2026 al 17/09/2026"
#   Carrefour  "Valido hasta el 21/09/2026"
#
# De aqui sale el `promo_hasta` de Alcampo, que hasta hoy era 0 %: 3.125
# productos con texto de oferta y ninguno con fecha de fin, porque la fecha
# estaba dentro del texto.
# Sin \b, con miradas: el guion bajo ES un caracter de palabra, asi que
# "(10/09/26_23/09/26)" -- que es literalmente como Alcampo separa las dos
# fechas -- no casaba ninguna de las dos. Mismo tropiezo que con el simbolo del
# euro: \b no sirve para delimitar numeros pegados a puntuacion.
_FECHA = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2,4})(?!\d)")


def fechas(texto: str | None) -> tuple[date | None, date | None]:
    """(desde, hasta) si el texto de la oferta lleva fechas dentro.

    Con una sola fecha se asume que es el final, que es lo que interesa y lo
    que casi siempre significa ("valido hasta el 21/09"). Con dos o mas, la
    primera y la ultima.
    """
    if not texto:
        return None, None
    halladas = []
    for d, m, a in _FECHA.findall(texto):
        anio = int(a)
        if anio < 100:
            anio += 2000
        try:
            halladas.append(date(anio, int(m), int(d)))
        except ValueError:
            continue          # 32/13/26 y demas erratas de folleto
    if not halladas:
        return None, None
    if len(halladas) == 1:
        return None, halladas[0]
    return min(halladas), max(halladas)


def unidades_optimas(mecanica: Mecanica, quiero: int, tope: int = 4) -> int:
    """Cuantas unidades salen a mejor precio por unidad, sin pasarse.

    Una oferta de "3x2" cuando solo necesitas dos te invita a llevarte tres. A
    veces compensa y a veces es comprar de mas: aqui solo se dice cuantas
    unidades bajan el precio unitario, y la interfaz decide si lo sugiere.
    `tope` evita proponer una carretilla por ahorrar treinta centimos.
    """
    if not mecanica.util or quiero <= 0:
        return quiero
    mejor, mejor_unitario = quiero, mecanica.coste(quiero, 1000) / quiero
    for n in range(quiero + 1, min(quiero + tope, 24) + 1):
        unitario = mecanica.coste(n, 1000) / n
        if unitario < mejor_unitario - 1e-9:
            mejor, mejor_unitario = n, unitario
    return mejor
