# B11 · **`Chispa.tsx`: la grafica que se NIEGA a dibujar** -- y dice por que

*(13 de octubre de 2026. **Tercera ronda de B11. Y la clausula «declara MEDIDA y UNIDAD» tiene su respuesta.**)*

## 1. Lo que hay, literal (`componentes/Chispa.tsx`)

```typescript
/** La chispa del historico: una serie de precio POR UNIDAD, sin ejes. */

export type { PuntoChispa } from '../logica/chispa'

export function Chispa({ puntos, alto = 40, color = '#0369a1', etiqueta }: Props)

// **Si la serie mezcla unidades, no se dibuja una linea que las junte.** Mismo [producto...]
const unidades = serieDeChispa(puntos)
if (!unidades.dibujable && unidades.motivoUnidad) {
  return <p className="text-xs text-tinta-suave">{unidades.motivoUnidad}</p>
}
```

## 2. Y contesta la clausula (3) de B11 -- **«declara MEDIDA y UNIDAD»** -- de la forma mas fuerte

```
B11 PIDE:  «Cada grafica declara MEDIDA, UNIDAD, UNIVERSO, PERIODO, FUENTE Y VERSION»
```

> *** Y `Chispa` no **declara** su unidad en un cartel: *** *** se NIEGA A DIBUJAR SI LA SERIE MEZCLA UNIDADES. ***
>
> *** «Si la serie mezcla unidades, **no se dibuja una linea que las junte**.» ***
>
> *** O sea: **el problema no se resuelve etiquetando mal una linea: se resuelve NO DIBUJANDOLA** *** -- *porque
> **una linea que junta euros y kilos es una mentira**, *y **una etiqueta no la arregla.** *
>
> *** Y hay **una segunda cosa** en esas cuatro lineas, y es la misma que en B07: ***
>
> ```
> const unidades = serieDeChispa(puntos)
> if (!unidades.dibujable && unidades.motivoUnidad) { ... }
> ```
>
> *** O sea: `serieDeChispa` devuelve **un veredicto Y UN MOTIVO** (`dibujable`, `motivoUnidad`) *** -- *que es
> **exactamente** `Permiso(ok, reason)` de `importar_receta.comprueba_fuente` (B07) y `_presentacion(a, b) ->
> tuple[bool, list[str]]` de `identidad.py` (B09).*
>
> *** Tercera vez: **el «no» con su motivo**, y aqui con **la razon en la pantalla**: *** *`{unidades.motivoUnidad}`
> **se pinta**, no se registra -- *o sea: **la persona lee por que no hay grafica.** *

## 3. Y la primera linea contesta **la MEDIDA y la UNIDAD juntas**

> *** «Una serie de **precio por unidad**» ***
>
> *** O sea: **la MEDIDA es el precio, y la UNIDAD es la del producto** *** -- *y **las dos estan dichas en la primera
> linea del fichero**, que es **el docstring del componente.** *
>
> *** Y **`sin ejes`** es lo tercero: *** *una sparkline **no lleva ejes** -- *y **el docstring lo dice**, para que
> nadie le pida a esa grafica **una precision que no tiene.** *
>
> *** O sea: *** *** `Chispa` declara **MEDIDA** (precio), **UNIDAD** (la del producto) y **lo que NO es** (sin
> ejes) -- *y **se niega a dibujar cuando la unidad no es una.** *
>
> *** Y **el UNIVERSO, el PERIODO, la FUENTE y la VERSION** no son de la chispa: *** *son **de los datos que le
> llegan** (`puntos`), *y **cada uno tiene su sitio**: `cobertura` (universo), `rango`/`DIAS_DE_VENTANA` (periodo),
> `fuente_dato` (fuente), y `version`.* *

## 4. Y hay **una tercera pieza** que no se ha leido, y hay que decir cual

```
POR LEER:
  *** `plataforma/web/app/src/logica/chispa.ts` *** -- *** el modulo que produce `dibujable` y `motivoUnidad` ***
  y `core/`? -- *no: el import es `../logica/chispa`, o sea **tambien del frontend**.*
```

> *** Y es **el sitio donde tiene que estar la regla**: *** *el componente **pinta**, y **la logica decide** --
> *`serieDeChispa(puntos)` devuelve **si se puede dibujar y por que no**.*
>
> *** Y por eso **el siguiente paso esta claro**: *** *`logica/chispa.ts`, *que es **el tercer modulo de la familia**
> (junto a `api/formato.ts` y `componentes/Chispa.tsx`) **y el unico que no se ha abierto.** *

## 5. Y B11, con tres rondas

```
  1) DONDE ESTA           LOCALIZADO -- cuatro ficheros del frontend, y NINGUN ENSAYO
  2) LA «UNIDAD»          *** HECHA, y en dos sitios: *** `sufijoUnidad`/`eurosUnidad`/`NO_LO_SE` en
                          `api/formato.ts`, *** y la negativa a dibujar en `componentes/Chispa.tsx` ***
  3) LA MEDIDA            *** HECHA: *** «una serie de precio por unidad» -- *y **`sin ejes`**, que es declarar
                          **lo que la grafica NO es** *
  4) UNIVERSO/PERIODO/
     FUENTE/VERSION        *de los DATOS, no de la chispa: `cobertura` · `rango`/`DIAS_DE_VENTANA` · `fuente_dato` ·
                          `version`*
  5) Y `logica/chispa.ts`  *** POR LEER -- el que produce `dibujable` y `motivoUnidad` ***
```

> *** Y la conclusion de B11 **no es «faltan graficas»**: *** *es que **la que hay (una sparkline) hace las tres
> cosas que el criterio pide mas dificiles**:*
>
>   1. **declara su medida y su unidad** (en el docstring);
>   2. **declara lo que no es** («sin ejes»);
>   3. *** y se niega a dibujar cuando la unidad no es una, diciendo por que. ***
>
> *** Y las otras cinco cosas del criterio **no son de la grafica**: son **de los datos que le llegan** *** -- *y
> **cada una tiene su sitio ya leido**, en cuatro modulos distintos.*
>
> *** Que es **el hallazgo de B11**: *** **«utiles, no decorativas» no se consigue poniendo un cartel debajo: se
> consigue que la grafica NO PUEDA decir algo que no sabe.** *
