/** *** EL CUADERNO DE «MIS ALIMENTOS», GUARDADO EN EL APARATO. *** *
 *
 *  **El fallo que arregla (P0-3):** *`/calorias/alimentos` era el único sitio de la app que perdía
 *  lo que la persona escribía.* *La receta y los apuntes vivían en `useState`, y al recargar o
 *  cerrar la pestaña se quedaban vacíos sin avisar de nada.*
 *
 *  **Por qué aquí y no en la API:** *el diario real (`/api/diario`) es otra cosa —lo que se ha
 *  comido, con su fecha y su comida— y **no hay ninguna ruta para este cuaderno**: guardar una
 *  receta propia con sus valores de etiqueta exige una API nueva, y eso no se inventa desde el
 *  front.* *Mientras no exista, lo escrito **no se pierde al recargar**: se guarda en este
 *  aparato, que es lo que la pantalla promete.*
 *
 *  **Dependencia pendiente, dicha aquí para que no se olvide:** *sincronizar el cuaderno con la
 *  cuenta necesita una ruta de la API (algo como `GET/PUT /api/cocina`).* *El día que exista, esta
 *  pieza se sustituye por esa consulta y la pantalla no cambia de forma.*
 *
 *  **Y lo que guarda lo valida al leer**: *un cuaderno de otra versión, o roto, no puede tumbar la
 *  pantalla; se ignora y se empieza vacío.*
 */
import type { Receta } from './cocina'

/** Un apunte de comida del cuaderno. *No es una entrada del diario: no viaja a la API.* */
export type Apunte = {
  id: string
  fecha: string
  nombre: string
  raciones: number
  /** `null` es «no se sabe», y **no es un cero**. */
  kcal: number | null
  incompleto: boolean
}

export interface Cuaderno {
  receta: Receta | null
  diario: Apunte[]
}

/** *La clave del aparato. Lleva `cesta.` delante como las demás (`cesta.ultimo`).* */
const CLAVE = 'cesta.cocina'

export const CUADERNO_VACIO: Cuaderno = { receta: null, diario: [] }

function esObjeto(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null
}

/** *Lo mínimo que tiene que cumplir una receta guardada para poder pintarse.* */
function esReceta(v: unknown): v is Receta {
  return esObjeto(v)
    && typeof v.nombre === 'string'
    && typeof v.raciones === 'number'
    && Array.isArray(v.ingredientes)
}

function esApunte(v: unknown): v is Apunte {
  return esObjeto(v)
    && typeof v.id === 'string'
    && typeof v.fecha === 'string'
    && typeof v.nombre === 'string'
}

/** Lo guardado, o el cuaderno vacío. *Nunca lanza: la pantalla tiene que abrirse igual.* */
export function leeCuaderno(): Cuaderno {
  if (typeof localStorage === 'undefined') return { receta: null, diario: [] }
  try {
    const crudo = localStorage.getItem(CLAVE)
    if (!crudo) return { receta: null, diario: [] }
    const dato: unknown = JSON.parse(crudo)
    if (!esObjeto(dato)) return { receta: null, diario: [] }
    return {
      receta: esReceta(dato['receta']) ? dato['receta'] : null,
      diario: Array.isArray(dato['diario']) ? dato['diario'].filter(esApunte) : [],
    }
  } catch {
    // *JSON roto, o un navegador que no deja leer: se empieza de cero, sin ruido.*
    return { receta: null, diario: [] }
  }
}

/** Guarda el cuaderno. *Si el navegador no deja escribir (modo privado), no revienta: la pestaña
 *  sigue funcionando y lo escrito se pierde al cerrar, que es lo único que se puede hacer.* */
export function guardaCuaderno(c: Cuaderno): void {
  if (typeof localStorage === 'undefined') return
  try {
    localStorage.setItem(CLAVE, JSON.stringify(c))
  } catch {
    // Sin almacenamiento no hay nada que hacer; no es un fallo que la pantalla deba contar.
  }
}
