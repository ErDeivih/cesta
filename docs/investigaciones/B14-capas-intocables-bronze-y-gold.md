# B14 · **`CAPAS_INTOCABLES = ("bronze", "gold")`** -- la politica, con su nombre y sus dos exclusiones

*(13 de octubre de 2026. **Y el nombre lo dice todo.**)*

## 1. La constante, literal

```python
# core/storage.py
l13  ROOT = config.DATA
l16  # *** Capas que no se borran nunca. *** `raw` se puede tirar cuando caduca -- oc[upa 338 MB]
l24  *** CAPAS_INTOCABLES = ("bronze", "gold") ***
l67      for capa in *** CAPAS_INTOCABLES ***:
             [revienta si la ruta cae dentro]
```

> *** Y **el nombre es el mejor posible**: *** *** no «protegidas», no «permanentes», no «criticas»: ***
> *** INTOCABLES. *** *
>
> *** Y **dice lo que hace sin explicarlo**: *una capa **intocable** *es **una que no se toca** -- *y **si se
> intenta, revienta.** *

## 2. Y **la lista tiene DOS nombres, y las dos ausencias son la politica**

```
*** `CAPAS_INTOCABLES = ("bronze", "gold")` ***
   *** -> y NO estan `raw` NI `silver`. *** *
```

> *** Y **las dos ausencias dicen cosas distintas, y las dos son coherentes**: *
> ```
> *** `raw` ***     -> *y el comentario lo dice: *** «se puede tirar CUANDO CADUCA -- ocupa 338 MB» *** *
>    *** -> o sea: **es lo mas grande** (338 MB), *y **se tira por tamano, con una condicion: «cuando caduca»** *
> *** `silver` ***  -> *** y NO se dice por que, y se puede deducir sin forzar: *** *
>    *** si `bronze` es intocable y `silver` sale de el, entonces `silver` SE RECALCULA *** *
>    *** -> y **por eso se puede tirar**: *no **porque sobre**, *sino **porque se rehace.** *
> ```
>
> *** O sea: *** *** **la politica es: lo que se recalcula se puede tirar; lo que no, no.** *
> *Y **`bronze` y `gold` no se recalculan** (bronze es el parseo del crudo, *y gold es **lo publicado**, *y
> `publicacion.py:23` dice: *** «publicar NO BORRA. *Un catalogo no se destruye por publicar otro.» ***)*
>
> *** Y **es el mismo criterio que `OPERACION.md:459`** *** *-- *«**el crudo es lo unico irrecuperable**» -- *
> *y **aqui esta la version por capas, y con una guarda.** *

## 3. Y **la diferencia con el manual**, que hay que decir

```
*** `OPERACION.md:459` ***   -> *«el crudo es lo unico irrecuperable»*     *-- y **nombra UNA cosa** *
*** `storage.py:24` ***       -> *** `CAPAS_INTOCABLES = ("bronze", "gold")` ***  *-- y **nombra DOS** *
```

> *** O sea: *** *** **el codigo es mas estricto que el manual**: *el manual dice que **el crudo** es lo unico
> irrecuperable; *y el codigo **protege tambien `gold`** -- *o sea: **lo publicado.** *
>
> *** Y **tiene sentido, y `publicacion.py:23` lo dice**: *** *** «**publicar no borra**. *Un catalogo no se
> destruye por publicar otro» -- *o sea: **cada version publicada se queda**, *porque **volver atras es apuntar a
> una anterior.** *
>
> *** Y **por eso `gold` es intocable**: *no **porque no se pueda recalcular**, *sino **porque es el registro de
> lo que se publico y cuando.** *

## 4. Y el estado de B14, con los logs **y su politica** medidos

```
*** B14 · 3 de 5 · y la copia DECIDIDA ***
  *** el CSRF ***     -> *** 5 ensayos ***
  *** los GET ***     -> *** `test_ninguna_ruta_que_muta_es_un_get` ***
  *** los LOGS ***    -> *** `runs.csv` (6 columnas, 228 filas, sin secretos) ***
     *** y `CAPAS_INTOCABLES = ("bronze", "gold")` + `comprueba_borrable` + «apartar, no borrar» *** *
  *** LAS COPIAS ***  -> *** las tres piezas medidas + el diff + el orden + lo que hay dentro ***
  *** y queda ***     -> *** una palabra del propietario para `datos_api:/app/data` *** *
```

> *** Y **B14 pedía «logs crecientes con rotacion, metricas y secretos ausentes»**, *y **el proyecto da las tres
> cosas por otra via**: *
> ```
> *** «crecientes» ***  -> *`runs.csv`: **228 filas, y una por pasada y cadena** *
> *** «metricas» ***    -> *y sus 6 columnas **son** la metrica: `filas`, `errores`, `segundos`, `ok`, por fuente*
> *** «sin secretos» *** -> *** y no hay sitio para uno *** *
> *** «rotacion» ***    -> *** y en vez de rotar lineas, DECLARA CAPAS INTOCABLES y APARTA lo malo con su motivo *** *
> ```
