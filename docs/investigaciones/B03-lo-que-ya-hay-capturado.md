# B03 · Lo que **ya hay capturado** de Lidl, medido

*(13 de octubre de 2026. **Cuarta medicion de B03, y la primera que no es leer un documento: mirar el
disco.**)*

## 1. Y hay mas de lo que cualquier documento decia

```
data/raw/fuente=lidl/fecha=2026-10-06/7a80df1fb521-f97171170bc5.json.gz     80,2 KB
data/raw/fuente=lidl/fecha=2026-10-07/09d33dc85ccf-1df4f05e0c65.json.gz     70,7 KB
data/raw/fuente=lidl/fecha=2026-10-07/0cef363c1f86-8cb5a0d1de06.json.gz     65,4 KB
data/raw/fuente=lidl/fecha=2026-10-07/1011c701b2a9-f3a8a3a574da.json.gz    116,8 KB
data/raw/fuente=lidl/fecha=2026-10-07/162601c2e1a0-4306d1040f29.json.gz       66 KB
data/raw/fuente=lidl/fecha=2026-10-07/1cf84cb5af4a-908259f7fb5f.json.gz     63,7 KB
```

**BRONZE DE LIDL EXISTE, de dos fechas.** *Y su registro de peticiones:*

```json
{ "peticiones": 40, "por_host": { "www.lidl.es": 40 }, "cache": 0,
  "evitadas": 0, "motivos": [], "fuente": "lidl" }
```

**40 peticiones a lidl.es el 7 de octubre, ninguna cacheada y ninguna evitada.** *Es el «contador visible» que
la aceptacion de B03 pide, y ya se escribe.*

### Y tambien hay cola de fichas

```
data/fichas-lidl/
data/peticiones/lidl-2026-10-06.json
data/peticiones/lidl-2026-10-07.json
```

**Asi que de Lidl hay: colector, descubrimiento, cola de fichas, parser, bronze de dos fechas y contador de
peticiones.** *Lo que NO hay es que corra en las 06:00 -- y eso es deliberado.*

## 2. Y la captura guardada que parecia la buena **no lo es**

*Habia un `data/lidl-ficha-ejemplo.html` de 438 KB, y parecia una captura de la pagina de ofertas.* **Se paso
por el piloto, sin red:**

```
$ uv run python sondear_lidl.py --html data/lidl-ficha-ejemplo.html
ValueError: HTML sin fichas Lidl: no equivale a catalogo vacio valido
```

**Y el piloto TENIA RAZON, y aqui esta la prueba:**

```
<title>PHILIPS Licuadora Viva Collection »HR1832/00« | Lidl</title>
lineas con data-grid-data: 0
```

> **No es la pagina de ofertas: es UNA PAGINA DE PRODUCTO.** *El nombre del fichero lo decia --
> `ficha-ejemplo` --, y aun asi lo primero que hice fue pasarsela al piloto esperando 76 fichas.*

**Y lo que importa no es el fallo, es lo que hizo el programa**: *no devolvio una lista vacia que pareciera
«Lidl no tiene ofertas hoy».* **Levanto una excepcion con un motivo escrito.**

> **«No confundir desafio con catalogo vacio» dejo de ser una regla del plan y paso a ser un hecho
> observado**: *con un fichero real, en un caso real, el programa se nego a mentir.* **Y el que se equivoco
> fui yo, que esperaba 76 fichas de una pagina de licuadoras.**

## 3. Lo que falta de B03, ahora con numeros

| | |
|---|---|
| colector con `robots.txt`, una pagina, EAN no inventado | **existe** (11,7 KB) |
| descubrimiento y cola de fichas | **existen** |
| parser y bronze | **existen**, con dos fechas |
| contador de peticiones | **existe** (40 el 7 de octubre) |
| en `CADENAS_QUE_SE_CAPTURAN` y en `ORDEN` | **si**, y `ORDEN` dice que es «la primera mitad del 189» |
| **en la tarea de las 06:00** | **NO, a proposito** |
| **una captura ACOTADA Y RECIENTE** | **NO: la ultima es del 7 de octubre, hace seis dias** |

> **Asi que lo que falta son los dos pasos que el colector dice, y ademas uno que ahora se ve**: *la captura
> acotada tiene que ser **de hoy**, no del 7.* **Una captura de hace seis dias no acredita que Lidl siga
> publicando lo mismo** -- *y presentarla como el estado de hoy seria exactamente lo que esta fase prohibe.*

## 4. Y lo que NO se ha hecho, y se dice

**No se ha pedido nada por red en esta ronda.** *Se intento usar la captura guardada, y no servia.* **Pedir
la pagina de ofertas es el paso siguiente, y tiene su forma**: *`--web`, una sola peticion despues de mirar
`robots.txt`, como el piloto ya sabe hacer.*

*Y no se ha hecho todavia porque **conviene mirarlo antes**: la tarea `Cesta diaria` lleva corriendo desde
las 10:59, y **abrir una captura nueva mientras otra ejecucion trabaja** es justo lo que el runlock esta para
evitar. *Se comprueba el runlock, y despues se pide.*
