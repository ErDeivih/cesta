# B09 · **Los nombres de los ensayos trazan las fronteras**: «nunca exacto», «alternativa no identidad»

*(13 de octubre de 2026. **Tercera ronda de B09. Y las dos reglas del EAN empiezan a aparecer.**)*

## 1. Los nombres, en `tests/test_identidad.py`

```
test_sin_gtin_compatible_es_probable_y_NUNCA_EXACTO          <- «probable», y JAMAS «exacto»
test_marcas_distintas_son_ALTERNATIVA_no_IDENTIDAD            <- «alternativa» NO es «identidad»
test_los_negativos_son_misma_marca_y_codigo_distinto          <- y la marca distingue
```

> *** Y los tres nombres **no describen un caso: trazan una frontera**. *** *«Probable **y nunca exacto**»,
> «alternativa **no identidad**» -- *o sea: **el nombre dice que dos veredictos NO se pueden confundir**.*
>
> *** Y eso es **exactamente** la clausula (3) de B09: *** *** «exacto/familia/alternativa/desconocido
> **VISIBLES**» *** -- *y **«visibles» quiere decir que se distinguen**, y **estos nombres son la prueba de que se
> distinguen.***

## 2. Y contestan **las dos reglas del EAN** de la clausula (4)

```
B09 PIDE:  «EAN COINCIDENTE NO NEUTRALIZA FORMATO INCOMPATIBLE;
            DISTINTO NO ACREDITA MISMO ARTICULO»
```

> *** Y los tres nombres son **casos concretos de las dos reglas**: ***
>
>   - **`test_sin_gtin_compatible_es_probable_y_nunca_exacto`** *-- *sin GTIN compatible, **el veredicto no llega a
>     «exacto»**: **se queda en «probable»**.* *** O sea: **que se parezca no lo acredita.** ***
>   - **`test_marcas_distintas_son_alternativa_no_identidad`** *-- *marcas distintas => **alternativa**, **no
>     identidad**: *** que se diferencien en la marca **lo saca de la identidad** *** -- *que es **la otra mitad**:
>     «distinto no acredita mismo articulo»... **al reves**: *«distinto **desacredita**».*
>   - **`test_los_negativos_son_misma_marca_y_codigo_distinto`** *-- *y aqui hay **un caso de «parecido pero
>     distinto»**: **misma marca, codigo distinto**.*
>
> *** Y las tres juntas **son las dos reglas, en tres ejemplos**: *** **sin GTIN -> probable; marca distinta ->
> alternativa; codigo distinto -> otra cosa.** *
>
> *** Y los tres son **fronteras de la misma escala**, que es lo que hace que el veredicto sea **visible**. ***

## 3. Y aparece la palabra que el criterio NO decia: **«probable»**

```
EL CRITERIO DICE:   exacto / familia / alternativa / desconocido
EL ENSAYO DICE:     *** «probable» ***
```

> *** O sea: **hay un quinto nombre** -- *o **«probable» es el nombre interno de uno de los cuatro**.*
>
> *** Y no se dice cual, porque **no se ha leido `identidad.py`**. *** *Pero **se dice que aparece**, y **donde**.*
>
> *** Y es **la misma clase de hallazgo que `MANUAL` en B08**: *** *el mismo concepto, **con un nombre que el
> criterio no usa** -- *y **que hay que leer para saber si es un quinto veredicto o el nombre de campo de uno de los
> cuatro**.*
>
> *** Segunda vez en dos paquetes. ***

## 4. Y B09, con tres rondas

```
  1) REUTILIZAR (y ser INDEPENDIENTE)  *** HECHO: *** `oraculo_reparto.py` NO IMPORTA `cesta.py`, y su
                                       docstring razona por que: «si los dos coinciden, es porque los dos
                                       calculan bien, no porque compartan el mismo codigo»
  2) EL BANCO DE PARES                 `core/banco_de_pares.py` + `tests/test_banco_de_pares.py` -- POR LEER
  3) LOS CUATRO VEREDICTOS             *** LOCALIZADOS: *** `test_identidad.py` los nombra por sus fronteras
                                       («nunca exacto», «alternativa no identidad») -- y aparece un QUINTO
                                       nombre, **«probable»**, cuyo sitio POR LEER
  4) LAS DOS REGLAS DEL EAN            *** tres ensayos son casos de las dos reglas *** -- y `identidad.py`
                                       POR LEER
  5) Y LA PROHIBICION DEL ORDINAL      *** POR MIRAR ***
```

> *** Y el «COMPLETO» del titulo ya no preocupa: *** *el oraculo **dice lo que cubre y lo que no**, con su razon y
> con su numero (**2400 vs 1900**), y **prefiere estar incompleto antes que elegir una lectura y llamarla verdad**.*
>
> *** Que es **la decimosexta vez** que aparece la doctrina, y **la primera en que se aplica a una DECISION en vez de
> a un dato**: *** *no se decide lo que no se puede decidir -- **y se dice.***
