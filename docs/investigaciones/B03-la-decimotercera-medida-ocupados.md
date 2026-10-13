# B03 · **La decimotercera medida**: el «1-a-1 por par de cadenas» lo impone `ocupados`

*(13 de octubre de 2026. **El sitio, con nombre y numero de linea. Y no es ninguna de las funciones que se
llamaban asi.**)*

## 1. El sitio

`core/matching.py:648-672`, dentro de `enlaces`:

```python
def emitir(x, y, s, ocupados):
    ...
    emitidos.add((x, y))
    ocupados.add((x, filas[y]["fuente"]))        # <- (producto, CADENA)
    ocupados.add((y, filas[x]["fuente"]))
    ocupados_todos.add((x, filas[y]["fuente"]))
    ocupados_todos.add((y, filas[x]["fuente"]))
    ...

for canal in ("marca", "equivalente", "vector"):
    ocupados: set[tuple[int, str]] = set()        # <- (producto, cadena)
    for _grupo, candidatos in sorted(canales[canal].items()):
        for x, y, s in _asignacion_1a1(candidatos, umbral):
            emitir(x, y, s, ocupados)
```

> **El «1-a-1 por par de cadenas» no lo impone `_asignacion_1a1`.** *Lo impone **`ocupados`**, que es un conjunto
> de **`(producto, cadena)`**.*
>
> *Y eso es lo que significa «1-a-1 por par de cadenas» en el codigo:* **un producto no puede quedar emparejado
> dos veces con la misma cadena** -- *porque `(x, filas[y]["fuente"])` ya estaria en `ocupados`.*

## 2. Y entonces la zona entra en `ocupados`, y en un sitio mas

**La clave pasa de `(producto, cadena)` a `(producto, cadena, zona)`:**

```
ocupados: set[tuple[int, str]]            ->  set[tuple[int, str, str | None]]
ocupados.add((x, filas[y]["fuente"]))     ->  ocupados.add((x, filas[y]["fuente"], z(filas[y])))
```

*Donde `z(f)` es `f.get("region")`.*

> **Y el efecto es el que se busca**: *un producto **puede** emparejarse con **la misma cadena en otra zona**
> -- *que es lo correcto, porque son dos precios distintos* -- **y no puede** con la misma cadena en la misma
> zona.

**Y hay un segundo sitio: `canales[canal]`.** *Los bloques de candidatos se forman por canal y grupo; si el
bloque mezcla zonas, `_asignacion_1a1` reparte entre zonas.* *Hay que mirar como se construye `canales` --*
**que es la decimocuarta medida, y con eso termina.**

## 3. Y esto cierra el mapa, y lo cierra con una leccion

*La ronda 81 dijo que el cambio eran cuatro funciones.* *Y han aparecido **seis sitios**, y ninguno de los
cuatro primeros era el que impone la regla:*

```
  adelgaza          -> conserva el dato                        (ronda 82)
  grupos_de         -> lo pasa                                 (ronda 84)
  agrupar_enlaces   -> comprueba la invariante                 (ronda 83)
  tabla_de          -> lo guarda para manana                   (ya estaba)
  ---
  OCUPADOS          -> *** IMPONE EL 1-A-1 POR CADENAS ***     <- aqui esta la regla
  CANALES           -> forma los bloques de candidatos         <- la decimocuarta
```

> **La regla que se queria cambiar -- «1-a-1 por par de cadenas» -- no estaba en la funcion que lleva ese nombre
> en su docstring, ni en la guarda que la comprueba, ni en `grupos_de` que la pasa: estaba en un `set` local
> llamado `ocupados`, en `emitir`, en la linea 650.**
>
> *Y la forma de encontrarla ha sido **la misma seis veces**: seguir el dato desde donde se ve el sintoma hasta
> donde se decide. **Sin suponer ningun salto.***

## 4. Estado, con los seis sitios

```
HECHO:   matching.py :: adelgaza          -> conserva `region`                  -- 27756cd
HECHO:   matching.py :: agrupar_enlaces   -> la guarda por (cadena, zona)       -- 75e625f
HECHO:   grupos_ids.py :: tabla_de        -> la clave que se hereda             -- 0d1a50c
HECHO:   emparejar.py :: grupos_de        -> pasa `regiones`                    -- 7f0b72d
HECHO:   api/cesta.py :: donde_comprar    -> pide la zona (si esta)             -- f952c80

FALTA:   matching.py :: emitir / ocupados -> LA CLAVE POR (producto, CADENA, ZONA)   <- la regla
         matching.py :: canales           -> que los bloques no mezclen zonas       <- la 14ª medida
         y despues: que donde_comprar haga algo con la zona -- decision escrita
```

**Cinco hechas, dos medidas, y ninguna de las dos es la que el plan decia.**
