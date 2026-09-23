/** Los cambios que no han llegado al servidor, guardados en el movil.
 *
 *  Es la pieza que le faltaba al §3.5 del encargo: *"que tachar funcione igual sin red,
 *  sin ruedecita ni error"*, *"una linea discreta cuando hay cambios sin subir"* y *"al
 *  volver, se suba solo y se diga en una frase"*. La mecanica de la API ya estaba desde
 *  el primer dia -- **el identificador de linea lo genera el movil** y cada cambio viaja
 *  con **su hora** (`momento`), y existe `POST /listas/{id}/sincronizar` para subirlos
 *  todos de golpe --; lo que no existia era guardarlos.
 *
 *  **Por que en el movil y no en el servidor**: la lista se usa en el supermercado, que
 *  es donde peor va la red. Un cambio que no ha llegado al servidor no puede vivir en el
 *  servidor, obviamente; y guardarlo aqui es lo que hace que tachar **funcione igual**
 *  sin cobertura en vez de dar un error que hay que leer y reintentar.
 *
 *  Tres reglas, y las tres importan:
 *
 *  1. **La hora es la del movil** (`momento`), y se pone al tocar, no al subir. Tachar a
 *     las 18:04 sin cobertura y subirlo a las 18:20 tiene que contar como las 18:04; si
 *     no, el servidor se inventa el orden de los hechos. Es la misma razon que esta
 *     escrita en `api/cesta.ts`.
 *  2. **Un cambio por linea, gana el ultimo.** Tachar y destachar dos veces sin cobertura
 *     no son dos cambios que haya que subir en orden: es uno, el ultimo. La API es
 *     idempotente, pero mandar la historia entera es ruido.
 *  3. **Nada de `try/catch` tragandose fallos**: en modo privado el navegador deja leer y
 *     lanza al escribir. Si no se puede guardar, se dice (`null`), y la pantalla lo
 *     cuenta -- que la cola no se pueda guardar es justo lo que hay que saber.
 */

export interface CambioPendiente {
  lineaId: string
  /** Lo mismo que manda `PATCH /listas/{id}/lineas/{linea_id}`, sin la hora. */
  cambio: {
    tachado?: boolean
    en_carrito?: boolean
    cantidad?: number
    nota?: string | null
    borrado?: boolean
  }
  /** La hora DEL MOVIL, en ISO. Se pone al tocar y no se toca mas. */
  momento: string
}

const CLAVE = 'cesta.cola.v1'

type Cola = Record<string, CambioPendiente[]>

function leerTodo(): Cola {
  try {
    const crudo = window.localStorage.getItem(CLAVE)
    if (!crudo) return {}
    const datos: unknown = JSON.parse(crudo)
    if (typeof datos !== 'object' || datos === null || Array.isArray(datos)) return {}
    const salida: Cola = {}
    for (const [listaId, cambios] of Object.entries(datos as Record<string, unknown>)) {
      if (!Array.isArray(cambios)) continue
      const buenos = cambios.filter(esCambio)
      if (buenos.length) salida[listaId] = buenos
    }
    return salida
  } catch {
    // Dato corrupto de una version anterior: se empieza de cero en vez de reventar la
    // lista cada vez que se abre. Perder cambios ya guardados es malo; no poder usar la
    // lista en el pasillo es peor.
    return {}
  }
}

function esCambio(x: unknown): x is CambioPendiente {
  if (typeof x !== 'object' || x === null) return false
  const c = x as Record<string, unknown>
  return typeof c['lineaId'] === 'string' && typeof c['momento'] === 'string'
    && typeof c['cambio'] === 'object' && c['cambio'] !== null
}

function escribe(todo: Cola): boolean {
  try {
    window.localStorage.setItem(CLAVE, JSON.stringify(todo))
    return true
  } catch {
    return false
  }
}

/** Los cambios que esperan para esa lista, en el orden en que se tocaron. */
export function leerCola(listaId: string): CambioPendiente[] {
  return leerTodo()[listaId] ?? []
}

/** Apunta un cambio. Si esa linea ya tenia uno sin subir, **se sustituye**.
 *
 *  Devuelve la cola que queda, o `null` si no se ha podido guardar (sin permiso, sin
 *  sitio): quien llama tiene que poder decirlo, porque una cola que no se guarda es
 *  una promesa que se pierde al cerrar la pestaña.
 */
export function apuntaCambio(listaId: string, nuevo: CambioPendiente): CambioPendiente[] | null {
  const todo = leerTodo()
  const otros = (todo[listaId] ?? []).filter((c) => c.lineaId !== nuevo.lineaId)
  // Se junta con lo que ya hubiera para esa linea: tachar y luego cambiar la cantidad
  // sin cobertura son dos cambios de la misma linea, y el segundo no puede borrar al
  // primero -- la cantidad y el tachado son campos distintos del mismo PATCH.
  const antes = (todo[listaId] ?? []).find((c) => c.lineaId === nuevo.lineaId)
  const juntos = { ...nuevo, cambio: { ...(antes?.cambio ?? {}), ...nuevo.cambio } }
  const cola = [...otros, juntos]
  todo[listaId] = cola
  return escribe(todo) ? cola : null
}

/** La cola se vacia **solo cuando el servidor ha dicho que los aplico**. */
export function vaciaCola(listaId: string): void {
  const todo = leerTodo()
  delete todo[listaId]
  escribe(todo)
}

/** Cuantos cambios esperan, para poder decirlo sin abrir la lista entera. */
export function cuantosEsperan(listaId: string): number {
  return leerCola(listaId).length
}
