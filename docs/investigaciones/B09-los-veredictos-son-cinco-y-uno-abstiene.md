# B09 · **Los veredictos son CINCO, y el criterio nombra otros cuatro** -- y uno se llama **`ABSTIENE`**

*(13 de octubre de 2026. **Cuarta ronda de B09. Y el conjunto de veredictos es mas rico que el del plan.**)*

## 1. Lo que hay, literal (`core/identidad.py:33`)

```python
EXACTO      = "exacto"
PROBABLE    = "probable"
ALTERNATIVA = "alternativa"
CUARENTENA  = "cuarentena"
ABSTIENE    = "abstiene"
```

## 2. Y comparado con el criterio, **los dos conjuntos son DISTINTOS**

```
EL CRITERIO DE B09 DICE:   exacto · FAMILIA · alternativa · DESCONOCIDO
EL CODIGO TIENE:           exacto · PROBABLE · alternativa · CUARENTENA · ABSTIENE
```

> *** Y no coinciden **en tres de los cuatro**: ***
>
>   - **`exacto`** *-- *el unico que esta en los dos;*
>   - **`alternativa`** *-- *y tambien;*
>   - **`familia`** *-- *el criterio lo pide, **y no aparece aqui**;*
>   - **`desconocido`** *-- *el criterio lo pide, **y no aparece aqui** (aqui hay `CUARENTENA` y `ABSTIENE`);*
>   - **`probable`** *-- *el codigo lo tiene, **y el criterio no lo nombra**.*
>
> *** Y **no se dice que falten `familia` ni `desconocido`**: *** *se dice que **no estan en la lista de `identidad.py`**
> -- *y **pueden ser de otro modulo** (el banco de pares, o `matching`), **o pueden ser el nombre que el plan usa para
> `CUARENTENA`/`ABSTIENE`**.*
>
> *** Lo que **si** se puede decir es lo que hay: **cinco valores, con nombre y linea. ***

## 3. Y `ABSTIENE` es **la doctrina convertida en veredicto**

> *** «Abstiene» *** -- *y **no hace falta leer el cuerpo para saber que significa**: *es **el veredicto de «no me
> pronuncio»**.*
>
> *** Y es **la forma mas fuerte de las dieciseis**: *** *las otras quince eran **un valor que se guarda**
> (`DESCONOCIDO`, `NULL`, `sin_precio`) o **una imposibilidad** (clave, lista vacia, import) o **una negativa
> razonada** (el `umbral` del oraculo).*
>
> *** Y esta es **un veredicto que se puede devolver**: *** **el sistema puede decir, sobre un par de productos, «no
> me pronuncio»** -- *y **eso es un resultado, no un fallo.***
>
> *** Que es **exactamente** lo que hace falta para la regla del criterio: *** *** «EAN coincidente no neutraliza
> formato incompatible» -- *o sea: **cuando el formato no cuadra, el sistema no elige: se abstiene.** ***
>
> *** Y `CUARENTENA`, que esta al lado, es **su companera**: *** *«cuarentena» es **apartar un caso para mirarlo**, y
> `ABSTIENE` es **no decidir**. **Las dos son «no ahora», y las dos son estados, no errores.***

## 4. Y hay tres constantes mas que dicen de que va el fichero

```
l41: _UNIDADES = {...}
l49: RE_CANTIDAD = re.compile(...)
l51: RE_PACK = re.compile(r"(?:(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?))|(?:pack\s*(?:d...")
l58: def normaliza_gtin(codigo) -> str | None
l77: def atributos(nombre) -> dict
l103: class Producto
l125: def _presentacion(a: Producto, b: Producto) -> tuple[bool, list[str]]
l144: def _no_comparable(motivos: list[str]) -> bool
```

> *** Y ahi esta **`RE_PACK`**: *** *una expresion regular para **«2 x 500 g»** y **«pack de 3»** -- *que es
> **literalmente el «neto/pack» del criterio**.*
>
> *** Y `_presentacion(a, b) -> tuple[bool, list[str]]`: *** *devuelve **si son comparables** y **los motivos** --
> *que es **`razon_declarada`** otra vez: **el «no» con su motivo.***
>
> *** Y `_no_comparable(motivos)`: *** *una funcion **cuyo argumento son los motivos** -- *o sea: **no se puede llamar
> sin decir por que.***

## 5. Y B09, con cuatro rondas

```
  1) REUTILIZAR (y ser INDEPENDIENTE)  HECHO
  2) EL BANCO DE PARES                 POR LEER -- `core/banco_de_pares.py` y su ensayo
  3) LOS CUATRO VEREDICTOS             *** y son CINCO: `EXACTO · PROBABLE · ALTERNATIVA · CUARENTENA ·
                                       ABSTIENE` *** -- y el criterio nombra otros cuatro
                                       (`familia` y `desconocido` NO estan en esta lista)
  4) LAS DOS REGLAS DEL EAN            *** `ABSTIENE` es la forma que toma «no neutraliza formato
                                       incompatible»: no elige, se abstiene *** -- y el cuerpo POR LEER
  5) Y LA PROHIBICION DEL ORDINAL      POR MIRAR
```

> *** Y el banco de pares, que es la clausula (2) y **lo unico entero por leer**, es **donde tienen que estar
> `familia` y `desconocido`** *** -- *si es que estan.*
>
> *** Y por eso el siguiente paso es el (3) del metodo: **los nombres de `test_banco_de_pares.py`**. ***
