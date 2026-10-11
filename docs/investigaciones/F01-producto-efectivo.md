# F01 · El producto efectivo que se compra cuando se acepta una alternativa

Estado: **defecto reproducido, sin corregir**. Fecha: 13 de octubre de 2026.
Origen del hallazgo: revisión previa de fase 2, tabla §3, fila *«Sustitución estimada frente a compra»*.

> *«`coste_por_linea` filtra candidatos cuya llave termina en `alternativa`; `test_g03_cierre.py` prueba
> archivar el producto del grupo, **no el sustituto**. Probar compra realmente realizada del sustituto
> aceptado, su identidad/precio/promoción/tienda y recibo. **No dar por correcto ese contrato por estar
> verde.**»*

---

## 1. El escenario, tal y como lo pide el encargo

Catálogo controlado, grupo 100, una sola tienda:

| | producto | precio | oferta | EAN |
|---|---|---|---|---|
| **A** | `alcampo:P-A` — «Refresco de cola 2 L» | 300 c | — | 8412345678905 |
| **B** | `alcampo:P-B` — «Refis cola 2 L» | 250 c | **3×2** | 8499999999992 |

**La persona pide A, acepta la alternativa B en la tienda `alcampo`, y se lleva 3 unidades.**
Lo que cuesta de verdad: un 3×2 sobre 250 son **dos pagadas = 500 c**.

---

## 2. Cómo se ha comprobado, y con qué fuerza

**No es lectura de código.** Se ejecuta el motor real — `_candidatos`, `_llave_candidato`,
`identidad.decide`, `_es_la_confirmada`, `_elige`, `_serializa`, `donde_comprar`, `coste_por_linea` — y
**sólo se sustituyen las dos fuentes de datos**: la conexión a Postgres y el texto de promociones de
silver. *Sustituir `_candidatos` entero, como hace `test_cesta_api.py`, no sirve aquí: su mock devuelve
claves de dos elementos y valores de cuatro, y `coste_por_linea` lee `k[-1]` y `v[7]`.*

Reproducción: `tests/test_fase2_f01_sustitucion.py` — **2 pasan, 1 `xfail(strict)`**.

---

## 3. Lo que se ha medido

```
ESTIMACION (donde_comprar)
  cadena            : alcampo
  producto efectivo : alcampo:P-B          <-- la alternativa aceptada
  identidad         : confirmada
  total_cent        : 500                  <-- 3 unidades de B con 3x2

CIERRE (coste_por_linea -> compra_linea)
  cadena            : alcampo
  precio_cent       : 300                  <-- el unitario de A
  coste_cent        : 900                  <-- tres unidades de A, sin oferta
  producto_id       : alcampo:P-A          <-- EL PEDIDO, no el efectivo

DISCREPANCIA: 900 - 500 = 400 centimos
```

**La estimación está bien. El cierre no.** *Y el daño no es un redondeo: el histórico registra un
producto que nadie compró, a un precio que nadie pagó, sin la oferta que sí se aplicó.* **El gasto y el
diario heredan de ahí.**

---

## 4. La causa: **dos sitios independientes**, y arreglar uno solo no arregla nada

**1. El cierre no ve la confirmación.** `almacen.cierra_compra`, línea 563:

```sql
SELECT id, grupo_id, producto_id, nombre_visto, cantidad, cadena_elegida
  FROM lista_linea
 WHERE lista_id = %s AND borrado_en IS NULL AND en_carrito
```

**No selecciona `autorizado`, `autorizado_producto` ni `autorizado_cadena`.** Así que el cierre no puede
saber qué se aceptó aunque quisiera, y en la línea 586 escribe `linea["producto_id"]` — **el pedido**.
*Es el mismo hueco que el comentario de `coste_por_linea` documenta haber tapado en la estimación:
«sin esto, la comparación de la sustitución ve `None` y no cuenta ninguna confirmación». En el cierre
sigue abierto.*

**2. Y `coste_por_linea` descarta las alternativas.** Líneas 871-872:

```python
suyos = [(k[1], v[1]) for k, v in mejor.items()
         if k[0] == esperada and k[-1] != "alternativa"]
```

**El filtro es correcto para lo que se escribió** — separa el candidato principal de la oferta de
alternativa — **y por eso mismo deja fuera a B**, que es exactamente el que hay que cobrar cuando está
confirmado.

*Los dos son independientes: si sólo se arregla el (1), el precio sigue siendo el de A; si sólo se
arregla el (2), el cierre sigue sin recibir el dato.*

---

## 5. Por qué el cierre anterior pudo declararse sin que saltara nada

`test_g03_cierre.py` prueba **archivar el producto del grupo**, no comprar el sustituto. Y el
`xfail(strict)` de la reproducción es la primera prueba del proyecto que ejecuta el camino completo
—pedido, confirmación, precio, promoción y cierre— sobre el sustituto.

**Lo que este caso enseña y hay que conservar**: *una batería verde sobre el camino equivocado se lee
igual que una verde sobre el camino correcto.* **Es la misma lección que `banco_verdad.py` escribe para
el clasificador**: *un control que comparte vocabulario con lo que vigila confirma sus propios errores.*

---

## 6. Lo que F01 tiene que dejar hecho

1. **`cierra_compra` recibe lo aceptado**: añadir `autorizado`, `autorizado_producto` y
   `autorizado_cadena` al `SELECT` y pasarlos a `coste_por_linea` como ya hace su firma.
2. **`coste_por_linea` honra la confirmación**: cuando `_es_la_confirmada` sea cierta, el precio, la
   cadena y la oferta son **los de la alternativa** — la misma decisión que `_elige` ya toma.
3. **La identidad que se guarda es la efectiva**: `compra_linea.producto_id` tiene que ser **B**.
   *Decidir explícitamente qué se hace con el pedido original: el encargo pide conservarlo («la
   solicitud original permanece»), así que A no se pierde — **se guarda como lo pedido, con B como lo
   comprado**.*
4. **No archivar A «porque era el grupo»** mientras se compró B (criterio del encargo, punto 3 de F01).
5. **Verificación**: la prueba marcada `xfail(strict)` pasa a verde **y se le quita la marca**; más
   recorrido **HTTP y de almacenamiento real aislado**, que es lo que la aceptación de F01 exige.

**Y un límite que se declara ya**: *esta reproducción cubre el motor con un catálogo controlado en
memoria; **no** cubre todavía el recorrido HTTP ni el cierre contra PostgreSQL.* **Es implementación sin
ensayo servido hasta que F01 lo haga**, y así queda anotado.

---

## 7. Lo que NO se toca

*La estimación no se toca: es el camino correcto y ahora tiene prueba que lo fija.* **Si esa prueba se
rompe, lo que se ha roto es el bueno.**
