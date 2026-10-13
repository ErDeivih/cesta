# B03 · **La captura acotada, hecha.** Y Lidl publica precios de alimentacion, medido

*(13 de octubre de 2026. **El paso que el propio colector pedia antes de entrar en las 06:00.**)*

## 0. Y antes, dos cosas que habia que mirar

**El runlock, libre.** *La tarea `Cesta diaria` estaba en `Ready`, no en `Running`, y el lock de
`core.runlock.ejecucion_exclusiva` se pudo tomar.* **Asi que no habia otra ejecucion a la que estorbar** --
*que era la razon por la que la captura no se habia pedido antes.*

**Y la ingesta termino lo que faltaba**: *el bronze de `carrefour` es de hoy a las 12:29 y el de `alcampo` de
hoy a las 12:44.* **Los dos, que llevaban desde el 11.** *Lidl es ahora la unica fuente atrasada.*

> *Y un error mio, el decimonoveno*: **comprobe el runlock con `runlock.solo_uno()`, que no existe.**
> *`AttributeError: module 'core.runlock' has no attribute 'solo_uno'`.* **La funcion se llama
> `ejecucion_exclusiva`.** *Me invente el nombre, otra vez, en vez de mirarlo.*

## 1. La captura: **dos peticiones, y la primera es `robots.txt`**

```
$ uv run python sondear_lidl.py --web
```

*Y respondio:*

```json
{
  "fuente": "https://www.lidl.es/c/ofertas-semanales/a10089449",
  "cobertura": "ofertas_semanales_parcial",
  "fichas_variantes": 79,
  "productos_padre": 74,
  "con_precios_regionales": 79,
  "ejemplos": [
    { "id": 11150785, "nombre": "Naranja mesa",              "url": "/p/naranja-mesa/p11150785" },
    { "id": 11151052, "nombre": "QUALITE SUISSE Pepino granel", "url": "/p/qualite-suisse-pepino-granel/p11151052" },
    { "id": 11150771, "nombre": "Pomelo",                    "url": "/p/pomelo/p11150771" }
  ],
  "aviso": "No integrado en ingesta; no certifica stock, identidad ni precio vigente."
}
```

## 2. Y los tres numeros, leidos con cuidado

### `fichas_variantes: 79` y `productos_padre: 74`

*El 6 de octubre fueron **76 y 70**.* **Asi que la campana ha cambiado** -- *que es lo que se espera de
ofertas semanales, y **la razon por la que una captura de hace seis dias no vale como el estado de hoy***:
*se habria presentado como actual una campana que ya no lo es.*

### `con_precios_regionales: 79` -- **las 79, todas**

> **Y esto es lo que zanja la discusion de la ronda 18.** *La conclusion de septiembre decia que «lidl.es no
> publica precios de alimentacion».* **Hay 79 fichas, las 79 con precio regional, y las tres primeras son
> naranja, pepino y pomelo.**

**No es que Lidl publique «algo»: publica precios regionales de alimentacion, y los publica en las 79
fichas de su campana.** *Lo que **no** publica es su catalogo total* -- *y por eso `cobertura` dice
`ofertas_semanales_parcial`, que es la palabra exacta.*

### Y los nombres de las tres primeras

*Naranja de mesa, pepino al granel y pomelo.* **Alimentacion, perecedero, y a granel.** *No es bricolaje ni
drogueria: es la compra de la semana.*

## 3. Y `regional: null` en los tres ejemplos, que **no** es un fallo

**Los ejemplos traen `regional: null` porque la captura se pidio SIN `--region`.** *El piloto solo resuelve la
region si se le pide una*:

```python
"regional": precios_region(p, a.region) if a.region else None
```

**Asi que `null` quiere decir «no se pregunto», no «no tiene precio regional».** *Y la prueba de que si lo
tiene es el contador de arriba: `con_precios_regionales: 79`.* **Que es exactamente la distincion de toda esta
fase** -- *un `null` que dice «no se miro» y un cero que diria «no hay».*

**Y las regiones estan dentro del dato** (`regionsV2`), *asi que **el identificador de region se puede
observar** sin preguntarle nada a nadie.* **Lo unico que habria que preguntar es cual se quiere**, y solo si
se quiere una concreta.

## 4. Lo que esto deja hecho, y lo que falta

  - **LA CAPTURA ACOTADA: HECHA.** *Una pagina, dos peticiones contando `robots.txt`, y `robots.txt` primero.*
  - **Y Lidl publica precios de alimentacion: MEDIDO**, *no citado.*

**Lo que sigue faltando de B03:**

  - **la captura al bronze** *por el colector* (`collectors/lidl.py`), no por el piloto -- *el piloto imprime,
    el colector escribe.*
  - **bronze -> silver -> gold -> API -> UI** de esa captura.
  - **region/club/fechas/nutricion/ausencias probadas**, *que es lo que la aceptacion pide.*
  - **y anadirlo a la tarea de las 06:00**, *que es la segunda mitad del punto 189 de G09.*

## 5. Y lo que no se ha hecho, y por que

**No se ha guardado el HTML de esta captura.** *El piloto lo lee en memoria y no lo escribe* -- *su docstring
dice «sin publicar bronze», y cumplirlo es lo correcto.* **Guardarlo seria empezar a escribir bronze por un
camino que no es el del colector**, *y el colector es el que tiene que escribir.*

**Asi que esta captura es una medida, no una ingesta.** *Y se dice, para que nadie la cuente como bronze.*
