# Lidl: reconocimiento histórico y actualización

## Actualización verificada el 6 de octubre de 2026

La conclusión de septiembre que sigue abajo **no debe usarse para descartar Lidl**.
La página pública de ofertas semanales entrega JSON en `data-grid-data`: se han extraído
76 fichas/variantes (70 productos padre), con precios regionales y condiciones de club.
Existe un piloto probado, `projects/cesta/sondear_lidl.py`, aún sin integración en la ingesta.
Ver [resultado, límites y trabajo de integración](CESTA-AMPLIACION-2026-10-06.md).

## Reconocimiento del 7 de septiembre de 2026 (conservado como histórico)

Resumen en una linea: **lidl.es no publica precios de alimentacion**, asi que un
scraper de su web no serviria para lo que queremos.

## Lo que se comprobo

Comparando dos fichas reales del mismo sitio:

    /p/parkside-herramienta-multifuncional-310-w/p100397479   bazar    21,99 EUR en el HTML
    /p/milbona-yogur-natural/p11008612                        comida   NINGUN precio

Las fichas de alimentacion existen pero llevan **una fecha donde deberia ir el
precio**, y ademas son efimeras: varias que aparecian indexadas devuelven 404 el
mismo dia. Se publican y se retiran con la semana del folleto.

La categoria `/c/alimentacion/s10068374` responde literalmente que no hay ofertas
que mostrar.

Los precios de comida de Lidl solo estan en dos sitios: el **folleto semanal**
(un visor JavaScript, marcado `noindex`) y la **app Lidl Plus**.

## robots.txt (verificado, literal)

    User-agent: *
    Disallow: /user-api/*
    Disallow: *search?q=*
    Disallow: *?offset=*
    Disallow: *idsOnly=*
    Disallow: *productsOnly=*
    Disallow: *id=*
    Disallow: *sort=*
    Sitemap: https://www.lidl.es/static/sitemap.xml

No hay `Crawl-delay`. El `Disallow: *id=*` es lo bastante amplio como para cubrir
casi cualquier peticion util de listado, y ademas delata donde esta la API de
listados que no vamos a usar.

## La unica via real: la API movil de Lidl Plus

El proyecto `EvickaStudio/lidl-discounts` (mayo 2026) usa endpoints publicos que
**no piden login**, con cabeceras de la app Android:

    GET https://stores.lidlplus.com/api/v4/ES                    tiendas
    GET https://offers.lidlplus.com/app/api/v4/ES/<tienda>/offers ofertas

Devuelve nombre, marca, precio, precio anterior, descuento, precio por unidad y
fechas de validez. Es decir, encaja con nuestro esquema.

**Sin verificar por nosotros**: no se ha ejecutado ninguna llamada real a ES, no
se sabe si el payload trae EAN, y el endpoint se llama `offers` — lo mas probable
es que devuelva solo las promociones de la semana, no el surtido permanente con
su precio base.

## Decision

Lidl queda para despues, y cuando se haga sera un cliente de esa API movil, no un
scraper de la web. Antes de escribir codigo hay que hacer una sola llamada real y
mirar que trae: si son solo ofertas semanales, la cobertura sera parcial y sesgada
hacia lo que esta en promocion, muy distinto de los miles de referencias con precio
que dan las otras cinco. Eso hay que saberlo antes de invertir, no despues.
