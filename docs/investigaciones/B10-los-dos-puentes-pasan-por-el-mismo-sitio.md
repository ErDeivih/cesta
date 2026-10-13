# B10 · **Los DOS puentes pasan por el mismo sitio** -- y el codigo lo dice

*(13 de octubre de 2026. **Septima ronda de B10. Y la restriccion del propietario queda cerrada en los dos lados.**)*

## 1. La comprobacion, medida

```
PLAN -> LISTA      `plataforma/api/main.py:1625 def traer_del_plan(...)`

  l1608: *** «**Y AQUI ESTA LA CONSOLIDACION, QUE ES LA MISMA QUE LA DEL OTRO PUENTE.** *`...`» ***
  l1669:  `almacen.anade_linea(lista_id, usuario["id"], ...)`

RECETA -> LISTA    `plataforma/api/recetas.py:236 def a_la_lista(...)`

  l241:  «el servidor -- *el propietario es `usuario["id"]` y la semana la calcula `traspaso.sem[ana_de]`*»
  l247:  *** «-- asi que **la idempotencia esta DOS VECES**: `traspaso` impide la segunda operacion,
          `almacen.anade_linea` **ya es un upsert** (*«el id lo trae el movil; si llega dos vece[s]...»*)» ***
  l251:  `from core import traspaso`
  l263:  `def insertar(lineas) -> str:`
```

## 2. Y contesta **las dos mitades** de la restriccion del propietario

```
RESTRICCION:  «el fallo de que 300 g necesarios terminan como una unidad y una nota de 100 g,
               descartando la segunda receta como repetida.
               *** Afecta a AMBOS puentes de transferencia (receta->lista y plan->lista). ***»
```

> *** Y la primera mitad -- «el fallo» -- esta en `almacen.py:415-448` ***: *`GREATEST` + `LEAST` +
> `COALESCE(cantidad_en, 'epoch')` + «la hora del movil», *con el defecto escrito («esto era `cantidad = %s`... y
> ganaba la de las 17:50 que llego a las 18:31»).*
>
> *** Y la segunda mitad -- «AMBOS puentes» -- esta en las dos lineas de arriba: ***
>
>   - **`main.py:1669` llama a `almacen.anade_linea`** -- *o sea, **el puente del plan usa el upsert que tiene las
>     dos reglas**;*
>   - **`recetas.py:263` define `insertar` y lo pasa a `traspaso`** *-- *y **el docstring dice que
>     `almacen.anade_linea` «ya es un upsert»**.*
>
> *** Y **`main.py:1608` cierra la pregunta del todo**: ***
>
> > *** «Y AQUI ESTA LA CONSOLIDACION, **QUE ES LA MISMA QUE LA DEL OTRO PUENTE**.» ***
>
> *** O sea: **no hay dos consolidaciones que podrian divergir**: *** *hay **una**, *y **el comentario del segundo
> puente dice que es la misma del primero**.* *
>
> *** Que es **exactamente lo que la restriccion del propietario necesitaba saber** -- *y **el proyecto lo tiene
> escrito**, no deducido.*

## 3. Y la idempotencia esta **dos veces**, y el codigo dice por que

> *** `recetas.py:247`: *** *** «la idempotencia esta DOS VECES: `traspaso` impide la segunda operacion,
> `almacen.anade_linea` ya es un upsert» ***
>
> *** Y las dos no son redundancia: ***
>
> ```
> `traspaso`            -> identidad de la OPERACION     -> «la misma operacion no se repite»
> `almacen.anade_linea` -> upsert por `id` de LA LINEA   -> «la misma linea se actualiza, no se duplica»
> ```
>
> *** O sea: **una capa impide repetir el ENUNCIADO, y la otra impide duplicar el RESULTADO** *** -- *y **hacen falta
> las dos**, porque **una operacion puede generar varias lineas** (la identidad es de la operacion, **no de la
> linea**) **y una linea puede llegar por caminos distintos** (el id lo trae el movil).*
>
> *** Y es **la respuesta completa a la clausula (2) de B05** -- *«idempotencia **y consistencia entre almacenes**»
> --: **dos capas, dos identidades, y cada una en su almacen.** *

## 4. Y B10 queda con **seis de siete**, y la restriccion **cerrada**

```
  1) LOS ESTADOS           *** LEIDO: `almacen.py:415-448` -- LEAST/GREATEST, la hora del movil ***
  2) LAS LISTAS Y EL ORDEN HECHO -- 15 ensayos
  3) BUSCAR Y FILTRAR      *** POR MIRAR *** -- «marca/formato/EAN y filtros utiles»
  4) LA PAGINACION         MEDIDA -- `limite` con cotas; sin `cursor`/`version`/`offset`
  5) EL GASTO Y EL AHORRO  HECHO -- 17 ensayos
  6) Y LA DUREZA           *** HECHO, y con los DOS PUENTES LOCALIZADOS ***
  7) Y EL OBJETIVO         *B10 no lo pide; es de B08*
```

> *** Y lo unico que queda de B10 es **(3) buscar y filtrar** *** -- *«busqueda con marca/formato/EAN y filtros
> utiles» -- *que es **una clausula de pantalla**, y **la unica del paquete que no ha aparecido ni en los nombres de
> `almacen.py` ni en los ensayos leidos**.*
>
> *** Y **no se dice que no exista**: *** *se dice que **no aparece en los nombres que se han leido**, *y que **las
> palabras que hay que probar son `busca`, `filtro`, `marca`, `formato` y `ean`** -- *y **`EAN` ya salio en B09**
> (`identidad.py`, `normaliza_gtin`).*

## 5. Y lo que esta ronda deja, que es lo mas importante de B10

> *** La restriccion del propietario **no era una sospecha: era un defecto, y esta arreglado, escrito y probado** ***
> -- *y **la unica pregunta que quedaba** («¿afecta a los dos puentes?») **tiene dos respuestas en el codigo**:*
>
>   1. **los dos llaman al mismo upsert** (`main.py:1669` y `recetas.py` -> `almacen.anade_linea`);
>   2. **y el comentario lo dice**: «**la consolidacion, que es la misma que la del otro puente**».
>
> *** Que es **la forma en que este proyecto contesta**: *** *no con una afirmacion en un informe, **sino con una
> linea de codigo que se puede abrir** -- *y **con su razon escrita al lado.** *
