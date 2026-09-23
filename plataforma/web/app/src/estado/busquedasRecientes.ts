/** Las ultimas busquedas, para no volver a escribirlas.
 *
 *  Lo pide el encargo (§8, «los detalles que hacen que parezca terminada»): *"que
 *  recuerde las ultimas busquedas y que no exija pulsar una lupa"*. Y no es un
 *  adorno en esta aplicacion: la compra se repite **cada semana**, y "leche entera"
 *  es la misma busqueda de la semana pasada. Escribirla otra vez, de pie en el
 *  pasillo, con una mano, es justo el trabajo que hay que quitar.
 *
 *  En `localStorage` porque **no hay endpoint para esto** y no se va a inventar: es
 *  del aparato, no de la persona, y no tiene por que viajar. Si algun dia hay dos
 *  moviles, cada uno recuerda lo suyo, que es lo que se espera.
 *
 *  Todo va envuelto en try/catch: en modo privado el navegador deja leer pero lanza
 *  al escribir, y una excepcion aqui tumbaria el buscador entero por un adorno.
 */

const CLAVE = 'cesta.busquedas.v1'

/** Cuantas se recuerdan. Ocho caben en dos filas de chips en un movil; veinte no. */
export const CUANTAS = 8

/** Por debajo de esto no es una busqueda, es estar escribiendo. */
export const MINIMO = 3

function esTexto(x: unknown): x is string {
  return typeof x === 'string' && x.trim().length >= MINIMO
}

export function leerBusquedas(): string[] {
  try {
    const crudo = window.localStorage.getItem(CLAVE)
    if (!crudo) return []
    const datos: unknown = JSON.parse(crudo)
    if (!Array.isArray(datos)) return []
    return datos.filter(esTexto).slice(0, CUANTAS)
  } catch {
    // Dato corrupto de una version anterior: se empieza de cero en vez de
    // reventar el buscador en cada carga.
    return []
  }
}

function escribir(busquedas: string[]): string[] {
  try {
    window.localStorage.setItem(CLAVE, JSON.stringify(busquedas))
  } catch {
    // Sin sitio o sin permiso: la busqueda no se recuerda y ya esta.
  }
  return busquedas
}

/** Apunta una busqueda. La mas reciente va primera y **no se repite**.
 *
 *  Lo de no repetir importa mas de lo que parece: sin eso, buscar "leche" cinco
 *  semanas seguidas llena la lista con "leche" cinco veces y tapa todo lo demas.
 *  Se compara sin distinguir mayusculas ni espacios sobrantes, porque "Leche " y
 *  "leche" son la misma busqueda para quien la escribe.
 */
export function apuntaBusqueda(texto: string): string[] {
  const limpio = texto.trim()
  if (limpio.length < MINIMO) return leerBusquedas()
  const ya = leerBusquedas()
  const otras = ya.filter((b) => b.toLowerCase() !== limpio.toLowerCase())
  return escribir([limpio, ...otras].slice(0, CUANTAS))
}

export function olvidaBusquedas(): string[] {
  return escribir([])
}
