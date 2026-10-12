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
