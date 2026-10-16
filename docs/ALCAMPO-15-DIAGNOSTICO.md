# El rechazo de Alcampo del 15, *diagnostico*

*15/10/2026, ronda 3 del objetivo de validacion. *Esto es el punto 6, **primera mitad**:
*la investigacion. *La correccion **no** se hace aqui, *y se dice por que al final.* *

*Fuentes: `data/runs.csv` *y `data/ejecuciones.log`, *** leidos, *no modificados.*** *

---

## 1. *El exito de ejecucion, *que es un dato y no una impresion*

`data/runs.csv`, *columnas `ts,fuente,filas,errores,segundos,ok`:*

```
2026-10-10  alcampo  *** 22632 *** filas  *** 0 *** errores  *** 6927.8 *** s  ok=*** True ***
2026-10-11  alcampo  *** 23128 *** filas  *** 0 *** errores  *** 5980.0 *** s  ok=*** True ***
2026-10-13  alcampo  *** 22828 *** filas  *** 0 *** errores  *** 6732.8 *** s  ok=*** True ***
2026-10-14  alcampo  *** 22905 *** filas  *** 0 *** errores  *** 9967.0 *** s  ok=*** True ***
2026-10-15  alcampo  *** 17076 *** filas  *** 1 *** error    *** 4787.5 *** s  ok=*** False ***
```

*** O sea ***: *el 15 hizo *** un 25% menos de filas *** *y tardo *** la mitad de tiempo***,
*con *** 1 error***, *y quedo marcado *** `ok=False`***. *La forma es de **ejecucion
abortada**, *no de catalogo que encoge.* *

## 2. *Lo que dice el log, *y que explica la forma*

```
*** `175 categorias iniciales, empezando por la *** 106 *** (donde se corto la ultima vez)` *** *
   *-- *** la ejecucion REANUDA, *no empieza de cero *** ✓✓✓
*** `el WAF ha saltado en 'Drogueria Ecologica y sostenible'` *** *-- *y se reintenta *
*** `el WAF ha saltado en 'Higiene gatos' (2/20)` *** *-- *reintento 2 de 20 *
*** `(el reto no se paso sin ventana: se ha abierto el navegador)` *** *
*** `sesion renovada (con_ventana)` *** ✓
*** *y ademas: *`termino 'yogures proteina' sin datos: HTTPStatusError: *** HTTP 405 ***` *
```

*** Y con eso se puede decir que el 15 se junta TRES cosas ***: *un **WAF** que exige
renovar sesion con ventana, *unos **reintentos** que consumen tiempo, *y **405** en
terminos de busqueda. *Y la ejecucion *** reanuda desde donde se corto***, *lo que
explica que haga menos filas **sin** que el catalogo haya encogido.*

---

## 3. *Y ahora la separacion que pide el punto 6, *que hoy no existe*

*** Son tres cosas distintas, *y mirar una sola enganya ***: *

| | *valor el 15* | *que significa* |
|---|---|---|
| *** Exito de ejecucion *** | *`ok=False`, *1 error* | *la ejecucion **no termino limpia*** |
| *** Frescura *** | *ver seccion 4* | *de cuando es **lo que se sirve*** |
| *** Cobertura *** | *17.076 *frente a ~22.900* | *lo recogido ese dia, *que **no es** lo publicado* |

*** Y el enganyo, *dicho claro ***: *si se mira solo «17.076 productos», *parece que la
cobertura **bajo**; *si se mira solo «`ok=False`», *parece que **no se recogio nada**.* *
*Y las dos lecturas son falsas: *se recogieron 17.076, *y **no se publicaron**, *
*que es **lo correcto** cuando la ejecucion falla.* *

## 4. *La frescura, *y aqui hay algo que NO cuadra*

```
*** `data/ultima_ejecucion.txt` *** = 2026-10-15 *** ✓
*** `data/runs.csv` *** escrito el 16/10 a las 09:15 *** ✓
*** `data/ejecuciones.log` *** escrito el 16/10 a las 09:24 *** ✓
*** `data/ejecucion_en_curso.txt` *** escrito el 16/10 a las 09:13 *** *
   *-- *** hay una ejecucion en curso *** ✓
*** PERO `data/publicado/stats.json` *** dice *** fecha: 2026-09-16 *** *
   *y esta escrito el *** 16/09 a las 12:06 ***, *y su historico *** acaba ahi *** ⚠️⚠️⚠️
```

*** Y aqui NO concluyo ***: *el propietario dice que **la publicacion servida es
`20261015-123403`**, *que es del **15 de octubre**.* *Y este fichero es del **16 de
septiembre**.* *** Son dos artefactos distintos ***, *y **todavia no se cual se sirve.*** *
*No lo doy por sabido: *es *** la pregunta abierta*** de este punto, *y la primera que
hay que cerrar antes de tocar nada.* *

## 5. *Y un dato que si es firme, *sobre la cobertura*

```
*** `data/cobertura/` *** contiene *** SOLO ficheros `lidl-*.json` *** *
   *(-- lidl-2026-10-13, *-14, *-15 y *-16 --)* ⚠️
*** -> *** no hay ningun fichero de cobertura de alcampo *** ✓
```

*** O sea que «la cobertura parcial de Lidl» esta registrada, *y la de Alcampo no.*** *
*Si el punto 6 pide **mantener explicita** la de Lidl, *hay que ver **donde se declara**
para que la de Alcampo **no quede implicita por omision.*** *

---

## 6. *Por que NO se corrige todavia*

*** El encargo dice «corregir la causa CON PRUEBAS» ***, *y **no tengo la causa**: *
*tengo **la forma** del fallo (WAF + reintentos + 405 + reanudacion), *y **el sintoma**
(`ok=False` con 1 error), *pero **no cual de los errores hizo fallar la ejecucion.*** *

*** Y hay una tentacion que NO se va a seguir ***: *subir el umbral de errores para que
`ok=True` con 1 error.* *Eso es *** relajar el control para publicar***, *que es
exactamente lo que el encargo prohibe.* *

*** Lo siguiente, *en orden ***: *encontrar **el error concreto** que marco `ok=False`
*(el log tiene el recuento, *pero falta **cual**)*, *y **resolver cual de los dos
artefactos** es el que se sirve.* *
