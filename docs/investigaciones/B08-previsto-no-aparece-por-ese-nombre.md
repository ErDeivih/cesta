# B08 · **«Previsto» no aparece por ese nombre** -- y se dice como pregunta, no como falta

*(13 de octubre de 2026. **Quinta ronda de B08. Y por primera vez en tres paquetes, una busqueda sale vacia.**)*

## 1. Lo que se midio

```
$ git grep -ln "previsto" -- plataforma/api/ plataforma/web/app/src/
   (nada)
```

> *** Y **es la primera vez en tres paquetes que una busqueda sale vacia** *** -- *y por eso **hay que tratarla con
> el cuidado que B02 enseno**:*
>
> *** una busqueda vacia **no es** «no existe»: es **«no existe con esa palabra»**. ***

## 2. Y el criterio pide, literalmente

> **B08 · Calorias integradas pero personales**
>
> *«**Vista de previstos separada del diario real.**»*

> *** Y esa es **la primera clausula**, y **la que da nombre al paquete**: *** *«calorias integradas **pero
> personales**» -- *o sea: **lo que el plan calcula que vas a comer** (*previsto*) **y lo que de verdad comiste**
> (*registrado*) **son dos cosas, y no se pueden mezclar.***
>
> *** Y el propio criterio dice **por que** al final: «**sin totalizar un dia no completo**» -- *que solo tiene
> sentido si hay **dos numeros** que se podrian sumar por error.* ***

## 3. Y por eso **no se concluye que falte**: se dice que **no se ha encontrado con esa palabra**

```
PALABRAS QUE HAY QUE PROBAR, y no se ha hecho:
  - `plan` / `planificado` / `planificada`
  - `calculado` / `calculada` / `calcula`
  - `teorico` / `estimado`
  - `necesidad` / `necesidades`        <- y esta es la que el plan usa en B05: «duplica todas las necesidades»
  - `prevision` / `previsiones`
  - y `nutricion` en la API, que si aparece en `core/`
```

> *** Y hay **un indicio que apunta a que existe**: *** *el criterio de B05 decia «**editar un menu no borra lineas
> manuales de compra ni duplica todas las NECESIDADES**» -- *y **eso es el calculo previsto***.* *Asi que **el
> concepto esta nombrado en el plan**, y **en el codigo puede estar con otro nombre**.*
>
> *** Y `test_la_previa_del_plan.py` -- leido en B05 -- empieza por `test_la_previa_dice_lo_que_entraria` y
> `test_lo_que_ya_esta_se_dice_aparte_y_no_entra`: *** *o sea, **«la previa»**.*
>
> *** Y «previa» es **la palabra que el proyecto usa**: *** *`core/previa_compra` (importado por `traspaso`),
> `test_la_previa_del_plan.py`, y `Borrador` en `importar_receta` («**la previa**, que no escribe»).*
>
> *** Asi que **probablemente la «vista de previstos» se llame «previa»** *** -- *y **no se dice que sea eso**:
> se dice **que es la palabra que el proyecto usa en tres sitios**, y **que hay que probarla**.*

## 4. Y esto es, exactamente, el error que B02 tardo diez rondas en no cometer

```
RONDA 105 (B02):   un `grep` con MIS palabras («desafio», «backoff»)  ->  «NO EXISTE NADA»   *** FALSO ***
RONDA 155 (B08):   un `grep` con MI palabra («previsto»)               ->  «no aparece por ese nombre»
                                                                          *** y la pregunta queda abierta ***
```

> *** La diferencia es **una frase**: *** *en B02 se concluyo; **aqui se dice «no aparece por ese nombre», y se
> enumeran las palabras que faltan por probar.***
>
> *** Y es, mirado bien, **la leccion de los tres paquetes anteriores**: *** **la palabra que busca el plan no es
> la que usa el codigo** -- *`backoff` era `CORTES_PARA_RENDIRSE`, `requests` era `peticiones`, `fuentes revisadas`
> era `FUENTES`, `manual` era `MANUAL` en otro modulo…*
>
> *** Y esta vez, la candidata es **«previa»**. ***

## 5. Y B08 queda asi

```
  1) PREVISTO != REGISTRADO    *** NO ENCONTRADO POR «previsto»; candidata: «previa» ***
  2) QUE SE CONFIRMA Y CON QUE HECHO -- `de_ficha` (snapshot) y `_cobertura`
  3) EL RECIBO Y SU DESHACER   HECHO -- `apunta` y `borrar`
  4) EL OBJETIVO Y LAS GRAFICAS *** POR MIRAR ***
  5) Y LA ACEPTACION           LOCALIZADA
```

> *** Y la (1) es **la unica clausula de B08 que no tiene sitio**, despues de cinco rondas. ***
>
> *** Y lo que hay que hacer con ella **no es escribirla**: es **probarla con la palabra del proyecto** -- *que es
> lo mismo que se hizo con `runlog` y con `peticiones`, y **las dos veces funciono**. ***
