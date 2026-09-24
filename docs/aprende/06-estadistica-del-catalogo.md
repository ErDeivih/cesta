---
seccion: Medidas y agregados
resumen: Medianas frente a medias, percentiles, tamano de muestra y recortes contados.
---

# 06 · Estadística de un catálogo sucio

Este capítulo es el de la estadística que de verdad se usa en un proyecto de datos: **describir
bien una distribución, elegir el estadístico correcto y saber cuándo un número no significa
nada por falta de muestra**. Todo con los números de hoy y la consulta que los saca.

## 1. La forma de la distribución, y por qué la media no sirve

Precio por unidad de los 45.884 productos comparables del catálogo, en céntimos
(`data/gold/grupos.parquet`, `comparacion_fiable`):

    n        45.884
    p1           62,9    (0,63 EUR/kg o /l o /ud)
    p25         488,0
    mediana   1.029,9    <- "lo normal"
    p75       1.986,7
    p99      24.911,3    (249 EUR por unidad)
    maximo 1.419.000,0   (14.190 EUR por unidad)
    media     2.379,4    =  2,31 x la mediana

Esa última línea es el capítulo entero. La media está **dos veces y media por encima de la
mediana** porque la cola es larguísima: hay azafrán, hay trufa, hay productos a granel con
precios por unidad absurdos. En una distribución así:

- **la media no es un resumen, es un artefacto**: la mueve el extremo;
- **la mediana tiene un punto de ruptura del 50 %**: para desplazarla haría falta que la mitad
  del catálogo se moviera;
- **los percentiles cuentan la forma**: p1 y p99 dicen lo ancha que es la distribución, y son la
  base de las vallas de Tukey (p25 − 1,5·IQR, p75 + 1,5·IQR) que se usan para detectar outliers.

Por eso todo lo que decide en este proyecto es una **mediana**: el «precio de siempre»
(`core/derive.py`, mediana móvil), el desvío de una cadena frente a las otras
(`plataforma/api/analisis.py`, mediana del desvío) y la mediana de movimiento por cadena. La
media solo aparece cuando la distribución es razonable, y se dice.

## 2. La muestra, que es lo que casi nadie mira

Distribución de tamaños de grupo (`grupo_id`, todos los grupos del catálogo):

    de 1 producto       35.208     79,2 %
    de 2 productos       6.218
    de 3 a 5             3.003
    de 6 a 10                5
    de mas de 10             0
    ---------------------------
    grupos              44.434

Dos lecturas, y las dos importan:

1. **El 79 % de los grupos no sirve para comparar nada**: un producto en una sola cadena no
   tiene con quién. Eso no es un fallo del catálogo, es el catálogo (surtidos distintos). Cualquier
   media «por grupo» que se calcule sobre los 44.434 mezcla grupos de uno con grupos de cinco: hay
   que filtrar por `count(DISTINCT fuente) >= 2`, y decirlo.
2. **Los grupos grandes ya no existen** (0 de más de 10). Ese era el problema original —84
   cervezas mezclando sin gluten con sin alcohol— y hoy es cero, con trinquete en
   `tests/test_atributos.py`.

Es el sesgo de selección de manual: se analiza la parte del catálogo que se puede comparar, y esa
parte **no es una muestra aleatoria** (son productos de marca y de surtido común). Un resultado
sobre «lo emparejado» no se puede extrapolar a «el supermercado».

## 3. Cuánto se separan las cadenas, y cuándo eso es sospechoso

Dentro de cada grupo comparable, la diferencia entre el más caro y el más barato (8.333 grupos):

    mediana de la diferencia          15,9 %
    percentil 90                     111,8 %
    grupos donde el caro > 3x barato    254   (3,0 %)

La mediana del 16 % es el dato útil (lo mismo cuesta, más o menos, un 16 % más en unas cadenas
que en otras). El p90 del 112 % es el aviso: **en uno de cada diez grupos el más caro cuesta más
del doble**, y ahí no hay una oferta, hay algo mal o algo distinto. Y los 254 grupos donde la
diferencia pasa del triple son la lista de trabajo: casi siempre son **unidades distintas o un
emparejamiento flojo**, no un chollo (28× de marca blanca frente a marca sí es real, y también
existe: la frontera está en 30×, `core/comparacion.py`).

## 4. Los recortes, contados

El índice de precios compara cada producto consigo mismo en capturas consecutivas y **recorta**
los relativos fuera del rango `1/3`–`3` (`plataforma/api/analisis.py`). Sobre 797.390 relativos:

    fuera del rango     1.679     0,21 %

Un 0,21 % es un recorte bien calibrado: si fuera el 10 %, estaría tapando un problema de datos
en vez de un caso raro; si fuera 0, no estaría protegiendo nada. **Y se cuenta y se enseña**
(la tabla del índice tiene su columna «Recortados»), porque un recorte silencioso es una
manipulación aunque sea técnica.

## 5. Cuánto se mueve un catálogo (y cuánto parece moverse)

Sobre los mismos 797.390 pares de capturas consecutivas, con umbral de movimiento del 0,5 %:

    se mueve el precio por unidad                 18.185     2,3 %
    ... pero el precio de venta no cambio          1.943     0,24 %

Esos 1.943 son **movimientos falsos**: el precio por unidad cambió porque cambió la lectura del
formato, no porque cambiara el precio de la etiqueta. Es exactamente el control que necesita
cualquier análisis de precios, y por eso el proyecto compara **mismo producto, misma unidad,
misma cantidad deducida y el precio de venta movido en el mismo sentido** antes de llamar
«bajada» a algo (capítulo 08).

## 6. Las cauciones que quedan pendientes, dichas

Un material honesto dice también lo que aún no hace. En esta parte del proyecto faltan tres
cosas, y están identificadas con su fuente (anexo 91):

1. **El índice no publica intervalo de error.** Es barato de añadir porque el índice ya es
   `exp(avg(ln(rel)))`: su intervalo aproximado es `exp(avg ± 1,96·sd/√n)`. Sin él, un −1,4 %
   no se distingue de un −1,4 % de ruido.
2. **La cobertura del eslabón no se declara.** El número de productos que sostiene cada punto
   del índice varía (22.987 en Alcampo, 1.909 en Aldi), y comparar dos eslabones con muestras
   muy distintas es comparar dos precisiones distintas.
3. **La ventana es de 30 observaciones, no de 30 días**, y con `min_samples=7`: siete puntos son
   pocos para una mediana robusta, y si hay días sin captura, 30 observaciones pueden ser 45
   días. Medirlo es contar la distribución de observaciones por ventana.

Lo dice la metodología oficial (manual del IPC de OIT/FMI/OCDE, que recomienda validar con el
algoritmo de Tukey cuando hay muchos ceros de variación) y lo dice la investigación del anexo 91:
son mejoras concretas, no opiniones.

## 7. Lo que se aprende en este capítulo

- Con colas largas, **la mediana es el resumen y la media es un artefacto**: aquí la media es
  2,31× la mediana.
- El **tamaño de muestra** hay que mirarlo antes que el resultado: el 79 % de los grupos no
  permite comparar nada.
- Un percentil alto (p90 de 112 %) no es un resultado, es **una lista de trabajo**.
- Los recortes y los umbrales se **cuentan y se enseñan**; un filtro silencioso es una mentira
  técnica.
- Comparar magnitudes exige comprobar que el cambio es del precio y no de la lectura: 1.943 de
  18.185 movimientos eran falsos.
