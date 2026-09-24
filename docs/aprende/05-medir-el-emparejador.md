# 05 · Medir si el emparejador funciona (y no engañarse al medirlo)

El capítulo anterior explicaba el método. Este explica lo que casi nadie hace bien: **comprobar
si funciona**. Y aquí es donde un proyecto de datos se separa de una demo, porque medir mal es
peor que no medir: da confianza.

## 1. La verdad de referencia, y por qué es barata

Para medir hace falta saber la respuesta correcta, y eso normalmente cuesta dinero (etiquetar a
mano). Este proyecto tiene la suerte de tenerla gratis: **el código de barras**.

    dos fichas de dos cadenas con el mismo EAN  =  el mismo producto, sin discusion

De ahí sale el **banco de pares ciertos**: 1.795 pares, medidos hoy con
`uv run python -m projects.cesta.bloqueo`. Y de ahí sale la métrica principal:

    recall (pair-wise) = pares ciertos que el emparejador encuentra / pares ciertos
                       = 1.161 / 1.799  =  65 %

(`uv run python -m projects.cesta.emparejar --medir`, 498 s; los dos números no coinciden
exactamente porque el banco de `--medir` y el de `bloqueo` se construyen en sitios distintos,
con criterios ligeramente distintos de qué es un par: **y eso hay que decirlo, no esconderlo**).

## 2. El primer número que hay que medir no es el recall: es su techo

El emparejador no compara todos los pares posibles (serían 1.600 millones): compara los que
caen en el mismo **bloque**, y el bloque es el formato `(unidad, cantidad)`. Consecuencia que
cambia por completo la lectura del 65 %:

> **un par que no cae en el mismo bloque no se puede encontrar nunca**, por muy bueno que sea
> el matcher.

Eso es la *pair completeness* del bloqueo, y es el techo del recall. Medido hoy
(`uv run python -m projects.cesta.bloqueo`):

    pares ciertos (mismo EAN, dos cadenas)      1.795
    el bloqueo los puede ver                    1.359   (75,7 %)   <- el TECHO
    el bloqueo los pierde                         436   (24,3 %)
        no se le pudo leer el formato             336
        misma unidad y cantidad distinta           61
        una cadena por unidad y la otra al peso    39

Con eso, el 65 % deja de ser un número suelto y pasa a ser **86 % de lo que el bloqueo deja
ver** (65 / 75,7). Es una lectura completamente distinta: el matcher no está mal; lo que tiene
delante está limitado, y **el margen de mejora está sobre todo en las 436 parejas perdidas**,
que es un problema de datos (tamaños ilegibles) y de presentación (pack frente a suelta), no de
modelo.

**Y esto ya se midió una vez, el 8 de septiembre de 2026**, con el mismo resultado cualitativo:
sobre 1.767 pares, 579 caían en bloques distintos. La respuesta entonces fue **una segunda
pasada sin bloque y con el listón más alto** (`UMBRAL_SIN_FORMATO = 0.82`: si no se puede
comprobar el tamaño, se exige que el nombre sea casi el mismo), que es la solución que
recomienda la literatura: el bloqueo decide el techo, y cuando el bloqueo no puede, se paga el
coste de comparar más caro.

## 3. Lo que la métrica principal NO ve

El recall *pair-wise* es cómodo y engañoso, y conviene saber exactamente por qué:

1. **No dice nada de los grupos.** Si A≈B y B≈C, el proyecto une los tres (componentes conexas),
   pero A≈C puede ser falso. Un recall alto puede convivir con grupos mal formados.
2. **Premia lo fácil.** El banco son pares con EAN, y el EAN lo publican sobre todo las marcas
   conocidas (Alcampo y Aldi no lo publican: la mitad del catálogo se mide peor). Por eso este
   proyecto da los números **separados por marca y por marca blanca**.
3. **Un solo falso positivo puede fusionar dos grupos enteros.** Por eso existe la segunda red
   del capítulo 04 (los ejes que el nombre declara) y las invariantes del apartado siguiente.

Las métricas que sí miran los grupos (B-cubed, pairwise de cluster, cluster F1) existen y **no
ordenan igual** a los sistemas que el pair-wise: un emparejador puede mejorar el recall
pair-wise y empeorar los grupos. Un buen material de portfolio dice esto explícitamente en vez
de enseñar una sola cifra. ([A Practitioner's Guide to Evaluating Entity Resolution Results](https://arxiv.org/abs/1509.04238))

## 4. Las invariantes: métricas que no necesitan banco

Hay propiedades que **tienen que ser ciertas siempre**, y que se pueden comprobar sin etiquetar
nada. Son las que más veces han salvado este catálogo, y se miden con
`uv run python -m projects.cesta.ejes`:

    grupos con algun eje contradictorio        0    la leche entera y la desnatada, en el
                                                     mismo grupo, es un error seguro
    grupos de 11 o mas productos               0    un grupo enorme casi siempre es una
                                                     fusion: 84 cervezas mezclando sin gluten
                                                     con sin alcohol fue el caso real
    con la misma cadena repetida sin EAN       0    los enlaces son 1-a-1 por par de cadenas,
                                                     asi que un grupo no puede tener dos
                                                     fichas de la misma cadena con EAN
                                                     distinto
    codigos con el pack contradicho           85    y por eso el pack NO se usa como guarda

Las tres primeras bajan a cero con trabajo medido (venían de 49, 74 y 1.385) y son **trinquetes**:
si suben, algo ha empeorado, y la prueba falla en el mismo commit. Es el patrón que en
ingeniería de datos se llama *data contract* (capítulo 02) y aquí no hace falta ninguna
herramienta: son tres consultas.

## 5. El sesgo que hay que declarar antes de tocar el banco

Si el banco son pares con EAN, ningún campo derivado del EAN puede entrar como variable del
modelo: eso es **fuga de información** (leakage) y da números preciosos que no valen nada fuera
de casa. La versión avisada de este problema la publica el benchmark WDC Products: **todos los
matchers actuales empeoran cuando se les mide sobre entidades no vistas**, así que la evaluación
honesta separa productos, categorías y cadenas que no aparecen en el entrenamiento.
([WDC Products](https://arxiv.org/abs/2301.09521))

Y hay una fuga silenciosa que este proyecto ya cometió una vez y tiene documentada: medir con
un banco construido con la misma regla que se está evaluando. Se evita separando el banco
(identificadores con EAN) del método (nombres, formatos, ejes).

## 6. La auditoría que sigue: ¿fue el bloqueo o fue el matcher?

Cuando un par cierto no se encuentra, hay dos causas y el arreglo es distinto:

    fallo de bloqueo    el par no cae en el mismo bloque  -> el matcher no lo ve nunca
    fallo de matching   el par cae en el mismo bloque y no se enlaza -> umbral, similitud,
                                                                       asignacion 1-a-1

Separarlas es el diagnóstico con mejor relación valor/precio de todo el emparejamiento, y ya
están las dos piezas para hacerlo: el medidor de bloqueo (arriba) y el listado de pares que
`--medir` deja fuera. **Lo que falta es el cruce** (capítulo 09, primera fila de la tabla).

## 7. Lo que se aprende en este capítulo

- Antes de mejorar un modelo, **mide su techo**. Si el bloqueo ya pierde un cuarto de los pares,
  el matcher no es el problema.
- Las métricas de evaluación no son neutrales: pair-wise premia lo fácil, B-cubed mira los
  grupos, y las dos pueden contar historias distintas del mismo sistema.
- Las **invariantes** (propiedades que siempre deben cumplirse) son medidas baratas y potentes:
  no necesitan banco etiquetado y detectan la clase de error que más duele (fusiones).
- Declarar el sesgo del banco y la fuga de información no debilita el resultado: lo hace
  creíble.
