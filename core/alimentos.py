"""**Que parte del catalogo es comida**, y que parte no.

**Por que existe.** *El capitulo 18 del material mide la cobertura de nutricion y da un 21,6 por ciento.*
**Y ese numero no se puede juzgar sin saber de que se esta hablando**: *si una cuarta parte del catalogo es
lejia, gel de ducha y comida de gato, **pedirle nutricion a eso es pedirle peras al olmo** -- y el 21,6 se
lee como una carencia cuando parte de el es una categoria que no aplica.*

> *Decir un porcentaje sin haber mirado el universo es inventarlo*, que es lo que el capitulo 18 dejo
> escrito. **Esto es mirarlo.**

**De donde sale la regla, y no de mi cabeza.** *Se midieron las **19 secciones** que trae el catalogo y lo
que aporta cada una* -- *filas, cuantas tienen `kcal_100g` y cuantas tienen `ingredientes`.* **Y la
separacion es nitida:**

    despensa              7 783 filas   2 745 kcal   1 503 ingredientes
    higiene-belleza       7 303 filas       1 kcal       0 ingredientes     <- NO
    droguería-limpieza    3 536 filas       8 kcal       0 ingredientes     <- NO
    mascotas              1 584 filas       0 kcal      65 ingredientes     <- NO
    hogar                    56 filas       0 kcal       0 ingredientes     <- NO

**Una seccion de comida tiene cientos o miles de calorias; una que no lo es tiene cero o casi cero.**
*No hay zona gris en los extremos.*

**Y las ambiguas se tratan como ambiguas.** *`promociones`, `bebe`, `parafarmacia` y `ecologico` son
**mezclas**: en `bebe` hay potitos y hay toallitas; en `parafarmacia` hay cremas y hay complementos.*
**Devolver «si» o «no» para esas seria inventar** -- *y por eso hay tres respuestas, no dos.*
"""
from __future__ import annotations

from typing import Literal

# *Las secciones que son comida, leidas de la medicion del 12 de octubre de 2026 sobre
# `v20261007-103000/grupos.parquet`.* **Todas aportan cientos o miles de calorias por seccion.**
DE_COMIDA = frozenset({
    "despensa", "desayuno-dulces", "bebidas", "lacteos-huevos", "carniceria", "panaderia",
    "frutas-verduras", "aperitivos", "congelados", "pescaderia", "preparados",
})

# *Las que no lo son.* **Las tres grandes aportan 9 calorias entre 12 479 filas** -- *o sea, ninguna.*
NO_DE_COMIDA = frozenset({
    "higiene-belleza", "droguería-limpieza", "mascotas", "hogar",
})

# **Y las que son mezcla, que se dicen y no se resuelven.** *`promociones` es un cajon donde cabe
# cualquier cosa; `bebe` tiene potitos y toallitas; `parafarmacia` tiene cremas y complementos; y
# `ecologico` es una etiqueta, no una categoria -- 211 filas y ni una caloria, lo que no prueba nada
# porque muchas cosas ecologicas son comida sin datos.*
MEZCLA = frozenset({"promociones", "bebe", "parafarmacia", "ecologico"})

# *Y las que no se sabe: `None` y las vacias.* **185 filas sin seccion.** *No se meten en ninguna de las
# otras: se cuentan aparte, que es lo unico honesto que se puede hacer con ellas.*

Respuesta = Literal["comida", "no", "mezcla", "desconocido"]


def que_es(seccion: str | None) -> Respuesta:
    """**Que es esa seccion.** *Cuatro respuestas, y ninguna es «supongo».*

    *`None` y la cadena vacia no son errores: son las 185 filas que el catalogo no clasifica.* **Y se
    contestan «desconocido», no «no»** -- *porque «no lo se» y «no es comida» son cosas distintas, que es
    la regla que este proyecto repite en todas partes.*

    La comparacion **no distingue mayusculas** y quita espacios: *el catalogo trae `droguería-limpieza` con
    tilde y `Panadería y pastelería` con mayuscula inicial en `categoria`, y la seccion no siempre viene
    limpia.*
    """
    if seccion is None:
        return "desconocido"
    limpio = seccion.strip().lower()
    if not limpio:
        return "desconocido"
    if limpio in DE_COMIDA:
        return "comida"
    if limpio in NO_DE_COMIDA:
        return "no"
    if limpio in MEZCLA:
        return "mezcla"
    # *Una seccion que no este en ninguna lista es «desconocido», no «no».* **Clasificar por descarte
    # meteria cualquier seccion nueva en «no es comida» sin que nadie lo hubiera decidido** -- *y una
    # seccion nueva de comida desapareceria del universo sin que se notara.*
    return "desconocido"


def es_comida(seccion: str | None) -> bool:
    """*Solo cuando consta.* **`mezcla` y `desconocido` no son comida** -- *y por eso `es_comida` es
    distinto de `que_es`: quien pregunte «¿es comida?» recibe un si o un no, y quien necesite saber si
    **se sabe** pregunta `que_es`.*"""
    return que_es(seccion) == "comida"


def cobertura_sobre_comida(con_dato: int, de_comida: int, de_mezcla: int = 0) -> dict:
    """**El porcentaje de nutricion medido sobre la comida, con sus dos limites.**

    *`de_mezcla` existe porque las secciones mezcladas no se pueden contar enteras ni ignorar enteras:*
    **si resultara que todas fueran comida, el universo seria el mayor; y si ninguna lo fuera, el
    menor.** *Asi que se dan los dos limites, y el de arriba es el que se suele querer* -- *porque
    `promociones` a secas no es una seccion de comida.*

    *Devolver un solo numero seria elegir uno de los dos sin decirlo.*
    """
    if de_comida <= 0:
        return {"comida": 0, "con_dato": con_dato, "suelo": 0.0, "techo": 0.0,
                "motivo": "no hay filas de comida clasificadas"}
    suelo = 100.0 * con_dato / (de_comida + de_mezcla) if (de_comida + de_mezcla) else 0.0
    techo = 100.0 * con_dato / de_comida
    return {"comida": de_comida, "con_dato": con_dato, "suelo": suelo, "techo": techo}
