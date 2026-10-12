/** Importar una receta: **la previa, que no guarda nada**.
 *
 *  Criterio de `R02`: *«URL/archivo de **fuente permitida**; **previa, fuente, unidades y edicion antes de
 *  guardar**»*.
 *
 *  **Y esta capa solo pide la previa**: *no hay ninguna funcion que guarde, porque **la pantalla no guarda** --
 *  lo que hace es **enseñar antes de decidir**, que es lo que el criterio pide.*
 */
import { ErrorApi } from './cliente'

export interface Ingrediente {
  texto: string
  cantidad: number | null
  unidad: string | null
  producto_id?: string | null
  grupo_id?: number | null
  fuente?: string | null
}

export interface Previa {
  nombre: string
  raciones: number
  minutos: number | null
  preparacion: string
  ingredientes: Ingrediente[]
  /** **De donde se importo.** *El criterio lo pide por su nombre, y es lo que permite re-comprobarla.* */
  fuente: string
  /** **Lo que no se pudo leer, y por que.** *No se rellena con ceros: **se cuenta**.* */
  faltantes: string[]
  guardada: boolean
}

/** **Pide la previa.** *Y cuando no se puede, **el error trae el motivo del servidor tal cual** -- *«la fuente no
 *  esta declarada: recetas.example.com»* --, que es lo que permite decir **que** ha pasado en vez de «error».* */
export async function verPrevia(url: string): Promise<Previa> {
  const r = await fetch('/api/recetas/importar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ url }),
  })
  let detalle: string | null = null
  const json = await r.json().catch(() => null)
  if (typeof json?.detail === 'string') detalle = json.detail
  if (!r.ok) throw new ErrorApi(r.status, detalle)
  return json as Previa
}
