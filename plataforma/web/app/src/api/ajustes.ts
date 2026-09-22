/** Las preferencias del usuario.
 *
 *  Hoy hay una que de verdad cambia lo que se ve: **`cadenas_cerca`**, las
 *  cadenas que se tienen a mano. Con ella puesta, el buscador y el panel ordenan
 *  y filtran por lo que se puede comprar de verdad, en vez de por las cinco.
 *
 *  Se guarda con `PUT /api/preferencias`, que necesita sesion.
 */
import { ErrorApi, pide } from './cliente'

export async function guardarPreferencia(clave: string, valor: unknown): Promise<void> {
  const respuesta = await fetch('/api/preferencias', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ clave, valor }),
  })
  let detalle: string | null = null
  try {
    const json = await respuesta.json()
    if (typeof json?.detail === 'string') detalle = json.detail
  } catch {
    // Un 502 de Caddy delante de una API caida no es JSON.
  }
  if (!respuesta.ok) throw new ErrorApi(respuesta.status, detalle)
}

/** Las cadenas de cerca, normalizadas: [] si no hay ninguna puesta. */
export function cadenasCerca(preferencias: Record<string, unknown> | undefined): string[] {
  const v = preferencias?.['cadenas_cerca']
  if (!Array.isArray(v)) return []
  return v.filter((x): x is string => typeof x === 'string')
}

/** El panel de hoy, para saber que cadenas existen de verdad. */
export async function cadenasConocidas(): Promise<string[]> {
  const r = await pide<{ estado?: unknown; cadenas?: { cadena: string }[] }>('/estado')
  return (r.cadenas ?? []).map((c) => c.cadena)
}
