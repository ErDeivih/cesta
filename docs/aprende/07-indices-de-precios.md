---
seccion: Medidas y agregados
resumen: Jevons encadenado, las formulas oficiales y el sesgo de encadenamiento medido.
---

# 07 · Índices de precios: medir el nivel, no el caso

Un producto que sube 20 céntimos no dice nada del nivel de precios de un supermercado. Este
capítulo es el de la medida agregada: **cómo se construye un índice con datos de escáner**, qué
dicen las fuentes oficiales, y qué se ha medido aquí (incluido un sesgo conocido, comprobado y
**descartado con números**).

## 1. Las fórmulas, y por qué la elección no es un detalle

Tres familias, y la diferencia entre ellas no es estética:

**Índices elementales** (muchos productos, sin cantidades): comparan precios del mismo producto
entre dos momentos.

    Carli    media ARITMETICA de los relativos        (p_t/p_0)
    Dutot    cociente de las MEDIAS de precios
    Jevons   media GEOMETRICA de los relativos        exp(avg(ln(p_t/p_0)))

El manual del IPC (OIT, FMI, OCDE, CEPE y Banco Mundial) recomienda **Jevons** con datos de
escáner, por dos motivos técnicos: Carli tiene **sesgo al alza** (la media aritmética de
relativos sube aunque los precios no cambien, por un efecto de composición) y Dutot depende de
la dispersión de los precios. La media geométrica es la que se comporta.

**Índices agregados** (con cantidades o cuotas de gasto): Laspeyres (cesta base), Paasche
(cesta corriente), Fisher y Törnqvist (superlativos, media de los dos). Necesitan **cantidades**,
y aquí no hay ventas: no se pueden calcular. Lo que sí se puede deducir es la cantidad que
implica cada precio (`precio_cent / precio_unidad_cent`), y con eso cabría un Törnqvist
aproximado: es una de las mejoras listadas en el anexo 91.

## 2. Lo que hace este proyecto, y por qué está bien elegido

```
índice por cadena = 100 × Π_eslabones exp( avg( ln( precio_t / precio_{t-1} ) ) )
```

Es decir: un **Jevons encadenado** sobre el precio de venta del **mismo producto** en capturas
consecutivas de la misma cadena. Tres decisiones que lo hacen honesto:

1. **Cada eslabón compara el mismo producto consigo mismo.** Así el índice no se mueve porque
   cambie el surtido (que es el error clásico de una cesta fija mal hecha).
2. **Recorta los relativos fuera del rango `1/3`–`3`** y **dice cuántos** (columna
   «Recortados»): medido hoy, 1.679 de 797.390 eslabones, un **0,21 %**.
3. **Declara el método, la base y las capturas.** Cada serie lleva `metodo`, `base`, `capturas`
   y el número de productos de su último eslabón.

Resultado de hoy (`GET /api/indice`, o la pestaña **Índice** del panel):

    cadena       índice    variación   capturas   productos (último eslabón)
    alcampo       98,59     −1,41 %        16              22.987
    aldi         100,08     +0,08 %        18               1.909
    carrefour     99,95     −0,05 %        13              16.229
    dia           99,95     −0,05 %        17               5.772
    mercadona    100,04     +0,04 %        18               4.288

Leído bien, esto dice que en ~2,5 semanas el nivel de precios de las cinco cadenas se ha movido
menos de un 1,5 %, y que **el tamaño de la muestra con la que se dice varía mucho** (22.987
productos frente a 1.909): dos eslabones con muestras así no son comparables en precisión. Esto
último es una de las tres cauciones pendientes (§5).

## 3. El sesgo de encadenamiento: el miedo clásico, medido y descartado

Encadenar eslabones tiene un riesgo conocido: si un precio rebota (100 → 50 → 100 por una
promoción), un índice encadenado puede acabar **por debajo** de 100 — imposible comparando el
mismo producto consigo mismo. Es el *chain drift*, y la respuesta oficial moderna son los
índices **multilaterales** (GEKS-Törnqvist con ventana rodante).
([Chain drift, Ivancic/Diewert/Fox](https://users.nber.org/~confer/2009/SI2009/PRB/Ivancic_Diewert_Fox.pdf) ·
[Métodos multilaterales en el IPCA (Eurostat/CEPE 2024)](https://unece.org/sites/default/files/2024-09/Multilateral%20Methods%20in%20the%20HICP_final.pdf))

Aquí se ha comprobado **con la ventana que tenemos**, y la forma de comprobarlo es una cesta
fija: los productos presentes en la primera **y** en la última captura, comparados directamente,
con el mismo recorte y el mismo SQL que usa la aplicación (`analisis._enlaces_sql`):

    cadena       pares fijos   encadenado   directo   diferencia
    alcampo           43.233        98,59     98,97     −0,38 pp
    aldi               2.367       100,08    100,06     +0,01 pp
    carrefour         16.925        99,95     99,96     −0,00 pp
    dia                6.044        99,95     99,96     −0,01 pp
    mercadona          4.409       100,04    100,06     −0,02 pp

Las dos maneras de mirar el mismo dato coinciden **dentro de 0,4 puntos** (y en cuatro cadenas
dentro de 0,02). Conclusión: sobre una ventana de 19 capturas **el sesgo no es un problema
aquí**, y ahora se sabe cuánto vale. La literatura avisa de que el sesgo **crece con la longitud
de la cadena y con la frecuencia de promociones**, así que esto es una medida de hoy, no un
cheque en blanco: cuando la serie llegue a seis meses, se vuelve a medir con el mismo método.

**Y el primer intento de medirlo salió mal, lo que enseña más que el resultado.** Mi primera
versión comparaba el encadenado con un «directo» calculado **sin recorte** y con mi propio SQL,
y daba una diferencia de +8,2 puntos en Alcampo (43.775 pares con 1.491 relativos fuera de
rango, un 3,4 %). La conclusión parecía «hay un sesgo enorme». Era falso: estaba comparando dos
cosas que no eran la misma (distinto filtro, distinto recorte, distinta definición de par). Al
repetirlo con el SQL de la aplicación y el mismo recorte, el sesgo desapareció. **Dos
instrumentos distintos dando 8,2 y 0,38 no se resuelven eligiendo el que más gusta: se resuelven
haciendo que los dos midan lo mismo.**

## 4. Cuando no hay que fiarse del número

Tres cosas que un índice de este tipo **no** dice y conviene tener escritas:

- **No es inflación.** Un índice de 19 días de cinco cadenas no mide la inflación de un país: no
  hay ponderaciones por gasto (ni, por tanto, cesta representativa) y la ventana es demasiado
  corta para hablar de tendencia. Lo que mide es «a qué ritmo se mueve el nivel de precios de
  esta cadena en este periodo», que es lo que dice la pantalla.
- **No dice dónde comprar.** Para eso están la comparación por grupos y las equivalencias: el
  índice mide el nivel general, no el precio de lo que vas a comprar.
- **No es comparable entre cadenas si la muestra es muy distinta.** 22.987 productos frente a
  1.909 no dan la misma precisión, y decir «Alcampo ha bajado un 1,4 %» sin decir sobre cuántos
  productos es el mismo error que dar un porcentaje sin su base.

## 5. Las tres mejoras pendientes, con su fuente

Del anexo 91, y son las que un revisor técnico esperaría ver:

1. **Publicar el intervalo.** El índice ya es `exp(avg(ln rel))`, así que su error estándar sale
   casi gratis: `exp(avg ± 1,96 · sd/√n)`. Sin intervalo, un −1,41 % no se distingue de ruido.
2. **Declarar la cobertura del eslabón** (productos comparados frente al catálogo de esa cadena
   ese día) como métrica de calidad del número. La guía práctica de Eurostat sobre datos de
   supermercado es explícita con el tratamiento de productos que entran y salen.
   ([Practical Guide to Supermarket Scanner Data](https://circabc.europa.eu/sd/a/8e1333df-ca16-40fc-bc6a-1ce1be37247c/Practical-Guide-Supermarket))
3. **Mirar la ventana**: son 30 *observaciones*, no 30 días, y con `min_samples=7`. Con huecos en
   la serie, 30 observaciones pueden ser 45 días, y siete puntos son pocos para una mediana
   robusta. El manual del IPC recomienda validar con el algoritmo de Tukey cuando hay muchos
   ceros de variación (precios quietos), que es el caso.

## 6. Para qué sirve esto fuera de aquí

Con un índice por cadena, un «precio de siempre» por producto y su posición en 90 días se pueden
construir las tres cosas que la gente pide de verdad: **cuánto ha subido lo que yo compro**
(índice personal con la lista del usuario), **qué cadena sube más y en qué categoría**, y
**si una oferta anunciada se sostiene**. Las tres están en la tabla del capítulo 09, con sus
límites: sin cantidades no hay ponderación por gasto, y sin ventas no hay cuota ni elasticidad.

## 7. Lo que se aprende en este capítulo

- La fórmula no es un detalle: **Jevons** (media geométrica) es la recomendada con datos de
  escáner, y Carli tiene sesgo al alza.
- Encadenar tiene un riesgo conocido y **medible**: aquí vale 0,38 puntos como mucho, y esa
  cifra es una medida con fecha, no una propiedad permanente.
- Un índice honesto **declara su método, su base, su muestra y sus recortes**. Un porcentaje sin
  base es una opinión con decimales.
- Dos instrumentos que dan números distintos no se resuelven eligiendo: se resuelven haciendo que
  midan lo mismo.
