# F06 · El reparto se decidía con costes **sin agrupar**

Estado: **defecto reproducido y arreglado; falta el oráculo exhaustivo**. Fecha: 13 de octubre de 2026.
Origen del hallazgo: revisión previa de fase 2, tabla §3, fila *«Multi-tienda sin demostrar»*.

> *«Informe G11 admite que el oráculo cubre aritmética, no asignaciones multi-tienda. → **Oráculo
> exhaustivo independiente de asignaciones y promociones condicionadas al conjunto.**»*

Y el criterio de F06, que es el que decide qué es un arreglo y qué no:

> *«Aplicar promociones a cada conjunto **realmente asignado** […] **No elegir partes de un descuento
> calculado sobre una cesta que al final no se compra en esa tienda.**»*
> *«**Aceptación:** casos combinatorios con contraejemplos, **discrepancias cero** para escenarios
> cubiertos, **suma de partes igual al total**; garantías y límites del algoritmo publicados.»*

---

## 1. Lo que se midió antes de tocar nada

**El vocabulario de promociones** (`core/promos.py`, 284 líneas) es **por línea y por cantidad**:
`coste(unidades, precio_cent)`. *Nueve mecánicas: `nxm` (3×2), `enesima` (2ª unidad −50 %), `porcentaje`,
`precio_fijo`, `lote`, `descuento_fijo`, `umbral`, `sin_regla` — más `acumulable` y `solo_online`, que
se enseñan y **no** se restan, porque ese dinero no baja el ticket.*

**Y el motor ya agrupa por producto y cadena**: `_agrupa_y_reparte` (línea 337) existe desde antes y su
docstring lo dice con un caso medido — *«un 3x2 daba 200 céntimos en una línea de tres y 300 en dos
líneas de una y dos. La misma compra, dos precios»*. **Ese defecto ya estaba arreglado y no lo he
tocado.** *Conviene decirlo: la mitad de lo que se podía sospechar ya estaba bien.*

## 2. El defecto: **los dos lados de la comparación se calculaban distinto**

`donde_comprar` (línea 464) hacía esto, y son cinco líneas de cableado:

```python
por_cadena[fuente] = [_resolver(p, fuente, mejor) for p in peticiones]   # SIN agrupar
...
resueltas = _agrupa_y_reparte([e for e in elecciones if e])              # agrupadas, variable LOCAL
...
repartido = _mejor_reparto(peticiones, por_cadena, max_t, una_tienda)    # recibe las SIN agrupar
```

**`una_tienda` —la referencia de una sola tienda— se calculaba con los costes agrupados, y
`_mejor_reparto` comparaba con los de línea.** *Dos números distintos para la misma compra.*

**Consecuencia, y es material**: como los costes por línea son **mayores o iguales** que los agrupados,
el optimizador **cree que concentrar líneas en una tienda cuesta más de lo que cuesta**, y **descarta el
reparto que sí ahorra**.

### El contraejemplo, con números

Dos líneas del **mismo producto** `p1` (2 unidades a 1,00 € con 3×2) y una tercera `p2`:

```
alcampo   p1 en dos lineas de 2 uds con 3x2, y p2 a 1,00 EUR con 3x2
          por linea:  2,00 + 2,00 + 1,00 = 5,00
          agrupado:   p1 junto son 4 uds -> un grupo de 3 -> 3,00, mas p2 1,00 = 4,00
dia       solo p2, a 0,50

una tienda, alcampo .................. 4,00   (agrupado, y el motor ya lo hacia bien)
reparto  p1 -> alcampo, p2 -> dia .... 3,00 + 0,50 = 3,50   <- el bueno
lo que devolvia el motor ............. 4,00 + 0,50 = 4,50
```

**Y con eso**:

```
total_cent:      450        (son 350)
ahorro_cent:     -50        <- NEGATIVO
merece_la_pena:  False      <- descarta el reparto
```

*Es el criterio de F06 fallando con sus propias palabras: **la suma de las partes no era el total**, y
se elegía «parte de un descuento calculado sobre una cesta que al final no se compra en esa tienda».*

**Reproducido en `tests/test_fase2_f06_reparto_agrupado.py`** (`F.` antes del arreglo, `..` después —
*la reproducción fue la prueba de que discrimina*).

**El daño, dicho sin adorno**: a quien compra se le decía **que no partiera la lista**, con un ahorro
**negativo**, cuando partirla ahorraba 50 céntimos.

---

## 3. El arreglo

Tres líneas: **las elecciones agrupadas vuelven a `por_cadena`**, que es lo que el reparto compara.

```python
pendientes = iter(resueltas)
por_cadena[fuente] = [next(pendientes) if e else None for e in elecciones]
```

*`_agrupa_y_reparte` reparte el total del grupo entre sus líneas conservando la suma exacta, así que
sumar las partes sigue dando el total de la tienda* — que es la propiedad que F06 exige.

**Y hay un detalle que importa**: este defecto **no estaba en `_mejor_reparto`**, que recibe sus
estructuras y está bien. *Estaba en quien se las da.* **Por eso la prueba ataca `donde_comprar` y no la
función interna**: probar la interna con datos ya agrupados habría dado verde y no habría visto nada.

---

## 4. El oráculo exhaustivo, y **lo que ha encontrado**

**Está construido**: `core/oraculo_reparto.py`. *No importa nada de `cesta.py`* — ni el optimizador, ni
la aritmética de promociones, ni la agrupación: **la mecánica de la oferta entra ya leída** (`Oferta`),
así que ni siquiera depende del parser de castellano de folleto. *Si los dos coinciden, es porque los
dos calculan bien.*

**Y antes de usarlo contra el motor se comprueba él solo**: su aritmética contra cuentas a mano, su
agrupación por producto dentro de la tienda, que enumera **todas** las asignaciones (`asignaciones_vistas`
en el caso de dos líneas × dos tiendas da 4), y que una línea que no está en una tienda **no se puede
asignar ahí**. *Un oráculo que no se comprueba no es un oráculo: es otra opinión.*

### Y ha encontrado el defecto que F06 describía

**No cuatro casos hechos a mano** —*se eligen los que uno ya sabe que pasan*—: un **barrido de 200
escenarios al azar con semilla fija**, precio y oferta por tienda y producto.

```
9 discrepancias en 176 escenarios (5%), TODAS con el motor mas caro que el optimo
```

**El caso mínimo, entero:**

```
linea l1: p2, 2 unidades | linea l2: p1, 3 unidades | linea l3: p1, 1 unidad

alcampo  l1 80 3x2   l2 120 3x2   l3 120 3x2
aldi     l1 50 -25%  l2 100 sin   l3 100 sin
dia      l1 70 sin   (l2 y l3 no estan)

motor    l1->aldi, l2->alcampo, l3->alcampo :  75 + (270 + 90) = 435
oraculo  l1->aldi, l2->alcampo, l3->aldi    :  75 +  240 + 100 = 415
```

**Y por qué el motor manda `l3` a alcampo**: su **parte** del 3×2 allí es **90**, frente a 100 en aldi.
*Pero esa parte de 90 sale de un grupo de **cuatro** unidades que **sólo se forma si `l3` se queda**:
con `l3` fuera, alcampo son 3 unidades y cuesta **240**, y `l3` sola en aldi cuesta 100.*

**Es la frase de F06 al pie de la letra**: *«no elegir partes de un descuento calculado sobre una cesta
que al final no se compra en esa tienda»*. **La parte que se usa para decidir sólo existe si la decisión
ya está tomada.** *Circular.*

**Y no miente sobre el coste de lo que propone** — los 435 son el precio real de su asignación —:
**lo que hace es proponer una asignación peor que la que existe.** *Se le dice a quien compra que pague
20 céntimos de más, y se le manda a la tienda equivocada una de las líneas.*

**Queda fijado** en `tests/test_fase2_f06_oraculo_asignaciones.py` con `xfail(strict=True)`: *la prueba
afirma el criterio de F06 —discrepancias cero—, hoy falla, y el `strict` obligará a quitar la marca
cuando se arregle.* **No se borra ni se rebaja el criterio.**

### Lo que F06 pide y sigue pendiente

**Arreglarlo**: para cestas pequeñas, *enumerar asignaciones* —que es lo que el oráculo ya hace— y
re-puntuar cada una con su conjunto real; para lo que no se pueda enumerar, **llamar heurística a la
heurística**, que es lo que F06 dice con esas palabras. Y **publicar la garantía y el límite**: hoy no
está escrito en ningún sitio qué promete `_mejor_reparto` y qué no.

---

## 5. El arreglo: cada asignación se puntúa con **su** conjunto

**El reparto dejó de usar «partes».** `_mejor_reparto` recibe las elecciones **sin agrupar** y, para
cada asignación, **agrupa lo que de verdad va a cada tienda** y suma:

```python
def _coste_con_lo_agrupado(elecciones):
    return sum(e.coste_cent for e in _agrupa_y_reparte(list(elecciones)))
```

*Es la misma cuenta que `una_tienda` hace para una tienda entera, aplicada al conjunto real.*

**Y se enumera cuando cabe.** F06 pide el óptimo para cestas pequeñas y honestidad para las grandes:

```
_LIMITE_EXHAUSTIVO = 200_000

por debajo   producto cartesiano de tiendas -> el optimo, y exhaustivo = True
por encima   la heuristica de siempre       -> exhaustivo = False, y la respuesta lo dice
```

*El límite está puesto con números*: 6 cadenas y 8 líneas son 1,7 millones de asignaciones.

> **Y el write-back de la ronda anterior se quitó.** *Escribir en `por_cadena` las elecciones ya
> agrupadas fue el arreglo de entonces y era **a medias**: quitó la incoherencia entre los dos números
> y dejó la parte circular, que es justo lo que el oráculo encontró. Ahora `por_cadena` se queda sin
> agrupar a propósito, y quien agrupa es el reparto.*

**El resultado, medido**: el barrido de 200 escenarios pasa de **9 discrepancias** a **cero**, y el
`xfail(strict=True)` que las fijaba **saltó como `XPASS` al arreglarlo** — *que era exactamente para lo
que estaba: la marca se quita en cuanto la prueba pasa.* **Y los 41 tests de reparto que ya existían
—autorización, invariantes, reparto entre tiendas, el oráculo de G11— siguen pasando.**

---

## 6. Los dos límites de alcance, que también hay que publicar

**a) El `umbral`.** `umbral` («5 € dto comprando 20 €») se aplica hoy **a los productos de esa promoción
dentro de la tienda**. Medido: dos líneas *distintas* de 12 € con esa oferta dan **2400 céntimos** en el
motor y darían **1900** si el umbral fuera del ticket entero. *El texto del folleto no dice de qué es el
umbral, y el motor ha elegido una lectura sin publicarla.* **El oráculo lo excluye a propósito**:
mientras no se decida, incluirlo sería elegir una de las dos lecturas y llamarla verdad.

**b) La heurística por encima del límite.** Con más de ~200.000 asignaciones **no se promete el óptimo**,
y la respuesta lo dice con `exhaustivo: False`. *Es lo que F06 pide con «heurística se llama heurística»,
y la prueba comprueba **los dos lados**: que una cesta grande **no** se declara exhaustiva y que una
pequeña **sí**.*

**c) El banco de matching.** Positivos/negativos duros por familia/cadena, precisión/recall/abstención
**con denominadores**, y *«mismo GTIN no ignora contradicciones; distinto GTIN no demuestra engaño»*.
**Sin empezar.**

---

## 7. Lo que queda de F06

1. **Publicar la garantía y el límite** de `_mejor_reparto` en el documento del algoritmo —*hoy está en
   el código y en este informe, pero no donde se lee el algoritmo*.
2. **Decidir y decir el alcance del umbral.**
3. **El banco de matching**, sin empezar.
4. *Y una pregunta abierta que conviene no perder*: el límite exhaustivo es un número de asignaciones,
   **no de tiempo**. *Si alguna vez se mide que 200.000 asignaciones tardan demasiado, el número tendrá
   que bajar y habrá que decirlo.*
