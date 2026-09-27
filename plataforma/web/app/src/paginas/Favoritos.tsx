/** Los favoritos: lo que se compra siempre, con el estado de hoy.
 *
 *  Lo que hace util esta pantalla no es la lista, es **el orden**: la API los
 *  manda por lo que ha cambiado, no por alfabeto. Lo que ha bajado arriba, lo
 *  quieto al final. Una lista de la compra ordenada de la A a la Z hay que leerla
 *  entera para encontrar lo unico que importa.
 *
 *  Necesita sesion, como la cesta: los favoritos son de cada uno.
 *
 *  **Y desde el 25 de septiembre de 2026 esta pantalla sirve para algo mas que
 *  mirar**: el dueno pidio *"que sea facil anadir a una lista productos que ya estan
 *  en favoritos, esa seria la ventaja de tener favoritos configurado"*. Asi que cada
 *  tarjeta lleva un boton para pasarla a una lista, y arriba hay uno para pasar
 *  **todas** de golpe: montar la compra de la semana desde los favoritos es
 *  exactamente lo que se quiere poder hacer en dos toques.
 *
 *  Antes de eso, para anadir habia que usar la interfaz antigua o el movil; la
 *  pantalla solo sabia ver y quitar.
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { verFavoritos, quitarFavorito } from '../api/favoritos'
import { anadirDesdeFavoritos, misListas } from '../api/cesta'
import { textoDeError } from '../api/cliente'
import { yo } from '../api/cesta'
import { eurosUnidad, nombreCadena, porcentaje } from '../api/formato'
import { Aviso, Boton, Cargando, Etiqueta, Fallo, Tarjeta, Vacio } from '../componentes/ui'
import type { Favorito } from '../tipos'

/** El desplegable de listas, con la ultima usada ya elegida.
 *
 *  Se guarda en el movil cual fue la ultima: quien pasa veinte favoritos a la lista
 *  de la semana no quiere elegir la misma lista veinte veces. */
function ElegirLista({ listas, valor, alCambiar, etiqueta }: {
  listas: { id: string; nombre: string }[]
  valor: string
  alCambiar: (id: string) => void
  etiqueta: string
}) {
  if (!listas.length) {
    return (
      <Link to="/cesta" className="text-sm underline">
        Crea una lista para poder añadir
      </Link>
    )
  }
  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="text-tinta-suave">{etiqueta}</span>
      <select
        value={valor}
        onChange={(e) => alCambiar(e.target.value)}
        className="min-h-[44px] rounded-lg border border-neutral-300 bg-white px-2 dark:border-neutral-600 dark:bg-neutral-800"
      >
        {listas.map((l) => (
          <option key={l.id} value={l.id}>{l.nombre}</option>
        ))}
      </select>
    </label>
  )
}

export function Favoritos() {
  const cliente = useQueryClient()
  const sesion = useQuery({ queryKey: ['yo'], queryFn: yo })
  const listas = useQuery({
    queryKey: ['listas'],
    queryFn: misListas,
    enabled: sesion.data?.usuario != null,
  })
  const favoritos = useQuery({
    queryKey: ['favoritos'],
    queryFn: verFavoritos,
    enabled: sesion.data?.usuario != null,
  })
  // La lista a la que se pasan. Empieza por la primera que haya y se queda con lo
  // que elija la persona, sin volver a preguntarlo en cada tarjeta.
  const [destino, setDestino] = useState<string>('')
  const [dicho, setDicho] = useState<string | null>(null)
  const elegida = destino || listas.data?.[0]?.id || ''

  const quitar = useMutation({
    mutationFn: (f: { grupo_id: number | null; producto_id?: string | null }) =>
      quitarFavorito(f.grupo_id, f.producto_id ?? null),
    onSuccess: () => cliente.invalidateQueries({ queryKey: ['favoritos'] }),
  })

  const pasar = useMutation({
    mutationFn: (f: { grupo_id?: number | null; producto_id?: string | null
                      todos?: Favorito[] }) => {
      const grupo_ids: number[] = []
      const producto_ids: string[] = []
      if (f.todos) {
        for (const x of f.todos) {
          if (x.grupo_id != null) grupo_ids.push(x.grupo_id)
          else if (x.producto_id) producto_ids.push(x.producto_id)
        }
      } else {
        if (f.grupo_id != null) grupo_ids.push(f.grupo_id)
        else if (f.producto_id) producto_ids.push(f.producto_id)
      }
      return anadirDesdeFavoritos(elegida, { grupo_ids, producto_ids })
    },
    onSuccess: (cuantos) => {
      cliente.invalidateQueries({ queryKey: ['listas'] })
      cliente.invalidateQueries({ queryKey: ['lista', elegida] })
      cliente.invalidateQueries({ queryKey: ['reparto', elegida] })
      setDicho(cuantos === 1 ? 'Añadido a la lista' : `Añadidos ${cuantos} a la lista`)
      setTimeout(() => setDicho(null), 4000)
    },
  })

  if (sesion.isLoading || favoritos.isLoading) return <Cargando que="tus favoritos" />

  if (!sesion.data?.usuario) {
    return (
      <div className="grid gap-4">
        {/* El `h1` de la pagina, sin sesion: `Vacio` pinta su titulo como parrafo (es un
            estado vacio, no un titular), asi que la pantalla se quedaba sin encabezado de
            nivel 1. Medido con `data/debug/accesibilidad.py --sin-sesion`. */}
        <h1 className="sr-only">Favoritos</h1>
        <Vacio titulo="Entra para ver tus favoritos">
          <p>
            Los favoritos son tuyos, así que hacen falta tus listas. Se entra desde{' '}
            <Link to="/cesta" className="underline">la lista</Link>.
          </p>
        </Vacio>
      </div>
    )
  }

  if (favoritos.isError) {
    // **`Fallo` y no un `Vacio` escrito aquí**, que es el mismo fallo que tenía la cesta y que
    // se arregló allí el 23 de septiembre de 2026: un cartel que dice «No he podido traerlos» y
    // **no deja volver a intentarlo** obliga a recargar la página a mano, que en el móvil no es
    // evidente. Además `Fallo` es quien decide el tono: sin cobertura no es rojo. Medido con la
    // puerta el 27 de septiembre de 2026, al ampliar la prueba de errores de cuatro pantallas a
    // doce: era la única sin botón.
    return <Fallo error={favoritos.error} reintentar={() => void favoritos.refetch()} />
  }

  const lista = favoritos.data ?? []
  const nombreDeDestino = listas.data?.find((l) => l.id === elegida)?.nombre

  if (!lista.length) {
    return (
      /* **El caso vacío da por dónde empezar, y esto es lo mismo que se arregló en los avisos.**
         Antes decía dónde se añaden («desde la ficha de un producto, con el corazón») y no daba
         forma de llegar: en la pantalla que está a un toque de la barra de abajo, un callejón
         sin salida. Medido en una captura de un móvil el 27 de septiembre de 2026. */
      <Tarjeta>
        {/* `h1` y no `p`: en el caso vacio esta tarjeta **es** la pantalla, y sin encabezado la
            pagina se quedaba sin titulo (lo midio `data/debug/accesibilidad.py`). El estilo es
            el mismo: lo que cambia es lo que oye quien navega por encabezados. */}
        <h1 className="text-base font-semibold">Todavía no tienes favoritos</h1>
        <p className="mt-2 text-sm text-tinta-suave">
          Los favoritos son los productos que compras siempre. Aparecen aquí con el precio de
          hoy y marcados cuando han bajado, y se añaden desde la ficha de un producto, con el
          corazón.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link
            to="/buscar"
            className="inline-flex min-h-[44px] items-center rounded-lg bg-sky-700 px-3 text-sm font-semibold text-white dark:bg-sky-500 dark:text-neutral-900"
          >
            Buscar un producto
          </Link>
          <Link
            to="/cesta"
            className="inline-flex min-h-[44px] items-center rounded-lg border border-neutral-300 px-3 text-sm dark:border-neutral-600"
          >
            Ver mi lista
          </Link>
        </div>
      </Tarjeta>
    )
  }

  return (
    <div className="grid gap-4">
      <header className="grid gap-2">
        <h1 className="text-xl font-semibold">Favoritos</h1>
        <p className="text-sm text-tinta-suave">
          Con el estado de hoy. Primero lo que ha cambiado.
        </p>
        {/* Lo que hace util tener favoritos: pasarlos a la lista de la compra. */}
        <div className="flex flex-wrap items-center gap-3">
          <ElegirLista listas={listas.data ?? []} valor={elegida}
                       alCambiar={setDestino} etiqueta="Añadir a" />
          <Boton
            variante="principal"
            disabled={!elegida || pasar.isPending}
            onClick={() => pasar.mutate({ todos: lista })}
          >
            {pasar.isPending ? 'Añadiendo…' : `Añadir los ${lista.length} a la lista`}
          </Boton>
          {nombreDeDestino && (
            <Link to="/cesta" className="text-sm underline">
              Ver «{nombreDeDestino}»
            </Link>
          )}
        </div>
        {dicho && <Aviso tono="bien" titulo={dicho}>Se puede cambiar de tienda dentro de la lista.</Aviso>}
        {pasar.isError && (
          <Aviso tono="mal" titulo="No he podido añadirlos">
            {textoDeError(pasar.error)}
          </Aviso>
        )}
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
                  <Etiqueta tono="bien">−{porcentaje(f.ahorro_pct, 0)}</Etiqueta>
                )}
              </div>

              <p className="cifra mt-2 text-lg font-semibold">
                {eurosUnidad(f.precio_unidad_cent, f.unidad)}
              </p>
              {cadena && (
                <p className="text-sm text-tinta-suave">en {nombreCadena(cadena)}</p>
              )}

              <div className="mt-3 flex flex-wrap gap-2">
                <Boton
                  variante="principal"
                  disabled={!elegida || pasar.isPending}
                  onClick={() => pasar.mutate({
                    grupo_id: f.grupo_id, producto_id: f.producto_id ?? null,
                  })}
                >
                  A la lista
                </Boton>
                <Boton
                  variante="sutil"
                  disabled={quitar.isPending}
                  onClick={() => quitar.mutate({
                    grupo_id: f.grupo_id, producto_id: f.producto_id ?? null,
                  })}
                >
                  Quitar
                </Boton>
              </div>
            </Tarjeta>
          )
        })}
      </div>
    </div>
  )
}
