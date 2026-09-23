# Revisión del 23 de septiembre de 2026

Leído `docs/TRASPASO-CLAUDE.md` entero. Lo que sigue es lo que añade algo a lo
que ya está ahí: la ingesta de hoy en directo, **un criterio de corte que creo
que resuelve el punto 1.1 mejor que la cohesión contra el medoide**, tres
correcciones y unos cuantos avisos.

---

## 0. Lo primero: el criterio que parte los grupos

El traspaso pide la cohesión contra el medoide para el caso de las 84 cervezas,
«donde ningún eje se contradice y hoy sólo lo caza el pack». Creo que hay un
criterio mejor, y no es un umbral: **es la invariante que el propio reparto ya
promete y que la unión por componentes conexas rompe.**

El reparto húngaro es **1-a-1 por par de cadenas**. Eso significa que un grupo
correcto no puede tener dos productos de la misma cadena. Medido sobre el gold de
ahora mismo:

```
                                grupos   con cadena repetida
comparables (todos)              7.981         1.385
  de 2 a 4 productos             7.277           714   ( 9,8 %)
  de 5 a 10                        630           597   (94,8 %)
  de 11 o más                       74            74   (100,0 %)
```

**Los 74 grupos que incumplen la barra incumplen los 74 esta invariante.** Y el
grupo de las cervezas lo dice sin ambigüedad:

```
grupo 92   84 productos:  alcampo 25, dia 25, carrefour 17, mercadona 14, aldi 3
grupo 444  47 productos:  alcampo 20, carrefour 11, dia  9, mercadona  7
grupo 2532 43 productos:  alcampo 17, carrefour 14, dia  7, aldi 3, mercadona 2
```

Veinticinco cervezas de Alcampo en un grupo no son un grupo ancho: son
**diecisiete grupos fundidos en uno**. No hace falta medir parecidos contra un
medoide para verlo, y con el medoide además cuesta: en un grupo de 84 cervezas
todas se parecen razonablemente al centro —todas son «X Cerveza 33 cl»—, así que
el umbral que las separa es difícil de elegir y va a ser distinto por categoría.
La cuenta por cadena no necesita umbral.

### La regla

> Un grupo no puede contener dos productos de la misma cadena, **salvo que
> compartan código de barras**.

La excepción es el duplicado legítimo: la misma referencia listada dos veces. Son
pocos y se distinguen solos:

```
pares (grupo, cadena) con más de un producto     2.200
  con un solo EAN distinto  -> duplicado real        66
  sin ningún EAN                                    999
  con dos o más EAN distintos                     1.135
```

### Cómo partir, sin inventar nada nuevo

No hace falta otro algoritmo: hace falta **la misma unión con una guarda**. Es
Kruskal sobre los enlaces del grupo, ordenados por parecido de mayor a menor:

```
para cada enlace (a, b, parecido), de mayor a menor:
    si unir el subgrupo de a con el de b deja alguna cadena repetida
       (y los repetidos no comparten EAN)  ->  se descarta el enlace
    si no  ->  se unen
```

Es decir: `agrupar_enlaces()` sigue siendo union-find, pero **rechaza la unión
que rompería la invariante**. Los enlaces fuertes ganan; los flojos, que son los
que fundían categorías distintas, se caen solos. Cinco líneas dentro de la
función que ya existe, ordenación incluida.

Propiedades que me parecen las buenas:

- **No hay umbral que ajustar**, así que no hay nada que se desajuste por
  categoría. Es una invariante, no una tolerancia.
- **No mira el precio**, así que no puede borrar los ahorros de 28×. Cumple la
  regla 1 del dueño sin esfuerzo.
- **Se lleva bien con los ejes y el pack**: ésos cortan antes y más barato, en el
  bloqueo; esto es la red que recoge lo que se cuela. Los tres suman, no compiten.
- **Es determinista** si se desempata por `(i, j)` a igualdad de parecido.

### Lo que hay que vigilar, dicho antes de hacerlo

Kruskal con restricción es **voraz, no óptimo**: el resultado depende del orden y
un enlace fuerte puede bloquear a dos buenos. Por eso la medición de después no
es opcional. Mi apuesta, que puede salir mal y hay que comprobar:

```
grupos con cadena repetida        1.385  ->  0        por construcción
grupos de 11 o más                   74  ->  < 30     la barra
grupos con eje contradictorio        54  ->  baja, no necesariamente a 0
grupos comparables                 7.981 ->  sube     (se parten, no se pierden)
--medir                              65 % ->  ?        AQUÍ ESTÁ EL RIESGO
```

Si `--medir` cae por debajo del 57 %, el corte está partiendo pares ciertos y hay
que mirar por qué antes de tocar el umbral. Y las cinco condiciones se miden
juntas, que es la trampa número 1 del traspaso.

---

## 1. La ingesta de hoy, en directo

A las 08:08 UTC, con la ejecución todavía en marcha:

```
aldi        2.066 productos   0 errores    85s   escrito
mercadona   4.325             0 errores    93s   escrito
dia         5.809             0 errores   648s   escrito
carrefour   en 375/651 categorías, 13.267 productos
alcampo     en 150 categorías, 12.656 productos, 231 en cola
```

**Carrefour debería escribir hoy.** `cat11729677` ya está declarada en
`ROTAS_EN_ORIGEN`, y con la investigación hecha: se rastreó hasta el **8 de
septiembre** en el log, dos semanas antes de lo que yo había escrito. En el log
de hoy vuelve a dar HTTP 500 en la categoría 129 y ahora ya no cuenta como fallo
nuestro. Si no aparece otra rotura nueva, hoy se cierra la quinta condición de la
barra por primera vez desde el día 21.

**Alcampo va mejor que ayer.** Reanuda por donde se cortó —*«empezando por la
104»*— y a mitad de recorrido lleva 12.656 productos, cuando ayer acabó con
9.729. El WAF ha saltado cuatro veces y se ha recuperado las cuatro.

### Una alarma que retiro antes de darla

Iba a señalar que DIA había tardado 648 s hoy contra 112 s ayer, casi seis veces
más. Miré la serie antes de escribirlo:

```
15 sep  634s   16 sep  649s   17 sep  614s   18 sep  802s   19 sep 1.092s
20 sep  664s   21 sep  635s   21 sep   24s   22 sep  112s   23 sep  648s
```

648 s **es lo normal**. Lo raro eran los 24 s y los 112 s, que son dos relanzados
el mismo día con la caché caliente. La anomalía era al revés. Lo dejo escrito
porque es exactamente la trampa 3 del traspaso —*un ejemplo no es una
distribución*— y casi la piso yo.

---

## 2. Lo que corrijo de mi propia revisión

- **`/api/ean/{codigo}` y `/api/panel/matching` existen** y responden 200. Mi
  inventario era de la mañana y el trabajo era de la tarde. Retirado.
- **La paridad del front está resuelta**: escribir en la cesta, registro,
  compartir con enlace, favoritos y ajustes. También retirado.
- **La API de darse de baja funciona.** Falta el botón, no la ruta.

Queda en pie lo de las alertas (1.3), que es mío y sigue sin arreglar.

---

## 3. El canal de vectores: el arreglo propuesto no basta

El traspaso dice que el arreglo es que los candidatos de vectores pasen por **el
mismo reparto y el mismo `ocupados`** que los otros dos canales. Es necesario, y
creo que no es suficiente.

Los 861 conflictos no salen sólo de que cada canal reparta por su cuenta: salen
de que el canal de vectores **propone pares que el canal de nombre no propondría
nunca**, y con la misma puntuación nominal. Al meterlos en el mismo reparto,
algunos ganarán la plaza a un par de nombre peor puntuado pero mejor fundado —y
ahí el conflicto no desaparece, se convierte en un enlace flojo que sí se emite.

Lo que propongo, y ya existe en el código como principio: en la segunda pasada,
*«un enlace con formato comprobado siempre gana a uno sin comprobar, aunque el
nombre del segundo se parezca más»*. Lo mismo aquí. **Los vectores entran en el
mismo reparto pero con la puntuación penalizada** (o con un listón más alto), de
forma que sólo ganan donde el nombre no tiene nada que ofrecer. Así suman recall
en el hueco y no desplazan nada de lo que ya funciona.

Y después, las dos columnas: recall **y** conflictos. Como dice el traspaso.

---

## 4. Cosas que nadie está mirando

### 4.1 `embedding.parquet` son 200 MB dentro de `data/gold`

Gold es la frontera del sistema: lo que el scraper escribe y la plataforma monta
**en solo lectura**, y lo que `docs/DESPLIEGUE.md` define como «lo que lee todo
el mundo». Un artefacto de modelo de 200 MB no es eso. Hoy no rompe nada
—`catalogo.py` monta vistas sobre ficheros concretos y no lo toca—, pero:

- ensucia un contrato que hasta ahora estaba limpio;
- entra en cualquier copia o sincronización de gold que se haga;
- y cuando el canal de vectores se encienda, habrá que saber si se regenera
  entero cada día, porque son 200 MB de escritura diaria.

Sitio natural: `data/vectores/` o `data/modelos/`, fuera de gold.

### 4.2 La extensión lleva tres días sin que nadie la mire

La extensión del navegador pinta, **encima de la web del supermercado**, el
precio, la curva y «más barato en X: −N %». Ese «más barato en X» sale del grupo.
Con 74 grupos fundidos, ahora mismo hay productos en los que la extensión está
dando un consejo falso en el peor sitio posible: delante del estante, a alguien
que va a decidir con él.

No pido tocarla. Pido que entre en la lista de lo que hay que revisar cuando el
corte esté hecho, y que mientras tanto se aplique 4.3.

### 4.3 «Un grupo ancho no decide» — y esto va **antes** del arreglo

Es la regla puente, y es la misma que el proyecto ya aplica a los precios de más
de tres días: *se enseñan con su fecha, pero no deciden dónde comprar*.

Mientras haya 74 grupos que mezclan cosas distintas, cualquier pantalla que diga
«más barato en X» sobre uno de ellos está dando una respuesta falsa con mucha
seguridad. El campo que lo marca es barato de calcular —la invariante del punto 0
lo da gratis: *este grupo tiene la cadena repetida, no es de fiar*— y debería
existir **hoy**, no cuando el corte esté hecho. Porque el corte puede tardar y el
consejo falso ya se está dando.

Y cuando el corte esté hecho seguirá haciendo falta, porque siempre quedará algún
grupo dudoso y es mejor que la aplicación sepa callarse.

Afecta a `cesta.py` (dónde comprar la lista), a la ficha de grupo, a la extensión
y a las alertas.

---

## 5. Interfaz: lo que añadiría a las 33 medidas

El estudio de `docs/DISENO.md` no lo he leído y no lo voy a duplicar. Tres cosas
de las que el traspaso ya lista, ordenadas por lo que yo haría primero, y dos que
no están:

**Primero, `/favoritos` y `/ajustes` sin un solo enlace.** De todo lo listado, es
lo único que no es pulido sino **función muerta**: dos pantallas construidas,
probadas y terminadas a las que no se puede llegar. Y una de ellas es donde va a
vivir el botón de darse de baja. Arreglar esto es un `<Link>`.

**Segundo, la cesta sin separar «por coger» de «en el carro».** Con nueve líneas
y cuatro cogidas hay que leer nueve nombres con el carro en marcha. La columna
`en_carrito` existe en la base desde `002_invitaciones.sql` y se creó justo para
esto.

**Tercero, las siete zonas por debajo de 44 px.** Están medidas una a una, así
que es trabajo mecánico.

Y dos que no están en la lista:

**El estado de «no es de fiar» tiene que verse, no sólo aplicarse.** Si una
pantalla se calla porque el grupo es ancho, tiene que decir por qué. Un hueco sin
explicación se lee como un fallo de la aplicación; una frase corta —*«aquí hay
productos que no estoy seguro de que sean lo mismo»*— se lee como honestidad, que
es lo que de verdad distingue esto de la competencia.

**El mosaico de habituales está desbloqueado.** El traspaso dice que
`/api/habituales` no existe y que por eso el mosaico está parado. Cierto — pero
también dice que `/api/ean` se hizo en la ronda 11 del goal anterior. Son la misma
clase de trabajo: una consulta sobre datos que ya están. Con el historial de
listas que se va acumulando desde que hay cuentas, es la mejora que más reduce el
trabajo de usar la aplicación en el sitio donde se usa.

---

## 6. Lo que sigo pidiendo que no se haga

- **Cortar por margen.** Detecta, no corta.
- **Tocar el húngaro.** Está bien; el fallo está después.
- **Subir un número sin mirar los otros cuatro.**
- **La sexta cadena.** Con cinco y el emparejador arreglado hay más valor que con
  siete y los grupos fundidos.
- Y lo de siempre: ni resolver el reto del WAF, ni abrir puertos, ni guardar
  datos de pago, direcciones o códigos de tarjeta.

---

## 7. La barra, y lo que le falta

```
condición                                    traspaso     lo que espero del punto 0
pruebas verdes                               682 / 0      igual
--medir >= 57 %                              65 %         hay que volver a medir
cero grupos con eje contradictorio           54           baja, quizá no a 0
menos de 30 grupos de 11+                    74           debería cumplirse
cinco cadenas con bronze del mismo día       por comprobar hoy se decide
```

Y una sexta que propongo añadir, porque es la que ha resultado ser el mejor
detector de todos y hoy no está en la barra:

```
grupos comparables con la misma cadena repetida
  y sin EAN compartido                       1.385  ->  0
```
