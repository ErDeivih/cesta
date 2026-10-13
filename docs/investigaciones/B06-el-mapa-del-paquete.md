# B06 · **El mapa del paquete** -- el criterio, y donde mirar. Sin abrir ninguno.

*(13 de octubre de 2026. **Lo siguiente por el plan. Y con el metodo de B05 desde la primera ronda.**)*

## 1. El criterio, literal

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:269`:

> **B06 · Nutricion por campo, cadena y universo**
>
> *Inventario de **ingredientes, alergenos, kcal, macros, fibra/sal, pesos, cantidades, origen, conservacion,
> descripcion y fechas**. **Campo nativo / enriquecido / manual**; **ausente / no aplicable / no publicado / error /
> pendiente, diferenciados**. **Cola por nuevos/cambiados/caducados, hash y presupuesto por fuente**; **no 88 horas
> de fichas sin prioridad ni pedir cada detalle estable cada dia**. **Historicos de ficha** para poder explicar
> identidad y cambios, **no mezclar precio actual con detalle obsoleto**.*

## 2. Y desglosado, son cinco cosas

```
1) EL INVENTARIO DE CAMPOS          -- ingredientes, alergenos, kcal, macros, fibra/sal, pesos, cantidades,
                                       origen, conservacion, descripcion y fechas
2) DE DONDE VIENE CADA CAMPO         -- NATIVO / ENRIQUECIDO / MANUAL
3) Y POR QUE FALTA, SI FALTA         -- *** AUSENTE / NO APLICABLE / NO PUBLICADO / ERROR / PENDIENTE ***
                                       *** y los cinco SON COSAS DISTINTAS ***
4) LA COLA CON PRESUPUESTO           -- nuevos / cambiados / caducados · hash · presupuesto por fuente
                                       *** «no 88 horas de fichas sin prioridad» ***
                                       *** «ni pedir cada detalle estable cada dia» ***
5) Y EL HISTORICO DE FICHA           -- para explicar identidad y cambios
                                       *** «no mezclar precio actual con detalle obsoleto» ***
```

> *** Y las dos que mas fondo tienen son la (3) y la (5) ***:
>
>   - **la (3)** *-- **cinco motivos distintos para que un campo no este**, y **no son intercambiables**: «no
>     aplicable» (*un producto que no lleva fibra*) **no es** «no publicado» (*la cadena no lo da*) **ni** «pendiente»
>     (*aun no se ha pedido*).* *** Es la misma doctrina que ya aparecio cuatro veces en B05: «no se sabe» no es
>     «es cero». ***
>   - **la (5)** *-- **el historico es lo que permite decir «este dato es de entonces»** -- *y **no mezclar** el
>     precio de hoy con los macros de hace tres meses. Que es, en el fondo, **el mismo problema de identidad que
>     B04 y B05**: **que es «el mismo» dato, y cuando deja de serlo.***

## 3. Y donde mirar, medido -- los ficheros que nombran nutricion

```
$ git grep -ln "nutricion|alergeno|kcal|macros" -- core/

  core/alimentos.py    core/config.py       core/datos/alcance.yml    core/datos/secciones.yml
  core/diario.py       core/matching.py     core/off.py               core/schemas.py
```

> **Y de `core/alimentos.py` ya se sabe una cosa, porque esta escrita en su propia cabecera** *(leida en la ronda
> 112 de esta sesion)*:
>
> *«**Por que existe.** El **capitulo 18 del material** mide la **cobertura de nutricion** y da un **21,6 por
> ciento**.»* *Y tiene una funcion `cobertura_sobre_comida(con_dato, de_comida, de_mezcla=0) -> dict`.*
>
> *** O sea: hay un modulo dedicado a la nutricion, con una MEDIDA de cobertura, y con un numero medido (21,6 %). ***
> *Que es **exactamente** lo que B06 pide cuando dice «por campo, cadena y **universo**».*
>
> *** Y nada mas se dice: no se ha abierto. ***

## 4. Y el orden de trabajo, el de B05

```
  1) ls de la zona                    (hecho: los ocho ficheros)
  2) LEER el fichero que el titulo nombra: *** `core/alimentos.py` ***
     -- «nutricion» es el titulo del paquete, y `alimentos` es su nombre
  3) LOS NOMBRES DE LOS ENSAYOS       -- `git grep -l nutricion tests/`, y leer sus `def test_`
  4) COMPARAR los que hacen lo mismo  -- los ocho de la lista
  5) y grep al final, con las palabras del codigo

  Y NO DECIR NUNCA: «no existe», «y nada mas», «hay que construirlo», «ya esta» sin su cita
```

> *** Y el paso (3) es el que mas informa, y el que B05 puso a trabajar: *** *los nombres de los ensayos son **la
> documentacion que no miente**, y son los que encontraron que **Lidl era el unico de los seis sin registro** y que
> **`tests/fixtures/` vacio era una decision**.*
>
> *** Y el sitio por donde empezar, por el nombre y por el titulo: `core/alimentos.py`. ***
