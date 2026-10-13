# B09 · **`nivel()`: la marca decide **solo cuando no hay codigos** -- y la etiqueta mentia en el 30 %**

*(13 de octubre de 2026. **Y es un fallo corregido, con su medicion, su fecha y su palabra.**)*

## 1. El docstring, literal (`core/matching.py:344`)

```python
def nivel(a: dict, b: dict) -> str:
    """identico | equivalente. La distincion que pedia el proyecto.

    Mismo EAN es el mismo producto y no se discute. Distinta marca con el mismo
    formato es el equivalente de otra marca, que es justo lo que hay que comparar
    cuando las cadenas venden marca blanca y no comparten codigo de barras.

    *** La marca decide SOLO CUANDO NO HAY CODIGOS QUE COMPARAR. *** Antes decidia
    siempre, y eso hacia que el propio codigo llamara "identico" a dos productos
    con codigos de barras distintos por el hecho de compartir marca: *** medido el 22
    de septiembre, de los 1.475 enlaces marcados 'identico' con EAN en los dos
    lados, solo 1.033 (el 70 %) compartian codigo. *** *** La etiqueta mentia en el 30 %
    de los casos comprobables, *** *y quien la leyera para decidir se equivocaba.*"""
    ea, eb = _ean(a.get("ean")), _ean(b.get("ean"))
    if ea and eb: ...
```

## 2. *** Y son tres cosas, y las tres importan ***

```
*** 1) UN FALLO DE VERDAD, CON SU MEDICION ***
   *** 1.475 enlaces marcados «identico» con EAN en los dos lados ***
   *** -> y solo 1.033 (el 70 %) compartian codigo ***
   *** -> LA ETIQUETA MENTIA EN EL 30 % DE LOS CASOS COMPROBABLES *** *

*** 2) LA CAUSA, dicha sin adornos ***
   *** «la marca decidia SIEMPRE» *** *-- *o sea: **dos productos de la misma marca**
   *se llamaban **«identico»** *aunque **tuvieran codigos de barras distintos.** *
   *** -> y el nombre del veredicto -- «identico» -- era **el que mentia**, *y no el dato.*

*** 3) Y LA CORRECCION ***
   *** «Mismo EAN es el mismo producto y no se discute» *** *-> **el codigo manda** *
   *** «La marca decide SOLO CUANDO NO HAY CODIGOS QUE COMPARAR» *** *-> **y solo desempata** *
   *** y «distinta marca con el mismo formato es el EQUIVALENTE de otra marca» ***
      *-> *«que es justo lo que hay que comparar cuando las cadenas venden **marca blanca**
      y no comparten codigo de barras»*
```

> *** O sea: *** *** **el proyecto tenia una etiqueta que mentia en el 30 %, lo midio, y la arreglo** --
> *y **dejo la medicion escrita**, *con la fecha, *y con la palabra exacta: *** «mentia».** *
>
> *** Y **es la misma palabra que `formato.ts`**: *** *«un dato que no tenemos es "no lo se", nunca un cero.
> Un **0,00 €** se lee como **"gratis"** y una letra vacía como **"malo"**; *las dos cosas **serian mentira**.» *
>
> *** O sea: *** *** **la palabra «mentira» es un termino tecnico en este proyecto**, *y **aparece cuando una
> etiqueta afirma mas de lo que el dato sostiene.** *

## 3. Y **por que importa para B08 ***

```
*** EL PASO 3 (de la linea al producto) TIENE QUE DAR UN VEREDICTO, y NO un booleano ***
   -> *y `nivel` **ya ensena como se hace**: *** «identico | equivalente» *** *
   -> *y **la regla**: *** los codigos mandan; y la marca solo desempata *** *
   *** -> o sea: **un ingrediente que coincide por NOMBRE y no por codigo NUNCA es «identico»**,
      *es **«equivalente»** -- *o **`ABSTIENE`.** *
```

> *** Y **eso es lo que protege la prevision**: *** *si el paso 3 dijera **«identico»** cuando solo hay
> **parecido de nombre**, *entonces **la nutricion de un producto se atribuiria a otro**, *y **el numero
> seria una mentira** -- *y **`nivel` ya tiene la leccion escrita.** *
>
> *** Y **el `30 %` es el aviso, y con su fecha**: *** *** no es **una hipotesis de riesgo**; *
> *es **lo que paso**, *medido, *el **22 de septiembre.** *

## 4. Y el estado, con una pieza mas del paso 3

```
*** EL PASO 3 DE B08 (de la linea al producto): ***
  *** lo que hay ***     -> *** `tokens`, `trigramas`, `parecido` (con pesos), `nivel` (identico|equivalente), ***
                            *`decide` (el oraculo), `candidatos_por_gtin`/`por_bloque`, `ampliar_grupo`, *
                            *`precio_imposible`*
  *** lo que falta ***   -> *** el encadenamiento: nombre -> candidatos -> veredicto *** *
  *** y su regla ***     -> *** los codigos mandan, y la marca solo desempata (`nivel`) *** *
  *** y su vocabulario *** -> *** los CINCO veredictos, con `ABSTIENE` = «resultado valido y no un fallo» *** *
  *** y el sitio de la eleccion *** -> *`lista_linea`: `cadena_elegida`, `autorizado`, `autorizado_producto`*
```

> *** Y **lo que NO se puede hacer al escribir el paso 3**: *** *decidir por nombre y llamarlo «identico».
> *Porque **el proyecto ya pago ese error**: *1.475 enlaces, *y **el 30 % mentia.** *
