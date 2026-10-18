"""*** LA MEDIDA DEL BANCO DE IDENTIDAD: precision, recall, abstencion y matriz por estrato. ***

*M07 lo pide con estas palabras:*

> «Banco etiquetado de al menos 200 pares estratificados por cadenas/categorias, incluyendo dificiles
> y desconocidos, con procedencia de etiqueta. Separar ajuste y evaluacion; publicar precision, recall,
> abstencion y matriz de confusion por estrato. **Prioridad a evitar falsos exactos**; no pasar
> clasificandolo todo como desconocido.»

*Este modulo es **la medida**, no el banco.* *El banco son pares etiquetados por una persona o por un
agente con procedencia declarada; aqui se leen y se cuenta que hace `identidad.decide()` con ellos.*

**Las dos cifras que importan, y por que:**

  - **falso exacto** ... *dos productos distintos dados por el mismo.* *Es el error caro: hace que una
    lista diga que ya tienes algo que no tienes, o que dos precios se comparen como si fueran el
    mismo.* *La especificacion pide **prioridad a evitarlo**, asi que se cuenta aparte y no se diluye
    en una precision media.*
  - **abstencion** ... *decir «no lo se».* *No es un fallo: es lo que se enseña cuando no se sabe.*
    *Pero la especificacion tambien dice «no pasar clasificandolo todo como desconocido», asi que la
    abstencion se publica **junto** a la cobertura, nunca sola: un banco con el 100 % de abstencion
    tiene precision perfecta y no sirve para nada.*

**Y por estrato.** *Una media sola esconde justo lo que importa: un banco puede acertar el 95 % porque
casi todos los pares son faciles.* *Por eso la matriz va por estrato -- cadena y categoria -- y se
publica entera.*
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from core import identidad

# *Los estados de `decide()` que cuentan como «digo que son el mismo».* *`PROBABLE` **no** entra: no es
# una afirmacion, es una sugerencia, y meterla aqui convertiria la precision en una media de dos cosas
# distintas.*
_DICE_IGUAL = {identidad.EXACTO}
# *Los que cuentan como «no me mojo».* *La cuarentena es una abtencion con motivo -- algo no cuadra --
# y por eso entra aqui y no en el acierto.*
_NO_SE_MOJA = {identidad.ABSTIENE, identidad.CUARENTENA}


def mide(pares: Iterable[dict]) -> dict:
    """*Cuenta lo que hace `decide()` con una lista de pares etiquetados.*

    Cada par es un `dict` con:

        a, b ....... fichas (`identidad.Producto`)
        cierto ..... `True` si son el mismo producto, `False` si no
        estrato .... texto libre para agrupar («alcampo/bebida», «dia/drogueria»...)
        quien ...... quien puso la etiqueta (procedencia, que la spec exige)

    Devuelve, **global y por estrato**:

        exactos ............ cuantos dijo «mismo» (el numerador de la precision)
        exactos_bien ....... de esos, cuantos eran de verdad el mismo
        exactos_mal ........ *** los falsos exactos: el error caro ***
        precision .......... exactos_bien / exactos (o `None` si no dijo ninguno)
        recall ............. exactos_bien / todos los que SI son el mismo
        abstiene ........... cuantos no se mojaron
        cobertura .......... 1 - abstiene/total, que es lo que falta para que la precision signifique
        matriz ............. {(dijo, era): cuantos}
    """
    global_ = _cuenta()
    por_estrato: dict[str, dict] = defaultdict(_cuenta)
    procedencias: dict[str, int] = defaultdict(int)

    for par in pares:
        veredicto = identidad.decide(par["a"], par["b"])
        estado = veredicto["estado"]
        cierto = bool(par["cierto"])
        estrato = str(par.get("estrato") or "(sin estrato)")

        dice_igual = estado in _DICE_IGUAL
        no_se_moja = estado in _NO_SE_MOJA

        for destino in (global_, por_estrato[estrato]):
            destino["total"] += 1
            destino["matriz"][(estado, cierto)] += 1
            if cierto:
                destino["cierto"] += 1
            if dice_igual:
                destino["exactos"] += 1
                if cierto:
                    destino["exactos_bien"] += 1
                else:
                    destino["exactos_mal"] += 1
            if no_se_moja:
                destino["abstiene"] += 1

        procedencias[str(par.get("quien") or "(sin procedencia)")] += 1

    return {
        "global": _cierra(global_),
        "por_estrato": {k: _cierra(v) for k, v in sorted(por_estrato.items())},
        "procedencias": dict(sorted(procedencias.items())),
        # *** Y el aviso que la spec pide: si todo es cuarentena, la precision no vale nada. ***
        "sirve": _sirve(global_),
    }


def _cuenta() -> dict:
    return {"total": 0, "cierto": 0, "exactos": 0, "exactos_bien": 0, "exactos_mal": 0,
            "abstiene": 0, "matriz": defaultdict(int)}


def _cierra(c: dict) -> dict:
    total = c["total"]
    return {
        "total": total,
        "cierto": c["cierto"],
        # *`None` y no `0.0` cuando no dijo ninguno: no es que acierte el 0 %, es que no opino.*
        "precision": (c["exactos_bien"] / c["exactos"]) if c["exactos"] else None,
        "recall": (c["exactos_bien"] / c["cierto"]) if c["cierto"] else None,
        "exactos": c["exactos"],
        "exactos_bien": c["exactos_bien"],
        "exactos_mal": c["exactos_mal"],
        "abstiene": c["abstiene"],
        "cobertura": (total - c["abstiene"]) / total if total else None,
        "matriz": {f"{k[0]}|{k[1]}": v for k, v in sorted(c["matriz"].items())},
    }


def _sirve(c: dict) -> dict:
    """*Si la medida dice algo, y por que no, cuando no.*

    *Una precision perfecta sobre cero decisiones es una cifra vacia.* *Esto lo dice en palabras para
    que nadie la publique sola.*
    """
    if c["total"] == 0:
        return {"vale": False, "motivo": "el banco esta vacio"}
    if c["exactos"] == 0:
        return {"vale": False,
                "motivo": "no dijo «exacto» ni una vez: la precision no es 0, es que no hay"}
    cobertura = (c["total"] - c["abstiene"]) / c["total"]
    if cobertura < 0.1:
        return {"vale": False,
                "motivo": f"se abstiene en el {100 * (1 - cobertura):.0f} % de los pares: "
                          "no clasificarlo todo como desconocido"}
    return {"vale": True, "motivo": "hay decisiones y cobertura suficiente para leer la precision"}
