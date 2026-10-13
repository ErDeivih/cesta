# B03 · **La duodecima medida**: el par (cadena, zona) se forma donde se construyen los candidatos

*(13 de octubre de 2026. **Iba a tocarse `_asignacion_1a1`, y el docstring dice que no es ahi.**)*

## 1. Lo que dice `_asignacion_1a1`

`core/matching.py:365`:

```python
def _asignacion_1a1(candidatos: list[tuple[int, int, float]], umbral: float) -> list[...]:
    """Asignacion optima 1-a-1 entre dos listas de productos (algoritmo hungaro).

    `candidatos` son (izquierda, derecha, puntuacion) DE DOS CADENAS DISTINTAS
    dentro de un mismo bloque. Devuelve el subconjunto que maximiza la suma...
    ...
    El hungaro es O(n^3) y aqui n es el tamano de un bloque POR PAR DE CADENAS
    """
```

> **No agrupa por cadena: recibe los candidatos ya emparejados.** *«`candidatos` son ... **de dos cadenas
> distintas**» -- **es una precondicion, no algo que la funcion haga.***
>
> **Asi que el «por par de cadenas» ocurre en quien construye `candidatos`**, *una capa mas arriba.* **Y ahi es
> donde entra la zona.**

## 2. Y esto es la cuarta vez que el sitio se mueve, y siempre por el mismo motivo

```
ronda 55  -> se empezo en `donde_comprar`      y no era ahi
ronda 68  -> se creyo que era `estabiliza`     y no era ahi
ronda 71  -> se dijo que `grupos_de` era «el unico sitio»   y no era
ronda 74  -> parecia que `grupos_de` ya lo tenia            y era `enlaces`
ronda 79  -> se iba a tocar la guarda                        y era `adelgaza`
ronda 85  -> y ahora `_asignacion_1a1` tampoco               es quien construye `candidatos`
```

> **Seis veces.** *Y las seis, la causa es la misma: **la funcion que parece hacer algo es la que lo da por
> hecho**, y el trabajo esta en quien la llama.*
>
> *Un docstring que dice «`candidatos` son de dos cadenas distintas» **no esta describiendo lo que hace: esta
> describiendo lo que exige**.* **Y leerlo como descripcion es lo que ha mandado a tocar el sitio equivocado.**

## 3. Y el estado del cambio, con lo hecho y lo que queda

```
HECHO:   matching.py :: adelgaza        -> conserva `region`            -- 27756cd
HECHO:   matching.py :: agrupar_enlaces -> la guarda por (cadena, zona) -- 75e625f
HECHO:   grupos_ids.py :: tabla_de      -> la clave que se hereda       -- 0d1a50c
HECHO:   emparejar.py :: grupos_de      -> pasa `regiones`              -- 7f0b72d
HECHO:   api/cesta.py :: donde_comprar  -> pide la zona (si esta)       -- f952c80

FALTA:   QUIEN CONSTRUYE `candidatos`   -- y ahi se empareja por par de (CADENA, ZONA)
         y despues: que `donde_comprar` haga algo con la zona -- decision escrita
```

**Cinco piezas hechas, y la que falta es una capa mas arriba de donde se creia.** *Que es lo que hay que decir en
vez de tocar `_asignacion_1a1`, que **no es el sitio**.*

## 4. Y por que esto, aunque parezca un paso atras, es lo correcto

*Si se hubiera tocado `_asignacion_1a1` -- como decia el plan de la ronda 81 --, **habria pasado las pruebas y no
habria hecho nada**: la funcion recibe los candidatos ya formados, y **no los vuelve a agrupar**.*

> **Seria el mismo caso que la guarda**: *un cambio correcto, probado, y **sin efecto**, porque el dato o la
> decision estan en otro sitio.*
>
> *Y es la tercera vez en esta sesion que se caza antes de escribir* -- *la guarda en la ronda 79, `_asignacion_1a1`
> ahora.* **Lo que lo caza es siempre lo mismo: leer el cuerpo, y sobre todo **la primera linea del docstring,
> que dice que da por hecho**.*
