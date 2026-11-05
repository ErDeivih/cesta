/** El boton de guardar en favoritos, para la ficha del grupo.
 *
 *  Vive aparte porque tiene tres estados que hay que contar bien:
 *
 *  - **Sin sesion**: no se pinta. Un boton que al pulsarlo pide entrar es una
 *    promesa que no se puede cumplir en el pasillo, con una mano.
 *  - **No esta**: "Guardar". Al pulsar, se guarda y el boton cambia.
 *  - **Ya esta**: "Guardado", y al pulsar se quita.
 *
 *  El estado se sabe pidiendo la lista de favoritos, que ya se cachea con
 *  TanStack Query: no hay una llamada nueva por cada ficha que se abre.
 */
import { useQuery } from '@tanstack/react-query'

import { textoDeError } from '../api/cliente'
import { yo } from '../api/cesta'
import { useFavorito, verFavoritos } from '../api/favoritos'
import { IconoCorazon, IconoCorazonLleno } from './iconos'
import { Boton, Etiqueta } from './ui'

export function BotonFavorito({ grupoId }: { grupoId: number }) {
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const favs = useQuery({
    queryKey: ['favoritos'],
    queryFn: () => verFavoritos(),
    enabled: sesion.data?.usuario != null,
    staleTime: 60_000,
  })
  const cambio = useFavorito()

  if (!sesion.data?.usuario) return null

  const dentro = (favs.data?.favoritos ?? []).some((f) => f.grupo_id === grupoId)

  return (
    <div className="flex items-center gap-2">
      <Boton
        variante={dentro ? 'sutil' : 'normal'}
        aria-pressed={dentro}
        disabled={cambio.isPending}
        onClick={() => cambio.mutate({ grupoId, productoId: null, dentro })}
      >
        {/* *El corazon dice **en que estado esta** sin depender solo del texto: lleno cuando esta
            dentro, de trazo cuando no.* *Va `aria-hidden` (lo pone `Base`), porque el nombre del
            boton es su texto y un icono suelto no se anuncia.* */}
        {dentro ? (
          <IconoCorazonLleno width={18} height={18} className="text-terracota" />
        ) : (
          <IconoCorazon width={18} height={18} />
        )}
        {dentro ? 'Guardado' : 'Guardar'}
      </Boton>
      {cambio.isError && (
        <Etiqueta tono="aviso">{textoDeError(cambio.error)}</Etiqueta>
      )}
    </div>
  )
}
