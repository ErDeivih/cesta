/** El detalle de una receta: la receta de esa direccion, con sus versiones.

 *  **Lee la receta persistida de la ruta**, no un estado de la pantalla anterior: se puede abrir el enlace
 *  en otra pestana o recargar, y sigue enseñando lo mismo. Eso es lo que lo hace una pantalla y no un
 *  paso intermedio.
 *
 *  **Y tiene 404 de verdad.** Si la receta no existe -- o es de otra persona, que la API contesta igual para
 *  no decir cual existe -- se dice con esas palabras. Un 404 aqui no es un fallo: es una respuesta.
 */
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { textoDeError, esErrorApi } from '../api/cliente'
import { useReceta } from '../api/recetas'
import { Tarjeta, Vacio } from '../componentes/ui'

export function RecetaDetalle() {
  const { recetaId } = useParams()
  const id = recetaId ? Number(recetaId) : null
  const [version, setVersion] = useState<number | null>(null)
  const { data, isPending, error } = useReceta(id, version)

  if (isPending) {
    return <p className="text-[15px] text-secundaria">Leyendo la receta...</p>
  }

  if (error) {
    // **404 no es un fallo.** Se distingue del resto para no pintar en rojo algo que es una respuesta.
    if (esErrorApi(error) && error.estado === 404) {
      return (
        <Vacio titulo="Esa receta no existe">
          <p>
            Puede que se haya archivado o que el enlace este mal. <Link to="/recetas" className="underline">
              Vuelve al recetario
            </Link>.
          </p>
        </Vacio>
      )
    }
    return <p className="text-[15px] text-error">{textoDeError(error)}</p>
  }
  if (!data) return null

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-serif text-[24px] leading-8 font-semibold text-tinta-fuerte">
          {data.nombre}
        </h2>
        <Link to="/recetas/plan" className="min-h-[44px] text-[14px] text-secundaria underline">
          Planificar
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <label className="text-[13px] text-secundaria" htmlFor="version">
          Version
        </label>
        <select
          id="version"
          value={version ?? data.version}
          onChange={(e) => setVersion(Number(e.target.value))}
          className="min-h-[44px] rounded-md border border-borde-fuerte bg-papel px-2 text-[16px] text-tinta-fuerte"
        >
          {/* De la 1 a la ultima: la lista sale de la propia receta, sin inventar numeros. */}
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
        {version !== null && version !== data.version && (
          <span className="text-[13px] text-aviso">
            Estas viendo una version anterior. La ultima es la {data.version}.
          </span>
        )}
      </div>

      <Tarjeta>
        {data.ingredientes.length === 0 ? (
          <p className="text-[13px] text-secundaria">Sin ingredientes apuntados.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {data.ingredientes.map((i, posicion) => (
              <li key={`${i.texto}-${posicion}`} className="text-[14px] leading-[22px] text-tinta-fuerte">
                {i.cantidad ? <span className="tabular-nums">{i.cantidad} </span> : null}
                {i.unidad ? <span>{i.unidad} </span> : null}
                {i.texto}
              </li>
            ))}
          </ul>
        )}
      </Tarjeta>

      {data.preparacion && (
        <Tarjeta>
          <p className="whitespace-pre-line text-[14px] leading-[22px] text-tinta-fuerte">
            {data.preparacion}
          </p>
        </Tarjeta>
      )}
    </div>
  )
}
