/**
 * La operación que se está intentando, y por qué tiene que sobrevivir al reintento.
 *
 * ## El problema, medido el 13 de octubre de 2026
 *
 * `Diario.tsx` generaba `crypto.randomUUID()` **dentro del `onSubmit`**, así que pulsar «Anotar» otra
 * vez después de una respuesta perdida **era una operación nueva**: el servidor creaba una segunda
 * entrada. *La clave existía, el índice único existía y el servidor deduplicaba — pero el cliente
 * **nunca reenviaba la misma clave**, así que no servía de nada.*
 *
 * **Y no hay reintento automático**: las mutaciones de `api/diario.ts` no declaran `retry`. La premisa
 * que el comentario del componente daba por buena —*«un reintento de la misma operación la repite»*—
 * **no ocurría en ningún caso.** *Lo único que impedía un doble clic era `disabled={isPending}`, que es
 * otra cosa: eso tapa el clic mientras está en vuelo, no el reintento de después.*
 *
 * ## Lo que hace falta
 *
 * Recordar la operación **y su payload** mientras no haya un resultado inequívoco.
 * *Si vuelve a enviarse **lo mismo**, es un reintento y lleva la misma clave; si cambia algo, es otra
 * operación y lleva clave nueva.* **Y tras un alta buena se olvida**, para que dos meriendas iguales de
 * verdad sigan siendo dos — que es lo que el servidor ya prueba por su lado.
 *
 * ## Y el generador de la clave, que tenía su propio fallo
 *
 * `crypto.randomUUID` **solo existe en contexto seguro** (https o localhost), y esta aplicación se
 * sirve por http en el 8080, también por la IP de Tailscale: **ahí no está definido**. `api/cesta.ts`
 * ya lo sabía y tiene un respaldo con `getRandomValues`; **el diario llamaba al método a pelo**, así
 * que por esa IP «Anotar» reventaba. *El generador vive aquí, en un solo sitio, y los dos lo usan.*
 */

/** Lo que se está intentando: la clave, el payload **sin la clave**, y cuántas veces se ha enviado. */
export interface Pendiente<T> {
  clave: string
  datos: T
  /** *Cuántas veces se ha enviado esta misma operación.* Sirve para poder decirlo en pantalla. */
  intentos: number
}

/**
 * **Un uuid v4, también donde `crypto.randomUUID` no existe.**
 *
 * *El respaldo usa `getRandomValues`, que sí está en http, y saca los mismos 16 bytes con la versión
 * y la variante de un uuid v4.*
 */
export function claveNueva(): string {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const b = crypto.getRandomValues(new Uint8Array(16))
  b[6] = (b[6] & 0x0f) | 0x40
  b[8] = (b[8] & 0x3f) | 0x80
  const hex = [...b].map((x) => x.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

/** Ordena las claves para que dos objetos iguales den el mismo texto. */
function ordenado(valor: unknown): unknown {
  if (Array.isArray(valor)) return valor.map(ordenado)
  if (valor !== null && typeof valor === 'object') {
    const salida: Record<string, unknown> = {}
    for (const k of Object.keys(valor as Record<string, unknown>).sort()) {
      salida[k] = ordenado((valor as Record<string, unknown>)[k])
    }
    return salida
  }
  return valor
}

/**
 * **El sello del payload.** Dos envíos con el mismo sello son **la misma operación**.
 *
 * *Se ordenan las claves para que el orden en que se escriban los campos no cambie la respuesta:
 * un `JSON.stringify` a secas haría que el mismo formulario pareciera distinto según cómo se
 * construyera el objeto.*
 */
export function sello(datos: unknown): string {
  return JSON.stringify(ordenado(datos))
}

/** **¿Esto es reintentar lo mismo?** *Lo que la pantalla necesita para decirlo.* */
export function esReintento<T>(pendiente: Pendiente<T> | null, datos: T): boolean {
  return pendiente !== null && sello(pendiente.datos) === sello(datos)
}

/**
 * **La operación que corresponde a este envío.**
 *
 * - Si es **lo mismo** que estaba pendiente: **la misma clave**, y un intento más.
 * - Si es **distinto**: operación nueva, con clave nueva. *Cambiar el formulario es cancelar lo
 *   anterior, y no hace falta un botón para eso.*
 *
 * `nuevaClave` se inyecta para poder probar esto sin depender del azar.
 */
export function resolver<T>(
  pendiente: Pendiente<T> | null,
  datos: T,
  nuevaClave: () => string = claveNueva,
): Pendiente<T> {
  if (pendiente !== null && sello(pendiente.datos) === sello(datos)) {
    return { clave: pendiente.clave, datos, intentos: pendiente.intentos + 1 }
  }
  return { clave: nuevaClave(), datos, intentos: 1 }
}
