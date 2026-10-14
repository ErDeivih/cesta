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
  /** Las raciones que tiene la receta guardada. Distinta de `raciones`
   *  cuando se ha pedido para otras: son las dos cifras, y sin las dos no se sabe de donde sale. */
  raciones_receta?: number
  escalada?: boolean
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
export function useReceta(id: number | null, version?: number | null,
                     raciones?: number | null) {
  const cuenta = useClaveDeCuenta()
  return useQuery({
    queryKey: ['receta', cuenta, id, version ?? 'ultima', raciones ?? 'receta'],
    enabled: id !== null,
    queryFn: () => pide<Receta>(`/recetas/${id}`,
      { version: version ?? undefined, raciones: raciones ?? undefined }),
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
  /**
   * *** En que comida va, *que es **lo que da identidad a la ocurrencia.** *** *
   *
   * *El API la manda desde que el plan dejo de ser `(fecha, receta_id)`: *hoy la clave es
   * **`(fecha, comida, receta_id)`**, *asi que **la misma receta puede ir a la comida y a la cena
   * el mismo dia**, *y cada una **con sus raciones.** *
   *
   * *Y los valores son los de `core/diario.py:COMIDAS`* *-- «desayuno», «media manana», «comida»,
   * «merienda», «cena», «otras» --, *porque **el diario y el plan tienen que llamarlo igual.** *
   */
  comida: string
  /**
   * *** Las raciones **de esa vez**, *y `null` quiere decir «las de la receta».** *** *
   *
   * *No es un hueco: *es **la respuesta correcta** *cuando no se dijo nada. *Y **no se rellena aqui**
   * con las de la receta, *porque **el dia que la receta cambie**, *lo que se cocino **aquel dia
   * no cambia.** *
   */
  raciones: number | null
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

/** **La nutricion PREVISTA del plan**: lo que se **va** a comer, con su cobertura.
 *
 * *Y no es lo mismo que el diario: el diario es lo que **se comio**. Por eso son dos consultas y no una, y
 * por eso esta no escribe nada.*
 *
 * **Y `kcal` puede ser `null`, y no es cero**: *es que el ingrediente no resolvio a un producto, o que el
 * producto no declara energia. `motivo` dice cual de las dos, y `cobertura` dice **de cuantas lineas sale
 * cada numero** -- *sin eso, un hueco y una ausencia se verian igual.*
 */
export interface LineaDePrevision {
  texto: string
  producto_id: string | null
  nutrientes: Record<string, number | null> | null
  motivo: 'sin_catalogo' | 'sin_cantidad' | null
}

export interface ComidaDePrevision {
  fecha: string
  receta_id: number
  nombre: string | null
  version: number
  comensales: number
  lineas: LineaDePrevision[]
  conocido: Record<string, number | null>
  cobertura: Record<string, { con_dato: number; total: number; completa: boolean }>
  completo: boolean
}

export interface Prevision {
  desde: string
  hasta: string
  comidas: ComidaDePrevision[]
  /** ***Con su nombre***, como en `desde-la-compra`: *un ingrediente sin catalogo se conserva.* */
  sin_dato: string[]
  sin_cantidad: string[]
}

export function usePrevision(desde: string, hasta: string) {
  const cuenta = useClaveDeCuenta()
  return useQuery({
    queryKey: ['prevision', cuenta, desde, hasta],
    queryFn: () => pide<Prevision>('/recetas/plan/prevision', { desde, hasta }),
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

/**
 * *** El recibo de duplicar una semana, *y **sus dos numeros son el contrato.** *** *
 *
 * *`creadas` son las que **no estaban**, *y `ya_estaban` las que **se respetaron.** *Y las dos
 * **hacen falta**: *con solo `creadas`, *una semana que **ya estaba entera** devolveria **cero**,
 * *y quien lo leyera **no sabria si funciono o si no habia nada.** *
 *
 * *Es **la misma doctrina de B05**: *«*misma clave con contenido distinto produce *** conflicto,
 * no exito ficticio ***». *Decir «duplicado» cuando no se duplico nada **seria ese exito ficticio.** *
 */
export interface ReciboDeSemana {
  creadas: number
  ya_estaban: number
  desde: string
  hacia: string
}

/**
 * *** Copia lo planeado de una semana a otra. *** *
 *
 * *Y **no pisa lo que hay**: *lo que ya estaba **se respeta**, *y **vuelve contado** en `ya_estaban`.* *
 * *Por eso la pantalla **enseña el recibo** en vez de decir «hecho»: *porque **«hecho» no dice
 * si copio tres o ninguna.** *
 */
export function useDuplicarSemana() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: { desde: string; hacia: string }) =>
      conCuerpo<ReciboDeSemana>('/recetas/plan/semana', 'POST', datos),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['plan'] }),
  })
}

/** Una linea de la previa de compra. *Lo que habria que comprar, no lo que dice la receta.* */
export interface LineaDePrevia {
  clave: string
  texto: string
  producto_id: string | null
  cantidad: number
  unidad: string
  envases: number | null
  tamano_envase: number | null
  sobrante: number | null
  de_donde: string[]
}

export interface PreviaDeCompra {
  version: number
  raciones: number
  lineas: LineaDePrevia[]
  /** **Lo que NO se puede comprar, y por que.** *Sin cantidad, o en unidades incompatibles.* */
  sin_cantidad: string[]
  sin_consolidar: string[]
  nota: string
}

/** **Que se compraria. No escribe nada.** *Se mira antes de decidir.* */
export function usePreviaDeCompra(recetaId: number | null, version?: number | null) {
  return useQuery({
    queryKey: ['previa', recetaId, version ?? null],
    queryFn: () =>
      pide<PreviaDeCompra>(
        `/api/recetas/${recetaId}/a-la-lista` + (version ? `?version=${version}` : ''),
      ),
    enabled: recetaId !== null,
  })
}

/**
 * **Pasa la receta a la lista.** *Repetir no duplica: el servidor lleva la cuenta por operacion
 * -- receta, version y semana -- y la semana la calcula el.*
 *
 * *Y por eso **no manda ni el propietario ni la semana**: los dos son del servidor.*
 */
export function usePasarALista(recetaId: number) {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (listaId: string) =>
      conCuerpo(`/recetas/${recetaId}/a-la-lista`, 'POST', { lista_id: listaId }),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['listas'] }),
  })
}
