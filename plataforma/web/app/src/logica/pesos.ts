/** El control de pesos: como se ordenan las alternativas de un grupo.
 *
 *  Es la parte de la app donde es mas facil mentir sin querer, asi que las
 *  reglas estan escritas aqui y no repartidas por la pantalla:
 *
 *  1. **`calidad` y `gama` son excluyentes.** Un producto trae una o la otra
 *     (lo garantiza el contrato de `/api/grupo`), y el peso de "letra" se
 *     aplica a la que traiga, diciendo cual es. Nunca se suman las dos: hacerlo
 *     daria por bueno un producto del que solo sabemos su posicion de precio.
 *  2. **La nota se reparte solo entre lo que se sabe.** Un producto sin precio
 *     por unidad o sin letra no saca un cero en esa parte: saca una nota
 *     calculada con lo que hay. Un cero se lee como "malo" y seria mentira.
 *  3. **Un precio viejo no decide.** Lo que no puede decidir entra en la lista
 *     con su fecha y se queda fuera del calculo y del "mas barato".
 *  4. **`promo` mira lo que se paga en caja.** Una oferta de tarjeta cuenta la
 *     mitad y se dice; una promo ausente es un cero de verdad, porque "no hay
 *     promoción" es un dato, no un hueco.
 */
import type { Producto } from '../tipos'

export interface Pesos {
  /** Cuanto pesa lo barato que sea por unidad. */
  precio: number
  /** Cuanto pesa la letra: calidad si se leyo, gama si salio del precio. */
  letra: number
  /** Cuanto pesa no alejarse del mejor precio. */
  cercania: number
  /** Cuanto pesa que haya promocion de las que bajan lo que pagas. */
  promo: number
}

export const PESOS_INICIALES: Pesos = { precio: 45, letra: 25, cercania: 20, promo: 10 }

export const NOMBRE_PESO: Record<keyof Pesos, string> = {
  precio: 'precio',
  letra: 'letra (calidad o gama)',
  cercania: 'cercanía al mejor precio',
  promo: 'promoción',
}

export interface Componentes {
  /** 1 = el más barato por unidad del grupo. */
  precio: number | null
  letra: number | null
  /** De dónde sale la letra, para poder decirlo en pantalla. */
  letraDe: 'calidad' | 'gama' | null
  cercania: number | null
  promo: number
}

export interface Alternativa {
  producto: Producto
  componentes: Componentes
  /** 0 a 100, o null si no hay ni un componente con dato. */
  puntos: number | null
  /** Diferencia contra el mejor precio por unidad que puede decidir. */
  diferenciaPct: number | null
  /** false = su precio es viejo o no tiene precio por unidad: se enseña, no decide. */
  decide: boolean
  /** Por qué no decide, en una frase. */
  motivoNoDecide: string | null
}

/** A=1, B=0,6, C=0,2.
 *
 *  Las letras de `core/calidad.py` son terciles DENTRO del grupo, asi que una
 *  C no es "malo": es "de los peores de estos seis". Los cortes son los del
 *  reparto (dos tercios y un tercio), no una escala inventada aqui.
 */
function valorLetra(letra: string | null): number | null {
  if (letra === 'A') return 1
  if (letra === 'B') return 0.6
  if (letra === 'C') return 0.2
  return null
}

/** A partir del 5 % más caro que el mejor empieza a bajar; al 50 %, cero. */
const CERCA_HASTA = 1.05
const LEJOS_DESDE = 1.5

function valorCercania(precio: number, minimo: number): number | null {
  if (minimo <= 0) return null
  const ratio = precio / minimo
  if (ratio <= CERCA_HASTA) return 1
  if (ratio >= LEJOS_DESDE) return 0
  return 1 - (ratio - CERCA_HASTA) / (LEJOS_DESDE - CERCA_HASTA)
}

function valorPromo(p: Producto): number {
  if (!p.promo) return 0
  // La de tarjeta no baja lo que pagas en caja: cuenta la mitad, y en la ficha
  // se dice con esas palabras.
  return p.promo_club ? 0.5 : 1
}

export function puntuaAlternativas(
  productos: Producto[],
  pesos: Pesos,
  puedeDecidir: (p: Producto) => { decide: boolean; motivo: string | null },
): Alternativa[] {
  // El "mejor precio" se calcula SOLO con lo que puede decidir: si el precio
  // más barato del grupo es de hace cinco días, no puede ser la referencia de
  // nadie.
  const deciden = productos.filter((p) => puedeDecidir(p).decide)
  const precios = deciden
    .map((p) => p.precio_unidad_cent)
    .filter((c): c is number => c !== null && Number.isFinite(c) && c > 0)
  const minimo = precios.length > 0 ? Math.min(...precios) : null

  const sumaPesos = pesos.precio + pesos.letra + pesos.cercania + pesos.promo
  const reparto: Pesos =
    sumaPesos > 0
      ? pesos
      : // Todos los pesos a cero no es "da igual": es que no se ha dicho nada.
        // Se reparte a partes iguales y la pantalla lo dice.
        { precio: 1, letra: 1, cercania: 1, promo: 1 }
  const total = reparto.precio + reparto.letra + reparto.cercania + reparto.promo

  const salida: Alternativa[] = productos.map((p) => {
    const { decide, motivo } = puedeDecidir(p)
    const precio = p.precio_unidad_cent

    const componentes: Componentes = {
      precio:
        precio !== null && precio > 0 && minimo !== null && minimo > 0 ? minimo / precio : null,
      letra: valorLetra(p.calidad ?? p.gama ?? null),
      letraDe: p.calidad ? 'calidad' : p.gama ? 'gama' : null,
      cercania:
        precio !== null && precio > 0 && minimo !== null && minimo > 0
          ? valorCercania(precio, minimo)
          : null,
      promo: valorPromo(p),
    }

    // La nota reparte el peso solo entre los componentes con dato. Sin esto, un
    // producto sin precio por unidad pareceria carisimo por un cero que no es
    // un cero.
    const pares: [number, number | null][] = [
      [reparto.precio, componentes.precio],
      [reparto.letra, componentes.letra],
      [reparto.cercania, componentes.cercania],
      [reparto.promo, componentes.promo],
    ]
    let num = 0
    let den = 0
    for (const [peso, valor] of pares) {
      if (valor === null || peso <= 0 || total <= 0) continue
      num += peso * valor
      den += peso
    }
    const puntos = den > 0 ? Math.round((100 * num) / den * 10) / 10 : null

    const diferenciaPct =
      minimo !== null && minimo > 0 && precio !== null && precio > 0
        ? Math.round((100 * (precio - minimo)) / minimo * 10) / 10
        : null

    return { producto: p, componentes, puntos, diferenciaPct, decide, motivoNoDecide: motivo }
  })

  // Primero las que deciden, de mejor a peor. Las que no deciden van despues,
  // pero con su nota calculada: enterrarlas seria esconder un dato que existe.
  return salida.sort((a, b) => {
    if (a.decide !== b.decide) return a.decide ? -1 : 1
    if (a.puntos === null && b.puntos === null) return 0
    if (a.puntos === null) return 1
    if (b.puntos === null) return -1
    return b.puntos - a.puntos
  })
}

/** La frase que explica el orden, para que no sea un numero magico. */
export function explicaPesos(pesos: Pesos, letras: { calidad: number; gama: number }): string {
  const suma = pesos.precio + pesos.letra + pesos.cercania + pesos.promo
  if (suma <= 0) {
    return 'Todos los pesos están a cero, así que reparto a partes iguales: precio, letra, cercanía y promoción pesan lo mismo.'
  }
  const pct = (v: number) => Math.round((100 * v) / suma)
  const partes = [
    `${pct(pesos.precio)} % precio por unidad`,
    `${pct(pesos.letra)} % letra`,
    `${pct(pesos.cercania)} % cercanía al mejor`,
    `${pct(pesos.promo)} % promoción`,
  ]
  const matiz =
    pesos.letra > 0
      ? letras.gama > 0 && letras.calidad > 0
        ? ` De las ${letras.calidad + letras.gama} alternativas, ${letras.calidad} traen calidad leída de ingredientes y ${letras.gama} traen gama por precio: cada una usa la suya y lo dice en su ficha. No se suman.`
        : letras.gama > 0
          ? ` Ojo: en este grupo ninguna letra sale de leer ingredientes, así que la ${pct(pesos.letra)} % de "letra" está mirando el precio otra vez.`
          : letras.calidad > 0
            ? ' Las letras de este grupo salen de leer ingredientes, no del precio.'
            : ' Ninguna alternativa de este grupo tiene letra, así que ese peso no está haciendo nada.'
      : ''
  return `El orden lo decide: ${partes.join(', ')}.${matiz}`
}
