/** Los favoritos: lo que se compra siempre, con el estado de hoy.
 *
 *  Lo que hace util esta pantalla no es la lista, es **el orden**: la API los
 *  manda por lo que ha cambiado, no por alfabeto. Lo que ha bajado arriba, lo
 *  quieto al final. Una lista de la compra ordenada de la A a la Z hay que leerla
 *  entera para encontrar lo unico que importa.
 *
 *  Necesita sesion, como la cesta: los favoritos son de cada uno.
 *
 *  **Falta poner favoritos desde aqui**: se pueden ver y quitar, pero para anadir
 *  hay que usar la interfaz antigua o el movil. Esta apuntado en el BACKLOG.
 *
 *  Tampoco esta en la barra de abajo: en el movil hay cuatro sitios y este no es
 *  uno de los que se visitan en el pasillo. Se llega desde aqui o escribiendo la
 *  direccion.
 */
import { Link } from 'react-router-dom'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { verFavoritos, quitarFavorito } from '../api/favoritos'
import { textoDeError } from '../api/cliente'
import { yo } from '../api/cesta'
import { euros } from '../api/formato'
import { Boton, Cargando, Etiqueta, Tarjeta, Vacio } from '../componentes/ui'

export function Favoritos() {
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })
  const favs = useQuery({
    queryKey: ['favoritos'],
    queryFn: verFavoritos,
    enabled: sesion.data?.usuario != null,
  })
  const quitar = useMutation({
    mutationFn: (f: { grupo_id: number | null; producto_id?: string | null }) =>
      quitarFavorito(f.grupo_id, f.producto_id ?? null),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['favoritos'] }),
  })

  if (sesion.isLoading || favs.isLoading) return <Cargando que="tus favoritos" />

  if (!sesion.data?.usuario) {
    return (
      <Vacio titulo="Entra para ver tus favoritos">
        <p>
          Los favoritos son tuyos, así que hacen falta tus listas. Se entra desde{' '}
          <Link to="/cesta" className="underline">la cesta</Link>.
        </p>
      </Vacio>
    )
  }

  if (favs.isError) {
    return (
      <Vacio titulo="No he podido traerlos">
        <p>{textoDeError(favs.error)}</p>
      </Vacio>
    )
  }

  const lista = favs.data ?? []
  if (!lista.length) {
    return (
      <Vacio titulo="Todavía no tienes favoritos">
        <p>
          Los favoritos son los productos que compras siempre. Aparecen aquí con
          el precio de hoy y marcados cuando han bajado.
        </p>
      </Vacio>
    )
  }

  return (
    <div className="grid gap-4">
      <header>
        <h1 className="text-xl font-semibold">Favoritos</h1>
        <p className="text-sm text-tinta-suave">
          Con el estado de hoy. Primero lo que ha cambiado.
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {lista.map((f, n) => {
          const clave = f.producto_id ?? `g${f.grupo_id ?? n}`
          const cadena = f.cadena ?? f.fuente ?? null
          return (
            <Tarjeta key={clave}>
              <div className="flex items-start gap-2">
                <div className="min-w-0 flex-1">
                  {f.grupo_id != null ? (
                    <Link to={`/grupo/${f.grupo_id}`} className="font-medium underline">
                      {f.nombre}
                    </Link>
                  ) : (
                    <span className="font-medium">{f.nombre}</span>
                  )}
                  {f.marca && (
                    <p className="text-sm text-tinta-suave">{f.marca}</p>
                  )}
                </div>
                {f.ahorro_pct != null && f.ahorro_pct > 0 && (
                  <Etiqueta tono="bien">−{f.ahorro_pct.toFixed(0)} %</Etiqueta>
                )}
              </div>

              <p className="cifra mt-2 text-lg font-semibold">
                {f.precio_unidad_cent != null
                  ? `${euros(f.precio_unidad_cent)}/${f.unidad ?? ''}`
                  : 'no lo sé'}
              </p>
              {cadena && <p className="text-sm text-tinta-suave">en {cadena}</p>}

              <Boton
                variante="sutil"
                className="mt-3"
                disabled={quitar.isPending}
                onClick={() => quitar.mutate({
                  grupo_id: f.grupo_id, producto_id: f.producto_id ?? null,
                })}
              >
                Quitar
              </Boton>
            </Tarjeta>
          )
        })}
      </div>
    </div>
  )
}
