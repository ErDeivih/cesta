/** El modo cocina: **por donde ibas**, y temporizadores que sobreviven a la pantalla.
 *
 *  Criterio de `F10`: *«paso actual, ingredientes usados, temporizadores y **reanudacion sin conexion**»*.
 *
 *  **Y lo que hace que esto no sea un contador**: *un temporizador **no es una cuenta atras, es una hora de
 *  fin**.* Lo que se guarda es **cuando empezo**, y **lo que queda se calcula al leer** -- *asi que **reanudar es
 *  volver a leer**, y **funciona con la pantalla apagada, recargada o sin conexion***, porque **no hay nada que
 *  consultar**: el reloj lo lleva el aparato.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { ErrorApi, pide } from './cliente'

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

export interface Temporizador {
  paso: number | null
  minutos: number
  /** **El instante en que acaba.** *Y **es lo que hace que esto funcione sin conexion**: *con el numero ya
   *  calculado, al cortar la red **no hay nada que recalcular** y el numero se queda congelado (medido el 12 de
   *  octubre de 2026). **Con el instante, resta el aparato**, que es quien tiene el reloj.*
   */
  acaba_en: string
  /** *Lo que quedaba cuando el servidor contesto.* **Se conserva, pero la pantalla no lo usa para el reloj.** */
  queda_segundos: number
  terminado: boolean
}

export interface Reanudada {
  paso: number | null
  paso_actual: string | null
  usados: string[]
  hechos: number
  temporizadores: Temporizador[]
}

/** **Volver a la cocina.** *No guarda nada y no cambia nada: solo lee y calcula.* */
export async function reanudar(recetaId: number, version: number): Promise<Reanudada> {
  const r = await pide<Reanudada>(`/cocina/${recetaId}?version=${version}`)
  return { paso: r.paso ?? null, paso_actual: r.paso_actual ?? null,
           usados: r.usados ?? [], hechos: r.hechos ?? 0,
           temporizadores: r.temporizadores ?? [] }
}

export function empezar(recetaId: number, version: number) {
  return conCuerpo<{ paso: number }>('/cocina', { receta_id: recetaId, version, paso: 0 })
}

export function irAlPaso(recetaId: number, version: number, paso: number) {
  return conCuerpo<{ paso: number }>('/cocina/paso',
    { receta_id: recetaId, version, paso })
}

export function apuntaUsado(recetaId: number, version: number, texto: string) {
  return conCuerpo<{ usados: string[] }>('/cocina/usado',
    { receta_id: recetaId, version, texto })
}

/** **Poner un temporizador: se manda la DURACION, no lo que queda.** *El servidor guarda cuando empezo.* */
export function ponTemporizador(recetaId: number, version: number, minutos: number) {
  return conCuerpo<{ acaba_en: string }>('/cocina/temporizador',
    { receta_id: recetaId, version, minutos })
}

export function useCocina(recetaId: number, version: number) {
  return useQuery({
    queryKey: ['cocina', recetaId, version],
    queryFn: () => reanudar(recetaId, version),
    // **El refresco, SOLO cuando ya hay datos.** *Y esto es un arreglo, no un ajuste.*
    //
    // *Antes era `refetchInterval: 15000` a secas, y **eso es lo que dejaba la pantalla en «Cargando la cocina...»
    // para siempre** (medido el 12 de octubre de 2026):* **React Query da `isPending` mientras no haya tenido
    // nunca `data`** *y **el intervalo la vuelve a disparar antes de que el primer intento se resuelva**, asi que
    // el estado observable **nunca sale de `pending`** -- *y como `isPending` es verdadero, **la pantalla se queda
    // cargando aunque no haya ningun error***.
    //
    // **Y se comprobo que la red no tiene la culpa**: *veinte peticiones seguidas a `/api/cocina/7?version=2`
    // desde la propia pagina dieron **veinte `200`**.* *El fallo estaba **en la consulta**, no en la fontaneria.*
    //
    // **Con la condicion, el primer intento termina** -- *en `success` o en `error`, pero **termina*** --, **y el
    // refresco empieza despues**, que es cuando sirve: *para que lo que queda baje sin recargar.*
    refetchInterval: (consulta) => (consulta.state.data ? 15000 : false),
  })
}

export function useEmpieza(recetaId: number, version: number) {
  const c = useQueryClient()
  return useMutation({
    mutationFn: () => empezar(recetaId, version),
    onSuccess: () => c.invalidateQueries({ queryKey: ['cocina', recetaId, version] }),
  })
}
