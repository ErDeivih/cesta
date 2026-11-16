/** El botón de añadir que va en cada resultado del buscador.
 *
 *  *** EL BUSCADOR NO ES SOLO PARA MIRAR. *** *David lo pidió así: buscar «leche» y tener
 *  que abrir la ficha para apuntarla es un viaje de más, y el desplegable de la lista era
 *  el único sitio donde se podía añadir sin salir. Este botón lleva el mismo camino —la
 *  lista de casa, la que se crea sola— a la fila del resultado.*
 *
 *  Sin sesión no se pinta: un botón que al pulsarlo pide entrar es una promesa que no se
 *  puede cumplir en el pasillo, con una mano. Es la misma regla que `BotonAnadirACesta`.
 */
import { useQuery } from '@tanstack/react-query'

import { yo } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { useAnadeALaCesta } from '../api/consultas'
import type { ResultadoBusqueda } from '../tipos'
import { Boton, Etiqueta } from './ui'

export function AnadirDesdeElBuscador({ fila }: { fila: ResultadoBusqueda }) {
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const anade = useAnadeALaCesta()

  // *Una fila sin grupo no se puede enlazar: el botón no puede prometer un producto que
  // no tiene identidad en el catálogo.*
  if (fila.grupo_id === null || !sesion.data?.usuario) return null

  const dentro = anade.isSuccess

  return (
    <span className="inline-flex flex-wrap items-center gap-2">
      <Boton
        variante={dentro ? 'sutil' : 'normal'}
        compacto
        className="relative z-10"
        disabled={anade.isPending || dentro}
        title={dentro ? 'Ya está en la lista: la cantidad se cambia en la cesta.' : undefined}
        onClick={() =>
          anade.mutate({ grupoId: fila.grupo_id as number, nombre: fila.nombre })
        }
      >
        {anade.isPending ? 'Añadiendo…' : dentro ? 'En la cesta' : 'Añadir'}
      </Boton>
      {anade.isError && <Etiqueta tono="aviso">{textoDeError(anade.error)}</Etiqueta>}
    </span>
  )
}
