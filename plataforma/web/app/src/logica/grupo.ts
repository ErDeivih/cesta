/** *** QUE ES «EL MISMO ARTICULO» Y QUE ES UNA ALTERNATIVA. ***
 *
 *  *Esto decide si una diferencia de precio se puede contar como ahorro **del articulo que has
 *  elegido**, o si es otra cosa y hay que decirlo.*
 *
 *  **El defecto que lo trajo, medido el 18/10/2026 con datos reales de la ficha de
 *  `dia/147509`:**
 *
 *      elegido    dia:147509      EAN 8412206003235   Pote       0,4 g   687 500 ¢/kg   2,75 EUR
 *      grupo
 *        carrefour 699603651      EAN 8412206003235   Pote       400 mg        299 ¢/ud   2,99 EUR
 *        mercadona 8370           EAN 8402001022050   Hacendado  0,4 g     487 500 ¢/kg   1,95 EUR
 *        dia       147509         EAN 8412206003235   Pote       0,4 g     687 500 ¢/kg   = este
 *      ahorro_pct del grupo: 41,0
 *
 *  *La ficha decia **«Cuesta un 41 % mas que en Mercadona»**.* *Y Mercadona es **azafran
 *  Hacendado**: otra marca, otro EAN, **otro articulo**.* *Un 41 % de ahorro del articulo elegido
 *  que no existe.*
 *
 *  *** Dos condiciones, y las dos hacen falta ***:
 *
 *  1. **Mismo EAN.** *Es el unico identificador que dice «es el mismo producto».* *Marcas y nombres
 *     se parecen y no bastan.* *Sin EAN en alguno de los dos **no se afirma**: no saberlo no es
 *     saber que son iguales.*
 *  2. **Misma unidad de comparacion.** *El propio codigo ya avisa de esto: restar EUR/kg de EUR/ud
 *     es el disparate que el proyecto tiene escrito en tres sitios.* *En el caso de arriba,
 *     Carrefour **si** tiene el mismo EAN pero su precio va **por unidad** y el elegido **por kg**:
 *     no se comparan, y por eso el mismo articulo **no da ninguna frase** aqui.*
 *
 *  *Lo que no cumple las dos es **una alternativa**, y va en su apartado, con su nombre y su
 *  marca, **sin restar nada**.*
 */

/** Lo minimo que hace falta para decidir: el EAN y la unidad de comparacion. */
export interface ConEanYUnidad {
  ean?: string | null
  unidad?: string | null
}

/**
 * ¿Son el mismo articulo? Mismo EAN **y** misma unidad.
 *
 * *Sin EAN en alguno de los dos devuelve `false`: **no se puede afirmar**, y una afirmacion sin
 * dato es justo lo que no se hace.*
 */
export function esMismoArticulo(a: ConEanYUnidad, b: ConEanYUnidad): boolean {
  const eanA = (a.ean ?? '').trim()
  const eanB = (b.ean ?? '').trim()
  if (!eanA || !eanB) return false
  if (eanA !== eanB) return false
  return (a.unidad ?? null) === (b.unidad ?? null)
}

/** Los que **son** el mismo articulo que el elegido.
 *
 *  *Ojo: **incluye al elegido si esta en la lista**.* *Esta funcion no puede distinguirlo -- solo ve
 *  EAN y unidad --, asi que **quien la llama tiene que quitarlo** si su lista lo trae.* *Se dice
 *  aqui porque el primer comentario afirmaba lo contrario, y la prueba lo encontro.* */
export function mismosArticulos<T extends ConEanYUnidad>(
  elegido: ConEanYUnidad,
  candidatos: T[],
): T[] {
  return candidatos.filter((c) => esMismoArticulo(elegido, c))
}

/** Los que **no** lo son: se enseñan aparte, como alternativas, y no restan nada. */
export function alternativas<T extends ConEanYUnidad>(
  elegido: ConEanYUnidad,
  candidatos: T[],
): T[] {
  return candidatos.filter((c) => !esMismoArticulo(elegido, c))
}
