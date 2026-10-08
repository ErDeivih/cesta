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
  sin_dato: number[]
  completo: boolean
}

export type NuevaEntrada = {
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
  return undefined as T
}

export function useDia(fecha: string) {
  const cuenta = useClaveDeCuenta()
  return useQuery({
    queryKey: ['diario', cuenta, fecha],
    queryFn: () => pide<Dia>(`/diario/${fecha}`),
  })
}

export function useApuntar() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: NuevaEntrada) => conCuerpo('/diario', 'POST', datos),
    onSuccess: (_r, datos) => cliente.invalidateQueries({ queryKey: ['diario'] }),
  })
}

export function useBorrarEntrada(fecha: string) {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => conCuerpo(`/diario/entrada/${id}`, 'DELETE'),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['diario'] }),
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
