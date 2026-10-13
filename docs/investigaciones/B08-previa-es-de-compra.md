# B08 · **«Previa» es de COMPRA, no de nutricion** -- y la pregunta se afina, sin cerrarse

*(13 de octubre de 2026. **Sexta ronda de B08. Y la candidata resulto ser otra cosa.**)*

## 1. Lo que se encontro al probar «previa»

```
core/previa_compra.py:90:   def previa_de_compra(ingredientes) -> Pre[via...]
core/traspaso.py:29:        from core import previa_compra
core/traspaso.py:132:       previa = previa_compra.previa_de_compra(hallada["ingredientes"])
core/importar_receta.py:116: «la misma decision que `previa_compra` tomo en ...»
core/envases_enteros.py:5:   «`core/previa_compra.py::_tamano_del_envase` pedia el ...»
```

> *** Y `previa_compra` es **la previa DE LA COMPRA**: *** *la que **B04** usa en los dos puentes -- *«la previa de
> cantidades» --, y **no la de la nutricion**.*
>
> *** O sea: **la candidata era otra cosa** *** -- *y **eso es exactamente lo que se buscaba**: **una palabra que el
> proyecto usa, pero para otro concepto.***
>
> *** Y es el mismo caso que **`fuente`**: *** *en `importar_receta` era **la fuente de la receta**, y en el
> ingrediente era **otra cosa** -- *y el docstring lo decia: «el campo `fuente` que hay es **del ingrediente**».*
>
> *** Cuarta vez: `cadena`/`fuente` (B04), `fuente` del ingrediente (B07), `MANUAL` (B08), y ahora `previa`. ***

## 2. Y entonces la pregunta de B08 queda **mas fina**, y sigue abierta

```
LO QUE SE SABE AHORA:
  - «previsto» no aparece por ese nombre en la API ni en el frontend;
  - «previa» SI aparece, y es DE COMPRA (`previa_compra.previa_de_compra`) -- *** no es el previsto nutricional ***;
  - y `test_la_previa_del_plan.py` habla de «la previa» DEL PLAN -- o sea, *de lo que entraria en la lista*,
    *** que tampoco es el previsto nutricional ***.

LO QUE QUEDA POR PROBAR:
  - `plataforma/api/analisis.py` -- *** que salio en la lista de «previa», y NO SE HA MIRADO ***
  - «necesidad»/«necesidades» -- *la palabra que el plan usa en B05*
  - y las demas: planificado · calculado · teorico · prevision
```

> *** Y `plataforma/api/analisis.py` es **la pista mas directa** *** -- *porque **hay un modulo de API que se llama
> «analisis»**, **y el paquete se llama «calorias integradas»**.*
>
> *** Y no se dice que ahi este: se dice que **es el sitio que queda por mirar**, y **por que**. ***

## 3. Y esto es lo que hay que subrayar del metodo: **la busqueda vacia se convirtio en dos preguntas mejores**

```
ANTES DE ESTA RONDA:  «previsto no aparece» -- una ausencia, y una tentacion de concluir
DESPUES:              - «previsto» no aparece                     (medido)
                      - «previa» SI, y es de COMPRA               (medido, y descarta la candidata)
                      - y queda `api/analisis.py`                  (la pista)
```

> *** O sea: **la busqueda vacia no se cerro con un «no existe»**: *** *se **probo la candidata**, **resulto ser de
> otro concepto**, y **eso dejo una pista mejor** -- *`api/analisis.py`, que **salio en la lista y no se miro**.*
>
> *** Y es, en pequeno, **la historia entera de esta sesion**: *** **cada respuesta falsa dejo el sitio donde estaba
> la verdadera.** *«No existe nada» dejo `RetoWAF`. «Y nada mas» dejo `runlog` y `peticiones`. Y **«previsto» deja
> `api/analisis.py`**.*

## 4. Y B08, con seis rondas, tiene **cuatro de cinco**, y una con pista

```
  1) PREVISTO != REGISTRADO    *** NO ENCONTRADO; candidata «previa» DESCARTADA (es de compra);
                               pista: `plataforma/api/analisis.py` ***
  2) QUE SE CONFIRMA Y CON QUE HECHO -- `de_ficha` (snapshot) y `_cobertura`
  3) EL RECIBO Y SU DESHACER   HECHO -- `apunta` (que rechaza `compra`) y `borrar`
  4) EL OBJETIVO Y LAS GRAFICAS *** POR MIRAR *** -- y **el objetivo es «opcional por persona y fecha»**
  5) Y LA ACEPTACION           LOCALIZADA -- los quince ensayos, con las cifras
```

> *** Y las dos que quedan -- **previstos** y **objetivo** -- son **las dos de la VISTA**: *** *la (1) es **un
> numero que se calcula y no se ha comido**, y la (4) es **un numero que se pone como meta**.*
>
> *** Y las dos, juntas, son **la frase del paquete**: «calorias integradas **pero personales**». ***
