---
seccion: Medidas y agregados
resumen: Qué se anuncia, qué sostiene el histórico y por qué la mayoría no se puede juzgar.
en_una_frase: Casi todas las promociones de este catálogo no se pueden juzgar con los datos que hay, y decirlo es la conclusión, no una excusa.
---

# 08 · Promociones: lo que se anuncia y lo que el histórico sostiene

«Oferta» es la palabra que más se usa en un supermercado y la que menos se comprueba. Este
capítulo es el de la verificación: cómo se decide si un descuento existe, por qué la mayoría de
las promociones anunciadas **no se pueden juzgar** con un solo precio, y qué dice la norma.

## 1. El problema, en dos frases

Un cartel dice «−50 %». Para comprobarlo hacen falta dos cosas: **el precio de referencia** (lo
que ese producto cuesta normalmente) y **la unidad correcta** (el −50 % de qué). Si falta
cualquiera de las dos, la respuesta honesta no es «la oferta es falsa»: es **«no se puede
juzgar»**. Y eso es lo que este proyecto descubrió a base de mirar su propia lista.

## 2. Qué se anuncia, contado

Catálogo de hoy (`data/gold/grupos.parquet`):

    productos                          57.603
    con texto de promocion              7.848
    con la marca de "en promo"          7.929   (una cadena publica el si/no pero no el texto)
    solo con tarjeta                      576   (el descuento no existe sin la tarjeta)
    solo online                           341   (no existe si vas a la tienda)

Dos lecciones de ingeniería en esas cuatro filas:

1. **Publicar el booleano no es publicar la promoción.** Que una cadena diga «está en promo»
   sirve para marcarlo, no para verificarlo: sin el texto no se sabe qué promete.
2. **No todo lo que se anuncia lo paga cualquiera.** Un descuento que solo existe con la tarjeta
   o solo comprando online **no está disponible para todos**, y por eso el proyecto lo marca y
   (en el índice y en la cesta) lo trata aparte. Es la regla que la metodología oficial aplica a
   los datos de escáner: entra el precio rebajado si cualquier comprador lo tiene.

## 3. El precio de referencia: el «precio de siempre»

Para juzgar una oferta hace falta una referencia propia, y aquí se construye con una **mediana
móvil de 30 observaciones** por producto (`core/derive.py`): el precio que ese producto ha
tenido habitualmente, resistente al rebote de una promoción puntual. Con eso:

    de las 6.881 promociones anunciadas que tienen base calculable:
        bajan de verdad                        1.393   (20 %)
        no bajan                               5.488   (80 %)

Ese 80 % es el número que llama la atención, y **la trampa está en leerlo como «el 80 % de las
ofertas son falsas»**. No lo es, y el apartado siguiente explica por qué: la mayoría de esas
5.488 no se pueden juzgar con el precio de una unidad, así que ni son falsas ni son verdaderas.

## 4. La clasificación que cambia todo: qué mecánica tiene la oferta

El texto de promoción dice **cómo funciona** el descuento, y no todas las mecánicas se pueden
comprobar mirando el precio de una unidad. Medido hoy (el clasificador y los recuentos salen de
`plataforma/api/movimientos.py`, y se pueden pedir con
`uv run python -c "from plataforma.api import movimientos; print(movimientos.ofertas_sin_poder_juzgar())"`):

    de las 5.488 que anuncian oferta y no bajan:
        dependen de cuantas unidades compres    3.658     "3x2", "2ª unidad -50 %", "Todo a 1 EUR"
        no anuncian un descuento de precio        288     "En pack, mas facil", "Stock Fuera"
        la cantidad declarada cambio                4     el mismo envase leido de dos maneras
        ---------------------------------------------------------------------------------
        se juzgan (descuento sobre esta unidad) 1.538

**Un 3x2 no baja el precio de una unidad: baja el de la tercera.** Acusar a esas 3.658 de
«oferta falsa» sería un error del analista, no una mentira de la cadena. Y las 288 que no
anuncian un descuento de precio —«Stock Fuera (Unidades Limitadas)», «Novedad Alcampo»— no son
ofertas: son etiquetas de marketing en el mismo campo.

Quedan **1.538 ofertas que sí son un descuento sobre el precio de esta unidad y no bajan**: ésas
son las que conviene mirar dos veces, y son las que la pantalla enseña, diciendo además cuántas
se han quedado fuera y por qué.

## 5. La norma, como vara externa

No hace falta inventar el criterio: la **Directiva (UE) 2019/2161** modificó la Directiva 98/6/CE
para exigir que el «precio anterior» anunciado sea **el más bajo aplicado en los 30 días
previos**, precisamente para atacar la subida de precio antes de la rebaja.
([Orientaciones de la Comisión, C(2021) 1229](https://eur-lex.europa.eu/legal-content/ES/TXT/PDF/?uri=CELEX:52021XC1229(06)&from=ES) ·
[Informe COM(2024) 258](https://eur-lex.europa.eu/legal-content/ES/TXT/DOC/?uri=CELEX:52024DC0258))

Y aquí está la parte incómoda, medida:

    maximo de dias de historico por producto      19
    productos con 30 dias o mas                    0

Es decir: **la ventana legal no cabe en nuestro histórico**, así que hoy se pueden marcar
**indicios**, no incumplimientos. Decirlo es obligatorio; lo contrario sería exactamente el tipo
de titular que este material enseña a no firmar. (Hay estudios de consumidores que encuentran
tasas muy altas de «precios tachados» engañosos en comercio electrónico —[UFC-Que Choisir:
casi 9 de cada 10](https://www.quechoisir.org/action-ufc-que-choisir-prix-barres-sur-les-sites-d-e-commerce-pres-de-9-sur-10-sont-de-fausses-promotions-n168388/)—,
y se citan como contexto, no como prueba de nada sobre este catálogo.)

## 6. El detector propio, y por qué está dormido

El proyecto tiene su propia regla para el caso feo: *el precio de referencia subió justo antes de
la oferta*. Se calcula comparando el precio base de hoy con el de hace 45 días y exigiendo un
8 % de subida (`core/derive.py`, `oferta_sospechosa`). Medido hoy:

    872.650 filas de la serie, 0 marcadas

No está roto: está **dormido**, porque la regla necesita 45 días de serie y hay 19. Un campo que
devuelve siempre `False` durante seis semanas es una trampa para el analista que llega nuevo
—parece que «no hay ningún caso»— y por eso está escrito en el código y en la documentación.

## 7. Cómo se comprueba una promoción, en orden

La receta que sale de todo lo anterior, y que sirve para cualquier proyecto de precios:

1. **Separa la mecánica**: ¿es un descuento sobre el precio de esta unidad, o depende de cuántas
   compres? Sin esto, el análisis mide otra cosa.
2. **Comprueba la unidad y la cantidad**: un cambio de formato es un movimiento falso (capítulo
   06: 1.943 de 18.185 movimientos lo eran).
3. **Compara con una referencia robusta** (mediana móvil, no media) y **solo si hay bastante
   serie**: con siete puntos no hay referencia.
4. **Respeta la disponibilidad**: tarjeta y solo-online no son ofertas para todos.
5. **Declara lo que no se puede juzgar**, con su motivo y su cuenta. Es la diferencia entre un
   verificador y un generador de titulares.
6. **Mide el detector contra la norma** cuando la ventana lo permita, y di cuándo no lo permite.

## 8. Lo que se aprende en este capítulo

- **El 80 % que no baja no es el 80 % de ofertas falsas**: la mayor parte no se puede juzgar con
  el precio de una unidad, y confundirlo es el error clásico de este análisis.
- Un buen indicador no es el que más casos marca, sino el que **sabe lo que no puede juzgar** y lo
  dice con su motivo.
- La norma da una vara externa (precio anterior = mínimo de 30 días): compararse con ella es más
  honesto que inventar un umbral propio.
- Un campo dormido (`oferta_sospechosa` = 0 durante seis semanas) es un riesgo de interpretación:
  hay que documentarlo como lo que es.
