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
from pathlib import Path

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
        # *** DESCONOCIDO NO ES FALSO. ***
        # *La version anterior hacia `bool(par["cierto"])`, y `bool(None)` es `False`: una etiqueta
        # **desconocida** se contaba como «no son el mismo producto», asi que si el motor decia
        # «exacto» se apuntaba un **falso exacto que no existia**.* *Y al reves: un desconocido no
        # entra en el `cierto`, asi que el recall tampoco lo contaba.*
        # *Ahora solo se acepta un booleano de verdad. Cualquier otra cosa -- `None`, 0/1, "", la
        # cadena `"False"` -- se rechaza en vez de convertirse en una etiqueta que nadie puso.*
        cierto = _etiqueta_estricta(par.get("cierto"), par)
        estrato = str(par.get("estrato") or "(sin estrato)")

        dice_igual = estado in _DICE_IGUAL
        no_se_moja = estado in _NO_SE_MOJA

        for destino in (global_, por_estrato[estrato]):
            destino["total"] += 1
            # *** UN DESCONOCIDO NO ENTRA EN LA MATRIZ DE ACIERTO. ***
            # *Meterlo con `cierto=False` es lo que convertia una etiqueta que nadie puso en un falso
            # exacto.* *Se cuenta en `desconocidos` y no se suma a `cierto`.*
            if cierto is None:
                destino["desconocidos"] += 1
            else:
                destino["matriz"][(estado, cierto)] += 1
            if cierto:
                destino["cierto"] += 1
            if dice_igual:
                destino["exactos"] += 1
                # *Y con un desconocido NO se apunta ni acierto ni error: se apunta que no se sabe.*
                # *Sin esto, `if cierto:` cae en el `else` cuando `cierto` es `None`, que es el mismo
                # fallo de antes un piso mas abajo.*
                if cierto is True:
                    destino["exactos_bien"] += 1
                elif cierto is False:
                    destino["exactos_mal"] += 1
                else:
                    destino["exactos_sin_etiqueta"] += 1
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


def _etiqueta_estricta(valor, par) -> bool:
    """*** Solo un booleano de verdad es una etiqueta. *** *Lo demas se rechaza.*

    *`bool(None)` es `False`, y `bool("False")` es `True`: convertir a ciegas inventa etiquetas en las
    dos direcciones.* *Una etiqueta que nadie puso no puede contar ni como acierto ni como error.*
    """
    if isinstance(valor, bool):
        return valor
    # *`None` es **el desconocido explicito**, y el contrato lo admite: «admite bool real para
    # igualdad acreditada y desconocido explicito».* *No es una etiqueta negativa: es una etiqueta que
    # no se puso, y se cuenta aparte.*
    if valor is None:
        return None
    # *Y lo ambiguo se rechaza: `bol("False")` es `True` y `bool(0)` es `False`, asi que convertir a
    # ciegas inventa etiquetas en las dos direcciones.*
    raise ValueError(
        "etiqueta no valida en el par " + str(par.get("id") or "(sin id)") + ": "
        + repr(valor) + ". Se admite True, False o None (desconocido); no cadenas ni numeros."
    )


def _cuenta() -> dict:
    return {"total": 0, "cierto": 0, "exactos": 0, "exactos_bien": 0, "exactos_mal": 0,
            "abstiene": 0, "desconocidos": 0, "exactos_sin_etiqueta": 0, "matriz": defaultdict(int)}


def _cierra(c: dict) -> dict:
    total = c["total"]
    return {
        "total": total,
        "cierto": c["cierto"],
        # *`None` y no `0.0` cuando no dijo ninguno: no es que acierte el 0 %, es que no opino.*
        # *** LA PRECISION ES SOBRE LOS EVALUABLES, NO SOBRE TODAS LAS PREDICCIONES. ***
        # *Dividir por `exactos` metia en el denominador los pares que **no tienen etiqueta**: un
        # acierto conocido mas un exacto sin etiqueta daba 0,5 cuando la precision sobre lo evaluable
        # es 1,0.* *Un par sin etiqueta no es un fallo del motor: es una pregunta que nadie ha
        # contestado, y no puede diluir la precision.*
        "precision": (
            c["exactos_bien"] / (c["exactos_bien"] + c["exactos_mal"])
            if (c["exactos_bien"] + c["exactos_mal"]) else None
        ),
        # *Las tres cifras por separado, que es lo que hace legible la de arriba.*
        "predicciones": c["exactos"],
        "evaluables": c["exactos_bien"] + c["exactos_mal"],
        "recall": (c["exactos_bien"] / c["cierto"]) if c["cierto"] else None,
        "exactos": c["exactos"],
        "exactos_bien": c["exactos_bien"],
        "exactos_mal": c["exactos_mal"],
        # *Dijo «exacto» sobre pares que nadie etiqueto. No es un acierto ni un fallo: es una
        # pregunta sin contestar, y se cuenta para que no desaparezca.*
        "exactos_sin_etiqueta": c["exactos_sin_etiqueta"],
        "abstiene": c["abstiene"],
        # *Cuantas etiquetas no se pusieron. Va aparte de la abtencion del motor: una es del banco y
        # otra del que decide.*
        "desconocidos": c["desconocidos"],
        "cobertura_anotacion": ((total - c["desconocidos"]) / total) if total else None,
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
    evaluables = c["exactos_bien"] + c["exactos_mal"]
    if evaluables == 0:
        # *Sin pares con etiqueta conocida no hay precision que leer, aunque haya predicciones.*
        if c["exactos"]:
            return {"vale": False,
                    "motivo": (str(c["exactos"]) + " predicciones y ninguna con etiqueta conocida: "
                               "la precision no se puede leer")}
        return {"vale": False,
                "motivo": "no dijo «exacto» ni una vez: la precision no es 0, es que no hay"}
    cobertura = (c["total"] - c["abstiene"]) / c["total"]
    if cobertura < 0.1:
        return {"vale": False,
                "motivo": f"se abstiene en el {100 * (1 - cobertura):.0f} % de los pares: "
                          "no clasificarlo todo como desconocido"}
    return {"vale": True, "motivo": "hay decisiones y cobertura suficiente para leer la precision"}


def carga(ruta) -> list[dict]:
    """*** Lee el banco de pares y lo convierte en lo que `mide()` espera. ***

    *El fichero lo escribe `scripts/construye_banco_identidad.py`: **una linea JSON por par**, con los
    datos de las dos fichas, la relacion anotada, la evidencia, el autor y la fecha.*

    *Se valida al leer, y **se rechaza lo ambiguo**: `cierto` tiene que ser `True`, `False` o `None`, y
    nada mas.* *Un banco que se lee a ciegas convierte un `"False"` en un acierto sin que nadie lo vea.*
    """
    import json

    pares: list[dict] = []
    for numero, linea in enumerate(Path(ruta).read_text(encoding="utf-8").splitlines(), start=1):
        if not linea.strip():
            continue
        datos = json.loads(linea)
        for lado in ("a", "b"):
            ficha = datos.get(lado) or {}
            if not ficha.get("fuente") or not ficha.get("id_fuente"):
                raise ValueError(f"par {numero}: al lado {lado} le falta fuente o id_fuente")
        cierto = datos.get("cierto")
        if cierto is not None and not isinstance(cierto, bool):
            raise ValueError(f"par {numero}: `cierto` no es booleano ni None: {cierto!r}")
        pares.append({
            "id": f"{datos['a']['fuente']}:{datos['a']['id_fuente']}"
                  f"|{datos['b']['fuente']}:{datos['b']['id_fuente']}",
            "a": identidad.Producto(
                fuente=datos["a"]["fuente"], id_fuente=datos["a"]["id_fuente"],
                nombre=datos["a"].get("nombre"), marca=datos["a"].get("marca"),
                gtin=datos["a"].get("ean")),
            "b": identidad.Producto(
                fuente=datos["b"]["fuente"], id_fuente=datos["b"]["id_fuente"],
                nombre=datos["b"].get("nombre"), marca=datos["b"].get("marca"),
                gtin=datos["b"].get("ean")),
            "cierto": cierto,
            "estrato": datos.get("estrato"),
            "quien": datos.get("autor"),
        })
    return pares


def informe(medida: dict) -> str:
    """*La medida en palabras, con lo que la spec pide publicado y nada mas.*

    *Se publican **cuatro** cosas juntas, y nunca la precision sola: predicciones, evaluables,
    sin etiqueta y abstencion del motor.* *Una precision sin cobertura no dice nada.*
    """
    g = medida["global"]
    def pct(valor, dec=1):
        return "-" if valor is None else str(round(100 * valor, dec)) + " %"

    lineas = [
        "pares: " + str(g["total"])
        + "  (evaluables " + str(g["evaluables"])
        + ", sin etiqueta " + str(g["exactos_sin_etiqueta"]) + " de las predicciones"
        + ", desconocidos en el banco " + str(g["desconocidos"]) + ")",
        "precision: " + pct(g["precision"]) + "   recall: " + pct(g["recall"]),
        "exactos: " + str(g["exactos"]) + "   bien " + str(g["exactos_bien"])
        + "   MAL " + str(g["exactos_mal"]) + "   abstiene: " + str(g["abstiene"]),
        "cobertura del motor: " + pct(g["cobertura"])
        + "   cobertura de anotacion: " + pct(g["cobertura_anotacion"]),
        "sirve: " + str(medida["sirve"]["vale"]) + " -- " + medida["sirve"]["motivo"],
        "",
        "  por estrato (solo los que tienen pares):",
    ]
    for nombre, e in medida["por_estrato"].items():
        prec = pct(e["precision"], 0)
        lineas.append(
            "    " + nombre.ljust(26) + str(e["total"]).rjust(3) + " pares"
            + "  precision " + prec.rjust(5)
            + "  exactos " + str(e["exactos"]).rjust(3)
            + "  mal " + str(e["exactos_mal"]).rjust(2)
            + "  abstiene " + str(e["abstiene"]).rjust(3)
        )
    return "\n".join(lineas)
