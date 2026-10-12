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
