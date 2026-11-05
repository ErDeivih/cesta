import { useEffect, useState } from 'react'

import { estaAtascada } from '../logica/espera.ts'

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
  /** *** El cuerpo entero de la respuesta, cuando lo hubo. ***
   *
   * *No es un adorno: **un 409 del cierre trae `cotizacion_nueva` y `sello_visto`**, y hasta hoy se tiraban
   * a la basura.* *La pantalla decia «no cuadra» y se acababa, cuando lo correcto es enseñar la cotizacion
   * nueva y pedir que se confirme otra vez.*
   *
   * *Se guarda **el cuerpo tal cual** y no campos sueltos: quien lo mire sabe que es lo que mando el
   * servidor, y el siguiente 409 que traiga otro dato no necesita tocar esta clase.*
   */
  readonly cuerpo: unknown

  constructor(estado: number, detalle: string | null, cuerpo: unknown = null) {
    // **El mensaje no nombra la API ni el código HTTP**: lo lee una persona, no quien programa.
    // El texto que se enseña de verdad lo elige `textoDeError`, que es el único sitio que traduce.
    super(detalle ?? 'No he podido cargar esto.')
    this.name = 'ErrorApi'
    this.estado = estado
    this.detalle = detalle
    this.cuerpo = cuerpo
  }
}

export function esErrorApi(e: unknown): e is ErrorApi {
  return e instanceof ErrorApi
}

/** El fallo es que no hay red, no que la API haya dicho que no.
 *
 *  `fetch` lanza `TypeError` cuando no puede ni salir del aparato, y ese es el
 *  caso de estar en un pasillo sin cobertura. **No es lo mismo que un error de la
 *  API**, y confundirlos se paga en la pantalla de la lista: un 403 o un 500 son
 *  fallos que hay que contar y mirar, y quedarse sin cobertura en un supermercado
 *  no -- es lo normal. Lo unico que hace falta saber es que el cambio **no se ha
 *  guardado** y que hay que volver a pulsar, dicho sin alarma.
 *
 *  Vive aqui, al lado de `textoDeError` y de la linea que ya trata `TypeError`
 *  como "sin conexion", porque el texto y la decision de pintarlo en rojo tienen
 *  que salir de la misma regla: dos comprobaciones distintas del mismo hecho
 *  acaban discrepando. */
export function esSinRed(e: unknown): boolean {
  return e instanceof TypeError
}

type Valor = string | number | boolean | null | undefined

/** Un texto legible para cualquier fallo, nunca "undefined". */
export function textoDeError(e: unknown): string {
  if (esErrorApi(e)) {
    // *** NI LA API NI EL CÓDIGO HTTP SE NOMBRAN AQUÍ. *** *
    //
    // *Esto lo lee quien compra, no quien programa, y era el texto que veían seis pantallas al
    // abrirlas sin sesión: «La API ha contestado 401».* *Un 401 no es un fallo: es que no ha
    // entrado nadie, y se dice con la salida puesta.* *Los demás estados se cuentan sin número:
    // el número no cambia lo que la persona puede hacer.*
    if (e.estado === 401) return 'Entra para ver esto.'
    if (e.detalle) return e.detalle
    if (e.estado === 404) return 'No existe.'
    if (e.estado >= 500) return 'No he podido completarlo. Vuelve a intentarlo.'
    return 'No he podido cargar esto.'
  }
  if (e instanceof TypeError) {
    // fetch lanza TypeError cuando no hay red. En el pasillo esto pasa.
    return 'Sin conexión. Esto es lo último que tengo.'
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

  if (!respuesta.ok) throw new ErrorApi(respuesta.status, detalleDe(cuerpo), cuerpo)
  return cuerpo as T
}


/** **Si una consulta lleva demasiado cargando, se dice.** *Y esto es un arreglo, no un adorno.*
 *
 *  **El problema, medido el 12 de octubre de 2026**: *React Query da `isLoading` mientras la consulta **no haya
 *  tenido nunca `data`** y **siga intentando**.* **Y si la consulta se atasca -- sin llegar a fallar --, `isLoading`
 *  es verdadero para siempre**, *y la pantalla dice «Cargando...» **indefinidamente***:
 *
 *  - *la cocina, con `refetchInterval`, se quedaba en «Cargando la cocina...» para siempre;*
 *  - *y la despensa, **que no tiene intervalo**, tambien.*
 *
 *  > **«Cargando» y «no ha llegado» se parecen en la pantalla y no se parecen en nada** -- *que es la misma
 *  > distincion que esta fase usa para «limite de fuente» y «pendiente».*
 *
 *  **Asi que a partir de `segundos`, la pantalla deja de decir «Cargando» y dice que no pudo preguntar.** *Y no se
 *  corta nada: **si la respuesta llega despues, se pinta igual** -- *lo unico que cambia es **que se deja de
 *  mentir mientras tanto**.*
 */
export function useSeAtasca(cargando: boolean, segundos = 10): boolean {
  // **Cuando empezo a cargar -- y eso es lo unico que hay que recordar.** *No un contador: **un instante.**
  //
  // *El primer intento guardaba un `setTimeout` con `[cargando]` en las dependencias, **y eso lo rompia**: cada vez
  // que `cargando` cambiaba de valor, **el reloj se cancelaba y empezaba de cero** -- *y `isLoading` de React Query
  // **oscila** cuando vuelve a intentar, asi que **el reloj nunca llegaba a los diez segundos** (medido el 12 de
  // octubre de 2026: la despensa seguia en «Cargando» a los doce).*
  //
  // > **Es la misma decision que `core/cocina.py` tomo con los temporizadores**: *un temporizador **no es una cuenta
  // > atras, es una hora de fin**.* **Y aqui: no hay que contar, hay que **recordar cuando empezo**.*
  const [empezo, setEmpezo] = useState<number | null>(null)

  useEffect(() => {
    // *La forma funcional de `setState` es lo que evita depender de `empezo`* -- *y por eso el efecto **solo** mira
    // `cargando`, que es lo unico que cambia de verdad.*
    setEmpezo((previo) => {
      if (!cargando) return null // *Si ya no carga, deja de haber atasco: **llego**.*
      return previo === null ? Date.now() : previo // *Y si ya habia empezado, **se respeta el instante**.*
    })
  }, [cargando])

  // **Y el tic que hace repintar.** *`setInterval` **no pide nada a nadie** -- es el reloj del aparato.*
  const [, setTic] = useState(0)
  useEffect(() => {
    const latido = setInterval(() => setTic((n) => n + 1), 1000)
    return () => clearInterval(latido)
  }, [])

  // *La decision la toma `estaAtascada`, que es pura y tiene sus pruebas; **aqui solo esta el reloj**.*
  return empezo !== null && estaAtascada(true, Date.now() - empezo, segundos)
}


