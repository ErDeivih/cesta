/** La campana: "avisame si baja", desde la ficha del producto.
 *
 *  Es la otra mitad del punto 6, y la que hace que la pantalla de avisos sirva de algo:
 *  sin una forma de pedir el aviso, `/avisos` esta vacia para siempre.
 *
 *  Tres decisiones, y las tres son para que esto **no parezca un formulario**:
 *
 *  1. **El tipo por defecto es `minimo_90d`**, el unico que no exige saber cuanto
 *     deberia costar algo. El encargo lo dice: *"`baja_de` exige poner un numero, y la
 *     mayoria de la gente no sabe cual poner hasta que ve la curva"*. Asi que el boton
 *     no pregunta nada: pide el aviso util y ya. Poner un umbral a mano es una segunda
 *     intencion, y no cabe en el primer toque.
 *  2. **Un toque y el boton cambia de estado**, como el de anadir a la cesta: si ya
 *     estas siguiendo ese producto, dice que si, y volver a pulsarlo no crea nada (la
 *     API tiene una alerta por persona, grupo y tipo).
 *  3. **Sin sesion no hay campana.** Una alerta es de una persona y no se puede guardar
 *     sin saber de quien: el boton no se pinta, en vez de pintarse y fallar.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { borrarAlerta, crearAlerta, misAlertas } from '../api/alertas'
import { yo } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { Boton, Etiqueta } from './ui'

export function Campana({ grupoId }: { grupoId: number }) {
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const alertas = useQuery({
    queryKey: ['alertas'],
    queryFn: misAlertas,
    enabled: sesion.data?.usuario != null,
    staleTime: 60_000,
  })

  const mia = alertas.data?.alertas.find((a) => a.grupo_id === grupoId)

  const pone = useMutation({
    mutationFn: () => crearAlerta(grupoId),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['alertas'] }),
  })
  const quita = useMutation({
    mutationFn: (alertaId: string) => borrarAlerta(alertaId),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['alertas'] }),
  })

  if (!sesion.data?.usuario) return null

  const dentro = Boolean(mia)
  const pendiente = pone.isPending || quita.isPending
  const fallo = pone.isError || quita.isError

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Boton
        variante={dentro ? 'sutil' : 'normal'}
        disabled={pendiente || alertas.isPending}
        title={dentro ? 'Te aviso cuando este en su precio mas bajo de 90 dias.' : undefined}
        onClick={() => (dentro && mia ? quita.mutate(mia.id) : pone.mutate())}
      >
        {pendiente ? 'Un momento…' : dentro ? 'Te aviso' : 'Avisarme si baja'}
      </Boton>
      {/* Cuando ya esta, se dice **que** se ha prometido: "te aviso" a secas no dice de
          que, y esto es una promesa que la aplicacion tiene que cumplir sola. */}
      {dentro && !pendiente && (
        <span className="text-sm text-tinta-suave">
          cuando esté en su precio más bajo de 90 días
        </span>
      )}
      {fallo && (
        <Etiqueta tono="aviso">
          {textoDeError(pone.error ?? quita.error)}
        </Etiqueta>
      )}
    </div>
  )
}
