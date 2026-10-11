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

from core import envases

# **La tabla de unidades de `core.normalize`**, que ya sabe que `g` es `kg` por 0,001.
# *Se importa en vez de copiarse: una sola tabla, y la misma que usa el catalogo para el
# precio por kg.*
from core.normalize import _UNIDADES


@dataclass
class LineaDeCompra:
    """Una linea de la previa: **lo que habria que comprar**, no lo que dice la receta."""
    clave: str                     # producto + unidad: la identidad de la consolidacion
    texto: str                     # como se lee en la receta
    producto_id: str | None
    cantidad: float
    unidad: str
    # Los envases enteros, cuando se sabe el tamano del envase.
    envases: int | None = None
    tamano_envase: float | None = None
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
    """La unidad, dicha igual venga como venga. *Sin unidad no se consolida con nadie.*

    **Y `g` y `kg` son la MISMA unidad**, no dos: *la tabla de `core.normalize` ya lo sabe* --
    `"g": ("kg", 0.001)` --, *y sin usarla `1 kg` y `500 g` de harina caian en claves distintas y se nombraban
    como incompatibles, **que es lo que no son**.*

    *Medido (ronda 121): la aceptacion de F10 pide **«mezcla kg/g compatible y ud incompatible»** -- los dos
    casos puestos juntos a proposito --, y el modulo los trataba igual.* **Con esto se distinguen**: `kg` y `g`
    caen en `kg`, `ml` cae en `l`, y `ud` en `ud`, *asi que se suman los que se pueden sumar y se nombran los
    que no.*
    """
    return _UNIDADES.get((unidad or "").strip().lower(), ((unidad or "").strip().lower(), 1.0))[0]


def _a_canonica(cantidad: float, unidad: str | None) -> float:
    """**La cantidad, en la unidad canonica.** *Sumar `1 kg` con `500 g` sin convertir daria `501`.*

    *Es la otra mitad del mismo arreglo*: **cambiar el nombre de la unidad sin cambiar el numero empeora las
    cosas** -- *seria sumar peras con manzanas y decir que son todas peras.* **Se convierte con el factor de la
    tabla, y lo que no esta en la tabla se queda como esta** -- *un factor de 1.0, que es no tocar nada.*
    """
    factor = _UNIDADES.get((unidad or "").strip().lower(), (None, 1.0))[1]
    return float(cantidad) * factor


def previa_de_compra(ingredientes: list[dict]) -> Previa:
    """**Que habria que comprar.** *Pura: no escribe, no consulta, no decide por nadie.*

    Cada ingrediente es lo que guarda `core/recetas.py`: `texto`, `cantidad`, `unidad`, y
    opcionalmente `producto_id`, `grupo_id`, `fuente`, y -- si la API lo enriquecio -- el precio.
    """
    acumulado: dict[str, LineaDeCompra] = {}
    por_producto: dict[str, set[str]] = {}      # producto -> unidades vistas
    sin_cantidad: list[str] = []

    for ing in ingredientes:
        texto = str(ing.get("texto") or "").strip()
        cantidad = ing.get("cantidad")
        unidad = _unidad_canon(ing.get("unidad"))
        pid = ing.get("producto_id")
        pid = str(pid) if pid else None

        # **Regla 2: sin cantidad no hay compra.** *Y sin inventarla.*
        if not isinstance(cantidad, (int, float)) or cantidad <= 0:
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
        clave = f"{quien}|{unidad}"
        por_producto.setdefault(quien, set()).add(unidad)

        # **Y la cantidad, en la unidad canonica.** *Cambiar el nombre de la unidad sin cambiar el
        # numero seria sumar peras con manzanas y decir que son todas peras.*
        cantidad = _a_canonica(cantidad, ing.get("unidad"))

        if clave in acumulado:
            ln = acumulado[clave]
            ln.cantidad += cantidad
            if texto and texto not in ln.de_donde:
                ln.de_donde.append(texto)
        else:
            acumulado[clave] = LineaDeCompra(
                clave=clave, texto=texto, producto_id=pid,
                cantidad=float(cantidad), unidad=unidad, de_donde=[texto])

    # **Regla 1: lo que quedo en unidades incompatibles se nombra.** *No se suma ni se elige una.*
    sin_consolidar = []
    for quien, unidades in por_producto.items():
        if len(unidades) > 1:
            nombre = next((ln.texto for ln in acumulado.values()
                           if (ln.producto_id or ln.texto.lower()) == quien), quien)
            sin_consolidar.append(f"{nombre}: {' y '.join(sorted(unidades))}")

    # **Regla 3: envases enteros.** *Y el sobrante, dicho.*
    for ln in acumulado.values():
        tamano = _tamano_del_envase(ln.texto)
        if tamano and tamano > 0:
            ln.tamano_envase = tamano
            ln.envases = math.ceil(ln.cantidad / tamano)
            ln.sobrante = round(ln.envases * tamano - ln.cantidad, 3)

    lineas = sorted(acumulado.values(), key=lambda x: (-x.cantidad, x.texto))
    nota = ""
    if sin_cantidad:
        nota = ("Lo que no tiene cantidad no se compra, y no se le inventa: "
                + ", ".join(sin_cantidad) + ".")
    return Previa(lineas=lineas, sin_cantidad=sin_cantidad,
                  sin_consolidar=sin_consolidar, nota=nota)


def _tamano_del_envase(texto: str) -> float | None:
    """El tamano del envase tal y como lo diga el texto, o `None`.

    *Usa `core/envases.py`, que es quien sabe leer «garrafa», «malla», «Pack-6» y «a granel».* **Si
    no se puede leer, no se inventa: `None`, y la linea se queda sin calculo de envases.**
    """
    if not texto:
        return None
    try:
        leido = envases.lee(texto)
    except Exception:  # noqa: BLE001  (un texto raro no puede tumbar una previa)
        return None
    if not leido:
        return None
    cantidad = leido.get("cantidad") if isinstance(leido, dict) else getattr(leido, "cantidad", None)
    return float(cantidad) if isinstance(cantidad, (int, float)) and cantidad > 0 else None
