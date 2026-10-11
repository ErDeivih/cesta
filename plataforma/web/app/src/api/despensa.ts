/** La despensa: **lo que hay en casa, declarado** -- y no lo que se ha comprado.
 *
 *  Criterio de `F11`: *«existencias declaradas; **compra no acredita consumo ni stock restante**»*. Y eso
 *  **se ve en esta capa**: **no hay ninguna funcion que sume una compra**, porque **no hay ninguna ruta** que lo
 *  haga. *Si la ruta no existe, no se puede llamar.*
 *
 *  Necesita sesion, como la cesta: la despensa es de cada uno.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { ErrorApi, pide } from './cliente'

/** Pide a la API con cuerpo. *Devuelve el JSON, que es lo que la pantalla necesita para saber que paso.* */
async function conCuerpo<T>(ruta: string, cuerpo: unknown): Promise<T> {
  const respuesta = await fetch(`/api${ruta}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify(cuerpo),
  })
  let detalle: string | null = null
  const json = await respuesta.json().catch(() => null)
  if (typeof json?.detail === 'string') detalle = json.detail
  if (!respuesta.ok) throw new ErrorApi(respuesta.status, detalle)
  return json as T
}

export interface Existencia {
  texto: string
  /** **`null` quiere decir «no se sabe cuanto»**, y **no es un cero**. *Ver la migracion `017`.* */
  cantidad: number | null
  unidad: string
  donde: string
  caduca: string
  se_sabe: boolean
}

export interface RespuestaDespensa {
  existencias: Existencia[]
  /** **Cuantas no se sabe cuanto.** *Contarlas es lo que permite enseñarlo en vez de dejar que parezca un cero.* */
  sin_saber_cuanto: number
}

export async function verDespensa(): Promise<RespuestaDespensa> {
  const r = await pide<RespuestaDespensa>('/despensa')
  return { existencias: r.existencias ?? [], sin_saber_cuanto: r.sin_saber_cuanto ?? 0 }
}

/** Declarar lo que hay. *Y **sobrescribe**: declarar es decir lo que hay **ahora**.* */
export function declara(e: { texto: string; cantidad: number | null; unidad: string;
                             donde?: string; caduca?: string }) {
  return conCuerpo<Existencia>('/despensa', e)
}

/** Gastar. *Devuelve **el motivo** cuando no se puede -- *no esta declarado, no se sabe cuanto, o las unidades
 *  no se pueden convertir* --, y **la existencia se queda como estaba**.* */
export function consume(c: { texto: string; cantidad: number; unidad: string }) {
  return conCuerpo<{ texto: string; motivo: string; cantidad: number | null; unidad: string }>(
    '/despensa/consumir', c)
}

export function useDespensa() {
  return useQuery({ queryKey: ['despensa'], queryFn: verDespensa })
}
