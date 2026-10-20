/** *** QUE LISTA USA EL DIARIO CUANDO SE ANOTA UNA COMPRA. ***
 *
 * *M03 lo pide con estas palabras: «eleccion explicita de lista en Calorias».* *Y lo que habia antes era:*
 *
 *     find(es_de_casa)?.id ?? listas.data?.[0]?.id
 *
 * *** Que si no hay lista de casa anota en la PRIMERA que haya -- y esa puede ser la de otra persona del
 * hogar o una lista de ideas. *** *O sea: una compra apuntada en la lista de alguien sin que esa persona lo
 * sepa.*
 *
 * *La regla, ahora, en tres lineas:*
 *
 *   1. **Si la persona eligio una lista, manda su eleccion.**
 *   2. **Si no, la de casa.** *El comportamiento de siempre no cambia.*
 *   3. **Si no hay ninguna de las dos, `null`** -- y la pantalla lo dice, en vez de coger otra.
 *
 * *** Nunca se cae a «la primera que haya»: eso no es elegir, es decidir por quien no ha decidido. ***
 */

export interface ListaParaElDiario {
  id: string
  es_de_casa?: boolean
}

/**
 * *La lista que se usa, o `null` si no hay ninguna que se pueda usar sin elegirla.*
 *
 * `elegida` es lo que la persona ha tocado en esta pantalla o lo que guardo antes; `listas` son las
 * **suyas** -- la API ya las filtra por dueno antes de mandarlas.
 */
export function listaDelDiario(
  listas: ListaParaElDiario[] | undefined | null,
  elegida: string | null | undefined,
): string | null {
  // *Una eleccion que ya no existe (la borraron) no puede quedarse mandando.*
  if (elegida && Array.isArray(listas) && listas.some((l) => l.id === elegida)) return elegida

  const casa = listas?.find((l) => l.es_de_casa)
  return casa?.id ?? null
}

/** *Si hay que preguntar cual, o se puede usar la de casa sin molestar.* */
export function hayQueElegir(listas: ListaParaElDiario[] | undefined | null): boolean {
  if (!Array.isArray(listas) || listas.length === 0) return false
  // *Con una sola lista no hay nada que elegir; con casa, tampoco.*
  if (listas.some((l) => l.es_de_casa)) return false
  return listas.length > 1
}
