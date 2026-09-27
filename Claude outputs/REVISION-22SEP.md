# Revisión del 22 de septiembre de 2026

Escrita desde fuera, sin tocar código, mientras otro agente trabaja en el
emparejador. Todo lo que dice se reproduce con los comandos que van al lado.

> **Aviso sobre las cifras.** El catálogo se rehizo dos veces hoy: la ejecución
> diaria terminó a las 09:26 y alguien volvió a lanzar el emparejador a las
> 12:36. Los números de aquí salen de **la segunda**, que es lo que hay en
> `data/gold` ahora mismo. El resumen que imprimió la ejecución diaria dice otra
> cosa (6.379 grupos comparables) porque es de la primera.

---

## 0. Resumen para decidir

1. **El emparejador nuevo junta cosas que no son la misma.** Medido sobre las
   842 leches de un litro del catálogo de hoy, con los dos algoritmos y el mismo
   dato de entrada: el de antes daba 106 grupos comparables y el mayor tenía 18
   productos; el de hoy da **76 grupos y el mayor tiene 123**, con leche entera,
   desnatada y sin lactosa dentro del mismo. El titular global (8.394 grupos
   comparables, un 30 % más que ayer) sube mientras la respuesta empeora.
2. **Y se ve en el precio.** En los grupos de 11 productos o más, la diferencia
   mediana entre el más caro y el más barato es de **2,76×**, y el 39,5 % pasa de
   3×. En los grupos de 2 a 4 productos es de 1,16×. Un grupo ancho no enseña un
   ahorro: enseña dos productos distintos.
3. **Nadie ha vuelto a medir el listón después del cambio.** `DIAGNOSTICO-MATCHING.md`
   fija `--medir = 57 %` como el mínimo que no se puede bajar, y ese 57 % es
   **anterior** al algoritmo húngaro. Es la primera cifra que hay que sacar.
4. **Los enlaces rotos se siguen descubriendo a mano.** Lo de Alcampo (23.776
   enlaces con UUID durante quince días) no lo vio ningún control: lo vi al abrir
   dos productos en un navegador. Hay una forma de cazarlo el primer día, sin una
   sola petición de red, y está en el punto 3.
5. **Mercadona no publica ni una oferta y Aldi casi ninguna.** 0 % y 4,9 % frente
   al 22 % de Carrefour. Mientras las ofertas salgan de leer el texto que escribe
   la cadena, eso no tiene arreglo, y choca de frente con «no me gusta eso de que
   dato no encontrado».

---

## 1. El emparejador nuevo

### Lo que mejora, y es real

`core/matching.py` ha cambiado en dos cosas, y las dos estaban bien vistas:

**`nivel()` mentía.** Decía «idéntico» cuando dos productos compartían marca,
aunque tuvieran códigos de barras distintos. Medido por el propio agente: de
1.475 enlaces marcados `identico` con EAN en los dos lados, solo 1.033 (70 %)
compartían código. Ahora el EAN manda cuando existe y la marca solo decide
cuando no hay códigos que comparar. Eso es un arreglo limpio de algo que era
falso.

**La elección mutua dejaba parejas sobre la mesa.** Con «el mejor de cada uno»,
dos productos de una cadena pueden elegir al mismo de otra y uno se queda sin
pareja teniendo una igual de buena al lado. El reparto óptimo 1-a-1 (algoritmo
húngaro, escrito a mano, sin numpy ni scipy) lo resuelve. Está bien razonado y
bien comentado, incluido el detalle de maximizar **la ganancia por encima del
umbral** en vez del parecido a secas, que evita que dos parejas mediocres
desplacen a una buena.

### Lo que rompe

El reparto es 1-a-1 **por par de cadenas**. Con cinco cadenas hay diez pares, y
después `agrupar()` une todo por componentes conexas. Así que entera↔sin lactosa
en un par, sin lactosa↔desnatada en otro, y la unión transitiva mete entera con
desnatada. Es exactamente la avería que el código viejo documentaba y evitaba
—*«con componentes conexas... acaba metiendo tres mil productos en el mismo
grupo»*— entrando por otra puerta.

**El experimento, para repetirlo.** Mismo dato de entrada (las 842 leches de un
litro del catálogo de hoy), los dos algoritmos:

```
ANTES (elección mutua)    grupos 587 | comparables 106 | el mayor  18 productos
HOY   (húngaro)           grupos 469 | comparables  76 | el mayor 123 productos
```

El grupo de 123 tiene dentro, entre otros: *KAIKU Leche entera sin lactosa*,
*CENTRAL LECHERA ASTURIANA Leche desnatada 0 % materia grasa*, *PRIÉGOLA Leche
entera fresca*, *RAM Leche de vaca desnatada*. No son el mismo producto ni
equivalentes: son categorías distintas del mismo lineal.

En el catálogo entero de hoy, los grupos más grandes son del mismo tipo:

| grupo | productos | qué hay dentro |
|---|---:|---|
| 0 | **202** | todas las cervezas de 33 cl: radler con zumo de limón, sin gluten, 0,0 tostada, lager |
| 292 | 82 | aceite de oliva suave + virgen extra + **orujo** (2,85 €/l frente a 7,94 €/l) |
| 341 | 67 | café molido natural + descafeinado + mezcla |
| 694 | 62 | leche entera + desnatada + sin lactosa |
| 241 | 41 | agua mineral de 1,5 l — este sí es defendible |

### El tamaño del problema

```
tramo               grupos  productos   caro/barato (mediana)   % con >3×
2-4 productos         7.549    18.179            1,16             4,2 %
5-10                    715     4.327            1,87            11,3 %
11 o más                119     2.288            2,76            39,5 %
```

119 grupos, 2.288 productos: el 9,2 % de lo comparable. No es catastrófico en
volumen, pero son justo los grupos de los productos que más se compran —leche,
aceite, café, cerveza, agua— y son los que una persona va a mirar primero.

Y un dato que hay que leer con cuidado antes de alarmarse: **2.686 grupos
comparables (el 33,4 % de los que tienen EAN) contienen más de un EAN distinto.**
Eso **no** es un fallo por sí solo: comparar Hacendado con marca blanca de
Carrefour es el oficio de esta aplicación y son EAN distintos a propósito. Solo
sería contradicción si el enlace estuviera marcado `identico`. Lo dejo escrito
para que nadie lo use como prueba de nada sin separar antes los dos niveles.

### Lo que yo haría (no lo he hecho)

No tocar el húngaro: está bien. El problema no es el reparto, es **que la unión
transitiva no respeta lo que el reparto decidió**. Tres caminos, de más barato a
más caro:

1. **Un tope de tamaño de grupo.** Si un grupo pasa de N productos, es que algo
   se ha fundido; se parte o se marca como no comparable. Es una tirita, pero
   hoy dejaría fuera los 119 grupos malos en una línea.
2. **Que el atributo distinga.** *entera / semidesnatada / desnatada*,
   *con lactosa / sin lactosa*, *natural / descafeinado*, *virgen extra / suave /
   orujo*, *con alcohol / 0,0*. Son cinco listas cortas de palabras que ya están
   en el nombre. El bloqueo hoy usa formato y una palabra común; añadir el
   atributo al bloque es barato y arregla la causa, no el síntoma.
3. **Dejar que la persona corrija.** Es la idea 10.1 de `COMPETENCIA.md`, la que
   el propio documento llama «la mejor idea del día». Con 119 grupos malos y una
   persona que los ve, media hora de correcciones vale más que otra iteración del
   algoritmo. Y las correcciones se quedan: son datos de entrenamiento gratis.

**Antes que nada: volver a medir.** `uv run python -m projects.cesta.emparejar --medir`.
Si ha bajado del 57 %, el cambio no puede quedarse aunque el número de grupos
haya subido.

---

## 2. La ingesta de hoy

Tres cadenas de cinco.

```
aldi        2.123 productos   0 errores     65s   ✓
mercadona   4.328             0 errores     92s   ✓
dia         5.780             0 errores    112s   ✓
alcampo     9.729             1 error      463s   ✗ no escribió
carrefour  16.525             4 errores   2.790s   ✗ no escribió
```

**Alcampo**: ganó el WAF de AWS. Tras 11 intentos en 60 s seguía el reto. El
colector vio los agujeros por rama (Perfumería −100 %, Mascotas −100 %,
Droguería −99 %) y conservó el bronze del día 21. La defensa funcionó.

**Carrefour**: 16.525 de ~16.560 productos, y se descartó entera por **una**
categoría, `cat11729677` (papelería/colorear), con HTTP 500.

Eso último es culpa mía y conviene que quede escrito. Esa categoría aparece
fallando con HTTP 500 en **veinte ejecuciones** del log, desde mucho antes del
día 20. No se notaba porque Carrefour tenía una tolerancia que se la tragaba en
silencio. Al quitar la tolerancia el 21 de septiembre declaré las tres roturas
que el log del día 20 enseñaba y me dejé la cuarta, que es hermana de dos de
ellas —las tres de papelería son la misma avería en la misma rama—. La regla
estricta hizo lo que tenía que hacer; la lista de excepciones estaba incompleta.

Arreglo, en `projects/cesta/collectors/carrefour.py`:

```python
"cat11729677": "papeleria/colorear, HTTP 500 desde el 17 sep 2026",
```

---

## 3. Enlaces caídos: el control que falta

Hoy la comprobación de precios saca esto:

```
dia         8/8 coinciden
mercadona   8/8 coinciden
carrefour   3/8   (5 con HTTP 403: falla el verificador, no el dato)
alcampo     0/8   (8 con 404)
aldi        0/8   (8 sin precio)
```

Tres cosas distintas, y conviene no mezclarlas.

**Alcampo, 8 de 8 en 404.** Está muestreando el bronze del 21, anterior al
arreglo de las URL. Es el comportamiento correcto, pero significa que **el
arreglo sigue sin estar probado** y no lo estará hasta que Alcampo se deje
capturar. Mientras tanto, los 23.776 enlaces que publica la aplicación no llevan
a ninguna parte.

**Aldi, 8 de 8 «sin precio», y esto es nuevo.** El colector va perfecto, pero la
ficha pública ya no enseña ninguna cifra con euro a un cliente HTTP normal. O han
movido el precio a JavaScript, o nos sirven una página distinta. El efecto es que
**Aldi se ha quedado sin control independiente**: sus datos entran sin que nada
de fuera los contraste. Hay que sondear la ficha
(`uv run python -m projects.cesta.sondear_cadena aldi --guardar`) y, si el precio
está en un JSON incrustado, leerlo de ahí como se hace con Mercadona.

**Carrefour, 5 «no se pudo» por HTTP 403.** Es Cloudflare bloqueando al
verificador, no un dato malo. Pero deja la verificación de Carrefour en 3 de 8, y
una verificación que falla la mitad de las veces deja de ser una verificación.

### La comprobación que hay que añadir, y es gratis

El fallo de Alcampo no era un enlace caído: era **un enlace con la forma
equivocada**. Un UUID donde va un número. Y eso se puede comprobar **sin una sola
petición de red, sobre el 100 % de las filas, en el momento de escribir el
bronze**.

Los patrones ya existen y ya se comprueban contra el bronze real: están en
`extension/contenido.js` y los lee `tests/test_extension.py`. Hoy solo protegen a
la extensión. Si esos mismos patrones se suben a un sitio compartido y el
pipeline rechaza (o marca) la fila cuya `url` no encaja con la forma de su cadena:

- lo de Alcampo se habría visto **el primer día**, en la primera ejecución;
- no cuesta ni una petición, ni un segundo de red;
- y la prueba que ya existe deja de ser una prueba de la extensión para ser la
  regla del dato, que es donde tiene que estar.

Por encima de eso, y ya con red, un barrido de cabeceras (`HEAD`) sobre 50 URL
por cadena al día —250 peticiones, unos ocho minutos a 0,5/s— detecta una rotura
sistémica de inmediato: si las 23.776 están rotas, 50 muestras dan 50 fallos. No
sirve para encontrar *un* enlace muerto, y no hace falta: lo que hay que cazar
son las roturas de clase, no las de producto.

---

## 4. Ofertas: de dónde salen hoy

```
cadena      productos   con texto de oferta   de club   solo internet
alcampo        23.776    3.116 (13,1 %)          578       398
carrefour      16.560    3.645 (22,0 %)        1.124         0
aldi            2.123      103 ( 4,9 %)           0         0
dia             5.780      223 ( 3,9 %)         197         0
mercadona       4.328        0 ( 0,0 %)           0         0
```

Hoy una oferta es una cadena de texto que la cadena escribe en su ficha, y
`core/promos.py` la traduce a una regla con la que se puede multiplicar. Esa
parte está bien resuelta y es mejor que lo que hace la competencia: no decimos
«hay promo», decimos «llevando dos, 1,50 € menos por unidad». Y los descuentos de
tarjeta se reconocen y **no** bajan el precio, que es lo correcto porque ese
dinero no se descuenta en caja.

El problema no es cómo se lee: es **de dónde**.

**Mercadona no publica ni una.** Cero de 4.328. Y no es que no tenga ofertas: es
que no las escribe en la ficha. Aldi, 4,9 %. Con la regla de paridad de datos que
lleva este proyecto desde el principio, eso es un agujero, no un detalle.

### Las tres vías, en orden de lo que rinden

**1. Nuestra propia serie, que ya la tenemos y no la usamos para esto.** 17 días
de precios diarios por producto. Una bajada que hemos medido es mejor prueba que
una etiqueta que ha escrito el departamento de marketing de la cadena, y **está
disponible para las cinco cadenas por igual**, incluidas las dos que no publican
nada. `precio_derivado.parquet` ya tiene `precio_base_cent`, `min_90d_cent` y
`posicion_90d` calculados.

Ojo con el encuadre, que ya lo dijiste: esto no se enseña como «¡oferta! antes
3,00 ahora 2,50». Se enseña como lo que es —*«lleva 14 días a 3,00 y hoy está a
2,50; el mínimo de los últimos 90 días fue 2,45»*—, que es información para
decidir y no un reclamo. La diferencia entre las dos cosas es exactamente la
diferencia entre esta aplicación y las de la competencia.

**2. El precio tachado que algunas cadenas sí publican.** Antes de construir
nada, hay que mirar si el JSON de Mercadona trae un precio anterior junto al
actual (su ficha pública lleva un bloque `price_instructions` con más campos de
los que leemos). Es media hora de sondeo y puede resolver la cadena que peor
está.

**3. Los folletos.** Todas publican folleto semanal, y `COMPETENCIA.md` ya
estudió a Tiendeo y Ofertia. Es la vía más cara —un folleto es un PDF o un visor
propio por cadena, y se rompe cada temporada— y la que menos aporta, porque lo
que trae el folleto acaba casi siempre reflejado en el precio de la ficha, que ya
capturamos. **No la recomiendo todavía.**

---

## 5. Lo que tiene la competencia y no tenemos

De las listas de `COMPETENCIA.md`, quitando lo ya hecho (pasillos, escáner,
alertas, extensión de navegador, verificador de ofertas, nota de composición,
cuentas y registro), queda esto, ordenado por lo que de verdad cambia el uso:

**1. Corregir un emparejamiento a mano** (Soysuper, §10.1). Hoy es la primera de
la lista y no lo era ayer: con 119 grupos mal fundidos, una persona que pueda
decir «esto no es lo mismo» arregla en media hora lo que el algoritmo no sabe, y
deja las correcciones guardadas para siempre. Es además la única de toda la lista
que **mejora el dato** en vez de enseñarlo mejor.

**2. Añadir sin escribir**: el mosaico de lo habitual. Tres toques en lugar de
teclear en el pasillo con una mano ocupada. Necesita historial, que se construye
solo desde el primer día que se use la lista.

**3. Ver la mecánica de la oferta mientras añades** (idea de Tiendeo, hecha
mejor). `core/promos.py` ya sabe la regla; hoy esa regla solo se usa para decidir
la tienda, no se enseña al añadir.

**4. Notas por línea.** El campo ya existe en la base. Es interfaz y nada más.

**5. La nota de Yuka con la fórmula a la vista** (60 % Nutri-Score, 30 %
aditivos, 10 % ecológico). Es absoluta, no una posición dentro del grupo, así que
no se puede confundir con el precio — que es el problema que tiene hoy nuestra
letra de calidad.

**6. «Hay uno mejor y más barato».** Sigue bloqueado por lo mismo que el año
pasado: los grupos anchos. Con los grupos de hoy daría consejos falsos.

No me llevaría, y coincido con lo que ya está escrito: escaneo de tickets por
foto, tarjetas de fidelización, amigos por @usuario, y **correr a por la sexta y
séptima cadena**. RadarSuper cubre siete cadenas y enseña 177 referencias
comparables; nosotros con cinco tenemos miles. Las cadenas se suman; el
emparejamiento se gana.

---

## 6. La interfaz, mirada desde fuera

No la he tocado, por encargo. Tres cosas que veo y dejo para quien la esté
haciendo:

**La interfaz nueva no tiene entrar, ni lista de la compra, ni favoritos, ni
ajustes.** Su propio `README.md` lo dice y dice bien que servir `web/dist` hoy
quitaría funciones. Añado un dato que ese README no puede saber: hoy se ha
añadido **registro de cuentas** (`POST /api/registrarse`, pantalla de crear
cuenta, y el enlace de invitación que sobrevive al alta). Si un día se cambia el
montaje a `dist`, eso desaparece también.

**La fuente.** La interfaz vieja carga Archivo desde `fonts.googleapis.com`. Eso
contradice la decisión que sostiene todo el proyecto —los datos no salen del
PC—, porque cada vez que tu madre abre la aplicación, Google se entera de que la
ha abierto. La nueva ya usa fuente del sistema y hace bien. Es un cambio de una
línea en la vieja, y si hay una sola cosa de interfaz que valga la pena tocar hoy
es esa.

**Un grupo ancho no se puede enseñar como un ahorro.** Con lo del punto 1,
cualquier pantalla que diga «más barato en X» sobre un grupo de 123 productos
está dando una respuesta falsa con mucha seguridad. Mientras el emparejador no se
arregle, esas pantallas deberían callarse en los grupos grandes en vez de
adivinar: es la misma regla que ya se aplica a los precios de más de tres días.

---

## 7. Y una cosa que no es de datos

`F:\aprendizaje\scrap` **no tiene `.git`**, y ahora mismo hay dos agentes
escribiendo en los mismos ficheros. Hoy `core/matching.py`, `core/normalize.py` y
`pipeline.py` se modificaron mientras la ejecución diaria estaba en marcha, y el
gold se escribió después: no hay forma de saber si los números de esta mañana
salen todos del mismo código.

El otro agente ya lo puso como su decisión número uno y tiene razón. Sin
historial, el día que un cambio empeore algo no hay a dónde volver, y con dos
manos escribiendo a la vez ese día llega antes.
