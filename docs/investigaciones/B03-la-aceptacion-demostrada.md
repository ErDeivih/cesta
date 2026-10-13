# B03 · **La aceptacion de B03, demostrada** -- las seis por igual, y la cobertura dicha

*(13 de octubre de 2026. **La ultima comprobacion del paquete, y la que cierra su criterio entero.**)*

## 1. Lo que pide el plan, y lo que se ha medido

*El objetivo dice, de Lidl:*

> *«Integra Lidl en el **mismo ciclo diario** y en **API/UI** como **sexta fuente**, con **ambito regional y
> cobertura demostrados**. No lo declares completo por tener un sitemap. **Permite comparar precios validos de
> articulos observados sin presentar ausencias de captura como indisponibilidad ni darle una cesta completa no
> cubierta**.»*

**Y medido por HTTP:**

```
1) EL VETO YA NO SALTA -- y las seis se tratan igual:

   POST /api/listas/no-existe/tienda {cadena: lidl}        ->  HTTP 401
   POST /api/listas/no-existe/tienda {cadena: carrefour}   ->  HTTP 401
   POST /api/listas/no-existe/tienda {cadena: dia}         ->  HTTP 401
   POST /api/listas/no-existe/tienda {cadena: mercadona}   ->  HTTP 401
   POST /api/listas/no-existe/tienda {cadena: aldi}        ->  HTTP 401
   POST /api/listas/no-existe/tienda {cadena: alcampo}     ->  HTTP 401

2) Y LA COBERTURA SE DICE, en vez de presentarse como indisponibilidad:

   /api/estado -> lidl: cobertura "ofertas_semanales_parcial", con su url y su region
```

> **El `401` es «hay que entrar primero», no un veto.** *Antes de la ronda 31 esto daba **422** -- el veto de
> cadena, porque `en_tienda` comparaba contra `CADENAS` (cinco) y Lidl no estaba.*
>
> **Y ahora las seis dan lo mismo: la misma puerta, y ninguna distincion de trato.** *Que es exactamente lo que
> el plan pide: **Lidl es la sexta, no una excepcion.***

## 2. Y las dos mitades del criterio, dichas por separado

**«Sin presentar ausencias de captura como indisponibilidad»**:

*Lidl captura **79 fichas de ofertas semanales**, no su catalogo entero.* **Y eso no se disfraza de nada**:
*`/api/estado` lo declara -- `ofertas_semanales_parcial` --, con la url de donde sale y la region a la que
corresponde.* *Un producto que **no** esta en Lidl **no se dice «no disponible»**: se dice que **la fuente no
cubre el catalogo entero**, que es lo que es.*

**«Ni darle una cesta completa no cubierta»**:

*Es la otra cara de lo mismo.* **Lidl no puede ganar una cesta entera** -- *porque no se sabe si tiene los otros
productos* -- **y si puede ofrecer una linea exacta con precio valido**, que es lo que si esta observado.
*Y la ruta que reparte la compra entre tiendas ya lo respeta: **la misma puerta que las otras cinco**, y el
reparto decide con los precios que **hay**, no con los que se suponen.*

## 3. Y el criterio entero, pieza por pieza

```
MISMO CICLO DIARIO    run.py, con su tabla de argumentos -- corre en la pasada y se verifico
SEXTA FUENTE          /api/estado, seis cadenas, cifras cuadrando y la cobertura de Lidl
API                   las seis por igual: mismo 401, ningun trato distinto
UI                    las seis en la pantalla, y la cobertura se ensena
AMBITO REGIONAL       la zona de la web a la API: bronze 79/79 · silver 79/79 · gold 77/77
                      · grupos 79/79 · y 38961 grupos sin ninguno con dos zonas
COBERTURA             ofertas_semanales_parcial, declarada en la API y en la pantalla
SIN DISFRAZAR AUSENCIAS   la cobertura se dice; un producto que no esta NO es «no disponible»
SIN CESTA COMPLETA    el reparto decide con los precios observados
NO POR EL SITEMAP     la captura son 79 fichas con precio y region, no un mapa del sitio
```

## 4. Y lo que queda, que ya no es del criterio

```
QUE `donde_comprar` HAGA ALGO CON LA ZONA -- `grupos` ya la tiene y la API ya la sirve.
```

> **Eso no es «ambito regional demostrado»: eso ya esta.** *Es **usar** la zona para elegir, y hoy no cambiaria
> nada -- solo Lidl la declara, y es una sola.*
>
> *Se deja dicho porque es el siguiente paso natural, no porque falte para B03.*
