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
