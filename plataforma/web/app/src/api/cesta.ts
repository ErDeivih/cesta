/** La lista de la compra y quien ha entrado.
 *
 *  Es la parte de la API que necesita **sesion**: las listas y los favoritos son
 *  de cada uno, y el backend la lleva con una cookie. Por eso este fichero no usa
 *  `pide()` tal cual: hace falta mandar `credentials` en las peticiones que
 *  escriben, y `pide()` ya lo hace (`same-origin`), asi que vale la misma puerta.
 *
 *  Un solo origen (Caddy) es lo que hace que la cookie funcione sin CORS. Con dos
 *  origenes habria que pelear con `SameSite` y esto no funcionaria.
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
