/** Quien ha entrado, y la cache atada a ello.
 *
 *  **Por que vaciar la cache entera y no solo filtrar por usuario.** Hay 95 claves de consulta en la
 *  aplicacion. Poner el usuario en las 95 a mano no es viable, y basta olvidar una para que al cambiar
 *  de cuenta aparezca durante un instante el diario, el recetario o la lista de la compra de la otra
 *  persona. Vaciar no se puede olvidar.
 *
 *  **Y por que ademas se pone el usuario en las claves nuevas.** Porque son mias y son cuatro, y asi dos
 *  cuentas no comparten entrada de cache ni aunque el vaciado fallara. Defensa en profundidad: la
 *  primera capa es la que protege, la segunda es la que aguanta si la primera se rompe.
 */
import { useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { yo } from './cesta'

/** Una clave que identifica a la cuenta **sin depender de la forma** de la respuesta.
 *
 *  Se usa el JSON entero de la sesion: si el objeto cambia de campos, dos cuentas siguen dando claves
 *  distintas. Acertar el nombre del campo seria una forma silenciosa de que las dos compartieran clave.
 */
export function useClaveDeCuenta(): string {
  const { data } = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  return data === undefined ? 'sin-sesion' : JSON.stringify(data)
}

/** Vaciar la cache cuando la cuenta cambia. Se monta una vez, arriba del todo.
 *
 *  Cubre los tres cambios: entrar, salir y cambiar de una cuenta a otra. El primer render no vacia nada
 *  -- no hay nada que vaciar todavia --, y a partir de ahi cualquier cambio de identidad tira todo.
 */
export function VigilaCuenta() {
  const cliente = useQueryClient()
  const clave = useClaveDeCuenta()
  const anterior = useRef<string | null>(null)

  useEffect(() => {
    if (anterior.current !== null && anterior.current !== clave) {
      // **Todo fuera.** Consultas y mutaciones: una mutacion en vuelo tambien es de la cuenta anterior.
      cliente.clear()
    }
    anterior.current = clave
  }, [clave, cliente])

  return null
}
