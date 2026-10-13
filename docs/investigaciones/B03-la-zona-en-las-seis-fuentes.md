# B03 · **La zona en las seis fuentes** -- la respuesta a la pregunta del propietario

*(13 de octubre de 2026. **«Verifica si esto le pasa a mas supermercados o solo a Lidl.» Y le pasa a cuatro
de seis, y aparece un segundo caso identico al de Lidl.**)*

## 1. La tabla, medida fuente por fuente

| fuente | zona | de quien es | estado |
|---|---|---|---|
| **mercadona** | `config.CODIGO_POSTAL` | **del usuario** | ya estaba bien |
| **aldi** | `config.ALDI_SCOPE` (`es_pen`/`es_bal`/`es_can`) | **del usuario** | ya estaba bien |
| **lidl** | `regionsV2` -- 55 regiones | *era la constante «28»* | **arreglado hoy**: sale del CP |
| **alcampo** | `regionId` en la URL | *es la constante `«…384a» # peninsula`* | **PENDIENTE, y es el mismo defecto** |
| **carrefour** | *no usa zona* | -- | *no aplica* |
| **dia** | *no usa zona, y con motivo* | -- | *no aplica* |

## 2. Y en Alcampo esta el mismo defecto, palabra por palabra

`projects/cesta/collectors/alcampo.py`:

```python
REGION = "ac90d761-9d58-4918-a37d-dd14e1ce384a"   # peninsula
```

*Y esa constante va a la API, en la linea 310:*

```python
f"?searchTerm=&limit=20000&regionId={REGION}"
```

> **Asi que Alcampo SI tiene precios por zona** -- *su API los pide por `regionId`* -- **y el colector los pide
> siempre de «peninsula».** *Es literalmente el mismo caso que el `REGION_POR_DEFECTO = "28"` de Lidl, con
> otro nombre:* **una zona elegida una vez y nunca dicha.**
>
> *Y la consecuencia es la misma que tenia Lidl*: **quien viva en Canarias o en Baleares vera precios de la
> peninsula, sin que nada lo diga.** *Y al contrario: las zonas que Alcampo publica y no se piden, no
> existen para la aplicacion.*

## 3. Y las dos que no lo usan lo dicen

**DIA** lo explica, *y el motivo es bueno*:

> *«...postal: un domicilio social no es un origen, y ponerlo ahi seria...»*
> *«Se prefiere el pais cuando lo dice («Union Europea», «Espana») y, si no, el fabricante, que al menos dice
> quien lo hace. No se mezcla con la direccion...»*

**O sea: DIA no tiene precio por zona, y en vez de rellenar el campo con la direccion de la sede, lo deja**
-- *que es la misma regla que todo lo demas: **lo que no consta no se rellena.*** **Y `dia.py:264` lo deja
escrito para que no se «arregle» por error.**

**Carrefour** solo menciona «tienda» en un comentario sobre plantillas de pagina (*«paginas de marca o
"tienda", que usan otra plantilla»*), *no sobre precios por zona.*

## 4. Asi que la respuesta, y lo que implica

**No es solo Lidl: es Lidl y Alcampo**, *y los dos por el mismo motivo* -- **una zona fijada como constante en
vez de leida de la del usuario.**

**Y dos ya lo hacian bien** (`mercadona`, `aldi`), *con la variable que el propietario pide:*
`config.CODIGO_POSTAL` **y** `config.ALDI_SCOPE`.

> **Asi que el patron no hay que inventarlo: hay que terminarlo.** *Dos fuentes ya leen la zona del usuario,
> una se ha arreglado hoy, y **queda Alcampo** -- que necesita lo mismo que Lidl: saber que zonas publica, y
> acreditarlas desde el CP en vez de suponer la peninsula.*

**Y queda una cosa mas, que el propietario pidio de paso**: *«o en la que se encuentre en ese momento»*.
*Eso es geolocalizacion, y **no se va a hacer por IP ni por nada que el usuario no haya dicho*** -- *la regla
de esta fase es que la zona la elige quien la sufre, no el servidor.* **Asi que la zona es una preferencia
declarada y guardada, y la aplicacion dice cual esta usando.** *Si algun dia se anade «detectarla», tendra que
ser con permiso explicito y con el mismo criterio: **decir cual se uso, y poder cambiarla.***

## 5. Lo que queda para cerrarlo

  - **Alcampo**: ver que `regionId`s publica su API, y derivar el del CP acreditandolo -- *como Lidl*.
  - **Lidl**: ya hecho.
  - **Y en la interfaz**: *que se vea **de que zona** es el precio que se esta mirando.* *Un precio sin su
    zona no se puede comparar* -- *y compararlo con otro de otra zona seria el error que todo esto evita.*
