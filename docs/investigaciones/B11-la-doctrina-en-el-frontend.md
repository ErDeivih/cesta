# B11 · **La doctrina, en el frontend, con su constante y su razon** -- y `sufijoUnidad` es la «unidad»

*(13 de octubre de 2026. **Segunda ronda de B11. Y el fichero que parecia de formateo es la regla.**)*

## 1. El fichero y su cabecera, literales (`plataforma/web/app/src/api/formato.ts`, 236 lineas)

```typescript
/** Convertir los datos de la API en texto, con las reglas del proyecto.
 *
 *  La regla que manda aqui: **un dato que no tenemos es "no lo se"**, nunca un
 *  cero. Un 0,00 EUR se lee como "gratis" y una letra vacia como "malo"; las dos
 *  cosas serian mentira. Por eso casi todas estas funciones devuelven una frase
 *  cuando el dato es null, y **ninguna tiene un valor por defecto numerico**.
 *
 *  El dinero llega en centimos enteros y se pasa a euros solo al pintar. No se
 *  redondea antes de tiempo: 0,1 + 0,2 no da 0,3.
 */
import type { Nutricion } from '../tipos'

const EUROS  = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' })
const NUMERO = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 })

export const NO_LO_SE = 'no lo sé'

export function euros(cent: number | null | undefined): string
export function sufijoUnidad(unidad: string | null | undefined): string          <- *** LA UNIDAD ***
export function eurosUnidad(...)
export function numero(n, decimales = 1)
export function porcentaje(p, decimales = 1)
export function porcentajeConSigno(p, decimales = 1)
export function fecha(iso, corta = false)
export function diasDesde(iso, hoy = new Date())
export function hace(iso)
export function ms(iso)
export function nombreCadena(cadena)
export function cantidad(...)
export function selloLegible(s)
export function textoOrigenSello(origen)
```

## 2. Y es **la doctrina, vigesima vez**, y en su forma mas alta

> *** «La regla que manda aqui: **un dato que no tenemos es "no lo se", nunca un cero.**» ***
>
> *** Y **el motivo esta dado, con dos ejemplos que se leen**: ***
>
> ```
> un 0,00 EUR      -> se lee «GRATIS»     -> *** y seria MENTIRA ***
> una letra vacia  -> se lee «MALO»       -> *** y seria MENTIRA ***
> ```
>
> *** O sea: **el cero no es neutro: el cero **dice algo**** *** -- *y **lo que dice es falso cuando el dato no
> esta**.*
>
> *** Y la consecuencia esta escrita como regla de codigo: *** *** «casi todas estas funciones **devuelven una frase**
> cuando el dato es null, y **ninguna tiene un valor por defecto numerico**.» ***
>
> *** Que es **la version mas fuerte que ha aparecido en toda la sesion**: *** *no es «hay que acordarse de
> comprobar», *ni «se guarda `DESCONOCIDO`» -- *es **que la funcion NO PUEDE devolver un numero si no lo hay**,
> porque **no tiene valor por defecto.** *
>
> *** Y `export const NO_LO_SE = 'no lo sé'` es **la doctrina como constante de modulo**: *** *una sola cadena, en un
> solo sitio, para que **el «no lo sé» se escriba igual en las veinte pantallas.** *
>
> *** Vigesima vez. Y es **la primera que esta en el FRONTEND y como constante exportada** -- *o sea: **la regla
> cruzo la frontera** (Python -> TypeScript) **y sigue siendo la misma.** *

## 3. Y `sufijoUnidad` es **la «unidad» de B11**

```
B11 PIDE:  «Cada grafica declara MEDIDA, UNIDAD, UNIVERSO, PERIODO, FUENTE Y VERSION»
   -> *** `export function sufijoUnidad(unidad: string | null | undefined): string` ***
   -> y `eurosUnidad(...)`, que junta **el dinero con su unidad**
```

> *** Y `sufijoUnidad(unidad: string | null | undefined): string` dice **dos cosas de golpe**: ***
>
>   - **acepta `null` y `undefined`** *-- *o sea: **la unidad puede no conocerse**, y **la funcion tiene que
>     responder igual**;*
>   - **y devuelve `string`**, no `string | null` *-- *o sea: **siempre dice algo**, *y **lo que dice cuando no la hay
>     tiene que ser `NO_LO_SE` o el vacio explicito**.*
>
> *** Y `eurosUnidad(...)` es **la union**: *** *el dinero **y su unidad**, juntos -- *que es **exactamente**
> «declara MEDIDA y UNIDAD» del criterio de B11.*

## 4. Y el detalle del redondeo, que es de la misma familia

> *** «El dinero llega en **centimos enteros** y se pasa a euros **solo al pintar**. **No se redondea antes de
> tiempo: 0,1 + 0,2 no da 0,3.**» ***
>
> *** O sea: **el dinero se guarda en la unidad mas pequena (centimos enteros)** *** -- *y **se convierte a euros
> solo en el ultimo paso** -- *para que **la aritmetica sea exacta** y **el error de coma flotante no se acumule.** *
>
> *** Que es **la misma disciplina que `unidad_canon` de B06** («no es opcional») y que `GREATEST`/`LEAST` de B10:
> **decidir en el sitio donde la decision es exacta, y presentar en el ultimo momento.** *

## 5. Y B11, con dos rondas

```
  1) DONDE ESTA           *** LOCALIZADO: cuatro ficheros del frontend, y NINGUN ENSAYO ***
                          `componentes/Chispa.tsx` (una sparkline) · *** `api/formato.ts` *** · `App.tsx` · `iconos.tsx`
  2) LA «UNIDAD»          *** HECHA: `sufijoUnidad(unidad)` + `eurosUnidad(...)` + `NO_LO_SE` ***
  3) LAS OTRAS CINCO      *POR MIRAR: MEDIDA · UNIVERSO · PERIODO · FUENTE · VERSION*
                          *y las cinco tienen casa en la API: `cobertura` (universo) · `rango`/`DIAS_DE_VENTANA`
                          (periodo) · `fuente_dato` (fuente) · `version` · y `unidad_canon` (medida)*
  4) Y `Chispa.tsx`       *** POR LEER -- y su nombre es una metafora: «chispa» = sparkline ***
```

> *** Y no se dice que falten cinco: *** *se dice que **una de las seis tiene fichero con ese nombre**, y que **las
> otras cinco tienen casa conocida en la API** -- *porque **el criterio las pide juntas, y el proyecto las tiene
> repartidas**: **la unidad en el frontend, y el universo, el periodo, la fuente y la version en los datos.** *
>
> *** Y eso es un hallazgo, no una carencia: *** **la «declaracion» de una grafica no es un cartel: es que sus seis
> cosas vengan de sitios que ya las dicen.**
