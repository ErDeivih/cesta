# F10 . Plan y cocina


---

## El modo cocina, verificado en el navegador -- y la prueba es que el tiempo BAJA sin que nadie cuente

*(Ronda 179, con la pila del sandbox: API pid 25732, Vite pid 46096.)*

### Lo que se midio

```
empezar:               201
temporizador 10 min:   201  {"paso":0,"minutos":10,
                             "empezo_en":"2026-10-12T10:22:34.602482+00:00",
                             "acaba_en":"2026-10-12T10:32:34.602482+00:00"}

lectura 1:                  quedan 599 s
lectura 2 (4 s despues):    quedan 595 s
ha bajado 4 s   -> SI, y eso es la prueba
¿se reinicio a 600?: NO
```

**Y la pantalla, tras doce segundos:**

```
Cocina
Vas por el paso 1. 0 ingredientes usados.
10 min - quedan 9 min 55 s
Paso siguiente
Temporizador de 10 min
errores de JavaScript: []
```

### Y por que **eso** es la prueba, y no otra cosa

**Lo que se queria comprobar no es que la pantalla ensene un numero: es que el numero **no dependa de que alguien
lo este contando**.**

**Dos lecturas separadas cuatro segundos dieron `599` y `595`.** *Y entre las dos **no habia nada corriendo**:
ninguna peticion que dijera «resta», ningun proceso, ningun contador.* **El servidor guardo **cuando empezo**, y
cada lectura **calcula** lo que queda.**

> **Y por eso `595` y no `600`.** *Si el temporizador fuera una cuenta atras guardada, la segunda lectura habria
> devuelto **`599` otra vez** -- o **`600`**, si se hubiera reiniciado.* **Devolvio `595`: han pasado cuatro
> segundos de verdad, y el sistema no los estaba contando.**

**Es exactamente la decision que se escribio en `core/cocina.py`, en la migracion `018` y en la pantalla** -- *«un
temporizador **no es una cuenta atras, es una hora de fin**»* --, **y aqui esta medida de punta a punta**: *el
esquema guarda el instante, la ruta calcula al leer, y la pantalla lo ensena en palabras («quedan 9 min 55 s»).*

### Y lo que esto promete, que es lo que importa para quien cocina

**Si se recarga la pantalla, o se apaga el movil, o se va la conexion, al volver el numero es el correcto** --
*porque **no habia nada que perder**: el tiempo no estaba en ningun contador, estaba en dos instantes.*

**Y el limite sigue en pie**: *esto se ha medido **con** conexion. Lo que se ha probado es que **el calculo no
necesita al servidor para ser correcto** -- *el servidor da los instantes, y a partir de ahi el reloj lo lleva el
aparato.* **Medir «sin conexion» de verdad** -- *cortando la red* -- **es un ensayo que aun no se ha hecho.**

### Y el estado de `R05`

**Sus cuatro capas, verificadas**: *logica (`core/cocina.py`, 10 pruebas), tabla (`018`), ruta (5 endpoints) y
**pantalla vista**.* **Es la segunda de las cuatro funciones ausentes que queda entera de arriba abajo, despues
de `R08`.**


---

## 6. **El ensayo «sin conexion» -- y falla.** *El diseno era el bueno; lo que se manda es el numero, no el instante.*

*(Ronda 184. **Esto contradice lo que el §5 y el docstring de `core/cocina.py` afirman, y hay que decirlo.**)*

### Lo que se midio

**Se puso un temporizador de 30 minutos, se abrio la pantalla, y se corto la red** (`context.set_offline(True)`):

```
CON conexion:         quedan 1799 s
SIN conexion, t=0:    quedan 1799 s
SIN conexion, t=20:   quedan 1799 s
NO HA BAJADO -> EL NUMERO ESTA CONGELADO, no se recalcula
```

**Veinte segundos sin conexion y el numero no se movio.** *El numero **esta congelado**, no recalculado.*

### Y por que, que es lo importante: **el diseno era el bueno, y la costura no**

**La decision de `core/cocina.py` y de la migracion `018` es correcta**: *se guarda **cuando empezo**, y **lo que
queda se calcula**.* **El servidor lo hace bien**: *`Temporizador.queda()` **calcula** de verdad, y por eso el
ensayo de dos lecturas separadas cuatro segundos dio `599` y `595`.*

**Lo que falla es **lo que viaja**.** *El endpoint `reanudar` devuelve*

```python
{"paso": t.paso, "minutos": t.minutos,
 "queda_segundos": int(t.queda(ahora).total_seconds()),   # <-- EL NUMERO YA CALCULADO
 "terminado": t.ha_terminado(ahora)}
```

**-- el numero **ya calculado**, y no el instante.** *Y la pantalla pinta ese numero tal cual.* **Asi que sin
conexion no hay nada que recalcular: no llego el instante, llego la cuenta hecha.**

> **La promesa -- «reanudar es volver a leer, y funciona sin conexion porque el reloj lo lleva el aparato» -- **no
> se cumple**, porque **al aparato no le llego el reloj**: le llego el resultado.* **El calculo esta en el sitio
> equivocado.**

### Y el arreglo, que es pequeno y esta claro

**Que el endpoint devuelva **el instante** en vez del numero:**

```python
{"paso": t.paso, "minutos": t.minutos,
 "acaba_en": t.acaba_en.isoformat()}      # <-- el instante, y que reste quien lo tiene delante
```

**Y que la pantalla calcule `acaba_en - Date.now()`.** *Entonces si: **si se recarga, o se apaga el movil, o se va
la conexion, el numero es correcto** -- *porque **el instante sigue estando** y **el reloj lo lleva el aparato**.*

**No se ha hecho todavia**, y queda dicho con su forma exacta.

### Y lo que este ensayo enseña, que es lo que mas vale de la ronda

**El §5 dio por bueno el «funciona sin conexion» **sin cortar la red**.** *Se probo que **el servidor calcula**, y
**eso no es lo mismo** que **el cliente puede calcular**.* **Es exactamente la distincion que esta fase repite
-- «no se sale» no es «se lee bien», «limite de fuente» no es «pendiente» --, y esta vez cayo del lado mio:** *una
frase escrita en tres sitios -- el modulo, la migracion y el documento -- que **sonaba a decision tomada** y
**nadie habia medido**.*

> **Y solo se vio cortando la red.** *Que es, literalmente, **el ensayo que el propio §5 habia dejado apuntado como
> «aun no se ha hecho»**.*


---

## 7. El arreglo del §6: **hecho, y a medias** -- *con conexion si; sin conexion, todavia no*

*(Ronda 185.)*

### Lo que se cambio, y **esta bien**

**Tres cambios, y los tres son los del §6:**

1. **`core/cocina.py`**: el `reanuda` devuelve ademas **`"acaba_en": t.acaba_en.isoformat()`** -- *el instante, y no
   solo el numero ya calculado.*
2. **`api/cocina.ts`**: el tipo `Temporizador` **exige `acaba_en`**.
3. **`CocinaModo.tsx`**: **la pantalla resta ella** -- *`segundosQueQuedan(t.acaba_en)` = `acaba_en - Date.now()`.*

**Y medido**: *el servidor manda `{"paso": 0, "minutos": 30, "acaba_en": "2026-10-12T11:06:38.846371+00:00", ...}`*
**y la pantalla pinta `30 min -- quedan 29 min 21 s`.**

### Y un cuarto cambio, que salio del propio ensayo

**`if (error) return <p>{textoDeError(error)}</p>`** -- *y sin conexion, **el refresco de cada 15 segundos falla y
esa linea borraba la cocina entera**, temporizador incluido.* **Se cambio por `if (error && !data)`**, para que
*con datos en la mano, el fallo del refresco **se diga y se siga**.*

### Y lo que **todavia no funciona**

```
CON conexion:       quedan 1799 s
SIN conexion t=0:   quedan None s
SIN conexion t=12:  quedan None s
```

**Sigue sin recalcularse -- y esta vez `None` quiere decir que la pantalla no dice «quedan» en absoluto.**

### Y lo que **no** se ha hecho, que es lo que hay que hacer

**No se ha mirado QUE dice la pantalla en ese estado.** *El ensayo **solo busca la frase «quedan»**, y cuando no
la encuentra apunta `None` -- **que no es un diagnostico, es un no-encontrado**.* **Es el mismo error del §6, otra
vez: medir por una frase y concluir sobre la pantalla.**

**Lo siguiente, exacto**: *imprimir **el cuerpo entero** con la red cortada.* **Con eso se sabra si es (a) el
`refetchInterval` que deja la consulta en error, (b) un `pageerror` que no se estaba capturando en ese tramo, o
(c) que la pantalla se ha ido a la rama de «no esta empezada»** -- *y cada una se arregla distinto.*

**Y una hipotesis que hay que descartar primero, porque es la mas probable**: *Vite sirviendo un modulo viejo* --
*ya paso en el §4 (un `Not Found` que era un 404 de una API de tres horas) y **se descarta mirando, no suponiendo**:
`tsc` da 0 y el cambio esta en el fichero, pero **lo que sirve el navegador es otra cosa**.*


---

## 8. La lectura que decidia: **dos causas, y la segunda es un defecto de verdad**

*(Ronda 186. Se imprimio **el cuerpo entero** con la red cortada, que es lo que el §7 dejo apuntado.)*

### Lo que se midio

```
CON conexion:   «... Cocina | Vas por el paso 1. 0 ingredientes usados.
                 | 30 min -- quedan 30 min 0 s | Paso siguiente | Temporizador de 10 min»

¿el modulo que sirve Vite tiene `acaba_en`?:  False          <-- CAUSA 1

=== CON LA RED CORTADA ===
   ... Cocina
   «ESTA RECETA NO ESTA EMPEZADA.»                            <-- CAUSA 2
   «Empezar a cocinar»
   errores JS: []
   peticiones fallidas: []
```

### Causa 1: **Vite sirve un modulo viejo** -- *y ahora esta medido, no supuesto*

**`fetch('/src/api/cocina.ts')` y buscar `acaba_en` da `False`.** *O sea que **el modulo que llega al navegador no
tiene el arreglo del §7** -- aunque `tsc` de 0 y el fichero en disco si lo tenga.*

**Es la misma cosa que el §4** (*un `Not Found` que era un 404 de una API de tres horas*) **y la misma que el §6**
(*un «Cargando» que era prisa*): **mirar el fichero y concluir sobre lo que se sirve.** *Ya no es una hipotesis:
**el propio navegador lo dice**, y la comprobacion es **una linea**.*

### Causa 2: **sin conexion, la pantalla AFIRMA algo que no sabe** -- *y esto es un defecto del codigo, no del ensayo*

**«Esta receta no esta empezada.»** *Eso es lo que dice la pantalla con la red cortada.*

**Y es falso.** *La receta **si** esta empezada: *hay un paso y un temporizador de 30 minutos en la base.* **Lo que
pasa es que la consulta no ha podido traerlo.**

> **`if (!data || data.paso === null)` mete en el mismo saco dos cosas opuestas**: *«el servidor dice que no hay
> nada» y «no he podido preguntar»*. **Y la pantalla elige la primera, que es la que afirma.**

**Es exactamente el pecado que esta fase lleva cazando desde `sin_precio`**: *convertir **«no se sabe»** en
**una afirmacion**.* **Y aqui la afirmacion es ademas la que desanima**: *alguien que este cocinando, sin cobertura
en la cocina, abre la pantalla y **lee que no ha empezado** -- *cuando lo que pasa es que el movil no tiene
red.*

### Y el arreglo, que son dos cosas distintas

1. **Para la causa 1**: *que Vite sirva lo de ahora* -- *reiniciarlo, que **ya se hizo una vez en esta misma
   fase*** --, *y **volver a comprobar `acaba_en`** con la misma linea antes de creerse nada.*
2. **Para la causa 2**: **separar los dos casos.** *`isLoading` ya esta; lo que falta es **distinguir «la consulta
   fallo» de «la consulta dijo que no hay nada»**.* **Y la pantalla, cuando falla, tiene que decir **que no pudo
   preguntar** -- *y, si hay datos viejos, **seguir enseñandolos***, que es lo que el §7 empezo a arreglar con
   `if (error && !data)`.

**Y la causa 2 es la que importa**, porque *no es del ensayo: **es de la pantalla**, y **se ve sin cortar nada** --
*basta con que el servidor no conteste una vez.*


---

## 9. La causa 2, **arreglada y verificada** -- *y la causa 1 sigue en pie*

*(Ronda 187.)*

### La causa 2: **arreglada, y el arreglo se ve**

**El bloque se partio en tres, y cada uno dice una cosa distinta:**

```
45:  if (isLoading) return ...                     <- aun no ha llegado la primera respuesta
57:  if (!data) { ... }                            <- NO SE PUDO PREGUNTAR
72:  if (data.paso === null) { ... }               <- el servidor dice que NO HAY NADA
```

**Y medido con la red cortada, la pantalla dice:**

> **«No se ha podido preguntar al servidor. Esto **no** quiere decir que la receta no este empezada.»**

**Que es lo contrario de lo que decia antes** -- *«Esta receta no esta empezada»* --, **y es la verdad.** *`tsc` da 0.*

**Y esa rama no afirma nada**: *dice **que no pudo preguntar**, y **avisa explicitamente de que eso no significa
que no haya nada*** -- *que es la unica forma de no convertir un «no se sabe» en un «no hay».*

### Y la causa 1: **sigue, y despues de reiniciar Vite**

```
¿Vite sirve ya `acaba_en`?:  False
CON conexion:                quedan None s       <-- *el arreglo del §7 no llega al navegador*
```

**Se reinicio Vite, y la comprobacion sigue dando `False`.** *Asi que **el diagnostico del §8 -- «Vite sirve un
modulo viejo» -- no basta**: reiniciarlo **no lo arregla**.*

**Y hay dos lecturas, y no se sabe cual es** -- *que es exactamente lo que hay que decir cuando no se sabe:*

1. **La comprobacion esta mal.** *`fetch('/src/api/cocina.ts')` **puede no devolver el fuente tal cual**: Vite lo
   **transforma** al servirlo, y ademas **puede contestar desde su cache de `node_modules/.vite`**.*
   *Entonces `acaba_en` **estaria en el fuente y no en lo que esa peticion devuelve**, y la conclusion del §8
   seria **falsa**.*
2. **O Vite de verdad sirve otra cosa**, y *reiniciarlo no basta porque **la cache esta en disco**.*
   *Entonces el arreglo del §7 **esta escrito y no se usa**, que es peor.*

### Y lo siguiente, exacto, para no dejarlo en «no se sabe» arbitrario

**Mirar el fuente que el navegador tiene cargado, no pedirlo otra vez.** *En vez de `fetch`, **leer lo que el
propio navegador ya ejecuto** -- *por ejemplo, buscando `acaba_en` en el contenido de los scripts que
`performance.getEntriesByType('resource')` nombra, o **abriendo el fichero en la pestana de fuentes***.*
**Y la prueba que decide**: *si la pantalla, **con conexion**, vuelve a decir **«quedan 30 min 0 s»**, entonces el
modulo **si** llego y **lo que estaba mal era la comprobacion**.*

**Y esa prueba esta a una linea**: *el ensayo del §7 ya la hizo **una vez** y dio «quedan 29 min 21 s».*

### Y el balance de las dos causas, que conviene separar

| | |
|---|---|
| **causa 2** (*«no pude preguntar» ≠ «no hay nada»*) | **arreglada, y verificada con la red cortada** |
| **causa 1** (*el modulo que llega*) | **sin resolver, y el diagnostico del §8 no basta** |

**Y la 2 era la que importaba**: *es **codigo de la pantalla**, se ve **sin cortar nada**, y **desde luego no
depende de Vite**.*


---

## 10. La prueba que decidia la causa 1: **el modulo SI llega** -- *y aparece otra cosa, mas simple*

*(Ronda 188.)*

### Lo que se midio

```
LO QUE LA PANTALLA DICE, con conexion:
    ... Gasto y ahorro | Cuenta y preferencias | Aprender | COMPRA | Compra
    CARGANDO LA COCINA...                       <-- ni «quedan», ni nada: se queda ahi

ficheros de cocina que el navegador carga:
    /src/estado/cocina.ts, /src/api/cocina.ts
```

### Y la conclusion de las dos causas del §8/§9 **es falsa**

**El §9 decia que «el modulo no llega», y que la comprobacion `fetch('/src/api/cocina.ts')` daba `False` porque
Vite servia otra cosa.**

**Y no**: *el navegador **carga** `/src/api/cocina.ts`* -- *esta en la lista de lo que pide* --, **y la pantalla se
queda en `«Cargando la cocina...»`, que es una frase de MI componente.** *O sea que **mi componente si esta
montado y ejecutandose**.*

> **Asi que la comprobacion del §8 estaba mal, como sospechaba la primera de las dos lecturas**: *`fetch` de un
> `.ts` en Vite **no devuelve el fuente**, y de ahi el `False`.* **La segunda lectura -- «Vite sirve otra cosa» --
> era la equivocada**, y **estuve a punto de tratarla como la buena.**

### Y lo que hay de verdad: **la pantalla se queda cargando, y eso es mas simple**

`isLoading` **no termina nunca**. *Con la consulta a `/api/cocina/7?version=2` contestando `200`.*

**Y el camino probable esta en lo que SI se cargo: `/src/estado/cocina.ts`.**

**Ese fichero **existe desde antes** y es de **otra cosa**: *nutrientes, `validarReceta`, `Receta`, `Ingrediente`
-- **la pantalla de calorias**, no el modo cocina.* **Lo usan `logica/chispa.ts`, `logica/costeReceta.ts` y
`paginas/Cocina.tsx`.** *Y `App.tsx:13` lo dice: «**servidas por la misma pantalla de cocina con un `modo`**».*

**Y `paginas/Cocina.tsx` (101 lineas) **no tiene** ni `paso`, ni `temporizador`, ni `usados`, ni `reanudar`:
**es la pantalla de calorias**, y **`CocinaModo` no la duplica**.** *Eso se comprobo antes de sacar conclusiones,
y **la alarma inicial era falsa**.*

### Y lo que queda, exacto

**`isLoading` eterno con un `200` en la consulta.** *Las causas plausibles, y **cualquiera se descarta mirando**:
(a) el `refetchInterval` de 15 s mantiene la consulta en `fetching` y **React Query v5 puede seguir dando
`isLoading` mientras no haya habido **ningun** `data`**; (b) `useCocina` se llama con `id`/`v` que **no son
numeros** -- `Number(undefined)` es `NaN` -- y **la consulta se queda sin resolver**; (c) **el
`CocinaProvider`** que envuelve todo en `App.tsx:139` **intercepta la ruta**.*

**Y la (b) es la mas probable y la mas tonta**: *la ruta es `/compra/cocina/7/2` y los parametros se leen con
`useParams()`; **si el `Route` que gana no es el mio**, `recetaId` seria `undefined`.* **Se comprueba en una
linea: imprimir `id` y `v` en la pantalla.**


---

## 11. La causa de verdad: **el endpoint devuelve `500`, y `isLoading` lo tapa**

*(Ronda 189. **Una linea, y estaba ahi desde el principio.**)*

### Lo que se midio

**Se capturaron **todas** las llamadas a `/api/cocina` -- y el fallo del §10 fue **filtrar por `.ts`** y no verlas:**

```
llamadas a /api/cocina: [(200, '/src/api/cocina.ts'), (500, '/api/cocina/7?version=2')]
¿dice «Cargando»?: True
errores JS: []
```

**El endpoint contesta `500`.** *Y la pantalla dice **«Cargando la cocina...»** para siempre.*

### Y por que `isLoading` no se apaga nunca, que es lo que hay que entender

**`useCocina` tiene `refetchInterval: 15000`.** *Y React Query da `isLoading` mientras **la consulta no haya tenido
nunca `data`** y **siga intentando**.* **Con un `500` que se repite cada quince segundos, `isLoading` es cierto
casi todo el tiempo** -- *y el `error` que si existe **no se llega a mirar**, porque `if (isLoading)` va antes.*

> **Asi que la pantalla no dice «no se pudo preguntar»: dice «Cargando».** *Que es **la misma familia de fallo que
> la causa 2 del §9** -- *una cosa es lo que pasa y otra lo que se enseña* --, **y esta vez el culpable es el
> `refetchInterval`**: *convierte un error permanente en **una espera permanente**.*

### Y la causa del `500` es lo siguiente, y esta acotada

**El endpoint es `/api/cocina/{receta_id}?version=N`**, y **el `500` es nuestro**. *Los sitios donde puede romper,
en orden de probabilidad:*

1. **`_de_la_sesion`** -- *la consulta a la tabla `cocina`.* **Si la tabla no esta creada en la base que usa el
   proceso, o el `usuario_id` no es un `UUID` valido, revienta.** *La migracion `018` **se aplico** en la base de
   pruebas (`postgresql://...5434`), y **el proceso de la API usa esa misma** -- *pero eso hay que verlo, no
   suponerlo.*
2. **`datetime.fromisoformat(t["empezo_en"])`** en `_cocina_de` -- *si `psycopg` devuelve el `jsonb` ya como
   `dict`/`list` de Python, o con las claves en otro tipo, el `fromisoformat` puede recibir algo que no es `str`.*
3. **`version` no se usa en la consulta** -- *se recibe y **no se filtra por el**, asi que no puede ser la causa.*

**Y el `500` no se ha leido.** *FastAPI lo habra escrito en el log de la API, **y ese log esta en el sandbox**:
`data/debug/api5.log`.* **Una linea.**

### Y la leccion de estas tres rondas, que conviene juntar

| ronda | lo que crei | lo que era |
|---|---|---|
| §8 | «Vite sirve un modulo viejo» | *una comprobacion mia con `fetch` que no devuelve el fuente* |
| §10 | «el modulo no llega» | *mi filtro `.ts` escondia la llamada al API* |
| §11 | -- | **un `500` de mi propio endpoint** |

**Las tres veces el fallo estaba **a una linea de distancia** -- un log, una peticion, un filtro que sobraba --, y
las tres veces **construi una teoria antes de mirar lo que ya estaba delante**.** *Y la tercera es la que
importa: **el `500` llevaba ahi desde el primer ensayo**, y lo que lo tapaba era **mi propio filtro** y **un
`isLoading` que no se apaga**.*


---

## 12. El log dice `200` -- **y mi captura decia `500`**. *Una de las dos miente, y no se cual*

*(Ronda 190.)*

### Lo que se midio

**El log del proceso de la API (`data/debug/api5.log`, 2 473 bytes) acaba asi:**

```
INFO:  127.0.0.1:3442 - "GET /api/cocina/7?version=2 HTTP/1.1"  200 OK
INFO:  127.0.0.1:3441 - "GET /api/yo HTTP/1.1"                  200 OK
INFO:  127.0.0.1:3443 - "GET /api/yo HTTP/1.1"                  200 OK
INFO:  127.0.0.1:3444 - "GET /api/listas HTTP/1.1"              200 OK
```

**Y la captura del navegador del §11 decia `(500, '/api/cocina/7?version=2')`.**

**El mismo endpoint, la misma ronda, dos respuestas distintas.** *Y **no se cual de las dos es la buena**, asi que
se dice asi.*

### Y las dos lecturas, con lo que las distingue

1. **El `500` fue **transitorio**.** *El log **si** tiene un `200 OK` del mismo camino, y **es el unico que hay**:
   *no hay ningun `500` en el log entero.* **Y las peticiones del log son de la ronda 189.** *Asi que **si el
   navegador hubiera recibido un `500`, estaria escrito** -- *a menos que el `500` lo generase **otra cosa** y no
   el proceso (un proxy, o el propio Vite).*

2. **O el `500` **no era de esa peticion**.** *`pag.on("response", ...)` **captura todas las respuestas**, y yo
   filtre por `"/api/cocina" in q.url`.* *Si **algo** contesto `500` con esa URL -- *por ejemplo **Vite**, que
   tambien proxya `/api`* --, **la captura lo recogio y el log no**, porque **el log es de uvicorn y ese `500` no
   paso por ahi**.*

**Y la segunda lectura encaja mejor con todo**: *el `500` **no esta en el log de la API**, y **la pantalla si
recibio un 500**.* **Lo que significa que el que contesta `500` en esa ruta no es uvicorn.**

### Y por que esto importa mas que el `500` en si

**El proyecto tiene una pieza delante de la API.** *`F03-publicacion.md` §34 ya habla de **Caddy** («un 502 de
Caddy delante de una API caida no es JSON», dice el propio codigo en `api/favoritos.ts`).* **Y `vite.config` puede
tener un proxy para `/api`.** *Asi que **hay una tercera capa** que **no se ha mirado en ningun momento de estas
seis rondas** -- *y es exactamente donde vivio el §4 (un `404` que no era del router) y donde puede vivir esto.*

### Y lo siguiente, exacto

**Mirar si Vite proxya `/api`**, y **a donde**. *Una linea en `vite.config.ts`.* **Si hay proxy, el `500` es suyo
y el `200` de uvicorn es la verdad** -- *y entonces **el problema de la pantalla es otro**, y `isLoading` tampoco
se explica.*

### Y un tropiezo que se repite, y ya van cuatro

**Al escribir este script se me olvido `CESTA_POSTGRES`, otra vez** -- *el proceso se conecto al `5432` y murio con
`password authentication failed`.* **Es la cuarta vez en esta sesion** (*rondas 175, 176, 185 y 190*), y **siempre
igual: se escribe el script, se lanza, y falla por la variable que falta** -- *que es una linea que se puede poner
siempre.* **Queda dicho como lo que es: un descuido repetido, no un hallazgo.**


---

## 13. La capa que no se habia mirado: **Vite proxya `/api`, y por defecto al `8000`**

*(Ronda 191. **Esto es lo que el §12 dejo apuntado: «una linea en `vite.config.ts`».**)*

### Lo que dice el fichero

```ts
// El destino del proxy de desarrollo. Por defecto, el puerto donde escucha
// uvicorn si se levanta a mano. ...
//
//     $env:CESTA_API='http://127.0.0.1:8080'; npm run dev
//
// En produccion nada de esto se usa: es Caddy quien manda /api al backend.
const destinoApi = process.env.CESTA_API ?? 'http://127.0.0.1:8000'
...
server: {
  port: 5173,
  proxy: { '/api': { target: destinoApi, changeOrigin: true } },
},
```

### Y lo que eso significa, que son tres cosas

**1. Hay **cuatro** capas, y en estas siete rondas se han mirado tres.** *El navegador, **Vite**, la API... y
**entre Vite y la API hay un proxy que decide a donde va cada `/api/...`*** -- *y **a donde va depende de una
variable de entorno del proceso de Vite**, no del codigo.*

**2. Y el defecto **no** es `8102`: es `8000`.** *Asi que **si `CESTA_API` no llega al proceso de Vite, todas las
peticiones de la aplicacion van al puerto `8000`** -- *que en este sandbox **no tiene nada**, o **tiene otra
cosa***.* **Y eso produce fallos que parecen de la pantalla y son de la fontaneria.**

**3. Y esto ya paso, escrito, en esta misma fase.** *`F03-publicacion.md` §34 habla de **Caddy** («un 502 de Caddy
delante de una API caida no es JSON», dice `api/favoritos.ts`).* **La leccion estaba escrita y no se aplico:** *se
miro el navegador, se miro uvicorn, y **no se miro la pieza de en medio**.*

### Y lo que **no** cuadra todavia, dicho sin adornos

**El 502/500 del navegador y el `200 OK` del log siguen sin explicarse juntos.** *Y con el proxy delante, **hay una
tercera explicacion que no se habia considerado**:*

- **`ctx.request` (Playwright) y `pag.on('response')` pueden estar viendo cosas distintas.** *`ctx.request` es un
  cliente HTTP aparte -- **tambien pasa por `:5173`, tambien por el proxy** --, y **sus peticiones SI aparecen en el
  log con `200`**. *Y la de la **pagina** puede ir por otro camino.*
- **O el `500` es de una peticion que no es la que yo creia**, y **el filtro `"/api/cocina" in q.url` volvio a
  juntar cosas distintas** -- *que es **el mismo error del §10**, cometido **dos rondas despues de escribirlo**.*

**Y la comprobacion que lo decide, y que es la que habia que hacer desde el principio**: **abrir `/api/cocina/7?version=2`
en el navegador, a mano, y leer `data/debug/api5.log` en el mismo segundo.** *Si aparece la linea en el log, la
peticion llego; si no, se quedo en Vite.*

### Y lo que hay que anotar del ensayo, porque es lo que mas ha costado

**Siete rondas (§6 a §13) para un fallo que estaba a una capa de distancia**, *y en cada una se construyo una
teoria -- Vite viejo, el modulo que no llega, el `500`, el `200` -- **antes de mirar la pieza que faltaba**.* *Y la
pieza que faltaba **estaba en un fichero de once lineas que nadie abrio**: `vite.config.ts`.*


---

## 14. Y se cierra: **el `500` es de Vite, y la peticion no llega a uvicorn**

*(Ronda 192. **La comprobacion que el §13 dejo apuntada, y da una respuesta limpia.**)*

### Lo que se midio

**Se anoto el tamano del log, se hizo la peticion **desde dentro de la pagina**, y se volvio a medir:**

```
log antes:        2473 bytes
DESDE LA PAGINA:  status 500, y el cuerpo VACIO
log despues:      2473 bytes        <-- NO CRECIO: la peticion NO LLEGO a uvicorn
```

**Dos cosas, y las dos concluyentes:**

1. **El `500` viene con **el cuerpo vacio**.** *Un error de FastAPI **siempre trae `{"detail": ...}`** -- *lo dice el
   propio `api/cliente.ts`: «un 502 de Caddy delante de una API caida **no es JSON**»*. **Cuerpo vacio = no lo
   genero la API.***
2. **Y el log **no crecio ni un byte**.** *Asi que **la peticion no llego a uvicorn** -- *el log lo habria escrito,
   porque **escribe todas**.*

> **Asi que el `500` lo genera **Vite**, al no poder alcanzar su destino.** *Y el destino por defecto es
> **`http://127.0.0.1:8000`**, que en este sandbox **no tiene la API** -- *esta en el `8102`.*

### Y lo que **no** cuadra, y hay que decirlo

**El log **tampoco** crecio con las otras peticiones de esta misma corrida.** *Y sin embargo **la sesion se creo** y
las llamadas **parecieron funcionar** -- *o eso crei.* **Asi que hay dos posibilidades, y **no se sabe cual**:*

- **O esta corrida entera fue contra el `8000`** -- *y lo que "funcionaba" venia de **otra cosa** en ese puerto, o
  de **cookies de corridas anteriores**.*
- **O `data/debug/api5.log` **no es el log del proceso que escucha ahora**.** *Se han reiniciado **cinco** procesos
  de API en estas rondas (`api.log`, `api2`, `api3`, `api4`, `api5`), y **yo escribi en `api5.log` al reiniciar en
  la ronda 185** -- *pero **el proceso de la ronda 185 se reinicio otra vez**, y **el log de ese esta en otro
  sitio**.*

### Y la conclusion que **si** se puede afirmar, que es bastante

**El `500` de la pantalla **no es de la API**.** *Cuerpo vacio y log quieto: **lo genera la capa de delante**, que es
**Vite**, y **porque su destino no contesta**.* **Y el destino depende de `CESTA_API`, una variable del proceso de
Vite que **no se comprobo al arrancarlo**.*

**Y eso ya estaba escrito en esta fase.** *`F03-publicacion.md` §34 -- la leccion de Caddy -- **y el propio
`vite.config.ts`, que lo dice en un comentario de cinco lineas**.* **Siete rondas para llegar a un fichero que
**explicaba el fallo en su comentario**, y **el comentario decia exactamente lo que habia que hacer**: *«para
desarrollar contra la plataforma ya levantada hay que apuntar al puerto donde este»*.

### Y lo que queda para la continuacion, exacto

**1. Averiguar a donde apunta **el Vite que esta en pie ahora**: *`Get-Process` sobre el pid del `5173` y mirar su
entorno, o **reiniciarlo con `CESTA_API` puesto y comprobarlo con la misma peticion**.* *La segunda es mas rapida y
**no deja duda**.*

**2. Y despues, la pregunta de verdad:** ***por que la pantalla no dice «no se pudo preguntar» en vez de
«Cargando»***. *Eso **no depende de Vite** -- *es el `isLoading` del §11* --, y **es lo unico de toda esta cadena que
es codigo mio y esta mal**.


---

## 15. **Y era la fontaneria del ensayo.** `CESTA_API` no estaba puesta al arrancar Vite

*(Ronda 193. **Esto cierra la cadena entera de §6 a §14, y la cierra en contra de mis sospechas.**)*

### Lo que se midio, y es limpio

```
8000:  libre                    <-- NADIE ESCUCHA AHI: el proxy de Vite iba al VACIO
8102:  ESCUCHA (pid 34092)
5173:  ESCUCHA, arrancado CON CESTA_API=http://127.0.0.1:8102

sesion: 200
DESDE LA PAGINA: status 200
cuerpo: {"paso":0,"paso_actual":null,"usados":[],"hechos":0,
         "temporizadores":[{"paso":0,"minutos":30,
                            "acaba_en":"2026-10-12T11:17:34.722697+00:00",
                            "queda_segundos":1792,"terminado":false}]}
```

**Dos cosas, y las dos importan:**

1. **El `500` era **exactamente** lo que el §14 concluyo**: *Vite proxya `/api` a `CESTA_API`, **que por defecto es
   el `8000`** -- y en el `8000` **no hay nadie**.* **Con `CESTA_API` puesta, la misma peticion devuelve `200`.**
   *Confirmado, y **sin ninguna duda**: el log crecio y el cuerpo trae un JSON.*
2. **Y `acaba_en` **si** estaba llegando.** *El arreglo del §7 **funciona**: *el servidor devuelve
   **`"acaba_en": "2026-10-12T11:17:34.722697+00:00"`**, que es el instante y no el numero.*

### Y todo lo que se concluyo entre el §6 y el §14, revisado

| ronda | lo que se concluyo | **lo que era** |
|---|---|---|
| §8 | «Vite sirve un modulo viejo» | *la comprobacion con `fetch` no devuelve el fuente* |
| §10 | «el modulo no llega» | *mi filtro `.ts` escondia la llamada* |
| §11 | «el endpoint devuelve `500`» | **cierto, pero el `500` no era de la API** |
| §12 | «el log dice `200` y mi captura `500`» | **las dos eran ciertas: eran dos destinos distintos** |
| §13 | «hay una capa que no se ha mirado» | **correcto, y era la causa** |
| §14 | «el `500` es de Vite» | **correcto** |
| **§15** | -- | **Vite iba al `8000` porque `CESTA_API` no estaba puesta** |

**Y la conclusion que importa, en una linea: NADA DE ESTO ERA DEL PRODUCTO.** *Todas las sospechas sobre el codigo
-- el modulo, el `isLoading`, el endpoint -- **eran sobre un ensayo que no estaba midiendo lo que creia**.*

### Y la unica cosa que **si** era del producto, y sigue en pie

**El `isLoading` que no se apaga.** *El §11 lo demostro **con la API contestando**: *cinco rondas despues sigue sin
arreglarse, y **es codigo mio**.* **Con la fontaneria bien, ahora se puede ver si la pantalla pinta el
temporizador** -- *y si no lo pinta, **la causa sera esa y no otra**.*

### Y la leccion de metodo, que es la mas cara de toda la fase

**Siete rondas construyendo teorias sobre el producto** -- *Vite viejo, el modulo que no llega, el endpoint roto* --
**cuando el fallo estaba en **como se habia arrancado el ensayo**.**

> **Y el aviso estaba en **tres sitios escritos**: el comentario de cinco lineas de `vite.config.ts`, el §34 de
> `F03-publicacion.md` (*la leccion de Caddy*), y **el propio §14, que lo dijo y no lo comprobo hasta la ronda
> siguiente**.*

**Lo que costo no fue averiguarlo**: *fue **no mirar la pieza de en medio** -- *y **la pieza de en medio estaba
documentada en el fichero que la definia**.*


---

## 16. Con la fontaneria bien, **el defecto del producto queda aislado**: `isPending` no resuelve y no hay error

*(Ronda 194.)*

### Lo que se midio, con `CESTA_API` puesta y la API contestando

```
CON conexion, la pantalla dice:
    ... COMPRA | Compra
    «CARGANDO LA COCINA...»
-> quedan None s
SIN conexion t=0:   quedan None s
SIN conexion t=12:  quedan None s
```

**Asi que el §15 cerro la fontaneria, **y la pantalla sigue igual**.** *El defecto es **del producto**, y **esta
aislado**: *la API contesta `200` -- *comprobado con `fetch` desde la propia pagina, en el §15* --, **y la pantalla
no sale de `isLoading`**.*

### Y se aplico el arreglo del §11 -- *y **no basta***

**Se cambio `if (isLoading)` por `if (isLoading && !error)`**, con su razon escrita: *«`isLoading` solo mientras NO
haya error»*. *`tsc` da 0.*

**Y la pantalla sigue diciendo «Cargando la cocina...».** *Lo que significa, **y ahora se sabe con precision**:
**`error` es falsy Y `isPending` es verdadero, a la vez, indefinidamente.*** *O sea: **la consulta nunca ha tenido
exito y nunca ha fallado** -- *se queda intentando.*

### Y lo que eso deja como unico sospechoso, que es el `refetchInterval`

**`useCocina` tiene `refetchInterval: 15000`.** *Es lo unico de esa consulta que no es corriente, **y encaja con
«nunca resuelve»**: *React Query da `isPending` mientras no haya `data`, y **con un intervalo que la vuelve a
disparar, el estado observable puede quedarse en `pending` sin llegar nunca a `success` ni a `error`*** -- *sobre
todo **si la primera promesa no se resuelve como React Query espera**.*

**Y hay algo mas simple que encaja igual de bien, y hay que descartarlo primero**: ***que Vite siga sirviendo la
version anterior del componente***. *La frase «Cargando la cocina...» **existe en las dos versiones**, asi que
**verla no prueba que el cambio este**. *Y esto ya paso en el §4 y en el §8.*

### Y el siguiente paso, exacto, y son dos comprobaciones de una linea

**1. ¿Que version del componente sirve Vite?** *No con `fetch` -- **que no devuelve el fuente, §10** --, **sino
buscando `isLoading && !error` en el bundle que el navegador ya tiene cargado** (por ejemplo, imprimiendo
`performance.getEntriesByType('resource')` y **abriendo el fichero en la pestana de fuentes**, o **un `console.log`
del propio componente**).

**2. Y si el componente es el de ahora, `refetchInterval` es el sospechoso numero uno.** *La prueba es quitarlo:*
**sin intervalo, la consulta hace **un** intento y **tiene que resolverse** -- *en `success` o en `error`, pero
**resolverse**.*

**Y ninguna de las dos es una teoria**: *son **dos cambios de una linea** y **una lectura** cada uno.*

### Y una nota sobre el arreglo del §11, que **si** vale aunque no baste

**`if (isLoading && !error)` es correcto y se queda.** *No arregla este caso -- *porque **aqui no hay error*** --,
pero **si arregla el caso en que la consulta falla de verdad**, que es el que el §9 encontro con la red cortada.*
*Un arreglo que no basta **no es un arreglo que sobra**.*
