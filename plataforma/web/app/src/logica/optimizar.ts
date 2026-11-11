/** *** LA CESTA MÁS BARATA EN UNA O DOS TIENDAS. *** *
 *
 *  *Un algoritmo simple, y explicable en una frase: se prueban todas las tiendas y todas las
 *  parejas de tiendas, se exige que cubran **todos** los productos, y se queda la más barata.*
 *
 *  **Nada de ceros por lo que falta.** *Una tienda que no tiene un producto no entra como 0 €:
 *  si no cubre la lista, esa opción no se propone.* *Y una pareja solo vale si entre las dos
 *  cubren todos los productos.*
 *
 *  *Los costes son los que ya calculó el reparto para la cantidad pedida; aquí solo se suman y se
 *  comparan. El «ahorro» es la diferencia entre la mejor opción de una tienda y la mejor de dos:
 *  si repartir no ahorra, no se anuncia un ahorro.*
 */

export interface PrecioDeLinea {
  cadena: string
  /** Lo que cuesta la cantidad pedida en esa cadena, en céntimos. */
  coste_cent: number
}

export interface OpcionUnaTienda {
  cadena: string
  total_cent: number
  lineas: number
}

export interface ParteDeLaCompra {
  cadena: string
  total_cent: number
  lineas: number
}

export interface OpcionDosTiendas {
  a: string
  b: string
  total_cent: number
  partes: ParteDeLaCompra[]
}

export interface MejorCompra {
  una: OpcionUnaTienda | null
  dos: OpcionDosTiendas | null
  /** `null` si no hay dos opciones comparables o si repartir no ahorra nada. */
  ahorro_cent: number | null
}

/** Las cadenas que aparecen en algún precio, en orden alfabético para que el resultado sea estable. */
function cadenasDe(precios: Map<string, PrecioDeLinea[]>): string[] {
  const vistas = new Set<string>()
  for (const lista of precios.values()) for (const p of lista) vistas.add(p.cadena)
  return [...vistas].sort()
}

/**
 * La mejor compra en 1 o 2 tiendas para `lineas`.
 *
 * `precios` va de id de línea a los precios que hay para ella en cada cadena. Una línea sin
 * precio en una cadena es **ausencia**, no 0 €.
 */
export function mejorCompra(lineas: string[], precios: Map<string, PrecioDeLinea[]>): MejorCompra {
  const cadenas = cadenasDe(precios)
  const costeDe = (lineaId: string, cadena: string): number | null => {
    const encontrado = (precios.get(lineaId) ?? []).find((p) => p.cadena === cadena)
    return encontrado ? encontrado.coste_cent : null
  }

  // *** Una tienda: solo cuenta si tiene todos los productos. *** *
  let una: OpcionUnaTienda | null = null
  for (const cadena of cadenas) {
    const costes = lineas.map((id) => costeDe(id, cadena))
    if (costes.some((c) => c === null)) continue
    const total = (costes as number[]).reduce((suma, c) => suma + c, 0)
    if (!una || total < una.total_cent) {
      una = { cadena, total_cent: total, lineas: lineas.length }
    }
  }

  // *** Dos tiendas: cada producto, donde esté más barato de las dos. *** *
  let dos: OpcionDosTiendas | null = null
  for (let i = 0; i < cadenas.length; i += 1) {
    for (let j = i + 1; j < cadenas.length; j += 1) {
      const a = cadenas[i]
      const b = cadenas[j]
      const partes: Record<string, ParteDeLaCompra> = {
        [a]: { cadena: a, total_cent: 0, lineas: 0 },
        [b]: { cadena: b, total_cent: 0, lineas: 0 },
      }
      let total = 0
      let completa = true
      for (const id of lineas) {
        const ca = costeDe(id, a)
        const cb = costeDe(id, b)
        if (ca === null && cb === null) { completa = false; break }
        // *Empate: se queda en la primera, que es la que va antes en el orden alfabético.*
        const elegida = ca !== null && (cb === null || ca <= cb) ? a : b
        const coste = elegida === a ? ca as number : cb as number
        total += coste
        partes[elegida].total_cent += coste
        partes[elegida].lineas += 1
      }
      if (!completa) continue
      if (!dos || total < dos.total_cent) {
        dos = { a, b, total_cent: total, partes: [partes[a], partes[b]] }
      }
    }
  }

  const ahorro = una && dos && una.total_cent > dos.total_cent
    ? una.total_cent - dos.total_cent
    : null
  return { una, dos, ahorro_cent: ahorro }
}
