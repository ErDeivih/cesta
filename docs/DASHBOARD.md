# Cesta — el cuadro de mando

La app responde "que compro y donde". El cuadro de mando responde otra cosa:
**que esta pasando con los precios**. Es para ti, no para tu madre, y por eso va
en su propia pantalla y no dentro de la app.

Todo lo que hay aqui se ha probado contra los datos reales del 15 de septiembre
de 2026. Lo que no sale hoy, se dice que no sale y cuando saldra.

---

## 1. Lo que los datos aguantan hoy

Medido, no supuesto.

    productos en el catalogo                51.781
    grupos comparables                       6.448  (con 2 cadenas o mas)
    productos dentro de un grupo compartido 19.235  (el 39 %)
    dias de historico                            9
    filas de precio diario                 560.640
    productos con 7 dias o mas              34.329

    productos con Nutri-Score                8.359  (16 %)
    productos con letra de calidad           9.754  (19 %)
    productos con origen declarado           1.296  (2,5 %)

### La diferencia de precio entre cadenas, que es la pregunta de fondo

Sobre los 5.568 grupos con dos cadenas o mas y comparacion fiable (kg, l, m):

    diferencia mediana entre la mas cara y la mas barata    19,4 %
    percentil 90                                           158,4 %
    grupos con mas del 200 % (sospechosos, formato mal leido)  405

**El 19,4 % mediano es el numero que justifica el proyecto.** En la mitad de los
productos que se pueden comparar, comprar en la cadena equivocada cuesta un 19 %
mas.

### Quien es mas barato, medido

Veces que cada cadena tiene el precio por unidad mas bajo, sobre los grupos donde
esta presente:

    ALDI         60,5 %   (presente en 951 grupos)
    ALCAMPO      51,2 %   (6.448)
    MERCADONA    38,0 %   (1.826)
    DIA          27,5 %   (3.188)
    CARREFOUR    17,4 %   (5.456)

Aldi gana casi siempre pero juega poco: solo esta en 951 grupos de 5.578. Alcampo
gana la mitad de las veces y esta en casi todos. Carrefour es la cadena mas cara
de forma consistente, y esta en casi tantos grupos como Alcampo.

### Cuanto se mueven los precios

    cadena      productos que cambian de precio al dia    movimiento mediano
    DIA                        4,14 %                        0,13 EUR/kg
    ALCAMPO                    2,47 %                        1,25 EUR/kg
    CARREFOUR                  2,21 %                        0,40 EUR/kg
    MERCADONA                  1,06 %                        0,02 EUR/kg
    ALDI                       0,99 %                        0,54 EUR/kg

Mercadona casi no mueve precios, y cuando los mueve es por centimos. DIA los
mueve cuatro veces mas a menudo. Esto ya es una conclusion publicable, con nueve
dias.

---

## 2. Lo que NO sale todavia, y cuando saldra

Hay que decirlo antes de dibujar nada, porque son la mitad de las graficas que
uno querria.

    oferta_sospechosa       0 casos hoy. El detector compara con el precio de
                            hace 45 dias. Empieza a funcionar el 20 de octubre.
    tendencia_30d           0 productos hoy. Necesita 30 dias.
                            Empieza el 5 de octubre.
    posicion_90d            degenerada: el 90 % de los productos sale en 0,5
                            porque con 9 dias el minimo y el maximo casi
                            coinciden. Util a partir de diciembre.
    estacionalidad          hace falta un ano.

**Esto no se arregla programando.** El cuadro de mando se construye ahora con los
huecos marcados, y se va llenando solo. Un panel que diga "esta grafica necesita
30 dias de historico, lleva 9" es honesto; uno que dibuje una linea plana con
nueve puntos y la llame tendencia, no.

---

## 3. Cuatro estudios con su resultado, y uno que estuvo a punto de mentir

No son ideas de graficas: son preguntas ya contestadas contra los datos del 15
de septiembre. Cada una es una pantalla del panel.

### 3.1 ¿Cuanto se paga por el nombre de la marca?

Sobre los **1.899 grupos** donde compiten una marca propia y una marca de
fabricante, y donde la comparacion por unidad es fiable:

    marca propia    13,32 EUR por unidad (media)
    marca           16,39 EUR
    diferencia      18,8 %

Como "marca propia" se cuentan Hacendado, Deliplus, Bosque Verde y Compy en
Mercadona; PRODUCTO ALCAMPO; CARREFOUR y sus variantes; las marcas de DIA; y
**todo Aldi**, que es marca propia entera.

### 3.2 ¿Y es peor? — el estudio que casi sale al reves

La primera medida decia esto:

    marca propia    38,1 % con calidad A,  33,6 % con C
    marca           52,3 % con calidad A,  20,6 % con C

Titular evidente: la marca propia es mas barata pero peor. **Y es falso.**

El motivo esta en como se calcula la letra. `core/calidad.py` la saca de los
ingredientes cuando los hay, y cuando no hay ingredientes en ningun producto del
grupo, **cae a ordenar por precio**: la mas cara se lleva la A. El codigo es
honesto y lo marca en `calidad_origen`, pero nada aguas abajo miraba esa columna.

    de donde sale cada letra      productos     %
      precio                          9.032   77,0
      ingredientes                    1.724   14,7
      ingredientes de Open Food Facts   971    8,3

    y la prueba, dentro del grupo "precio":
      calidad A -> 9,14 EUR/unidad (mediana)
      calidad B -> 7,17
      calidad C -> 5,22

O sea: en el 76,9 % de los casos, "calidad A" significa literalmente "el mas caro
de su grupo". La marca propia es mas barata, luego se lleva la C, luego "es
peor". El razonamiento se muerde la cola.

**Rehecho mirando solo las letras leidas de una etiqueta de verdad**, cara a cara
dentro del mismo grupo:

    grupos donde compiten con calidad leida    355
      gana la marca propia                     122
      empatan                                  128
      gana la marca                            105

La conclusion honesta es la contraria de la primera: **la marca propia cuesta un
18,8 % menos y, donde se pueden leer los ingredientes, no es peor.**

Lo que hay que arreglar antes de ensenar nada de esto:

1. **Una letra sacada del precio no se llama calidad.** O se ensena como "gama"
   (alta / media / basica), que es lo que de verdad es, o no se ensena.
2. **Ninguna conclusion agregada puede mezclar los dos origenes.** El panel
   filtra por `calidad_origen` antes de sumar, siempre.
3. La app puede seguir usando la gama por precio para ordenar dentro de un grupo.
   Lo que no puede es llamarla calidad.

### 3.3 ¿Cuanto se mueven los precios?

    cadena      productos que cambian al dia    movimiento mediano
    DIA                    4,14 %                  0,13 EUR/kg
    ALCAMPO                2,47 %                  1,25 EUR/kg
    CARREFOUR              2,21 %                  0,40 EUR/kg
    MERCADONA              1,06 %                  0,02 EUR/kg
    ALDI                   0,99 %                  0,54 EUR/kg

Mercadona casi no mueve precios, y cuando los mueve es por centimos. DIA los
mueve cuatro veces mas a menudo. Con nueve dias esto ya es publicable, y son
entre 1.000 y 2.000 filas al dia: hay contenido de sobra para una pantalla de
"que se ha movido hoy".

### 3.4 ¿Donde esta el ahorro? — y por que este todavia no se publica

Agrupando por la seccion del arbol de Alcampo, que es el mas rico:

    seccion                  grupos   diferencia mediana
    Agua, Soda y Gaseosas        89         167,6 %
    Cervezas                    164         100,8 %
    Licores                      53          94,5 %
    Conservas vegetales          81          88,7 %
    Quesos                      291          80,0 %
    Conservas de pescado        146          78,8 %

Antes de creerselo hay que mirar un grupo. El de agua con gas mas disperso tiene
dentro, todos con el formato bien leido:

    Agua con gas Carrefour Classic 1,25 l     0,28 EUR/l
    Agua con gas Aldi 1,25 l                  0,33
    Agua con gas Dia 500 ml                   0,52
    San Pellegrino 50 cl                      2,20
    Perrier 50 cl                             2,40

Los formatos estan bien. **El problema es que el grupo es demasiado ancho**:
mete Perrier con la marca blanca. Son la misma *categoria*, no el mismo producto,
y llamar "diferencia de precio" a la distancia entre Perrier y la marca del
super es confundir dos cosas.

Asi que el 167,6 % del agua no mide un ahorro: mide lo ancho que es el grupo. La
pantalla de secciones **no se publica hasta que la anchura de los grupos este
bajo control** (punto 5), porque es exactamente la cifra que mas llama la
atencion y la que peor envejece si esta mal.

---

## 4. Las pantallas

Seis. La primera es la que se abre.

### 4.1 Hoy

- **La ingesta**: que cadenas entraron, cuantos productos, cuanto tardaron, si
  hubo fallos. Sale de `data/runs.csv`, que ya existe.
- **Precios que se han movido**: las bajadas y subidas de hoy, por cadena.
- **La alerta que importa**: si una cadena entro con muchos menos productos de lo
  normal. Alcampo paso de 43.643 a 23.500 al recortar el bazar; una caida asi sin
  un cambio de alcance detras significa que algo se rompio.

### 4.2 Cadenas

El ranking de barata a cara, filtrable. Cuanto se mueve cada una. Cobertura de
catalogo y de ficha nutricional, que es donde se ve de un golpe que Alcampo y
Aldi no dan ingredientes. Y el estudio 3.1.

### 4.3 Productos

La curva de las cinco cadenas superpuesta, la diferencia entre la mas cara y la
mas barata en el tiempo, y quien mueve primero. Lo ultimo necesita mas historico.

### 4.4 Marcas

Cuantos productos tiene cada marca y en cuantas cadenas esta. Si una marca cuesta
lo mismo en todas partes: una marca nacional que en Carrefour vale un 20 % mas
que en Alcampo es un hallazgo concreto. Y el estudio 3.2, con su advertencia.

### 4.5 Calidad y nutricion

Con la cobertura siempre delante: **esto habla del 16-19 % del catalogo**, y ese
porcentaje es casi todo Carrefour, DIA y Mercadona.

Reparto de Nutri-Score por cadena. Si lo mas barato es lo peor (ahora se puede
responder de verdad, filtrando por origen de la letra). Aditivos y aceite de
palma por cadena.

**Y lo que hay que traer de Open Food Facts y no estamos trayendo** (`CADENAS.md`
punto 5): 11.723 de nuestros productos tienen tabla de nutrientes completa en OFF
(calorias, grasas, azucares, sal), 10.209 tienen categoria, y 8.055 tienen
sellos: sin gluten (2.667), ecologico (1.205), vegano (763), sin lactosa (717),
sin aceite de palma (267). Eso son filtros utiles de verdad, mucho mas que el de
origen.

### 4.6 Lineas de producto

**Bloqueada** hasta que exista una categoria canonica y los grupos dejen de ser
demasiado anchos. Ver 3.4.

## 5. Como se construye

**No hace falta un producto de cuadros de mando.** Metabase o Superset piden un
contenedor grande, una base de datos propia y una configuracion que mantener, y
lo unico que ganan es que alguien que no eres tu haga consultas. Aqui no hay ese
alguien.

    consultas   DuckDB sobre los parquet de gold. Sin copiar nada.
    servidor    las mismas rutas de cesta-api, bajo /panel
    graficas    una libreria de graficos ligera sobre HTML. Nada mas.
    cache       cada consulta del panel se guarda en memoria hasta que cambia
                el parquet de gold, que es una vez al dia

La regla de oro: **cada numero del panel lleva al lado de donde sale y de que
fecha es**. Un panel que ensena un 19,4 % sin decir sobre cuantos grupos se ha
calculado no es un panel, es una opinion con tipografia.

---

## 6. Lo primero

Tres graficas. Ninguna necesita nada que no exista hoy, y las tres se pueden
comprobar contra los numeros de este documento:

1. **El ranking de cadenas** por veces que es la mas barata (punto 1).
2. **Los precios movidos hoy**, por cadena (estudio 3.3).
3. **Marca propia contra marca**, con el filtro de `calidad_origen` puesto desde
   el primer dia (estudios 3.1 y 3.2).

La tercera se pone la primera en la lista de las que hay que revisar, porque es
la que ya demostro que se puede contar mal.

**No se empieza por** la pantalla de secciones ni por nada que dependa de la
categoria: esta bloqueada por 3.4 y por la anchura de los grupos.
