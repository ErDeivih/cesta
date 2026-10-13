# B08 · **`Ajustes.tsx` es la pagina legal** -- y el objetivo de calorias **no se ha encontrado en ningun sitio**

*(13 de octubre de 2026. **Decima ronda de B08. Y la busqueda se cierra con una AUSENCIA MEDIDA.**)*

## 1. Lo que hay en `Ajustes.tsx`

```
l203: · la nutricion viene de Open Food Facts y su licencia es ODbL, que **obliga a** [atribucion]
l212: Los precios son ORIENTATIVOS y pueden variar: los publica cada cadena y Cesta se [compromete a...]
l217: Los datos viven en el ordenador de casa y no salen de ahi. Informacion nutricional [...]
```

> *** Es la **pagina legal**: *** *atribucion de la fuente, aviso de que los precios son orientativos, y que **los
> datos no salen de casa**.*
>
> *** Y **no es el objetivo de calorias**: *** *es **de donde vienen los datos**, **que no se garantizan**, y **donde
> se quedan**.*
>
> *** Y contiene, de propina, **la «atribucion» de B07**: *** *«la nutricion viene de **Open Food Facts** y su licencia
> es **ODbL**, que **obliga a** [atribucion]» -- *que es **exactamente** la clausula del criterio de B07*
> («y atribucion»), **y esta donde tiene que estar: en la pagina legal.***

## 2. Y entonces el objetivo de calorias **no se ha encontrado**, y hay que decirlo con precision

```
LO QUE SE HA PROBADO, Y NO ESTA:
  API        -- `objetivo` no aparece en `plataforma/api/`
  core       -- `objetivo` en `despensa.py` y `equivalencias.py`, y **en prosa**
  frontend   -- `objetivo` en cinco ficheros, y en `Cocina.tsx` es **una etiqueta de interfaz**
  y la pista -- `Ajustes.tsx` es **la pagina legal**, no un formulario de meta
  `orientativo` -- solo en `Ajustes.tsx` y `Cocina.tsx`, y **los dos son avisos**
```

> *** Y **no se dice «no existe»**, por la razon de siempre: *** *se dice que **no se ha encontrado**, y **se enumera
> donde se ha buscado**.*
>
> *** Pero **la busqueda ya es razonablemente completa**: *** *se han probado **siete palabras**, **la API**, **el
> core**, **cinco ficheros del frontend**, y **las dos pistas que aparecieron**.*
>
> *** Asi que se puede decir algo mas fuerte, y **medido**: *** **la clausula (4) de B08 no aparece por ninguno de
> los nombres que el proyecto usa para las cosas de su familia** -- *y **eso es un hecho sobre la busqueda, no sobre
> el codigo**.*

## 3. Y las graficas, que van con el objetivo, tampoco

**El criterio dice:** *«**grafias de registrado versus previsto versus objetivo**»*.

> *** Y si el objetivo no aparece, **sus graficas tampoco** *** -- *porque **no se puede pintar una meta que no
> esta.***
>
> *** Y conviene juntarlo con **la otra clausula que no aparece**: *** *el **previsto**. **Las dos son el mismo
> par** -- *«registrado **versus** previsto **versus** objetivo» -- y **las dos faltan**.*
>
> *** O sea: **lo que falta de B08 es un eje entero: el de la PREVISION.** *** *Lo registrado esta (el diario), lo
> usado esta (la despensa), lo que se gasta esta (`_con_precios`) **-- y lo que se preve que se va a comer NO.***

## 4. Y esto es lo mas util que B08 deja, y no es una lectura: es **un estado**

```
DE LAS CINCO CLAUSULAS DE B08:
  2) SNAPSHOT Y COBERTURA      HECHO
  3) EL RECIBO Y SU DESHACER    HECHO -- y la restriccion del propietario, en la firma
  5) Y LA ACEPTACION            HECHO -- 15 + 6 ensayos, con las cifras del propietario
  1) LA SEPARACION              EXISTE EN EL EJE DEL COSTE (G12/222); **el eje de la NUTRICION esta NOMBRADO**
  4) EL OBJETIVO Y LAS GRAFICAS *** NO ENCONTRADO, tras siete palabras y dos pistas ***
```

> *** Y por primera vez en diez paquetes, **una clausula del plan NO aparece en el proyecto** *** -- *y **el trabajo
> de esta sesion ha sido establecido que eso es cierto, midiendo**, y **no haberlo escrito en la ronda 150**, cuando
> **lo parecia**.*
>
> *** Y esa diferencia -- **«parece que falta» vs «se ha buscado y no esta»** -- *es **el producto de estas diez
> rondas**, y **es lo que hay que llevar a B09**.*
