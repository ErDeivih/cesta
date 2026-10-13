# B03 · **La decimocuarta medida**: los bloques de candidatos no llevan zona

*(13 de octubre de 2026. **La ultima medida, y la que cierra el mapa del cambio. Y no se toca en esta ronda, y
se dice por que.**)*

## 1. Lo que hay

`core/matching.py`, los tres sitios que forman bloques:

```
579:  canales["marca"][grupo].append((x, y, s))                     <- clave: el grupo de tokens
583:  canales["equivalente"][grupo].append((x, y, e))               <- clave: el grupo de tokens
630:  canales["vector"][(clave, filas[x]["fuente"], filas[y]["fuente"])].append((x, y, s))
                                                                    <- clave: (bloque, cadena, cadena)
684:  for _grupo, candidatos in sorted(canales[canal].items()):
          for x, y, s in _asignacion_1a1(candidatos, umbral):
```

> **Ninguna de las tres claves lleva la zona.** *Asi que **un bloque puede tener candidatos de dos zonas**, y
> `_asignacion_1a1` reparte entre ellos.*
>
> **Y como `ocupados` ya distingue zonas** -- *el cambio de la ronda 87* --, **un par entre zonas SI se
> emitiria.** *O sea: **un grupo con la zona A y la zona B dentro**, que es exactamente lo que B03 quiere
> evitar.*

## 2. Y el cambio, entonces, es el mismo de siempre: la zona en la clave

```
canales["marca"][(grupo, ...)]              -> con la zona de cada lado
canales["equivalente"][(grupo, ...)]        -> con la zona de cada lado
canales["vector"][(clave, fx, fy)]          -> (clave, fx, zx, fy, zy)
```

> **Y sin zonas sale lo mismo**, *porque todas las filas daran `None` y la clave sera la misma que hoy **con un
> `None` de mas*** -- *el mismo razonamiento que en `ocupados`, y la misma garantia: **las pruebas que ya
> existen.***

## 3. Y por que **no** se ha hecho en esta ronda, que es lo que hay que decir

**Porque son tres sitios, con dos formas distintas de clave** -- *dos por `grupo` y uno por `(clave, cadena,
cadena)`* --, **y no es el mismo cambio repetido tres veces**: *en los dos primeros hay que **rehacer la clave
del diccionario**, y en el tercero **anadir dos campos**.*

> *Y eso hay que hacerlo **con el contexto entero y mirando los tres sitios a la vez**, porque un cambio a medias
> aqui **no rompe una pantalla: deja el emparejamiento a medio cambiar**, con `ocupados` distinguiendo zonas y
> los bloques sin distinguirlas.*
>
> **Que es una combinacion que no se ha probado nunca y que no hay ninguna prueba que cubra** -- *porque hasta
> hoy la zona no existia en el emparejador.*

**Asi que se para aqui, y se deja dicho.** *Que es lo que se ha hecho otras veces en esta serie -- la captura de
Alcampo, el cambio de `donde_comprar` -- y por el mismo motivo: **medir y no empezar lo que no se puede terminar
bien.***

## 4. Y el mapa del cambio, con los siete sitios

```
HECHO:   matching.py :: adelgaza          -> conserva `region`                -- 27756cd
HECHO:   matching.py :: agrupar_enlaces   -> la guarda por (cadena, zona)     -- 75e625f
HECHO:   grupos_ids.py :: tabla_de        -> la clave que se hereda           -- 0d1a50c
HECHO:   emparejar.py :: grupos_de        -> pasa `regiones`                  -- 7f0b72d
HECHO:   api/cesta.py :: donde_comprar    -> pide la zona (si esta)           -- f952c80
HECHO:   matching.py :: emitir/ocupados   -> LA REGLA, por (producto, cadena, zona)  -- dea976a

FALTA:   matching.py :: canales           -> LA ZONA EN LA CLAVE DE LOS TRES BLOQUES   <- esta medida
         y despues: que donde_comprar haga algo con la zona -- decision escrita
```

**Seis de siete, y la que falta tiene sus tres lineas dichas: 579, 583 y 630.**

## 5. Y lo que esto dice del cambio, que es la conclusion de toda la serie

*La ronda 81 dijo:* **«el cambio son cuatro funciones»**.

**Y son **siete sitios**, en **cuatro ficheros**, y el que impone la regla -- `ocupados` -- **no estaba en la
lista de ninguno de los planes**:** *ni en el de la ronda 48 (que decia `donde_comprar`), ni en el de la 79 (que
decia la guarda), ni en el de la 81 (que decia `_asignacion_1a1`).*

> **Cada uno de esos planes habria producido un cambio correcto, probado, y sin efecto.**
>
> *Y lo que ha permitido encontrarlo no ha sido un plan mejor: ha sido **seguir el dato**, doce veces, **sin
> suponer ningun salto** -- y **leer los docstrings, que dicen lo que cada funcion da por hecho**.*
