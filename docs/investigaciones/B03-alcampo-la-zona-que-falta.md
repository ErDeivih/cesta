# B03 · **Alcampo: la zona que falta**, y hasta donde se puede llegar sin inventar

*(13 de octubre de 2026. **El segundo caso del defecto, medido sobre el bronze que ya existe.**)*

## 1. Lo que hay: una constante usada en un solo sitio

`projects/cesta/collectors/alcampo.py`:

```
linea  36:  REGION = "ac90d761-9d58-4918-a37d-dd14e1ce384a"   # peninsula
linea 310:  f"?searchTerm=&limit=20000&regionId={REGION}")
```

**Dos lineas en 670.** *La region se declara una vez, se usa en una URL de busqueda, **y no se descubre en
ninguna parte del fichero*** -- *no hay endpoint de regiones, ni lectura de config, ni nada.*

> **Asi que es el mismo caso que Lidl, y en la forma mas pura**: *una zona elegida una vez, **nunca dicha**, y
> **nunca comprobada**.*

## 2. Y lo que se puede saber del bronze que ya existe

*Se miro el crudo mas reciente de Alcampo (**891 KB**), sin pedir nada por red:*

```
regionId     : 6 apariciones
region       : 18 apariciones
postalCode   : 3 apariciones
storeId      : 0 apariciones
warehouse    : 0 apariciones

regionIds DISTINTOS en el dato: 1
  ac90d761-9d58-4918-a37d-dd14e1ce384a
```

**Un solo `regionId`, que es el que se pidio.** *Logico: se pidio la peninsula y se recibio la peninsula.*
**Asi que el bronze no puede decir que otras zonas existen** -- *no porque no existan, sino porque **no se
pregunto por ellas**.*

> *Y esa es la distincion de siempre: **una aparicion no es un catalogo, y su ausencia no es una prueba de que
> no haya mas.***

## 3. Y `postalCode` aparece tres veces -- pero **no como dato**

*Se miro el contexto de las tres, y son **cadenas de traduccion de la interfaz**:*

```
"accessibility.delivery.destination.temporary.home.button": "Seleccionar entrega a {postalCode}"
"address.form.field.postalCode": "Codigo postal"
"addresses.manual-form-map.postalCode": "Codigo postal"
```

**Son las etiquetas de la web, no valores.** *Asi que el crudo **no trae** el codigo postal que se uso.*

### Pero dicen algo, y es lo que hacia falta saber

**«Seleccionar entrega a {postalCode}» quiere decir que la web de Alcampo TIENE un selector de entrega por
codigo postal.** *O sea:*

  - **Alcampo si resuelve la zona a partir de un CP** -- *como Mercadona;*
  - **y el `regionId` sale de esa eleccion**, *no de una lista fija;*
  - **pero la correspondencia `CP -> regionId` NO esta en la captura**, porque *la captura es de la
    busqueda, no del selector.*

> **Asi que para derivar la region de Alcampo del CP hay que capturar la respuesta del selector** -- *una
> captura acotada, como la de Lidl, y por el mismo criterio: **primero se mira, y despues se escribe.***

## 4. Y lo que **no** se va a hacer

**No se va a probar `regionId`s a ciegas contra su API.** *Serian peticiones a un endpoint de busqueda con
identificadores inventados* -- *y **eso es sondear a ver si suena**, que es lo contrario de acreditar.*

**No se va a poner `config.CODIGO_POSTAL` en la URL de Alcampo.** *Un CP **no es** un `regionId`* -- *ni aqui
ni en Lidl* --, *y ponerlo «a ver si funciona» es exactamente lo que el plan prohibe: «no convertir CP en id
de region sin correspondencia».*

**Ni se va a copiar la constante de Lidl.** *Son formatos distintos: Lidl usa numeros («28»), Alcampo usa un
UUID. **Parecerse no es corresponder.***

## 5. Asi que Alcampo queda **medido y dicho**, no arreglado

  - **el defecto esta localizado**: *`REGION`, linea 36, usada en la 310.*
  - **es del mismo tipo que el de Lidl**, *y por eso tiene la misma solucion: acreditar la correspondencia.*
  - **y falta el dato que la acredita**: *la respuesta del selector de entrega por CP.*
  - **y no se ha inventado nada** para taparlo.

> *Y decir esto es mas util que un arreglo a medias*: **quien siga con B03 sabe exactamente que capturar, por
> que, y que no hay que hacer mientras tanto.**
