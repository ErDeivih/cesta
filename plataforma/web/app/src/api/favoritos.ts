/** Los favoritos: los productos que se compran siempre.
 *
 *  Lo que los hace utiles no es la lista, es que **cada uno trae el estado de
 *  hoy** y vienen ordenados por lo que ha cambiado, no por alfabeto: lo que ha
 *  bajado arriba. Una lista de favoritos ordenada de la A a la Z hay que leerla
 *  entera para encontrar lo unico que importa, que es lo que se ha movido.
 *
 *  Necesita sesion, como la cesta: los favoritos son de cada uno.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { ErrorApi, pide } from './cliente'
import type { Favorito } from '../tipos'

/** Pide a la API con cuerpo, que `pide()` no hace: solo sabe de GET. */
async function conCuerpo<T>(ruta: string, metodo: 'POST' | 'DELETE',
                           cuerpo: unknown): Promise<T> {
  const respuesta = await fetch(`/api${ruta}`, {
    method: metodo,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify(cuerpo),
  })
  let detalle: string | null = null
  try {
    const json = await respuesta.json()
    if (typeof json?.detail === 'string') detalle = json.detail
  } catch {
    // Un 502 de Caddy delante de una API caida no es JSON.
  }
  if (!respuesta.ok) throw new ErrorApi(respuesta.status, detalle)
  return undefined as T
}

export async function verFavoritos(): Promise<Favorito[]> {
  const r = await pide<{ favoritos: Favorito[] }>('/favoritos')
  return r.favoritos ?? []
}

export function anadirFavorito(grupoId: number | null,
                              productoId: string | null) {
  return conCuerpo<{ hecho: boolean }>('/favoritos', 'POST', {
    grupo_id: grupoId, producto_id: productoId,
  })
}

export function quitarFavorito(grupoId: number | null,
                               productoId: string | null) {
  return conCuerpo<{ hecho: boolean }>('/favoritos', 'DELETE', {
    grupo_id: grupoId, producto_id: productoId,
  })
}

/** El boton de la ficha: guardar o quitar, y refrescar lo que dependa de ello. */
export function useFavorito() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: async (f: { grupoId: number | null; productoId: string | null;
                            dentro: boolean }) =>
      f.dentro ? quitarFavorito(f.grupoId, f.productoId)
               : anadirFavorito(f.grupoId, f.productoId),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['favoritos'] }),
  })
}
