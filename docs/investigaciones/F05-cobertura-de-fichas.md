# F05 · La cobertura de fichas, medida

Estado: **medido; sin empezar el trabajo**. Fecha: 13 de octubre de 2026.
Origen del hallazgo: revisión previa de fase 2, tabla §3, fila *«Fichas sin ejecución suficiente»*.

> *«Informe anterior registra 79.887 sin ficha y cinco cadenas sin cobertura. → **Medir situación actual
> por campo/cadena, integrar ejecución real, parser y presupuesto**; **no llamar toda ausencia
> "limitación de fuente"**.»*

---

## 1. Lo primero que pide el hallazgo: medir

**El instrumento ya existe y no había que escribir nada**: `core/inventario.py` -- *«cola de fichas: qué
sabemos de cada producto, cuándo lo miramos y cuándo toca volver»* --, con su `resumen()`.

```
data/inventario.sqlite

    alcampo         pendiente 43.603
    carrefour       pendiente 17.283
    dia             pendiente  6.292
    lidl            correcto     28   ·   pendiente 5.026
    mercadona       pendiente  4.477
    aldi            pendiente  3.206
    ───────────────────────────────────────
    TOTAL           pendiente 79.887  ·  correcto 28
```

**79.887 pendientes y 28 correctas.** *El número coincide exactamente con el que citaba la revisión, así
que no se ha movido: la cola está montada y **no se ha procesado**.*

## 2. Y lo que eso significa, dicho sin adorno

**La ausencia de fichas no es una limitación de fuente.** *Es trabajo sin ejecutar: hay 79.887 productos
en cola, esperando, y **28 hechas**.*

**Por eso el hallazgo insiste en esa frase** -- *«no llamar toda ausencia "limitación de fuente"»* --:
*una ficha que nunca se pidió y una ficha que la tienda no publica se ven igual en un porcentaje de
cobertura, y son dos cosas distintas: una se arregla ejecutando, la otra no.* **El 99,96 % de esta cola
está en el primer caso.**

**Y hay una consecuencia práctica**: *mientras la cola no se procese, cualquier cifra de cobertura de
fichas que se publique mide **cuánto se ha ejecutado**, no **cuánto se puede saber**. *Llamarla
«cobertura» sin decirlo es el mismo error que el encargo prohíbe en otras formas.*

## 3. Lo que hay montado, y lo que falta

**Montado** --medido, no supuesto--:

- **La cola** (`core/inventario.py`, SQLite): estados, *lease* con vencimiento, hash, alta idempotente, y
  `resumen()`. *Con sus pruebas.*
- **El alta desde bronze**: `enganche()` -- *«S02: inventario de 74.861 fichas desde bronze en 75,7 s»*,
  medido y documentado.
- **El informe de cobertura por fuente** (`docs/`), *con deuda de cola*.
- **Y `lidl` tiene 28 `correcto`**, así que **el camino completo -- pedir, parsear, guardar y marcar --
  funciona al menos una vez**.

**Lo que falta**, y es lo que el hallazgo pide:

1. **Ejecutar la cola de verdad** -- *79.887 fichas, con presupuesto y ritmo, y sin que el WAF lo pare*.
   *Es la parte grande, y no se ha hecho.*
2. **Medir por campo y por cadena**, no sólo por estado: *cuántos productos tienen kcal, cuántos
   ingredientes, cuántos Nutri-Score -- **y separar «la tienda no lo publica» de «no lo hemos pedido
   todavía»**.* **Sin esa separación, la cifra de cobertura miente por omisión.**
3. **El parser**, con su banco de pruebas.
4. **Y el presupuesto**: cuántas peticiones, a qué ritmo, y qué se hace cuando una cadena bloquea.

## 4. Lo que NO se ha hecho en esta ronda, y por qué

**Sólo se ha medido.** *F05 es un paquete grande -- la ejecución de 79.887 fichas es un trabajo de
operación, con red, WAF y presupuesto --, y empezarlo sin poder verificarlo habría dejado trabajo a
medias y una cifra sin comprobar.*

**Y medir era, literalmente, lo primero que el hallazgo pide.** *Ahora se sabe qué hay y qué no: **una
cola de 79.887 esperando y 28 hechas**.*


---

## 5. Y al ir a ejecutarla, el hallazgo de verdad: **hay ejecutor para una cadena de seis**

*(Ronda 26.)* Iba a ejecutar la cola de `aldi` con presupuesto acotado. **No se puede: para `aldi` no hay
nada que ejecutar.** Medido:

```
projects/cesta/fichas_lidl.py:72     inventario.tomar(con, limite, fuentes=["lidl"], ahora=ahora)
projects/cesta/fichas_lidl.py:28     from projects.cesta import ficha_lidl
projects/cesta/fichas_lidl.py:30     PARSER_VERSION = "lidl-jsonld-2"

modulos que piden una ficha, por cadena:
   banco_de_pares.py    alcampo, aldi, dia     <- no es un ejecutor de fichas
   mide_nutricion.py    lidl
```

**Hay un solo descargador y un solo parser, y son de Lidl.** *No hay `ficha_alcampo`, ni `ficha_aldi`, ni
`ficha_dia`, ni `ficha_carrefour`, ni `ficha_mercadona`.*

**Y eso explica, sin dejar nada al azar, el numero de la seccion 1**: de 79.887 pendientes, **las 28
`correcto` son todas de Lidl** -- *la unica cadena con ejecutor es la unica con fichas.*

### Lo que corrijo de lo que yo mismo escribi

Dije: *«la ausencia no es una limitacion de fuente: **es trabajo sin ejecutar**»*. **Es verdad a medias, y
la mitad que falta importa:**

- Para **Lidl**: hay ejecutor, y **28 de 5.054**. *Ahi si es trabajo sin ejecutar.*
- Para **las otras cinco**: **no hay con que ejecutarlo.** *No es trabajo pendiente de una pasada: es
  codigo que no existe.* **Llamarlo «sin ejecutar» hacia parecer que bastaba con lanzarlo.**

**Y la distincion que F05 pide -- «no llamar toda ausencia limitacion de fuente» -- ya esta hecha, campo a
campo, para Lidl**, en el propio comentario del ejecutor:

> *«**Y lo que este hash NO puede vigilar, medido.** El bloque `@type=Product` de Lidl trae nueve [campos]
> [...] Asi que no hay campos de contenido que hashear: **no es un parser incompleto, es una fuente que no
> los da**. Para tenerlos hay que **parsear el HTML** de la ficha o ir a **fuente** [externa].»*

*Es exactamente la frase del hallazgo, aplicada y con evidencia.* **Lo que falta es hacerla para las otras
cinco.**

### El estado de F05, entonces, es este

| pieza | estado |
|---|---|
| La cola (estados, *lease*, hash, revision, resumen) | **hecha y probada** |
| El alta desde bronze | **hecha** (74.861 fichas en 75,7 s, medido) |
| El presupuesto y el ritmo | **hechos** (`--limite`, `RITMO`, y dice cuantos dias faltan) |
| **Un descargador y un parser** | **solo de Lidl** |
| **Las otras cinco cadenas** | **no tienen nada** |
| La distincion «no lo publica» / «no lo hemos pedido» | **hecha para Lidl**; para las demas, **todo es «no lo hemos pedido»** |

**Y por eso la accion siguiente no es «lanzar una pasada»**: es **escribir el descargador y el parser de
una segunda cadena** -- *`aldi`, que tiene 3.206 pendientes y es la mas pequena --, con su `PARSER_VERSION`
y su prueba sin red (`fetch` es inyectable, asi que se puede probar sin pedir nada).*


---

## 6. Y para Aldi la respuesta esta en el crudo que **ya esta en disco**

*(Ronda 27.)* Iba a escribir `ficha_aldi.py`. **Antes de escribirlo mire que hay**, y el crudo lo
respondio **sin una sola peticion**.

`projects/cesta/collectors/aldi.py:74` -- *«sitemap oficial de productos + **API de producto por
lotes**»* -- llama a `{BASE}/api/product/pds/{ids}?scope=...`, **guarda la respuesta entera en crudo**
(`save_raw(FUENTE, f"pds-{lote[0]}", body)`) **y la reutiliza**. *Asi que la respuesta de Aldi esta en
`data/raw/fuente=aldi/`, y se puede leer sin pedir nada.*

**Los 18 campos que trae, medidos:**

```
assets  brandName  categoryIDs  currentPrice  isAvailable  isComingSoon  isFreezing  isRecall
longDescription  longDescriptionFormatted  mainCategoryID  metaDescription  metaTitle
name  objectID  productReferences  productSlug  salesUnit
```

**Ninguno es nutricion. Ni kcal, ni ingredientes, ni alergenos, ni Nutri-Score.**

### Lo que eso significa, y es exactamente la distincion que F05 pide

**Para Aldi NO es «no lo hemos pedido».** *El colector pide, a diario, por lotes, y la respuesta esta en
disco.* **Es «la fuente no lo publica» -- en la API que se usa.**

**Y la salida es la misma que el ejecutor de Lidl ya documenta para Lidl**: *«no es un parser incompleto,
es una fuente que no los da. Para tenerlos hay que **parsear el HTML** de la ficha o ir a **fuente**
[externa]».*

### Y otra vez corrige la accion siguiente

**Ayer escribi que habia que «escribir el descargador y el parser de una segunda cadena (`aldi`)».**
*Medido, eso habria sido escribir un descargador para una API que **no trae nutricion**: trabajo que no
resuelve el problema.*

**Lo que hay que decidir primero es donde vive la nutricion de Aldi** -- la pagina HTML del producto, o
una fuente externa --, y **eso es una decision con evidencia, no un modulo que se escribe por inercia.**
*Y la misma pregunta hay que contestarla para alcampo, carrefour, dia y mercadona antes de escribir
ninguno.*

**Es la cuarta vez en esta fase que medir antes de escribir cambia el trabajo que iba a hacer.**
