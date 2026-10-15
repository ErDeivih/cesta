/** Guardar la combinacion de filtros con un nombre, y volver a ella.
 *
 *  Se guarda en `localStorage` porque no hay endpoint de vistas guardadas. Lo
 *  que se guarda es la consulta entera, asi que una vista es exactamente el
 *  enlace que se copiaria a mano: no hay un formato propio que se pueda quedar
 *  desincronizado con los filtros.
 */
import { useState } from 'react'

import { borrarVista, guardarVista, leerVistas, type VistaGuardada } from '../estado/vistasGuardadas'
import { Aviso, Boton, CampoTexto, cx } from './ui'

interface Props {
  /** La consulta actual, con el `?` delante. */
  consulta: string
  onAplicar: (consulta: string) => void
}

export function VistasGuardadas({ consulta, onAplicar }: Props) {
  const [vistas, setVistas] = useState<VistaGuardada[]>(() => leerVistas())
  const [abierto, setAbierto] = useState(false)
  const [nombre, setNombre] = useState('')
  const [nota, setNota] = useState<string | null>(null)

  const guarda = () => {
    const limpio = nombre.trim()
    if (!limpio) return
    setVistas(guardarVista(limpio, consulta))
    setNombre('')
    setAbierto(false)
    setNota(`Guardada «${limpio}». Solo está en este navegador.`)
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {vistas.map((v) => (
        <span
          key={v.nombre}
          className="inline-flex items-center overflow-hidden rounded-campo border border-borde bg-papel "
        >
          <button
            type="button"
            onClick={() => onAplicar(v.consulta)}
            title={v.consulta || 'Sin filtros'}
            className="min-h-[44px] px-3 py-1 text-cuerpo font-medium hover:bg-marfil dark:hover:bg-papel"
          >
            {v.nombre}
          </button>
          <button
            type="button"
            aria-label={`Borrar la vista ${v.nombre}`}
            onClick={() => setVistas(borrarVista(v.nombre))}
            className="min-h-[44px] min-w-[44px] border-l border-borde px-2 text-tinta-suave hover:bg-marfil hover:text-error dark:hover:bg-papel dark:hover:text-error"
          >
            ×
          </button>
        </span>
      ))}

      {abierto ? (
        <form
          className="flex flex-wrap items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            guarda()
          }}
        >
          <CampoTexto
            etiqueta="Nombre de la vista"
            value={nombre}
            autoFocus
            maxLength={40}
            placeholder="Sin lactosa barato"
            onChange={(e) => setNombre(e.target.value)}
            className="w-56"
          />
          <Boton type="submit" variante="principal" disabled={!nombre.trim()}>
            Guardar
          </Boton>
          <Boton variante="sutil" onClick={() => setAbierto(false)}>
            Cancelar
          </Boton>
        </form>
      ) : (
        <Boton
          variante="normal"
          onClick={() => setAbierto(true)}
          className={cx(!consulta && 'opacity-60')}
        >
          Guardar estos filtros
        </Boton>
      )}

      {nota && (
        <div className="w-full">
          <Aviso tono="info">{nota}</Aviso>
        </div>
      )}
    </div>
  )
}