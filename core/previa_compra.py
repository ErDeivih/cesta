"""G12, punto 221: **la previa de compra de una receta**, sin escribir nada.

G12 lo pide asi: *«Receta→lista: **previa de cantidades**, **consolidacion compatible**, distincion
g/ml/unidades y **envases enteros necesarios**. Repetir la misma transferencia no duplica; otra
semana/operacion legitima si. Descontar despensa solo si esta modelada y la persona lo elige.»*

**Esto es la previa y solo la previa.** *No escribe en ninguna lista, no toca ninguna base y no pide
nada por red.* Devuelve **que habria que comprar**, linea a linea y ya consolidada, para que la
persona lo vea antes de decidir. *Escribir es otra cosa y va despues -- y con la disciplina del 223
(dueno comprobado en el servidor) y del 227 (mutaciones protegidas).*

**Las tres reglas que aplica, y por que:**

1. **La consolidacion es por producto Y unidad.** *Dos lineas del mismo producto en kilos se suman;
   una en kilos y otra en unidades **no**, y se dice por que.* **Sumar 1 kg con 2 unidades daria un
   numero que no significa nada**, y es la clase de cifra inventada que este proyecto no escribe.
2. **Lo que no tiene cantidad no se compra.** *Un ingrediente anotado como "sal" no se puede
   convertir en una cantidad de compra.* **Es la regla que `core/recetas.py:escala` ya escribe: «lo
   que no tiene cantidad, no la gana… inventarle un cero seria convertir lo que falta en un dato
   falso».** *Aqui sale en la previa como «sin cantidad», y no se le inventa ninguna.*
3. **Los envases son enteros.** *Si hacen falta 1,4 kg y el envase es de 1 kg, hay que comprar 2.*
   **Y el sobrante se dice**, porque es informacion util: *«te sobran 600 g»* no es un error de
   calculo, es lo que pasa de verdad.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from core import normalize

# **`envases` ya no se usa aqui, y es a proposito.** *Le pedia el tamano del envase y **nunca lo tuvo**:
# devuelve (tipo de envase, unidades del pack).* **La regla vive en `envases_enteros`.**
from core.envases_enteros import envases_enteros


@dataclass
class LineaDeCompra:
    """Una linea de la previa: **lo que habria que comprar**, no lo que dice la receta."""
    clave: str                     # producto + unidad: la identidad de la consolidacion
    texto: str                     # como se lee en la receta
    producto_id: str | None
    cantidad: float
    unidad: str
    # **El grupo al que apunta el ingrediente, cuando no tiene producto exacto.** *Faltaba, y su ausencia
    # se notaba en el puente receta->lista*: `a_la_lista` pasaba `None` de `grupo_id` **siempre**, asi que
    # un ingrediente identificado **solo por grupo** llegaba a la lista sin destino -- *y la tabla exige
    # `linea_con_destino`: producto **o** grupo.*
    #
    # *Y el modulo ya decia que lo aceptaba*: su docstring nombra `producto_id`, `grupo_id` y `fuente`
    # entre lo que cada ingrediente puede traer. **Lo nombraba y no lo leia.**
    #
    # **Va aqui, despues de `unidad`, y no al lado de `producto_id`**: *un campo con valor por defecto
    # delante de uno sin el es un `TypeError` en Python* -- *y lo dijo el import, con estas palabras:
    # «non-default argument 'cantidad' follows default argument».*
    grupo_id: int | None = None
    # Los envases enteros, cuando se sabe el tamano del envase.
    envases: int | None = None
    tamano_envase: float | None = None
    # **La unidad del envase, que no es la del ingrediente.** *Una receta pide `200 g` de algo que se
    # vende en `1 l`, y ahi **no hay conversion**: se dice y se para.* *Suponer que son la misma seria
    # comparar gramos con litros sin decirlo.*
    unidad_envase: str | None = None
    sobrante: float | None = None
    de_donde: list[str] = field(default_factory=list)   # que ingredientes la formaron


@dataclass
class Previa:
    """El resultado: lo comprable, lo que no se puede y por que."""
    lineas: list[LineaDeCompra]
    sin_cantidad: list[str]              # ingredientes sin cantidad: no se compran
    sin_consolidar: list[str]            # el mismo producto en unidades incompatibles
    nota: str = ""


def _unidad_canon(unidad: str | None) -> str:
    """La unidad, dicha igual venga como venga. *Sin unidad no se consolida con nadie.*"""
    return (unidad or "").strip().lower()


def previa_de_compra(ingredientes: list[dict]) -> Previa:
    """**Que habria que comprar.** *Pura: no escribe, no consulta, no decide por nadie.*

    Cada ingrediente es lo que guarda `core/recetas.py`: `texto`, `cantidad`, `unidad`, y
    opcionalmente `producto_id`, `grupo_id`, `fuente`, y -- si la API lo enriquecio -- el precio.

    **Y el tamano del envase, cuando se sabe, viaja en `tamano_envase` y `unidad_envase`.** *Es la
    conexion que A08 pedia: **el tamano neto publicado del articulo elegido**.*
    *Antes no habia por donde entrara* -- *`cantidad` es **cuanto se necesita**, no **cuanto trae un
    envase**, y confundirlas daria un pedido de un solo envase siempre.* **Si no viene, la linea se queda
    sin calculo de envases**, *que es lo correcto: no se inventa una compra fraccionaria.*

    *La unidad del envase va aparte de la del ingrediente, y no se supone igual*: *una receta pide
    `200 g` de algo que se vende en `1 l`, y ahi **no hay conversion** -- se dice y se para.*
    """
    acumulado: dict[str, LineaDeCompra] = {}
    por_producto: dict[str, set[str]] = {}      # producto -> unidades vistas
    unidades_originales: dict[str, set[str]] = {}
    sin_cantidad: list[str] = []

    for ing in ingredientes:
        texto = str(ing.get("texto") or "").strip()
        cantidad = ing.get("cantidad")
        unidad = _unidad_canon(ing.get("unidad"))
        pid = ing.get("producto_id")
        pid = str(pid) if pid else None
        # *Y el grupo, que el docstring nombraba y el codigo no leia.* **Un ingrediente puede estar
        # identificado solo por grupo, sin producto exacto** -- *y sin esto, el puente receta->lista
        # llegaba con `None` de destino y la tabla lo rechazaba.*
        gid = ing.get("grupo_id")
        gid = int(gid) if gid is not None else None
        # **El tamano del envase, si el ingrediente lo trae.** *Un numero que no sirve se ignora en vez de
        # tumbar la previa* -- *y se guarda `None`, que es «no se sabe».*
        tamano_envase = ing.get("tamano_envase")
        if (isinstance(tamano_envase, bool) or not isinstance(tamano_envase, (int, float))
                or not math.isfinite(tamano_envase) or tamano_envase <= 0):
            tamano_envase = None
        # *Y su unidad: si no viene, se cae a la del ingrediente* -- *que es lo correcto **cuando el
        # articulo se vende en la misma unidad en la que se pide**, y lo mas frecuente.*
        unidad_envase = ing.get("unidad_envase") or ing.get("unidad")

        # **Regla 2: sin cantidad no hay compra.** *Y sin inventarla.*
        if (isinstance(cantidad, bool) or not isinstance(cantidad, (int, float))
                or not math.isfinite(cantidad) or cantidad <= 0):
            if texto:
                sin_cantidad.append(texto)
            continue
        # Y sin unidad tampoco: 3 de que. *Se dice, no se supone.*
        if not unidad:
            sin_cantidad.append(f"{texto} (sin unidad)")
            continue

        # **La clave de la consolidacion: producto si lo hay, y si no el texto.** *La unidad va
        # dentro: sumar kilos con unidades seria inventar.*
        quien = pid or texto.lower()
        # Comparar en una base comun no obliga a cambiar como se muestra una
        # linea homogenea. Solo una mezcla g/kg se presenta en kg (ml/l en l).
        canon, factor = normalize._UNIDADES.get(unidad, (unidad, 1.0))
        clave = f"{quien}|{canon}"
        por_producto.setdefault(quien, set()).add(canon)
        unidades_originales.setdefault(clave, set()).add(unidad)
        cantidad = round(cantidad * factor, 9)

        if clave in acumulado:
            ln = acumulado[clave]
            ln.cantidad += cantidad
            if texto and texto not in ln.de_donde:
                ln.de_donde.append(texto)
            # *Si la linea que ya estaba no traia tamano y esta si, se queda el que aparece* -- *y si las
            # dos traen uno distinto, **se deja en `None`**: dos tamanos para el mismo producto significa
            # que no se sabe cual vale, y elegir uno seria inventar.*
            if ln.tamano_envase is None:
                ln.tamano_envase = tamano_envase
                ln.unidad_envase = unidad_envase if tamano_envase else None
            elif tamano_envase is not None and ln.tamano_envase != tamano_envase:
                ln.tamano_envase = None
                ln.unidad_envase = None
        else:
            acumulado[clave] = LineaDeCompra(
                clave=clave, texto=texto, producto_id=pid, grupo_id=gid,
                cantidad=float(cantidad), unidad=canon, de_donde=[texto],
                tamano_envase=tamano_envase, unidad_envase=unidad_envase if tamano_envase else None)

    for clave, ln in acumulado.items():
        originales = unidades_originales[clave]
        if len(originales) == 1:
            original = next(iter(originales))
            _, factor = normalize._UNIDADES.get(original, (original, 1.0))
            ln.cantidad = round(ln.cantidad / factor, 9)
            ln.unidad = original
        else:
            ln.cantidad = round(ln.cantidad, 9)

    # **Regla 1: lo que quedo en unidades incompatibles se nombra.** *No se suma ni se elige una.*
    sin_consolidar = []
    for quien, unidades in por_producto.items():
        if len(unidades) > 1:
            nombre = next((ln.texto for ln in acumulado.values()
                           if (ln.producto_id or ln.texto.lower()) == quien), quien)
            sin_consolidar.append(f"{nombre}: {' y '.join(sorted(unidades))}")

    # **Regla 3: envases enteros.** *Y el sobrante, dicho.*
    #
    # *De donde sale el tamano*: **de `ln.tamano_envase`, que lo publica la ficha del articulo elegido**
    # -- *no del texto del nombre.* **Esto llamaba a `_tamano_del_envase(ln.texto)`, que devolvia `None`
    # siempre** (*le pedia un tamano a quien nunca lo tuvo*), **asi que ni `envases` ni `sobrante` se
    # calculaban nunca.**
    #
    # *Se saca a `_envases_de` para poder probarlo*: **el fallo duro porque no habia forma de mirarlo.**
    _envases_de(list(acumulado.values()))

    lineas = sorted(acumulado.values(), key=lambda x: (-x.cantidad, x.texto))
    nota = ""
    if sin_cantidad:
        nota = ("Lo que no tiene cantidad no se compra, y no se le inventa: "
                + ", ".join(sin_cantidad) + ".")
    return Previa(lineas=lineas, sin_cantidad=sin_cantidad,
                  sin_consolidar=sin_consolidar, nota=nota)


def _envases_de(lineas: list) -> list:
    """**Regla 3, aparte y probable**: cuantos envases enteros y cuanto sobra, linea a linea.

    *Se saco de `previa_de_compra` porque el fallo que arregla duro sin que nadie lo viera*: **la regla
    estaba escrita, se ejecutaba... y devolvia `None` siempre**, porque le pedia el tamano a
    `envases.lee`, que nunca lo tuvo. *Una funcion que no falla y no hace nada es la clase de defecto que
    solo se caza mirandola.*

    **De donde sale el tamano**: *de `ln.tamano_envase`, que lo publica **la ficha del articulo
    elegido**.* **Cuando consta**, el calculo lo hace `core/envases_enteros.py` -- *la regla con sus
    pruebas: **1,4 kg con envases de 1 kg -> 2 envases y 600 g***. **Cuando no consta**, los dos campos se
    quedan en `None`: *ni un cero -- que diria «no sobra nada», y seria falso -- ni una compra
    fraccionaria inventada.*

    *Devuelve las mismas lineas, tocadas.* **Se mutan a proposito: son las de la previa, y hacer copias
    obligaria a emparejarlas despues.**
    """
    for ln in lineas:
        if ln.tamano_envase and ln.tamano_envase > 0:
            calculo = envases_de_la_linea(ln.cantidad, ln.unidad, ln.tamano_envase,
                                             ln.unidad_envase)
            ln.envases = calculo["envases"]
            ln.sobrante = calculo["sobrante"]
        else:
            # *Y no se rellena con un cero ni con una compra fraccionaria.* **`None` es «no se sabe».**
            ln.envases = None
            ln.sobrante = None
    return lineas


def _tamano_del_envase(texto: str) -> float | None:
    """El tamano del envase **publicado en la ficha**, o `None`. *Y del texto **no sale**.*

    **Aqui estaba el defecto, medido el 12 de octubre de 2026, y era doble.** *Esto pedia el tamano asi:*

    ```python
    cantidad = leido.get("cantidad") if isinstance(leido, dict) else getattr(leido, "cantidad", None)
    ```

    *Y `core/envases.py::lee` devuelve `tuple[str | None, int | None]`* -- **(tipo de envase, unidades del
    pack)** --, asi que `isinstance(leido, dict)` era **falso**, `getattr(tupla, "cantidad", None)` daba
    **`None`**, **y `ln.envases` y `ln.sobrante` no se calculaban nunca.**

    *Y aunque se hubiera arreglado el `dict`, seguiria dando `None`*: **`envases.lee` nunca devolvio un
    tamano** -- *lee «botella», «malla», «Pack-6», que son **el tipo de envase y cuantas unidades van
    dentro**, no cuanto pesa o cuanto cabe.*

    **Asi que esta funcion ya no intenta adivinarlo del texto.** *«Leche entera 1 l» se puede leer, pero
    **«Leche entera» a secas no dice cuanto trae**, y de ahi no se saca un numero.* **El tamano sale de
    `ln.tamano_envase`, que lo publica la ficha del articulo elegido** -- *y si no lo trae, la linea se
    queda sin calculo de envases, que es lo correcto: **no se inventa una compra fraccionaria.***

    *Se conserva la funcion, devolviendo `None`, para no romper a quien la llame y para que **el motivo
    este escrito donde estaba el error**.*
    """
    return None


def envases_de_la_linea(cantidad, unidad, tamano_envase, unidad_envase=None) -> dict:
    """Cuantos envases hay que comprar y cuanto sobra, **para una linea de la previa**.

    *Delegacion en `core/envases_enteros.py`, que es la regla y tiene sus pruebas.* **Aqui solo se junta
    lo que la linea sabe**: *cuanto se quiere y cuanto trae un envase.*
    """
    return envases_enteros(cantidad, unidad, tamano_envase, unidad_envase or unidad)
