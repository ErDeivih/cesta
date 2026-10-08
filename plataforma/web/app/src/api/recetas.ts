/** Las recetas: el recetario y sus versiones.
 *
 *  `pide()` solo sabe de GET, asi que el resto va por el mismo camino que los favoritos: un `fetch` con
 *  cuerpo y el detalle del error sacado del JSON, porque la API contesta el motivo en `detail` y ese
 *  motivo es lo que hay que enseñar (por ejemplo, que una compra no es consumo).
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { ErrorApi, pide } from './cliente'
import { useClaveDeCuenta } from './cuenta'

export type Ingrediente = {
  texto: string
  cantidad?: number | null
  unidad?: string | null
  producto_id?: string | null
  grupo_id?: number | null
  fuente?: string | null
}

export type Receta = {
  id: number
  nombre: string
  creada: string
  archivada: boolean
  version: number
  raciones: number
  preparacion: string
  minutos: number | null
  etiquetas: string
  ingredientes: Ingrediente[]
}

export type ResumenReceta = {
  id: number
  nombre: string
  creada: string
  archivada: boolean
  version: number
  raciones: number
  minutos: number | null
  etiquetas: string
}

export type NuevaReceta = {
  nombre: string
  raciones: number
  preparacion: string
  ingredientes: Ingrediente[]
  minutos: number | null
  etiquetas: string
}

async function conCuerpo<T>(ruta: string, metodo: 'POST' | 'PUT', cuerpo: unknown): Promise<T> {
  const respuesta = await fetch(`/api${ruta}`, {
    method: metodo,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify(cuerpo),
  })
  let detalle: string | null = null
  try {
    const json = (await respuesta.json()) as { detail?: unknown }
    if (typeof json?.detail === 'string') detalle = json.detail
  } catch {
    // Un 502 de Caddy delante de una API caida no es JSON.
  }
  if (!respuesta.ok) throw new ErrorApi(respuesta.status, detalle)
  return undefined as T
}

export function useRecetas(incluirArchivadas = false) {
  const cuenta = useClaveDeCuenta()
  return useQuery({
    queryKey: ['recetas', cuenta, incluirArchivadas],
    queryFn: () => pide<{ recetas: ResumenReceta[] }>('/recetas', { incluir_archivadas: incluirArchivadas }),
  })
}

/** Una receta concreta. Con `version`, **esa** version: es lo que permite ver que la vieja no se mueve. */
export function useReceta(id: number | null, version?: number | null) {
  const cuenta = useClaveDeCuenta()
  return useQuery({
    queryKey: ['receta', cuenta, id, version ?? 'ultima'],
    enabled: id !== null,
    queryFn: () => pide<Receta>(`/recetas/${id}`, { version: version ?? undefined }),
  })
}

export function useCrearReceta() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: NuevaReceta) => conCuerpo('/recetas', 'POST', datos),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['recetas'] }),
  })
}

export function useCambiarReceta(id: number) {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: Partial<NuevaReceta>) => conCuerpo(`/recetas/${id}`, 'PUT', datos),
    onSuccess: () => {
      cliente.invalidateQueries({ queryKey: ['recetas'] })
      cliente.invalidateQueries({ queryKey: ['receta', id] })
    },
  })
}

export function useArchivarReceta() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => conCuerpo(`/recetas/${id}/archivar`, 'POST', {}),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['recetas'] }),
  })
}

export type LineaPlan = {
  fecha: string
  comensales: number
  version: number
  receta_id: number
  nombre: string
}

export function usePlan(desde: string, hasta: string) {
  const cuenta = useClaveDeCuenta()
  return useQuery({
    queryKey: ['plan', cuenta, desde, hasta],
    queryFn: () => pide<{ plan: LineaPlan[] }>('/recetas/plan', { desde, hasta }),
  })
}

export function usePlanificar() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: { fecha: string; receta_id: number; comensales: number }) =>
      conCuerpo('/recetas/plan', 'POST', datos),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['plan'] }),
  })
}
