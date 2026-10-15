/** El recetario: la pantalla propia de Recetas.
 *
 *  **El selector de version es lo importante de esta pantalla.** El recetario guarda versiones para que
 *  el diario pueda citar una y que no se mueva; pero eso, sin poder mirarlo, es una promesa. Con el
 *  selector, quien cocina puede comprobar que la version 1 sigue diciendo lo que decia despues de haber
 *  cambiado la receta, que es exactamente lo que se promete.
 *
 *  Estados de verdad: cargando, sin nada, y error con el motivo que da la API. Una pantalla que solo
 *  sabe pintar el caso bueno no esta terminada.
 */
import { useState } from 'react'

import {
  useArchivarReceta,
  useCrearReceta,
  useReceta,
  useRecetas,
} from '../api/recetas'
import type { Ingrediente } from '../api/recetas'
import { textoDeError } from '../api/cliente'
import { Boton, Cargando, Fallo, Tarjeta, Vacio, Etiqueta } from '../componentes/ui'
import { etiquetasDe, filtraRecetas, textoDelVacio } from '../logica/recetario'

function ListaDeIngredientes({ ingredientes }: { ingredientes: Ingrediente[] }) {
  if (ingredientes.length === 0) {
    return <p className="text-[13px] text-secundaria">Sin ingredientes apuntados.</p>
  }
  return (
    <ul className="mt-1 flex flex-col gap-1">
      {ingredientes.map((i, posicion) => (
        <li key={`${i.texto}-${posicion}`} className="text-[14px] leading-[22px] text-tinta-fuerte">
          {i.cantidad ? <span className="tabular-nums">{i.cantidad} </span> : null}
          {i.unidad ? <span>{i.unidad} </span> : null}
          {i.texto}
        </li>
      ))}
    </ul>
  )
}

function Detalle({ id, alCerrar }: { id: number; alCerrar: () => void }) {
  const [version, setVersion] = useState<number | null>(null)
  const { data, isPending, error } = useReceta(id, version)

  if (isPending) return <Tarjeta><p className="text-[16px]">Leyendo la receta...</p></Tarjeta>
  if (error) {
    return (
      <Tarjeta>
        <Etiqueta tono="mal">{textoDeError(error)}</Etiqueta>
      </Tarjeta>
    )
  }
  if (!data) return null

  return (
    <Tarjeta>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-serif text-[24px] leading-8 font-semibold text-tinta-fuerte">
          {data.nombre}
        </h2>
        <button type="button" onClick={alCerrar} className="min-h-[44px] min-w-[44px] text-[14px] text-secundaria underline">
          Cerrar
        </button>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-3">
        <label className="text-[13px] text-secundaria" htmlFor="version">
          Version
        </label>
        <select
          id="version"
          value={version ?? data.version}
          onChange={(e) => setVersion(Number(e.target.value))}
          className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
        >
          {/* Del 1 a la ultima: la lista sale de la propia receta, asi que no hay nada que inventar. */}
          {Array.from({ length: data.version }, (_, i) => i + 1).map((n) => (
            <option key={n} value={n}>
              {n}
              {n === data.version ? ' (ultima)' : ''}
            </option>
          ))}
        </select>
        <span className="text-[13px] text-secundaria tabular-nums">
          {data.raciones} raciones{data.minutos ? ` · ${data.minutos} min` : ''}
        </span>
      </div>

      <ListaDeIngredientes ingredientes={data.ingredientes} />

      {data.preparacion && (
        <p className="mt-3 whitespace-pre-line text-[14px] leading-[22px] text-tinta-fuerte">
          {data.preparacion}
        </p>
      )}
    </Tarjeta>
  )
}

function Alta() {
  const [abierto, setAbierto] = useState(false)
  const [nombre, setNombre] = useState('')
  const [raciones, setRaciones] = useState(2)
  const [preparacion, setPreparacion] = useState('')
  const [ingredientes, setIngredientes] = useState('')
  const crear = useCrearReceta()

  if (!abierto) {
    return (
      <Boton onClick={() => setAbierto(true)}>Anadir una receta</Boton>
    )
  }
  return (
    <Tarjeta>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          // Una linea por ingrediente, y "cantidad unidad texto" si se sabe. Es la forma mas rapida de
          // escribir una receta de pie en la cocina, y la que menos se equivoca.
          const lista: Ingrediente[] = ingredientes
            .split('\n')
            .map((linea) => linea.trim())
            .filter((linea) => linea.length > 0)
            .map((linea) => {
              const trozos = linea.split(' ')
              const cantidad = Number(trozos[0]?.replace(',', '.'))
              if (Number.isFinite(cantidad) && trozos.length > 2) {
                return { texto: trozos.slice(2).join(' '), cantidad, unidad: trozos[1] }
              }
              return { texto: linea }
            })
          crear.mutate(
            { nombre, raciones, preparacion, ingredientes: lista, minutos: null, etiquetas: '' },
            {
              onSuccess: () => {
                setAbierto(false)
                setNombre('')
                setPreparacion('')
                setIngredientes('')
              },
            },
          )
        }}
        className="flex min-h-full flex-col gap-3"
      >
        <label className="flex flex-col gap-1 text-[13px] text-secundaria">
          Nombre
          <input
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            required
            className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
          />
        </label>
        <label className="flex flex-col gap-1 text-[13px] text-secundaria">
          Raciones
          <input
            type="number"
            min={1}
            value={raciones}
            onChange={(e) => setRaciones(Number(e.target.value))}
            className="min-h-[44px] w-24 rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte tabular-nums"
          />
        </label>
        <label className="flex flex-col gap-1 text-[13px] text-secundaria">
          Ingredientes, uno por linea
          <textarea
            value={ingredientes}
            onChange={(e) => setIngredientes(e.target.value)}
            rows={4}
            placeholder={'600 g patatas\n5 ud huevos'}
            className="rounded-md border border-borde-fuerte bg-papel p-2 text-[16px] leading-[22px] text-tinta-fuerte"
          />
        </label>
        <label className="flex flex-col gap-1 text-[13px] text-secundaria">
          Preparacion
          <textarea
            value={preparacion}
            onChange={(e) => setPreparacion(e.target.value)}
            rows={3}
            className="rounded-md border border-borde-fuerte bg-papel p-2 text-[16px] leading-[22px] text-tinta-fuerte"
          />
        </label>
        {crear.error && <Etiqueta tono="mal">{textoDeError(crear.error)}</Etiqueta>}
        <div className="flex gap-2">
          <Boton type="submit" disabled={crear.isPending}>
            {crear.isPending ? 'Guardando...' : 'Guardar'}
          </Boton>
          <Boton onClick={() => setAbierto(false)}>
            Cancelar
          </Boton>
        </div>
      </form>
    </Tarjeta>
  )
}

export function Recetario() {
  const [abierta, setAbierta] = useState<number | null>(null)
  const [verArchivadas, setVerArchivadas] = useState(false)
  // **G12, punto 218: el buscador que faltaba.** *Se filtra en el cliente a proposito: la lista ya
  // viene filtrada por dueno desde el servidor, asi que esconder es elegir un subconjunto de lo que
  // ya era tuyo -- y no anade un parametro del que alguien pueda olvidarse de comprobar el dueno.*
  const [texto, setTexto] = useState('')
  const [etiqueta, setEtiqueta] = useState('')
  const { data, isPending, error } = useRecetas(verArchivadas)
  const archivar = useArchivarReceta()

  const todas = data?.recetas ?? []
  const visibles = filtraRecetas(todas, { texto, etiqueta: etiqueta || null })
  const etiquetas = etiquetasDe(todas)

  return (
    <div className="flex flex-col gap-4">
      {todas.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="search"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Buscar por nombre..."
            aria-label="Buscar recetas por nombre"
            className="min-h-[44px] flex-1 rounded border border-borde bg-papel px-3 text-[16px]"
          />
          {etiquetas.length > 0 && (
            <select
              value={etiqueta}
              onChange={(e) => setEtiqueta(e.target.value)}
              aria-label="Filtrar por etiqueta"
              className="min-h-[44px] rounded border border-borde bg-papel px-2 text-[16px]"
            >
              <option value="">Todas las etiquetas</option>
              {etiquetas.map((e) => (
                <option key={e} value={e}>{e}</option>
              ))}
            </select>
          )}
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Boton onClick={() => setVerArchivadas(!verArchivadas)}>
          {verArchivadas ? 'Ver solo las de ahora' : 'Ver tambien las archivadas'}
        </Boton>
        <Alta />
      </div>

      {isPending && <Cargando que="el recetario" />}
      {error && <Fallo error={error} />}

      {data && todas.length === 0 && (
        <Vacio titulo="Todavia no hay recetas" className="grow">
          <p>Anade la primera y aparecera aqui, con sus ingredientes y sus raciones.</p>
        </Vacio>
      )}

      {todas.length > 0 && visibles.length === 0 && (
        <Vacio titulo="Ninguna receta coincide">
          <p>{textoDelVacio({ texto, etiqueta: etiqueta || null }, todas.length)}</p>
        </Vacio>
      )}

      {visibles.length > 0 && (
        <ul className="flex flex-col gap-2">
          {visibles.map((r) => (
            <li key={r.id}>
              <Tarjeta>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => setAbierta(r.id === abierta ? null : r.id)}
                    className="min-h-[44px] min-w-[44px] text-left font-serif text-[19px] leading-7 text-tinta-fuerte"
                  >
                    {r.nombre}
                  </button>
                  <span className="text-[13px] text-secundaria tabular-nums">
                    {r.raciones} raciones · version {r.version}
                    {r.archivada ? ' · archivada' : ''}
                  </span>
                </div>
                {!r.archivada && (
                  <button
                    type="button"
                    onClick={() => archivar.mutate(r.id)}
                    className="mt-1 min-h-[44px] min-w-[44px] text-[13px] text-secundaria underline"
                  >
                    Archivar
                  </button>
                )}
                  {/* **El error, si falla.** Archivar puede fallar -- la sesion, la red -- y hasta ahora
                      se pulsaba y no pasaba nada visible, que es lo mismo que hacer creer que si
                      funciono. */}
                  {archivar.error && !r.archivada && (
                    <Etiqueta tono="mal">{textoDeError(archivar.error)}</Etiqueta>
                  )}
              </Tarjeta>
              {abierta === r.id && <div className="mt-2"><Detalle id={r.id} alCerrar={() => setAbierta(null)} /></div>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
