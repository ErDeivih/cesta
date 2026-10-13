# B03 · **Lidl llega a silver** -- y no aparece en `/api/estado`, que es lo siguiente

*(13 de octubre de 2026. **El primer desenlace de los dos que se dejaron dichos: el bueno, y con una segunda
mitad.**)*

## 1. El pipeline lo cogio, y sin tocar el esquema

```
pipeline: cargando bronze...
  1651966 filas, 6 cadenas
    alcampo 2026-10-13 · aldi · carrefour · dia · LIDL · mercadona
  silver: 51725 filas de 6 cadenas
  gold: 1652509 filas de historico, 37 dias acumulados
```

*Y en el disco:*

```
data/silver/fuente=alcampo  aldi  carrefour  dia  LIDL  mercadona
```

> **`_cargar_bronze` une «todos los parquet de bronze», y asi fue: Lidl entro por donde entran todas.** *No
> hubo que tocar el esquema, que era el segundo desenlace posible.* **Asi que el recorrido bronze -> silver ->
> gold de Lidl esta HECHO.**

## 2. Y no aparece en `/api/estado`, y eso **ya estaba dicho**

```
version: 20261013-132451 · fecha: 2026-10-13
  alcampo 22816 · aldi 2476 · carrefour 16149 · dia 5760 · mercadona 4168
```

**Cinco. Lidl no esta.** *Y en la ronda anterior quedo escrito, antes de correrlo:*

> *«**Lidl no va a aparecer como una sexta cadena «igual que las otras».** Aunque su silver salga bien:
> `CADENAS` sigue teniendo cinco, porque es la lista de las que **cierran una cesta**.»*

**Se cumplio, y era lo esperado.** *`/api/estado` informa por `CADENAS` -- las comparables --, y **Lidl no
esta en esa lista, con su motivo.***

## 3. Y aqui esta el trabajo que queda, con su forma exacta

**Lidl tiene dato y no tiene presencia.** *Y B03 pide que la tenga: «Integra Lidl ... en API/UI como sexta
fuente.»* **Pero no como una mas**, *que es lo que `cesta.py` protege.*

**Lo que corresponde**, y es el mismo patron de todo el paquete:

  1. **`/api/estado` informa de `CADENAS`** *y deberia informar **tambien de las capturadas que no comparan**,
     cada una con su cobertura y su `por_que_no_se_compara`.* **Asi Lidl aparece -- y aparece diciendo lo que
     es.**
  2. **Y con los numeros que importan, que no son `productos`.** *79 fichas de ofertas semanales al lado de
     22 816 de Alcampo **no son la misma clase de numero*** -- *y el campo `productos` no lo distingue.*
     **Lidl necesita sus propios campos: `cobertura: ofertas_semanales_parcial`, `con_precio: 77` de `79`, y
     el `aviso`** -- *que ya se escriben en `data/cobertura/lidl-2026-10-13.json`.*
  3. **Y la interfaz tiene que poder decirlo** *sin que parezca que a Lidl le faltan productos.*

> **O sea: a Lidl no le falta un numero en una lista; le falta una FORMA de aparecer que diga que su catalogo
> es parcial.** *Que es exactamente lo que `por_que_no_se_compara` sabe decir, y lo que `CADENAS` separa.*

## 4. Y una cosa que el pipeline hizo y conviene decir

**Reescribio `docs/CIFRAS.md`** -- *«cifras: CIFRAS.md reescrito con los numeros de hoy».* **Es lo que el
pipeline hace siempre, y ese fichero esta entre los que el propietario tiene sin commitear.** *Asi que se
quedo reescrito por una ejecucion, no por una edicion mia* -- *y se dice, para que no parezca un cambio a
mano.*

## 5. Estado del paquete, con lo que queda

```
captura acotada                     HECHO
bronze publicado con zona           HECHO
cobertura por campo y contador      HECHO (data/cobertura/lidl-2026-10-13.json)
bronze -> silver -> gold            HECHO (silver de 6 cadenas)
veto global quitado                 HECHO (en_tienda admite lidl)
el motivo llega a la respuesta      HECHO (aviso en las tres respuestas)
/api/estado con Lidl y su cobertura PENDIENTE, y es lo que queda
region/club/fechas/nutricion        PENDIENTE de probar en el recorrido
06:00                               PENDIENTE (y el bronze ya lo haria entrar)
```

*Y la suite sigue en 2012 pasan, 0 fallan, y ruff limpio: el pipeline no toca codigo, toca datos.*
