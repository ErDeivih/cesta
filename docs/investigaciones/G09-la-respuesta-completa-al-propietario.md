# G09 · **LA RESPUESTA COMPLETA AL PROPIETARIO**: la region ya sale de `config.CODIGO_POSTAL`, y **si no casa, no se publica**

*(2026-10-14, ~02:30. **Y la funcion que el propietario pidio ya esta escrita, y con su regla.**)*

## 1. La pregunta, y donde estaba la respuesta

> *** El propietario dijo: *** *** «que dependa de *** LA REGION *** que elija el usuario, o en la UE se
> encuentre en ese momento. *** Verifica si esto le pasa a mas supermercados o solo a lidl *** para mejorar la
> experiencia del usuario» *
>
> *** Y **la respuesta estaba EN EL PROPIO COLECTOR**, *en `projects/cesta/collectors/lidl.py:59-69`: *
> ```python
> l58  FUENTE = "lidl"
> l59-61 # *** «**Y la region sale de la zona del usuario, que YA existe en `config`.** *** *`REGION_POR_DEFECTO`
>        # era «28», y su propio comentario decia lo que era: *** «la unica observada; *** NO ES LA ZONA DEL
>        # HOGAR DE NADIE ***»*. *** Elegirla habria publicado precios de una zona que no es la de quien los
>        # lee.** ***» *
> l63-64 # *** «*Y `config.CODIGO_POSTAL` («tu zona», en sus palabras) *** YA FIJA EL ALMACEN DE MERCADONA Y
>        # EL AMBITO DE ALDI. *** *** Asi que la zona es UNA, y es la del usuario. ***» *
> l66-68 # *** «*Pero *** un CP NO es un id de `regionsV2` ***, y *** el plan prohibe suponerlo. *** *** Asi que
>        # se acredita por el nombre que la propia fuente publica *** (`region_del_cp`), *y *** si no casa, no
>        # hay region y no se publica *** -- *no se elige «la mas parecida».» *
> l69  COBERTURA = "ofertas_semanales_parcial"
> ```

## 2. *** Y contesta las cuatro cosas, y la cuarta es la que importa ***

```
*** 1) QUE ES `'28'` ***  -> *** el `REGION_POR_DEFECTO` que quedo observado ***, *y **su propio comentario
   dice lo que es**: *** «la unica observada; *** *** NO ES LA ZONA DEL HOGAR DE NADIE *** ***» *** *
*** 2) Y POR QUE NO SE USA POR DEFECTO ***  -> *** «eligirla habria publicado precios de una zona que no es
   la de quien los lee» *** ***  <- *** y es la doctrina entera, en una frase. *** *
*** 3) Y DE DONDE SALE LA REGION, ENTONCES ***  -> *** de `config.CODIGO_POSTAL` ***, *que es **«tu zona»**,
   *y que **YA FIJA el almacen de Mercadona y el ambito de Aldi** *-- *
   *** -> o sea: **la zona es UNA, y es la del usuario**, *y **no hay que elegirla en una pantalla.** *
*** 4) Y QUE PASA SI NO CASA ***  -> *** `region_del_cp`: se acredita POR EL NOMBRE QUE LA PROPIA FUENTE
   PUBLICA ***, *y *** «si no casa, NO HAY REGION Y NO SE PUBLICA» *** -- *
   *** y NO SE ELIGE «LA MAS PARECIDA». *** *
```

> *** O sea: *** *** **la funcion que el propietario pidio **ya esta escrita**, *y con la regla que el
> encargo exige**: *
> ```
> *** la region depende del USUARIO ***  *-- *via `config.CODIGO_POSTAL`*
> *** y si la de Lidl no casa, NO SE PUBLICA ***  *-- *en vez de enseñar la de otro*
> *** y el valor observado (`'28'`) NO se usa por defecto ***  *-- *y **el motivo esta escrito**:
>    *«no es la zona del hogar de nadie»*
> ```

## 3. *** Y eso hace que mi respuesta anterior fuera INCOMPLETA, y se dice ***

```
*** LO QUE YO ESCRIBI EN LA RONDA 313: ***
  *«la region es un parametro de la CAPTURA, no de la interfaz... y si la region del usuario no es la
  capturada, lo que hay que decir es que no se sabe»*

*** Y EL CODIGO YA HACIA ESO, Y MAS: ***
  *** 1) la region NO es un parametro de la captura suelto: *** *sale de **`config.CODIGO_POSTAL`**, *
     *que ya existe y **ya sirve para Mercadona y Aldi.** *
  *** 2) y si no casa, *** *** NO SE PUBLICA *** *-- *que es **mas estricto** que «decir que no se sabe»: *
     *la linea **no sale.** *
  *** 3) y hay un `--region=<id>` *** *para cuando **se sabe cual es**, *y **el plan prohibe suponerlo.** *
```

> *** O sea: *** *** **mi conclusion era correcta en la forma y estaba ya implementada**, *y **lo que aporta
> esta ronda es encontrarla** -- *y **decir que la mia era incompleta.** *

## 4. Y el estado de G09, con **la pregunta del propietario contestada por partida doble**

```
*** G09 · el ambito regional de Lidl ***
  *** es solo Lidl ***       -> *cinco cadenas con `region = None`, *y **el unico valor del fichero es `'28'`** *
  *** y por que ***           -> *** «su pagina publica de ofertas semanales publica un numero acotado de
                                fichas *** CON PRECIOS POR REGION ***» *** *
  *** y el mecanismo ***      -> *** `regionsV2[region].regionPriceId` ***, *y *** «se resuelve ANTES de mirar
                                el precio» *** *
  *** y de donde sale ***     -> *** `config.CODIGO_POSTAL` *** *-- *y **si no casa, no se publica** *
  *** y que es `'28'` ***     -> *** el valor observado, y NO la zona de nadie *** *-- *y **por eso no se usa** *
  *** -> o sea: *** *** LA PREGUNTA ESTA CONTESTADA, Y LA FUNCION TAMBIEN. *** *
```
