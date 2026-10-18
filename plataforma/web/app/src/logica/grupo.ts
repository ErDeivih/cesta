/** *** TRES DECISIONES DISTINTAS, QUE ESTABAN METIDAS EN UNA. ***

 *  *Caso real medido el 18/10/2026, ficha de `dia/147509` («Azafran en hebras Pote 0,4 g»):*
 *
 *      ELEGIDO   dia:147509        Pote       0,0004 kg   687500 ¢/kg   2,75 EUR
 *      GRUPO
 *        carrefour 699603651       Pote       (sin cantidad) ud   299 ¢/ud   2,99 EUR
 *        mercadona 8370            Hacendado  0,0004 kg   487500 ¢/kg   1,95 EUR
 *
 *  *** Y la ficha metia tres preguntas en una sola: ***
 *
 *  1. **¿Es el mismo articulo?** *Solo lo dice el **EAN**.*
 *  2. **¿Se pueden comparar los precios?** *Solo si la base es la misma: **misma unidad**, y
 *     **peso neto con peso neto** o **escurrido con escurrido**.* *`ud` frente a `kg` no se resta,
 *     aunque sea el mismo paquete.*
 *  3. **¿Se puede ofrecer?** *Y eso es otra cosa mas.*
 *
 *  *Al mezclarlas salieron los dos errores:*
 *
 *  - *el Pote de Carrefour tiene **el mismo EAN** y salia en «no son este articulo», **que es
 *    falso**: es el mismo articulo; lo que no se puede es comparar 2,99 EUR/ud con 6,87 EUR/g.*
 *  - *y el Hacendado, que es **otro articulo**, se restaba del elegido y daba «un 41 % mas barato»,
 *    **que tambien es falso**.*
 *
 *  *** Y una cuarta trampa, la que costo una ronda entera ***: *el objeto `producto` que devuelve
 *  `/api/producto` **no trae `ean`** (tiene 13 claves y ninguna es esa).* *Asi que filtrar con
 *  `producto.ean` **rechazaba tambien las coincidencias exactas**, y el defecto se disfrazaba de
 *  arreglo: la frase incorrecta desaparecia porque desaparecia **todo**.*
 *
 *  *Por eso aqui no se pregunta «¿son iguales?» con un `boolean` que confunde «no» con «no lo se»:*
 *  *se devuelve **`'no-verificada'`** cuando falta el dato, y la pantalla lo dice asi.*
 */

/** Lo minimo para decidir. */
export interface ConIdentidad {
  ean?: string | null
  unidad?: string | null
  /** *El precio va por peso escurrido.* *Mezclarlo con el neto es restar dos cosas distintas.* */
  precio_por_escurrido?: boolean | null
}

/** *** ¿Es el mismo articulo? *** *`'no-verificada'` NO es «no»: es que no se sabe.* */
export type Identidad = 'mismo' | 'distinto' | 'no-verificada'

/** *El EAN, sin espacios.* *Vacio es «no lo se», no «no tiene».* */
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
 * **¿Se pueden restar los precios?** *Misma base: misma unidad y misma convencion de peso.*
 *
 * *`ud` y `kg` no se restan ni siendo el mismo paquete: es el disparate que el proyecto tiene
 * escrito en tres sitios.*
 */
export function precioComparable(a: ConIdentidad, b: ConIdentidad): boolean {
  if ((a.unidad ?? null) !== (b.unidad ?? null)) return false
  return Boolean(a.precio_por_escurrido) === Boolean(b.precio_por_escurrido)
}

/** *Mismo articulo **y** precios comparables: el unico caso en que una diferencia es un ahorro.* */
export function esAhorroDelElegido(a: ConIdentidad, b: ConIdentidad): boolean {
  return identidad(a, b) === 'mismo' && precioComparable(a, b)
}

export interface Clasificado<T> {
  /** *Mismo articulo y se puede comparar: aqui si hay ahorro del elegido.* */
  comparables: T[]
  /** *Mismo articulo, pero el precio va en otra base: **se dice**, no se resta.* */
  mismoSinComparar: T[]
  /** *Otro articulo: alternativa, y no se resta.* */
  distintas: T[]
  /** *No se sabe si es el mismo: ni se resta ni se llama alternativa.* */
  sinVerificar: T[]
}

/**
 * **Parte el grupo en cuatro, no en dos.** *Quien pinta usa los cuatro: los dos del medio son los
 * que antes se perdian.*
 *
 * *El elegido, si viene en la lista, cae en `comparables` consigo mismo; quien llame lo quita.*
 */
export function clasificaGrupo<T extends ConIdentidad>(
  elegido: ConIdentidad,
  candidatos: T[],
): Clasificado<T> {
  const salida: Clasificado<T> = {
    comparables: [],
    mismoSinComparar: [],
    distintas: [],
    sinVerificar: [],
  }
  for (const c of candidatos) {
    switch (identidad(elegido, c)) {
      case 'mismo':
        if (precioComparable(elegido, c)) salida.comparables.push(c)
        else salida.mismoSinComparar.push(c)
        break
      case 'distinto':
        salida.distintas.push(c)
        break
      default:
        salida.sinVerificar.push(c)
    }
  }
  return salida
}
