# G09 · **Lidl NO es «el catalogo de Lidl»: es «ofertas conocidas», y por region** -- y una **contradiccion**

*(2026-10-14, ~02:00. **Y la cabecera de `lidl.py` dice las ocho cosas, y la ultima contradice a `run.py`.**)*

## 1. Lo que la cabecera dice, y es del propio colector

```
*** `projects/cesta/collectors/lidl.py` ***
l1   *** «Lidl: OFERTAS CONOCIDAS de su pagina publica, con cobertura parcial dicha por delante.» ***
l3-5 *** «**Que es y que no es.** Esto *** NO ES EL CATALOGO DE LIDL. *** Es una lectura de su pagina publica
     de OFERTAS SEMANALES (`/c/ofertas-semanales/...`), que publica *** un numero acotado de fichas con
     precios POR REGION. *** Por eso:» ***
l7   *** «- se llama OFERTAS CONOCIDAS, y el nombre lo dice el propio fichero de cobertura que escribe;» ***
l8   *** «- NO SE DECLARA A LIDL GANADOR DE UNA CESTA si le faltan productos;» ***
l9   *** «- la ausencia de un producto en la campana NO es que se haya retirado.» ***
l13  *** «- robots.txt primero, y una sola pagina. Sin API movil, sin login, sin rastrear bricolaje.» ***
l14-15 *** «- El EAN NO SE INVENTA. La ficha trae `ians` e identificadores internos; ninguno es un EAN
     comprobado, asi que `ean` va vacio. *** UN CODIGO INVENTADO ENVENENA LAS COMPARACIONES (T03). ***» ***
l16-17 *** «- El precio tachado NO ES EL PRECIO. Lo que se cobra va en `precio_cent` y el anterior en
     `precio_anterior_nativo_cent`: *** confundirlos seria anunciar una bajada que no existe. ***» ***
l18-19 *** «- LA REGION SE RESUELVE ANTES DE MIRAR EL PRECIO (`regionsV2[region].regionPriceId`), y el precio
     del club de Lidl se conserva como lo que es: *** UNA CONDICION, NO EL PRECIO GENERAL. ***» ***
l20  *** «- El estado de la region NO ES STOCK. No hay stock en esta fuente y no se finge.» ***
```

> *** Y **son ocho clausulas, y hay que leerlas porque cada una es una decision**: *
> ```
> *** 1) NO ES EL CATALOGO ***  -> *son **ofertas semanales**, *y **el nombre lo dice**: «ofertas conocidas»*
> *** 2) Y CON PRECIOS POR REGION ***  *-- *y **aqui esta la respuesta al propietario.** *
> *** 3) NO DECLARA GANADOR A LIDL SI LE FALTAN PRODUCTOS ***  *** <- es el encargo, literal *** *
> *** 4) LA AUSENCIA EN LA CAMPANA NO ES RETIRADA ***          *** <- es el encargo, literal *** *
> *** 5) ROBOTS.TXT PRIMERO, UNA PAGINA, SIN LOGIN ***          *-- *y **no elude nada** *
> *** 6) EL EAN NO SE INVENTA ***  *-- *«un codigo inventado **ENVENENA LAS COMPARACIONES**»*
> *** 7) EL PRECIO TACHADO NO ES EL PRECIO ***  *-- *«confundirlos seria **anunciar una bajada que no existe**»*
> *** 8) Y EL PRECIO DEL CLUB ES UNA CONDICION, NO EL PRECIO GENERAL *** *
> ```

## 2. *** Y contradice lo que B02 midio: hay que resolverlo ***

```
*** `lidl.py:22-23` DICE: *** *** «**NO ESTA EN LA TAREA DE LAS 06:00, A PROPOSITO.** *La ampliacion lo pide
asi: *"pasar una captura acotada antes de anadirlo a la tarea diaria". *** SE EJECUTA A MANO Y NO PUEDE ROMPER
LA PASADA DIARIA. ***» *

*** Y `run.py:40` DICE: *** *** `ORDEN = ["carrefour","dia","mercadona","aldi","alcampo","*** lidl ***"]` *** *
   *-- *y **es lo que me hizo escribir, en B02, «**Lidl ES el sexto**».** *
```

> *** O sea: *** *** **una de las dos frases esta desactualizada, y NO SE PUEDE SUPONER CUAL.** *
>
> *** Y **las dos son posibles**: *
> ```
> *** a) el DOCSTRING esta viejo ***  -> *se escribio cuando Lidl **no** estaba en la tarea, *
>    *y **despues se anadio a `ORDEN`** -- *y entonces **la frase de `l22` es un resto.** *
> *** b) o `ORDEN` no es la tarea de las 06:00 ***  -> *y **es otra lista** -- *y entonces *
>    *mi conclusion de B02 **estaba mal encuadrada.** *
> ```
>
> *** Y **hay una pista, y no es concluyente**: *** *`run.py:44-48` **ya documenta un defecto de Lidl en el
> bucle** («su `main` exige `--html` o `--web`, y aqui se llamaba `main()` a secas»), *y **eso solo tiene
> sentido si Lidl ESTA en el bucle.** *
>
> *** -> **pero «tiene sentido» no es «esta medido»**, *y **por eso se deja abierto.** *

## 3. *** Y de aqui sale la respuesta completa al propietario ***

> *** El propietario pidio: *** *** «que dependa de la region que elija el usuario... *** *** verifica si esto
> le pasa a mas supermercados o solo a lidl *** ***». *
>
> *** Y **ahora se puede responder entero**: *
> ```
> *** 1) ES SOLO LIDL ***  *-- *cinco cadenas tienen `region = None` (catalogo nacional), *
>    *y **el unico valor del fichero es `'28'`, con 77 filas, y es de Lidl.** *
> *** 2) Y LA RAZON ESTA ESCRITA EN SU COLECTOR ***  ***  -> *** *** «su pagina publica de ofertas semanales
>    publica un numero acotado de fichas *** CON PRECIOS POR REGION ***» *** *
> *** 3) Y EL MECANISMO TIENE NOMBRE ***  -> *** `regionsV2[region].regionPriceId` ***, *y *
>    *** «se resuelve ANTES de mirar el precio» *** *
> *** 4) Y «28» es el `regionPriceId` que se capturo ***  *-- *y **su nombre no se ha buscado**, *y **no se
>    inventa.** *
> ```
>
> *** O sea: *** *** **la respuesta al propietario no es «Lidl es raro»: es que Lidl publica POR REGION y las
> otras cinco no**, *y **su propio codigo lo dice, con el mecanismo y la URL.** *
