/** Vistas guardadas: una combinacion de filtros con un nombre.
 *
 *  En `localStorage` porque **no hay endpoint de vistas guardadas** y no voy a
 *  inventarlo. Lo que se guarda es la cadena de consulta tal cual
 *  (`?sellos=sin-lactosa&cadenas=dia`), asi que una vista guardada es
 *  exactamente lo mismo que el enlace que se copiaria a mano.
 *
 *  Todo va envuelto en try/catch: en modo privado el navegador deja leer pero
 *  lanza al escribir, y una excepcion aqui tumbaria la pantalla entera por un
 *  adorno.
 */

const CLAVE = 'cesta.vistas.v1'

export interface VistaGuardada {
  nombre: string
  /** La cadena de consulta, con el `?` delante. */
  consulta: string
}

function esVista(x: unknown): x is VistaGuardada {
  if (typeof x !== 'object' || x === null) return false
  const v = x as Record<string, unknown>
  return typeof v['nombre'] === 'string' && typeof v['consulta'] === 'string'
}

export function leerVistas(): VistaGuardada[] {
  try {
    const crudo = window.localStorage.getItem(CLAVE)
    if (!crudo) return []
    const datos: unknown = JSON.parse(crudo)
    if (!Array.isArray(datos)) return []
    return datos.filter(esVista)
  } catch {
    // Dato corrupto de una version anterior: se empieza de cero en vez de
    // reventar la pantalla en cada carga.
    return []
  }
}

function escribir(vistas: VistaGuardada[]): VistaGuardada[] {
  try {
    window.localStorage.setItem(CLAVE, JSON.stringify(vistas))
  } catch {
    // Sin sitio o sin permiso: la vista no se guarda y la pantalla lo dice.
  }
  return vistas
}

export function guardarVista(nombre: string, consulta: string): VistaGuardada[] {
  const limpio = nombre.trim()
  if (!limpio) return leerVistas()
  // Una vista con el mismo nombre se sustituye: guardar dos veces "Sin lactosa"
  // y acabar con dos chips identicos no ayuda a nadie.
  const otras = leerVistas().filter((v) => v.nombre !== limpio)
  return escribir([...otras, { nombre: limpio, consulta }].slice(-40))
}

export function borrarVista(nombre: string): VistaGuardada[] {
  return escribir(leerVistas().filter((v) => v.nombre !== nombre))
}
