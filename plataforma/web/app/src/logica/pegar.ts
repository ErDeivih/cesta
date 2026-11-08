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
  return leerPegado(texto).pegadas
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

// ---------------------------------------------------------- CSV y JSON ------

/** De donde salio lo pegado. **No se adivina por el nombre del fichero**: se mira el texto. */
export type FormatoPegado = 'texto' | 'csv' | 'json'

export interface LecturaPegado {
  pegadas: Pegada[]
  formato: FormatoPegado
  /** Lo que no se pudo leer y por que. No se rellena con ceros ni con productos inventados. */
  avisos: string[]
}

const CLAVES_NOMBRE = ['nombre', 'name', 'producto', 'product', 'articulo', 'descripcion']
const CLAVES_CANTIDAD = ['cantidad', 'quantity', 'qty', 'peso', 'weight']
const CLAVES_NOTA = ['nota', 'note', 'notes', 'observaciones', 'comentario']

function normalizaClave(texto: string): string {
  return texto
    .replace(/^\uFEFF/, '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

function primerValor(objeto: Record<string, unknown>, claves: string[]): string | null {
  for (const clave of Object.keys(objeto)) {
    if (!claves.includes(normalizaClave(clave))) continue
    const valor = objeto[clave]
    if (typeof valor === 'string' && valor.trim()) return valor.trim()
    if (typeof valor === 'number' && Number.isFinite(valor)) return String(valor)
  }
  return null
}

/** Parte una linea CSV respetando las comillas dobles. No es un parser RFC completo: es el
 *  subconjunto que usan las exportaciones de una lista (nombre, cantidad, nota). */
function camposCSV(linea: string, delimitador: string): string[] {
  const campos: string[] = []
  let actual = ''
  let entreComillas = false
  for (let i = 0; i < linea.length; i += 1) {
    const c = linea[i]
    if (c === '"') {
      if (entreComillas && linea[i + 1] === '"') {
        actual += '"'
        i += 1
      } else {
        entreComillas = !entreComillas
      }
    } else if (c === delimitador && !entreComillas) {
      campos.push(actual)
      actual = ''
    } else {
      actual += c
    }
  }
  campos.push(actual)
  return campos.map((c) => c.trim())
}

function delimitadorCSV(linea: string): string {
  const candidatos = [',', ';', '\t']
  let mejor = ','
  let maximo = -1
  for (const candidato of candidatos) {
    // Se cuentan solo los que caen fuera de comillas; para el caso normal basta.
    const cuenta = camposCSV(linea, candidato).length
    if (cuenta > maximo) {
      maximo = cuenta
      mejor = candidato
    }
  }
  return mejor
}

function desdeColumnas(nombre: string, cantidad: string, nota: string): Pegada | null {
  const limpio = nombre.trim()
  if (!limpio) return null
  const partes = [cantidad.trim(), nota.trim()].filter(Boolean)
  return {
    nombre: limpio,
    cantidad: cantidad.trim() || null,
    unidad: null,
    nota: partes.join(' · '),
  }
}

function leeCSV(texto: string): LecturaPegado | null {
  const lineas = texto.replace(/^\uFEFF/, '').split(/\r?\n/).filter((l) => l.trim())
  if (lineas.length < 1) return null
  const delimitador = delimitadorCSV(lineas[0])
  const cabecera = camposCSV(lineas[0], delimitador).map(normalizaClave)
  const iNombre = cabecera.findIndex((c) => CLAVES_NOMBRE.includes(c))
  if (iNombre < 0) return null
  const iCantidad = cabecera.findIndex((c) => CLAVES_CANTIDAD.includes(c))
  const iNota = cabecera.findIndex((c) => CLAVES_NOTA.includes(c))
  const pegadas: Pegada[] = []
  let sinNombre = 0
  for (const linea of lineas.slice(1)) {
    const campos = camposCSV(linea, delimitador)
    const una = desdeColumnas(
      campos[iNombre] ?? '',
      iCantidad >= 0 ? (campos[iCantidad] ?? '') : '',
      iNota >= 0 ? (campos[iNota] ?? '') : '',
    )
    if (una) pegadas.push(una)
    else sinNombre += 1
  }
  const avisos = sinNombre
    ? [`${sinNombre} fila(s) sin nombre: no se han anadido.`]
    : []
  return { pegadas, formato: 'csv', avisos }
}

function leeJSON(texto: string): LecturaPegado | null {
  let datos: unknown
  try {
    datos = JSON.parse(texto)
  } catch {
    return null
  }
  const lista = Array.isArray(datos)
    ? datos
    : (datos && typeof datos === 'object'
      ? ((datos as Record<string, unknown>).productos
        ?? (datos as Record<string, unknown>).items
        ?? null)
      : null)
  if (!Array.isArray(lista)) return null

  const pegadas: Pegada[] = []
  let malas = 0
  for (const item of lista) {
    if (typeof item === 'string') {
      if (item.trim()) pegadas.push(partirCantidad(item))
      continue
    }
    if (!item || typeof item !== 'object') {
      malas += 1
      continue
    }
    const objeto = item as Record<string, unknown>
    const nombre = primerValor(objeto, CLAVES_NOMBRE)
    if (!nombre) {
      malas += 1
      continue
    }
    const cantidad = primerValor(objeto, CLAVES_CANTIDAD) ?? ''
    const nota = primerValor(objeto, CLAVES_NOTA) ?? ''
    const una = desdeColumnas(nombre, cantidad, nota)
    if (una) pegadas.push(una)
    else malas += 1
  }
  const avisos = malas ? [`${malas} elemento(s) sin nombre: no se han anadido.`] : []
  return { pegadas, formato: 'json', avisos }
}

/** Lee texto libre, CSV o JSON. **La cantidad siempre acaba en la nota**, nunca en un numero de
 *  envases: el formato de entrada no cambia esa regla. */
export function leerPegado(texto: string): LecturaPegado {
  const limpio = texto.trim()
  if (!limpio) return { pegadas: [], formato: 'texto', avisos: [] }

  if (limpio.startsWith('{') || limpio.startsWith('[')) {
    const json = leeJSON(limpio)
    if (json) return json
    return {
      pegadas: parteLoPegadoTexto(limpio),
      formato: 'texto',
      avisos: ['No se ha podido leer como JSON: se trata como texto libre.'],
    }
  }

  const csv = leeCSV(limpio)
  if (csv) return csv

  return { pegadas: parteLoPegadoTexto(limpio), formato: 'texto', avisos: [] }
}

/** La parte de siempre, sin volver a mirar el texto como CSV/JSON. */
function parteLoPegadoTexto(texto: string): Pegada[] {
  return texto
    .split(/\r?\n/)
    .map((l) => sinAdorno(l))
    .filter((l) => l.length > 0)
    .map((l) => partirCantidad(l))
}

export function resumenDeLaLectura(lectura: LecturaPegado): string {
  const base = resumenDeLaPrevia(lectura.pegadas)
  if (lectura.formato === 'texto') return base
  return `${base} Leido de un ${lectura.formato.toUpperCase()}.`
}
