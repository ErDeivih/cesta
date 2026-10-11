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

## 4. El límite que queda, y hay que publicarlo

**El reparto se sigue calculando con la parte que a cada línea le toca suponiendo que *todas* las líneas
van a esa tienda.** Si una asignación deja en la tienda **sólo una parte** del grupo, esa parte se
calculó sobre un conjunto que al final no se compra allí.

*Es literalmente la frase de F06* —«no elegir partes de un descuento calculado sobre una cesta que al
final no se compra en esa tienda»— **y sigue en pie**. El arreglo de hoy quita la incoherencia entre
`una_tienda` y el reparto, que era el defecto **medido**; **no** convierte el algoritmo en exacto.

**Lo que falta, y es el entregable central de F06**: el **oráculo exhaustivo de asignaciones** para
cestas pequeñas —*enumerar todas las asignaciones, calcular cada conjunto realmente asignado y aplicar
la promoción a ese conjunto*—, comparar contra `donde_comprar` y exigir **discrepancias cero**. Y para
lo que no se pueda enumerar, **publicar la garantía y llamar heurística a la heurística**.

**Y queda por decidir, también con prueba, el alcance del umbral.** `umbral` («5 € dto comprando 20 €»)
se aplica hoy **a los productos de esa promoción dentro de la tienda**. Medido: dos líneas *distintas*
de 12 € con esa oferta dan **2400 céntimos** en el motor y darían **1900** si el umbral fuera del ticket
entero. *El texto del folleto no dice de qué es el umbral, y el motor ha elegido una lectura sin
publicarla.* **No lo llamo defecto**: lo llamo límite sin publicar, que es lo que F06 pide cerrar.

---

## 5. Lo que queda de F06

1. **El oráculo exhaustivo de asignaciones**, independiente del optimizador. *Es lo que el hallazgo pide
   y lo único que convierte «discrepancias cero» en una afirmación con contenido.*
2. **Publicar la garantía y el límite** de `_mejor_reparto`: hoy no está escrito en ningún sitio qué
   promete y qué no.
3. **El alcance del umbral**, decidido y dicho.
4. Banco de matching: positivos/negativos duros por familia/cadena, precisión/recall/abstención **con
   denominadores**, y *«mismo GTIN no ignora contradicciones; distinto GTIN no demuestra engaño»*.
   *Sin empezar.*
