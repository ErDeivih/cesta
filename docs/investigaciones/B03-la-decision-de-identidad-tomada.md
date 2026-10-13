# B03 · **La decision de identidad, tomada**: la zona entra en la clave

*(13 de octubre de 2026. **La disyuntiva que quedaba abierta, resuelta con la respuesta del propietario delante
-- y no con una opinion.**)*

## 1. La disyuntiva, y las dos respuestas

```
clave_de(fuente, id_fuente)                    <- hoy: el mismo producto en dos zonas es EL MISMO
clave_de(fuente, id_fuente, region)            <- y la otra: son DOS DISTINTOS
```

*Y las dos son legitimas, y tienen consecuencias distintas:*

| | **sin la zona en la clave** | **con la zona en la clave** |
|---|---|---|
| un producto en dos zonas | **es uno** | **son dos** |
| y la comparacion | *tiene que elegir entre dos precios de zonas distintas* | *compara como con cualquier otro* |
| y un cambio de `SCRAP_CP` | *no cambia ninguna identidad* | *renueva las identidades de esa cadena* |
| y la herencia (`estabiliza`) | *no se entera* | *lo ve como productos nuevos* |

## 2. Y la respuesta del propietario decide, y es la que el encargo ya tenia

*Cuando se le pregunto por la region de Lidl, respondio:*

> *«**Que dependa de la region que elija el usuario**, o en la que se encuentre en ese momento.»*

**«Que dependa de la region».** *No «que se pueda elegir», no «que se muestre»: **que el precio dependa de
ella**.* **Y de ahi sale la consecuencia, y es una sola:**

> **Un precio de la zona A y un precio de la zona B no son el mismo hecho.**
>
> *Y por tanto **no pueden ser la misma entrada**: si lo fueran, la aplicacion tendria **un `grupo_id` con dos
> precios validos y de zonas distintas**, y **tendria que elegir uno** -- *que es exactamente lo que el plan
> prohibe:* **«comparar precios validos de articulos observados sin presentar ausencias de captura como
> indisponibilidad»**. *Presentar dos zonas como una sola es presentar una ausencia -- la de la zona -- como si
> no importara.*

**Asi que la zona entra en la clave.** *No por elegancia: **porque el dato que el propietario pidio -- que el
precio dependa de su zona -- no se puede servir de otra forma sin mentir.***

## 3. Y la consecuencia que daba miedo **es correcta, y ademas se dice**

*Era esta:* **un cambio de `SCRAP_CP` renovaria todas las identidades de esa cadena en `estabiliza`.**

> **Y mirado del derecho, es lo que tiene que pasar**: *si alguien cambia de zona, **su catalogo de Lidl es
> otro** -- otros precios, otras ofertas, otro club.* *Que las identidades se renueven **es el sistema diciendo
> la verdad**: lo de antes era de otra zona.*
>
> **Lo que hay que hacer no es evitarlo: decirlo.** *Y ya hay donde*: **la cobertura del dia lleva `region`**
> (`data/cobertura/lidl-2026-10-13.json`, con su `\"region\": 28`), *asi que un cambio de zona se ve en el
> fichero de cobertura y en el `region` de cada fila.*
>
> *O sea que **el «problema» de la herencia no es un problema: es la senal de que la zona cambio**, y lo unico
> que falta es que alguien lo lea y lo diga.* **Que es la misma forma que `sin_cantidad`, `sin_consolidar` y el
> `aviso` de la cobertura: lo que pasa, dicho.**

## 4. Asi que la decision, escrita

```
LA ZONA ENTRA EN LA CLAVE.

  clave_de(fuente, id_fuente, region)     -- con la zona DENTRO, no como atributo

  y la consecuencia, aceptada y dicha:
  un cambio de SCRAP_CP renueva las identidades de esa cadena,
  y eso ES CORRECTO: su catalogo de esa cadena es otro.
  Se ve en la cobertura del dia -- que ya lleva `region`.
```

**Y queda descartada la otra opcion, con su motivo**: *dejar la zona como atributo daria grupos con dos zonas y
el mismo id, y **la comparacion elegiria por precio entre dos zonas** -- que es la mentira que B03 lleva toda la
sesion evitando.*

## 5. Y lo que queda, que ya es escribir codigo

  1. **`clave_de(fuente, id_fuente, region)`** *-- y quien la llama le pasa la zona.*
  2. **`region` en las filas de `grupos.parquet`** *-- y la vista `grupos` la expone sola.*
  3. **`region` al final del `SELECT` de `donde_comprar`** *-- probado que no mueve indices.*
  4. **Y la regla de la comparacion**: *comparar solo dentro de la misma zona, y decir cuando no hay con quien
     comparar.* *Que es lo que el plan pide: «Lidl no gana una cesta completa si faltan lineas; si puede ofrecer
     una linea exacta con precio valido».*

> **Y el paso 1 no se hace sin el 2**: *una firma con un parametro que nadie pasa es **una pieza correcta que
> nadie llama** -- el `por_que_no_se_compara` otra vez.*

## 6. Y con esto, B03 tiene su ultimo paso decidido y no medido

**Siete medidas y una decision.** *Y la decision no es mia: **es la consecuencia de lo que pidio el
propietario**, leida con el plan delante.* *Que es la forma en que este encargo pide que se decidan las cosas
que no se pueden medir.*
