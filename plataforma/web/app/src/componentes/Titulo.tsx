/** El titulo de la pestana, que es lo que se ve cuando hay diez abiertas.
 *
 *  Lo pide el encargo (§8): *"el titulo de cada pantalla en la pestana, para quien la
 *  tenga abierta entre otras diez"*. Y es literal: con el buscador, la cesta, el panel y
 *  tres fichas abiertas, todas con el mismo titulo, no hay forma de saber cual es cual.
 *
 *  **Dos niveles, y el de dentro gana.** `App` pone el titulo por ruta ("La cesta",
 *  "Panel"), y una pantalla que sabe **de que** esta hablando lo mejora con el dato: la
 *  ficha pone el nombre del producto. Ese segundo nivel funciona por orden natural de
 *  los efectos -- el dato llega en un render posterior al de la ruta, asi que su efecto
 *  corre despues -- sin necesidad de coordinacion entre las dos partes.
 *
 *  El sufijo `· Avío` va siempre: una pestana que solo dice "Leche entera" no dice de
 *  que aplicacion es, y con diez abiertas eso importa.
 */
import { useEffect } from 'react'

import { MARCA } from '../marca'

export const SUFIJO = `· ${MARCA}`

/** Pone el titulo de la pestana. Sin texto, deja solo el nombre de la aplicacion. */
export function useTitulo(texto?: string | null) {
  useEffect(() => {
    const limpio = (texto ?? '').trim()
    document.title = limpio ? `${limpio} ${SUFIJO}` : MARCA
  }, [texto])
}
