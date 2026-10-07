/** El boton de anadir a la cesta, que es el mismo en la ficha del grupo y en la del producto.
 *
 *  Vivía dentro de `paginas/Grupo.tsx` hasta el 27 de septiembre de 2026, y ese dia se sacó
 *  aqui **porque faltaba donde mas falta hace**: la ficha del producto (`/producto/<cadena>/<id>`)
 *  es a la que se llega **escaneando el codigo de barras**, y desde ella no se podia apuntar
 *  nada. El flujo documentado en `docs/PANTALLAS.md` §6 dice «+ ficha + anadir» para el caso de
 *  «lo conozco y puedo comparar», y la pantalla no tenia el anadir: habia que volver al grupo a
 *  buscarlo, con el paquete en la mano. Dos copias del boton habrian acabado en dos
 *  comportamientos; una sola, no.
 *
 *  Cuatro decisiones que no se leen en el codigo:
 *
 *  - **Sin sesion no se pinta**, igual que el boton de favoritos: un boton que al pulsarlo pide
 *    entrar es una promesa que no se puede cumplir en el pasillo, con una mano y el carro en la
 *    otra.
 *  - Desde una ficha se conserva el producto exacto. Desde un grupo se conserva el grupo.
 *    No sustituir la eleccion concreta antes de disponer de identidades verificadas.
 *  - **No se pregunta si el grupo ya esta en la lista.** Habria que pedir `GET /listas/{id}`, y
 *    esa llamada **marca la visita** (`marca_visita`, main.py:376): los avisos de "lo que ha
 *    puesto la otra persona" se calculan contra esa marca, asi que mirar una ficha los gastaria.
 *    En su lugar, el boton se queda en "En la cesta" despues de anadir, que es lo que evita el
 *    error facil de verdad: pulsarlo tres veces.
 *  - **La cantidad no se pregunta aqui.** Se anade con 1 y se cambia en la cesta, que es donde
 *    se ve la lista entera y lo que va a costar.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { anadirLinea, crearLista, misListas, yo } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { Boton, Etiqueta } from './ui'
import { referenciaLinea } from '../estado/referenciaLinea'

export function BotonAnadirACesta({ grupoId, productoId, nombre }: { grupoId?: number; productoId?: string; nombre: string }) {
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo, staleTime: 60_000 })
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: sesion.data?.usuario != null,
    staleTime: 60_000,
  })

  // La de casa primero, que es la lista de la compra de verdad. Si no hay ninguna de casa vale
  // la primera (la API ya las manda con la de casa delante), y si no hay ninguna se crea: sin
  // lista no hay donde escribir.
  const destino = listas.data?.find((l) => l.es_de_casa) ?? listas.data?.[0] ?? null

  const anade = useMutation({
    mutationFn: async () => {
      const lista = destino ?? (await crearLista('Casa', true))
      await anadirLinea(lista.id, { nombre, ...referenciaLinea(grupoId, productoId) })
      return lista.id
    },
    onSuccess: (listaId) => {
      // Lo que hay en pantalla de esa lista ya no vale: la cesta la enseña con su total y con
      // donde sale mas barata, y las dos cosas cambian al anadir.
      cliente.invalidateQueries({ queryKey: ['listas'] })
      cliente.invalidateQueries({ queryKey: ['lista', listaId] })
      cliente.invalidateQueries({ queryKey: ['donde', listaId] })
    },
  })

  if (!sesion.data?.usuario) return null

  const dentro = anade.isSuccess

  return (
    <div className="flex items-center gap-2">
      <Boton
        variante={dentro ? 'sutil' : 'principal'}
        disabled={anade.isPending || dentro || listas.isPending}
        title={dentro ? 'Ya está en la lista: la cantidad se cambia en la cesta.' : undefined}
        onClick={() => anade.mutate()}
      >
        {anade.isPending ? 'Añadiendo…' : dentro ? 'En la cesta' : 'Añadir a la cesta'}
      </Boton>
      {anade.isError && <Etiqueta tono="aviso">{textoDeError(anade.error)}</Etiqueta>}
      {listas.isError && <Etiqueta tono="aviso">No sé en qué lista apuntarlo.</Etiqueta>}
    </div>
  )
}
