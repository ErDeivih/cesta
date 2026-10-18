/** *** PEGAR UNA LISTA ENTERA, Y ENSEÑARLA ANTES DE GUARDAR NADA. ***
 *
 *  *La especificación lo pide con estas palabras (M05): «Texto libre y pegar varias líneas con
 *  previa; **no interpretar «2 kg» como dos envases sin base**».*
 *
 *  **Lo que esta función hace, y lo que NO.**
 *
 *  Hace: partir el texto pegado en líneas, quitar numeración y viñetas, y **separar la cantidad y
 *  la unidad del nombre** -- pero dejándolas como **texto**, no como un número de envases.
 *
 *  No hace: decidir cuántos envases son. *«2 kg» es un peso, y cuántos envases son depende del
 *  formato que se compre, que aquí no se sabe.* *Convertirlo en `cantidad: 2` sería exactamente el
 *  fallo que la especificación nombra: inventar una base.*
 *
 *  Por eso `Pegada.cantidad` y `Pegada.unidad` son **texto** y no se suman a nada: viajan a la nota
 *  de la línea, que es donde la persona las lee. *El número de envases lo pone quien compra.*
 */

export interface Pegada {
  /** *El nombre, sin la cantidad delante.* */
  nombre: string
  /** *La cantidad tal como se escribió: «2», «1,5», «½». **Texto**, no número.* */
  cantidad: string | null
  /** *La unidad tal como se escribió: kg, g, l, ml, ud.* **Texto**, no una equivalencia.* */
  unidad: string | null
  /** *Lo que se guarda como nota: la cantidad y la unidad juntas, o vacío.* */
  nota: string
}

/** *Las unidades que se reconocen como unidad, **y ninguna se convierte a otra**.*
 *
 *  *No hay tabla de equivalencias a propósito: «2 kg» y «2000 g» son la misma cantidad, pero
 *  decidirlo aquí sería una conversión que nadie ha pedido y que puede equivocarse.*
 */
const UNIDADES = [
  'kg', 'kgs', 'kilo', 'kilos', 'g', 'gr', 'grs', 'gramo', 'gramos',
  'l', 'lt', 'lts', 'litro', 'litros', 'ml', 'cl',
  'ud', 'uds', 'unidad', 'unidades', 'paquete', 'paquetes', 'bote', 'botes',
  'lata', 'latas', 'caja', 'cajas', 'bolsa', 'bolsas', 'docena', 'docenas',
]

/** *Quita la numeración y las viñetas del principio de una línea.*
 *
 *  *«1. leche», «- pan», «• arroz», «2) huevos» -- todo eso es cómo se escribe una lista a mano, no
 *  parte del nombre del producto.*
 */
function sinAdorno(linea: string): string {
  return linea.replace(/^\s*(?:[-*•·]|\d+[.)])\s+/, '').trim()
}

/** *Parte «2 kg de arroz» en cantidad, unidad y nombre.*
 *
 *  *Sólo reconoce la cantidad **al principio**, y sólo si la unidad es una de la lista.*
 *  *«Arroz 2 kg» se queda entero como nombre: partirlo por el medio convertiría «pan de 2 kg» en
 *  «pan de», que es peor que no partirlo.*
 */
export function partirCantidad(texto: string): Pegada {
  const limpio = texto.trim()
  // *La cantidad puede ser entera, decimal con coma o punto, o una fracción escrita.*
  const m = limpio.match(
    /^(\d+(?:[.,]\d+)?|½|¼|¾)\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)?\.?\s+(?:de\s+)?(.+)$/,
  )
  if (!m) return { nombre: limpio, cantidad: null, unidad: null, nota: '' }

  const [, cantidad, posibleUnidad, resto] = m
  const unidad = (posibleUnidad ?? '').toLowerCase()
  if (!unidad || !UNIDADES.includes(unidad)) {
    // *Hay cantidad pero no unidad reconocida: «2 latas» sí, «2 cosas» no.*
    // *Se deja todo en el nombre: sin unidad, el número no dice nada.*
    return { nombre: limpio, cantidad: null, unidad: null, nota: '' }
  }
  const nota = `${cantidad} ${unidad}`.trim()
  return { nombre: resto.trim(), cantidad, unidad, nota }
}

/** *Parte lo pegado en líneas, y cada una en nombre y cantidad.*
 *
 *  *Las líneas vacías se descartan: pegar de un documento trae saltos de más.*
 *  *Los repetidos **se conservan**: apuntar «leche» dos veces es una lista válida, y es la persona
 *  quien decide si sobra.*
 */
export function parteLoPegado(texto: string): Pegada[] {
  if (!texto.trim()) return []
  return texto
    .split(/\r?\n/)
    .map((l) => sinAdorno(l))
    .filter((l) => l.length > 0)
    .map((l) => partirCantidad(l))
}

/** *Lo que la previa tiene que decir, en una frase.*
 *
 *  *Se dice **cuántas** líneas y **cuántas traen cantidad**, porque son cosas distintas: la persona
 *  que pega diez líneas quiere saber si se han leído diez, y si alguna trae peso.*
 */
export function resumenDeLaPrevia(pegadas: Pegada[]): string {
  const total = pegadas.length
  if (total === 0) return 'No hay ninguna linea que anadir.'
  const conCantidad = pegadas.filter((p) => p.cantidad !== null).length
  const lineas = total === 1 ? '1 linea' : `${total} lineas`
  if (conCantidad === 0) {
    return `${lineas}. Ninguna trae cantidad: se anaden sin ella, y la pones tu en la lista.`
  }
  return (
    `${lineas}, ${conCantidad} con cantidad. ` +
    'La cantidad va a la nota tal como la escribiste: no se convierte en envases.'
  )
}
