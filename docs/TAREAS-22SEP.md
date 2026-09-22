# Encargo de trabajo — 22 de septiembre de 2026

Escrito para el agente que está trabajando en el emparejador y la interfaz.
Cada tarea lleva **por qué**, **cómo se acepta** y **qué no hacer**. La condición
de aceptación es un número o una prueba, nunca una opinión.

---

## 0. Lo que corrijo de lo que dije ayer

Antes de pedir nada, tres cosas mías que estaban mal:

**«Nadie ha vuelto a medir el listón.»** Falso: sí se midió. `--medir` da 65 %
sin vectores y 73 % con ellos. El listón del 57 % está superado. Lo escribí
porque no vi la medición, y afirmar que algo no se ha hecho porque yo no lo he
visto es exactamente el error que este proyecto persigue en los datos.

**«Dejar que la persona corrija un emparejamiento.»** Retirado sin reservas. La
ley del encargo es *«no habrá validación humana NUNCA»* y yo la desconocía. Todo
lo que sigue se apoya en criterios que la máquina puede aplicar sola.

**El inventario de la interfaz nueva.** Dije que le faltaban entrar, lista,
favoritos y ajustes. Ya están. Lo leí del `README.md` de `web/app`, que era de
esta mañana y el trabajo es de esta tarde.

Y una que no es mía: el número de 8.394 grupos comparables que cité salía del
canal de vectores, que ya está revertido. Las cifras de este documento son las
del gold de ahora mismo, y **coinciden con las tuyas**: 74 grupos de 11 o más
productos, con una mediana caro/barato de 2,59 y un 27,0 % por encima de 3×.

---

## 1. El orden, y por qué

Primero lo que **hace falso un dato**, después lo que **pierde un dato**, después
lo que **enseña mejor el dato**. Una interfaz preciosa sobre un grupo que mezcla
leche entera con desnatada es una mentira mejor presentada.

```
A  el emparejador          un grupo ancho da respuestas falsas
B  la captura              dos cadenas de cinco no escribieron hoy
C  la comprobación         hay enlaces rotos que nadie detecta
D  las ofertas             Mercadona publica cero y no lo suplimos
E  la plataforma           funciones a medio conectar
F  la interfaz             la parte que ya estás haciendo
G  la operación            no hay git, y hay dos manos escribiendo
```

---

## A. El emparejador

### A1 · Partir por atributo, no por margen

**Qué.** Que dos productos no puedan caer en el mismo grupo cuando sus nombres
declaran atributos que se contradicen.

**Por qué el margen no sirve como criterio de corte.** El margen es un buen
*detector* —la mediana sube de 1,16 a 2,59 según crece el grupo— y un mal
*cuchillo*: `core/comparacion.py` documenta ahorros reales de 28× entre marca
blanca y marca (preservativos, cerveza, tampones). Cortar por margen borraría
justo los hallazgos que esta aplicación existe para encontrar. La causa no es el
margen; el margen es el síntoma. La causa es que el bloqueo usa **formato +
palabra común** y eso no distingue *entera* de *desnatada*.

**Las listas, sacadas de los grupos que fallan hoy:**

```
leche        entera | semidesnatada | desnatada        y  con lactosa | sin lactosa
aceite       virgen extra | virgen | suave | intenso | orujo | girasol
cafe         natural | mezcla | torrefacto             y  con cafeina | descafeinado
cerveza      con alcohol | sin alcohol (0,0)           y  con gluten | sin gluten
             y  radler/shandy (lleva zumo: no es cerveza sola)
agua         con gas | sin gas
```

**La regla.** Dos productos **no** pueden compartir grupo si cada uno declara un
valor distinto del mismo eje. Si uno no declara nada, **no bloquea**: eso no es
una tolerancia, es ausencia de prueba, y tratarla como contradicción inventaría
un dato que no tenemos.

**Cómo se acepta.**

- `grupo 92` (84 cervezas) se parte en al menos: con alcohol / sin alcohol /
  radler, y ninguno de los tres mezcla con los otros.
- `grupo 2532` (43 aceites) deja fuera el orujo.
- Ningún grupo comparable contiene dos productos con valores distintos del mismo
  eje. Un contador nuevo en el diagnóstico: **grupos con eje contradictorio = 0**.
- `--medir` no baja del 57 %. Si baja, el corte está mal hecho, no la idea.

**Qué no.** No inventar ejes que no estén escritos en el nombre. No usar el
precio para deducir el atributo.

---

### A2 · El pack no es la unidad

**Qué.** Separar la venta suelta de la venta en pack dentro del bloqueo.

**Por qué.** `grupo 444` mezcla *AQUABONA botella de 1,5 l* con *SOLAN DE CABRAS
pack de 6 uds. × 1,5 l*. El precio por litro los hace parecer comparables y no lo
son: la respuesta «el agua más barata está en X» acaba recomendando nueve litros
frente a uno y medio. `grupo 6182` tiene el mismo problema con *pack de 12 latas*
contra lata suelta, y ese grupo por lo demás es correcto —todas son cerveza sin
alcohol—, así que es un caso limpio para probarlo.

**Cómo se acepta.** El número de unidades del envase entra en la clave de bloque.
Un pack de 6 y una botella suelta del mismo litraje quedan en grupos distintos, y
los dos siguen siendo comparables **dentro de su clase** entre cadenas.

**Qué no.** No descartar los packs. Son la mitad de la cesta real.

---

### A3 · Cohesión del grupo: que la unión no deshaga el reparto

**Qué.** Después de `agrupar()`, comprobar que cada miembro se parece al grupo y
no solo a su pareja.

**Por qué.** Éste es el fallo de fondo, y A1 y A2 solo lo tapan por categorías.
El reparto húngaro es 1-a-1 **por par de cadenas**; con cinco cadenas hay diez
pares y `agrupar()` los une por componentes conexas. Entera↔sin lactosa en un
par, sin lactosa↔desnatada en otro, y la transitividad mete entera con desnatada
sin que ningún enlace individual sea malo. Es la avería que el código viejo
documentaba —*«con componentes conexas acaba metiendo tres mil productos en el
mismo grupo»*— entrando por otra puerta.

**Cómo.** Para cada grupo, el medoide (el miembro con mayor parecido medio al
resto). Un miembro que no llegue al umbral contra el medoide sale del grupo y se
queda solo o forma el suyo. Iterar hasta que no se mueva nadie.

**Cómo se acepta.** Con A1, A2 y A3 puestos:

```
tramo      hoy: grupos   hoy: mediana   hoy: >3x     objetivo
2-4            7.277         1,16          4,5 %     igual o mejor
5-10             630         1,97         10,5 %     mediana < 1,7
11 o mas          74         2,59         27,0 %     < 30 grupos y >3x < 10 %
```

Y `--medir` ≥ 57 %. **Las dos condiciones a la vez o no vale**: el fallo que
estamos arreglando fue exactamente subir una mientras bajaba la otra.

**Qué no.** No tocar el algoritmo húngaro. Está bien hecho y bien razonado; el
problema está después de él.

---

### A4 · El listón, en dos números y con trinquete

**Qué.** Que la condición de aceptación deje de ser un solo número.

**Por qué.** El recall premia fundir: cuanto más ancho el grupo, más pares
ciertos caen dentro. Un listón que solo mira recall aplaude la avería. Hizo falta
una lectura desde fuera para ver la otra columna, y eso no puede volver a pasar.

**Cómo.** Un fichero de referencia con las cifras del día (los tres tramos, la
mediana, el % >3×, los grupos con eje contradictorio, el recall con y sin
vectores) y una prueba que falla si **cualquiera** empeora. Como el trinquete que
ya propusiste, pero de la distribución entera y no de dos cifras.

**Cómo se acepta.** La prueba existe, se pone roja al reintroducir a propósito la
unión transitiva sin cohesión, y verde con el código bueno. Una guarda que no se
puede poner roja no guarda nada: demuéstralo en los dos sentidos.

---

### A5 · Separar los dos niveles antes de medir contradicciones

**Qué.** Que `idéntico` y `equivalente` se midan por separado en el diagnóstico.

**Por qué.** Hoy, 2.686 grupos comparables (el 33 % de los que tienen EAN)
contienen más de un EAN. Eso **no es un fallo**: comparar Hacendado con marca
blanca de Carrefour son EAN distintos a propósito, y es el oficio de esta
aplicación. Solo es contradicción si el enlace dice `idéntico`. Si ese 33 % se
cita sin separar, alguien lo usará como prueba de una avería que no existe — y
peor, ocultará la que sí.

**Cómo se acepta.** Dos contadores separados en el informe:
*enlaces `idéntico` con dos EAN distintos* (debe ser **0** desde tu arreglo de
`nivel()`) y *grupos con EAN distintos*, con una frase al lado que diga que eso
es lo esperado.

---

### A6 · Guardar por qué están juntos

**Qué.** Que cada enlace guarde el motivo: `ean`, `nombre+formato`, `sin formato`,
y el parecido.

**Por qué.** `enlaces.parquet` ya tiene `parecido` y `nivel`, pero no el camino.
Sin él no se puede responder «¿por qué me dices que esto es lo mismo?», que es lo
que sostiene la confianza, y no se puede medir qué camino falla más. Además
alimenta directamente `ExplicacionEmparejamiento.tsx`, que ya existe.

**Cómo se acepta.** La columna está, el diagnóstico saca el reparto por motivo, y
la ficha de grupo puede decir en una frase por qué está cada producto dentro.

---

## B. La captura

### B1 · Carrefour: la cuarta categoría rota

```python
# projects/cesta/collectors/carrefour.py
"cat11729677": "papeleria/colorear, HTTP 500 desde el 17 sep 2026",
```

**Por qué.** Hoy se han tirado 16.525 productos buenos por esa categoría. Lleva
fallando con HTTP 500 en veinte ejecuciones del log; no se notaba porque la
tolerancia que quitamos el día 21 se la tragaba, y al declarar las roturas me
dejé ésta, que es hermana de las otras dos de papelería.

**Cómo se acepta.** La siguiente ejecución de Carrefour escribe bronze.

---

### B2 · Que no vuelva a pasar por olvido

**Qué.** Que el colector se declare a sí mismo las roturas de origen, con prueba.

**Por qué.** B1 es un parche a un olvido, y los olvidos se repiten. Lo que falló
no fue la regla estricta —hizo justo lo que debía— sino la lista escrita a mano.

**Cómo, sin tolerancias y sin validación humana.** Una categoría pasa a
`rota en origen` cuando se cumplen las tres a la vez:

- devuelve el **mismo** código 5xx en **N ejecuciones seguidas** (N = 3);
- sigue apareciendo en el sitemap, así que no es que la hayan quitado;
- el resto de su rama responde bien, así que no es un bloqueo nuestro.

Se anota en un fichero de estado **con su fecha de primera vez y su código**, y
se revisa cada día: el día que conteste 200, sale de la lista y se dice en el
resumen («ya funciona»). Eso no es «hasta N fallos permitidos»: es *estas
categorías, por su id, desde esta fecha, con esta prueba*.

**Cómo se acepta.** Reproducir el caso de hoy: con el log de las últimas diez
ejecuciones, las cuatro de papelería/congelados salen declaradas solas y ninguna
otra. Ni una de más.

---

### B3 · Alcampo y el WAF

**Qué.** Que perder contra el WAF cueste menos catálogo.

**Por qué.** Hoy se quedó en 9.729 de 23.776 y descartó, bien descartado. Pero
las ramas que se pierden son siempre las últimas del recorrido: Perfumería
−100 %, Mascotas −100 %, Droguería −99 %. No es casualidad, es el orden.

**Cómo.** Rotar el orden de las ramas entre ejecuciones (semilla = el día), de
forma que a lo largo de la semana ninguna sea sistemáticamente la sacrificada.
Y aprovechar `data/alcampo_por_donde_iba.txt`, que ya existe, para reanudar por
donde se quedó en vez de empezar de cero.

**Cómo se acepta.** Sobre las capturas parciales de los últimos diez días, ningún
nodo de primer nivel queda por debajo del 50 % más de dos veces seguidas.

**Qué no.** Ni resolver el reto ni automatizar nada que lo esquive. Si el WAF
gana, se conserva el bronze anterior y se dice, que es lo que ya hace.

---

### B4 · Por qué hoy se ejecutó dos veces

**Qué.** Investigar el par de ejecuciones de hoy: una a las 07:52 que registró
aldi y mercadona y paró, y otra completa a las 09:13.

**Por qué.** Hay un `runlock` precisamente para esto. O no cubrió el caso, o la
primera murió sin soltarlo, o la tarea programada disparó dos veces. El 21 de
septiembre ya hubo una ejecución que murió en silencio a las 09:31 y solo se
salvó porque el disparador de inicio de sesión saltó un minuto después. Dos
síntomas del mismo sitio.

**Cómo se acepta.** Una explicación con la línea del log que la prueba, y el
arreglo o la razón escrita de por qué no lo necesita.

---

### B5 · La forma del enlace, comprobada al escribir

**Qué.** Subir los patrones de URL de `extension/contenido.js` a un módulo
compartido y hacer que el pipeline marque (o rechace) la fila cuya `url` no
encaje con la forma de su cadena.

**Por qué.** Lo de Alcampo no fue un enlace caído: fue **un enlace con la forma
equivocada** —un UUID donde va un número— durante quince días, en los 23.776. No
lo vio ningún control; lo vi abriendo dos productos a mano. Y se puede comprobar
**sin una sola petición de red, sobre el 100 % de las filas**, en el momento de
escribir. Los patrones ya existen y `tests/test_extension.py` ya los comprueba
contra el bronze real: hoy solo protegen a la extensión.

**Cómo se acepta.** Reinyectando el bronze de Alcampo del 21 de septiembre, el
pipeline lo señala. Con el del 22 en adelante, no dice nada.

---

### B6 · Barrido de cabeceras

**Qué.** 50 URL al azar por cadena y día, petición `HEAD`, a 0,5/s. Unos ocho
minutos.

**Por qué.** B5 caza la forma; esto caza que la tienda haya movido las fichas. Si
las 23.776 están rotas, 50 muestras dan 50 fallos: sirve para detectar roturas de
**clase**, que son las que importan. Para encontrar *un* enlace muerto no sirve,
y no hace falta.

**Cómo se acepta.** Sale en el resumen diario junto a la comprobación de precios,
y una cadena con más del 20 % de 404 en la muestra es un fallo, no un aviso.

---

## C. La comprobación

### C1 · Aldi se ha quedado sin control

**Qué.** Sondear la ficha de Aldi y, si el precio viaja en un JSON incrustado,
leerlo de ahí en `verificar_precios.py` como ya se hace con Mercadona.

**Por qué.** Hoy: 8 de 8 «sin precio». El colector va perfecto (2.123 filas, 0
errores) porque usa otra ruta, pero la ficha pública ya no enseña ninguna cifra
con euro a un cliente HTTP normal. O lo han pasado a JavaScript, o nos sirven otra
página. El efecto es que **los datos de Aldi entran sin que nada de fuera los
contraste**, que es justo lo que la comprobación existe para impedir.

```
uv run python -m projects.cesta.sondear_cadena aldi --guardar
```

**Cómo se acepta.** Aldi vuelve a dar 8 de 8, o queda escrito con pruebas que su
ficha ya no publica precio y cuál es la ruta alternativa.

---

### C2 · Carrefour: 403 en el verificador

**Qué.** Que la comprobación use el mismo **transporte** que el colector
(curl_cffi con impersonación y su sesión), no el `Fetcher` desnudo.

**Por qué.** 5 de 8 salen «no se pudo» por HTTP 403 de Cloudflare. Una
comprobación que falla la mitad de las veces deja de ser una comprobación.

**Y el límite que no se cruza:** se comparte el transporte, **nunca el parser**.
El precio se sigue leyendo como lo leería una persona, con los patrones de
`sondear_cadena`. Un control que usa el mismo lector que el colector siempre está
de acuerdo consigo mismo, y un control que no puede discrepar no es un control.
Esto está escrito en la cabecera de `verificar_precios.py` y sigue vigente.

**Cómo se acepta.** Carrefour da 8 de 8, o los que no coincidan lo hacen por el
precio y no por la red.

---

### C3 · Probar el arreglo de las URL de Alcampo

**Qué.** En cuanto Alcampo vuelva a capturar, comprobar que los enlaces nuevos
llevan `retailerProductId` y responden 200.

**Por qué.** El arreglo del día 21 **sigue sin estar probado**: la comprobación
muestrea el último bronze, que es del 21 y es anterior al arreglo. Mientras
tanto, los 23.776 enlaces que publica la aplicación no llevan a ninguna parte.
`tests/test_extension.py` ya tiene la fecha declarada en `ARREGLADAS` y volverá
solo.

---

### C4 · Que la comprobación no dependa de la suerte de la muestra

**Qué.** Fijar la semilla por día y guardar el histórico de veredictos.

**Por qué.** Ocho productos por cadena es poco para afirmar nada de un producto y
suficiente para afirmar algo de la cadena, **si se acumula**. Con el histórico,
«alcampo lleva tres días a 0/8» es un hecho; sin él, cada día es una anécdota.

---

## D. Las ofertas

Punto de partida, medido hoy:

```
cadena      productos   con texto de oferta   de club   solo internet
alcampo        23.776    3.116 (13,1 %)          578       398
carrefour      16.560    3.645 (22,0 %)        1.124         0
aldi            2.123      103 ( 4,9 %)           0         0
dia             5.780      223 ( 3,9 %)         197         0
mercadona       4.328        0 ( 0,0 %)           0         0
```

### D1 · Mercadona publica cero, y hay que mirar si es verdad

**Qué.** Sondear el JSON de la ficha de Mercadona buscando precio anterior,
precio por bulto o cualquier campo de promoción. Su bloque `price_instructions`
tiene más campos de los que leemos.

**Por qué.** Cero de 4.328 no significa que Mercadona no tenga ofertas: significa
que no las escribe donde miramos. Con la regla de paridad de datos de este
proyecto, una cadena entera sin ofertas es un agujero, no un detalle.

**Cómo se acepta.** Un sondeo con el veredicto escrito, gane o pierda.

---

### D2 · La oferta medida, que es la que sí tenemos para las cinco

**Qué.** Un derivado `oferta_medida` a partir de nuestra propia serie: precio de
hoy contra la base de los últimos N días, con el mínimo de 90 días al lado.

**Por qué.** Es la única fuente **igual de disponible en las cinco cadenas**,
incluidas las dos que no publican nada. Y es mejor prueba: una bajada que hemos
medido durante 17 días vale más que una etiqueta escrita por el departamento de
marketing de la cadena. `precio_derivado.parquet` ya tiene `precio_base_cent`,
`min_90d_cent` y `posicion_90d` calculados; falta usarlos para esto.

**El encuadre, que no es un detalle.** Esto **no** se enseña como «¡oferta! antes
3,00, ahora 2,50». Se enseña como lo que es: *«lleva 14 días a 3,00 y hoy está a
2,50; el mínimo de los últimos 90 días fue 2,45»*. Lo primero es vender; lo
segundo es informar para decidir, y es la diferencia entre esta aplicación y las
de la competencia.

**Cómo se acepta.** Las cinco cadenas tienen cobertura comparable, y las cuatro
reglas de `movimientos` se aplican igual: si cambió la unidad, si cambió la
cantidad implícita, si el precio de venta no se movió o si el factor es
imposible, **no es una bajada**.

---

### D3 · Cuánto del texto de oferta no entendemos

**Qué.** Medir el porcentaje de `promo_txt` que acaba en `Mecanica.SIN_REGLA`,
por cadena, y cerrar las formas que más aparezcan.

**Por qué.** `core/promos.py` está bien hecho y cubre «la gran mayoría», pero esa
frase no es un número. El 17 de septiembre, al añadir DIA, resultó que solo se
entendía la mitad de lo suyo. Lo que no se entiende se trata como si no hubiera
oferta —que es el error seguro y está bien elegido—, pero no sabemos cuánto es.

**Cómo se acepta.** El número sale en el resumen diario por cadena.

---

### D4 · Las ofertas que no bajan el precio, contadas aparte

**Qué.** Que el resumen diga cuántas promociones son de tarjeta o de solo
internet, por cadena.

**Por qué.** Hoy son 1.124 de club en Carrefour y 578 + 398 en Alcampo. No bajan
lo que se paga en caja y por eso no cuentan —decisión correcta y ya tomada—, pero
tampoco se ven. Saber que una cuarta parte de las «ofertas» de una cadena no
existen en caja **es** un dato para decidir dónde comprar.

---

## E. La plataforma

### E1 · Las alertas no le buscan a nadie

**Qué.** Evaluar las alertas en la cadena diaria, después del pipeline, y dejar
el resultado guardado.

**Por qué.** Hoy `alertas.evalua()` solo se ejecuta cuando alguien abre
`GET /api/alertas`. Es decir: **la alerta solo salta si entras a mirar**, que es
exactamente lo contrario de para lo que existe. El módulo dice de sí mismo que es
«lo único que convierte un histórico en algo que te busca a ti en vez de esperar a
que entres», y hoy espera. Es un fallo mío y está sin corregir.

**Cómo se acepta.** El resumen diario dice cuántas alertas saltaron y de quién, y
al abrir la aplicación ya están calculadas.

---

### E2 · El escáner no tiene detrás a nadie

**Qué.** `GET /api/ean/{codigo}`.

**Por qué.** `Escaner.tsx` existe en la interfaz nueva y la ruta no existe en la
API. Está en `docs/API.md` como «tarea 8» y sigue pendiente. Con 25.517 productos
con código de barras, es la función que mejor relación trabajo/valor tiene de
toda la lista.

**Cómo se acepta.** Devuelve el producto, su grupo y el aviso de cobertura
—cuántos de los nuestros tienen EAN— para que un «no lo encuentro» no se lea como
«no existe».

---

### E3 · Con el registro abierto, falta la puerta de salida

**Qué.** Poder quitarle la cuenta a alguien.

**Por qué.** Desde hoy cualquiera que llegue a la página se hace una cuenta.
`GET /api/personas` deja ver quién ha entrado, pero no hay forma de echar a nadie
desde la aplicación: hoy es una consulta SQL a mano. La función
`borrar_usuario(uuid)` ya existe en `sql/003_mas_de_dos.sql` y hace lo correcto
(se lleva lo suyo y no vacía la lista de otro).

**Cómo.** Un booleano `es_duenno` en la primera cuenta creada. No es un sistema
de roles y no contradice «sin papeles ni niveles»: es una llave, no una jerarquía.

---

### E4 · La cesta óptima merece su pantalla

**Qué.** Sacar «dónde compro la lista» de dentro de la ficha y darle pantalla.

**Por qué.** Es el cálculo más valioso que hace la aplicación —usa las mecánicas
de promoción de verdad, no el precio a secas— y está escondido.

---

### E5 · Un grupo ancho no decide

**Qué.** Que la API marque los grupos que no son de fiar y que ninguna pantalla
que recomiende tienda los use para decidir.

**Por qué.** Es la misma regla que ya existe para los precios de más de tres días:
se enseñan con su fecha pero no deciden. Mientras A1–A3 no estén, 74 grupos dan
respuestas falsas con mucha seguridad. Y cuando estén, seguirá habiendo alguno.

**Cómo se acepta.** El campo existe, `cesta.py` lo respeta, y la pantalla dice
por qué se calla en lugar de callarse sin más.

---

### E6 · Añadir sin escribir

**Qué.** El mosaico de lo habitual, a partir del historial de listas.

**Por qué.** Es la segunda de `COMPETENCIA.md` §7 y la que más cambia el uso real:
en el pasillo, con el carro y una mano ocupada, teclear es lo que no se hace. Se
construye solo desde el primer día que se use la lista.

---

## F. La interfaz (recomendaciones, no encargo)

Esto es tuyo y no lo he tocado. Lo que veo desde fuera:

**F1.** La fuga de `fonts.googleapis.com` ya la has arreglado — era lo más
urgente y contradecía de frente la decisión que sostiene el proyecto entero.

**F2.** Un grupo tiene que poder decir **por qué** está junto, y decir «no estoy
seguro». `ExplicacionEmparejamiento.tsx` ya existe; con A6 tendrá el motivo real
que contar.

**F3.** Un precio sin fecha es una afirmación falsa. Cualquier cifra que no sea
de hoy lleva su día al lado; una de más de tres días se ve pero no decide. Ya está
decidido en `/api/estado`; que ninguna pantalla nueva se lo salte.

**F4.** Nunca «antes 3,00 / ahora 2,50» con aspecto de oferta. El movimiento se
enseña como movimiento. Es una instrucción explícita del dueño.

**F5.** Los estados vacíos dicen qué falta y por qué. El «Nada con «».» de un
pasillo vacío fue un fallo real que solo se vio en una captura de pantalla.

**F6.** La lista funciona sin cobertura: el identificador de línea lo genera el
móvil y cada cambio viaja con su hora. Es lo que hace usable la aplicación en el
único sitio donde se usa de verdad.

**F7.** Zona del pulgar. Lo que se toca con el carro en marcha —tachar, sumar
uno, marcar en el carrito— abajo y grande.

**F8.** Ninguna pantalla de la interfaz nueva puede perder lo que tiene la vieja.
Hoy ya incluye registro, compartir lista e invitación por enlace.

---

## G. La operación

**G1 · git.** Antes que todo lo demás. `F:\aprendizaje\scrap` no tiene `.git`, y
hoy dos agentes han escrito en los mismos ficheros: `core/matching.py`,
`core/normalize.py` y `pipeline.py` se modificaron mientras la ejecución diaria
estaba en marcha, y el gold se escribió después. No hay forma de saber si los
números de esta mañana salen todos del mismo código. Sin historial, el día que un
cambio empeore algo no hay a dónde volver — y con dos manos ese día llega antes.
`data/` y `.env` fuera, claro.

**G2 · La tarea programada.** El 21 de septiembre la ejecución de las 06:18 murió
en silencio a las 09:31 y solo se salvó porque el disparador de inicio de sesión
saltó un minuto después. Hace falta que una ejecución que muere **lo diga**.

**G3 · El respaldo.** `respaldar.bat` existe. Falta que corra solo y que alguien
compruebe alguna vez que el `.sql.gz` no está vacío, que es el fallo clásico de
todos los respaldos del mundo.

---

## Lo que NO hay que hacer

- **Validación humana de emparejamientos.** Ley del encargo. Todo lo de arriba es
  automático a propósito.
- **Cortar por margen.** Borraría los ahorros reales de 28× que esta aplicación
  existe para encontrar. El margen detecta; el atributo corta.
- **Tocar el algoritmo húngaro.** Está bien. El fallo está después.
- **Correr a por la sexta cadena.** RadarSuper cubre siete y enseña 177
  referencias comparables; nosotros con cinco tenemos miles. Las cadenas se
  suman, el emparejamiento se gana.
- **Resolver o esquivar el reto de AWS WAF**, abrir un puerto en el router,
  guardar datos de pago, direcciones o códigos de tarjeta de fidelización.
- **Folletos.** Caros, se rompen cada temporada, y lo que traen acaba reflejado
  en el precio de la ficha, que ya capturamos.
- **Subir un número sin mirar el otro.** Es lo que pasó hoy.

---

## Cómo se acepta el conjunto

Al final de todo, y en una sola ejecución:

```
uv run pytest -q                                   todo verde
uv run python -m projects.cesta.emparejar --medir  >= 57 %
uv run python -m projects.cesta.diagnostico_matching
        grupos con eje contradictorio              0
        grupos de 11+                              < 30
        de esos, con >3x                           < 10 %
        enlaces 'identico' con dos EAN distintos   0
uv run python -m projects.cesta.verificar_precios  las 5 cadenas informan,
                                                   y ninguna a 0/8
uv run python -m projects.cesta.verificar_docs     sin avisos
ruff check .                                       limpio
```

Y las cinco cadenas escribiendo bronze el mismo día, que es lo único que de
verdad mide si esto funciona.
