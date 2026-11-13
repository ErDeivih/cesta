/** El aviso de «sin conexión», igual en las tres pantallas.
 *
 *  Existe porque el dato de la red **lo lee un solo sitio** (`estado/conexion.ts`) y lo pinta
 *  un solo componente: si cada pantalla escribiera su frase, el dia que una diga «se guarda»
 *  y otra «no se ha guardado» la app estara mintiendo en una de las dos.
 *
 *  **No bloquea nada.** Sin red se sigue tachando y apuntando: la cola de cambios
 *  (`estado/cola.ts`) guarda con la hora del movil y sube al volver `online`. Un aviso que
 *  tapara la pantalla convertiria una molestia (no hay cobertura en el pasillo) en un
 *  bloqueo.
 */
import { useSinConexion } from '../estado/conexion'
import { Aviso } from './ui'

export function SinConexion({
  que = 'Lo que apuntes se guarda en el móvil y sube solo al volver la red.',
}: {
  /** Lo que pasa en esta pantalla sin red. Por defecto, la regla general de la app. */
  que?: string
}) {
  const sin = useSinConexion()
  if (!sin) return null
  return (
    <Aviso tono="aviso" titulo="Sin conexión">
      <p>{que}</p>
    </Aviso>
  )
}
