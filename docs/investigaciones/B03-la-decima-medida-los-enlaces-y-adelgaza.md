# B03 · **La decima medida, hecha**: los enlaces se generan en `enlaces`, y hay dos sitios con nombre

*(13 de octubre de 2026. **La ultima medida, y con ella el mapa del cambio esta completo de verdad.**)*

## 1. Donde se generan los enlaces

`core/matching.py:447`:

```python
def enlaces(filas_completas: list[dict], umbral: float = 0.55, ...) -> list[tuple[int, int, float, str]]:
    \"\"\"Pares (i, j, parecido, motivo) del mismo producto en cadenas distintas.

    Dos pasos, y los dos importan:

    1. **Quien puede ser pareja de quien** (bloqueo): mismo formato y alguna palabra en comun.
    2. **Quien se queda con quien** (asignacion): dentro de cada bloque y de cada
       **par de cadenas**, el reparto 1-a-1 que maximiza la suma de parecidos, con el
       algoritmo hungaro. Ver `_asignacion_1a1`.

    `filas` necesita: fuente, nombre, marca, cantidad, unidad_canon, ean.
    ...
    Lo primero que hace es quedarse con esas seis columnas **y tirar el resto**: ver `adelgaza`.
    \"\"\"
```

> **Y ahi estan las dos cosas que hacian falta saber, y las dos con nombre:**
>
>   - **`adelgaza`** -- *«se queda con esas seis columnas **y tira el resto**»* ✗
>   - **`_asignacion_1a1`** -- *«dentro de cada bloque y **de cada par de cadenas**, el reparto 1-a-1»*

## 2. Y por eso la zona **no llega** hoy al generador de enlaces

**Aunque `enlaces` recibe `filas_completas` -- que podrian traerla --, `adelgaza` la tira.** *Asi que el
emparejamiento por pares de cadenas **no sabe de zonas**, y no por decision: **porque nadie se las paso**.*

> *Que es exactamente lo que habia que averiguar, y la respuesta es: **hay que llevarselas**.*

## 3. El cambio, entonces, con sus cuatro sitios y lo que hay que hacer en cada uno

```
1) core/matching.py :: adelgaza(...)
   -> QUE CONSERVE `region` -- hoy tira todo menos seis columnas.
   -> *Sin esto, los otros tres no sirven de nada.*

2) core/matching.py :: _asignacion_1a1(...)
   -> EMPAREJAR POR PAR DE (CADENA, ZONA), no solo por par de cadenas.
   -> *Aqui NACE la invariante: es lo que hace que un grupo no pueda tener
      dos productos de la misma cadena en la misma zona.*

3) core/matching.py :: agrupar_enlaces(...)
   -> `regiones: list[str] | None = None`, al lado de `cadenas`.
   -> Y la guarda por (cadena, zona), CON SU PRUEBA DE «SIN ZONAS NADA CAMBIA».

4) core/grupos_ids.py :: tabla_de(...)      YA HECHO -- 0d1a50c
   -> Y groups_de (emparejar.py) pasa `regiones` al lado de `cadenas`.
```

> **Y fijate en que el orden de la lista es el orden de la cadena de datos**: *la zona entra por `adelgaza`,
> viaja hasta `_asignacion_1a1` **donde nace la invariante**, y `agrupar_enlaces` **la comprueba**.*
>
> *Al reves -- empezando por la guarda -- **se rechazarian uniones que los enlaces no deberian haber
> propuesto**, y el resultado serian **grupos peores**.* **Que es lo que la ronda 79 dejo dicho, ahora con los
> dos nombres.**

## 4. Y el mapa del cambio, entero

```
HECHO:   donde_comprar PIDE la zona (si esta)                       -- f952c80
HECHO:   tabla_de GUARDA la zona (si las filas la traen)            -- 0d1a50c
MEDIDO:  emparejar.py :: grupos_de  -- pasar `regiones` al lado de `cadenas`
MEDIDO:  matching.py :: adelgaza    -- QUE CONSERVE `region`         <- el que faltaba, y es el primero
MEDIDO:  matching.py :: _asignacion_1a1 -- por par de (CADENA, ZONA) <- y aqui nace la invariante
MEDIDO:  matching.py :: agrupar_enlaces -- la guarda, con su prueba de «sin zonas nada cambia»
FALTA:   escribirlo, en ese orden
         y despues: que donde_comprar HAGA algo con la zona -- la decision esta escrita
```

**Diez medidas. Y esta ultima no dejo una incognita: dejo dos funciones con nombre y una frase («tira el
resto») que dice exactamente por que la zona no llega.**

## 5. Y la decima medida existio por leer un docstring

*En la ronda 79 se iba a tocar `agrupar_enlaces` -- la guarda -- porque es donde el sintoma aparece.* *Y el
docstring dijo:* **«los enlaces son 1-a-1 por par de cadenas»**.

> **Esa frase mando a mirar los enlaces. Y los enlaces mandaron a `adelgaza`.** *Tres sitios, encadenados, y
> **el primero es el que tira el dato**.*
>
> *Si se hubiera empezado por la guarda -- que es lo que el plan decia, «generalizar la invariante» -- **el
> cambio habria pasado las pruebas y no habria hecho nada**: la zona no llega hasta alli.*
>
> **Es la misma forma que las veintiocho anteriores, y esta vez se cazo antes de escribir.** *Lo que la caza es
> **leer el cuerpo, no la firma** -- y en este caso, **una frase entre parentesis en un docstring**.*
