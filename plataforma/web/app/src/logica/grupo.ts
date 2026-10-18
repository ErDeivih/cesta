/**
 * *** UN UNICO RESULTADO DE COMPARACION, Y NADA MAS. ***
 *
 * *Caso real medido el 18/10/2026, ficha de `dia/147509` («Azafran en hebras Pote 0,4 g»):*
 *
 *      ELEGIDO   dia:147509        Pote       0,0004 kg   687500 ¢/kg   2,75 EUR
 *      GRUPO
 *        carrefour 699603651       Pote       (sin cantidad) ud   299 ¢/ud   2,99 EUR
 *        mercadona 8370            Hacendado  0,0004 kg   487500 ¢/kg   1,95 EUR
 *
 *  *** Aqui se juntaron tres errores, y los tres venian de mezclar cifras del grupo con las del
 *  articulo: ***
 *
 *  1. **La frase recibia `grupo.ahorro_cent` y `grupo.cadenas`**, *que son del grupo entero
 *     --incluidas las alternativas--, aunque los candidatos ya estuvieran filtrados.* *Si el
 *     elegido es el mas barato, la frase podia anunciar un ahorro y un numero de cadenas que no
 *     son de ese articulo.*
 *  2. **`precioComparable` daba `true` con las dos unidades ausentes**: *`null !== null` es `false`,
 *     asi que no salia por ahi, y `Boolean(undefined) === Boolean(undefined)` es `true`.*
 *     *** Que no se sepa la base no demuestra que las bases coincidan.***
 *  3. **La diferencia normalizada se enseñaba como euros sin unidad**: *«2000 EUR» cuando eran
 *     2000 EUR **por kilo**.* *Y eso no es lo mismo que el ahorro del envase que se lleva a casa.*
 *
 *  *** La regla, de aqui en adelante ***: **todo lo que se anuncia sale de `construyeComparacion`,
 *  que solo mira candidatos exactos y elegibles.** *Nada de estadisticas del grupo entero.*
 */

/** Lo minimo para decidir. */
export interface ConIdentidad {
  ean?: string | null
  unidad?: string | null
  /** *El precio va por peso escurrido.* *Mezclarlo con el neto es restar dos cosas distintas.* */
  precio_por_escurrido?: boolean | null
  /** *Lo que cuesta el envase entero, en centimos.* *Para el ahorro que se lleva a casa.* */
  precio_cent?: number | null
}

/** *** ¿Es el mismo articulo? *** *`'no-verificada'` NO es «no»: es que no se sabe.* */
export type Identidad = 'mismo' | 'distinto' | 'no-verificada'

function limpiaEan(ean: string | null | undefined): string {
  return (ean ?? '').trim()
}

/**
 * **La identidad del articulo, con tres respuestas y no dos.**
 *
 * *Sin EAN en cualquiera de los dos: `'no-verificada'`.* *Decir «distinto» sin dato seria afirmar
 * algo que no se sabe -- y la pantalla lo diria con esas palabras.*
 */
export function identidad(elegido: ConIdentidad, candidato: ConIdentidad): Identidad {
  const a = limpiaEan(elegido.ean)
  const b = limpiaEan(candidato.ean)
  if (!a || !b) return 'no-verificada'
  return a === b ? 'mismo' : 'distinto'
}

/**
 * **¿Se pueden restar los precios?** *Misma base declarada, y la misma convencion de peso.*
 *
 * *** Una base ausente NO vale.*** *Si no consta en que se mide, no se puede afirmar que coincida
 * con la del otro: `'' !== ''` es falso y una comparacion de cadenas vacias daria «comparable», que
 * es justo el error que trajo esto.*
 */
export function precioComparable(a: ConIdentidad, b: ConIdentidad): boolean {
  const ua = (a.unidad ?? '').trim()
  const ub = (b.unidad ?? '').trim()
  if (!ua || !ub) return false
  if (ua !== ub) return false
  return Boolean(a.precio_por_escurrido) === Boolean(b.precio_por_escurrido)
}

/** *Mismo articulo **y** base declarada y comparable: el unico caso en que una diferencia es un ahorro.* */
export function esAhorroDelElegido(a: ConIdentidad, b: ConIdentidad): boolean {
  return identidad(a, b) === 'mismo' && precioComparable(a, b)
}

/** **El unico resultado que se puede anunciar.** *Todo lo de la ficha sale de aqui.* */
export interface Comparacion<T> {
  /** *Mismo articulo y misma base declarada: **solo aqui** se calculan cifras que se anuncian.* */
  comparables: T[]
  /** *Mismo articulo, otra base: se enseña, no se resta.* */
  mismoSinComparar: T[]
  /** *Otro articulo: alternativa, ni se resta ni cuenta como cadena.* */
  distintas: T[]
  /** *No se sabe si es el mismo: ni se resta ni se llama alternativa.* */
  sinVerificar: T[]
  /** *La base de precio de los comparables (`kg`, `l`, `ud`...).* `null` si no hay ninguno. */
  unidad: string | null
  /** *Cadenas **distintas** entre los comparables.* *No del grupo: de lo comparable.* */
  cadenas: number
  /** *El mas barato y el mas caro, en centimos **por la unidad de `unidad`**.* */
  minimo: number | null
  maximo: number | null
  /** *Diferencia normalizada, **con su unidad**: «2000 cent por kg» no es «2000 EUR».* */
  diferenciaCent: number | null
  diferenciaPct: number | null
  /** *Ahorro **por envase** del elegido, en centimos, contra el mas barato comparable.* *Distinto
   *  de la diferencia normalizada, y es el que se lleva a casa.* */
  ahorroEnvaseCent: number | null
}

type ConFuente = ConIdentidad & { fuente?: string; precio_unidad_cent?: number | null }

/**
 * **Construye la comparacion de una vez, y esa es la que se pinta.**
 *
 * *Solo cuentan los candidatos con **identidad exacta** (`'mismo'`) y **base declarada y
 * coincidente**.* *Las alternativas **no** entran en `cadenas`, ni en el minimo, ni en el ahorro.*
 *
 * *El elegido, si viene en la lista, se queda dentro; quien pinte lo quita de las listas.*
 */
export function construyeComparacion<T extends ConFuente>(
  elegido: ConFuente,
  candidatos: T[],
): Comparacion<T> {
  const comparables: T[] = []
  const mismoSinComparar: T[] = []
  const distintas: T[] = []
  const sinVerificar: T[] = []

  for (const c of candidatos) {
    switch (identidad(elegido, c)) {
      case 'mismo':
        if (precioComparable(elegido, c)) comparables.push(c)
        else mismoSinComparar.push(c)
        break
      case 'distinto':
        distintas.push(c)
        break
      default:
        sinVerificar.push(c)
    }
  }

  const conPrecio = comparables.filter(
    (p) => p.precio_unidad_cent != null && Number.isFinite(p.precio_unidad_cent) && p.precio_unidad_cent > 0,
  )

  // *** EL ELEGIDO CUENTA, AUNQUE NO VENGA EN LA LISTA. ***
  // *La diferencia es **de este articulo** contra los demas, asi que su precio forma parte de la
  // cuenta.* *La primera version sumaba solo los candidatos, y entonces dos ofertas exactas del
  // mismo articulo daban diferencia **cero** si el elegido no estaba entre ellas -- lo encontro la
  // prueba de la regresion.*
  const unidadDeclarada = (elegido.unidad ?? '').trim()
  const elElegidoEntra =
    unidadDeclarada.length > 0 &&
    elegido.precio_unidad_cent != null &&
    Number.isFinite(elegido.precio_unidad_cent) &&
    (elegido.precio_unidad_cent as number) > 0
  const precios = [
    ...conPrecio.map((p) => p.precio_unidad_cent as number),
    ...(elElegidoEntra ? [elegido.precio_unidad_cent as number] : []),
  ]

  const unidad = precios.length > 0 ? unidadDeclarada || null : null
  const cadenas = new Set(
    conPrecio.map((p) => (p.fuente ?? '').trim()).filter((f) => f.length > 0),
  ).size
  const minimo = precios.length > 0 ? Math.min(...precios) : null
  const maximo = precios.length > 0 ? Math.max(...precios) : null

  let diferenciaCent: number | null = null
  let diferenciaPct: number | null = null
  if (minimo != null && maximo != null && minimo > 0) {
    diferenciaCent = maximo - minimo
    diferenciaPct = Math.round((100 * (maximo - minimo)) / minimo)
  }

  // *El ahorro del envase: lo que se lleva a casa, en dinero.* *Solo si los dos precios de envase
  // existen y el elegido no es ya el mas barato.*
  let ahorroEnvaseCent: number | null = null
  const mio = elegido.precio_cent
  if (mio != null && Number.isFinite(mio) && conPrecio.length > 0) {
    const masBarato = conPrecio.reduce((a, b) =>
      (a.precio_unidad_cent as number) <= (b.precio_unidad_cent as number) ? a : b,
    )
    // *Solo hay ahorro si el otro es **mas barato por unidad** que el elegido: si el elegido ya es
    // el mas barato, no se anuncia nada.*
    const miUnidad = elegido.precio_unidad_cent
    const suyo = masBarato.precio_cent
    const otroEsMasBarato =
      miUnidad != null && Number.isFinite(miUnidad) &&
      (masBarato.precio_unidad_cent as number) < miUnidad
    if (otroEsMasBarato && suyo != null && Number.isFinite(suyo) && suyo < mio) ahorroEnvaseCent = mio - suyo
  }

  return {
    comparables,
    mismoSinComparar,
    distintas,
    sinVerificar,
    unidad,
    cadenas,
    minimo,
    maximo,
    diferenciaCent,
    diferenciaPct,
    ahorroEnvaseCent,
  }
}
