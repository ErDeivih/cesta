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
