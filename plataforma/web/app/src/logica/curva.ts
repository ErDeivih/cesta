/** La frase que va debajo de la curva: lo que el historico tiene que decir.
 *
 *  Punto 3 del encargo, apartado 3: *"**La curva**, que ya existe, **con una frase
 *  debajo**: «lleva 14 dias a este precio» o «esta mas barato que en los ultimos 90
 *  dias»"*. La curva estaba desde el primer dia (`componentes/Chispa.tsx`) y la frase
 *  no existia: una linea que sube y baja, sin decir nada, es un adorno del dato
 *  (`Chispa.tsx:6` dice justo eso) y no una respuesta.
 *
 *  Las cuatro reglas que sigue, y por que:
 *
 *  1. **Nunca se dice "los ultimos 90 dias" si no los tenemos.** El historico de hoy
 *     son 18 dias. La frase dice **cuantos dias hay de verdad** -- *"de los 18 dias que
 *     tenemos"* --, porque un plazo que no se cumple es una mentira tranquila: suena
 *     mejor y no es verdad. Es la misma regla que el "no lo se" del resto de la app.
 *  2. **Si la unidad cambio por el camino, no hay frase.** `kg` un dia y `ud` otro dan
 *     un minimo que no significa nada; es exactamente lo que dice `api/alertas.py`:
 *     *"si la unidad cambio, no es una bajada"*. Cuando pasa, se dice por que.
 *  3. **El precio mas alto tambien es una respuesta.** «¿Esto esta caro?» se contesta
 *     igual de bien con *"es el precio mas alto de los 18 dias"* que con *"es el mas
 *     bajo"*, y ese caso se quedaba sin decir.
 *  4. **Con un solo dia no hay nada que decir**: lo dice la pantalla con un `Vacio`
 *     ("Solo tenemos un dia de este precio"), no una frase inventada.
 *
 *  No pinta nada: solo decide que se dice, para poder probarlo sin montar la pantalla.
 *  La misma separacion que `logica/frase.ts`.
 */
import { numero } from '../api/formato'

/** Un punto del historico tal como lo manda `/api/grupo`. */
export interface PuntoDeLaCurva {
  fecha: string
  /** Precio por unidad de ese dia, en centimos. La API lo manda nulo si no lo sabe. */
  precio_unidad_cent: number | null
  /** La unidad con la que se midio ese dia, si la API la manda. */
  unidad_canon?: string | null
}

export interface LoQueDiceLaCurva {
  /** La frase, o `null` si no hay nada honesto que decir. */
  frase: string | null
  /** Por que no la hay, cuando no la hay y hay algo que explicar. */
  motivo: string | null
}

const NADA: LoQueDiceLaCurva = { frase: null, motivo: null }

/** Cuantos dias seguidos, contando el ultimo, llevan el mismo precio. */
function diasAlMismoPrecio(puntos: ConPrecio[]): number {
  const ultimo = puntos[puntos.length - 1].precio_unidad_cent
  let seguidos = 1
  for (let i = puntos.length - 2; i >= 0; i -= 1) {
    if (puntos[i].precio_unidad_cent !== ultimo) break
    seguidos += 1
  }
  return seguidos
}

/** Un punto del que si sabemos el precio. */
type ConPrecio = PuntoDeLaCurva & { precio_unidad_cent: number }

/** Lo que hay que decir debajo de la curva. */
export function loQueDiceLaCurva(puntos: PuntoDeLaCurva[]): LoQueDiceLaCurva {
  // Dias con precio: un punto sin precio no cuenta ni para el minimo ni para el plazo.
  const con = puntos.filter(
    (p): p is ConPrecio => p.precio_unidad_cent != null && p.precio_unidad_cent > 0,
  )
  if (con.length < 2) return NADA

  // La unidad, si la API la manda: tres dias en `kg` y uno en `ud` son dos series
  // pegadas, y el minimo de las dos juntas no es el minimo de nada.
  const unidades = new Set(
    con.map((p) => p.unidad_canon ?? null).filter((u): u is string => Boolean(u)),
  )
  if (unidades.size > 1) {
    return {
      frase: null,
      motivo:
        `La unidad de este producto cambió en el histórico (${[...unidades].join(', ')}), ` +
        'así que el precio de esos días no se puede comparar con el de hoy.',
    }
  }

  const dias = con.length
  const ultimo = con[dias - 1].precio_unidad_cent
  const minimo = Math.min(...con.map((p) => p.precio_unidad_cent))
  const maximo = Math.max(...con.map((p) => p.precio_unidad_cent))
  const plazo = `de los ${dias} días que tenemos`

  if (ultimo <= minimo) {
    return { frase: `Es el precio más bajo ${plazo}.`, motivo: null }
  }
  if (ultimo >= maximo) {
    const mas = Math.round((100 * (ultimo - minimo)) / minimo)
    return {
      frase:
        `Es el precio más alto ${plazo}: un ${numero(mas)} % por encima del más bajo.`,
      motivo: null,
    }
  }

  const seguidos = diasAlMismoPrecio(con)
  if (seguidos >= 2) {
    return { frase: `Lleva ${seguidos} días al mismo precio.`, motivo: null }
  }

  const mas = Math.round((100 * (ultimo - minimo)) / minimo)
  if (mas >= 1) {
    return { frase: `Está un ${numero(mas)} % por encima del más bajo ${plazo}.`, motivo: null }
  }
  return NADA
}
