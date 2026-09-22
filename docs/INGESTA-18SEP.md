# La ingesta del 18 de septiembre, y los tres agujeros que destapo

Revisada la manana del 18. La ejecucion nocturna dijo "4 de 5 cadenas" y en
realidad estaban mal **tres** cosas, dos de ellas invisibles desde el log.

---

## 1. Lo que dijo el log

```
2026-09-18  aldi        2.175   0 errores    78s   ok
2026-09-18  mercadona   4.322   0 errores   103s   ok
2026-09-18  dia         5.869   0 errores   802s   ok
2026-09-18  carrefour  11.613 376 errores  2271s   FALLO
2026-09-18  alcampo    20.571   0 errores  3770s   ok
```

Carrefour fallo y se supo. Alcampo "fue bien" y fue lo peor del dia.

---

## 2. GRAVE — Alcampo entrego un catalogo sin la seccion de frescos

20.571 productos en vez de 23.573, con **cero errores**, asi que se dio por
completo, se escribio el bronze, el pipeline lo proceso y el catalogo del dia
salio a la app.

Lo que faltaba:

| rama | 17 sep | 18 sep |
|---|---:|---:|
| **Frescos** | **2.646** | **91** |
| Alimentación | 3.647 | 3.433 |
| Perfumería | 2.981 | 3.040 |
| Bebidas | 2.394 | 2.419 |

Fruta, verdura, carne y pescado. Justo donde mas se notan las diferencias de
precio entre supermercados, y la mitad de la razon de ser de esta aplicacion.

En el crudo del dia hay 91 filas de Frescos frente a 3.835 el dia anterior, y 41
ficheros menos: **no es que se leyera mal, es que no se llego a pedir**. La causa
mas probable es que la categoria padre devolviera pocos productos y ninguna hija,
que el codigo interpreta como "categoria pequena" en vez de como "respuesta
degradada"; son indistinguibles desde dentro.

### Por que no lo vio ninguno de los tres controles que ya habia

Los tres miran el **total**:

    check_drift          imprime un aviso en el log y no decide nada
    MERMA_ACEPTABLE      solo se aplica si la ejecucion YA se dio por parcial
    errores == 0         no fallo nadie: simplemente no se pidio

Un total puede bajar un 13 % por mil razones normales. Lo que no es normal es que
una rama con 2.646 productos se quede en 91 mientras las demas siguen igual. **El
total lo esconde; la rama lo grita.**

### El arreglo: `core/cobertura.py`

Compara la captura de hoy con el ultimo bronze bueno **rama a rama**. Si una rama
que tenia 100 productos o mas pierde mas de la mitad, la captura no se guarda,
tenga los errores que tenga y sea cual sea el total:

```
  faltan ramas enteras respecto a la ultima captura buena:
      Frescos: 2646 -> 91 (97% menos)
  eso no es un catalogo mas pequeno, es un catalogo con agujeros.
  Se conserva el anterior y manana se vuelve a intentar.
```

Es la unica regla del colector que dice "no" sin mirar el tamano total, y es a
proposito: cuando falta una rama entera **sabemos** que se ha perdido, no lo
estimamos. Si Frescos hubiera tenido mil productos en vez de 2.646, el total se
habria quedado por encima del 90 % y la regla de la merma habria dado el visto
bueno a un catalogo sin pescaderia.

Esta puesto en las cinco cadenas, no solo en Alcampo.

---

## 3. GRAVE — Carrefour perdio el 57 % del catalogo por no reintentar

373 de sus 653 categorias contestaron **HTTP 403**. Mirando el log de cerca:

- los 403 empiezan en la **categoria 3**, o sea casi desde el principio
- siguen hasta la **468**
- a partir de ahi el recorrido va normal hasta el final

Es un bloqueo de Cloudflare que duro unos veinte minutos y **se levanto solo**. Y
el codigo, para cada una de esas 373 categorias, se rindio a la primera:

```python
if r.status_code >= 400:
    raise HTTPStatusError(...)      # 429, 500, 502, 503 y 504 si se reintentan
```

El 403 no estaba en la lista de estados que se reintentan. Y el bucle de
categorias contaba el error y pasaba a la siguiente, **sin volver a por ella
nunca**. Cuando el bloqueo se levanto, las 373 ya estaban descartadas.

### El arreglo, en dos capas

**Una,** el `Fetcher` reintenta los 403 con espera creciente, y se activa por
cadena (`reintentar_403=True`). Alcampo **no** lo usa: reconoce el reto de AWS
WAF mirando el cuerpo de la respuesta y tiene su propia renovacion de cookie, que
es mejor que esperar a ciegas.

**Dos,** y esta es la que de verdad importa: Carrefour ahora **vuelve a por las
categorias que fallaron**, hasta tres veces, esperando 2, 4 y 6 minutos y a la
mitad de ritmo en cada vuelta.

```
  373 categorias quedaron sin recoger; se espera 120s y se reintentan
  a ritmo mas lento (vuelta 1)
  rescatadas 341 de 373
```

Un bloqueo por sospecha de bot se levanta solo; lo unico que hace falta es estar
ahi cuando se levante. E insistir al mismo ritmo es lo que nos tenia fichados,
asi que cada vuelta va mas despacio.

---

## 4. El silver huerfano: el arreglo que no arreglaba nada

Al apartar el bronze malo de Alcampo y rehacer el pipeline, **el catalogo volvio
a salir sin frescos**. La razon:

- el pipeline escribe el silver bajo la fecha **de su bronze**, o sea el 17
- el silver roto del 18, hijo de la captura descartada, seguia en disco
- el emparejador coge **el silver mas reciente de cada cadena**: el del 18

Un silver mas nuevo que su bronze solo puede venir de una captura que despues se
descarto, asi que ahora el pipeline lo borra al escribir:

```
  se tira el silver huerfano de alcampo fecha=2026-09-18: su bronze ya no esta
```

---

## 5. Lo demas que salio al repasar los datos

### DIA arrastraba una deuda de fichas que crecia sola

DIA aparecio con 459 productos nuevos. El cupo de fichas era **100 fijas al dia**,
asi que se pidieron 100 y quedaron **374 sin ficha**: sin EAN, sin ingredientes,
sin alergenos y sin tabla nutricional. Al dia siguiente habria productos nuevos
otra vez y la cola no baja nunca.

Ahora el cupo es lo que falte, con suelo de 100 y techo de 400. A una peticion
por segundo son menos de siete minutos de mas en una tarea que ya dura trece.

### El resumen diario llamaba "imposibles" a 340 diferencias que no lo eran

Decia esto:

    aviso: 340 grupos con diferencias imposibles (>200%)

200 % es tres veces, y **tres veces es una diferencia normal** entre marca blanca
y marca: los preservativos de marca blanca contra Durex son 28 veces. La frontera
de lo imposible estaba medida y escrita desde el 17 de septiembre, pero en otro
sitio: la interfaz usaba 30 veces y el resumen 3, y los dos lo llamaban igual.

La regla vive ahora en `core/comparacion.py`, compartida por los dos, y el
resumen distingue las dos bandas:

    352 grupos con diferencias grandes pero creibles (entre 200% y 2900%):
        marca blanca contra marca, casi siempre
    aviso: 5 grupos con diferencias imposibles (>2900%, o sea mas de 30 veces)

De 340 a 5.

### Las filas "en disputa" seguian decidiendo donde estaba mas barato algo

El 17 de septiembre se marcaron 72 filas donde nuestro precio por unidad y el de
la cadena se contradicen por mas del doble y no se sabe cual esta mal. Se
apartaron de las comparaciones... en silver. **`precio_comparable` no llegaba a
gold**, asi que ni la interfaz ni el resumen se enteraban, y esas 72 filas salian
como los peores casos del dia.

Ahora llega, y las dos mitades la respetan.

---

## 6. Lo que se hizo con los datos del dia

| cadena | que se uso | por que |
|---|---|---|
| aldi, dia, mercadona | la captura del 18 | correctas |
| alcampo | la del **17** | la del 18 venia sin Frescos; el bronze malo esta en `data/debug/descartados/` |
| carrefour | la del **17** | la del 18 tenia 373 categorias sin recoger |

El catalogo quedo en **52.575 productos** y 6.448 grupos comparables, en vez de
los 49.353 y 6.060 que habia dejado la ejecucion nocturna.

---

## 7. La regla que sale de todo esto

> **Una ejecucion sin errores no es una ejecucion correcta.** "Cero errores"
> significa que nadie fallo, no que este todo. Lo que hay que comprobar no es si
> algo se rompio, sino si falta algo que ayer estaba.

Y su forma practica: cualquier control de calidad de una captura tiene que mirar
**la forma** del catalogo, no solo su tamano.
