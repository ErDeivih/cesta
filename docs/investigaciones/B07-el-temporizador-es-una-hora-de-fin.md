# B07 · **`core/cocina.py`**: el temporizador **no es una cuenta atras, es una hora de fin**

*(13 de octubre de 2026. **Segunda ronda de B07. Y el fichero no tiene una pieza: tiene una idea.**)*

## 1. Lo que hay: 175 lineas, y tres nombres

```
core/cocina.py -- 175 lineas

  l43: def minutos_de(texto: str | None) -> int | None
  l67: class Temporizador:
  l92: class Cocina:
```

## 2. Y su docstring **razona la decision del modulo**, entera

```python
"""F10 / `R05`: **el modo cocina** -- paso actual, ingredientes usados, temporizadores y reanu[dacion].

El criterio (`docs/SUPERAPP-COMPETENCIA-Y-REA.md:105`) dice:

> **Paso actual, ingredientes usados, temporizadores** y **reanudacion sin conexion cuando sea** [...]

**Medido el 11 de octubre de 2026** (`docs/investigaciones/F09-recetario.md` §10), *el modo co[cina
no existia]*, y lo mejor del hallazgo fue que **el propio proyecto lo dijo sin querer**:
`plataforma/prueba_[...]` «y no es una visita guiada: **no hay pasos que pasar**».

## Y la parte que hay que pensar no es el paso: es el **tiempo**

**«Paso actual» e «ingredientes usados» son estado, y el estado se guarda.** *Pero **un tempor[izador
no se] guarda**: se **cuenta**.*

**Y ahi esta la decision de este modulo:** ***un temporizador NO es una cuenta atras.*** *Una [cuenta
atras vive] en la pantalla, y **muere con ella**: *si se apaga el movil, o se recarga, o se va la
conexion, [lo] transcurrido se pierde** -- *y quien esta cocinando **no se entera** hasta que algo se
quema.*

**Un temporizador es una **hora de fin**.** *Se guarda `empezo_en` y `minutos`, y **lo que que[da]**
**reanudar es volver a leer**, y **funciona sin conexion** *porque **no hay nada que consultar**[: lo]
lleva el aparato.*

> **Es la misma forma que `F15` encontro en la aplicacion**: *React Query **pausa** las mutaci[ones]
> -- *no las pierde.* **Y aqui: el tiempo **no se pierde**, porque **no se estaba contando**. *
"""
```

## 3. Y contesta **la clausula de cocina** de B07, con su razon

```
B07 PIDE                                        Y AQUI ESTA
  «COCINA RECUPERABLE, pasos/temporizadores
   y preparado/pendiente, SIN DECLARAR CONSUMO»   *** `class Cocina` -- el paso actual ***
                                                  *** `class Temporizador` -- y con la decision de diseño ***
                                                  *** «reanudacion SIN CONEXION» -> resuelta ***
                                                  *** «SIN DECLARAR CONSUMO» -> POR MIRAR (no se ha leido el cuerpo) ***
```

> *** Y la decision de diseño es lo que hay que subrayar, porque es **la respuesta a una pregunta que no se habia
> hecho**: ***
>
> *«Reanudable» suena a **guardar el estado**. Y **eso funciona para el paso actual** -- *que es estado.* **Pero no
> para el tiempo** -- *porque **el tiempo no es estado, es un contador***.
>
> *** Y la solucion no es «guardar el contador»: es **no contar**. ***
>
> *Se guarda **cuando empezo** y **cuanto dura**, y **lo que queda se calcula al leer**. Asi que:*
>
>   - **sobrevive a recargar** *-- *no hay nada vivo que perder;*
>   - **sobrevive a perder la conexion** *-- *no hay nada que consultar: **lo lleva el aparato**;*
>   - **y sobrevive a apagar el movil** *-- que es **el caso que importa**, porque *«quien esta cocinando **no se
>     entera** hasta que algo se quema».*
>
> *** Y el docstring emparenta la idea con otra que ya existia: *** *«React Query **pausa** las mutaciones -- no
> las pierde. Y aqui: el tiempo **no se pierde, porque no se estaba contando**.»*
>
> *** Que es **la misma ley de las nueve de B06**, con otra cara: *** **un dato que se puede recalcular no hay que
> guardarlo** -- *y **guardarlo mal** es lo que hace que se pierda.*

## 4. Y hay un dato de proceso que vale

**«Medido el 11 de octubre de 2026..., el modo cocina [no existia], y lo mejor del hallazgo fue que EL PROPIO
PROYECTO LO DIJO SIN QUERER: `plataforma/prueba_...` "y no es una visita guiada: **no hay pasos que pasar**".»**

> *** O sea: **el modo cocina no existia el 11 de octubre, y se supo por un mensaje de la propia herramienta de
> prueba** *** -- *que es **exactamente** el metodo que esta sesion ha usado tres veces: **leer los nombres y los
> mensajes**, que **son la documentacion que no miente**.*
>
> *** Y es la tercera pieza que **no existia el 11 de octubre y se creo despues**: *** *la despensa (017), el modo
> cocina (`cocina.py`), y... **y las tres con la regla escrita dentro**.*

## 5. Y lo que NO se dice

**No se han leido las 175 lineas.** *No se dice qué campos tiene `Cocina` ni `Temporizador`, ni si `minutos_de`
parsea «20 min» de un texto.*

```
POR LEER:
  - el cuerpo de `minutos_de` (l43-67), `Temporizador` (l67-92) y `Cocina` (l92-175)
    *** y ahi esta «SIN DECLARAR CONSUMO»: si `Cocina` toca el diario o no ***
  - y `tests/test_detalle_receta.py` y `tests/test_editar_receta.py` -- los nombres de sus ensayos
  - y `core/importar_receta.py`, que es la clausula con MAS guardas (SSRF, redirecciones, tamano, timeout)
```
