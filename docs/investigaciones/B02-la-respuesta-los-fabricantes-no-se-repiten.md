# B02 · **La respuesta**: los fabricantes **no se repiten**, y `tests/fixtures/` **sobra**

*(13 de octubre de 2026. **La pregunta de la ronda 126, contestada. Y la carpeta vacia era una decision.**)*

## 1. Los fabricantes, con su firma

```
test_lidl_colector.py:23   def ficha(d: dict) -> str:
test_lidl_colector.py:27   def oferta_simple(**extra) -> dict:
test_banco_de_pares.py:42  def ficha(fuente, nombre, marca=None, ean=None, un...)
test_sondear_lidl.py:9     def ficha(d):
test_carrefour.py:436      def _html_con_navegacion(nav_id, items=1, total=10...)
```

> **`ficha` aparece **tres veces** -- *en `test_lidl_colector`, en `test_banco_de_pares` y en `test_sondear_lidl` --*
> **y las tres con firma distinta**:*
>
>   - *`ficha(d: dict) -> str`* **construye HTML** *a partir de un dict;*
>   - *`ficha(fuente, nombre, marca=None, ean=None, un...)* **construye una FILA**, *no HTML;*
>   - *`ficha(d)`* **otra cosa mas.**
>
> *** No se repiten: cada uno fabrica lo que SU parser necesita. ***
>
> *Y `test_carrefour` ni se llama `ficha`: se llama `_html_con_navegacion(nav_id, items, total)` -- **que fabrica
> justo lo que su parser de navegacion necesita, y nada mas**.*

## 2. Y entonces la pregunta de la ronda 126 tiene respuesta

```
¿SE REPITEN LOS FABRICANTES?   ->  NO
¿SOBRA tests/fixtures/?         ->  SI, para esto
```

> **La carpeta existe, esta vacia, y **es una decision, no una tarea pendiente**: *los fixtures de bytes de este
> proyecto **viven al lado del parser que los prueba**, cada uno con la forma que su parser entiende.*
>
> *Y **tiene sentido**: un HTML de Lidl metido en una carpeta comun **no le sirve a nadie mas** -- *Alcampo no lo
> entiende, Carrefour no lo entiende, **y el unico que lo entiende es el ensayo que lo construyo**.*
>
> *** Un fixture que solo sirve a un ensayo es mejor que este dentro de ese ensayo. ***

## 3. Y lo que esto cambia del plan, que hay que decir con cuidado

**El plan dice, de B02:** *«Aceptar **fixtures** de desafios, esquema cambiado, pagina vacia, corte a mitad,
reanudar y publicacion final, **mas captura acotada real cuando sea posible**.»*

```
DE LOS SEIS CASOS:
  desafio           -> ya probado (test_waf_alcampo.py, 13 ensayos, y se simula con `obtener`)
  corte a mitad      -> ya probado (VUELTAS_DE_RESCATE, VUELTAS_SIN_BLOQUEO)
  reanudar           -> ya probado (las mismas vueltas)
  publicacion final  -> ya probado (`guardar = completa` en Alcampo; y Lidl ya no publica sin precios vigentes)
  esquema cambiado   -> *** NO SE SI ESTA ***   <- HAY QUE MIRARLO, y NO SE DICE QUE FALTE
  pagina vacia       -> *** NO SE SI ESTA ***   <- HAY QUE MIRARLO, y NO SE DICE QUE FALTE
```

> **O sea: de los seis casos, **cuatro ya tienen ensayo** -- *y no en `tests/fixtures/`: **en los ensayos de los
> colectores**, que es donde se prueban las cosas de los colectores.*
>
> *Y los **dos que quedan** -- *«esquema cambiado» y «pagina vacia» -- **no se ha mirado si estan**, y **no se dice
> que falten**.* **Porque ya van nueve correcciones, y todas eran afirmar sobre lo no mirado.**

## 4. Y la regla, con su novena confirmacion

**`tests/fixtures/` vacio parecia una tarea pendiente.** *Y era **una decision del proyecto**: los fixtures viven
donde vive su parser.*

> *Lo que la descubrio no fue `grep` ni leer un fichero entero: fue **comparar los ocho fabricantes entre si** --
> *la misma herramienta que encontro que **Lidl era el unico de los seis sin `log_run`**.*
>
> *** Y esa es la herramienta que faltaba en el metodo: `ls`, leer entero, `grep` con los nombres del codigo...
> **y comparar los que hacen lo mismo**.* *Que es lo unico que distingue **«no hay nada»** de **«hay algo, y
> distinto»**.*
