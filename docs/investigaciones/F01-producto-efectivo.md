# F01 · El producto efectivo que se compra cuando se acepta una alternativa

Estado: **motor y cierre arreglados y probados; falta el recorrido distinguible por HTTP**. Fecha: 13
de octubre de 2026.
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

## 2. Cómo se comprueba, y con qué fuerza

**No es lectura de código.** Se ejecuta el motor real — `_candidatos`, `_llave_candidato`,
`identidad.decide`, `_es_la_confirmada`, `_elige`, `_serializa`, `donde_comprar`, `coste_por_linea` — y
**sólo se sustituyen las dos fuentes de datos**: la conexión a Postgres y el texto de promociones de
silver. *Sustituir `_candidatos` entero, como hace `test_cesta_api.py`, no sirve aquí: su mock devuelve
claves de dos elementos y valores de cuatro, y `coste_por_linea` lee `k[-1]` y `v[7]`.*

Reproducción: `tests/test_fase2_f01_sustitucion.py` — **3 pasan**.

---

## 3. Lo que se midió, antes y después

```
ANTES (reproducido el 13 de octubre de 2026)

  ESTIMACION   producto efectivo alcampo:P-B · identidad «confirmada» · total  500 c
  CIERRE       precio_cent 300 · coste_cent 900 · producto_id alcampo:P-A (el pedido)
  DISCREPANCIA 400 centimos

DESPUES (13 de octubre de 2026, tras el arreglo)

  ESTIMACION   alcampo:P-B · confirmada · 500 c
  CIERRE       alcampo:P-B · alcampo · precio 250 · coste 500
  DISCREPANCIA 0
```

**El daño que se evitó no era un redondeo**: el histórico apuntaba a un producto que nadie compró, a un
precio que nadie pagó, sin la oferta que sí se aplicó. *Y una compra no se recalcula: lo que se guarda
mal miente para siempre.*

---

## 4. Las causas, y **una corrección de mi propio diagnóstico**

**Causa 1 — `coste_por_linea` descartaba las alternativas.** Líneas 871-872:

```python
suyos = [(k[1], v[1]) for k, v in mejor.items()
         if k[0] == esperada and k[-1] != "alternativa"]
```

*El filtro es correcto para lo que se escribió* — separa el candidato principal de la oferta de
alternativa — **y por eso mismo dejaba fuera a B**, que es el que hay que cobrar cuando está confirmado.

**Causa 2 — la identidad que se guardaba era el pedido, nunca el efectivo.**
`almacen.cierra_compra` escribía `linea["producto_id"]`, que es lo que la línea pide. **Con una línea
que sólo pide grupo, eso es `NULL`**: la compra no guardaba *qué* producto le había puesto el precio.
**La autorización no influía en la identidad en ningún sitio.**

> ### Y una corrección, porque el informe de esta misma investigación decía otra cosa
>
> **Decía**: *«el cierre no ve la confirmación: `cierra_compra:563` no selecciona `autorizado*`»*, y de
> ahí deducía que el precio salía de A **porque el dato no llegaba**.
>
> **Es falso.** `main.py:575` hace `lineas = _con_autorizacion(lineas, lista_id)`, con el comentario
> *«lo autorizado se lee de la base, no del cuerpo de la petición»*: **la autorización sí llega a
> `coste_por_linea`**. *Lo demostró mi propia reproducción sin querer: le pasé `autorizado*` a mano y
> aun así devolvía A.*
>
> **El precio salía de A sólo por la causa 1.** *Y el `SELECT` de `cierra_compra` no necesita
> `autorizado*`: recibe los precios ya calculados.* **Corregido aquí, no borrado.**

*Las dos causas son independientes: arreglar sólo la 1 deja el `producto_id` sin identidad; arreglar
sólo la 2 deja el precio en el de A.*

---

## 5. Por qué el cierre anterior pudo declararse sin que saltara nada

**Porque el fixture de `test_g03_cierre.py` no puede distinguir la sustitución, y eso está medido.**
Grupo 6803 en `alcampo`, consultado el 13 de octubre de 2026:

```
clave=(6803, 'alcampo')                 pid=alcampo:202841  precio=518  exacta=False
clave=(6803, 'alcampo', 'alternativa')  pid=alcampo:202841  precio=518  exacta=False
```

**En esa tienda hay un solo candidato, y ocupa las dos casillas.** *Así que aceptar la sustitución y no
aceptarla archivan el mismo producto, la misma tienda y el mismo precio — no por una regla, sino porque
no hay dos productos que distinguir.*

**Y el docstring del módulo prometía una diferencia que ese fixture no puede ver**: decía que
*«revocada, la línea coge el más barato de hoy: día, 260»*. **No**: el fixture **decide la tienda**, y
con la tienda decidida revocar también archiva `alcampo` a 518. *Las dos afirmaciones están corregidas
en el fichero.*

**Lo que este caso enseña y hay que conservar**: *una batería verde sobre un caso que no puede
distinguir se lee igual que una verde sobre el caso correcto.* **Es la misma lección que
`banco_verdad.py` escribe para el clasificador**: *un control que comparte vocabulario con lo que vigila
confirma sus propios errores.* **Y es el hallazgo 2 de la revisión — «aceptación rebajada» — en su forma
más literal: se generalizó «el cierre guarda lo que se compró» desde un caso que no podía comprobarlo.**

---

## 6. Lo que se ha hecho

1. **`plataforma/sql/015_lo_pedido_y_lo_comprado.sql`** — `compra_linea.producto_pedido_id`, nullable,
   `IF NOT EXISTS`, con su `COMMENT ON COLUMN`. *`producto_id` pasa a significar **lo comprado**; lo
   pedido se guarda aparte cuando difiere.* **En la compra y no sólo en la línea de la lista**, porque
   `limpiar_lineas_borradas` poda las archivadas a los 30 días: *una compra de un año tiene que poder
   explicarse sola.*
2. **`cesta.coste_por_linea`** — honra la confirmación: si `_es_la_confirmada` es cierta, el precio, la
   cadena, **la oferta** y el producto son los de la alternativa. *Sin confirmación, el
   comportamiento de antes, que era correcto.* Y devuelve `promo` y `producto_id` en vez de dejar que
   el reparto los adivine por precio y cadena.
3. **`almacen.cierra_compra`** — guarda el producto efectivo en `producto_id` y el pedido en
   `producto_pedido_id`; y `lineas_de_compra` expone la columna nueva.
4. **`test_g03_cierre.py`** — la prueba que consagraba el contrato viejo **se sustituye, no se borra**:
   ahora afirma la identidad que antes era `NULL`, y lleva escrito **el límite medido** del fixture.
   *El docstring del módulo corrige la promesa falsa sobre «día, 260».*
5. **`test_fase2_f01_sustitucion.py`** — la marca `xfail(strict)` **se quitó al arreglar**, que era
   exactamente para lo que estaba: *el `strict` obliga a quitar la marca en cuanto la prueba pasa.*

---

## 7. Lo que queda de F01

**Un recorrido por HTTP con una sustitución distinguible, y el de navegador.** *El fixture de grupo 6803
no sirve, y ya se sabe por qué.* Hace falta un caso donde **A y B difieran en precio o en oferta** — el
del catálogo controlado, que hoy sólo corre en memoria.

*Es implementación sin ensayo servido en la parte HTTP*, y así queda anotado en el tablero.
**No se declara F01 cerrado por tener el motor verde.**

---

## 8. Lo que no se toca

*La estimación no se toca: es el camino correcto y ahora tiene prueba que lo fija.* **Si esa prueba se
rompe, lo que se ha roto es el bueno.**
