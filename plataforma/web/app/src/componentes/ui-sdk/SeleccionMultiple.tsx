/** *** ELEGIR VARIAS LINEAS Y ACTUAR SOBRE ELLAS DE UNA VEZ. *** *
 *
 *  *Quitar de una en una es el trabajo que hace que la lista se deje de usar; y buscar
 *  alternativa solo en lo marcado necesita poder marcar.*
 *
 *  Pieza de comportamiento: **`Listbox` de `@ui-sdk/react/listbox`** con `multiple` — resuelve
 *  `role="listbox"` + `aria-multiselectable`, `aria-selected` por opcion, espacio que marca,
 *  Mayus+espacio y Mayus+flechas para el rango, Ctrl/Cmd+A para todas y el recorrido del foco.
 *  *Escape y la barra de acciones en lote son de esta pieza, no del paquete.*
 */
import { useEffect, useState } from 'react'

import { Listbox, ListboxItem } from '@ui-sdk/react/listbox'

import { euros } from '../../api/formato'
import { Boton } from '../ui'

export type FilaSeleccionable = {
  id: string
  nombre: string
  /** El precio que se enseña al lado, si la pantalla lo sabe. */
  precioCent?: number | null
}

export function SeleccionMultiple({
  filas,
  alQuitar,
  alSalir,
  etiqueta = 'Líneas de la compra',
  accion = 'Quitar',
}: {
  filas: FilaSeleccionable[]
  /** La accion en lote, con **las marcadas**: no con todas ni con las que se vean. */
  alQuitar: (ids: string[]) => void
  /** Salir del modo de seleccion (Escape o el boton). */
  alSalir: () => void
  etiqueta?: string
  /** El verbo de la accion en lote. */
  accion?: string
}) {
  const [seleccion, setSeleccion] = useState<string[]>([])
  const cuantas = seleccion.length
  const aviso = cuantas === 1 ? '1 línea seleccionada' : `${cuantas} líneas seleccionadas`

  // *Escape sale del modo de seleccion **antes** de que lo vea el listbox: se captura en el
  // documento para que funcione aunque el foco este en una opcion.*
  useEffect(() => {
    function alTeclear(evento: KeyboardEvent) {
      if (evento.key !== 'Escape') return
      setSeleccion([])
      alSalir()
    }
    document.addEventListener('keydown', alTeclear, true)
    return () => document.removeEventListener('keydown', alTeclear, true)
  }, [alSalir])

  return (
    <div className="flex flex-col gap-2">
      <Listbox
        multiple
        value={seleccion}
        onValueChange={setSeleccion}
        aria-label={etiqueta}
        className="flex flex-col gap-1"
      >
        {filas.map((fila) => (
          <ListboxItem
            key={fila.id}
            value={fila.id}
            label={fila.nombre}
            className="flex min-h-[44px] cursor-pointer items-center justify-between gap-3 rounded-campo border border-borde bg-papel px-3 py-2 aria-selected:border-bosque aria-selected:bg-marfil"
          >
            <span className="min-w-0 truncate text-cuerpo text-tinta-fuerte">{fila.nombre}</span>
            <span className="cifra shrink-0 text-etiqueta text-tinta-suave">
              {fila.precioCent === null || fila.precioCent === undefined
                ? ''
                : euros(fila.precioCent)}
            </span>
          </ListboxItem>
        ))}
      </Listbox>

      <div className="flex flex-wrap items-center gap-2" role="status">
        {cuantas > 0 ? (
          <>
            <span className="text-etiqueta text-tinta-suave">{aviso}</span>
            <Boton variante="principal" onClick={() => alQuitar(seleccion)}>
              {accion} {cuantas} {cuantas === 1 ? 'línea' : 'líneas'}
            </Boton>
          </>
        ) : (
          <span className="text-etiqueta text-tinta-suave">
            Marca con Espacio. Ctrl+A marca todas. Escape sale.
          </span>
        )}
        <Boton
          variante="sutil"
          onClick={() => {
            setSeleccion([])
            alSalir()
          }}
        >
          Salir de la selección
        </Boton>
      </div>
    </div>
  )
}
