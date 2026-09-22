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
  entra en el total.
- **Distinguir el texto que no es una oferta.** "En pack, más fácil" y
  "PROTEÍNA, CALIDAD, SABOR" estan en `promo_txt` y no anuncian ningun
  descuento. Hoy el verificador los saca como ofertas dudosas, y tecnicamente lo
  son -- anuncian algo y el precio no baja -- pero lo honesto es separarlos.
- **La pantalla en la app.** Los dos endpoints estan y devuelven datos; la
  interfaz de `plataforma/web` todavia no los pinta.
