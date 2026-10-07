"""Identidad exacta: cuando dos fichas son el mismo producto, y cuando no se puede afirmar.

**El problema que resuelve, y por que importa mas que casi nada.** Hoy el proyecto empareja productos
entre cadenas por parecido de nombre y por codigo, y de ahi salen grupos que mezclan cosas distintas:
de los grupos multi-cadena medidos, **2.276 agrupan productos con EAN distinto**. Un grupo asi hace
que la comparacion *parezca* exacta y no lo sea, y la regla del encargo es tajante: **elegir un
producto concreto no autoriza a sustituirlo por otro mas barato**. Este modulo decide, y cuando no
puede decidir, **se abstiene** -- que es un resultado valido y no un fallo.

**Las decisiones del contrato de SUPERAPP-02 seccion 6, una a una, y por que:**

  - **El GTIN se valida, no se copia.** Es la via fuerte: mismo GTIN valido y presentacion compatible
    es identidad. Un GTIN de 13 digitos con digito de control correcto *no basta* por si solo: hay que
    comprobar ademas que la presentacion cuadra.
  - **Mismo GTIN con presentacion incompatible va a cuarentena**, no a identidad ni a alternativa
    silenciosa: o el codigo esta mal en alguna de las dos fichas, o una de las dos miente.
  - **GTIN distinto no se fusiona por texto, nunca.** Podrian ser el mismo producto reformulado, pero
    eso es una **excepcion con evidencia comercial**, y aqui no hay ninguna: como mucho seran
    **alternativas**, y elegir una es cosa del usuario.
  - **Sin GTIN no hay identidad exacta.** Marca, nombre y formato compatibles dan **probable**, que es
    una hipotesis util para proponer, no una afirmacion para comparar precios.
  - **Sin cierre transitivo.** Que A se parezca a B y B a C **no** hace que A y C sean lo mismo: un
    grupo se amplia solo si el candidato es compatible con **todos** sus miembros.
  - **Los atributos no se tiran.** "Sin lactosa", el sabor, el corte o el pack no son palabras vacias:
    cambian el producto. Aqui se leen la cantidad, la unidad y el numero de envases, que son los que
    mas se confunden al comparar precios.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

EXACTO = "exacto"
PROBABLE = "probable"
ALTERNATIVA = "alternativa"
CUARENTENA = "cuarentena"
ABSTIENE = "abstiene"

# Unidades y su equivalente canonico. `l` y `kg` se pasan a mililitros y gramos para poder comparar
# 1 l con 1000 ml, que es la misma cosa escrita de dos maneras.
_UNIDADES = {
    "kg": ("g", 1000.0), "kilo": ("g", 1000.0), "kilos": ("g", 1000.0),
    "g": ("g", 1.0), "gr": ("g", 1.0), "gramos": ("g", 1.0), "gramo": ("g", 1.0),
    "l": ("ml", 1000.0), "litro": ("ml", 1000.0), "litros": ("ml", 1000.0),
    "ml": ("ml", 1.0), "cl": ("ml", 10.0), "cc": ("ml", 1.0),
    "ud": ("ud", 1.0), "uds": ("ud", 1.0), "unidad": ("ud", 1.0), "unidades": ("ud", 1.0),
}

RE_CANTIDAD = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(kg|kilos?|gramos?|gr|g|litros?|l|ml|cl|cc|uds?|unidades?)\b", re.I)
RE_PACK = re.compile(r"(?:(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?))|(?:pack\s*(?:de\s*)?(\d+))", re.I)


def _numero(texto: str) -> float:
    return float(texto.replace(",", "."))


def normaliza_gtin(codigo: object) -> str | None:
    """El GTIN en forma canonica si es valido; None si no.

    Se aceptan 8, 12, 13 y 14 digitos. El de 14 que empieza por cero es el mismo que el de 13 (el
    cero es relleno), asi que se recorta. El digito de control se **calcula**: es lo unico que
    distingue un codigo de barras de una cadena de digitos que se le parece.
    """
    digitos = re.sub(r"\D", "", str(codigo or ""))
    if len(digitos) == 14 and digitos.startswith("0"):
        digitos = digitos[1:]
    if len(digitos) not in (8, 12, 13):
        return None
    cuerpo, control = digitos[:-1], int(digitos[-1])
    suma = 0
    for posicion, digito in enumerate(reversed(cuerpo)):
        suma += int(digito) * (3 if posicion % 2 == 0 else 1)
    return digitos if (10 - suma % 10) % 10 == control else None


def atributos(nombre: str | None) -> dict:
    """Lo que el titulo dice de la presentacion: cantidad, unidad y envases.

    Se lee del nombre porque es lo unico que traen todas las cadenas; cuando la ficha traiga el dato
    estructurado, se preferira ese y esto quedara como respaldo.
    """
    texto = nombre or ""
    cantidad = unidad = None
    encontrado = RE_CANTIDAD.search(texto)
    if encontrado:
        clave = encontrado.group(2).lower()
        # Se prueban las dos formas -- "litros" y "litro" -- porque el diccionario tiene ambas, y
        # recortar la "s" a secas convertiria "unidades" en "unidade", que no existe.
        canonica, factor = _UNIDADES.get(clave) or _UNIDADES.get(clave.rstrip("s")) or (None, None)
        if canonica:
            cantidad = round(_numero(encontrado.group(1)) * factor, 3)
            unidad = canonica
    pack = None
    envases = RE_PACK.search(texto)
    if envases:
        pack = int(envases.group(1) or envases.group(3) or 1)
    return {"cantidad": cantidad, "unidad": unidad, "envases": pack,
            "texto": " ".join(texto.lower().split())}


@dataclass
class Producto:
    """Lo minimo para decidir identidad: quien es, de donde y como viene presentado."""

    fuente: str
    id_fuente: str
    nombre: str | None = None
    marca: str | None = None
    gtin: str | None = None
    familia: str | None = None
    atributos: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.atributos:
            self.atributos = atributos(self.nombre)
        # El GTIN se normaliza al entrar: asi nadie decide con un codigo sin validar.
        self.gtin = normaliza_gtin(self.gtin)

    @property
    def marca_normalizada(self) -> str:
        return " ".join((self.marca or "").lower().split())


def _presentacion(a: Producto, b: Producto) -> tuple[bool, list[str]]:
    """Si las dos presentaciones son compatibles, y por que no lo son si no lo son."""
    motivos = []
    ca, cb = a.atributos.get("cantidad"), b.atributos.get("cantidad")
    ua, ub = a.atributos.get("unidad"), b.atributos.get("unidad")
    if ua and ub and ua != ub:
        # Gramos contra mililitros no se comparan sin densidad documentada: no es contradiccion,
        # es que no se sabe. Y "no se sabe" no puede acabar en identidad.
        motivos.append(f"unidad no comparable ({ua} y {ub})")
    elif ca is not None and cb is not None and abs(ca - cb) > max(ca, cb) * 0.02:
        motivos.append(f"cantidad distinta ({ca:g} {ua} y {cb:g} {ub})")
    # Un titulo sin envases se lee como uno: casi todo se vende de uno en uno. Asi, un pack
    # declarado frente a un titulo sin pack es una diferencia real y no un hueco de informacion.
    pa, pb = a.atributos.get("envases") or 1, b.atributos.get("envases") or 1
    if pa != pb:
        motivos.append(f"envases distintos ({pa} y {pb})")
    return (not motivos), motivos


def _no_comparable(motivos: list[str]) -> bool:
    return any("no comparable" in m for m in motivos)


def decide(a: Producto, b: Producto) -> dict:
    """El veredicto entre dos fichas, con su evidencia. Nunca "exacto" sin GTIN valido.

    Devuelve `estado`, `motivos` y `evidencia`, para que la interfaz pueda explicar la decision en
    lugar de pedir confianza. La abtencion es un resultado: es lo que se enseña cuando no se sabe.
    """
    compatible, motivos = _presentacion(a, b)
    evidencia = {"gtin_a": a.gtin, "gtin_b": b.gtin,
                 "marca_a": a.marca_normalizada, "marca_b": b.marca_normalizada,
                 "presentacion": {"a": a.atributos, "b": b.atributos}}

    if a.gtin and b.gtin:
        if a.gtin == b.gtin:
            if compatible:
                return {"estado": EXACTO, "motivos": ["mismo GTIN valido y presentacion compatible"],
                        "evidencia": evidencia}
            return {"estado": CUARENTENA,
                    "motivos": ["mismo GTIN con presentacion incompatible", *motivos],
                    "evidencia": evidencia}
        # **GTIN distinto no se fusiona por texto.** Podran ser alternativas elegidas, nunca lo mismo.
        return {"estado": ALTERNATIVA,
                "motivos": ["GTIN distinto: no se fusiona por parecido de nombre"],
                "evidencia": evidencia}

    if not compatible and not _no_comparable(motivos):
        return {"estado": ALTERNATIVA, "motivos": ["presentacion incompatible", *motivos],
                "evidencia": evidencia}

    mismo_nombre = bool(a.atributos.get("texto")) and a.atributos["texto"] == b.atributos["texto"]
    misma_marca = bool(a.marca_normalizada) and a.marca_normalizada == b.marca_normalizada
    if _no_comparable(motivos):
        return {"estado": ABSTIENE, "motivos": ["no se puede comparar la presentacion", *motivos],
                "evidencia": evidencia}
    if mismo_nombre and (misma_marca or not a.marca_normalizada or not b.marca_normalizada):
        return {"estado": PROBABLE,
                "motivos": ["nombre y presentacion coinciden, pero falta un GTIN que lo confirme"],
                "evidencia": evidencia}
    if mismo_nombre or misma_marca:
        return {"estado": PROBABLE, "motivos": ["coincidencia parcial sin GTIN"], "evidencia": evidencia}
    # Sin GTIN, sin marca y sin nombre igual: no se sabe, y se dice.
    return {"estado": ABSTIENE, "motivos": ["sin evidencia suficiente"], "evidencia": evidencia}


def candidatos_por_gtin(productos: list[Producto]) -> dict[str, list[Producto]]:
    """Los grupos **exactos**: mismo GTIN valido. Es la unica via que autoriza a decir "el mismo"."""
    indice: dict[str, list[Producto]] = {}
    for p in productos:
        if p.gtin:
            indice.setdefault(p.gtin, []).append(p)
    return {g: miembros for g, miembros in indice.items() if len(miembros) > 1}


def candidatos_por_bloque(productos: list[Producto]) -> dict[tuple, list[Producto]]:
    """Los **probables**: misma marca, misma familia y misma presentacion, sin GTIN que confirme.

    No son identidad: son candidatos para proponer y para que alguien decida. Se separan de los
    exactos a proposito, porque juntarlos es exactamente el error que este paquete persigue.
    """
    bloque: dict[tuple, list[Producto]] = {}
    for p in productos:
        if p.gtin or not p.marca_normalizada or not p.familia:
            continue
        clave = (p.marca_normalizada, p.familia, p.atributos.get("cantidad"),
                 p.atributos.get("unidad"), p.atributos.get("envases") or 1)
        bloque.setdefault(clave, []).append(p)
    return {c: miembros for c, miembros in bloque.items() if len(miembros) > 1}


class Cuarentena(RuntimeError):
    """Un grupo que no se puede ampliar sin romper la regla de identidad."""


def ampliar_grupo(grupo: list[Producto], candidato: Producto) -> list[Producto]:
    """Anade al grupo **solo si es compatible con todos sus miembros**. Sin cierre transitivo.

    Es la parte que evita el error clasico: A se parece a B, B se parece a C, y acaba un grupo con A,
    B y C donde A y C no tienen nada que ver. Aqui cada ampliacion se comprueba contra el grupo
    entero, y si falla se levanta `Cuarentena` en vez de fusionar en silencio.
    """
    if not grupo:
        return [candidato]
    for miembro in grupo:
        veredicto = decide(miembro, candidato)
        if veredicto["estado"] not in (EXACTO, PROBABLE):
            raise Cuarentena(
                f"{candidato.fuente}/{candidato.id_fuente} no es compatible con "
                f"{miembro.fuente}/{miembro.id_fuente}: {'; '.join(veredicto['motivos'])}")
    return [*grupo, candidato]
