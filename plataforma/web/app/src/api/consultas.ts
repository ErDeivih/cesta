/** Las consultas a la API, con TanStack Query.
 *
 *  Query y no `useEffect` + `useState` porque la mitad de las pantallas miran
 *  los mismos datos: el estado de las cadenas lo usa la cabecera, el buscador y
 *  la ficha del grupo. Con Query se pide una vez y se comparte.
 *
 *  `staleTime` largo a proposito: gold cambia **una vez al dia**, cuando
 *  termina el pipeline. Refrescar cada vez que se cambia de pantalla es pedir
 *  lo mismo cuarenta veces para recibir la misma respuesta.
 */
import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { ErrorApi, pide } from './cliente'
import type {
  RespuestaBajadas,
  RespuestaBuscar,
  RespuestaEan,
  RespuestaEstado,
  RespuestaProducto,
  RespuestaSecciones,
  Grupo,
  PanelCadenas,
  PanelHistorico,
  PanelHoy,
  PanelMarcas,
  PanelMovidos,
} from '../tipos'

const CINCO_MIN = 5 * 60 * 1000
const UNA_HORA = 60 * 60 * 1000

/** Filtros del buscador, tal como viajan a `/api/buscar`. */
export interface FiltrosBuscar {
  q: string
  cadenas: string[]
  seccion: string
  comparables: boolean
  conNutricion: boolean
  ofertas: boolean
  marcaPropia: boolean
  sinAlcohol: boolean
  sellos: string[]
  conservacion: string
  limite: number
}

export const FILTROS_VACIOS: FiltrosBuscar = {
  q: '',
  cadenas: [],
  seccion: '',
  comparables: false,
  conNutricion: false,
  ofertas: false,
  marcaPropia: false,
  sinAlcohol: false,
  sellos: [],
  conservacion: '',
  limite: 40,
}

/** Por debajo de dos letras no se busca: `%l%` casa con media tienda y la
 *  respuesta tarda y no dice nada. La API de hoy no lo corta sola, asi que la
 *  decision se toma aqui y la pantalla lo explica en vez de quedarse en blanco. */
export function consultaUtil(f: FiltrosBuscar): boolean {
  return f.q.trim().length >= 2 || f.seccion !== ''
}

export function useEstado() {
  return useQuery({
    queryKey: ['estado'],
    queryFn: ({ signal }) => pide<RespuestaEstado>('/estado', undefined, signal),
    staleTime: CINCO_MIN,
  })
}

export function useBuscar(f: FiltrosBuscar) {
  return useQuery({
    queryKey: ['buscar', f],
    queryFn: ({ signal }) =>
      pide<RespuestaBuscar>(
        '/buscar',
        {
          q: f.q.trim(),
          cadenas: f.cadenas.join(','),
          seccion: f.seccion,
          comparables: f.comparables ? 'true' : '',
          con_nutricion: f.conNutricion ? 'true' : '',
          ofertas: f.ofertas ? 'true' : '',
          marca_propia: f.marcaPropia ? 'true' : '',
          sin_alcohol: f.sinAlcohol ? 'true' : '',
          sellos: f.sellos.join(','),
          conservacion: f.conservacion,
          limite: f.limite,
        },
        signal,
      ),
    enabled: consultaUtil(f),
    staleTime: CINCO_MIN,
    // Al cambiar un filtro, lo de antes se queda en pantalla mientras llega lo
    // nuevo. Sin esto, la lista parpadea a vacio en cada tecla.
    placeholderData: keepPreviousData,
  })
}

export function useSecciones(cadenas: string[]) {
  return useQuery({
    queryKey: ['secciones', cadenas],
    queryFn: ({ signal }) =>
      pide<RespuestaSecciones>('/secciones', { cadenas: cadenas.join(',') }, signal),
    staleTime: UNA_HORA,
  })
}

export function useGrupo(grupoId: number | null) {
  return useQuery({
    queryKey: ['grupo', grupoId],
    queryFn: ({ signal }) => pide<Grupo>(`/grupo/${grupoId}`, undefined, signal),
    enabled: grupoId !== null && Number.isFinite(grupoId),
    staleTime: CINCO_MIN,
  })
}

export function useProducto(fuente: string, idFuente: string) {
  return useQuery({
    queryKey: ['producto', fuente, idFuente],
    queryFn: ({ signal }) =>
      pide<RespuestaProducto>(`/producto/${fuente}/${idFuente}`, undefined, signal),
    enabled: Boolean(fuente) && Boolean(idFuente),
    staleTime: CINCO_MIN,
  })
}

export function useBajadas(dias: number, subidas: boolean, cadenas: string[]) {
  return useQuery({
    queryKey: ['bajadas', dias, subidas, cadenas],
    queryFn: ({ signal }) =>
      pide<RespuestaBajadas>(
        '/bajadas',
        { dias, subidas: subidas ? 'true' : '', cadenas: cadenas.join(',') },
        signal,
      ),
    staleTime: CINCO_MIN,
  })
}

/** El escaner. No es una consulta de fondo: se dispara al pulsar, y el 400 por
 *  un codigo que no es un codigo es una respuesta que hay que ensenar. */
export function useEan(codigo: string | null) {
  return useQuery({
    queryKey: ['ean', codigo],
    queryFn: ({ signal }) => pide<RespuestaEan>(`/ean/${codigo}`, undefined, signal),
    enabled: Boolean(codigo),
    retry: false,
    staleTime: UNA_HORA,
  })
}

export function usePanelHoy() {
  return useQuery({
    queryKey: ['panel', 'hoy'],
    queryFn: ({ signal }) => pide<PanelHoy>('/panel/hoy', undefined, signal),
    staleTime: CINCO_MIN,
  })
}

export function usePanelCadenas() {
  return useQuery({
    queryKey: ['panel', 'cadenas'],
    queryFn: ({ signal }) => pide<PanelCadenas>('/panel/cadenas', undefined, signal),
    staleTime: CINCO_MIN,
  })
}

export function usePanelMarcas() {
  return useQuery({
    queryKey: ['panel', 'marcas'],
    queryFn: ({ signal }) => pide<PanelMarcas>('/panel/marcas', undefined, signal),
    staleTime: CINCO_MIN,
  })
}

export function usePanelHistorico() {
  return useQuery({
    queryKey: ['panel', 'historico'],
    queryFn: ({ signal }) => pide<PanelHistorico>('/panel/historico', undefined, signal),
    staleTime: CINCO_MIN,
  })
}

export function usePanelMovidos() {
  return useQuery({
    queryKey: ['panel', 'movidos'],
    queryFn: ({ signal }) => pide<PanelMovidos>('/panel/movidos', undefined, signal),
    staleTime: CINCO_MIN,
  })
}

/** `GET /api/panel/matching` **todavia no existe**.
 *
 *  Se pide como si existiera, porque el dia que se implemente esta pantalla ya
 *  funciona. Mientras tanto el 404 no se reintenta (no va a aparecer solo) y no
 *  se pinta como un fallo: es "esa ruta aun no esta", que es otra cosa.
 */
export function usePanelMatching() {
  return useQuery({
    queryKey: ['panel', 'matching'],
    queryFn: ({ signal }) =>
      pide<Record<string, unknown>>('/panel/matching', undefined, signal),
    staleTime: CINCO_MIN,
    retry: (intento, error) => {
      if (error instanceof ErrorApi && error.estado < 500) return false
      return intento < 1
    },
  })
}
