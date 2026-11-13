/** El estado «sin conexión», que es un estado y no un error.
 *
 *  La app se usa en el supermercado, que es donde peor va la red. Hoy cada pantalla resuelve
 *  el modo sin red por su cuenta -- `Cesta.tsx` encola los cambios y no los sube hasta que
 *  vuelve `online`, `PegarEnLaLista` guarda en el aparato -- y **ninguna de las tres pantallas
 *  lo dice en pantalla**: quien tacha en el pasillo sin cobertura no sabe si se ha guardado
 *  o no. Este modulo es la unica pieza que lee `navigator.onLine`, para que la respuesta sea
 *  la misma en las tres.
 *
 *  **No se cachean datos aqui.** Que la pantalla enseñe lo ultimo que se trajo es cosa de
 *  React Query (`staleTime`), que ya guarda la ultima respuesta buena; esto solo dice la
 *  verdad sobre la red. Mezclarlo con los datos daria un «sin conexión» que miente cuando la
 *  red va fina pero el servidor no contesta, y al reves.
 */
import { useEffect, useState } from 'react'

/** Si el aparato esta ahora mismo sin red, y se entera cuando cambia.
 *
 *  `navigator.onLine === false` es la unica señal que da el navegador y **solo es fiable en un
 *  sentido**: `false` es «no hay red» de verdad; `true` no garantiza que la peticion llegue
 *  (wifi de tienda con portal cautivo). Por eso el aviso dice «sin conexión» y no «no se ha
 *  guardado»: lo segundo lo sabe la cola de cambios, no esto.
 */
export function useSinConexion(): boolean {
  const [sin, setSin] = useState(
    () => typeof navigator !== 'undefined' && navigator.onLine === false,
  )

  useEffect(() => {
    const alCambiar = () => setSin(navigator.onLine === false)
    window.addEventListener('online', alCambiar)
    window.addEventListener('offline', alCambiar)
    // Al montar se vuelve a mirar: entre el primer render y el efecto, la red puede haber
    // cambiado, y `useState` se quedo con la foto de antes.
    alCambiar()
    return () => {
      window.removeEventListener('online', alCambiar)
      window.removeEventListener('offline', alCambiar)
    }
  }, [])

  return sin
}
