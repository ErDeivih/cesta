"""A08 — Envases enteros: cuantos hay que comprar y cuanto sobra.

**El defecto, medido el 12 de octubre de 2026, y era doble.**

`core/previa_compra.py::_tamano_del_envase` pedia el tamano del envase asi:

```python
cantidad = leido.get("cantidad") if isinstance(leido, dict) else getattr(leido, "cantidad", None)
```

*Y `core/envases.py::lee` devuelve `tuple[str | None, int | None]`* -- **(tipo de envase, unidades del
pack)** --, asi que:

1. **`isinstance(leido, dict)` es falso**, y `getattr(tupla, "cantidad", None)` da `None`.
2. **Y aunque se arreglara, seguiria dando `None`**: *`envases.lee` **nunca devolvio un tamano*** -- *lee
   «botella», «malla», «Pack-6», que son **el tipo de envase y cuantas unidades van dentro**, no cuanto
   pesa o cuanto cabe.*

**Consecuencia, y es lo que importa**: `ln.envases` y `ln.sobrante` **no se calculaban nunca**. *El
calculo de envases enteros estaba escrito, probado a medias... y muerto.*

**De donde sale el tamano, entonces.** *De **la ficha del articulo elegido**, que es quien lo publica*:
*el `tamano_envase` de la linea. **No se deduce del texto del nombre** -- *«Leche entera 1 l» se puede
leer, pero **«Leche entera» a secas no dice cuanto trae**, y ahi no se inventa nada.*

**Y la regla que pide A08, con su ejemplo**: *1,4 kg con envases de 1 kg son **dos envases** y **0,6 kg
sobrantes**.*
"""
from __future__ import annotations

import math

# Las unidades que se pueden convertir entre si. **Masa con masa, volumen con volumen.**
# *Y **no** masa con volumen: pasar de gramos a mililitros necesita la densidad, que no se publica.*
_MAGNITUD = {
    "g": ("masa", 1.0), "gr": ("masa", 1.0), "gramo": ("masa", 1.0), "gramos": ("masa", 1.0),
    "kg": ("masa", 1000.0), "kilo": ("masa", 1000.0), "kilos": ("masa", 1000.0),
    "mg": ("masa", 0.001),
    "ml": ("volumen", 1.0), "cc": ("volumen", 1.0), "cl": ("volumen", 10.0),
    "l": ("volumen", 1000.0), "litro": ("volumen", 1000.0), "litros": ("volumen", 1000.0),
    "ud": ("unidades", 1.0), "uds": ("unidades", 1.0),
    "unidad": ("unidades", 1.0), "unidades": ("unidades", 1.0),
}


def a_canonica(cantidad, unidad: str | None) -> tuple[float, str] | None:
    """Una cantidad con su unidad, en la base de su magnitud: **gramos, mililitros o unidades**.

    *Devuelve `None` si no se puede* -- *sin cantidad, sin unidad, o con una unidad que no consta.*
    **No se supone que «4» sean cuatro unidades**: *podrian ser cuatro gramos, y elegir mal aqui cambia
    los envases que hay que comprar.*
    """
    if cantidad is None or unidad is None:
        return None
    try:
        n = float(cantidad)
    except (TypeError, ValueError):
        return None
    # *Y un numero que no es un numero no pasa.* **`bool` es `int` en Python, y `True` no son 1 gramo.**
    if isinstance(cantidad, bool) or not math.isfinite(n) or n <= 0:
        return None
    magnitud = _MAGNITUD.get(str(unidad).strip().lower())
    if magnitud is None:
        return None
    familia, factor = magnitud
    return (n * factor, familia)


def envases_enteros(pedido, unidad_pedida: str | None,
                    tamano, unidad_tamano: str | None) -> dict:
    """**Cuantos envases hay que comprar y cuanto sobra.** *Es la regla de A08.*

    *`pedido` es lo que se quiere, `tamano` lo que trae un envase.* *Las dos cosas con su unidad.*

    **Los cuatro resultados posibles, y ninguno se confunde con otro:**

      - **`envases`** y **`sobrante`**: se pudo calcular. *1,4 kg con envases de 1 kg -> **2 envases, 0,6
        kg**.*
      - **`None` en los dos, `motivo` «no se sabe cuanto trae el envase»**: *la ficha no publica el
        tamano.* **No se inventa una compra fraccionaria**: *decir «1,4 envases» es decir una cosa que no
        se puede comprar.*
      - **`None` en los dos, `motivo` «no se pueden comparar»**: *masa contra volumen, o unidades contra
        masa.* *Sin densidad documentada, **no se sabe**, y eso no es lo mismo que ser igual.*
      - **`None` en los dos, `motivo` «no se sabe cuanto se quiere»**: *la linea no trae cantidad.*

    **Y `sobrante` siempre es «lo que se compra de mas», nunca negativo**: *si el pedido cabe exacto, es
    cero* -- *y cero sobrante es un dato, no un hueco.*
    """
    quiere = a_canonica(pedido, unidad_pedida)
    trae = a_canonica(tamano, unidad_tamano)

    if quiere is None:
        # *Y se distingue «no hay tamano» de «no hay pedido»: son dos huecos distintos y se arreglan en
        # sitios distintos -- uno en la ficha del articulo, el otro en la lista.*
        return {"envases": None, "sobrante": None, "unidad": None,
                "motivo": "no se sabe cuanto se quiere"}
    if trae is None:
        return {"envases": None, "sobrante": None, "unidad": None,
                "motivo": "no se sabe cuanto trae el envase"}

    cantidad_querida, familia_querida = quiere
    cantidad_por_envase, familia_envase = trae
    if familia_querida != familia_envase:
        # **Masa contra volumen no se convierte sin densidad, y las unidades no son ni una ni otra.**
        # *Decir «no se pueden comparar» es la respuesta honesta; decir un numero seria inventarlo.*
        return {"envases": None, "sobrante": None, "unidad": None,
                "motivo": f"no se pueden comparar: {familia_querida} contra {familia_envase}"}

    # **Envases enteros, hacia arriba**: *no se vende medio envase.*
    n = math.ceil(round(cantidad_querida / cantidad_por_envase, 9))
    sobra = round(n * cantidad_por_envase - cantidad_querida, 9)
    # *Y se devuelve en la unidad del envase, que es la que la persona reconoce.*
    unidad = {"masa": "g", "volumen": "ml", "unidades": "ud"}[familia_envase]
    return {"envases": n, "sobrante": sobra, "unidad": unidad, "motivo": None}
