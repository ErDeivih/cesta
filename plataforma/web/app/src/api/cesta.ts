/** La lista de la compra y quien ha entrado.
 *
 *  Es la parte de la API que necesita **sesion**: las listas y los favoritos son
 *  de cada uno, y el backend la lleva con una cookie. Por eso este fichero no usa
 *  `pide()` tal cual: hace falta mandar `credentials` en las peticiones que
 *  escriben, y `pide()` ya lo hace (`same-origin`), asi que vale la misma puerta.
 *
 *  Un solo origen (Caddy) es lo que hace que la cookie funcione sin CORS. Con dos
 *  origenes habria que pelear con `SameSite` y esto no funcionaria.
 *
 *  `pide()` solo sabe de GET. Lo que escribe (anadir y cambiar lineas, crear la
 *  lista de casa) pasa por `escribe()`, que es la misma puerta con metodo y
 *  cuerpo, y el mismo trato del error: `ErrorApi` con el `detail` de la API para
 *  que la pantalla pueda decir QUE ha fallado y no solo que fallo.
 */
import { ErrorApi, pide } from './cliente'
import type { Donde, Estimacion, Linea, Lista, Sesion } from '../tipos'

/** Entra con usuario y clave. La cookie la pone la API en la respuesta. */
export async function entrar(usuario: string, clave: string,
                             dispositivo = 'web'): Promise<void> {
  const respuesta = await fetch('/api/entrar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ usuario, clave, dispositivo }),
  })
  if (!respuesta.ok) {
    let detalle: string | null = null
    try {
      const cuerpo = await respuesta.json()
      if (typeof cuerpo?.detail === 'string') detalle = cuerpo.detail
    } catch {
      // Un 502 de Caddy no es JSON: el detalle se queda en null.
    }
    throw new ErrorApi(respuesta.status, detalle)
  }
}

/** Sale: borra la cookie. */
export async function salir(): Promise<void> {
  await fetch('/api/salir', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  })
}

/** Quien esta dentro, si hay alguien. Nunca falla: sin sesion devuelve null. */
export async function yo(): Promise<Sesion> {
  try {
    return await pide<Sesion>('/yo')
  } catch {
    return { usuario: null, preferencias: {} }
  }
}

export async function misListas(): Promise<Lista[]> {
  const r = await pide<{ listas: Lista[] }>('/listas')
  return r.listas ?? []
}

/** Una lista nueva. Hace falta para la de casa: quien entra por primera vez no
 *  tiene ninguna y sin esto no habria donde anadir nada. */
export async function crearLista(nombre: string, esDeCasa = false): Promise<Lista> {
  return await escribe<Lista>('/listas', 'POST', { nombre, es_de_casa: esDeCasa })
}

export interface DetalleLista {
  papel: string
  lineas: Linea[]
  estimacion: Estimacion
  personas: unknown[]
  fecha_datos: string
}

export async function verLista(id: string): Promise<DetalleLista> {
  return await pide<DetalleLista>(`/listas/${encodeURIComponent(id)}`)
}

/** Donde sale mas barata la lista entera. Con las ofertas puestas. */
export async function donde(id: string,
                            cadenas?: string[]): Promise<Donde> {
  return await pide<Donde>(`/listas/${encodeURIComponent(id)}/donde`, {
    cadenas: cadenas?.length ? cadenas.join(',') : undefined,
  })
}

/* ---------------------------------------------------------------- escribir -- */

/** Escribe en la API y devuelve el JSON. `pide()` es solo GET.
 *
 *  Esto ya existe dentro de `api/favoritos.ts` (`conCuerpo`). No se sube a
 *  `cliente.ts` en este encargo porque alli vive la funcion que usan todas las
 *  pantallas, y mover eso por dos llamadas es un cambio que hay que revisar en
 *  sitios que no tienen nada que ver con la cesta.
 */
async function escribe<T>(ruta: string, metodo: 'POST' | 'PATCH',
                          cuerpo: unknown): Promise<T> {
  const respuesta = await fetch(`/api${ruta}`, {
    method: metodo,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify(cuerpo),
  })
  let dato: unknown = null
  let detalle: string | null = null
  try {
    const json = await respuesta.json()
    dato = json
    if (typeof json?.detail === 'string') detalle = json.detail
  } catch {
    // Un 502 de Caddy delante de una API caida no es JSON: el detalle se queda
    // en null y el codigo de estado ya cuenta lo que hay que contar.
  }
  if (!respuesta.ok) throw new ErrorApi(respuesta.status, detalle)
  return dato as T
}

/** Un id de linea. Lo genera el cliente, no el servidor, y no es un capricho:
 *  la API hace `ON CONFLICT (id) DO UPDATE`, asi que el reintento actualiza la
 *  linea en vez de duplicarla. Sin eso, el pasillo con mala cobertura acaba con
 *  la leche tres veces en la lista.
 *
 *  `crypto.randomUUID` solo existe en **contexto seguro** (https o localhost), y
 *  esta aplicacion se sirve por http en el 8080, tambien por la IP de Tailscale:
 *  ahi no esta definido. El respaldo usa `getRandomValues`, que si existe en
 *  http, y saca los mismos 16 bytes con la version y la variante de un uuid v4.
 */
function idDeLinea(): string {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const b = crypto.getRandomValues(new Uint8Array(16))
  b[6] = (b[6] & 0x0f) | 0x40
  b[8] = (b[8] & 0x3f) | 0x80
  const hex = [...b].map((x) => x.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

/** El cuerpo de `POST /listas/{id}/lineas`. Los nombres son los de la API. */
export interface NuevaLinea {
  nombre: string
  grupo_id: number | null
  producto_id: string | null
  cantidad?: number
  nota?: string | null
}

/** Anade una linea a la lista. */
export async function anadirLinea(listaId: string, linea: NuevaLinea): Promise<void> {
  await escribe(`/listas/${encodeURIComponent(listaId)}/lineas`, 'POST', {
    id: idDeLinea(),
    // Cantidad 1 y sin nota es lo que hace la interfaz vieja (`anade`, app.js:614):
    // desde la ficha se dice QUE se compra, no cuanto. El cuanto se cambia en la
    // cesta, que es donde se ve la lista entera.
    cantidad: 1,
    nota: null,
    ...linea,
  })
}

/** El cuerpo de `PATCH /listas/{id}/lineas/{linea_id}`. Todo es opcional. */
export interface CambioLinea {
  tachado?: boolean
  en_carrito?: boolean
  /** 1..99: fuera de ahi la API contesta 422. */
  cantidad?: number
  nota?: string | null
  borrado?: boolean
  momento?: string
}

/** Cambia una linea: tacharla, cambiar la cantidad o borrarla. */
export async function cambiarLinea(listaId: string, lineaId: string,
                                   cambio: CambioLinea): Promise<void> {
  await escribe(`/listas/${encodeURIComponent(listaId)}/lineas/${encodeURIComponent(lineaId)}`,
    'PATCH', {
      // La hora del movil, no la de llegada: tachar sin cobertura a las 18:04 y
      // subirlo a las 18:20 tiene que contar como las 18:04, o el servidor se
      // inventa el orden de los hechos. Se manda en todos los cambios porque la
      // API solo la usa para decidir quien gano al tachar, y ahi hace falta.
      momento: new Date().toISOString(),
      ...cambio,
    })
}
