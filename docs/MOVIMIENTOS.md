# Bajadas, subidas y ofertas que no lo son

Dos pantallas copiadas a la competencia, hechas el 18 de septiembre de 2026.

    "bajadas de esta semana"    de Precios del Super
    "verificador de ofertas"    de PrecioReal

Lo interesante es que **no hubo que calcular nada**. `core/derive.py` llevaba
semanas escribiendo `ha_bajado`, `variacion_cent`, `precio_base_cent`,
`posicion_90d` y `min/max_90d` en `gold/precio_derivado.parquet`. Lo que faltaba
no era el analisis: era ensenarlo. `plataforma/api/movimientos.py` son dos
consultas.

    GET /api/bajadas?dias=7&cadenas=aldi,dia&limite=60&subidas=false
    GET /api/ofertas-dudosas?limite=60&cadenas=alcampo

---

## 1. Lo que costo trabajo: que una bajada sea una bajada

La primera version, probada contra los datos reales del dia, encabezaba asi:

```
  -96.7%  alcampo  NATURTIERRA Berberina           594,00 ->  19,80 EUR/ud
  -96.7%  alcampo  AQUILEA Descanso              1.020,00 ->  34,00 EUR/ud
  -96.7%  alcampo  PRODUCTO ALCAMPO Detergente     570,00 ->  19,00 EUR/ud
```

Ocho productos, todos de Alcampo, todos exactamente al **-96,7 %**. Dividir por
treinta no es una oferta: son envases de 30 unidades que un dia se leyeron como
una unidad y al siguiente como treinta. **El precio de venta no se habia
movido.**

El control que ya habia -- no aceptar variaciones de mas de 30 veces -- no los
paro por un detalle tonto: la variacion era **exactamente** 30, y la comparacion
era `<=`.

### Las tres condiciones que se pusieron

Una bajada es una bajada solo si:

1. **La unidad es la misma.** Comparar EUR/kg con EUR/ud no es ver una bajada, es
   comparar dos cosas distintas.
2. **La cantidad es la misma.** Se deduce del propio dato, `precio_cent /
   precio_unidad_cent`, y se admite un 2 % de diferencia por redondeo. Si no
   coincide, lo que cambio fue la lectura del formato.
3. **El precio de venta se movio en el mismo sentido.** Lo que paga la gente en
   caja es la prueba de que hubo un cambio de precio. Medido sobre el dia: de
   31.653 productos que se pueden comparar con la semana anterior, **1.349
   cambian de precio por unidad sin que cambie el de venta**. Son todos falsos.

Con eso puesto, lo que sale arriba es de verdad:

```
  -74.9%  alcampo  Mikados de citronela        3,99 -> 1,00 EUR
  -74.7%  alcampo  LURPAK Barra de mantequilla 3,95 -> 1,00 EUR
  -70.9%  alcampo  AXE Black Desodorante       3,44 -> 1,00 EUR
```

Todos a **exactamente 1,00 €**, sostenido varios dias. Es una liquidacion de
Alcampo: ese dia tenia **1.115 productos a 1,00 € clavado**.

Y las subidas tambien salen bien, que es la otra mitad util: "Galletas con
formas" de Aldi pasa de 1,74 a 3,49 €, o sea que **se acabo la oferta**. Verlo a
tiempo vale tanto como ver una bajada.

---

## 2. El verificador de ofertas, y un control que esta dormido

La pregunta no es cuanto cuesta: es **si el descuento que anuncian existe**. Se
cruza el texto de promocion que publica la cadena (`promo_txt`, 6.885 productos)
con lo que dice la serie de ese mismo producto (`precio_base_cent`, la mediana
movil). Si hoy no cuesta menos de lo que cuesta siempre, el cartel no dice la
verdad.

**`oferta_sospechosa` no sirve todavia, y conviene saberlo.** `core/derive.py`
calcula ademas ese campo, que es mas exigente: marca el caso feo de verdad, subir
el precio normal justo antes de anunciar la oferta. Compara con `shift(45)`, o
sea con el precio base de hace 45 dias, y hoy hay **trece dias de historico**:
sale `False` en las 593.509 filas. No esta roto, esta **dormido**, y despierta
solo cuando la serie llegue a los 45 dias. Basar la pantalla en el habria sido
ensenar una pantalla vacia durante seis semanas sin que nadie supiera por que.

---

## 3. Lo que destapo la pantalla: 1.244 ofertas de tarjeta contadas como rebajas

Al mirar lo que salia en el verificador aparecio esto, una y otra vez:

    alcampo    PESCANOVA Preparado de paella    "Club Alcampo 10% dto acumulado en tu tarjeta"
    alcampo    SPONTEX Bayeta absorbente        "Club Alcampo 20% dto acumulado en tu tarjeta"
    carrefour  ...                              "2x1 Acumula"

El descuento de tarjeta **no baja lo que pagas en caja**, y esa regla lleva
escrita desde el principio del proyecto. Lo que no estaba era aplicada a todos:
solo DIA publica un campo para decirlo (`only_club_dia`), asi que solo DIA tenia
`promo_club` puesto. Medido sobre el catalogo entero:

| cadena | promociones de tarjeta | marcadas |
|---|---:|---:|
| alcampo | 573 | 0 |
| carrefour | 869 | 0 |
| dia | 198 | 198 |
| **sin marcar** | **1.442** | |

Mil doscientas cuarenta y cuatro ofertas que se anunciaban como rebajas y en el
ticket no bajaban un centimo.

Lo mas irritante es que **el proyecto ya sabia leerlo**: `core/promos.py` tiene
`_ACUMULA = re.compile(r"acum|tarjeta|club|monedero|cheque|cupon|vale")` y
`Mecanica.acumulable`, y `Mecanica.util` ya las excluye del calculo de la cesta.
El conocimiento estaba; lo que no llegaba era la **columna** que mira la busqueda.
Es el patron de siempre: un dato que no cruza la frontera no existe.

Arreglado en `pipeline._marca_ofertas_de_tarjeta`: donde la cadena lo declara
manda la cadena, y donde no, manda el texto.

**Ojo al relanzar**: los recuentos de "con oferta" de la busqueda van a bajar en
la proxima ejecucion, y es que estaban mal. No es una perdida de datos.

---

## 4. Lo que falta

- **`solo_online`** (backlog N17). En el verificador salen ya textos como
  *"5€ dto. comprando 20€ en Nestle. Exclusivo Online"*. Un descuento que no
  existe si vas a la tienda es el mismo caso que el de la tarjeta, y todavia
  entra en el total. (Ojo: esos textos ya **no se acusan** en el verificador, porque
  dicen "comprando" y el descuento depende de cuantas unidades compres. Lo que falta
  es no contarlos como oferta en la cesta.)
- ~~**Distinguir el texto que no es una oferta.**~~ — **hecho el 24 de septiembre de
  2026**, ver §5.3.
- ~~**La pantalla en la app.**~~ — **hecha el 24 de septiembre de 2026**: la pestaña
  **Ofertas dudosas** del panel nuevo (`plataforma/web/app/src/paginas/Panel.tsx`), con
  la misma frase del servidor (`por_que`) antes que el precio y una regla de 90 días.

---

## 5. Lo que aparecio al pintarlo: la pantalla acusaba con numeros que no eran suyos

El 24 de septiembre de 2026 se pintaron por primera vez las tres pantallas del panel
que le faltaban a la interfaz nueva. La de ofertas dudosas encabezaba así:

```
Ampollas en stick anti-fricción Compeed 8 ml.
anuncia oferta y hoy cuesta mas que su precio de siempre
1.306,25 €/l  hoy · su precio de siempre 10,45 €/l
```

Eso no es una oferta dudosa: es **una cantidad mal leída**. El envase se leyó un día
como **una unidad** (1.045 céntimos, el precio del envase leído como si fuera por
litro) y otro como sus **8 ml** (349 céntimos / 0,008 l = 130.625 céntimos/l). Los dos
números no son del mismo producto. Y no era un caso suelto: **ordenada por
`posicion_90d`, las diez primeras eran de esa familia**.

### 5.1 La ventana de `core/derive.py` era del producto, no de su unidad

Todas las columnas derivadas (`precio_base_cent`, `min/max_90d`, `posicion_90d`,
`descuento_real`) comparan un precio con los suyos anteriores, y **un precio por litro
no se puede comparar con uno por unidad**: es la misma regla que ya sigue el resto del
proyecto. Medido sobre el gold de ese día: **2.239 productos tienen más de una unidad
en su historial**.

Partiendo la ventana por `unidad_canon`, sobre el mismo gold:

| | antes | después |
|---|---:|---:|
| ofertas acusadas con hoy > 3× su base | 337 | **17** |
| productos con un rango de 90 días > 3× | 3.175 | **1.694** |
| "el más barato de sus 90 días" cuya unidad cambió | 150 | **101** |

Un producto que cambia de unidad **empieza de cero en la nueva**: su base tarda en
existir y hasta entonces dice «no lo sé» en vez de inventar una comparación.

### 5.2 Y lo que quedaba era la cantidad, no la unidad

Los 17 que seguían saliendo tenían la misma unidad y **otra cantidad declarada**: el
mismo envase leído como 2,0057 kg un día y como 0,2 kg otro (un 10× exacto). Eso ya no
es cosa de `derive.py`: es que la comparación **no habla del mismo producto**. El
control que hacía falta **ya existía en este mismo fichero** para las bajadas
(`TOLERANCIA_CANTIDAD`, §1.2), y no estaba puesto en el verificador de ofertas. Ahora
sí, y con la misma tolerancia del 2 %.

### 5.3 Y el 63 % de la lista no se podía juzgar de ninguna manera

Al contar por qué salían tantas, apareció lo gordo. De las **5.488** ofertas anunciadas
cuyo precio de hoy no baja de su precio de siempre:

| familia | cuántas | qué son |
|---|---:|---|
| `por_varias_unidades` | **3.658** | el descuento depende de cuántas compres: `3x2` (2.195), `2ª unidad -50 %` (848+…), `Todo a 1 €` (653), lote, pack, "comprando 20 €" |
| `sin_descuento_de_precio` | **288** | el texto no anuncia un descuento de precio: "En pack, más fácil", "Stock Fuera (Unidades Limitadas)", "Novedad Alcampo", "Producto en Folleto" |
| `cantidad_cambiada` | **4** | el tamaño declarado cambió dentro de la ventana |
| **se juzgan** | **1.538** | descuentos sobre el precio de **esta** unidad |

**Un 3x2 no baja el precio de una unidad, baja el de la tercera.** Decir "anuncia
oferta y hoy cuesta más que su precio de siempre" es verdad y no significa nada: el
descuento no está donde lo buscamos. Acusar a esas 3.658 era un error de la pantalla,
no una mentira de la cadena.

Así que el verificador juzga **sólo** lo que anuncia un descuento sobre el precio de
ese producto, y **cuenta y dice** lo que deja fuera, por motivo
(`GET /api/ofertas-dudosas` → `sin_poder_juzgar`). Es la regla de siempre: un dato que
no tenemos es «no lo sé», y aquí el dato que falta es el precio normal de *ese*
producto.

### 5.4 Lo que sigue sin saberse

Con las tres cosas puestas, lo que queda en la lista es defendible (hoy cuesta más que
su mediana de 30 días, misma unidad y misma cantidad), pero **por qué** pasa eso no
está resuelto: hay textos como *"Todo a 1€ (14/09/2026 - 08/10/2026)"* en productos que
cuestan 1,70 € y no 1 €. Puede ser que el texto se pegue a productos a los que no
aplica, o que el precio no haya bajado. El control que lo contestaría
(`oferta_sospechosa`: subir el precio normal justo antes de la oferta) **sigue dormido**
hasta los 45 días de histórico (§2). Hasta entonces, la frase que se enseña es la que
los datos sostienen, y ni una más.

