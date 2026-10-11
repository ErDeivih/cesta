/** El diario: lo que se comio, con lo que se sabe y lo que no.
 *
 *  El tipo `Dia` trae las tres cosas separadas a proposito -- `conocido`, `sin_dato` y `completo` --
 *  porque juntarlas en un solo total es justo lo que el encargo prohibe.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { ErrorApi, pide } from './cliente'
import { useClaveDeCuenta } from './cuenta'

export type Entrada = {
  id: number
  fecha: string
  comida: string
  tipo: string
  referencia: string | null
  version: string | null
  cantidad_g: number | null
  kcal: number | null
  proteinas_g: number | null
  grasas_g: number | null
  hidratos_g: number | null
  fuente_dato: string
  nota: string
}

export type Conocido = {
  entradas: number
  kcal: number | null
  proteinas_g: number | null
  grasas_g: number | null
  hidratos_g: number | null
}

export type Dia = {
  fecha: string
  entradas: Entrada[]
  comidas: Record<string, Entrada[]>
  conocido: Conocido
  /** **Cobertura por nutriente**: de cuantas entradas sale cada numero. Sin esto, "600 kcal" se
   *  lee como el dia entero. */
  cobertura: Record<string, { con_dato: number; total: number; completa: boolean }>
  sin_dato: number[]
  completo: boolean
}

/** El alta desde una ficha. Los valores van por 100 g **tal como los publica la ficha**: el
 *  servidor escala por los gramos y **de lo que la ficha no traiga no anota cero, anota `null`**. */
export type FichaNueva = {
  fecha: string
  comida: string
  referencia: string
  gramos: number
  /** Los campos de la ficha por 100 g; `null`/ausente es desconocido, no cero. */
  producto: Record<string, unknown>
  nota?: string
}

export type NuevaEntrada = {
  /** **La clave de la operación**, y es lo que impide que un doble clic duplique.** Se genera al
   *  enviar y viaja **dentro de los datos**, así que un reintento de la misma operación la repite;
   *  y al limpiarse tras el alta, la siguiente genera otra. Dos comidas iguales de verdad llevan
   *  claves distintas y se registran las dos: no se deduplica por parecido. */
  clave_operacion?: string | null
  fecha: string
  comida: string
  tipo: string
  referencia: string | null
  version: string | null
  cantidad_g: number | null
  kcal: number | null
  proteinas_g: number | null
  grasas_g: number | null
  hidratos_g: number | null
  fuente_dato: string
  nota: string
}

async function conCuerpo<T>(ruta: string, metodo: 'POST' | 'DELETE', cuerpo?: unknown): Promise<T> {
  const respuesta = await fetch(`/api${ruta}`, {
    method: metodo,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    credentials: 'same-origin',
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  })
  let detalle: string | null = null
  try {
    const json = (await respuesta.json()) as { detail?: unknown }
    if (typeof json?.detail === 'string') detalle = json.detail
  } catch {
    // Un 502 de Caddy delante de una API caida no es JSON.
  }
  if (!respuesta.ok) throw new ErrorApi(respuesta.status, detalle)
  // **El recibo del servidor se devuelve, no se tira.** Antes esto era `return undefined as T`, y
  // por eso el puente de la compra decia «se han anotado N» con el numero de **la previa** en vez
  // de con lo que el servidor habia anotado de verdad: si la previa y el resultado no coinciden
  // -- lineas que ya estaban, o que dejaron de estar --, el mensaje miente. El servidor ya
  // devuelve `{id, dia}` al apuntar y `{entrada}` desde ficha; esto lo entrega.
  const texto = await respuesta.text()
  if (!texto) return undefined as T
  return JSON.parse(texto) as T
}

export function useDia(fecha: string) {
  const cuenta = useClaveDeCuenta()
  return useQuery({
    queryKey: ['diario', cuenta, fecha],
    queryFn: () => pide<Dia>(`/diario/${fecha}`),
  })
}

/** Lo que el servidor devuelve al apuntar: **el identificador de la entrada y el dia entero**
 *  recalculado. Es el recibo, y es lo unico que puede sostener un mensaje de exito. */
export type ReciboDeAlta = { id: number; dia: Dia }

/** Lo que el servidor devuelve al anotar desde una ficha: la entrada ya calculada. */
export type ReciboDeFicha = { entrada: Entrada }

export function useApuntar() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: NuevaEntrada) => conCuerpo<ReciboDeAlta>('/diario', 'POST', datos),
    onSuccess: () => {
      // **El dia y los rangos.** Invalidar solo `['diario']` dejaba las tendencias con el dato
      // viejo: usan `['diario-rango', ...]`, que es otra clave. Medido el 11 de octubre de 2026.
      void cliente.invalidateQueries({ queryKey: ['diario'] })
      void cliente.invalidateQueries({ queryKey: ['diario-rango'] })
    },
  })
}

/** Alta desde una ficha del catalogo: **la cuenta la hace el servidor** con los valores por 100 g. */
export function useApuntarDesdeFicha() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: FichaNueva) => conCuerpo<ReciboDeFicha>('/diario/desde-ficha', 'POST', datos),
    onSuccess: () => {
      void cliente.invalidateQueries({ queryKey: ['diario'] })
      void cliente.invalidateQueries({ queryKey: ['diario-rango'] })
    },
  })
}

export function useBorrarEntrada(fecha: string) {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => conCuerpo<{ borrada: number }>(`/diario/entrada/${id}`, 'DELETE'),
    onSuccess: () => {
      void cliente.invalidateQueries({ queryKey: ['diario'] })
      // Y los rangos, por lo mismo que al apuntar: borrar tambien mueve las tendencias.
      void cliente.invalidateQueries({ queryKey: ['diario-rango'] })
    },
  })
}

export type DiaResumen = {
  fecha: string
  entradas: number
  con_dato: number
  /** **`null` cuando ninguna entrada del dia trae energia.** No es cero: es que no se sabe. */
  kcal_conocida: number | null
  sin_dato: number
  completo: boolean
}

export function useRango(desde: string, hasta: string) {
  const cuenta = useClaveDeCuenta()
  return useQuery({
    queryKey: ['diario-rango', cuenta, desde, hasta],
    queryFn: () => pide<{ dias: DiaResumen[] }>('/diario/rango', { desde, hasta }),
  })
}
