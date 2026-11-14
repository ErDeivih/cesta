/** *** EL ALMACÉN DE LA DEMO: LOS DATOS EN EL DISPOSITIVO. *** *
 *
 *  *La demo publicada no tiene servidor, así que lo que se escribe se guarda en el navegador con
 *  **IndexedDB** y sobrevive a recargar la página.* *Es la primera pieza de la decisión del 14/11:
 *  los datos de la cesta viven en el dispositivo y la demo lleva una muestra pequeña incrustada.*
 *
 *  Tres reglas:
 *   - **Nunca romper la demo**: si IndexedDB no está (modo privado, navegador viejo) la app sigue
 *     funcionando con el estado en memoria y no se dice nada raro.
 *   - **Una sola clave**: lo que se guarda es el estado entero de la muestra, con su versión. Si la
 *     muestra cambia de versión, se vuelve a sembrar (lo viejo no se mezcla con lo nuevo).
 *   - **`?demo=reset` borra lo guardado** y deja la muestra como recién instalada: es la forma de
 *     recuperar la demo para otra persona sin borrar datos del navegador a mano.
 */
const NOMBRE = 'cesta-demo'
const ALMACEN = 'estado'
const CLAVE = 'datos'

function abre(): Promise<IDBDatabase> {
  return new Promise((ok, ko) => {
    if (typeof indexedDB === 'undefined') {
      ko(new Error('sin IndexedDB'))
      return
    }
    const peticion = indexedDB.open(NOMBRE, 1)
    peticion.onupgradeneeded = () => {
      const bd = peticion.result
      if (!bd.objectStoreNames.contains(ALMACEN)) bd.createObjectStore(ALMACEN)
    }
    peticion.onsuccess = () => ok(peticion.result)
    peticion.onerror = () => ko(peticion.error ?? new Error('no se pudo abrir'))
  })
}

/** Lo guardado, o `null` si no hay nada o el navegador no deja. */
export async function lee(): Promise<unknown> {
  try {
    const bd = await abre()
    return await new Promise((ok) => {
      const tx = bd.transaction(ALMACEN, 'readonly')
      const peticion = tx.objectStore(ALMACEN).get(CLAVE)
      peticion.onsuccess = () => ok(peticion.result ?? null)
      peticion.onerror = () => ok(null)
    })
  } catch {
    return null
  }
}

/** Guarda el estado entero. Si falla, se calla: la demo sigue con lo que tiene en memoria. */
export async function guarda(valor: unknown): Promise<void> {
  try {
    const bd = await abre()
    await new Promise<void>((ok) => {
      const tx = bd.transaction(ALMACEN, 'readwrite')
      tx.objectStore(ALMACEN).put(valor, CLAVE)
      tx.oncomplete = () => ok()
      tx.onerror = () => ok()
    })
  } catch {
    /* sin IndexedDB no se persiste; la demo funciona igual durante la visita */
  }
}

/** Borra lo guardado (para `?demo=reset`). */
export async function borra(): Promise<void> {
  try {
    const bd = await abre()
    await new Promise<void>((ok) => {
      const tx = bd.transaction(ALMACEN, 'readwrite')
      tx.objectStore(ALMACEN).delete(CLAVE)
      tx.oncomplete = () => ok()
      tx.onerror = () => ok()
    })
  } catch {
    /* nada que borrar */
  }
}
