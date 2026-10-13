# B02/B16 · **El ciclo diario nombra CINCO cadenas, y Lidl no esta entre ellas**

*(13 de octubre de 2026. **El hallazgo mas concreto de las ultimas rondas. Y es una clausula del encargo.**)*

## 1. Lo que dice el lanzador, literal

```
`ejecutar.bat`  (64 lineas) -- *** «Cesta: la recoleccion diaria entera en un solo comando» ***

  l6:  REM   1. *** las cinco cadenas (carrefour, dia, mercadona, aldi, alcampo) ***
  l7:  REM   2. las fichas maestras nuevas del dia (EAN, ingredientes, marca)
  l57: uv run python -m projects.cesta.run >> "data\ejecuciones.log" 2>&1
```

> *** Y **LIDL NO ESTA EN LA LISTA** *** -- *y **el encargo dice, palabra por palabra**:*
>
> > *** «Integra Lidl en el MISMO CICLO DIARIO y en API/UI **como sexta fuente**, con ambito regional y cobertura
> > demostrados.» ***
>
> *** O sea: **la clausula tiene dos mitades**, *y **una esta y la otra no**:*
> ```
> «en API/UI»         -> *** B03: superficie, `region` en los grupos, y cobertura medida ***
> «en el MISMO CICLO» -> *** `ejecutar.bat` nombra CINCO, y Lidl no esta. ***
> ```

## 2. Y encaja con **todo lo demas que se ha medido**, sin forzar nada

```
HECHO 1:  `data/runs.csv` -> *** lidl tiene CERO pasadas *** (las otras cinco, 41-48 cada una)
HECHO 2:  `data/raw/fuente=lidl` *** SI existe *** -> *Lidl **capturo** en algun momento*
HECHO 3:  `lidl.py` registra con `log_run` *** DENTRO del bloque `--escribir` *** (arreglo `5039b9c`, ronda 123)
HECHO 4:  *** y `lidl` NO aparece en ningun `.ps1`, `.yml` ni en `scripts/` ***
HECHO 5:  y **`ejecutar.bat` nombra las cinco, y llama a `projects/cesta/run.py`**
```

> *** Y los cinco hechos **encajan en una sola lectura**, y es la que no hay que inventar:** *** *Lidl **no esta en el
> ciclo diario**; **su crudo existe porque se ejecuto a mano** (o por otra via); *y **por eso `runs.csv` no tiene
> ninguna pasada suya.** *
>
> *** Y **el arreglo de la ronda 123 sigue siendo correcto**: *** *`log_run` **dentro del `--escribir`** -- *y su
> consecuencia, **medida hoy**, es que **un Lidl en seco no deja rastro.** *
>
> *** O sea: **las dos cosas son ciertas a la vez**: *** *** el arreglo esta bien, **y** falta meterlo en el ciclo. ***

## 3. Y **no se concluye** sin comprobar **una** cosa

> *** Lo unico que podria cambiar la lectura: *** *** que `projects/cesta/run.py` **descubra los colectores solo** ***
> -- *por ejemplo, recorriendo `projects/cesta/collectors/` -- *y entonces **el `REM` de `ejecutar.bat` seria un
> comentario desactualizado**, y **Lidl si correria.** *
>
> *** Y **la comprobacion es una sola**: *** *leer `projects/cesta/run.py` y ver **si la lista de fuentes esta
> escrita o se descubre.** *
>
> *** *** Y NO SE DICE QUE FALTE HASTA ENTONCES. *** ***

## 4. Y esto **afina la casilla del dictamen**, que ya decia «limitado»

```
B16, la casilla de Lidl:  *** «implementado · LIMITADO EN ALCANCE» ***
   -> *y ahora los limites son DOS, y concretos:*
      1) *** su ambito es regional *** (B03: la columna `region`, y el propietario lo pidio asi)
      2) *** y su pasada NO esta en el ciclo diario *** -- *y eso **no es «alcance»: es cobertura del ciclo.** *
```

> *** O sea: **la casilla «limitado» era la correcta**, *y **ahora se puede decir por que con una linea de
> `ejecutar.bat`.** *
>
> *** Y **es la clase de cosa que B16 pide que no se esconda**: *** *** «Si una fuente es inaccesible, explicar
> alcance y no fingir que ya son seis catalogos completos.» ***
>
> *** Y aqui **la fuente es accesible** (hay crudo), *y **lo que falta es su sitio en el ciclo** -- *que es **otra
> cosa, y se dice distinto.** *
