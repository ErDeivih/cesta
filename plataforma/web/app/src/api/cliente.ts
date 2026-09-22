/** El unico sitio del frontend que habla con el servidor.
 *
 *  Todo va por rutas relativas `/api/...`. Nunca `http://localhost:8000`:
 *  Caddy sirve la interfaz y manda `/api` al backend, asi que hay **un solo
 *  origen**. Con dos origenes el navegador mete CORS por medio y, el dia que
 *  haya cookies de sesion, se pierden por el camino.
 */

/** El error de la API, con su codigo, para poder distinguir un 404 de un 500.
 *
 *  El 404 del escaner no es un fallo: es una respuesta. Y el 404 de
 *  `/api/panel/matching` es "ese endpoint todavia no existe", que la pantalla
 *  tiene que contar tal cual en vez de pintar un error rojo.
 */
export class ErrorApi extends Error {
  readonly estado: number
  readonly detalle: string | null

  constructor(estado: number, detalle: string | null) {
    super(detalle ?? `La API ha contestado ${estado}.`)
    this.name = 'ErrorApi'
    this.estado = estado
    this.detalle = detalle
  }
}

export function esErrorApi(e: unknown): e is ErrorApi {
  return e instanceof ErrorApi
}

type Valor = string | number | boolean | null | undefined

/** Un texto legible para cualquier fallo, nunca "undefined". */
export function textoDeError(e: unknown): string {
  if (esErrorApi(e)) {
    if (e.detalle) return e.detalle
    if (e.estado === 404) return 'No existe.'
    if (e.estado >= 500) return 'El servidor ha fallado. Mira los registros de la API.'
    return `La API ha contestado ${e.estado}.`
  }
  if (e instanceof TypeError) {
    // fetch lanza TypeError cuando no hay red. En el pasillo esto pasa.
    return 'Sin conexion con casa. Esto es lo ultimo que hay en pantalla.'
  }
  if (e instanceof Error) return e.message
  return 'Fallo desconocido.'
}

function detalleDe(cuerpo: unknown): string | null {
  if (typeof cuerpo !== 'object' || cuerpo === null) return null
  const d = (cuerpo as Record<string, unknown>)['detail']
  if (typeof d === 'string') return d
  // FastAPI manda un 422 con `detail` como lista de errores de validacion.
  if (Array.isArray(d)) {
    return d
      .map((x) => {
        if (typeof x === 'object' && x !== null) {
          const m = (x as Record<string, unknown>)['msg']
          if (typeof m === 'string') return m
        }
        return null
      })
      .filter((m): m is string => m !== null)
      .join('. ')
  }
  return null
}

/** Pide a la API y devuelve el JSON ya tipado.
 *
 *  Los parametros vacios se omiten. Un `?sellos=` no es un filtro a medias: el
 *  backend lo lee como "sin filtro" y contesta otra cosa de la que parece.
 */
export async function pide<T>(
  ruta: string,
  parametros?: Record<string, Valor>,
  senal?: AbortSignal,
): Promise<T> {
  const url = new URL(`/api${ruta}`, window.location.origin)
  for (const [clave, valor] of Object.entries(parametros ?? {})) {
    if (valor === undefined || valor === null || valor === '') continue
    url.searchParams.set(clave, String(valor))
  }

  const respuesta = await fetch(url, {
    signal: senal,
    headers: { Accept: 'application/json' },
    credentials: 'same-origin',
  })

  let cuerpo: unknown = null
  try {
    cuerpo = await respuesta.json()
  } catch {
    // Un 502 de Caddy delante de una API caida no es JSON. Sin esto, el
    // `await respuesta.json()` tira un SyntaxError que no dice nada util.
  }

  if (!respuesta.ok) throw new ErrorApi(respuesta.status, detalleDe(cuerpo))
  return cuerpo as T
}
