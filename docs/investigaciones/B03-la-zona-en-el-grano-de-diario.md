# B03 · **La zona en el grano de `diario`** -- la decision, y por que no es tan grande

*(13 de octubre de 2026. **Se dijo que hacia falta «decidir si un precio es por producto y dia o por producto,
dia y zona». Y medido, la decision es mas pequena de lo que parecia.**)*

## 1. Lo que es `diario`, medido

```
table_type: VIEW

  fuente              VARCHAR
  id_fuente           VARCHAR
  precio_cent         BIGINT
  precio_unidad_cent  DOUBLE
  unidad_canon        VARCHAR
  producto_id         VARCHAR
  fecha               VARCHAR
```

> **No es una tabla: es una vista.** *Y su grano es `(fuente, id_fuente, fecha)`.*
>
> **Y eso cambia la pregunta.** *No hay que decidir «que significa una fila de una tabla» -- **hay que anadir
> una columna a una proyeccion**, y que la vista la saque de gold.*

## 2. Y la respuesta al miedo: **hoy no multiplica nada**

*El miedo era: «si hay zonas, un precio por producto y dia deja de ser cierto: hay uno por zona».*

**Y es verdad en general, y hoy no pasa** -- *medido:*

```
  fuente       regiones distintas
  alcampo      0   (region vacia)
  aldi         0
  carrefour    0
  dia          0
  mercadona    0
  lidl         1   ("28")
```

> **Una sola zona por fuente.** *Asi que anadir `region` al grano **no multiplica ninguna fila hoy**: la clave
> pasa de tres campos a cuatro, y el cuarto tiene **un solo valor por fuente**.*
>
> **Y el dia que una fuente publique dos zonas, la clave ya estara bien puesta** -- *que es la diferencia entre
> anadirlo ahora, cuando es barato, o descubrirlo cuando ya hay filas mezcladas.*

## 3. Y `region` **vacia** en las otras cinco, que hay que decir que significa

*Mercadona y Aldi fijan la zona **al pedir** -- `config.CODIGO_POSTAL` y `ALDI_SCOPE` --, y **la respuesta no
viene etiquetada con ella**.* *Carrefour y DIA no publican precio por zona.*

> **Asi que `region` vacia en esas cinco quiere decir «no se declara por fila», no «no tiene zona».** *Y eso
> **no hay que arreglarlo inventando un valor**: hay que **decirlo**, que es lo que esta fase hace con todo.*
>
> *Y es la misma distincion de siempre, ahora en una columna: un `NULL` que dice «no se sabe» y un `"28"` que
> dice «se sabe y es esta».*

## 4. Asi que el cambio son **tres pasos, no una decision dificil**

  1. **`a_silver` tiene que llevarse `region` de bronze.** *Hoy selecciona columnas y la deja caer.*
  2. **Y gold tiene que guardarla** -- *que es donde esta el trabajo de verdad, porque gold se reconstruye dia
     a dia desde bronze (`pipeline.py:629`), asi que **hay que reconstruir el historico** o aceptar que las
     filas viejas se quedan sin zona.*
  3. **Y la vista `diario` la expone**, *y `region` entra en su clave.*

**Y el paso 2 es el que tiene la decision de verdad, y es esta**: *¿se reconstruye el gold entero -- que son
**37 dias** --, o se deja el historico sin zona y solo la llevan las filas nuevas?*

> **Y hay un argumento para reconstruir**: *las 37 jornadas salen del mismo bronze, y **`region` para Lidl
> depende de la zona que se acredito cada dia** -- que puede cambiar si el propietario cambia su CP.* *Dejarlo
> a medias daria un historico donde unas filas dicen la zona y otras no, **sin que se pueda saber por que**.*
>
> **Y otro para no hacerlo**: *reconstruir gold toca el historico de las seis cadenas, y **eso no es B03**.*

## 5. Y lo que se decide, con lo medido delante

**Se hace el paso 1 (`a_silver`), que es el que no toca nada historico**, *y **se deja dicho** que el paso 2
--propagar a gold-- es una decision sobre el historico, con las dos opciones y sus costes.*

> *Y esto no es escurrir el bulto: es que **el paso 1 es reversible y el 2 no**.* *Anadir `region` al silver
> no cambia ninguna cifra; **reconstruir 37 dias de gold de las seis cadenas es otra clase de cambio**, y
> merece su propia ronda y su propia prueba.*
