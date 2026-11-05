/** La puerta de sesión: **«Entra para ver esto», con la salida puesta.**
 *
 *  Seis pantallas pedían datos que exigen sesión **sin preguntar antes si había alguien**:
 *  Despensa, Recetario, RecetaDetalle, PlanSemanal, Diario y Tendencias. Lo que salía era el
 *  error de la petición —«La API ha contestado 401»—, que es el primer texto que leía quien
 *  abría la app recién instalada.
 *
 *  Las cuatro pantallas que ya lo hacían bien (Favoritos, Avisos, Cesta y Ajustes) tenían cada
 *  una su copia del mismo cartel. Esto es esa pieza, una sola vez, para que la séptima pantalla
 *  no nazca sin puerta: es el mismo motivo por el que `Fallo` y `Vacio` viven en `ui.tsx`.
 *
 *  **Y no es un error**: no se pinta en rojo ni con `role="alert"`, porque no ha fallado nada.
 *  Es un estado más de la pantalla, con su `h1` (`comoPagina`) y su enlace de entrada.
 */
import { Link } from 'react-router-dom'

import { Vacio } from './ui'

export function EntraParaVer({ texto }: {
  /** Qué se guarda con la cuenta, en una frase. Se lee debajo del título. */
  texto: string
}) {
  return (
    <Vacio titulo="Entra para ver esto" comoPagina className="grow">
      <p>
        {texto} Se entra desde <Link to="/cesta" className="underline">la cesta</Link>.
      </p>
    </Vacio>
  )
}
