/** **«¿Esto está caro?», contestado con la serie de verdad.**
 *
 *  La ficha lleva un chip con la respuesta y su motivo -- «está caro: el máximo de los últimos 60
 *  días» --, y ahí cada palabra es una afirmación sobre el histórico. Así que la decisión vive
 *  aquí, pura y probada (`tests/juicio.test.mjs`), y el componente solo pinta lo que se decide.
 *
 *  Cuatro reglas, y las cuatro tienen un caso que las obligó:
 *
 *  1. **La ventana es la que hay.** `dias` sale de las fechas de la serie (del primer día al
 *     último, contando los dos) y no de un número escrito a mano: la ficha no puede decir «90
 *     días» cuando la serie tiene 60, y tampoco «60» si mañana la API sirve 45.
 *  2. **Con un solo día con precio no se juzga.** «El máximo de un día» no es una respuesta.
 *  3. **Con dos unidades no se juzga.** *Es la misma regla que `logica/curva.ts` y
 *     `api/alertas.py`: si la unidad cambió por el camino, el mínimo mezclado no significa nada.*
 *  4. **Un precio que no se movió no es «el mínimo».** *Tres días al mismo precio dan «el mínimo
 *     de los últimos 3 días», que es cierto y no informa de nada. Ahí se dice que no se movió.*
 *
 *  Y no hay cuarto estado escondido: o el precio de hoy es el máximo, o el mínimo, o ninguno de los
 *  dos, o la serie es plana. Lo que no se hace es llamar «normal» a un precio: eso sería una
 *  opinión, y la pantalla no opina.
 */
/** **La fecha en milisegundos, o `null` si no es una fecha.**
 *
 *  *Está repetida de `logica/chispa.ts` a propósito.* *Una pieza de `logica/` **no importa otra**:
 *  *`node --test` carga estos módulos tal cual (sin empaquetador) y un import sin extensión no lo
 *  resuelve.* *Son tres líneas y la regla es la misma en los dos sitios; el día que cambie, las
 *  dos pruebas lo dicen.*
 */
function aMs(fecha: string): number | null {
  if (!fecha) return null
  const t = new Date(fecha.length <= 10 ? `${fecha}T00:00:00` : fecha).getTime()
  return Number.isNaN(t) ? null : t
}

/** Un punto del histórico, como lo manda `/api/grupo` (con su unidad, si la trae). */
export interface PuntoDePrecio {
  fecha: string
  precio_unidad_cent: number | null
  unidad_canon?: string | null
}

/** De qué lado cae el precio de hoy. `medio` es «ni lo uno ni lo otro», no «normal». */
export type Juicio = 'caro' | 'barato' | 'medio'

export interface Veredicto {
  juicio: Juicio
  /** La frase entera del chip, con su motivo. Es lo que se lee. */
  texto: string
  /** La ventana real de la serie, en días de calendario (el primero y el último incluidos). */
  dias: number
  /** Días con precio: los que cuentan para el mínimo, el máximo y la media. */
  conPrecio: number
  /** Días de la ventana sin precio: los huecos de la línea. */
  huecos: number
  minimo: number
  maximo: number
  /** El último precio observado, que es el de «hoy» en la pantalla. */
  hoy: number
  /** La unidad de toda la serie, o `null` si no consta. */
  unidad: string | null
  /** La primera y la última fecha con dato legible, en ISO. */
  desde: string
  hasta: string
}

const UN_DIA = 24 * 60 * 60 * 1000

export function veredictoDelPrecio(puntos: PuntoDePrecio[]): Veredicto | null {
  // **Un punto sin fecha legible no está en el eje.** *No se coloca en 1970 ni se cuenta: es la
  // regla de `chispa.ts`, y la ventana no puede estirarse por un dato roto.*
  const conFecha = puntos
    .map((p) => ({ ...p, ms: aMs(p.fecha) }))
    .filter((p): p is PuntoDePrecio & { ms: number } => p.ms !== null)
    .sort((a, b) => a.ms - b.ms)

  if (conFecha.length === 0) return null

  const con = conFecha.filter(
    (p): p is PuntoDePrecio & { ms: number; precio_unidad_cent: number } =>
      p.precio_unidad_cent != null && Number.isFinite(p.precio_unidad_cent) &&
      p.precio_unidad_cent > 0,
  )
  // *Un solo día con precio no da serie, y sin serie no hay respuesta.*
  if (con.length < 2) return null

  // **La unidad, si la API la manda.** *Con dos unidades, el mínimo de las dos juntas no es el
  // mínimo de nada: es la misma guarda que `curva.ts`.*
  const unidades = new Set(
    con.map((p) => p.unidad_canon ?? null).filter((u): u is string => Boolean(u)),
  )
  if (unidades.size > 1) return null

  const dias = Math.floor((conFecha[conFecha.length - 1].ms - conFecha[0].ms) / UN_DIA) + 1
  const ventanaDe = dias === 1 ? 'del último día' : `de los últimos ${dias} días`
  const ventanaEn = dias === 1 ? 'en el último día' : `en los últimos ${dias} días`

  const precios = con.map((p) => p.precio_unidad_cent)
  const minimo = Math.min(...precios)
  const maximo = Math.max(...precios)
  const hoy = con[con.length - 1].precio_unidad_cent

  const base = {
    dias,
    conPrecio: con.length,
    huecos: conFecha.length - con.length,
    minimo,
    maximo,
    hoy,
    unidad: [...unidades][0] ?? null,
    desde: conFecha[0].fecha,
    hasta: conFecha[conFecha.length - 1].fecha,
  }

  // *Y un precio que nunca se movió no es «el mínimo»: es que no se movió.*
  if (maximo === minimo) {
    return {
      ...base,
      juicio: 'medio',
      texto: `está en lo de siempre: sin cambios ${ventanaEn}`,
    }
  }
  if (hoy >= maximo) {
    return { ...base, juicio: 'caro', texto: `está caro: el máximo ${ventanaDe}` }
  }
  if (hoy <= minimo) {
    return { ...base, juicio: 'barato', texto: `está bien: el mínimo ${ventanaDe}` }
  }
  return {
    ...base,
    juicio: 'medio',
    texto: `está en lo de siempre: ni máximo ni mínimo ${ventanaDe}`,
  }
}
