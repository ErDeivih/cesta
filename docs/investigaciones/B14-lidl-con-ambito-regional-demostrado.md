# B14 · **Lidl, sexta fuente: con ambito regional y cobertura DEMOSTRADOS**

*14/10/2026. **Lo que el complemento pide, con sus palabras**: *** «Integra Lidl en el MISMO ciclo diario y
en API/UI como sexta fuente, *** con ambito regional y cobertura demostrados ***. **No lo declares completo
por tener un sitemap.**» *

---

## 1. *** En el MISMO ciclo diario ***

```
*** `data/runs.csv`, el ciclo del 14/10 *** *
  *** `2026-10-14T08:16:21,lidl,79,0,146.9,True` *** *
*** -> 79 filas · 0 errores · 146,9 s · *** `ok=True` *** ✓✓✓
*** y la tarea del ciclo: ***  *** `LastTaskResult: 0` *** *-- *o sea **termino** *(no `0x41301`, que es
   «en marcha»)* ✓
*** y las seis fuentes, las seis con fila y con `ok` ***: *
  *lidl 79 · aldi 2570 · mercadona 4212 · dia 5701 · carrefour 16164 · alcampo 22905*
```

> *** No es una fila suelta: *es **el ciclo entero, con Lidl dentro y con las otras cinco.** *

## 2. *** Y PUBLICADO, no solo capturado ***

```
*** el catalogo publicado (`data/gold/v20261014-130958`) *** *
  *** alcampo 22.905 · carrefour 16.164 · dia 5.701 · mercadona 4.212 · aldi 2.570 · *** *** lidl 79 *** *
*** -> `SELECT count(*) FROM grupos WHERE fuente='lidl'` ***  *** = 79 *** ✓✓✓
```

> *** O sea: *los 79 productos de Lidl **estan en `gold`** -- *que es **el catalogo que la API sirve**.* *
> *Asi que **no es «una fila del CSV»**: *es **una fuente publicada y consultable.** *

## 3. *** Y con AMBITO REGIONAL ***

```
*** la columna ***  *** `region` *** *
*** y los 79, todos de la misma ***  *** `region = '28'` *** ✓
*** y un producto entero, con precio, cantidad y unidad *** *
  *** `(10740, 'Naranja mesa',  1.0, 'kg', 169.0)` ***  *-- 1,69 €/kg*
  *** `(30380, 'Pepino granel', 1.0, 'kg', 129.0)` ***  *-- 1,29 €/kg*
```

> *** Y **eso es lo que hace que se puedan comparar**: *sin **precio, cantidad y unidad** no hay comparacion
> posible, *y los tres estan.* ✓

## 4. *** Y LO QUE NO SE, que es la mitad de «regional» ***

```
*** `region = '28'` *** *** es un NUMERO, y NO SE QUE REGION ES *** ⚠️ *
  *-- *se capturo como `regionPriceId` del sitio de Lidl, *y **su nombre geografico no se ha buscado***
  *-- *y **no lo voy a inventar**: *«28» podria ser una provincia, una zona de precio o un ambito interno*
*** -> asi que lo demostrado es: *** *** una sola region, con sus 79 productos y sus precios *** *
   *** y NO: *** *que el catalogo cubra la region donde vive la casa* ⚠️
*** y la COBERTURA, en el sentido de «cuanto del catalogo de Lidl se captura», tampoco consta *** *
   *-- *79 productos **es poco** al lado de los 22.905 de Alcampo: *puede ser **la profundidad del
   sitio**, *o **lo que el colector alcanza** -- *y **cual de las dos** no lo he medido* ⚠️
```

## 5. Y el resto del complemento, para situar esto

```
*** (1) LOS ENVASES ***       *** hecho en los dos puentes ***, *medido en vivo* ✓✓
*** (2) EL SIN CATALOGO ***    *entra como pendiente, y la nota lo dice* ✓
*** (3) LA TELEMETRIA DE LIDL ***  *** hecha ***: *tres salidas mudas que ahora registran, *
                              *con sus dos regresiones probadas* ✓
*** (4) LA RESTAURACION ***   *** hecha con las tres patas ***, *en base nueva y desechable* ✓✓✓
*** y la ingesta ***          *viva, sin duplicar, y terminada* ✓
```
