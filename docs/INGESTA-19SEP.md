# La ingesta del 19 de septiembre: Cloudflare bloquea desde la peticion numero 1

Primera ejecucion con los arreglos del 18 puestos. Se reviso en caliente y se
cerro al terminar. **Termino con las cinco cadenas: `=== todo correcto ===`.**

    aldi        2.183 productos   0 errores      72 s
    mercadona   4.327 productos   0 errores      97 s
    dia         5.837 productos   0 errores   1.092 s
    alcampo    23.794 productos   0 errores   4.434 s
    carrefour  16.547 productos   6 errores   7.473 s

    catalogo    52.688 productos        historico  645.975 filas, 14 dias
    grupos       6.429 comparables

---

## 1. Lo que funciono: **Frescos ha vuelto**

Es el arreglo que mas importaba y se ve en una tabla:

| rama de Alcampo | 17 sep | **18 sep** | 19 sep |
|---|---:|---:|---:|
| **Frescos** | 2.646 | **91** | **2.719** |
| Alimentacion | 3.647 | 3.433 | 3.442 |
| Perfumeria | 2.981 | 3.040 | 3.029 |
| Bebidas | 2.394 | 2.419 | 2.422 |

Fruta, verdura, carne y pescado, de vuelta. Y el total: **23.794 productos**,
frente a los 20.571 del dia que salio roto. El propio colector lo dijo:

    [DERIVA] alcampo: 23794 filas hoy vs 20571 la ultima vez

El recorrido tambien lo confirma: la cola de categorias pendientes se mantuvo
alta hasta el final (410 categorias vistas, 0 en cola, 28.621 productos brutos),
en vez de vaciarse sola a mitad como el 18.

**Y el rescate de Carrefour funciono: 381 de 387 categorias recuperadas.** Las 6
que quedaron no son bloqueos: son dos 500, un 520 y un `__INITIAL_STATE__` que no
cierra. Con 16.547 productos, mas que los 16.416 del 17.

---

## 2. Lo que no: Carrefour bloqueado de arriba abajo

```
error HTTP en 1/653 cat20329: HTTP 403 ...
error HTTP en 2/653 cat10650814: HTTP 403 ...
...
error HTTP en 426/653 cat20161: HTTP 403 al pedir https://www.carrefour.es/
```

**Desde la peticion numero uno.** A los catorce minutos: **383 respuestas 403** y
2.563 productos unicos, contra los 16.416 de un dia normal. El bloqueo se levanto
sobre la categoria 465 y a partir de ahi la cosa fue bien: la pasada principal
acabo con 11.796 productos y el rescate subio a 16.547.

La linea que lo explica todo es la de la categoria 426: el 403 es a
`https://www.carrefour.es/` **a secas**, la portada. No es que una categoria
este cortada: estamos cortados nosotros.

Es distinto de lo del 18, cuando el bloqueo empezo pasada la categoria 300 y se
levanto solo a los veinte minutos. Hoy empezo antes de la primera peticion, o sea
que veniamos ya fichados del dia anterior.

---

## 3. El arreglo: enterarse una vez, no 653

Recorrer las 653 categorias en ese estado es **coleccionar 653 fallos
identicos**. No se recoge nada, se tarda media hora larga y —lo peor— cada
peticion de mas alarga el bloqueo. Y luego el bucle de rescate repite el paseo
tres veces mas: unas 2.600 peticiones para que nos digan 2.600 veces que no.

`collectors/carrefour.py` gana `UMBRAL_BLOQUEO_TOTAL = 25`:

```
  25 bloqueos seguidos: el bloqueo es total, no una categoria. Se deja de
  recorrer y las 628 que quedan pasan al rescate, que es quien sabe esperar.
```

El contador es de **403 seguidos** y se pone a cero en cuanto una categoria
responde bien, asi que una categoria rota suelta no para nada. Lo que para el
recorrido es el patron de "no nos hablan".

### Medido contra un Carrefour de mentira que bloquea de verdad

Con el servidor de pruebas configurado para rechazar **todas** las categorias
durante los primeros segundos y el umbral bajado a 5 (el catalogo de mentira solo
tiene 20 categorias):

```
  error HTTP en 1/20 ... 403
  ... (5 en total)
  5 bloqueos seguidos: el bloqueo es total ... las 15 que quedan pasan al rescate
  20 categorias quedaron sin recoger; se espera 4s y se reintentan (vuelta 1)
  rescatadas 20 de 20
  carrefour: 60 productos, 0 errores, 5s

  peticiones al servidor: 27 (403: 5)
```

**27 peticiones en total, 5 de ellas bloqueadas.** Sin el arreglo serian 20
bloqueadas en la primera pasada y otras tantas por vuelta.

### Es la otra mitad de la leccion del 18

El 18 se aprendio que **no hay que esperar en cada peticion** (45 s por categoria
bloqueada, 4 h 40 min en un dia malo). Hoy se aprende lo complementario:
**tampoco hay que enterarse 653 veces de lo mismo**. Quien espera es el bucle de
rescate, una vez por tanda; quien recorre, en cuanto ve que el muro es para todos,
se calla y le pasa el trabajo.

---

## 4. Lo que este arreglo NO resuelve

Si Cloudflare nos tiene fichados de un dia para otro, esperar doce minutos en
tres vueltas puede no bastar: el 18 el bloqueo duro veinte. El arreglo evita
gastar horas y peticiones, pero **no recupera el catalogo de un dia asi**.

La salida de verdad esta apuntada desde hace dias y sigue sin hacerse: **N13, el
buscador con API propia de Carrefour** (`/search-api/query/v1/search`). Hoy se
recorre por 653 direcciones de categoria, que es el patron que mas se parece a un
robot. Un buscador es otra puerta, y Alcampo ya usa ese mismo camino de rescate.

Mientras tanto, lo razonable cuando un dia sale asi:

    uv run python -m projects.cesta.run --solo carrefour

mas tarde, cuando el bloqueo se haya levantado. El crudo del dia esta en cache,
asi que solo se piden las que faltan.


---

## 5. Los tres controles nuevos: ni un aviso falso

El resumen del dia dice exactamente lo que tiene que decir, ni mas ni menos:

```
  historico: 645975 filas, 14 dias acumulados
  nota: 20559 filas de alcampo del 2026-09-18 vienen de una captura apartada
        (sin frescos); el bronze esta en data/debug/descartados
```

Una **nota**, no un aviso: la captura del 18 se aparto a proposito y el control lo
sabe porque el motivo va escrito en el nombre de la carpeta. Ningun
`TERMINO BIEN PERO NO HAY BRONZE`, ningun `AVISO ... sin rastro`, y el control de
cobertura no tuvo que negarse a escribir nada.

Tambien se nota el arreglo de las **ofertas de tarjeta**:

| cadena | con promocion | marcadas como de tarjeta |
|---|---:|---:|
| carrefour | 3.439 | **885** |
| alcampo | 3.126 | **575** |
| dia | 228 | 198 |
| aldi | 145 | 0 |

De 6.938 productos con texto de promocion, **1.658 son de tarjeta** y no bajan lo
que pagas en caja. Antes solo estaban marcadas las 198 de DIA: **1.460
promociones se anunciaban como rebajas y no lo eran**.

---

## 6. Lo que quedo apuntado del dia

- **N13, el buscador con API de Carrefour, sube a lo mas alto del backlog.** Dos
  dias seguidos de bloqueo, y hoy dos horas y cuatro minutos de ejecucion para
  una cadena. Recorrer 653 direcciones de categoria es el patron que mas se
  parece a un robot.
- Las cifras de la ejecucion viven ahora en **`docs/CIFRAS.md`**, que se reescribe
  entero cada dia. Los demas documentos conservan las suyas con la fecha en que se
  midieron: una cifra fechada no es una cifra caducada, es un registro, y
  cambiarla no la actualiza sino que la falsifica.
