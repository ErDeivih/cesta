# B03 · **Decimoquinta medida, medida por accidente**: `grupos.parquet` se rehizo, y la zona **no** llego

*(13 de octubre de 2026. **Se rehizo el emparejamiento entero para que la zona llegara al fichero. Y no llego.**)*

## 1. Lo que se hizo

```
$ python -c "from projects.cesta import emparejar; emparejar.main([])"
  51725 productos de 6 cadenas
  51676 de 51725 productos conservan el numero de ayer
  22873 enlaces (6618 identicos, 16255 equivalentes)
  8768 grupos comparables entre cadenas
  equivalencias versionadas en ejecucion=20261013-154114
emparejar: hecho en 440s
```

*Y despues, comprobado:*

```
grupos.parquet tiene region: False
columnas: 62
```

> **La zona no llego.** *El emparejador corrio entero, con las piezas de transporte puestas -- `adelgaza` la
> conserva, `grupos_de` la pasa, `tabla_de` la guardaria **si las filas la trajeran** --, **y el fichero salio sin
> ella**.*

## 2. Y por que, que es lo que hay que mirar ahora

**`tabla_de` solo anade `region` si las filas la traen:**

```python
if any("region" in f for f in filas):
    columnas["region"] = [f.get("region") for f in filas]
```

*Asi que **las `filas` que llegan al final NO traen `region`** -- y no la traen **mucho antes** de `tabla_de`.*

> **Los tres candidatos, en orden de probabilidad:**
>
>   1. **`catalogo_actual()`** (`emparejar.py:129`) -- *la funcion que lee el catalogo y devuelve las filas.*
>      **Si selecciona un juego fijo de columnas, la zona se cae ahi** -- *y es el mismo caso que `adelgaza`, una
>      capa antes.*
>   2. **`_enlaces_guardados` / la lectura de ayer** -- *si las filas vienen del fichero de la pasada anterior,
>      que tampoco tiene la columna.*
>   3. **y `adelgaza`** -- *que ya conserva `region`, pero **solo si la fila la tiene al entrar**.*

## 3. Y esto es, exactamente, la decimoquinta vez que pasa lo mismo

```
  el plan decia:  donde_comprar (48) · la guarda (79) · _asignacion_1a1 (81) · cuatro funciones (81)
  y los sitios son: adelgaza · grupos_de · _bloque · ocupados · la guarda · tabla_de · ... y ahora
                    LA LECTURA DEL CATALOGO
```

> **Otra vez: la funcion que parece hacer algo es la que lo da por hecho, y el dato se cae en quien la llama.**
>
> *Y esta vez no lo ha dicho un docstring: **lo ha dicho el fichero que salio sin la columna**.* **Que es la forma
> mas cara de averiguarlo -- 440 segundos -- y la mas dificil de discutir.**

## 4. Y lo que se gano, que no es poco

  - **El emparejamiento se rehizo entero** y salio coherente: *51725 productos, 22873 enlaces, **51676 de 51725
    conservan el numero de ayer** -- o sea que `estabiliza` heredo bien, que es lo que la ronda 69 vigila.*
  - **Y quedan 62 columnas, con los mismos grupos que antes** -- *o sea que las piezas de transporte, tal como
    estan, **no cambiaron nada**, que es lo que tenian que hacer.*
  - **Y la zona no esta en `grupos.parquet`, medido.** *Que es un hecho, no una sospecha.*

> ***Y de paso: `donde_comprar` pide la zona **si esta**, y no esta. Asi que el catalogo se compara como
> siempre -- que es lo que la ronda 90 dejo dicho, ahora comprobado en el fichero de verdad.***

## 5. Lo que queda, con el sitio nuevo

```
  (1) QUE LA ZONA LLEGUE A LAS FILAS -- donde se lee el catalogo (`catalogo_actual`, emparejar.py:129)
      -> y despues `adelgaza` y `tabla_de` la llevaran solas, porque ya estan puestas.
  (2) que `donde_comprar` HAGA ALGO con ella -- decision escrita (ronda 63).
```

*Y (1) es ahora **una sola funcion**, no siete: **las otras seis ya estan hechas y probadas**, y solo falta que el
dato entre por la puerta.*
