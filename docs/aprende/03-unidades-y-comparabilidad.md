---
seccion: Fundamentos
resumen: Por qué un catálogo es una tabla de envases, y el pack medido y no usado como cuchillo.
en_una_frase: Un catálogo de supermercado es una tabla de envases: sin normalizar la unidad, comparar precios da ahorros de miles de euros en un azafrán.
---

# 03 · Unidades, comparabilidad y el precio por unidad

Un catálogo de supermercado no es una tabla de precios: es una tabla de **precios de envases**.
Comparar 1,09 € de una botella de leche con 0,89 € de un brik de 200 ml no da una diferencia,
da un disparate. Este capítulo es el de la normalización, y es el que más veces salva al
proyecto de decir una tontería.

Las fórmulas --la regla de tres del precio por unidad, las conversiones de unidad canónica, el
peso con el que se elige la unidad que manda en un grupo y el factor 30 que prohibe comparar--
están en el **anexo 93**, apartados 6 y 9.

## 1. El problema, con el caso que lo enseñó

En la ficha de un azafrán de 0,4 g, la aplicación llegó a decir **«te ahorras 6.872 €/kg»**. Los
números eran correctos y la frase era absurda: estaba comparando el precio por kilo de un
azafrán con el de otra presentación. Es el ejemplo que se usa en todo el proyecto para explicar
por qué existe `unidad_canon`.

Lo que hace falta, entonces, no es «el precio»: es **el precio por unidad de medida**:

    €/kg      para lo que se vende al peso (carne, fruta, embutido)
    €/l       para lo que se vende por volumen (leche, aceite, agua)
    €/ud      para lo que se vende por piezas (papel de cocina, cápsulas)
    €/m       para lo que se vende por longitud (papel de aluminio)

Y tres reglas que se derivan de eso:

1. **Solo se comparan precios en la misma unidad.** `unidad_canon` es la que se usa para
   comparar; `ud` no entra en las comparaciones fiables (`core/matching.py`, `UNIDADES_FIABLES`
   = kg, l, m), porque «1 ud» puede ser una barra de pan o un envase de 30 pañales.
2. **La cantidad tiene que ser la cantidad.** Si la cadena no publica el tamaño, el precio por
   unidad no se puede calcular... salvo que se deduzca del propio precio: `cantidad ≈
   precio_cent / precio_unidad_cent`. Ese truco es el que se usa para saber si dos días del
   mismo producto son comparables (capítulo 06).
3. **Un tamaño mal leído contamina todo lo que se calcule sobre él.** El caso documentado:
   un aceite de 400 g leído como 400 mg.

## 2. Los tres datos que hacen falta, y cuántos hay

Medido hoy sobre el catálogo (`docs/CIFRAS.md` se reescribe cada día con estos números):

    productos del catalogo                     57.603
    comparables por kg/l/m                     45.891   (80 %)
    con codigo de barras                       25.413   (44 %)
    con tabla nutricional                       3.853

Ese 80 % es la parte del catálogo sobre la que se puede decir algo. El 20 % restante no se
descarta: se enseña su precio, se puede añadir a la lista, pero **no decide dónde sale más
barato algo**, que es la regla de la casa: un dato que no tenemos no se inventa.

## 3. Cuando la cadena y nosotros no coincidimos

Aquí está la parte interesante, y es una decisión de ingeniería que merece copiarse: hay fichas
en las que **el precio por unidad que calculamos y el que publica la propia cadena se
contradicen por un factor de dos o más**. ¿Quién tiene razón? No se sabe, y por eso **no se
elige ganador**:

    CORRIGE  -> si lo que explica la diferencia es un pack de N unidades, se corrige
    en_disputa -> si no, la fila se aparta de las comparaciones (72 de 52.002, 0,14 %)

Ni se borra ni se inventa: se aparta, se sigue enseñando su precio y se puede añadir a la
lista. Es exactamente el patrón de *cuarentena* que se pide en un proyecto de datos serio.

Y una medición que enseña a mirar los datos: de las 220 filas que caían en el caso «1 ud a
14,90 € con etiqueta de 4,97 €/ud», **148 eran tres recambios dentro del envase**. «El envase
trae tres» explicaba mejor el dato que «alguien se equivocó», y por eso la inferencia de
unidades va **antes** del control de calidad en el código, no después.

## 4. El pack: la medida que decidió no usarlo como cuchillo

Los packs son el caso más difícil, porque **no son un error**: un pack de 6 botellas de 1,5 l y
una botella suelta son el mismo producto en dos presentaciones, y el precio por litro de los
dos se puede comparar perfectamente.

La tentación es usar `unidades_pack` como guarda (si uno dice 6 y el otro 1, no son el mismo
producto). Se midió y **no se usa**, por dos razones que están escritas en el código:

    de 1.809 pares ciertos (mismo EAN en dos cadenas), 120 tienen una cadena diciendo
    pack = 1 y la otra diciendo 2, 3, 12 o 24  -> `1` NO es una declaración, es el silencio

Y porque los 12 grupos que una guarda estrecha separaría **no son un error**: son el mismo
producto en formato de 2 y de 4 (lonchas de embutido), o una errata de lectura (`85x4 g` leído
como 85 unidades). Separarlos quitaría comparaciones legítimas, que en esta aplicación es el
error caro.

Así que el pack **se usa para decirlo**, no para cortar: «donde compro agua» no puede
recomendar 9 litros sin decir que son un pack.

Y hay una consecuencia medida sobre el catálogo de hoy (`uv run python -m projects.cesta.ejes`):

    grupos que mezclan un pack con sueltas        661
    de esos, de 11 o mas productos                  0

Que 661 grupos mezclen presentaciones no es una contradicción de nadie (todas las unidades son
el mismo producto), y el segundo número es el que importa: **ningún grupo grande lo hace**, que
era el problema original.

## 5. Hasta dónde llega el desastre si no se normaliza

La forma más rápida de ver por qué esto importa no es un argumento, es una consulta. Los pares
ciertos por código de barras que **no caen en el mismo bloque de formato** —el bloque es
`(unidad, cantidad)`— son, medidos hoy (`uv run python -m projects.cesta.bloqueo`):

    pares ciertos (mismo EAN, dos cadenas)      1.795
    el bloqueo los puede ver                    1.359   (75,7 %)
    el bloqueo los pierde                         436
        no se le pudo leer el formato             336
        misma unidad y cantidad distinta           61   (un pack frente a la suelta)
        una cadena por unidad y la otra al peso    39

Ejemplos reales de los dos últimos, que se entienden sin explicación:

    Bombon mini helado Magnum (carrefour)  <->  Magnum mini almendrado 6 x 44 g (dia)
    Pepsi zero azucar pack 2 botellas 1,75 cl. (carrefour)  <->  Pepsi 2 x 1,75 L (dia)

El segundo es una mina: el mismo producto con el tamaño escrito en **cl** donde debería estar en
**l**. Si un emparejador se fía del texto, ahí se equivoca; si se fía del campo normalizado,
acierta. Es la lección de todo el capítulo en una línea.

## 6. Lo que se aprende en este capítulo

- Un catálogo es una tabla de **envases**, no de precios. Sin normalizar la unidad no hay
  comparación posible, solo apariencia de comparación.
- Cuando dos fuentes se contradicen, la respuesta profesional no es elegir una: es **apartar la
  fila** y decirlo.
- Un campo ausente disfrazado de valor (`pack = 1` cuando en realidad no se sabe) es peor que un
  nulo, porque se puede usar por error. El silencio tiene que ser distinguible.
- La medida de «cuántos pares ciertos pierde el bloqueo» no es un detalle del emparejador: es
  la que dice si el techo de todo lo demás está donde crees (capítulo 05).
