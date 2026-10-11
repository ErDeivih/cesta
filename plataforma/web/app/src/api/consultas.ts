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
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { anadirLinea, crearLista, misListas, verLista, yo } from './cesta'
import { misAlertas } from './alertas'
import { ErrorApi, pide } from './cliente'
import type {
  RespuestaBajadas,
  RespuestaBuscar,
  RespuestaEan,
  RespuestaEstado,
  RespuestaHabituales,
  RespuestaIndice,
  RespuestaOfertasDudosas,
  RespuestaPosicion,
  RespuestaProducto,
  RespuestaSecciones,
  Grupo,
  PanelCadenas,
  PanelDonde,
  PanelHistorico,
  PanelHoy,
  PanelMarcas,
  PanelMatching,
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

/** Lo que ha bajado (o subido) de precio.
 *
 *  `soloMios` contesta a *"¿ha bajado algo de lo mio?"*, que es una de las cuatro
 *  preguntas con las que se abre la aplicacion. El filtro se hace **en el servidor**
 *  y no aqui: la respuesta viene recortada a 60, y filtrar despues dejaria fuera
 *  bajadas mias que no estan entre las sesenta mayores del catalogo.
 */
export function useBajadas(dias: number, subidas: boolean, cadenas: string[],
                           soloMios = false) {
  return useQuery({
    queryKey: ['bajadas', dias, subidas, cadenas, soloMios],
    queryFn: ({ signal }) =>
      pide<RespuestaBajadas>(
        '/bajadas',
        { dias, subidas: subidas ? 'true' : '', cadenas: cadenas.join(','),
          solo_mios: soloMios ? 'true' : '' },
        signal,
      ),
    staleTime: CINCO_MIN,
  })
}

/** El mosaico de lo habitual: "lo de siempre", para anadirlo de un toque.
 *
 *  Pide sesion, porque es el historial de compra de una persona. Y **el 404 no es un
 *  fallo**: mientras la imagen de la API que corre no tenga la ruta, esto contesta 404
 *  y la pantalla se queda como estaba -- con la tarjeta de la primera vez -- en vez de
 *  ensenar un error rojo por algo que todavia no se ha desplegado. No hace falta
 *  decirlo aqui: la regla de `main.tsx` **no reintenta un 4xx**, y quien decide que
 *  hacer con ese 404 es la pantalla.
 */
export function useHabituales(limite = 12) {
  return useQuery({
    queryKey: ['habituales', limite],
    queryFn: ({ signal }) =>
      pide<RespuestaHabituales>('/habituales', { limite }, signal),
    staleTime: CINCO_MIN,
  })
}

/** Los avisos de esta persona, y cuantos estan sin ver para el punto del icono.
 *
 *  Se pide en el armazon (la barra de abajo), asi que va con `staleTime` largo y solo
 *  cuando hay sesion: sin sesion la API contesta 401 y no hay nada que mirar.
 */
export function useAlertas() {
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  return useQuery({
    queryKey: ['alertas'],
    queryFn: misAlertas,
    enabled: sesion.data?.usuario != null,
    staleTime: CINCO_MIN,
  })
}

/** Cuantos avisos han saltado y nadie ha visto todavia.
 *
 *  **El punto cuenta lo que ha saltado, no lo que hay**: una alerta que existe y no se
 *  ha cumplido no es un aviso, es una promesa. Y `vista_en` es de la persona, no de la
 *  pantalla que se abre (`salto_en` es la otra mitad, y la pone el vigilante).
 */
export function useAvisosSinVer(): number {
  const { data } = useAlertas()
  return (data?.alertas ?? []).filter((a) => a.salto_en && !a.vista_en).length
}

/** **Cuantas lineas quedan por coger** en la lista de casa. Es el numero de la barra.
 *
 *  La pregunta 3 del encargo -- *"¿voy tachando bien?"* -- se contesta con este numero
 *  **sin abrir nada**: la interfaz vieja lo ponia en el icono de la lista
 *  (`app.js:507-509`, el `pin-lista`) y era lo unico que se podia leer de un vistazo con
 *  el carro en la mano. Servir `dist` sin esto era quitarle a la cesta la unica senal que
 *  se ve desde cualquier pantalla.
 *
 *  Se apoya en **las mismas claves de cache** que la cesta (`['yo']`, `['listas']` y
 *  `['lista', id]`), asi que abrir la cesta no pide nada dos veces. Sin sesion no se pide
 *  nada y devuelve 0 -- y si la peticion falla (sin cobertura) tambien, porque un cero
 *  callado es mejor que un aviso rojo en la barra de abajo: estar sin red en el pasillo no
 *  es un fallo de la aplicacion.
 */
export function usePorCoger(): number {
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: sesion.data?.usuario != null,
  })
  const listaId = listas.data?.find((l) => l.es_de_casa)?.id ?? listas.data?.[0]?.id ?? null
  const detalle = useQuery({
    queryKey: ['lista', listaId],
    queryFn: () => verLista(listaId as string),
    enabled: listaId != null,
  })
  return (detalle.data?.lineas ?? []).filter((l) => l.tachado_en === null).length
}

/** Lo que hay que decir en la entrada de Listas, **con las cuatro situaciones separadas**.
 *
 *  **Antes esto era un numero, y devolvia `0` en tres casos distintos**: mientras cargaba, si la
 *  peticion fallaba, y si de verdad no quedaba nada por coger. Tres cosas con la misma cara, y
 *  por eso no habia forma de saber si el contador estaba bien o roto. Medido el 11 de octubre de
 *  2026, persiguiendo el contador tres rondas: el cero silencioso era el problema.
 *
 *  Y ademas **elegia `?? listas[0]`** cuando no habia lista de casa: contaba una lista que no era
 *  la de casa **sin decirlo**. Aqui o es la de casa, o se dice que no hay.
 */
export type EstadoPorCoger =
  | { tipo: 'oculto' }
  | { tipo: 'cargando' }
  | { tipo: 'error' }
  | { tipo: 'sin-lista' }
  | { tipo: 'listo'; pendientes: number; lista: string }

export function usePorCogerDeCasa(): EstadoPorCoger {
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const conSesion = sesion.data?.usuario != null
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: conSesion,
  })
  // **Solo la de casa.** Sin `?? listas[0]`: si no hay lista de casa, no hay nada que contar y se
  // dice; elegir otra en silencio es contar una lista que nadie ha pedido.
  const casa = listas.data?.find((l) => l.es_de_casa) ?? null
  const detalle = useQuery({
    queryKey: ['lista', casa?.id],
    queryFn: () => verLista(casa?.id as string),
    enabled: casa != null,
  })

  if (sesion.isError) return { tipo: 'error' }
  if (sesion.isPending) return { tipo: 'cargando' }
  if (!conSesion) return { tipo: 'oculto' }
  if (listas.isError) return { tipo: 'error' }
  if (listas.isPending) return { tipo: 'cargando' }
  if (casa == null) return { tipo: 'sin-lista' }
  if (detalle.isError) return { tipo: 'error' }
  if (detalle.isPending) return { tipo: 'cargando' }
  const pendientes = (detalle.data?.lineas ?? [])
    .filter((l) => l.tachado_en === null).length
  return { tipo: 'listo', pendientes, lista: casa.nombre }
}

/** Anade un producto a la lista de casa, que es donde se apunta la compra.
 *
 *  **La cuadricula se usa de pie y con una mano**, asi que no hay dialogo ni selector
 *  de lista: un toque es un toque. La lista de casa es la de la compra de verdad; si
 *  no hay ninguna, se crea (mandar a otra pantalla a crearla seria justo el rodeo que
 *  esto quita). La cantidad no se pregunta aqui: se anade con 1 y se cambia en la
 *  cesta, que es donde se ve la lista entera.
 */
export function useAnadeALaCesta() {
  const cliente = useQueryClient()
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    staleTime: 60_000,
  })
  const destino = listas.data?.find((l) => l.es_de_casa) ?? listas.data?.[0] ?? null

  return useMutation({
    mutationFn: async (x: { grupoId: number; nombre: string }) => {
      const lista = destino ?? (await crearLista('Casa', true))
      await anadirLinea(lista.id, { nombre: x.nombre, grupo_id: x.grupoId,
                                    producto_id: null })
      return lista.id
    },
    onSuccess: (listaId) => {
      // Lo que hay en pantalla de esa lista ya no vale: la cesta la ensena con su
      // total y con donde sale mas barata, y las dos cosas cambian al anadir.
      cliente.invalidateQueries({ queryKey: ['listas'] })
      cliente.invalidateQueries({ queryKey: ['lista', listaId] })
      cliente.invalidateQueries({ queryKey: ['donde', listaId] })
    },
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

/** **Dónde comprar**: quién gana en cada pasillo, medido sobre los mismos productos.
 *
 *  Es la respuesta a *"¿dónde hago la compra?"* con la única medida que no depende del
 *  surtido de cada cadena: para cada producto comparable, el desvío respecto a la mediana
 *  de las OTRAS cadenas de su grupo. Lo que esta pantalla **no** dice es cuál es la cadena
 *  más barata en total, y lo dice el texto: cada cadena tiene su catálogo.
 */
export function usePanelDonde() {
  return useQuery({
    queryKey: ['panel', 'donde'],
    queryFn: ({ signal }) => pide<PanelDonde>('/panel/donde', undefined, signal),
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

/** **Las cadenas que tienes cerca**, de tus preferencias (`cadenas_cerca`).
 *
 *  Es lo que hace util el panel: quien tiene Alcampo y DIA a mano no necesita que
 *  las cinco le ensenen el indice, necesita que le ensenen el suyo. Va con la misma
 *  clave de cache que la sesion (`['yo']`) que usa el armazon, asi que no pide nada
 *  de mas; sin sesion devuelve lista vacia, que en el panel significa "las cinco".
 */
export function useCadenasCerca(): string[] {
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const v = sesion.data?.preferencias?.['cadenas_cerca']
  if (!Array.isArray(v)) return []
  return v.filter((x): x is string => typeof x === 'string')
}

/** El indice de precios por cadena. Sin `cadenas` en la URL se piden las cinco y
 *  el filtro se aplica al pintar: son cinco series y catorce puntos, y recortarlas
 *  en el servidor multiplicaria las respuestas por cada combinacion de filtro. */
export function useIndice() {
  return useQuery({
    queryKey: ['panel', 'indice'],
    queryFn: ({ signal }) => pide<RespuestaIndice>('/indice', undefined, signal),
    staleTime: CINCO_MIN,
  })
}

export function usePosicion() {
  return useQuery({
    queryKey: ['panel', 'posicion'],
    queryFn: ({ signal }) => pide<RespuestaPosicion>('/posicion', undefined, signal),
    staleTime: CINCO_MIN,
  })
}

/** Las ofertas que el historico no sostiene. El filtro de cadenas **si** va al
 *  servidor: la respuesta viene recortada a 60 y filtrar despues dejaria fuera
 *  ofertas de las cadenas que si te tocan. */
export function useOfertasDudosas(cadenas: string[], limite = 60) {
  return useQuery({
    queryKey: ['panel', 'dudosas', cadenas, limite],
    queryFn: ({ signal }) =>
      pide<RespuestaOfertasDudosas>(
        '/ofertas-dudosas',
        { limite, cadenas: cadenas.join(',') },
        signal,
      ),
    staleTime: CINCO_MIN,
  })
}

/** `GET /api/panel/matching` — el panel de auditoria del matching.
 *
 *  Existe en `plataforma/api/panel.py` desde el 22 de septiembre, pero la imagen
 *  de la API que corre puede ser anterior y contestar 404. Ese 404 **no se
 *  reintenta** (repetirlo no lo va a crear) y no se pinta como un fallo: es
 *  "esa ruta no está en el servidor que me atiende", que es otra cosa.
 *
 *  Lo que esta pantalla NO hace, y no va a hacer: aprobar ni rechazar pares.
 *  El endpoint es de solo lectura y aqui no hay un solo boton de escritura.
 */
export function usePanelMatching(limite = 20) {
  return useQuery({
    queryKey: ['panel', 'matching', limite],
    queryFn: ({ signal }) =>
      pide<PanelMatching>('/panel/matching', { limite }, signal),
    staleTime: CINCO_MIN,
    retry: (intento, error) => {
      if (error instanceof ErrorApi && error.estado < 500) return false
      return intento < 1
    },
  })
}
